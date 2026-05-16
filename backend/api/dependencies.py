"""认证依赖项和中间件

提供API认证和授权的依赖注入
"""
from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import logging

from backend.core.auth import (
    AuthManager,
    get_auth_manager,
    UserRole,
    Permission,
    ROLE_PERMISSIONS
)

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """获取当前用户（可选，不强制认证）
    
    Returns:
        用户信息字典或None
    """
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
            "role": payload.get("role", UserRole.GUEST),
            "email": payload.get("email")
        }
    except Exception as e:
        logger.warning(f"Failed to get current user: {e}")
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """获取当前用户（强制认证）
    
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 未认证时抛出401
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        auth_manager = get_auth_manager()
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role", UserRole.GUEST),
            "email": payload.get("email")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_roles(allowed_roles: List[UserRole]):
    """角色检查依赖项工厂
    
    Args:
        allowed_roles: 允许的角色列表
        
    Returns:
        依赖项函数
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_role = UserRole(current_user.get("role", UserRole.GUEST))
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {[r.value for r in allowed_roles]}"
            )
        
        return current_user
    
    return role_checker


def require_permissions(required_permissions: List[Permission]):
    """权限检查依赖项工厂
    
    Args:
        required_permissions: 必需的权限列表
        
    Returns:
        依赖项函数
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_role = UserRole(current_user.get("role", UserRole.GUEST))
        
        # 管理员拥有所有权限
        if user_role == UserRole.ADMIN:
            return current_user
        
        # 检查每个必需的权限
        for perm in required_permissions:
            if not has_permission(user_role, perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{perm.value}' required"
                )
        
        return current_user
    
    return permission_checker


def has_permission(role: UserRole, permission: Permission) -> bool:
    """检查角色是否有特定权限
    
    Args:
        role: 用户角色
        permission: 权限
        
    Returns:
        是否有权限
    """
    if role not in ROLE_PERMISSIONS:
        return False
    return permission in ROLE_PERMISSIONS[role]


def admin_only():
    """管理员专属依赖项"""
    return require_roles([UserRole.ADMIN])


def user_or_admin():
    """用户或管理员依赖项"""
    return require_roles([UserRole.USER, UserRole.ADMIN])


class RateLimitMiddleware:
    """简单的速率限制中间件（内存实现，生产环境应使用Redis）"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}
    
    async def __call__(self, request: Request, call_next):
        # 简单的IP级别的速率限制
        client_ip = request.client.host if request.client else "unknown"
        import time
        
        current_time = time.time()
        
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        
        # 清理过期的请求记录
        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if current_time - t < self.window_seconds
        ]
        
        # 检查速率限制
        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # 记录请求
        self._requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response


from fastapi.responses import JSONResponse
