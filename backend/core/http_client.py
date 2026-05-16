"""
NeuralAgent - HTTP Client with Connection Pool
高性能HTTP客户端：连接池、重试、超时、异步
"""
import asyncio
import time
from typing import (
    Dict,
    Any,
    Optional,
    Union,
    Callable,
    Awaitable,
    List
)
from dataclasses import dataclass, field
from enum import Enum
import logging


try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None


class HTTPMethod(Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HTTPClientConfig:
    """HTTP客户端配置"""
    timeout: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 5.0
    retries: int = 3
    retry_delay: float = 1.0
    retry_backoff_factor: float = 2.0
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    follow_redirects: bool = True
    verify_ssl: bool = True
    proxy: Optional[str] = None
    default_headers: Dict[str, str] = field(default_factory=dict)
    base_url: Optional[str] = None


@dataclass
class HTTPResponse:
    """HTTP响应包装"""
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Any] = None
    elapsed_ms: float = 0.0
    url: str = ""
    request_id: str = ""


class HTTPClientError(Exception):
    """HTTP客户端错误基类"""
    pass


class HTTPTimeoutError(HTTPClientError):
    """HTTP超时错误"""
    pass


class HTTPStatusError(HTTPClientError):
    """HTTP状态错误"""
    def __init__(self, message: str, status_code: int, response: Optional[HTTPResponse] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class HTTPClient:
    """高级HTTP客户端"""
    
    def __init__(self, config: Optional[HTTPClientConfig] = None):
        if not HAS_HTTPX:
            raise ImportError("httpx is required. Install with: pip install httpx")
        
        self.config = config or HTTPClientConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None
        self.logger = logging.getLogger(__name__)
        self._request_count = 0
    
    async def __aenter__(self) -> "HTTPClient":
        await self._init_async_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def __enter__(self) -> "HTTPClient":
        self._init_sync_client()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_sync()
    
    async def _init_async_client(self):
        """初始化异步客户端"""
        if self._client is None:
            timeout = httpx.Timeout(
                timeout=self.config.timeout,
                connect=self.config.connect_timeout,
                read=self.config.read_timeout,
                write=self.config.write_timeout
            )
            
            limits = httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_keepalive_connections,
                keepalive_expiry=self.config.keepalive_expiry
            )
            
            self._client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=self.config.follow_redirects,
                verify=self.config.verify_ssl,
                proxy=self.config.proxy,
                base_url=self.config.base_url
            )
    
    def _init_sync_client(self):
        """初始化同步客户端"""
        if self._sync_client is None:
            timeout = httpx.Timeout(
                timeout=self.config.timeout,
                connect=self.config.connect_timeout,
                read=self.config.read_timeout,
                write=self.config.write_timeout
            )
            
            limits = httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_keepalive_connections,
                keepalive_expiry=self.config.keepalive_expiry
            )
            
            self._sync_client = httpx.Client(
                timeout=timeout,
                limits=limits,
                follow_redirects=self.config.follow_redirects,
                verify=self.config.verify_ssl,
                proxy=self.config.proxy,
                base_url=self.config.base_url
            )
    
    async def close(self):
        """关闭异步客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def close_sync(self):
        """关闭同步客户端"""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
    
    def _get_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        self._request_count += 1
        return f"req-{uuid.uuid4().hex[:8]}-{self._request_count}"
    
    async def _request_with_retry(
        self,
        method: HTTPMethod,
        url: str,
        **kwargs
    ) -> HTTPResponse:
        """带重试的异步请求"""
        await self._init_async_client()
        
        last_exception = None
        request_id = self._get_request_id()
        start_time = time.time()
        
        headers = kwargs.pop("headers", {})
        headers.update(self.config.default_headers)
        headers["X-Request-ID"] = request_id
        
        for attempt in range(1, self.config.retries + 1):
            try:
                self.logger.debug(
                    f"HTTP Request {request_id}: {method.value} {url} "
                    f"(Attempt {attempt}/{self.config.retries})"
                )
                
                response = await self._client.request(
                    method=method.value,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                
                elapsed = (time.time() - start_time) * 1000
                
                if response.status_code in self.config.retry_status_codes and attempt < self.config.retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff_factor ** (attempt - 1))
                    self.logger.warning(
                        f"HTTP {request_id}: Status {response.status_code}, "
                        f"retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                
                result = self._wrap_response(response, elapsed, url, request_id)
                
                if response.status_code >= 400:
                    raise HTTPStatusError(
                        f"HTTP {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response=result
                    )
                
                return result
                
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.config.retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff_factor ** (attempt - 1))
                    self.logger.warning(f"HTTP {request_id}: Timeout, retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    raise HTTPTimeoutError(f"Request timed out after {self.config.timeout}s") from e
            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self.config.retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff_factor ** (attempt - 1))
                    self.logger.warning(f"HTTP {request_id}: Error {e}, retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    raise HTTPClientError(f"HTTP request failed: {e}") from e
        
        raise last_exception
    
    def _request_with_retry_sync(
        self,
        method: HTTPMethod,
        url: str,
        **kwargs
    ) -> HTTPResponse:
        """带重试的同步请求"""
        self._init_sync_client()
        
        last_exception = None
        request_id = self._get_request_id()
        start_time = time.time()
        
        headers = kwargs.pop("headers", {})
        headers.update(self.config.default_headers)
        headers["X-Request-ID"] = request_id
        
        for attempt in range(1, self.config.retries + 1):
            try:
                self.logger.debug(
                    f"HTTP Request {request_id}: {method.value} {url} "
                    f"(Attempt {attempt}/{self.config.retries})"
                )
                
                response = self._sync_client.request(
                    method=method.value,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                
                elapsed = (time.time() - start_time) * 1000
                
                if response.status_code in self.config.retry_status_codes and attempt < self.config.retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff_factor ** (attempt - 1))
                    self.logger.warning(
                        f"HTTP {request_id}: Status {response.status_code}, "
                        f"retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    continue
                
                result = self._wrap_response(response, elapsed, url, request_id)
                
                if response.status_code >= 400:
                    raise HTTPStatusError(
                        f"HTTP {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response=result
                    )
                
                return result
                
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.config.retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff_factor ** (attempt - 1))
                    self.logger.warning(f"HTTP {request_id}: Timeout, retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    raise HTTPTimeoutError(f"Request timed out after {self.config.timeout}s") from e
            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self.config.retries:
                    delay = self.config.retry_delay * (self.config.retry_backoff_factor ** (attempt - 1))
                    self.logger.warning(f"HTTP {request_id}: Error {e}, retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    raise HTTPClientError(f"HTTP request failed: {e}") from e
        
        raise last_exception
    
    def _wrap_response(
        self,
        response: Union[httpx.Response, Any],
        elapsed: float,
        url: str,
        request_id: str
    ) -> HTTPResponse:
        """包装HTTP响应"""
        json_data = None
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                json_data = response.json()
        except Exception:
            pass
        
        return HTTPResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            text=response.text,
            json_data=json_data,
            elapsed_ms=elapsed,
            url=url,
            request_id=request_id
        )
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """GET请求（异步）"""
        return await self._request_with_retry(
            HTTPMethod.GET, url, params=params, **kwargs
        )
    
    async def post(
        self,
        url: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """POST请求（异步）"""
        return await self._request_with_retry(
            HTTPMethod.POST, url, json=json, data=data, **kwargs
        )
    
    async def put(
        self,
        url: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """PUT请求（异步）"""
        return await self._request_with_retry(
            HTTPMethod.PUT, url, json=json, data=data, **kwargs
        )
    
    async def patch(
        self,
        url: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """PATCH请求（异步）"""
        return await self._request_with_retry(
            HTTPMethod.PATCH, url, json=json, data=data, **kwargs
        )
    
    async def delete(
        self,
        url: str,
        **kwargs
    ) -> HTTPResponse:
        """DELETE请求（异步）"""
        return await self._request_with_retry(
            HTTPMethod.DELETE, url, **kwargs
        )
    
    def get_sync(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """GET请求（同步）"""
        return self._request_with_retry_sync(
            HTTPMethod.GET, url, params=params, **kwargs
        )
    
    def post_sync(
        self,
        url: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """POST请求（同步）"""
        return self._request_with_retry_sync(
            HTTPMethod.POST, url, json=json, data=data, **kwargs
        )
    
    def put_sync(
        self,
        url: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """PUT请求（同步）"""
        return self._request_with_retry_sync(
            HTTPMethod.PUT, url, json=json, data=data, **kwargs
        )
    
    def patch_sync(
        self,
        url: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """PATCH请求（同步）"""
        return self._request_with_retry_sync(
            HTTPMethod.PATCH, url, json=json, data=data, **kwargs
        )
    
    def delete_sync(
        self,
        url: str,
        **kwargs
    ) -> HTTPResponse:
        """DELETE请求（同步）"""
        return self._request_with_retry_sync(
            HTTPMethod.DELETE, url, **kwargs
        )


_global_client: Optional[HTTPClient] = None


def get_http_client(config: Optional[HTTPClientConfig] = None) -> HTTPClient:
    """获取全局HTTP客户端"""
    global _global_client
    if _global_client is None:
        _global_client = HTTPClient(config)
    return _global_client


def set_http_client_config(config: HTTPClientConfig) -> None:
    """设置全局HTTP客户端配置"""
    global _global_client
    _global_client = HTTPClient(config)
