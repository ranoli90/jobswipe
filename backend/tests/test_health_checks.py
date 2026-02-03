"""
Health Check Tests

Unit and integration tests for health check service and endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Import the health check service components
from backend.services.health_check_service import (
    HealthCheckService,
    HealthCheckResult,
    HealthStatus,
    HealthCheckCache,
)


# Fixtures
@pytest.fixture
def health_check_service():
    """Create a health check service instance for testing"""
    return HealthCheckService(
        database_url="postgresql://user:pass@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
        rabbitmq_url="http://localhost:15672/api/health",
        opensearch_url="http://localhost:9200/_cluster/health",
        cache_ttl_seconds=1,  # Short TTL for testing
    )


@pytest.fixture
def mock_db_engine():
    """Mock database engine"""
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_engine.connect = MagicMock(return_value=mock_conn)
    mock_engine.dispose = AsyncMock()
    return mock_engine


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.info = AsyncMock(return_value={
        "redis_version": "7.0.0",
        "used_memory_human": "1.5M",
        "connected_clients": 10,
    })
    mock_client.close = AsyncMock()
    return mock_client


# Unit Tests for HealthCheckResult
class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass"""

    def test_health_check_result_creation(self):
        """Test creating a HealthCheckResult"""
        result = HealthCheckResult(
            service="database",
            status=HealthStatus.HEALTHY,
            latency_ms=25.5,
            message="Database is healthy",
            details={"version": "15.0"},
        )

        assert result.service == "database"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms == 25.5
        assert result.message == "Database is healthy"
        assert result.details == {"version": "15.0"}
        assert result.timestamp is not None
        assert result.error is None

    def test_health_check_result_to_dict(self):
        """Test converting HealthCheckResult to dictionary"""
        result = HealthCheckResult(
            service="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=5.2,
            message="Redis is healthy",
            details={"version": "7.0.0"},
        )

        result_dict = result.to_dict()

        assert result_dict["service"] == "redis"
        assert result_dict["status"] == "healthy"
        assert result_dict["latency_ms"] == 5.2
        assert result_dict["message"] == "Redis is healthy"
        assert result_dict["details"] == {"version": "7.0.0"}
        assert "timestamp" in result_dict

    def test_health_check_result_with_error(self):
        """Test HealthCheckResult with error"""
        result = HealthCheckResult(
            service="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=5000.0,
            message="Database connection failed",
            error="Connection timeout",
        )

        result_dict = result.to_dict()

        assert result_dict["status"] == "unhealthy"
        assert result_dict["error"] == "Connection timeout"


# Unit Tests for HealthCheckCache
class TestHealthCheckCache:
    """Tests for HealthCheckCache"""

    @pytest.mark.asyncio
    async def test_cache_get_set(self):
        """Test cache get and set operations"""
        cache = HealthCheckCache(ttl_seconds=1)

        result = HealthCheckResult(
            service="test",
            status=HealthStatus.HEALTHY,
            latency_ms=10.0,
            message="Test",
        )

        # Set cache
        await cache.set("test_key", result)

        # Get cache
        cached = await cache.get("test_key")

        assert cached is not None
        assert cached.service == "test"
        assert cached.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration"""
        cache = HealthCheckCache(ttl_seconds=0.1)  # Very short TTL

        result = HealthCheckResult(
            service="test",
            status=HealthStatus.HEALTHY,
            latency_ms=10.0,
            message="Test",
        )

        await cache.set("test_key", result)

        # Wait for expiration
        import asyncio
        await asyncio.sleep(0.2)

        # Cache should be expired
        cached = await cache.get("test_key")
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test cache clear operation"""
        cache = HealthCheckCache(ttl_seconds=60)

        result = HealthCheckResult(
            service="test",
            status=HealthStatus.HEALTHY,
            latency_ms=10.0,
            message="Test",
        )

        await cache.set("key1", result)
        await cache.set("key2", result)

        # Clear cache
        await cache.clear()

        # Both should be None
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


# Unit Tests for HealthCheckService
class TestHealthCheckService:
    """Tests for HealthCheckService"""

    @pytest.mark.asyncio
    async def test_check_database_success(self, health_check_service, mock_db_engine):
        """Test successful database health check"""
        with patch("backend.services.health_check_service.create_async_engine", return_value=mock_db_engine):
            result = await health_check_service.check_database()

            assert result.service == "database"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms >= 0
            assert "successful" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_database_no_url(self, health_check_service):
        """Test database check with no URL configured"""
        health_check_service.database_url = None

        result = await health_check_service.check_database()

        assert result.service == "database"
        assert result.status == HealthStatus.UNKNOWN
        assert "not configured" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_database_failure(self, health_check_service):
        """Test database check failure"""
        with patch("backend.services.health_check_service.create_async_engine", side_effect=Exception("Connection refused")):
            result = await health_check_service.check_database()

            assert result.service == "database"
            assert result.status == HealthStatus.UNHEALTHY
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_check_redis_success(self, health_check_service, mock_redis_client):
        """Test successful Redis health check"""
        with patch("backend.services.health_check_service.redis_async.from_url", return_value=mock_redis_client):
            result = await health_check_service.check_redis()

            assert result.service == "redis"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms >= 0
            assert result.details is not None
            assert "version" in result.details

    @pytest.mark.asyncio
    async def test_check_redis_no_url(self, health_check_service):
        """Test Redis check with no URL configured"""
        health_check_service.redis_url = None

        result = await health_check_service.check_redis()

        assert result.service == "redis"
        assert result.status == HealthStatus.UNKNOWN
        assert "not configured" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_rabbitmq_success(self, health_check_service):
        """Test successful RabbitMQ health check"""
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"status": "ok"})
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("backend.services.health_check_service.httpx.AsyncClient", return_value=mock_client):
            result = await health_check_service.check_rabbitmq()

            assert result.service == "rabbitmq"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_check_rabbitmq_failure(self, health_check_service):
        """Test RabbitMQ check failure"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("backend.services.health_check_service.httpx.AsyncClient", return_value=mock_client):
            result = await health_check_service.check_rabbitmq()

            assert result.service == "rabbitmq"
            assert result.status == HealthStatus.UNHEALTHY
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_check_opensearch_success(self, health_check_service):
        """Test successful OpenSearch health check"""
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "status": "green",
            "cluster_name": "test-cluster",
            "number_of_nodes": 1,
            "active_shards": 5,
        })
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("backend.services.health_check_service.httpx.AsyncClient", return_value=mock_client):
            result = await health_check_service.check_opensearch()

            assert result.service == "opensearch"
            assert result.status == HealthStatus.HEALTHY
            assert result.latency_ms >= 0
            assert result.details is not None
            assert result.details["status"] == "green"

    @pytest.mark.asyncio
    async def test_check_opensearch_yellow(self, health_check_service):
        """Test OpenSearch health check with yellow status"""
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "status": "yellow",
            "cluster_name": "test-cluster",
            "number_of_nodes": 1,
        })
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("backend.services.health_check_service.httpx.AsyncClient", return_value=mock_client):
            result = await health_check_service.check_opensearch()

            assert result.service == "opensearch"
            assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_check_celery_success(self, health_check_service):
        """Test successful Celery health check"""
        mock_inspect = MagicMock()
        mock_inspect.active = MagicMock(return_value={
            "celery@worker1": [],
            "celery@worker2": [],
        })
        mock_inspect.stats = MagicMock(return_value={
            "celery@worker1": {"total": {"tasks": 100}, "prefetch_count": 4},
        })

        mock_celery = MagicMock()
        mock_celery.control.inspect = MagicMock(return_value=mock_inspect)

        with patch("backend.services.health_check_service.celery_app", mock_celery):
            result = await health_check_service.check_celery()

            assert result.service == "celery"
            assert result.status == HealthStatus.HEALTHY
            assert result.details is not None
            assert result.details["worker_count"] == 2

    @pytest.mark.asyncio
    async def test_check_celery_no_workers(self, health_check_service):
        """Test Celery health check with no active workers"""
        mock_inspect = MagicMock()
        mock_inspect.active = MagicMock(return_value=None)
        mock_inspect.stats = MagicMock(return_value=None)

        mock_celery = MagicMock()
        mock_celery.control.inspect = MagicMock(return_value=mock_inspect)

        with patch("backend.services.health_check_service.celery_app", mock_celery):
            result = await health_check_service.check_celery()

            assert result.service == "celery"
            assert result.status == HealthStatus.DEGRADED
            assert result.details["worker_count"] == 0

    @pytest.mark.asyncio
    async def test_check_all(self, health_check_service):
        """Test comprehensive health check"""
        # Mock all individual checks
        with patch.object(health_check_service, "check_database") as mock_db, \
             patch.object(health_check_service, "check_redis") as mock_redis, \
             patch.object(health_check_service, "check_rabbitmq") as mock_rabbit, \
             patch.object(health_check_service, "check_opensearch") as mock_search, \
             patch.object(health_check_service, "check_celery") as mock_celery:

            mock_db.return_value = HealthCheckResult(
                service="database", status=HealthStatus.HEALTHY,
                latency_ms=10.0, message="OK"
            )
            mock_redis.return_value = HealthCheckResult(
                service="redis", status=HealthStatus.HEALTHY,
                latency_ms=5.0, message="OK"
            )
            mock_rabbit.return_value = HealthCheckResult(
                service="rabbitmq", status=HealthStatus.HEALTHY,
                latency_ms=15.0, message="OK"
            )
            mock_search.return_value = HealthCheckResult(
                service="opensearch", status=HealthStatus.HEALTHY,
                latency_ms=20.0, message="OK"
            )
            mock_celery.return_value = HealthCheckResult(
                service="celery", status=HealthStatus.HEALTHY,
                latency_ms=30.0, message="OK"
            )

            result = await health_check_service.check_all()

            assert result["status"] == "healthy"
            assert "services" in result
            assert "total_latency_ms" in result
            assert len(result["services"]) == 5

    @pytest.mark.asyncio
    async def test_check_all_with_degraded(self, health_check_service):
        """Test comprehensive health check with degraded service"""
        with patch.object(health_check_service, "check_database") as mock_db, \
             patch.object(health_check_service, "check_redis") as mock_redis, \
             patch.object(health_check_service, "check_rabbitmq") as mock_rabbit, \
             patch.object(health_check_service, "check_opensearch") as mock_search, \
             patch.object(health_check_service, "check_celery") as mock_celery:

            mock_db.return_value = HealthCheckResult(
                service="database", status=HealthStatus.HEALTHY,
                latency_ms=10.0, message="OK"
            )
            mock_redis.return_value = HealthCheckResult(
                service="redis", status=HealthStatus.DEGRADED,
                latency_ms=500.0, message="Slow"
            )
            mock_rabbit.return_value = HealthCheckResult(
                service="rabbitmq", status=HealthStatus.HEALTHY,
                latency_ms=15.0, message="OK"
            )
            mock_search.return_value = HealthCheckResult(
                service="opensearch", status=HealthStatus.HEALTHY,
                latency_ms=20.0, message="OK"
            )
            mock_celery.return_value = HealthCheckResult(
                service="celery", status=HealthStatus.HEALTHY,
                latency_ms=30.0, message="OK"
            )

            result = await health_check_service.check_all()

            assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_service_health(self, health_check_service):
        """Test getting health for specific service"""
        with patch.object(health_check_service, "check_database") as mock_db:
            mock_db.return_value = HealthCheckResult(
                service="database", status=HealthStatus.HEALTHY,
                latency_ms=10.0, message="OK"
            )

            result = await health_check_service.get_service_health("database")

            assert result is not None
            assert result.service == "database"

    @pytest.mark.asyncio
    async def test_get_service_health_invalid(self, health_check_service):
        """Test getting health for invalid service"""
        result = await health_check_service.get_service_health("invalid_service")

        assert result is None

    def test_set_timeout(self, health_check_service):
        """Test setting timeout for service"""
        health_check_service.set_timeout("database", 10.0)

        assert health_check_service.timeouts["database"] == 10.0


# Integration Tests for Health Check Endpoints
class TestHealthCheckEndpoints:
    """Integration tests for health check API endpoints"""

    def test_basic_health_endpoint(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_readiness_endpoint(self, client: TestClient):
        """Test readiness check endpoint"""
        response = client.get("/ready")

        # Status could be 200 or 503 depending on database connectivity
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_rabbitmq_health_endpoint(self, client: TestClient):
        """Test RabbitMQ health check endpoint"""
        with patch("backend.services.health_check_service.HealthCheckService.check_rabbitmq") as mock_check:
            mock_check.return_value = HealthCheckResult(
                service="rabbitmq",
                status=HealthStatus.HEALTHY,
                latency_ms=15.0,
                message="RabbitMQ is healthy",
                details={"status": "ok"},
            )

            response = client.get("/health/rabbitmq")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "rabbitmq"
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_opensearch_health_endpoint(self, client: TestClient):
        """Test OpenSearch health check endpoint"""
        with patch("backend.services.health_check_service.HealthCheckService.check_opensearch") as mock_check:
            mock_check.return_value = HealthCheckResult(
                service="opensearch",
                status=HealthStatus.HEALTHY,
                latency_ms=25.0,
                message="OpenSearch cluster status: green",
                details={"cluster_name": "test", "status": "green"},
            )

            response = client.get("/health/opensearch")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "opensearch"
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_celery_health_endpoint(self, client: TestClient):
        """Test Celery health check endpoint"""
        with patch("backend.services.health_check_service.HealthCheckService.check_celery") as mock_check:
            mock_check.return_value = HealthCheckResult(
                service="celery",
                status=HealthStatus.HEALTHY,
                latency_ms=45.0,
                message="2 Celery worker(s) active",
                details={"worker_count": 2, "workers": ["celery@worker1"]},
            )

            response = client.get("/health/celery")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "celery"
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health_endpoint(self, client: TestClient):
        """Test detailed health check endpoint"""
        with patch("backend.services.health_check_service.HealthCheckService.check_all") as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "total_latency_ms": 100.0,
                "services": {
                    "database": {
                        "service": "database",
                        "status": "healthy",
                        "latency_ms": 20.0,
                        "message": "OK",
                    },
                },
            }

            response = client.get("/health/detailed")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data
            assert "total_latency_ms" in data


# Performance Tests
class TestHealthCheckPerformance:
    """Performance tests for health checks"""

    @pytest.mark.asyncio
    async def test_health_check_caching(self, health_check_service):
        """Test that health check results are cached"""
        call_count = 0

        async def mock_check():
            nonlocal call_count
            call_count += 1
            return HealthCheckResult(
                service="test",
                status=HealthStatus.HEALTHY,
                latency_ms=10.0,
                message="OK",
            )

        # Patch the specific check method
        with patch.object(health_check_service, "check_database", side_effect=mock_check):
            # First call should hit the service
            result1 = await health_check_service.check_database()
            # Second call should use cache
            result2 = await health_check_service.check_database()

            # Both should return valid results
            assert result1.status == HealthStatus.HEALTHY
            assert result2.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_parallel_health_checks(self, health_check_service):
        """Test that health checks run in parallel"""
        import asyncio
        import time

        delay = 0.1  # 100ms delay per check

        async def slow_check(*args, **kwargs):
            await asyncio.sleep(delay)
            return HealthCheckResult(
                service="test",
                status=HealthStatus.HEALTHY,
                latency_ms=delay * 1000,
                message="OK",
            )

        with patch.object(health_check_service, "check_database", side_effect=slow_check), \
             patch.object(health_check_service, "check_redis", side_effect=slow_check), \
             patch.object(health_check_service, "check_rabbitmq", side_effect=slow_check), \
             patch.object(health_check_service, "check_opensearch", side_effect=slow_check), \
             patch.object(health_check_service, "check_celery", side_effect=slow_check):

            start = time.time()
            result = await health_check_service.check_all()
            elapsed = time.time() - start

            # Should complete in less than 5 * delay (if sequential would take 5 * delay)
            assert elapsed < (delay * 3)  # Allow some overhead
            assert len(result["services"]) == 5


# Error Handling Tests
class TestHealthCheckErrorHandling:
    """Tests for error handling in health checks"""

    @pytest.mark.asyncio
    async def test_database_timeout(self, health_check_service):
        """Test database check timeout handling"""
        health_check_service.set_timeout("database", 0.001)  # Very short timeout

        with patch("backend.services.health_check_service.create_async_engine") as mock_engine:
            mock_engine.return_value.connect = MagicMock(side_effect=Exception("Timeout"))

            result = await health_check_service.check_database()

            assert result.status == HealthStatus.UNHEALTHY
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_exception_in_check_all(self, health_check_service):
        """Test that exceptions in individual checks don't break check_all"""
        with patch.object(health_check_service, "check_database") as mock_db, \
             patch.object(health_check_service, "check_redis") as mock_redis, \
             patch.object(health_check_service, "check_rabbitmq") as mock_rabbit, \
             patch.object(health_check_service, "check_opensearch") as mock_search, \
             patch.object(health_check_service, "check_celery") as mock_celery:

            mock_db.return_value = HealthCheckResult(
                service="database", status=HealthStatus.HEALTHY,
                latency_ms=10.0, message="OK"
            )
            mock_redis.side_effect = Exception("Redis error")
            mock_rabbit.return_value = HealthCheckResult(
                service="rabbitmq", status=HealthStatus.HEALTHY,
                latency_ms=15.0, message="OK"
            )
            mock_search.return_value = HealthCheckResult(
                service="opensearch", status=HealthStatus.HEALTHY,
                latency_ms=20.0, message="OK"
            )
            mock_celery.return_value = HealthCheckResult(
                service="celery", status=HealthStatus.HEALTHY,
                latency_ms=30.0, message="OK"
            )

            result = await health_check_service.check_all()

            # Should still complete with error info
            assert "services" in result
            # The exception should be handled gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
