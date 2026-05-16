"""认证和授权中间件

为API路由提供认证和授权保护
"""
from typing import Optional, Callable, List, Dict
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import logging
import time

from backend.core.auth import (
    AuthManager,
    get_auth_manager,
    UserRole,
    Permission,
    ROLE_PERMISSIONS
)

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class AuthConfig:
    """认证配置"""
    
    # 需要认证的端点前缀
    PROTECTED_PREFIXES: List[str] = [
        "/api/v1/tasks",
        "/api/v1/feedback",
        "/api/v1/health/detailed",
        "/api/v1/code/process",
        "/api/v1/code/search",
        "/api/v1/config"
    ]
    
    # 公开端点（无需认证）
    PUBLIC_ENDPOINTS: List[str] = [
        "/",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/demo-token",
        "/api/v1/health"
    ]
    
    # 管理员专属端点
    ADMIN_ENDPOINTS: List[str] = [
        "/api/v1/config/reload",
        "/api/v1/config/hot-reload",
        "/api/v1/metrics/reset"
    ]


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[Dict]:
    """验证JWT令牌"""
    if not credentials:
        return None
    
    try:
        auth_manager = get_auth_manager()
        payload = auth_manager.verify_token(credentials.credentials)
        
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": UserRole(payload.get("role", UserRole.GUEST)),
            "email": payload.get("email")
        }
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def require_auth(func: Callable) -> Callable:
    """要求认证的装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        # 检查是否是公开端点
        if is_public_endpoint(request.url.path):
            return await func(*args, **kwargs)
        
        # 验证令牌
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header.replace("Bearer ", "")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = await verify_token(credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 检查管理员专属端点
        if is_admin_endpoint(request.url.path):
            if user["role"] != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
        
        # 将用户信息添加到request state
        request.state.current_user = user
        
        return await func(*args, **kwargs)
    
    return wrapper


def is_public_endpoint(path: str) -> bool:
    """检查是否是公开端点"""
    for public_path in AuthConfig.PUBLIC_ENDPOINTS:
        if path.startswith(public_path) or path == public_path:
            return True
    return False


def is_admin_endpoint(path: str) -> bool:
    """检查是否是管理员专属端点"""
    for admin_path in AuthConfig.ADMIN_ENDPOINTS:
        if path.startswith(admin_path):
            return True
    return False


def require_role(required_roles: List[UserRole]):
    """角色检查装饰器工厂"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            current_user = getattr(request.state, 'current_user', None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user["role"] not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {[r.value for r in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(required_permissions: List[Permission]):
    """权限检查装饰器工厂"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            current_user = getattr(request.state, 'current_user', None)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = current_user["role"]
            
            # 管理员拥有所有权限
            if user_role == UserRole.ADMIN:
                return await func(*args, **kwargs)
            
            # 检查权限
            if user_role not in ROLE_PERMISSIONS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            for perm in required_permissions:
                if perm not in ROLE_PERMISSIONS[user_role]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{perm.value}' required"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class RequestLoggingMiddleware:
    """请求日志中间件"""
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # 日志请求
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # 日志响应
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.3f}s"
        )
        
        return response
