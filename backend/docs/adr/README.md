# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records that document significant architectural decisions made for the JobSwipe platform.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences. ADRs help teams track the rationale behind technical choices and provide a historical record for future reference.

## Format

Each ADR follows the format:
1. **Title**: Descriptive title with ADR number
2. **Status**: Proposed, Accepted, Deprecated, or Superseded
3. **Context**: The problem or situation that prompted the decision
4. **Decision**: The chosen solution
5. **Consequences**: Both positive and negative effects of the decision
6. **Alternatives Considered**: Other options that were evaluated
7. **Implementation Notes**: Technical details for implementation

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-choose-fastapi.md) | Choose FastAPI as Web Framework | Accepted | 2024-01 |
| [ADR-002](ADR-002-choose-postgresql.md) | Choose PostgreSQL as Primary Database | Accepted | 2024-01 |
| [ADR-003](ADR-003-jwt-authentication.md) | Use JWT for API Authentication | Accepted | 2024-01 |

## Creating New ADRs

To create a new ADR:

1. Copy the template: `adr-template.md`
2. Fill in all sections
3. Use status "Proposed" initially
4. Get team review and approval
5. Update status to "Accepted" when approved

## ADR Lifecycle

```
Proposed → Review → Accepted → (Deprecated | Superseded)
```

- **Proposed**: Initial draft awaiting review
- **Accepted**: Approved and implemented
- **Deprecated**: No longer recommended
- **Superseded**: Replaced by a newer ADR
