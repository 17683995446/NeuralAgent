"""
认证与授权 - 简化版本

使用 FastAPI 标准方式，避免复杂依赖
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import hashlib

from backend.config import settings


# ==================== 类型定义 ====================

class UserRole(str, Enum):
    """用户角色枚举"""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class Permission(str, Enum):
    """权限枚举"""
    CREATE_TASK = "create_task"
    READ_TASK = "read_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    CODE_PROCESSING = "code_processing"
    ADMIN_OPERATIONS = "admin_operations"


class User:
    """用户数据模型"""
    def __init__(self, username: str, role: UserRole, 
                 email: Optional[str] = None, disabled: bool = False):
        self.username = username
        self.role = role
        self.email = email
        self.disabled = disabled


# ==================== 权限矩阵 ====================

ROLE_PERMISSIONS: Dict[UserRole, set] = {
    UserRole.GUEST: {Permission.READ_TASK},
    UserRole.USER: {
        Permission.CREATE_TASK, 
        Permission.READ_TASK, 
        Permission.UPDATE_TASK, 
        Permission.DELETE_TASK, 
        Permission.CODE_PROCESSING
    },
    UserRole.ADMIN: {
        Permission.CREATE_TASK, 
        Permission.READ_TASK, 
        Permission.UPDATE_TASK, 
        Permission.DELETE_TASK, 
        Permission.CODE_PROCESSING, 
        Permission.ADMIN_OPERATIONS
    }
}


# ==================== 密码处理 ====================

def hash_password(password: str) -> str:
    """简单密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password


# ==================== 内存用户数据库（示例） ====================

fake_users_db: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin12"),
        "email": "admin@example.com",
        "role": UserRole.ADMIN,
        "disabled": False
    },
    "user": {
        "username": "user",
        "hashed_password": hash_password("user12"),
        "email": "user@example.com",
        "role": UserRole.USER,
        "disabled": False
    },
    "guest": {
        "username": "guest",
        "hashed_password": hash_password("guest12"),
        "email": "guest@example.com",
        "role": UserRole.GUEST,
        "disabled": False
    }
}


# ==================== JWT 处理 ====================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    
    secret_key = settings.jwt_secret_key or "fallback-secret-key-change-in-production"
    
    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


# ==================== 用户获取与认证 ====================

def get_user(username: str) -> Optional[User]:
    """从数据库获取用户"""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return User(
            username=user_dict["username"],
            role=user_dict["role"],
            email=user_dict.get("email"),
            disabled=user_dict.get("disabled", False)
        )
    return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = get_user(username)
    if not user:
        return None
    user_dict = fake_users_db[username]
    if not verify_password(password, user_dict["hashed_password"]):
        return None
    if user.disabled:
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        secret_key = settings.jwt_secret_key or "fallback-secret-key-change-in-production"
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        role_str: str = payload.get("role")
        
        if username is None:
            raise credentials_exception
        
        role = UserRole(role_str) if role_str else UserRole.USER
        
    except JWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
    
    # 更新用户角色为 JWT 中的角色
    user.role = role
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# ==================== 权限检查 ====================

def has_permission(user: User, permission: Permission) -> bool:
    """检查用户是否有指定权限"""
    return permission in ROLE_PERMISSIONS.get(user.role, set())


# ==================== 依赖注入 ====================

# 基本认证依赖
require_auth = get_current_active_user


def require_role(*required_roles: UserRole):
    """角色检查依赖"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


def require_permission(required_permission: Permission):
    """权限检查依赖"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not has_permission(current_user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_checker


# 预定义快捷依赖
require_admin = require_role(UserRole.ADMIN)
require_user = require_role(UserRole.USER, UserRole.ADMIN)


# ==================== 工具函数 ====================

def get_all_breaker_statuses():
    """获取熔断器状态 - 保持 API 兼容"""
    return []
