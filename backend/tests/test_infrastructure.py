"""
Infrastructure Tests for JobSwipe

Tests for backup manager, dynamic rate limiting, and metrics collection.
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from backend.api.middleware.dynamic_rate_limit import DynamicRateLimiter
from backend.monitoring.metrics_collector import MetricsCollector
import backend.metrics as metrics


# ================================
# Backup Manager Tests
# ================================

@patch('backup.backup_manager.os.path.exists')
@patch('backup.backup_manager.open', new_callable=mock_open, read_data='{"backup": {"base_dir": "/test/backups"}}')
def test_load_config_from_file(mock_file, mock_exists):
    """Test loading configuration from file"""
    from backup.backup_manager import load_config

    mock_exists.return_value = True

    config = load_config('/etc/backup/config.json')

    assert config["backup"]["base_dir"] == "/test/backups"
    assert config["database"]["host"] == "localhost"  # Default value
    assert config["schedule"]["full_backup"] == "0 2 * * 0"  # Default value


def test_load_config_default():
    """Test loading default configuration when file not exists"""
    from backup.backup_manager import load_config

    config = load_config('/nonexistent/config.json')

    assert config["backup"]["base_dir"] == "/var/backups/postgres"
    assert config["database"]["port"] == 5432
    assert config["encryption"]["enabled"]


@patch('backup.backup_manager.subprocess.run')
def test_run_command_success(mock_subprocess):
    """Test running a successful command"""
    from backup.backup_manager import run_command

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = b'Success'
    mock_result.stderr = b''
    mock_subprocess.return_value = mock_result

    result = run_command(['echo', 'test'])

    assert result["success"]
    assert result["return_code"] == 0
    assert 'Success' in result["stdout"]


@patch('backup.backup_manager.subprocess.run')
def test_run_command_failure(mock_subprocess):
    """Test running a failing command"""
    from backup.backup_manager import run_command

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = b'Output'
    mock_result.stderr = b'Error message'
    mock_subprocess.return_value = mock_result

    result = run_command(['false'])

    assert not result["success"]
    assert result["return_code"] == 1
    assert 'Error message' in result["stderr"]


@patch('backup.backup_manager.smtplib.SMTP')
def test_send_notification_success(mock_smtp):
    """Test sending email notification successfully"""
    from backup.backup_manager import send_notification

    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    config = {
        "notifications": {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "sender_email": "backup@jobswipe.com",
            "recipient_emails": ["devops@jobswipe.com"],
            "subject_prefix": "[JobSwipe Backup]"
        }
    }

    send_notification(config, "Test Subject", "Test Message")

    assert mock_smtp.called
    mock_smtp_instance.send_message.assert_called_once()


@patch('backup.backup_manager.smtplib.SMTP')
def test_send_notification_failure(mock_smtp):
    """Test handling email notification failure"""
    from backup.backup_manager import send_notification

    mock_smtp.side_effect = Exception("Connection error")

    config = {
        "notifications": {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "sender_email": "backup@jobswipe.com",
            "recipient_emails": ["devops@jobswipe.com"],
            "subject_prefix": "[JobSwipe Backup]"
        }
    }

    # Should not raise exception
    send_notification(config, "Test Subject", "Test Message")


@patch('backup.backup_manager.load_config')
@patch('backup.backup_manager.datetime')
@patch('backup.backup_manager.run_command')
def test_backup_dir_cleanup(mock_run_cmd, mock_datetime, mock_load_config):
    """Test backup directory cleanup logic"""
    from backup.backup_manager import cleanup_backup_dirs

    config = {
        "backup": {
            "base_dir": "/test/backups",
            "retention_days": 7,
            "incremental_retention_days": 3
        }
    }
    mock_load_config.return_value = config

    # Mock current time
    current_time = datetime(2024, 1, 10, 12, 0, 0)
    mock_datetime.now.return_value = current_time

    # Mock directory listing
    mock_run_cmd.side_effect = [
        # First call: list base directory
        {"success": True, "stdout": "/test/backups/full_20240101.tar.gz\n/test/backups/full_20240108.tar.gz"},
        # Subsequent calls: remove old files
        {"success": True}
    ]

    cleanup_backup_dirs()

    # Should have called ls and rm commands
    assert mock_run_cmd.called
    assert any("rm" in str(call) and "20240101" in str(call) for call in mock_run_cmd.call_args_list)
    assert any("rm" in str(call) and "20240108" not in str(call) for call in mock_run_cmd.call_args_list)  # 20240108 is within retention


# ================================
# Dynamic Rate Limiting Tests
# ================================

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for rate limiting tests"""
    client = AsyncMock()
    client.get.return_value = None
    client.set.return_value = None
    client.incr.return_value = 1
    client.expire.return_value = True
    return client


@pytest.fixture
def rate_limiter(mock_redis_client):
    """Create a DynamicRateLimiter instance with mock Redis"""
    with patch('backend.api.middleware.dynamic_rate_limit.redis_async.from_url') as mock_redis:
        mock_redis.return_value = mock_redis_client
        limiter = DynamicRateLimiter()
        limiter.redis = mock_redis_client
        return limiter


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object"""
    request = MagicMock()
    request.headers = {}
    request.state.user_tier = "free"
    return request


@pytest.mark.asyncio
async def test_get_user_tier_anonymous(rate_limiter, mock_request):
    """Test getting user tier for anonymous user (no API key)"""
    mock_request.headers = {}

    tier = await rate_limiter.get_user_tier(mock_request)

    assert tier == "anonymous"


@pytest.mark.asyncio
async def test_get_user_tier_free(rate_limiter, mock_request):
    """Test getting user tier from API key (free tier)"""
    mock_request.headers = {"X-API-Key": "test-api-key"}

    with patch('backend.api.middleware.dynamic_rate_limit.get_api_key_tier') as mock_get_tier:
        mock_get_tier.return_value = "free"

        tier = await rate_limiter.get_user_tier(mock_request)

        assert tier == "free"
        mock_get_tier.assert_called_once_with("test-api-key")


@pytest.mark.asyncio
async def test_get_rate_limit_for_tier(rate_limiter):
    """Test getting rate limit configuration for different tiers"""
    assert rate_limiter.get_rate_limit("anonymous") == (60, timedelta(minutes=1))
    assert rate_limiter.get_rate_limit("free") == (100, timedelta(minutes=1))
    assert rate_limiter.get_rate_limit("premium") == (500, timedelta(minutes=1))
    assert rate_limiter.get_rate_limit("enterprise") == (2000, timedelta(minutes=1))


@pytest.mark.asyncio
async def test_check_rate_limit_not_exceeded(rate_limiter, mock_request, mock_redis_client):
    """Test checking rate limit when not exceeded"""
    mock_redis_client.get.return_value = None
    mock_redis_client.incr.return_value = 50

    result = await rate_limiter.check_rate_limit(mock_request, "192.168.1.1")

    assert result["allowed"]
    assert result["remaining"] == 50
    assert result["reset"] > 0
    mock_redis_client.incr.assert_called_once()


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(rate_limiter, mock_request, mock_redis_client):
    """Test checking rate limit when exceeded"""
    mock_redis_client.incr.return_value = 101  # Free tier limit is 100

    result = await rate_limiter.check_rate_limit(mock_request, "192.168.1.1")

    assert not result["allowed"]
    assert result["remaining"] == 0
    assert result["reset"] > 0


@pytest.mark.asyncio
async def test_check_rate_limit_redis_unavailable(rate_limiter, mock_request):
    """Test rate limiting when Redis is unavailable"""
    rate_limiter.redis = None

    result = await rate_limiter.check_rate_limit(mock_request, "192.168.1.1")

    assert result["allowed"]


# ================================
# Metrics Collection Tests
# ================================

@patch('backend.monitoring.metrics_collector.get_db')
def test_metrics_collector_initialization(mock_get_db):
    """Test MetricsCollector initialization"""
    collector = MetricsCollector()

    assert collector is not None
    assert hasattr(collector, 'settings')
    assert hasattr(collector, 'logger')


@patch('backend.monitoring.metrics_collector.get_db')
def test_collect_system_metrics(mock_get_db):
    """Test collecting system metrics"""
    collector = MetricsCollector()

    metrics = collector.collect_system_metrics()

    assert 'cpu_percent' in metrics
    assert 'memory_percent' in metrics
    assert 'disk_percent' in metrics
    assert 'network_io' in metrics
    assert 0 <= metrics['cpu_percent'] <= 100
    assert 0 <= metrics['memory_percent'] <= 100
    assert 0 <= metrics['disk_percent'] <= 100


@patch('backend.monitoring.metrics_collector.get_db')
def test_collect_database_metrics(mock_get_db):
    """Test collecting database metrics"""
    collector = MetricsCollector()

    db_metrics = collector.collect_database_metrics()

    assert 'active_connections' in db_metrics
    assert 'slow_queries' in db_metrics
    assert 'total_transactions' in db_metrics


@patch('backend.monitoring.metrics_collector.get_db')
def test_collect_api_metrics(mock_get_db):
    """Test collecting API metrics from Prometheus client registry"""
    collector = MetricsCollector()

    api_metrics = collector.collect_api_metrics()

    assert 'api_requests_total' in api_metrics
    assert 'api_request_duration' in api_metrics
    assert 'api_error_rate' in api_metrics


@patch('backend.monitoring.metrics_collector.get_db')
@patch('backend.monitoring.metrics_collector.psutil.virtual_memory')
def test_collect_memory_usage(mock_memory, mock_get_db):
    """Test collecting memory usage metrics"""
    mock_memory.return_value.percent = 45.2
    mock_memory.return_value.available = 4294967296
    mock_memory.return_value.used = 3221225472

    collector = MetricsCollector()
    metrics = collector.collect_system_metrics()

    assert metrics['memory_percent'] == 45.2
    assert metrics['memory_available'] == 4294967296
    assert metrics['memory_used'] == 3221225472


@patch('backend.monitoring.metrics_collector.get_db')
@patch('backend.monitoring.metrics_collector.psutil.cpu_percent')
def test_collect_cpu_usage(mock_cpu, mock_get_db):
    """Test collecting CPU usage metrics"""
    mock_cpu.return_value = 30.5

    collector = MetricsCollector()
    metrics = collector.collect_system_metrics()

    assert metrics['cpu_percent'] == 30.5


@patch('backend.monitoring.metrics_collector.get_db')
def test_calculate_throughput_metrics(mock_get_db):
    """Test calculating API throughput metrics"""
    collector = MetricsCollector()

    throughput = collector.calculate_throughput_metrics()

    assert 'requests_per_second' in throughput
    assert 'requests_per_minute' in throughput
    assert 'requests_per_hour' in throughput
    assert isinstance(throughput['requests_per_second'], float)


# ================================
# Prometheus Metrics Tests
# ================================

def test_metrics_registration():
    """Test that all required metrics are properly registered"""
    required_metrics = [
        'api_requests_total',
        'api_request_duration_seconds',
        'applications_submitted_total',
        'jobs_ingested_total',
        'job_matching_requests_total',
        'users_registered_total',
        'auth_login_attempts_total',
        'celery_tasks_total',
        'database_connections_active',
        'redis_memory_used'
    ]

    # Check if metrics are registered
    from prometheus_client import REGISTRY

    for metric_name in required_metrics:
        assert any(metric_name in collector.name for collector in REGISTRY._collector_to_names.keys())


def test_api_requests_total_metric():
    """Test api_requests_total counter metric"""
    # Save initial value
    initial_value = metrics.api_requests_total._value.get()

    # Increment counter
    metrics.api_requests_total.labels(method='GET', endpoint='/jobs', status_code=200).inc()

    # Verify increment
    assert metrics.api_requests_total._value.get() == initial_value + 1


def test_api_request_duration_metric():
    """Test api_request_duration histogram metric"""
    # Observe duration
    duration = 0.5
    metrics.api_request_duration.labels(method='GET', endpoint='/jobs').observe(duration)

    # Verify histogram has data (we can't easily get the actual value from Histogram)
    # but we can check it has the expected labels
    assert hasattr(metrics.api_request_duration, '_labelnames')
    assert 'method' in metrics.api_request_duration._labelnames
    assert 'endpoint' in metrics.api_request_duration._labelnames


def test_jobs_processed_per_day_gauge():
    """Test jobs_processed_per_day gauge metric"""
    # Set gauge value
    metrics.jobs_processed_per_day.set(150)

    # Verify value
    assert metrics.jobs_processed_per_day._value.get() == 150


def test_application_success_rate_gauge():
    """Test application_success_rate gauge metric"""
    # Set gauge value
    metrics.application_success_rate.set(0.15)

    # Verify value
    assert metrics.application_success_rate._value.get() == 0.15


# ================================
# Integration Tests
# ================================

@pytest.mark.integration
@patch('backup.backup_manager.smtplib.SMTP')
@patch('backup.backup_manager.subprocess.run')
def test_full_backup_workflow(mock_run_cmd, mock_smtp):
    """Test the full backup workflow integration"""
    from backup.backup_manager import run_full_backup, load_config

    # Configure mocks
    mock_run_cmd.return_value = {"success": True}
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    config = load_config()

    # Run full backup
    result = run_full_backup(config)

    assert result["success"]
    assert "backup_file" in result
    assert "size" in result
    assert "duration" in result
    assert "timestamp" in result

    # Verify email notification
    mock_smtp.assert_called_once()
    mock_smtp_instance.send_message.assert_called_once()


@pytest.mark.integration
@patch('backend.api.middleware.dynamic_rate_limit.get_api_key_tier')
@pytest.mark.asyncio
async def test_dynamic_rate_limit_integration(mock_get_tier, rate_limiter, mock_request, mock_redis_client):
    """Test dynamic rate limiting integration with API key tiers"""
    mock_get_tier.return_value = "premium"
    mock_request.headers = {"X-API-Key": "premium-api-key"}
    mock_redis_client.incr.return_value = 499  # Below premium tier limit of 500

    result = await rate_limiter.check_rate_limit(mock_request, "192.168.1.1")

    assert result["allowed"]
    assert result["remaining"] == 1

    # Now test exceeding the limit
    mock_redis_client.incr.return_value = 501

    result = await rate_limiter.check_rate_limit(mock_request, "192.168.1.1")

    assert not result["allowed"]
    assert result["remaining"] == 0


@pytest.mark.integration
@patch('backend.monitoring.metrics_collector.get_db')
def test_metrics_collection_integration(mock_get_db, rate_limiter, mock_redis_client):
    """Test metrics collection pipeline integration"""
    collector = MetricsCollector()

    # Collect different types of metrics
    system_metrics = collector.collect_system_metrics()
    database_metrics = collector.collect_database_metrics()
    api_metrics = collector.collect_api_metrics()
    business_metrics = collector.collect_business_metrics()

    # Verify all metrics are collected properly
    assert all(isinstance(x, dict) for x in [system_metrics, database_metrics, api_metrics, business_metrics])
    assert len(system_metrics) > 0
    assert len(database_metrics) > 0
    assert len(api_metrics) > 0
    assert len(business_metrics) > 0

    # Verify critical business metrics are present
    assert 'jobs_processed_per_day' in business_metrics
    assert 'applications_sent_per_day' in business_metrics
    assert 'application_success_rate' in business_metrics
    assert 'job_match_quality_score' in business_metrics
