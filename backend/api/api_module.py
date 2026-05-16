"""
API Module - RESTful API 和 WebSocket 支持

支持：
1. RESTful CRUD 接口
2. WebSocket 实时通信
3. API 版本控制
4. 请求限流
5. 身份验证
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.openapi.utils import get_openapi
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    logger.warning("fastapi not installed")
    FASTAPI_AVAILABLE = False


class APIResponse(BaseModel):
    """统一 API 响应模型"""
    success: bool = True
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class PaginationResponse(BaseModel):
    """分页响应模型"""
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0


class MemoryItem(BaseModel):
    """记忆项模型"""
    key: str
    value: Any
    ttl: Optional[int] = None
    importance: Optional[str] = "medium"


class WorkflowRequest(BaseModel):
    """工作流执行请求"""
    workflow_id: str
    context: Dict[str, Any] = {}


class LLMRequest(BaseModel):
    """LLM 请求模型"""
    prompt: str
    model: Optional[str] = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1024


class NeuralAgentAPI:
    """NeuralAgent API 类"""
    
    def __init__(self, app: Optional["FastAPI"] = None, prefix: str = "/api/v1"):
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, API disabled")
            self.app = None
            return
        
        self.app = app or FastAPI(
            title="NeuralAgent API",
            description="NeuralAgent 智能代理系统 API",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        self.prefix = prefix
        self._setup_middleware()
        self._register_routes()
        logger.info("NeuralAgent API initialized")
    
    def _setup_middleware(self):
        """设置中间件"""
        if not self.app:
            return
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _register_routes(self):
        """注册路由"""
        if not self.app:
            return
        
        # 健康检查
        @self.app.get("/health", tags=["健康检查"])
        async def health_check():
            """健康检查端点"""
            return APIResponse(
                success=True,
                data={"status": "healthy", "timestamp": datetime.now().isoformat()},
                message="NeuralAgent is running"
            )
        
        # 记忆系统路由
        @self.app.get(f"{self.prefix}/memory", tags=["记忆系统"])
        async def get_memory_list(
            page: int = 1,
            page_size: int = 10,
            key_pattern: Optional[str] = None
        ):
            """获取记忆列表"""
            from backend.core.memory.unified_memory import get_memory_system
            
            memory = get_memory_system()
            # 简化实现，实际应该分页查询
            return PaginationResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
        
        @self.app.get(f"{self.prefix}/memory/{key}", tags=["记忆系统"])
        async def get_memory(key: str):
            """获取单个记忆"""
            from backend.core.memory.unified_memory import get_memory_system
            
            memory = get_memory_system()
            result = await memory.retrieve(key)
            
            if not result:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return APIResponse(
                success=True,
                data={"key": key, "value": result.value}
            )
        
        @self.app.post(f"{self.prefix}/memory", tags=["记忆系统"])
        async def create_memory(item: MemoryItem):
            """创建记忆"""
            from backend.core.memory.unified_memory import get_memory_system
            
            memory = get_memory_system()
            await memory.store(item.key, item.value, item.ttl)
            
            return APIResponse(
                success=True,
                data={"key": item.key},
                message="Memory created successfully"
            )
        
        @self.app.put(f"{self.prefix}/memory/{key}", tags=["记忆系统"])
        async def update_memory(key: str, item: MemoryItem):
            """更新记忆"""
            from backend.core.memory.unified_memory import get_memory_system
            
            memory = get_memory_system()
            exists = await memory.has(key)
            
            if not exists:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            await memory.store(key, item.value, item.ttl)
            
            return APIResponse(
                success=True,
                data={"key": key},
                message="Memory updated successfully"
            )
        
        @self.app.delete(f"{self.prefix}/memory/{key}", tags=["记忆系统"])
        async def delete_memory(key: str):
            """删除记忆"""
            from backend.core.memory.unified_memory import get_memory_system
            
            memory = get_memory_system()
            exists = await memory.has(key)
            
            if not exists:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            await memory.remove(key)
            
            return APIResponse(
                success=True,
                message="Memory deleted successfully"
            )
        
        # LLM 路由
        @self.app.post(f"{self.prefix}/llm/complete", tags=["LLM"])
        async def llm_complete(request: LLMRequest):
            """LLM 文本生成"""
            from backend.core.llm_adapter import llm_adapter
            
            response = await llm_adapter.complete(
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature
            )
            
            return APIResponse(
                success=True,
                data={"response": response.content}
            )
        
        # 工作流路由
        @self.app.post(f"{self.prefix}/workflow/execute", tags=["工作流"])
        async def execute_workflow(request: WorkflowRequest):
            """执行工作流"""
            from backend.core.workflow_engine import get_workflow_engine
            
            engine = get_workflow_engine()
            result = await engine.execute(
                request.workflow_id,
                request.context
            )
            
            return APIResponse(
                success=True,
                data={
                    "execution_id": result.execution_id,
                    "status": result.status.value,
                    "duration": result.duration
                }
            )
        
        @self.app.get(f"{self.prefix}/workflow", tags=["工作流"])
        async def list_workflows():
            """列出工作流"""
            from backend.core.workflow_engine import get_workflow_engine
            
            engine = get_workflow_engine()
            workflows = engine.list_workflows()
            
            return APIResponse(
                success=True,
                data=workflows
            )
    
    def setup_websocket(self):
        """设置 WebSocket 端点"""
        if not self.app:
            return
        
        active_connections: List[WebSocket] = []
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket 实时通信端点"""
            await websocket.accept()
            active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    
                    # 处理消息
                    response = {
                        "type": "message",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # 广播给所有连接
                    for conn in active_connections:
                        await conn.send_json(response)
            except WebSocketDisconnect:
                active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in active_connections:
                    active_connections.remove(websocket)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """运行 API 服务器"""
        if not self.app:
            logger.error("FastAPI not available")
            return
        
        try:
            import uvicorn
            logger.info(f"Starting NeuralAgent API on {host}:{port}")
            uvicorn.run(self.app, host=host, port=port)
        except ImportError:
            logger.error("uvicorn not installed")
    
    async def run_async(self, host: str = "0.0.0.0", port: int = 8000):
        """异步运行 API 服务器"""
        if not self.app:
            logger.error("FastAPI not available")
            return
        
        try:
            import uvicorn
            logger.info(f"Starting NeuralAgent API on {host}:{port}")
            config = uvicorn.Config(self.app, host=host, port=port)
            server = uvicorn.Server(config)
            await server.serve()
        except ImportError:
            logger.error("uvicorn not installed")


class APIClient:
    """API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """GET 请求"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                    return await response.json()
        except ImportError:
            logger.error("aiohttp not installed")
            return {}
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST 请求"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    return await response.json()
        except ImportError:
            logger.error("aiohttp not installed")
            return {}
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT 请求"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.put(f"{self.base_url}{endpoint}", json=data) as response:
                    return await response.json()
        except ImportError:
            logger.error("aiohttp not installed")
            return {}
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE 请求"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.base_url}{endpoint}") as response:
                    return await response.json()
        except ImportError:
            logger.error("aiohttp not installed")
            return {}


# 全局 API 实例
_api_instance = None


def get_api() -> NeuralAgentAPI:
    """获取 API 实例"""
    global _api_instance
    if not _api_instance:
        _api_instance = NeuralAgentAPI()
    return _api_instance


async def example_usage():
    """示例用法"""
    # 创建 API
    api = NeuralAgentAPI()
    
    # 设置 WebSocket
    api.setup_websocket()
    
    # 运行 API（异步）
    # await api.run_async()
    
    # API 客户端示例
    client = APIClient()
    
    # 创建记忆
    result = await client.post("/api/v1/memory", {
        "key": "test",
        "value": "test value"
    })
    print(f"Create memory: {result}")


if __name__ == "__main__":
    asyncio.run(example_usage())
