"""
NeuralAgent - 管理仪表板API
提供管理界面的后端API
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel


class DashboardStats(BaseModel):
    """仪表板统计"""
    total_agents: int
    active_agents: int
    total_memories: int
    total_queries: int
    avg_response_time_ms: float
    uptime_seconds: float
    cpu_usage: float
    memory_usage: float


class AgentInfo(BaseModel):
    """Agent信息"""
    id: str
    name: str
    type: str
    status: str
    created_at: str
    last_active: Optional[str] = None
    tasks_completed: int = 0
    config: Dict[str, Any]


class WorkflowInfo(BaseModel):
    """工作流信息"""
    id: str
    name: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    steps: List[Dict[str, Any]] = []


class LogEntry(BaseModel):
    """日志条目"""
    id: str
    timestamp: str
    level: str
    message: str
    component: Optional[str] = None
    metadata: Dict[str, Any] = {}


# 创建路由
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# 内存存储（简化版）
class DashboardDataStore:
    """仪表板数据存储"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.logs: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {
            "total_queries": 0,
            "response_times": []
        }


store = DashboardDataStore()


@dashboard_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """获取仪表板统计数据"""
    import psutil
    
    uptime = (datetime.now() - store.start_time).total_seconds()
    
    total_agents = len(store.agents)
    active_agents = len([a for a in store.agents.values() if a.get("status") == "active"])
    
    avg_response_time = 0.0
    if store.stats["response_times"]:
        avg_response_time = sum(store.stats["response_times"]) / len(store.stats["response_times"])
    
    cpu_usage = psutil.cpu_percent() if hasattr(psutil, "cpu_percent") else 0.0
    memory = psutil.virtual_memory() if hasattr(psutil, "virtual_memory") else None
    memory_usage = memory.percent if memory else 0.0
    
    return DashboardStats(
        total_agents=total_agents,
        active_agents=active_agents,
        total_memories=0,  # 可扩展
        total_queries=store.stats["total_queries"],
        avg_response_time_ms=avg_response_time,
        uptime_seconds=uptime,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage
    )


@dashboard_router.get("/agents", response_model=List[AgentInfo])
async def list_agents(
    status: Optional[str] = None,
    limit: int = 100
):
    """列出所有Agent"""
    agents_list = []
    
    for agent_id, agent_data in store.agents.items():
        if status and agent_data.get("status") != status:
            continue
        
        agents_list.append(AgentInfo(
            id=agent_id,
            name=agent_data.get("name", ""),
            type=agent_data.get("type", ""),
            status=agent_data.get("status", "unknown"),
            created_at=agent_data.get("created_at", ""),
            last_active=agent_data.get("last_active"),
            tasks_completed=agent_data.get("tasks_completed", 0),
            config=agent_data.get("config", {})
        ))
    
    return agents_list[:limit]


@dashboard_router.get("/workflows", response_model=List[WorkflowInfo])
async def list_workflows(
    status: Optional[str] = None,
    limit: int = 100
):
    """列出所有工作流"""
    workflows_list = []
    
    for wf_id, wf_data in store.workflows.items():
        if status and wf_data.get("status") != status:
            continue
        
        workflows_list.append(WorkflowInfo(
            id=wf_id,
            name=wf_data.get("name", ""),
            status=wf_data.get("status", "unknown"),
            created_at=wf_data.get("created_at", ""),
            started_at=wf_data.get("started_at"),
            completed_at=wf_data.get("completed_at"),
            steps=wf_data.get("steps", [])
        ))
    
    return workflows_list[:limit]


@dashboard_router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    level: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = 100
):
    """获取日志"""
    logs_list = []
    
    for log_data in reversed(store.logs):
        if level and log_data.get("level") != level.upper():
            continue
        if component and log_data.get("component") != component:
            continue
        
        logs_list.append(LogEntry(
            id=log_data.get("id", ""),
            timestamp=log_data.get("timestamp", ""),
            level=log_data.get("level", "INFO"),
            message=log_data.get("message", ""),
            component=log_data.get("component"),
            metadata=log_data.get("metadata", {})
        ))
        
        if len(logs_list) >= limit:
            break
    
    return logs_list


@dashboard_router.post("/agents")
async def create_agent(name: str, agent_type: str, config: Dict[str, Any] = {}):
    """创建Agent"""
    import uuid
    
    agent_id = str(uuid.uuid4())
    agent_data = {
        "id": agent_id,
        "name": name,
        "type": agent_type,
        "status": "inactive",
        "created_at": datetime.now().isoformat(),
        "tasks_completed": 0,
        "config": config
    }
    
    store.agents[agent_id] = agent_data
    
    # 记录日志
    add_log("INFO", f"Created agent: {name} ({agent_id})", "dashboard")
    
    return {"id": agent_id, "success": True}


@dashboard_router.post("/agents/{agent_id}/activate")
async def activate_agent(agent_id: str):
    """激活Agent"""
    if agent_id not in store.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    store.agents[agent_id]["status"] = "active"
    store.agents[agent_id]["last_active"] = datetime.now().isoformat()
    
    add_log("INFO", f"Activated agent: {agent_id}", "dashboard")
    
    return {"success": True}


def add_log(level: str, message: str, component: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """添加日志条目"""
    import uuid
    
    log_data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "level": level.upper(),
        "message": message,
        "component": component,
        "metadata": metadata or {}
    }
    
    store.logs.append(log_data)
    
    # 只保留最近1000条日志
    if len(store.logs) > 1000:
        store.logs = store.logs[-1000:]
