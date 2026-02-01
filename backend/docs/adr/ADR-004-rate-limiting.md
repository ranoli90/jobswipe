# ADR-004: Dynamic Rate Limiting Strategy

## Status

Accepted

## Context

JobSwipe API needs to protect against abuse, ensure fair usage, and maintain service availability. We need a rate limiting strategy that supports different user tiers, is scalable, and provides flexibility.

## Decision

We will implement **dynamic rate limiting** based on user subscription tiers using Redis-backed sliding window rate limiting.

### Rate Limit Tiers

```python
RATE_LIMITS = {
    "anonymous": {"requests": 60, "window": timedelta(minutes=1)},  # 60 requests per minute
    "free": {"requests": 100, "window": timedelta(minutes=1)},      # 100 requests per minute
    "premium": {"requests": 500, "window": timedelta(minutes=1)},   # 500 requests per minute
    "enterprise": {"requests": 2000, "window": timedelta(minutes=1)} # 2000 requests per minute
}
```

### Key Features

1. **Tier-Based Limiting**: Different limits for anonymous, free, premium, and enterprise users
2. **Redis-Backed Storage**: Sliding window algorithm with Redis for scalability
3. **Dynamic User Tier Detection**: Extracts user tier from authentication context
4. **Rate Limit Headers**: Returns `X-RateLimit-*` headers with each response
5. **Graceful Degradation**: Disables rate limiting if Redis connection fails

## Consequences

### Positive

1. **Fair Usage**: Ensures premium users get higher rate limits
2. **Scalability**: Redis-backed storage supports high concurrency
3. **Flexibility**: Easy to adjust rate limits per tier
4. **Transparency**: Rate limit headers inform clients of their limits
5. **Resilience**: System continues to function if rate limiting fails

### Negative

1. **Redis Dependency**: Requires Redis infrastructure
2. **Implementation Complexity**: Dynamic tier detection adds complexity
3. **Overhead**: Each request incurs Redis operations cost

## Alternatives Considered

### Fixed Rate Limiting (All Users Same Limit)
- Pros: Simple implementation
- Cons: Unfair for premium users, doesn't reflect value

### Token Bucket Algorithm
- Pros: Smoother traffic shaping
- Cons: More complex, less intuitive for users to understand

### Leaky Bucket Algorithm
- Pros: Consistent output rate
- Cons: Doesn't handle burst traffic well

### In-Memory Rate Limiting
- Pros: No external dependencies
- Cons: Not scalable across multiple API instances

## Implementation Notes

1. **Middleware Architecture**: Implement as FastAPI middleware
2. **Redis Connection**: Use `redis.asyncio` for async Redis operations
3. **Rate Limit Keys**: Generate unique keys per user tier and identifier (user ID, API key, IP)
4. **Response Headers**: Include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `X-RateLimit-Tier`
5. **Error Handling**: Return 429 Too Many Requests with `Retry-After` header
6. **Monitoring**: Log rate limit violations with user tier information
