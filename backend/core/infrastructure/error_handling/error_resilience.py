"""错误处理与重试（使用业界标准库）

- tenacity: 重试库 (https://github.com/jd/tenacity)
- pybreaker: 熔断器 (https://github.com/danielfm/pybreaker)

不重复造轮子，直接使用成熟的开源工具！
"""
from typing import Any, Callable, Optional, Type, Union, List
from functools import wraps
import logging
import time

import tenacity
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState
)
import pybreaker
from pybreaker import CircuitBreaker, CircuitBreakerError

logger = logging.getLogger(__name__)


# ==================== 全局熔断器配置 ====================

# 预定义的熔断器
_default_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

# LLM服务熔断器
llm_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

# 向量存储熔断器
vector_store_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

# API服务熔断器
api_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)


# ==================== 重试装饰器工厂 ====================

def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Optional[Union[Type[Exception], List[Type[Exception]]]] = Exception,
    before_sleep: Optional[Callable[[RetryCallState], None]] = None,
    reraise: bool = True
) -> Callable:
    """标准重试装饰器
    
    使用业界标准的tenacity库
    
    Args:
        max_attempts: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数回退底数
        jitter: 是否添加随机抖动
        retry_exceptions: 需要重试的异常类型
        before_sleep: 重试前的回调
        reraise: 是否重新抛出异常
        
    Returns:
        装饰器函数
    """
    # 配置等待策略
    if jitter:
        wait = wait_exponential_jitter(
            initial=initial_delay,
            max=max_delay,
            exp_base=exponential_base
        )
    else:
        wait = wait_exponential_jitter(
            initial=initial_delay,
            max=max_delay,
            exp_base=exponential_base
        )
    
    # 配置重试条件
    if retry_exceptions:
        if isinstance(retry_exceptions, list):
            retry_cond = retry_if_exception_type(tuple(retry_exceptions))
        else:
            retry_cond = retry_if_exception_type(retry_exceptions)
    else:
        retry_cond = retry_if_exception_type(Exception)
    
    # 默认回调（日志记录）
    if before_sleep is None:
        before_sleep = before_sleep_log(logger, logging.WARNING)
    
    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait,
            retry=retry_cond,
            before_sleep=before_sleep,
            reraise=reraise
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ==================== 常用的预配置重试 ====================

def retry_network(max_attempts: int = 3) -> Callable:
    """网络请求专用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        
    Returns:
        装饰器
    """
    import requests
    
    network_exceptions = [
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError
    ]
    
    return with_retry(
        max_attempts=max_attempts,
        initial_delay=1.0,
        max_delay=10.0,
        retry_exceptions=network_exceptions
    )


def retry_llm(max_attempts: int = 2) -> Callable:
    """LLM调用专用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        
    Returns:
        装饰器
    """
    # 添加LLM相关的异常类型
    llm_exceptions = [
        Exception
    ]
    
    return with_retry(
        max_attempts=max_attempts,
        initial_delay=2.0,
        max_delay=30.0,
        retry_exceptions=llm_exceptions
    )


def retry_vector_store(max_attempts: int = 3) -> Callable:
    """向量存储专用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        
    Returns:
        装饰器
    """
    return with_retry(
        max_attempts=max_attempts,
        initial_delay=0.5,
        max_delay=5.0
    )


# ==================== 熔断器装饰器 ====================

def with_circuit_breaker(
    breaker: Optional[CircuitBreaker] = None,
    fallback: Optional[Callable] = None
) -> Callable:
    """熔断器装饰器
    
    使用pybreaker提供的标准熔断器模式
    
    Args:
        breaker: 熔断器实例，使用默认或指定
        fallback: 熔断时的降级回调函数
        
    Returns:
        装饰器函数
    """
    if breaker is None:
        breaker = _default_breaker
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.warning(f"Circuit breaker open for {func.__name__}: {e}")
                if fallback:
                    return fallback(*args, **kwargs)
                raise
        
        return wrapper
    
    return decorator


# ==================== 组合装饰器 ====================

def retry_with_circuit_breaker(
    breaker: CircuitBreaker,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    fallback: Optional[Callable] = None
) -> Callable:
    """重试 + 熔断器组合装饰器
    
    先重试，再熔断
    
    Args:
        breaker: 熔断器实例
        max_attempts: 最大重试次数
        initial_delay: 初始延迟
        fallback: 降级回调
        
    Returns:
        装饰器函数
    """
    retry_decorator = with_retry(
        max_attempts=max_attempts,
        initial_delay=initial_delay
    )
    
    circuit_decorator = with_circuit_breaker(
        breaker=breaker,
        fallback=fallback
    )
    
    def decorator(func):
        @retry_decorator
        @circuit_decorator
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ==================== LLM专用装饰器 ====================

def robust_llm_call(
    max_attempts: int = 2,
    use_fallback: bool = True
) -> Callable:
    """LLM调用的鲁棒性装饰器
    
    包含：
    - LLM专用熔断器
    - 指数回退重试
    - 可选的降级处理
    
    Args:
        max_attempts: 最大重试次数
        use_fallback: 是否使用降级策略
        
    Returns:
        装饰器函数
    """
    def llm_fallback(*args, **kwargs):
        """LLM调用降级处理"""
        logger.warning(f"LLM call failed, using fallback")
        return {
            "role": "assistant",
            "content": "抱歉，服务暂时不可用，请稍后再试。"
        }
    
    fallback_func = llm_fallback if use_fallback else None
    
    return retry_with_circuit_breaker(
        breaker=llm_breaker,
        max_attempts=max_attempts,
        initial_delay=2.0,
        fallback=fallback_func
    )


# ==================== 工具函数 ====================

def get_circuit_breaker_status(breaker: Optional[CircuitBreaker] = None) -> dict:
    """获取熔断器状态
    
    Args:
        breaker: 熔断器实例
        
    Returns:
        状态信息字典
    """
    if breaker is None:
        breaker = _default_breaker
    
    # 状态映射（兼容不同版本）
    state = "unknown"
    if hasattr(breaker, "state"):
        try:
            if breaker.state == pybreaker.CircuitBreaker.STATE_CLOSED:
                state = "closed"
            elif breaker.state == pybreaker.CircuitBreaker.STATE_OPEN:
                state = "open"
            elif breaker.state == pybreaker.CircuitBreaker.STATE_HALF_OPEN:
                state = "half-open"
        except Exception:
            pass
    
    return {
        "state": state,
        "fail_count": getattr(breaker, "fail_counter", 0),
        "fail_max": getattr(breaker, "fail_max", 5),
        "timeout": getattr(breaker, "reset_timeout", 60)
    }


def get_all_breaker_statuses() -> List[dict]:
    """获取所有预定义熔断器的状态
    
    Returns:
        所有熔断器状态列表
    """
    breakers = [
        ("default", _default_breaker),
        ("llm_service", llm_breaker),
        ("vector_store", vector_store_breaker),
        ("external_api", api_breaker)
    ]
    
    return [
        {
            "name": name,
            **get_circuit_breaker_status(breaker)
        }
        for name, breaker in breakers
    ]


def reset_circuit_breaker(breaker: Optional[CircuitBreaker] = None):
    """重置熔断器
    
    Args:
        breaker: 熔断器实例
    """
    if breaker is None:
        breaker = _default_breaker
    
    if hasattr(breaker, "close"):
        breaker.close()
    logger.info("Circuit breaker reset")


# ==================== 预配置装饰器 ====================

def retry_db(max_attempts: int = 3) -> Callable:
    """数据库专用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        
    Returns:
        装饰器函数
    """
    return with_retry(
        max_attempts=max_attempts,
        initial_delay=0.5,
        max_delay=5.0
    )


def retry_api(max_attempts: int = 2) -> Callable:
    """API专用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        
    Returns:
        装饰器函数
    """
    return with_retry(
        max_attempts=max_attempts,
        initial_delay=0.2,
        max_delay=2.0
    )


def llm_circuit_breaker(fallback: Optional[Callable] = None) -> Callable:
    """LLM专用熔断器装饰器
    
    Args:
        fallback: 降级回调函数
        
    Returns:
        装饰器函数
    """
    return with_circuit_breaker(breaker=llm_breaker, fallback=fallback)


def db_circuit_breaker(fallback: Optional[Callable] = None) -> Callable:
    """数据库专用熔断器装饰器
    
    Args:
        fallback: 降级回调函数
        
    Returns:
        装饰器函数
    """
    return with_circuit_breaker(breaker=vector_store_breaker, fallback=fallback)


def api_circuit_breaker(fallback: Optional[Callable] = None) -> Callable:
    """API专用熔断器装饰器
    
    Args:
        fallback: 降级回调函数
        
    Returns:
        装饰器函数
    """
    return with_circuit_breaker(breaker=api_breaker, fallback=fallback)
