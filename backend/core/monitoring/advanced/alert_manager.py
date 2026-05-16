"""
NeuralAgent - 高级监控与告警系统
企业级监控、告警规则、多渠道通知
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import threading
from collections import deque


class AlertStatus(Enum):
    """告警状态"""
    PENDING = "pending"
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class AlertSeverity(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """通知渠道"""
    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class Alert:
    """告警"""
    id: str
    name: str
    severity: AlertSeverity
    message: str
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """告警规则"""
    id: str
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    channels: List[NotificationChannel]
    enabled: bool = True
    cooldown_seconds: int = 60
    last_triggered: Optional[datetime] = None


@dataclass
class Metric:
    """指标"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


class NotificationProvider(ABC):
    """通知提供者抽象基类"""
    
    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """发送通知"""
        pass


class LogNotificationProvider(NotificationProvider):
    """日志通知提供者"""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
    
    async def send(self, alert: Alert) -> bool:
        self.logger.warning(f"[ALERT] {alert.severity.name}: {alert.name} - {alert.message}")
        return True


class WebhookNotificationProvider(NotificationProvider):
    """Webhook通知提供者"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert) -> bool:
        try:
            # 简化实现
            print(f"[WEBHOOK] Sending to {self.webhook_url}: {alert.name}")
            return True
        except Exception:
            return False


class MetricsStore:
    """指标存储"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics: deque = deque(maxlen=10000)
        self.retention_hours = retention_hours
    
    def record(self, metric: Metric) -> None:
        """记录指标"""
        self.metrics.append(metric)
        self._cleanup()
    
    def query(
        self,
        name: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Metric]:
        """查询指标"""
        if not start:
            start = datetime.now() - timedelta(hours=1)
        if not end:
            end = datetime.now()
        
        results = []
        for metric in reversed(self.metrics):
            if len(results) >= limit:
                break
            if metric.name == name and start <= metric.timestamp <= end:
                results.insert(0, metric)
        return results
    
    def _cleanup(self) -> None:
        """清理过期指标"""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        while self.metrics and self.metrics[0].timestamp < cutoff:
            self.metrics.popleft()


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.metrics_store = MetricsStore()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def register_provider(
        self,
        channel: NotificationChannel,
        provider: NotificationProvider
    ) -> None:
        """注册通知提供者"""
        self.providers[channel] = provider
    
    def register_rule(self, rule: AlertRule) -> None:
        """注册告警规则"""
        self.rules[rule.id] = rule
    
    def create_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """创建告警"""
        import uuid
        alert = Alert(
            id=str(uuid.uuid4()),
            name=name,
            severity=severity,
            message=message,
            status=AlertStatus.PENDING,
            metadata=metadata or {}
        )
        self.alerts[alert.id] = alert
        return alert
    
    async def trigger_alert(self, alert: Alert) -> None:
        """触发告警"""
        alert.status = AlertStatus.ACTIVE
        
        # 根据规则发送通知
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # 简化实现：匹配规则名称
            if rule.name in alert.name:
                for channel in rule.channels:
                    provider = self.providers.get(channel)
                    if provider:
                        await provider.send(alert)
    
    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """确认告警"""
        alert = self.alerts.get(alert_id)
        if alert and alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.now()
            return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        alert = self.alerts.get(alert_id)
        if alert and alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            return True
        return False
    
    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[Alert]:
        """获取告警列表"""
        alerts = list(self.alerts.values())
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        return alerts[:limit]
    
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """记录指标"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics_store.record(metric)
    
    async def start_monitoring(self, check_interval_seconds: int = 30) -> None:
        """启动监控"""
        self._running = True
        
        async def monitor_loop():
            while self._running:
                await self._check_rules()
                await asyncio.sleep(check_interval_seconds)
        
        self._monitor_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self) -> None:
        """停止监控"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _check_rules(self) -> None:
        """检查告警规则"""
        now = datetime.now()
        metrics = self._collect_metrics()
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # 检查冷却时间
            if rule.last_triggered:
                cooldown = timedelta(seconds=rule.cooldown_seconds)
                if now - rule.last_triggered < cooldown:
                    continue
            
            # 检查条件
            try:
                if rule.condition(metrics):
                    rule.last_triggered = now
                    alert = self.create_alert(
                        name=rule.name,
                        severity=rule.severity,
                        message=rule.description,
                        metadata={"rule_id": rule.id}
                    )
                    await self.trigger_alert(alert)
            except Exception:
                continue
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """收集指标（简化版）"""
        import psutil
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available": memory.available,
            "timestamp": datetime.now().isoformat()
        }


def create_alert_manager() -> AlertManager:
    """创建告警管理器"""
    manager = AlertManager()
    
    # 注册默认提供者
    manager.register_provider(
        NotificationChannel.LOG,
        LogNotificationProvider()
    )
    
    # 创建默认规则
    high_cpu_rule = AlertRule(
        id="high_cpu",
        name="High CPU Usage",
        description="CPU usage exceeds 90%",
        condition=lambda m: m.get("cpu_usage", 0) > 90,
        severity=AlertSeverity.WARNING,
        channels=[NotificationChannel.LOG],
        cooldown_seconds=300
    )
    
    high_memory_rule = AlertRule(
        id="high_memory",
        name="High Memory Usage",
        description="Memory usage exceeds 90%",
        condition=lambda m: m.get("memory_usage", 0) > 90,
        severity=AlertSeverity.WARNING,
        channels=[NotificationChannel.LOG],
        cooldown_seconds=300
    )
    
    manager.register_rule(high_cpu_rule)
    manager.register_rule(high_memory_rule)
    
    return manager
