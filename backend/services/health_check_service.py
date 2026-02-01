"""
Health Check Service

Provides comprehensive health checks for all application dependencies
with caching, async support, and configurable timeouts.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx
import redis.asyncio as redis_async
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Try to import Celery
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service: str
    status: HealthStatus
    latency_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "service": self.service,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "error": self.error,
        }


class HealthCheckCache:
    """Cache for health check results to prevent overload"""

    def __init__(self, ttl_seconds: int = 30):
        self._cache: Dict[str, Tuple[HealthCheckResult, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[HealthCheckResult]:
        """Get cached result if not expired"""
        async with self._lock:
            if key in self._cache:
                result, cached_at = self._cache[key]
                if datetime.utcnow() - cached_at < self._ttl:
                    return result
                else:
                    del self._cache[key]
            return None

    async def set(self, key: str, result: HealthCheckResult):
        """Cache a health check result"""
        async with self._lock:
            self._cache[key] = (result, datetime.utcnow())

    async def clear(self):
        """Clear all cached results"""
        async with self._lock:
            self._cache.clear()


class HealthCheckService:
    """
    Service for performing health checks on all application dependencies.
    
    Supports:
    - Database health checks
    - Redis health checks
    - RabbitMQ health checks
    - OpenSearch health checks
    - Celery worker health checks
    - Caching of results
    - Configurable timeouts
    - Parallel async health checks
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        rabbitmq_url: Optional[str] = None,
        opensearch_url: Optional[str] = None,
        cache_ttl_seconds: int = 30,
    ):
        self.database_url = database_url
        self.redis_url = redis_url
        self.rabbitmq_url = rabbitmq_url or "http://localhost:15672/api/health"
        self.opensearch_url = opensearch_url or "http://localhost:9200/_cluster/health"
        self.cache = HealthCheckCache(ttl_seconds=cache_ttl_seconds)
        
        # Default timeouts (in seconds)
        self.timeouts = {
            "database": 5,
            "redis": 3,
            "rabbitmq": 5,
            "opensearch": 5,
            "celery": 10,
        }

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity and health"""
        cache_key = "database"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        start_time = time.time()
        
        if not self.database_url:
            result = HealthCheckResult(
                service="database",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                message="Database URL not configured",
            )
            await self.cache.set(cache_key, result)
            return result

        try:
            # Create async engine for health check
            engine = create_async_engine(
                self.database_url.replace("postgresql://", "postgresql+asyncpg://"),
                echo=False,
                pool_pre_ping=True,
            )
            
            async with engine.connect() as conn:
                await asyncio.wait_for(
                    conn.execute(text("SELECT 1")),
                    timeout=self.timeouts["database"]
                )
            
            await engine.dispose()
            
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Database connection successful",
                details={"url": self.database_url.split("@")[-1]},  # Hide credentials
            )
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Database connection timed out",
                error=f"Timeout after {self.timeouts['database']}s",
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Database connection failed",
                error=str(e),
            )

        await self.cache.set(cache_key, result)
        return result

    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity and health"""
        cache_key = "redis"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        start_time = time.time()
        
        if not self.redis_url:
            result = HealthCheckResult(
                service="redis",
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                message="Redis URL not configured",
            )
            await self.cache.set(cache_key, result)
            return result

        try:
            redis_client = redis_async.from_url(
                self.redis_url,
                socket_connect_timeout=self.timeouts["redis"],
                socket_timeout=self.timeouts["redis"],
            )
            
            await asyncio.wait_for(
                redis_client.ping(),
                timeout=self.timeouts["redis"]
            )
            
            # Get Redis info
            info = await redis_client.info()
            await redis_client.close()
            
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Redis connection successful",
                details={
                    "version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                },
            )
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Redis connection timed out",
                error=f"Timeout after {self.timeouts['redis']}s",
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Redis connection failed",
                error=str(e),
            )

        await self.cache.set(cache_key, result)
        return result

    async def check_rabbitmq(self) -> HealthCheckResult:
        """Check RabbitMQ connectivity and health"""
        cache_key = "rabbitmq"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeouts["rabbitmq"]) as client:
                # Try RabbitMQ Management API health endpoint
                response = await client.get(self.rabbitmq_url)
                response.raise_for_status()
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Parse health response
                health_data = response.json()
                status = HealthStatus.HEALTHY
                
                # Check if status is in response
                if isinstance(health_data, dict):
                    if health_data.get("status") == "ok":
                        status = HealthStatus.HEALTHY
                    elif health_data.get("status") in ["warning", "degraded"]:
                        status = HealthStatus.DEGRADED
                    else:
                        status = HealthStatus.UNHEALTHY
                
                result = HealthCheckResult(
                    service="rabbitmq",
                    status=status,
                    latency_ms=latency_ms,
                    message="RabbitMQ is healthy",
                    details=health_data if isinstance(health_data, dict) else {},
                )
                
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="rabbitmq",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="RabbitMQ connection timed out",
                error=f"Timeout after {self.timeouts['rabbitmq']}s",
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="rabbitmq",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="RabbitMQ connection failed",
                error=str(e),
            )

        await self.cache.set(cache_key, result)
        return result

    async def check_opensearch(self) -> HealthCheckResult:
        """Check OpenSearch connectivity and health"""
        cache_key = "opensearch"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeouts["opensearch"]) as client:
                # Check cluster health
                response = await client.get(self.opensearch_url)
                response.raise_for_status()
                
                latency_ms = (time.time() - start_time) * 1000
                
                health_data = response.json()
                cluster_status = health_data.get("status", "unknown")
                
                # Map OpenSearch status to our status
                if cluster_status == "green":
                    status = HealthStatus.HEALTHY
                elif cluster_status == "yellow":
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY
                
                result = HealthCheckResult(
                    service="opensearch",
                    status=status,
                    latency_ms=latency_ms,
                    message=f"OpenSearch cluster status: {cluster_status}",
                    details={
                        "cluster_name": health_data.get("cluster_name"),
                        "status": cluster_status,
                        "number_of_nodes": health_data.get("number_of_nodes"),
                        "active_shards": health_data.get("active_shards"),
                    },
                )
                
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="opensearch",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="OpenSearch connection timed out",
                error=f"Timeout after {self.timeouts['opensearch']}s",
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="opensearch",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="OpenSearch connection failed",
                error=str(e),
            )

        await self.cache.set(cache_key, result)
        return result

    async def check_celery(self) -> HealthCheckResult:
        """Check Celery workers health"""
        cache_key = "celery"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        start_time = time.time()

        try:
            # Use Celery's inspect to check workers
            inspect = celery_app.control.inspect(timeout=self.timeouts["celery"])
            
            # Get active workers
            active_workers = inspect.active()
            stats = inspect.stats()
            
            latency_ms = (time.time() - start_time) * 1000
            
            if active_workers:
                worker_count = len(active_workers)
                worker_names = list(active_workers.keys())
                
                # Get worker statistics if available
                worker_details = {}
                if stats:
                    for worker_name, worker_stats in stats.items():
                        worker_details[worker_name] = {
                            "processed": worker_stats.get("total", {}).get("tasks", 0),
                            "prefetch_count": worker_stats.get("prefetch_count", 0),
                        }
                
                result = HealthCheckResult(
                    service="celery",
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency_ms,
                    message=f"{worker_count} Celery worker(s) active",
                    details={
                        "worker_count": worker_count,
                        "workers": worker_names,
                        "worker_stats": worker_details,
                    },
                )
            else:
                result = HealthCheckResult(
                    service="celery",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency_ms,
                    message="No active Celery workers found",
                    details={"worker_count": 0},
                )
                
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="celery",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Celery health check timed out",
                error=f"Timeout after {self.timeouts['celery']}s",
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service="celery",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message="Celery health check failed",
                error=str(e),
            )

        await self.cache.set(cache_key, result)
        return result

    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks in parallel.
        
        Returns:
            Dictionary with overall status and individual service results
        """
        start_time = time.time()
        
        # Run all checks in parallel
        results = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_rabbitmq(),
            self.check_opensearch(),
            self.check_celery(),
            return_exceptions=True,
        )

        # Process results
        services = {}
        overall_status = HealthStatus.HEALTHY
        
        for result in results:
            if isinstance(result, Exception):
                # Handle exceptions that weren't caught
                service_name = "unknown"
                services[service_name] = HealthCheckResult(
                    service=service_name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message="Health check failed with exception",
                    error=str(result),
                ).to_dict()
                overall_status = HealthStatus.UNHEALTHY
            else:
                services[result.service] = result.to_dict()
                # Update overall status (worst wins)
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        total_latency_ms = (time.time() - start_time) * 1000

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "total_latency_ms": round(total_latency_ms, 2),
            "services": services,
        }

    async def get_service_health(self, service_name: str) -> Optional[HealthCheckResult]:
        """
        Get health check for a specific service.
        
        Args:
            service_name: Name of the service (database, redis, rabbitmq, opensearch, celery)
            
        Returns:
            HealthCheckResult or None if service not found
        """
        check_methods = {
            "database": self.check_database,
            "redis": self.check_redis,
            "rabbitmq": self.check_rabbitmq,
            "opensearch": self.check_opensearch,
            "celery": self.check_celery,
        }
        
        if service_name not in check_methods:
            return None
            
        return await check_methods[service_name]()

    def set_timeout(self, service: str, timeout_seconds: float):
        """
        Set timeout for a specific service check.
        
        Args:
            service: Service name
            timeout_seconds: Timeout in seconds
        """
        if service in self.timeouts:
            self.timeouts[service] = timeout_seconds

    async def clear_cache(self):
        """Clear all cached health check results"""
        await self.cache.clear()


# Singleton instance
_health_check_service: Optional[HealthCheckService] = None


def get_health_check_service(
    database_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    rabbitmq_url: Optional[str] = None,
    opensearch_url: Optional[str] = None,
) -> HealthCheckService:
    """Get or create the singleton health check service instance"""
    global _health_check_service
    
    if _health_check_service is None:
        _health_check_service = HealthCheckService(
            database_url=database_url,
            redis_url=redis_url,
            rabbitmq_url=rabbitmq_url,
            opensearch_url=opensearch_url,
        )
    
    return _health_check_service
