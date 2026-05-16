#!/usr/bin/env python3
"""系统健康检查工具

定期检查系统各组件的健康状态并生成报告
"""
import sys
import time
import argparse
import json
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: float
    message: str
    details: Dict[str, Any]


class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.checks: List[Dict[str, Any]] = []
    
    def check_api_server(self, url: str = "http://localhost:8000") -> HealthCheckResult:
        """检查API服务器"""
        import requests
        start = time.time()
        
        try:
            response = requests.get(f"{url}/health", timeout=5)
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    component="API Server",
                    status="healthy",
                    latency_ms=latency,
                    message="API server is responding",
                    details=response.json()
                )
            else:
                return HealthCheckResult(
                    component="API Server",
                    status="degraded",
                    latency_ms=latency,
                    message=f"API server returned status {response.status_code}",
                    details={}
                )
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                component="API Server",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                message="Cannot connect to API server",
                details={}
            )
        except Exception as e:
            return HealthCheckResult(
                component="API Server",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                message=f"Error: {str(e)}",
                details={}
            )
    
    def check_database(self, postgres_url: str = "sqlite:///./neural_agent.db") -> HealthCheckResult:
        """检查数据库连接"""
        start = time.time()
        
        try:
            from sqlalchemy import create_engine
            engine = create_engine(postgres_url)
            conn = engine.connect()
            conn.execute("SELECT 1")
            conn.close()
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                component="Database",
                status="healthy",
                latency_ms=latency,
                message="Database connection successful",
                details={}
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthCheckResult(
                component="Database",
                status="degraded",
                latency_ms=latency,
                message=f"Database error: {str(e)}",
                details={}
            )
    
    def check_redis(self, redis_url: str = "redis://localhost:6379") -> HealthCheckResult:
        """检查Redis连接"""
        start = time.time()
        
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=5)
            r.ping()
            latency = (time.time() - start) * 1000
            
            info = r.info()
            
            return HealthCheckResult(
                component="Redis",
                status="healthy",
                latency_ms=latency,
                message="Redis connection successful",
                details={
                    "version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients")
                }
            )
        except ImportError:
            return HealthCheckResult(
                component="Redis",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                message="Redis client not installed",
                details={}
            )
        except Exception as e:
            return HealthCheckResult(
                component="Redis",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                message=f"Redis error: {str(e)}",
                details={}
            )
    
    def check_vector_store(self, store_type: str = "chroma") -> HealthCheckResult:
        """检查向量存储"""
        start = time.time()
        
        try:
            if store_type == "chroma":
                from backend.core.vector_store import ChromaVectorStore
                store = ChromaVectorStore(persist_directory="./chroma_db")
                count = store.count()
                latency = (time.time() - start) * 1000
                
                health = store.health_check()
                
                return HealthCheckResult(
                    component=f"Vector Store ({store_type})",
                    status=health.get("status", "healthy"),
                    latency_ms=latency,
                    message=f"Vector store has {count} vectors",
                    details=health
                )
            else:
                return HealthCheckResult(
                    component=f"Vector Store ({store_type})",
                    status="degraded",
                    latency_ms=(time.time() - start) * 1000,
                    message=f"Unsupported store type: {store_type}",
                    details={}
                )
        except Exception as e:
            return HealthCheckResult(
                component=f"Vector Store ({store_type})",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                message=f"Vector store error: {str(e)}",
                details={}
            )
    
    def check_llm_adapter(self) -> HealthCheckResult:
        """检查LLM适配器"""
        start = time.time()
        
        try:
            from backend.core.llm_adapter import llm_adapter
            
            messages = [{"role": "user", "content": "Hello"}]
            response = llm_adapter.chat_sync(messages)
            
            latency = (time.time() - start) * 1000
            
            return HealthCheckResult(
                component="LLM Adapter",
                status="healthy",
                latency_ms=latency,
                message="LLM adapter responding",
                details={"response_length": len(response)}
            )
        except Exception as e:
            return HealthCheckResult(
                component="LLM Adapter",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                message=f"LLM error: {str(e)}",
                details={}
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """检查系统资源"""
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                status = "degraded"
            
            return HealthCheckResult(
                component="System Resources",
                status=status,
                latency_ms=0,
                message="System resources checked",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent
                }
            )
        except ImportError:
            return HealthCheckResult(
                component="System Resources",
                status="degraded",
                latency_ms=0,
                message="psutil not installed",
                details={}
            )
        except Exception as e:
            return HealthCheckResult(
                component="System Resources",
                status="unhealthy",
                latency_ms=0,
                message=f"Error: {str(e)}",
                details={}
            )
    
    def run_all_checks(self) -> List[HealthCheckResult]:
        """运行所有健康检查"""
        checks = [
            self.check_system_resources,
            self.check_api_server,
            self.check_database,
            self.check_redis,
            self.check_vector_store,
            self.check_llm_adapter
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
                logger.info(f"[{result.status.upper()}] {result.component}: {result.message}")
            except Exception as e:
                logger.error(f"Check failed for {check.__name__}: {e}")
        
        return results
    
    def generate_report(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """生成健康报告"""
        overall_status = "healthy"
        for result in results:
            if result.status == "unhealthy":
                overall_status = "unhealthy"
                break
            elif result.status == "degraded":
                overall_status = "degraded"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "checks": [
                {
                    "component": r.component,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "message": r.message,
                    "details": r.details
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "healthy": sum(1 for r in results if r.status == "healthy"),
                "degraded": sum(1 for r in results if r.status == "degraded"),
                "unhealthy": sum(1 for r in results if r.status == "unhealthy")
            }
        }


def main():
    parser = argparse.ArgumentParser(description="System Health Check Tool")
    parser.add_argument("--output", "-o", help="Output file path (JSON)")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text",
                        help="Output format")
    parser.add_argument("--watch", "-w", action="store_true",
                        help="Watch mode (continuous monitoring)")
    parser.add_argument("--interval", "-i", type=int, default=30,
                        help="Watch mode check interval (seconds)")
    
    args = parser.parse_args()
    
    checker = SystemHealthChecker()
    
    if args.watch:
        logger.info(f"Starting continuous health monitoring (interval: {args.interval}s)")
        try:
            while True:
                results = checker.run_all_checks()
                report = checker.generate_report(results)
                
                if args.format == "json":
                    print(json.dumps(report, indent=2))
                else:
                    print_report(report)
                
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Health monitoring stopped")
    else:
        results = checker.run_all_checks()
        report = checker.generate_report(results)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {args.output}")
        
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print_report(report)


def print_report(report: Dict[str, Any]):
    """打印文本格式的报告"""
    print("\n" + "=" * 60)
    print(f"System Health Report - {report['timestamp']}")
    print("=" * 60)
    
    overall = report['overall_status']
    status_icon = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌"
    }
    
    print(f"\nOverall Status: {status_icon.get(overall, '')} {overall.upper()}")
    print(f"Summary: {report['summary']['healthy']} healthy, "
          f"{report['summary']['degraded']} degraded, "
          f"{report['summary']['unhealthy']} unhealthy")
    
    print("\n" + "-" * 60)
    print("Component Status:")
    print("-" * 60)
    
    for check in report['checks']:
        icon = status_icon.get(check['status'], '❓')
        print(f"{icon} {check['component']:<30} {check['status']:<10} "
              f"{check['latency_ms']:.1f}ms")
        print(f"   {check['message']}")
        
        if check['details']:
            for key, value in list(check['details'].items())[:3]:
                print(f"   - {key}: {value}")
        print()


if __name__ == "__main__":
    main()
