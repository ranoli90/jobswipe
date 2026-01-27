# ADR-002: Choose PostgreSQL as Primary Database

## Status

Accepted

## Context

We need to select a primary database for storing structured application data including users, jobs, applications, and analytics.

## Decision

We have chosen **PostgreSQL** as our primary database.

## Consequences

### Positive

1. **ACID Compliance** - Ensures data integrity for financial transactions
2. **JSON Support** - Native JSON/JSONB for flexible data storage
3. **Full-Text Search** - Built-in search capabilities
4. **Extensions** - Rich ecosystem (PostGIS, pgvector, etc.)
5. **可靠性** - Excellent reliability and data protection
6. **性能** - Strong performance for complex queries
7. **开源** - Fully open-source with no licensing costs

### Negative

1. **Complexity** - Requires more expertise than SQLite
2. **Resource Usage** - Higher memory and storage requirements
3. **Scaling** - Vertical scaling is primary approach
4. **运维** - Requires regular maintenance and backups

## Alternatives Considered

### MySQL/MariaDB
- Pros: Simpler, good replication
- Cons: Less flexible JSON support, no full-text search in older versions

### SQLite
- Pros: Simple, zero configuration
- Cons: Not suitable for concurrent writes, limited features

### MongoDB
- Pros: Flexible document model
- Cons: Less suitable for relational data, no ACID by default

## Implementation Notes

- Use SQLAlchemy with async support (sqlalchemy[asyncio])
- Use alembic for migrations
- Use connection pooling (asyncpg)
- Implement read replicas for heavy read workloads
- Use PostgreSQL JSONB for flexible fields (profile data, metadata)
