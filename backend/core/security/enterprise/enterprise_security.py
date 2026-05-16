"""
NeuralAgent - 企业级安全增强
RBAC权限控制、审计日志、SSO集成
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib


class Role(Enum):
    """用户角色"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class Permission(Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SETTINGS = "manage_settings"
    EXECUTE_WORKFLOW = "execute_workflow"
    ACCESS_API = "access_api"


class AuditAction(Enum):
    """审计操作类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    EXECUTE = "execute"
    ERROR = "error"


@dataclass
class AuditLog:
    """审计日志"""
    log_id: str
    user_id: str
    action: AuditAction
    resource: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    email: str
    role: Role
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None


@dataclass
class RBACConfig:
    """RBAC配置"""
    role_hierarchy: Dict[Role, List[Role]] = field(default_factory=dict)
    role_permissions: Dict[Role, Set[Permission]] = field(default_factory=dict)
    default_role: Role = Role.GUEST


class RBACPolicy:
    """RBAC策略"""
    
    def __init__(self, config: Optional[RBACConfig] = None):
        self.config = config or self._get_default_config()
        self.users: Dict[str, User] = {}
    
    def _get_default_config(self) -> RBACConfig:
        """获取默认配置"""
        return RBACConfig(
            role_hierarchy={
                Role.ADMIN: [Role.MANAGER, Role.USER, Role.GUEST],
                Role.MANAGER: [Role.USER, Role.GUEST],
                Role.USER: [Role.GUEST]
            },
            role_permissions={
                Role.ADMIN: {p for p in Permission},
                Role.MANAGER: {
                    Permission.READ, Permission.WRITE, 
                    Permission.EXECUTE_WORKFLOW, Permission.ACCESS_API
                },
                Role.USER: {Permission.READ, Permission.EXECUTE_WORKFLOW},
                Role.GUEST: {Permission.READ}
            }
        )
    
    def add_user(self, user: User) -> None:
        """添加用户"""
        self.users[user.user_id] = user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.users.get(user_id)
    
    def has_permission(
        self,
        user: User,
        permission: Permission
    ) -> bool:
        """检查用户是否有特定权限"""
        if not user.is_active:
            return False
        
        if permission in user.permissions:
            return True
        
        role_permissions = self.config.role_permissions.get(user.role, set())
        if permission in role_permissions:
            return True
        
        for inherited_role in self.config.role_hierarchy.get(user.role, []):
            inherited_permissions = self.config.role_permissions.get(inherited_role, set())
            if permission in inherited_permissions:
                return True
        
        return False
    
    def has_role(self, user: User, role: Role) -> bool:
        """检查用户是否有特定角色"""
        if user.role == role:
            return True
        
        for inherited_role in self.config.role_hierarchy.get(user.role, []):
            if inherited_role == role:
                return True
        
        return False
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """检查权限（便捷方法）"""
        user = self.get_user(user_id)
        if not user:
            return False
        return self.has_permission(user, permission)


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self):
        self.logs: List[AuditLog] = []
    
    def log(
        self,
        user_id: str,
        action: AuditAction,
        resource: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ) -> AuditLog:
        """记录审计日志"""
        import uuid
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        self.logs.append(log)
        return log
    
    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """获取审计日志"""
        filtered = self.logs
        
        if user_id:
            filtered = [l for l in filtered if l.user_id == user_id]
        
        if action:
            filtered = [l for l in filtered if l.action == action]
        
        filtered.sort(key=lambda l: l.timestamp, reverse=True)
        
        return filtered[offset:offset + limit]


class SSOProvider(ABC):
    """SSO提供者抽象基类"""
    
    @abstractmethod
    async def authenticate(self, token: str) -> Optional[Dict[str, Any]]:
        """认证用户"""
        pass
    
    @abstractmethod
    def get_authorization_url(self, redirect_uri: str) -> str:
        """获取授权URL"""
        pass


class SimpleSSOProvider(SSOProvider):
    """简单SSO提供者（示例）"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def authenticate(self, token: str) -> Optional[Dict[str, Any]]:
        """简单认证（示例）"""
        if token:
            return {
                "user_id": hashlib.md5(token.encode()).hexdigest(),
                "email": f"user_{token[:8]}@example.com",
                "name": "SSO User"
            }
        return None
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """获取授权URL（示例）"""
        return f"https://sso.example.com/auth?client_id={self.client_id}&redirect_uri={redirect_uri}"


class EnterpriseSecurityManager:
    """企业安全管理器"""
    
    def __init__(self):
        self.rbac = RBACPolicy()
        self.audit = AuditLogger()
        self.sso_providers: Dict[str, SSOProvider] = {}
    
    def register_sso_provider(self, name: str, provider: SSOProvider) -> None:
        """注册SSO提供者"""
        self.sso_providers[name] = provider
    
    def require_permission(self, permission: Permission):
        """权限检查装饰器"""
        def decorator(func):
            async def wrapper(user_id: str, *args, **kwargs):
                if not self.rbac.check_permission(user_id, permission):
                    raise PermissionError(f"Permission denied: {permission}")
                return await func(user_id, *args, **kwargs)
            return wrapper
        return decorator


def create_enterprise_security() -> EnterpriseSecurityManager:
    """创建企业安全管理器"""
    return EnterpriseSecurityManager()
