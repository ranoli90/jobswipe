# ADR-006: ELK Stack for Structured Logging

## Status

Accepted

## Context

JobSwipe needs a centralized logging solution to:
- Aggregate logs from distributed services
- Enable efficient log querying and analysis
- Support troubleshooting and debugging
- Track user behavior and application performance
- Comply with security and audit requirements

## Decision

We will implement a **structured logging strategy with ELK Stack (Elasticsearch, Logstash, Kibana)** for log management.

### Architecture

```
[FastAPI API] → [Structured JSON Logs] → [Logstash] → [Elasticsearch] → [Kibana]
[Celery Workers] → [Structured JSON Logs] → [Logstash] → [Elasticsearch] → [Kibana]
[Services] → [Structured JSON Logs] → [Logstash] → [Elasticsearch] → [Kibana]
```

### Key Features

1. **Structured JSON Format**: Consistent log structure across all services
2. **Correlation IDs**: Trace requests through distributed system
3. **Environment Support**: Configurable log levels per environment (development/staging/production)
4. **Multiple Formats**: Support for JSON, text, ELK, and Datadog formats
5. **Centralized Storage**: Elasticsearch for scalable log storage
6. **Visualization**: Kibana dashboards for log analysis

### Log Structure

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "logger": "api",
  "message": "User login successful",
  "correlation_id": "uuid-1234",
  "service": "jobswipe",
  "environment": "production",
  "source": {
    "file": "auth.py",
    "line": 123,
    "function": "login"
  },
  "user_id": "user-123",
  "email": "user@example.com"
}
```

## Consequences

### Positive

1. **Centralized Logs**: All services log to a single system
2. **Powerful Querying**: Elasticsearch query DSL for advanced searches
3. **Visualization**: Kibana dashboards for real-time monitoring
4. **Troubleshooting**: Correlation IDs simplify debugging distributed systems
5. **Audit Trail**: Comprehensive log history for security audits

### Negative

1. **Infrastructure Complexity**: Requires managing ELK Stack components
2. **Resource Intensive**: Elasticsearch can be memory and storage heavy
3. **Cost**: May require additional infrastructure resources
4. **Learning Curve**: Team needs to learn ELK Stack tools

## Alternatives Considered

### Datadog Log Management
- Pros: Managed service, easy integration
- Cons: Vendor lock-in, cost
- Decision factor: We want to avoid vendor lock-in

### Splunk
- Pros: Powerful, enterprise-grade
- Cons: High cost, complex setup
- Decision factor: Overkill for JobSwipe's needs

### CloudWatch Logs
- Pros: Native AWS integration
- Cons: Vendor lock-in, limited query capabilities
- Decision factor: We want a portable solution

### File-Based Logging
- Pros: Simple, low overhead
- Cons: Hard to aggregate, query, and analyze
- Decision factor: Not suitable for distributed system

## Implementation Notes

1. **Structured Logging**: Use `pythonjsonlogger` for JSON log formatting
2. **Correlation IDs**: Implement middleware to track requests
3. **Log Levels**: Configurable per environment (DEBUG/INFO/WARNING)
4. **ELK Integration**: Use Logstash for log collection and parsing
5. **Security**: Implement log redaction for sensitive data
6. **Retention**: Configure Elasticsearch index retention policies
7. **Monitoring**: Set up log anomaly detection in Kibana
