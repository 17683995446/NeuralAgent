"""
NeuralAgent 日志配置系统
提供结构化日志和追踪功能
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import os
from pathlib import Path
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        log_format: 日志格式
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数量
    """
    # 获取根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 默认日志格式
    if not log_format:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
        )
    
    formatter = logging.Formatter(log_format)
    
    # 控制台输出
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 文件输出
    if enable_file and log_file:
        from logging.handlers import RotatingFileHandler
        
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 避免日志重复传播
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)


def get_application_logger() -> logging.Logger:
    """获取应用主日志记录器"""
    return get_logger("neuralagent")


def log_exception(
    logger: logging.Logger,
    e: Exception,
    level: int = logging.ERROR,
    context: Optional[dict] = None
) -> None:
    """
    记录异常信息
    
    Args:
        logger: 日志记录器
        e: 异常对象
        level: 日志级别
        context: 额外的上下文信息
    """
    message = str(e)
    if context:
        message += f" | Context: {context}"
    
    logger.log(level, message, exc_info=True)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    level: int = logging.INFO,
    extra: Optional[dict] = None
) -> None:
    """
    记录性能信息
    
    Args:
        logger: 日志记录器
        operation: 操作名称
        duration_ms: 持续时间（毫秒）
        level: 日志级别
        extra: 额外信息
    """
    message = f"Performance: {operation} | Duration: {duration_ms:.2f}ms"
    if extra:
        message += f" | Extra: {extra}"
    logger.log(level, message)


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    level: int = logging.INFO
) -> None:
    """
    记录HTTP请求信息
    
    Args:
        logger: 日志记录器
        method: HTTP方法
        path: 请求路径
        status_code: 响应状态码
        duration_ms: 持续时间（毫秒）
        level: 日志级别
    """
    message = (
        f"Request: {method} {path} | "
        f"Status: {status_code} | "
        f"Duration: {duration_ms:.2f}ms"
    )
    logger.log(level, message)


# 全局日志初始化
def init_logging_from_config(config) -> None:
    """从配置对象初始化日志"""
    setup_logging(
        level=getattr(config, "log_level", "INFO"),
        enable_console=True
    )
