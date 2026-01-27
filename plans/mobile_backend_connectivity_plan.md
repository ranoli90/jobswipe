# Backend Deployment & Mobile App Connectivity Improvement Plan

## Executive Summary

This plan addresses critical gaps between the backend API and mobile app requirements, along with deployment optimizations for Fly.io.

**Critical Issue Identified:** The mobile app expects a `/v1/auth/refresh` endpoint for token refresh, but this endpoint doesn't exist in the backend. This will cause authentication failures on mobile login.

---

## Part 1: Backend Missing Endpoints (CRITICAL)

### Authentication Endpoints Required

| Mobile App Expects | Backend Status | Priority |
|-------------------|----------------|----------|
| `/v1/auth/refresh` | ❌ MISSING | **CRITICAL** |
| `/v1/auth/logout` | ❌ MISSING | HIGH |
| `/v1/auth/verify-email` | ❌ MISSING | HIGH |
| `/v1/auth/forgot-password` | ❌ MISSING | MEDIUM |
| `/v1/auth/reset-password` | ❌ MISSING | MEDIUM |

### Notifications Endpoints Required

| Mobile App Expects | Backend Status |
|-------------------|----------------|
| `/v1/notifications/mark-all-read` | ❌ MISSING |

---

## Part 2: Implementation Plan

### Phase 1: Critical Authentication Fixes

#### 1.1 Add Token Refresh Endpoint

```python
# backend/api/routers/auth.py

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_token: str = Body(...),
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token
    
    Mobile app expects:
    - POST /v1/auth/refresh
    - Body: {"refresh_token": "..."}
    - Returns: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
    """
    try:
        # Verify refresh token
        payload = jwt.decode(
            refresh_token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Get user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        # Generate new refresh token
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=str(user.id), 
                email=user.email, 
                created_at=user.created_at
            ),
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
```

#### 1.2 Add Logout Endpoint

```python
# backend/api/routers/auth.py

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout user and invalidate tokens
    """
    # Blacklist the current access token (implement token blacklist)
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}
```

#### 1.3 Update Login Response to Include Refresh Token

The current `TokenResponse` model needs to include `refresh_token`:

```python
# backend/api/routers/auth.py

class TokenResponse(BaseModel):
    """Response model for login/register with token and user info"""
    access_token: str
    refresh_token: str  # ADD THIS
    token_type: str
    user: UserResponse
```

Update the login endpoint to generate and return a refresh token.

### Phase 2: Email & Password Recovery

#### 2.1 Add Email Verification Endpoint

```python
# backend/api/routers/auth.py

class EmailVerificationRequest(BaseModel):
    email: str

@router.post("/verify-email")
async def send_verification_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """Send email verification link"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if user exists
        return {"message": "If the email exists, a verification link has been sent"}
    
    # Generate verification token and send email
    verification_token = create_email_verification_token(request.email)
    # Send email via notification service
    
    return {"message": "Verification email sent"}

@router.get("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email with token"""
    # Decode and verify token
    # Update user email_verified = True
    return {"message": "Email verified successfully"}
```

#### 2.2 Add Forgot/Reset Password Endpoints

```python
# backend/api/routers/auth.py

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Send password reset email"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token and send email
    reset_token = create_password_reset_token(request.email)
    # Send email via notification service
    
    return {"message": "Password reset email sent"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset password with token"""
    try:
        payload = jwt.decode(
            request.token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        email = payload.get("sub")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token",
            )
        
        # Update password
        user.password_hash = get_password_hash(request.new_password)
        db.commit()
        
        return {"message": "Password reset successfully"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
```

### Phase 3: Notifications Enhancement

#### 3.1 Add Mark All Notifications Read Endpoint

```python
# backend/api/routers/notifications.py

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
```

---

## Part 3: Mobile App Configuration

### API Configuration (mobile-app/lib/config/app_config.dart)

The mobile app is already configured to use the correct API URL structure:

```dart
static const String baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://jobswipe.fly.dev',
);
```

### Required Environment Variables

For production deployment, ensure these are set:
- `API_BASE_URL`: https://jobswipe.fly.dev (already configured)
- `ENVIRONMENT`: production

---

## Part 4: Deployment Status

### Current Fly.io Deployment

✅ **Completed:**
- Dockerfile fixed (Playwright issue resolved with `python:3.12-slim-bullseye`)
- Multi-stage build configured
- Secrets configured (DATABASE_URL, REDIS_URL, JWT secrets, etc.)
- Redis database created (jobswipe-cache)
- PostgreSQL database configured
- Root-level fly.toml with improved configuration
- .dockerignore file created

⏳ **In Progress:**
- Build context transfer (currently uploading ~1.77GB)

### Build Optimization Recommendations

1. **Reduce Build Context Size**
   - Current: ~1.77GB transfer
   - Recommendation: Add more exclusions to .dockerignore
   - Exclude: `flutter/`, `backup/`, `docs/`, `mobile-app/`

2. **Multi-stage Build Benefits**
   - Builder stage: Install dependencies, compile Python packages
   - Runner stage: Minimal image with only runtime dependencies
   - Result: Smaller final image, faster deploys

---

## Part 5: Summary of Required Changes

### Backend Changes (Priority Order)

| Priority | File | Change |
|----------|------|--------|
| CRITICAL | `backend/api/routers/auth.py` | Add `/refresh` endpoint |
| CRITICAL | `backend/api/routers/auth.py` | Update login to return `refresh_token` |
| HIGH | `backend/api/routers/auth.py` | Add `/logout` endpoint |
| HIGH | `backend/api/routers/auth.py` | Add `/verify-email` endpoints |
| HIGH | `backend/api/routers/notifications.py` | Add `/mark-all-read` endpoint |
| MEDIUM | `backend/api/routers/auth.py` | Add `/forgot-password` endpoint |
| MEDIUM | `backend/api/routers/auth.py` | Add `/reset-password` endpoint |

### Mobile App Changes

✅ **No changes required** - Mobile app is already configured correctly

### Deployment Changes

| File | Change |
|------|--------|
| `.dockerignore` | Add `flutter/`, `backup/`, `docs/` exclusions |
| `fly.toml` | Increase VM memory if needed |

---

## Part 6: Testing Checklist

After implementing changes:

- [ ] Test login returns `refresh_token`
- [ ] Test `/v1/auth/refresh` endpoint returns new access token
- [ ] Test logout invalidates tokens
- [ ] Test email verification flow
- [ ] Test forgot/reset password flow
- [ ] Test mobile app login flow end-to-end
- [ ] Test notification "mark all as read"
- [ ] Verify all mobile screens load correctly

---

## Conclusion

The backend is missing critical authentication endpoints that the mobile app depends on. The most urgent fix is implementing the `/v1/auth/refresh` endpoint and updating the login response to include a refresh token. Once these changes are made, the mobile app should be able to authenticate successfully.

The Fly.io deployment infrastructure is properly configured and the build is in progress. After deployment, the backend will be accessible at `https://jobswipe.fly.dev` for the mobile app to connect to.
