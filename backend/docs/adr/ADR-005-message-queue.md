# ADR-005: Use Celery with Redis for Background Task Processing

## Status

Accepted

## Context

JobSwipe needs to handle background tasks such as:
- Email/SMS notifications
- Job ingestion and processing
- Analytics generation
- Data cleanup
- Resume parsing

We need a message queue system that is reliable, scalable, and easy to integrate with our Python backend.

## Decision

We will use **Celery with Redis as broker and result backend** for background task processing.

### Architecture

```
[FastAPI API] → [Celery Tasks] → [Redis Broker] → [Celery Workers]
                                 ↓
                           [Result Backend]
```

### Key Features

1. **Task Routing**: Dedicated queues for different task types (notifications, ingestion, analytics, cleanup)
2. **Scheduled Tasks**: Celery Beat for periodic task scheduling
3. **Monitoring**: Integration with Prometheus metrics
4. **Error Handling**: Retry mechanisms and dead-letter queues
5. **Concurrency Control**: Configurable worker concurrency and prefetch limits

### Current Configuration

```python
celery_app = Celery(
    "jobswipe",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.workers.celery_tasks.notification_tasks",
        "backend.workers.celery_tasks.ingestion_tasks",
        "backend.workers.celery_tasks.analytics_tasks",
        "backend.workers.celery_tasks.cleanup_tasks",
    ],
)

# Task routing
task_routes={
    "backend.workers.celery_tasks.notification_tasks.*": {"queue": "notifications"},
    "backend.workers.celery_tasks.ingestion_tasks.*": {"queue": "ingestion"},
    "backend.workers.celery_tasks.analytics_tasks.*": {"queue": "analytics"},
    "backend.workers.celery_tasks.cleanup_tasks.*": {"queue": "cleanup"},
}
```

## Consequences

### Positive

1. **Simple Integration**: Well-documented and widely used in Python ecosystem
2. **Redis Synergy**: Reuses existing Redis infrastructure
3. **Flexible Routing**: Easy to prioritize and isolate task types
4. **Monitoring Support**: Built-in Prometheus integration
5. **Scheduling**: Celery Beat provides cron-like scheduling

### Negative

1. **Redis Limitations**: Not suitable for very large message volumes or long-term storage
2. **Complexity**: Requires managing worker processes
3. **Result Backend**: Redis may not be ideal for large result sets

## Alternatives Considered

### RabbitMQ
- Pros: Advanced queuing features (priorities, transactions, pub/sub)
- Cons: Additional infrastructure, more complex setup

### Amazon SQS
- Pros: Managed service, highly scalable
- Cons: Vendor lock-in, higher cost, limited routing features

### RQ (Redis Queue)
- Pros: Simple, lightweight
- Cons: Less feature-rich, no built-in scheduling

### Apache Kafka
- Pros: High throughput, fault-tolerant
- Cons: Overkill for JobSwipe's needs, higher complexity

## Implementation Notes

1. **Worker Configuration**: Run separate worker processes for each queue type
2. **Monitoring**: Use Prometheus to track task execution metrics
3. **Error Handling**: Implement exponential backoff for retries
4. **Dead Letter Queues**: Handle failed tasks separately for debugging
5. **Task Timeouts**: Set reasonable time limits per task type
6. **Serialization**: Use JSON serialization for compatibility
