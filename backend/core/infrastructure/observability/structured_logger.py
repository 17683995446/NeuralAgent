"""结构化日志系统 - 基于 structlog（业界标准）
    
    遵循原则：
    - 站在巨人的肩膀上（使用 structlog）
    - 不重复造轮子
    - 高度模块化
"""
import logging
import sys
from typing import Any, Dict, Optional
from pathlib import Path

import structlog
from pythonjsonlogger import jsonlogger


def setup_structured_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    json_logs: bool = False,
    service_name: str = "neural_agent"
) -> None:
    """设置结构化日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录（可选）
        json_logs: 是否输出 JSON 格式的日志
        service_name: 服务名称
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 配置标准 logging
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除默认处理器
    root_logger.handlers.clear()
    
    # 配置处理器
    processors = []
    
    if json_logs:
        # JSON 格式日志
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
    else:
        # 人类可读格式
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # 添加到根 logger
    console_handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(console_handler)
    
    # 文件日志（可选）
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_path / f"{service_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        root_logger.addHandler(file_handler)
    
    # 配置 structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """获取结构化日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        结构化日志记录器
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """绑定全局上下文到所有日志
    
    Args:
        **kwargs: 要绑定的上下文键值对
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """从全局上下文解绑
    
    Args:
        *keys: 要解绑的键
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """清除所有上下文"""
    structlog.contextvars.clear_contextvars()
