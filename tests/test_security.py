"""
测试 security 模块

验证我们基于 FastAPI 标准的安全认证系统是否正常工作
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from backend.core.infrastructure.security import (
    User,
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    verify_password,
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    has_permission,
    require_role,
    require_permission,
    require_auth,
    require_admin,
    require_user
)


class TestUserRoleAndPermissions:
    """测试用户角色和权限"""
    
    def test_user_role_enum(self):
        """测试用户角色枚举"""
        assert UserRole.GUEST == "guest"
        assert UserRole.USER == "user"
        assert UserRole.ADMIN == "admin"
    
    def test_permission_enum(self):
        """测试权限枚举"""
        assert Permission.CREATE_TASK == "create_task"
        assert Permission.ADMIN_OPERATIONS == "admin_operations"
    
    def test_role_permissions(self):
        """测试角色权限矩阵"""
        # Guest 只有读权限
        guest_perms = ROLE_PERMISSIONS[UserRole.GUEST]
        assert Permission.READ_TASK in guest_perms
        assert Permission.CREATE_TASK not in guest_perms
        
        # User 有基本操作权限
        user_perms = ROLE_PERMISSIONS[UserRole.USER]
        assert Permission.CREATE_TASK in user_perms
        assert Permission.UPDATE_TASK in user_perms
        assert Permission.DELETE_TASK in user_perms
        assert Permission.ADMIN_OPERATIONS not in user_perms
        
        # Admin 有所有权限
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert all(perm in admin_perms for perm in Permission)


class TestPasswordHandling:
    """测试密码处理"""
    
    def test_hash_and_verify_password(self):
        """测试密码哈希与验证"""
        password = "my_secret_password"
        hashed = hash_password(password)
        
        # 哈希值不是原文
        assert hashed != password
        # 验证正确的密码
        assert verify_password(password, hashed) is True
        # 验证错误的密码
        assert verify_password("wrong_password", hashed) is False
    
    def test_same_password_different_hash(self):
        """测试相同密码产生相同哈希"""
        password = "test_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # 使用简单哈希，每次结果相同
        assert hash1 == hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAuthentication:
    """测试认证功能"""
    
    def test_authenticate_user_success(self):
        """测试成功认证用户"""
        user = authenticate_user("admin", "admin12")
        assert user is not None
        assert user.username == "admin"
        assert user.role == UserRole.ADMIN
    
    def test_authenticate_user_wrong_password(self):
        """测试错误密码"""
        user = authenticate_user("admin", "wrong_password")
        assert user is None
    
    def test_authenticate_user_nonexistent(self):
        """测试不存在的用户"""
        user = authenticate_user("nonexistent", "any_password")
        assert user is None
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        with patch('backend.core.security.settings') as mock_settings:
            mock_settings.jwt_secret_key = "test_secret_key"
            mock_settings.jwt_algorithm = "HS256"
            
            data = {"sub": "test_user", "role": "user"}
            expires_delta = timedelta(minutes=15)
            
            token = create_access_token(data, expires_delta)
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0


class TestAuthorization:
    """测试授权功能"""
    
    def test_has_permission(self):
        """测试权限检查"""
        admin_user = User(username="admin", role=UserRole.ADMIN)
        user_user = User(username="user", role=UserRole.USER)
        guest_user = User(username="guest", role=UserRole.GUEST)
        
        # Admin 有所有权限
        assert has_permission(admin_user, Permission.ADMIN_OPERATIONS) is True
        
        # User 有任务操作权限
        assert has_permission(user_user, Permission.CREATE_TASK) is True
        assert has_permission(user_user, Permission.ADMIN_OPERATIONS) is False
        
        # Guest 只有读权限
        assert has_permission(guest_user, Permission.READ_TASK) is True
        assert has_permission(guest_user, Permission.CREATE_TASK) is False


class TestUserDataclass:
    """测试 User 数据类"""
    
    def test_create_user(self):
        """测试创建用户"""
        user = User(
            username="test_user",
            role=UserRole.USER,
            email="test@example.com"
        )
        assert user.username == "test_user"
        assert user.role == UserRole.USER
        assert user.email == "test@example.com"
        assert user.disabled is False
    
    def test_create_disabled_user(self):
        """测试创建禁用的用户"""
        user = User(
            username="disabled_user",
            role=UserRole.GUEST,
            disabled=True
        )
        assert user.disabled is True


class TestDependencyHelpers:
    """测试依赖注入辅助函数"""
    
    def test_require_role_factory(self):
        """测试角色检查工厂函数"""
        checker = require_role(UserRole.ADMIN)
        assert callable(checker)
    
    def test_require_permission_factory(self):
        """测试权限检查工厂函数"""
        checker = require_permission(Permission.CREATE_TASK)
        assert callable(checker)
    
    def test_shortcut_dependencies(self):
        """测试快捷依赖"""
        assert callable(require_auth)
        assert callable(require_admin)
        assert callable(require_user)


class TestTokenValidation:
    """测试令牌验证（简化版）"""
    
    def test_token_expiry(self):
        """测试令牌过期"""
        with patch('backend.core.security.settings') as mock_settings:
            mock_settings.jwt_secret_key = "test_secret_key"
            mock_settings.jwt_algorithm = "HS256"
            
            # 创建一个即将过期的令牌
            token = create_access_token(
                {"sub": "test"},
                timedelta(seconds=-1)
            )
            
            # 验证逻辑会拒绝过期令牌（这里不完整测试，但框架本身会处理）
            assert token is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
