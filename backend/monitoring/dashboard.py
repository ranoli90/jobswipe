"""
JobSwipe Monitoring Dashboard - Backend API

Provides endpoints for accessing and managing monitoring data, metrics, and dashboards.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from prometheus_client import REGISTRY, generate_latest

from backend.config import Settings, get_settings
from backend.db.database import get_db
from backend.metrics import (
    api_requests_total,
    api_request_duration,
    applications_submitted_total,
    jobs_ingested_total,
    job_matching_requests_total,
    users_registered_total,
    auth_login_attempts_total,
    celery_tasks_total,
    database_connections_active,
    redis_memory_used,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/metrics")
def get_prometheus_metrics():
    """
    Get Prometheus-compatible metrics for scraping.
    """
    try:
        return generate_latest()
    except Exception as e:
        logger.error("Failed to generate metrics: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate metrics") from e


@router.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    time_range: int = Query(3600, description="Time range in seconds (default: 1 hour)")
):
    """
    Get a high-level summary dashboard with key metrics.
    """
    try:
        # Calculate time range boundaries
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(seconds=time_range)

        # Collect key business metrics
        metrics = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": time_range
            },
            "api_metrics": {
                "total_requests": api_requests_total._value.get(),
                "avg_response_time": _get_average_api_response_time(),
                "requests_by_status": _get_requests_by_status(),
                "top_endpoints": _get_top_endpoints()
            },
            "business_metrics": {
                "total_jobs_processed": jobs_ingested_total._value.get(),
                "applications_submitted": applications_submitted_total._value.get(),
                "jobs_matched": job_matching_requests_total._value.get(),
                "users_registered": users_registered_total._value.get(),
                "login_attempts": auth_login_attempts_total._value.get()
            },
            "system_metrics": {
                "active_db_connections": database_connections_active._value.get(),
                "redis_memory_used_mb": redis_memory_used._value.get() / (1024 * 1024) if redis_memory_used._value.get() else 0,
                "celery_tasks": celery_tasks_total._value.get(),
                "active_workers": _get_active_worker_count()
            },
            "performance_metrics": {
                "api_response_time_p50": _get_response_time_percentile(50),
                "api_response_time_p95": _get_response_time_percentile(95),
                "api_response_time_p99": _get_response_time_percentile(99),
                "job_matching_duration": _get_job_matching_duration()
            }
        }

        return metrics
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")


@router.get("/dashboard/metrics/{metric_name}")
def get_metric_details(
    metric_name: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    labels: Optional[List[str]] = Query(None, description="Filter by labels"),
    time_range: int = Query(3600, description="Time range in seconds (default: 1 hour)")
):
    """
    Get detailed information about a specific metric.
    """
    try:
        metric = REGISTRY._names_to_collectors.get(metric_name)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(seconds=time_range)

        metric_info = {
            "name": metric_name,
            "type": type(metric).__name__,
            "description": metric._documentation,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }

        if hasattr(metric, "_value"):
            metric_info["current_value"] = metric._value.get()

        if hasattr(metric, "_sum"):
            metric_info["sum"] = metric._sum.get()

        if hasattr(metric, "_count"):
            metric_info["count"] = metric._count.get()

        if hasattr(metric, "_buckets"):
            metric_info["buckets"] = _get_buckets_info(metric)

        return metric_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get metric details: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to get metric details") from e


@router.get("/dashboard/alerts")
def get_active_alerts(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Get active alerts and notifications.
    """
    try:
        alerts = []

        # Check for high response times
        avg_response_time = _get_average_api_response_time()
        if avg_response_time > 5.0:  # 5 seconds
            alerts.append({
                "level": "critical",
                "message": "High average API response time",
                "value": f"{avg_response_time:.2f}s",
                "threshold": "5.0s",
                "category": "performance"
            })

        # Check for high error rates
        error_rate = _get_error_rate()
        if error_rate > 0.1:  # 10% error rate
            alerts.append({
                "level": "warning",
                "message": "High API error rate",
                "value": f"{error_rate:.1%}",
                "threshold": "10%",
                "category": "reliability"
            })

        # Check for low worker count
        active_workers = _get_active_worker_count()
        if active_workers < 2:
            alerts.append({
                "level": "warning",
                "message": "Low active worker count",
                "value": str(active_workers),
                "threshold": "2",
                "category": "system"
            })

        # Check for high memory usage
        redis_memory = redis_memory_used._value.get() / (1024 * 1024 * 1024) if redis_memory_used._value.get() else 0
        if redis_memory > 2.0:  # 2GB
            alerts.append({
                "level": "warning",
                "message": "High Redis memory usage",
                "value": f"{redis_memory:.1f}GB",
                "threshold": "2.0GB",
                "category": "system"
            })

        return {
            "alerts": alerts,
            "total_alerts": len(alerts)
        }
    except Exception as e:
        logger.error("Failed to get active alerts: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to get active alerts") from e


@router.get("/dashboard/performance")
def get_performance_metrics(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    time_range: int = Query(3600, description="Time range in seconds (default: 1 hour)")
):
    """
    Get detailed performance metrics for the application.
    """
    try:
        return {
            "api_performance": {
                "response_time_p50": _get_response_time_percentile(50),
                "response_time_p95": _get_response_time_percentile(95),
                "response_time_p99": _get_response_time_percentile(99),
                "requests_per_second": _get_requests_per_second(time_range),
                "error_rate": _get_error_rate()
            },
            "database_performance": {
                "avg_query_time": _get_avg_db_query_time(),
                "connection_count": database_connections_active._value.get(),
                "query_count": _get_db_query_count()
            },
            "worker_performance": {
                "task_queue_length": _get_celery_queue_length(),
                "avg_task_duration": _get_avg_celery_task_duration(),
                "task_success_rate": _get_celery_task_success_rate()
            },
            "system_performance": {
                "memory_usage": _get_system_memory_usage(),
                "cpu_usage": _get_system_cpu_usage(),
                "disk_usage": _get_system_disk_usage()
            }
        }
    except Exception as e:
        logger.error("Failed to get performance metrics: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to get performance metrics") from e


def _get_average_api_response_time() -> float:
    """Calculate average API response time from histogram."""
    try:
        # Get sum and count from histogram
        if hasattr(api_request_duration, "_sum") and hasattr(api_request_duration, "_count"):
            total_seconds = api_request_duration._sum.get()
            total_requests = api_request_duration._count.get()
            if total_requests > 0:
                return total_seconds / total_requests
        return 0.0
    except Exception:
        return 0.0


def _get_requests_by_status() -> Dict[str, int]:
    """Get request count by status code."""
    try:
        if hasattr(api_requests_total, "_metrics"):
            status_counts = {}
            for metric in api_requests_total._metrics.values():
                status_code = metric.labels.get("status_code", "unknown")
                status_counts[status_code] = status_counts.get(status_code, 0) + metric._value.get()
            return status_counts
        return {}
    except Exception:
        return {}


def _get_top_endpoints() -> List[Dict[str, str]]:
    """Get top endpoints by request count."""
    try:
        if hasattr(api_requests_total, "_metrics"):
            endpoint_counts = {}
            for metric in api_requests_total._metrics.values():
                endpoint = metric.labels.get("endpoint", "unknown")
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + metric._value.get()

            # Sort by count descending and take top 5
            sorted_endpoints = sorted(
                endpoint_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            return [{"endpoint": ep, "count": int(count)} for ep, count in sorted_endpoints]
        return []
    except Exception:
        return []


def _get_response_time_percentile(percentile: int) -> float:
    """Get API response time percentile from histogram."""
    try:
        if hasattr(api_request_duration, "_buckets"):
            cumulative = 0
            count = api_request_duration._count.get()
            if count == 0:
                return 0.0

            target = count * percentile / 100

            # Process buckets
            for bucket, value in sorted(api_request_duration._buckets._metrics.items()):
                cumulative += value._value.get()
                if cumulative >= target:
                    return float(bucket)

            return 0.0
    except Exception:
        return 0.0


def _get_job_matching_duration() -> float:
    """Get average job matching duration."""
    try:
        from backend.metrics import job_matching_duration
        if hasattr(job_matching_duration, "_sum") and hasattr(job_matching_duration, "_count"):
            total_seconds = job_matching_duration._sum.get()
            total_requests = job_matching_duration._count.get()
            if total_requests > 0:
                return total_seconds / total_requests
        return 0.0
    except Exception:
        return 0.0


def _get_active_worker_count() -> int:
    """Get number of active workers."""
    try:
        from backend.workers.celery_app import celery_app
        stats = celery_app.control.inspect().active()
        if stats:
            return len(stats)
        return 0
    except Exception:
        return 0


def _get_error_rate() -> float:
    """Calculate API error rate."""
    try:
        total_requests = api_requests_total._value.get()
        error_requests = 0

        if hasattr(api_requests_total, "_metrics"):
            for metric in api_requests_total._metrics.values():
                status_code = metric.labels.get("status_code", "200")
                if status_code and (status_code.startswith("4") or status_code.startswith("5")):
                    error_requests += metric._value.get()

        return error_requests / total_requests if total_requests > 0 else 0.0
    except Exception:
        return 0.0


def _get_buckets_info(metric) -> List[Dict[str, float]]:
    """Get bucket information from histogram."""
    try:
        if hasattr(metric, "_buckets"):
            buckets = []
            for bucket, value in sorted(metric._buckets._metrics.items()):
                buckets.append({
                    "upper_bound": float(bucket),
                    "count": value._value.get()
                })
            return buckets
        return []
    except Exception:
        return []


def _get_celery_queue_length() -> int:
    """Get Celery task queue length."""
    try:
        from backend.metrics import celery_queue_length
        return celery_queue_length._value.get()
    except Exception:
        return 0


def _get_avg_celery_task_duration() -> float:
    """Get average Celery task duration."""
    try:
        from backend.metrics import celery_task_duration
        if hasattr(celery_task_duration, "_sum") and hasattr(celery_task_duration, "_count"):
            total_seconds = celery_task_duration._sum.get()
            total_tasks = celery_task_duration._count.get()
            if total_tasks > 0:
                return total_seconds / total_tasks
        return 0.0
    except Exception:
        return 0.0


def _get_celery_task_success_rate() -> float:
    """Get Celery task success rate."""
    try:
        from backend.metrics import celery_tasks_total
        if hasattr(celery_tasks_total, "_metrics"):
            total = 0
            success = 0
            for metric in celery_tasks_total._metrics.values():
                status = metric.labels.get("status", "unknown")
                count = metric._value.get()
                total += count
                if status == "success":
                    success += count

            return success / total if total > 0 else 0.0
        return 0.0
    except Exception:
        return 0.0


def _get_avg_db_query_time() -> float:
    """Get average database query time."""
    try:
        from backend.metrics import database_query_duration
        if hasattr(database_query_duration, "_sum") and hasattr(database_query_duration, "_count"):
            total_seconds = database_query_duration._sum.get()
            total_queries = database_query_duration._count.get()
            if total_queries > 0:
                return total_seconds / total_queries
        return 0.0
    except Exception:
        return 0.0


def _get_db_query_count() -> int:
    """Get database query count."""
    try:
        from backend.metrics import database_query_duration
        if hasattr(database_query_duration, "_count"):
            return database_query_duration._count.get()
        return 0
    except Exception:
        return 0


def _get_requests_per_second(time_range: int) -> float:
    """Get requests per second over time range."""
    try:
        total_requests = api_requests_total._value.get()
        return total_requests / time_range
    except Exception:
        return 0.0


def _get_system_memory_usage() -> float:
    """Get system memory usage (mock implementation)."""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except Exception:
        return 0.0


def _get_system_cpu_usage() -> float:
    """Get system CPU usage (mock implementation)."""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except Exception:
        return 0.0


def _get_system_disk_usage() -> float:
    """Get system disk usage (mock implementation)."""
    try:
        import psutil
        return psutil.disk_usage('/').percent
    except Exception:
        return 0.0
