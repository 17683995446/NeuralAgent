"""
NeuralAgent Python SDK
简洁优雅的API接口，支持同步和异步
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import json

# 可选依赖
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None


@dataclass
class SDKConfig:
    """SDK配置"""
    api_key: str
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    verify_ssl: bool = True


class NeuralAgentSDK:
    """NeuralAgent Python SDK"""
    
    def __init__(self, config: SDKConfig):
        self.config = config
        self.session = None
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_url(self, endpoint: str) -> str:
        """获取完整URL"""
        return f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    # ========== 同步方法 ==========
    
    def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送聊天消息"""
        payload = {
            "query": query,
            "session_id": session_id,
            "agent_id": agent_id,
            **kwargs
        }
        response = requests.post(
            self._get_url("/api/chat"),
            headers=self._headers,
            json=payload,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        response.raise_for_status()
        return response.json()
    
    def create_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建记忆"""
        payload = {
            "content": content,
            "metadata": metadata or {},
            **kwargs
        }
        response = requests.post(
            self._get_url("/api/memory"),
            headers=self._headers,
            json=payload,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        response.raise_for_status()
        return response.json()
    
    def search_memory(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索记忆"""
        params = {
            "query": query,
            "limit": limit,
            **kwargs
        }
        response = requests.get(
            self._get_url("/api/memory/search"),
            headers=self._headers,
            params=params,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        response.raise_for_status()
        return response.json().get("results", [])
    
    def execute_workflow(
        self,
        workflow_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行工作流"""
        payload = {
            "workflow_name": workflow_name,
            "inputs": inputs or {},
            **kwargs
        }
        response = requests.post(
            self._get_url("/api/workflow/execute"),
            headers=self._headers,
            json=payload,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        response.raise_for_status()
        return response.json()
    
    def get_health(self) -> Dict[str, Any]:
        """获取健康状态"""
        response = requests.get(
            self._get_url("/health"),
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        response.raise_for_status()
        return response.json()
    
    # ========== 异步方法 ==========
    
    async def async_chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步发送聊天消息"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "query": query,
            "session_id": session_id,
            "agent_id": agent_id,
            **kwargs
        }
        
        async with self.session.post(
            self._get_url("/api/chat"),
            headers=self._headers,
            json=payload,
            timeout=self.config.timeout
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def async_create_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步创建记忆"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "content": content,
            "metadata": metadata or {},
            **kwargs
        }
        
        async with self.session.post(
            self._get_url("/api/memory"),
            headers=self._headers,
            json=payload,
            timeout=self.config.timeout
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def async_search_memory(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """异步搜索记忆"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        params = {
            "query": query,
            "limit": limit,
            **kwargs
        }
        
        async with self.session.get(
            self._get_url("/api/memory/search"),
            headers=self._headers,
            params=params,
            timeout=self.config.timeout
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return result.get("results", [])
    
    async def async_execute_workflow(
        self,
        workflow_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步执行工作流"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "workflow_name": workflow_name,
            "inputs": inputs or {},
            **kwargs
        }
        
        async with self.session.post(
            self._get_url("/api/workflow/execute"),
            headers=self._headers,
            json=payload,
            timeout=self.config.timeout
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def async_get_health(self) -> Dict[str, Any]:
        """异步获取健康状态"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(
            self._get_url("/health"),
            timeout=self.config.timeout
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def close(self) -> None:
        """关闭异步会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def create_sdk(
    api_key: str,
    base_url: str = "http://localhost:8000",
    **kwargs
) -> NeuralAgentSDK:
    """创建NeuralAgent SDK实例"""
    config = SDKConfig(
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )
    return NeuralAgentSDK(config)
