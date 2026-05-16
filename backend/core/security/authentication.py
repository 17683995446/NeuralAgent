"""
NeuralAgent 身份认证系统
提供 JWT 认证和用户管理功能
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

try:
    from jose import jwt
except ImportError:
    import jwt


@dataclass
class User:
    """用户模型"""
    id: str
    username: str
    email: str
    hashed_password: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    is_admin: bool = False
    permissions: List[str] = field(default_factory=list)

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hashed == self.hashed_password


@dataclass
class TokenData:
    """令牌数据"""
    user_id: str
    username: str
    permissions: List[str] = field(default_factory=list)
    token_type: str = "access"
    expires_at: Optional[datetime] = None


class TokenType(str, Enum):
    """令牌类型"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class AuthProvider(str, Enum):
    """认证提供商"""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


_auth_service_instance: Optional['AuthenticationService'] = None


class AuthenticationService:
    """认证服务"""

    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.max_username_length = 256

    def validate_username(self, username: str) -> tuple[bool, Optional[str]]:
        """验证用户名"""
        if not username:
            return False, "Username cannot be empty"

        if len(username) > self.max_username_length:
            return False, f"Username too long (max {self.max_username_length} chars)"

        if not username.replace("_", "").replace("-", "").isalnum():
            return False, "Username can only contain letters, numbers, hyphens and underscores"

        return True, None

    def create_access_token(self, user_id: str, username: str, permissions: List[str]) -> str:
        """创建访问令牌"""
        is_valid, error = self.validate_username(username)
        if not is_valid:
            raise ValueError(f"Invalid username: {error}")

        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "username": username,
            "permissions": permissions,
            "exp": expire,
            "type": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTClaimsError:
            return None
        except Exception:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """从令牌获取用户ID"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None

    def create_tokens(self, user: User) -> Dict[str, str]:
        """创建完整的令牌对"""
        return {
            "access_token": self.create_access_token(
                user.id,
                user.username,
                user.permissions
            ),
            "refresh_token": self.create_refresh_token(user.id),
            "token_type": "bearer"
        }


def get_auth_service() -> AuthenticationService:
    """获取认证服务单例"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthenticationService()
    return _auth_service_instance


def require_auth():
    """认证装饰器"""
    pass


def require_permission(permission: str):
    """权限检查装饰器"""
    pass
