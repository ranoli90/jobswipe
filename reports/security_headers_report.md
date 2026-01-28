# Security Headers Validation Report

**Generated:** 2026-01-27 19:26:36
**Target:** http://localhost:8000

## Summary

- Total endpoints tested: 13
- Endpoints with missing headers: 0
- Endpoints with mismatched headers: 0
- Endpoints with errors: 13

## Detailed Results

### GET /api/v1/auth/register

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### POST /api/v1/auth/register

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/auth/login

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### POST /api/v1/auth/login

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/auth/refresh

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/auth/refresh (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/auth/me

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/auth/me (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/jobs

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/jobs (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/jobs/matches

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/jobs/matches (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/profile

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/profile (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/profile/resume

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/profile/resume (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /api/v1/applications

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/applications (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### POST /api/v1/applications

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api/v1/applications (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

### GET /health

**Errors:**
- HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /health (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refused"))

