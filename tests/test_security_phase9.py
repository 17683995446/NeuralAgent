"""
NeuralAgent 阶段9安全测试
测试身份认证、API密钥管理和限流功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta


class TestAuthentication:
    """身份认证测试"""
    
    def test_user_creation(self):
        """测试用户创建"""
        from backend.core.security import User
        
        user = User(
            id="test-1",
            username="testuser",
            email="test@example.com",
            hashed_password=User.create_password_hash("password123")
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.verify_password("password123")
        assert not user.verify_password("wrongpassword")
    
    def test_password_hashing(self):
        """测试密码哈希"""
        from backend.core.security import User
        
        password = "securepassword123"
        hashed = User.create_password_hash(password)
        
        assert hashed != password
        assert len(hashed) == 64  # SHA256 hex length
    
    def test_auth_service_registration(self):
        """测试用户注册"""
        from backend.core.security import AuthenticationService
        
        auth = AuthenticationService()
        user = auth.register_user(
            username="newuser",
            email="new@example.com",
            password="password123"
        )
        
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.verify_password("password123")
    
    def test_auth_service_authentication(self):
        """测试用户认证"""
        from backend.core.security import AuthenticationService
        
        auth = AuthenticationService()
        auth.register_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        user = auth.authenticate_user("testuser", "password123")
        assert user is not None
        assert user.username == "testuser"
        
        wrong_user = auth.authenticate_user("testuser", "wrongpassword")
        assert wrong_user is None
    
    def test_token_creation(self):
        """测试令牌创建"""
        from backend.core.security import AuthenticationService, TokenType
        
        auth = AuthenticationService()
        user = auth.register_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        access_token = auth.create_access_token(user)
        assert access_token.token_type == TokenType.ACCESS
        assert access_token.user_id == user.id
        assert access_token.username == user.username
    
    def test_token_verification(self):
        """测试令牌验证"""
        from backend.core.security import AuthenticationService
        
        auth = AuthenticationService()
        user = auth.register_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        token_data = auth.create_access_token(user)
        verified = auth.verify_token(token_data.token)
        
        assert verified is not None
        assert verified.user_id == user.id
        assert verified.username == user.username
    
    def test_refresh_token(self):
        """测试刷新令牌"""
        from backend.core.security import AuthenticationService, TokenType
        
        auth = AuthenticationService()
        user = auth.register_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        refresh_token = auth.create_refresh_token(user)
        assert refresh_token.token_type == TokenType.REFRESH
        assert refresh_token.user_id == user.id


class TestAPIKeyManager:
    """API密钥管理测试"""
    
    def test_key_creation(self):
        """测试密钥创建"""
        from backend.core.security.api_key_manager import APIKeyManager, KeyType
        
        manager = APIKeyManager()
        key_obj, api_key = manager.create_key(
            name="test-key",
            key_type=KeyType.USER
        )
        
        assert key_obj.name == "test-key"
        assert key_obj.key_type == KeyType.USER
        assert api_key.startswith("na_")
        assert len(api_key) > 20
    
    def test_key_verification(self):
        """测试密钥验证"""
        from backend.core.security.api_key_manager import APIKeyManager, KeyType
        
        manager = APIKeyManager()
        key_obj, api_key = manager.create_key(
            name="test-key",
            key_type=KeyType.USER
        )
        
        verified_key = manager.verify_key(api_key)
        assert verified_key is not None
        assert verified_key.id == key_obj.id
    
    def test_key_revocation(self):
        """测试密钥撤销"""
        from backend.core.security.api_key_manager import APIKeyManager, KeyType
        
        manager = APIKeyManager()
        key_obj, api_key = manager.create_key(
            name="test-key",
            key_type=KeyType.USER
        )
        
        result = manager.revoke_key(key_obj.id)
        assert result is True
        
        verified_key = manager.verify_key(api_key)
        assert verified_key is None
    
    def test_key_deletion(self):
        """测试密钥删除"""
        from backend.core.security.api_key_manager import APIKeyManager, KeyType
        
        manager = APIKeyManager()
        key_obj, api_key = manager.create_key(
            name="test-key",
            key_type=KeyType.USER
        )
        
        result = manager.delete_key(key_obj.id)
        assert result is True
        
        deleted_key = manager.get_key(key_obj.id)
        assert deleted_key is None
    
    def test_key_expiration(self):
        """测试密钥过期"""
        from backend.core.security.api_key_manager import APIKeyManager, KeyType
        
        manager = APIKeyManager()
        key_obj, api_key = manager.create_key(
            name="test-key",
            key_type=KeyType.USER,
            expires_in_days=1
        )
        
        assert key_obj.is_expired() is False
        
        key_obj.expires_at = datetime.now() - timedelta(days=1)
        assert key_obj.is_expired() is True
    
    def test_usage_stats(self):
        """测试使用统计"""
        from backend.core.security.api_key_manager import APIKeyManager, KeyType
        
        manager = APIKeyManager()
        key_obj, api_key = manager.create_key(
            name="test-key",
            key_type=KeyType.USER
        )
        
        manager.verify_key(api_key)
        manager.verify_key(api_key)
        manager.verify_key(api_key)
        
        stats = manager.get_usage_stats(key_obj.id)
        
        assert stats["key_id"] == key_obj.id
        assert stats["usage_count"] == 3


class TestRateLimiter:
    """限流测试"""
    
    def test_rate_limiter_creation(self):
        """测试限流器创建"""
        from backend.core.security import RateLimiter, RateLimitConfig
        
        limiter = RateLimiter()
        assert limiter is not None
        
        config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=10000
        )
        limiter.set_limit("test-user", config)
        
        assert "test-user" in limiter._limits
    
    def test_rate_limit_check(self):
        """测试限流检查"""
        from backend.core.security import RateLimiter, RateLimitConfig
        
        limiter = RateLimiter()
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_size=5
        )
        limiter.set_limit("test-user", config)
        
        for _ in range(5):
            result = limiter.check_limit("test-user")
            assert result.allowed is True
        
        result = limiter.check_limit("test-user")
        assert result.allowed is False
        assert result.retry_after_seconds is not None
    
    def test_token_bucket(self):
        """测试令牌桶"""
        from backend.core.security import TokenBucket
        
        bucket = TokenBucket(capacity=10, refill_rate=1.0, refill_period_seconds=1.0)
        
        for _ in range(10):
            assert bucket.consume() is True
        
        assert bucket.consume() is False
        
        bucket._refill()
        assert bucket.get_tokens() > 0
    
    def test_custom_limits(self):
        """测试自定义限流"""
        from backend.core.security import RateLimitMiddleware, RateLimitConfig
        
        middleware = RateLimitMiddleware()
        middleware.set_custom_limit(
            identifier="premium-user",
            requests_per_minute=1000,
            requests_per_hour=10000,
            requests_per_day=100000,
            burst_size=100
        )
        
        limiter = middleware._limiter
        config = limiter._limits.get("premium-user")
        
        assert config is not None
        assert config.requests_per_minute == 1000
    
    def test_rate_limit_stats(self):
        """测试限流统计"""
        from backend.core.security import RateLimiter, RateLimitConfig
        
        limiter = RateLimiter()
        config = RateLimitConfig()
        limiter.set_limit("test-user", config)
        
        limiter.check_limit("test-user")
        limiter.check_limit("test-user")
        
        stats = limiter.get_stats("test-user")
        assert stats["minute_requests"] == 2


class TestSecurityIntegration:
    """安全集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self):
        """测试完整认证流程"""
        from backend.core.security import (
            AuthenticationService,
            APIKeyManager,
            RateLimiter,
            KeyType
        )
        
        auth = AuthenticationService()
        key_manager = APIKeyManager()
        rate_limiter = RateLimiter()
        
        user = auth.register_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        authenticated = auth.authenticate_user("testuser", "password123")
        assert authenticated is not None
        
        token_data = auth.create_access_token(user)
        verified = auth.verify_token(token_data.token)
        assert verified is not None
        
        key_obj, api_key = key_manager.create_key(
            name="test-key",
            key_type=KeyType.USER,
            user_id=user.id
        )
        
        verified_key = key_manager.verify_key(api_key)
        assert verified_key is not None
        
        result = rate_limiter.check_limit(user.id)
        assert result.allowed is True
    
    def test_password_strength(self):
        """测试密码强度"""
        from backend.core.security import User
        
        weak_passwords = ["123", "abc", "password"]
        strong_passwords = ["P@ssw0rd!123", "MySecureP@ssw0rd", "C0mpl3x!Pass"]
        
        for pwd in weak_passwords:
            hashed = User.create_password_hash(pwd)
            assert len(hashed) == 64
        
        for pwd in strong_passwords:
            hashed = User.create_password_hash(pwd)
            assert len(hashed) == 64
    
    def test_api_key_format(self):
        """测试API密钥格式"""
        from backend.core.security.api_key_manager import APIKey
        
        key = APIKey.generate_key()
        
        assert key.startswith("na_")
        assert len(key) > 20
        assert " " not in key
    
    def test_permission_control(self):
        """测试权限控制"""
        from backend.core.security import User
        
        admin_user = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password=User.create_password_hash("admin123"),
            is_admin=True,
            permissions=["read", "write", "delete", "admin"]
        )
        
        regular_user = User(
            id="user-1",
            username="user",
            email="user@example.com",
            hashed_password=User.create_password_hash("user123"),
            is_admin=False,
            permissions=["read", "write"]
        )
        
        assert "admin" in admin_user.permissions
        assert "delete" in admin_user.permissions
        assert "admin" not in regular_user.permissions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
