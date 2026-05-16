"""
NeuralAgent API密钥管理系统
提供API密钥的生成、验证和管理功能
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class KeyType(Enum):
    """密钥类型"""
    USER = "user"
    SERVICE = "service"
    ADMIN = "admin"


@dataclass
class APIKey:
    """API密钥模型"""
    id: str
    key_hash: str
    name: str
    key_type: KeyType
    user_id: Optional[str]
    permissions: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    
    def verify_key(self, api_key: str) -> bool:
        """验证密钥"""
        return self.key_hash == self._hash_key(api_key)
    
    @staticmethod
    def _hash_key(api_key: str) -> str:
        """哈希密钥"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_key() -> str:
        """生成新的API密钥"""
        return f"na_{secrets.token_urlsafe(32)}"
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """检查是否有效"""
        return self.is_active and not self.is_expired()


@dataclass
class KeyUsage:
    """密钥使用记录"""
    api_key_id: str
    endpoint: str
    method: str
    timestamp: datetime
    response_time_ms: float
    status_code: int


class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        self._key_usage: Dict[str, List[KeyUsage]] = {}
        self._key_by_hash: Dict[str, str] = {}
    
    def create_key(
        self,
        name: str,
        key_type: KeyType = KeyType.USER,
        user_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """创建新的API密钥"""
        api_key = APIKey.generate_key()
        key_hash = APIKey._hash_key(api_key)
        
        key_id = secrets.token_urlsafe(16)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        if permissions is None:
            permissions = self._get_default_permissions(key_type)
        
        api_key_obj = APIKey(
            id=key_id,
            key_hash=key_hash,
            name=name,
            key_type=key_type,
            user_id=user_id,
            permissions=permissions,
            expires_at=expires_at
        )
        
        self._keys[key_id] = api_key_obj
        self._key_by_hash[key_hash] = key_id
        
        return api_key_obj, api_key
    
    def verify_key(self, api_key: str) -> Optional[APIKey]:
        """验证API密钥"""
        key_hash = APIKey._hash_key(api_key)
        
        key_id = self._key_by_hash.get(key_hash)
        if not key_id:
            return None
        
        api_key_obj = self._keys.get(key_id)
        if not api_key_obj:
            return None
        
        if not api_key_obj.is_valid():
            return None
        
        api_key_obj.last_used_at = datetime.now()
        api_key_obj.usage_count += 1
        
        return api_key_obj
    
    def get_key(self, key_id: str) -> Optional[APIKey]:
        """获取密钥"""
        return self._keys.get(key_id)
    
    def list_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        """列出密钥"""
        keys = list(self._keys.values())
        
        if user_id:
            keys = [k for k in keys if k.user_id == user_id]
        
        return keys
    
    def revoke_key(self, key_id: str) -> bool:
        """撤销密钥"""
        api_key = self._keys.get(key_id)
        if not api_key:
            return False
        
        api_key.is_active = False
        
        if api_key.key_hash in self._key_by_hash:
            del self._key_by_hash[api_key.key_hash]
        
        return True
    
    def delete_key(self, key_id: str) -> bool:
        """删除密钥"""
        api_key = self._keys.get(key_id)
        if not api_key:
            return False
        
        if api_key.key_hash in self._key_by_hash:
            del self._key_by_hash[api_key.key_hash]
        
        del self._keys[key_id]
        
        if key_id in self._key_usage:
            del self._key_usage[key_id]
        
        return True
    
    def record_usage(
        self,
        api_key_id: str,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int
    ):
        """记录密钥使用"""
        if api_key_id not in self._key_usage:
            self._key_usage[api_key_id] = []
        
        usage = KeyUsage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            timestamp=datetime.now(),
            response_time_ms=response_time_ms,
            status_code=status_code
        )
        
        self._key_usage[api_key_id].append(usage)
        
        if len(self._key_usage[api_key_id]) > 1000:
            self._key_usage[api_key_id] = self._key_usage[api_key_id][-1000:]
    
    def get_usage_stats(self, key_id: str) -> Dict[str, Any]:
        """获取使用统计"""
        api_key = self._keys.get(key_id)
        if not api_key:
            return {}
        
        usage_list = self._key_usage.get(key_id, [])
        
        total_requests = len(usage_list)
        avg_response_time = 0
        if total_requests > 0:
            avg_response_time = sum(u.response_time_ms for u in usage_list) / total_requests
        
        status_counts = {}
        for usage in usage_list:
            status_counts[usage.status_code] = status_counts.get(usage.status_code, 0) + 1
        
        return {
            "key_id": key_id,
            "key_name": api_key.name,
            "total_requests": total_requests,
            "usage_count": api_key.usage_count,
            "avg_response_time_ms": avg_response_time,
            "status_codes": status_counts,
            "created_at": api_key.created_at.isoformat(),
            "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None
        }
    
    def _get_default_permissions(self, key_type: KeyType) -> List[str]:
        """获取默认权限"""
        if key_type == KeyType.ADMIN:
            return ["read", "write", "delete", "admin", "manage_keys"]
        elif key_type == KeyType.SERVICE:
            return ["read", "write"]
        else:
            return ["read"]
    
    def cleanup_expired_keys(self) -> int:
        """清理过期密钥"""
        expired_ids = []
        for key_id, key in self._keys.items():
            if key.is_expired():
                expired_ids.append(key_id)
        
        for key_id in expired_ids:
            self.delete_key(key_id)
        
        return len(expired_ids)


_global_key_manager = None


def get_api_key_manager() -> APIKeyManager:
    """获取全局API密钥管理器单例"""
    global _global_key_manager
    if _global_key_manager is None:
        _global_key_manager = APIKeyManager()
    return _global_key_manager
