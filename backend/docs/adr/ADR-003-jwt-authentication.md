# ADR-003: Use JWT for API Authentication

## Status

Accepted

## Context

We need to implement authentication for the API. The solution must be secure, scalable, and support multiple client types (mobile, web, service-to-service).

## Decision

We will use **JWT (JSON Web Tokens)** for API authentication with the following structure:

- **Access Token**: Short-lived (60 minutes), contains user identity
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens
- **API Keys**: For service-to-service authentication

## Consequences

### Positive

1. **Stateless** - No server-side session storage needed
2. **Scalable** - Works across multiple API instances
3. **Flexible** - Can embed custom claims
4. **Secure** - Uses industry-standard algorithms (RS256)
5. **Mobile Friendly** - Works well with mobile apps

### Negative

1. **Token Revocation** - Difficult to revoke tokens before expiration
2. **Token Size** - Larger than session IDs
3. **Secret Management** - Requires secure key storage
4. **Replay Attacks** - Need implement rate limiting

## Implementation

### Token Payload

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "user",
  "mfa_verified": true,
  "exp": 1234567890,
  "iat": 1234564290
}
```

### Security Measures

1. **Short-lived access tokens** (60 minutes)
2. **Refresh token rotation** on each use
3. **Token binding** to device/client
4. **Rate limiting** per token
5. **Secure cookie storage** for web clients

## Alternatives Considered

### Session-based (Session ID in cookie)
- Pros: Easy revocation, server-side control
- Cons: Requires session storage, not stateless

### OAuth2 Access Tokens
- Pros: Industry standard, supports delegation
- Cons: Complex implementation, requires token introspection

### API Keys Only
- Pros: Simple, good for service-to-service
- Cons: No user context, hard to revoke per user
