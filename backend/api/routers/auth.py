"""
Authentication and Authorization Router

Handles user registration, login, and authentication.
"""

import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from backend.api.validators import email_validator, string_validator
from backend.config import settings
from backend.db.database import get_db
from backend.db.models import FailedLoginAttempt, User
from backend.services.mfa_service import mfa_service
from backend.services.oauth2_service import oauth2_service

# Configure logging
logger = logging.getLogger(__name__)


router = APIRouter()

# Security configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(
    schemes=["pbkdf2-sha256", "argon2"],
    deprecated="auto",
    pbkdf2_sha256__rounds=settings.pbkdf2_rounds,
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


class UserCreate(BaseModel):
    """Request model for user registration with enhanced validation"""

    email: str
    password: str

    # Use common validators
    _email_validator = email_validator()

    @validator("password")
    def password_must_be_strong(cls, v):
        """Validate password strength: at least 8 characters, contains uppercase, lowercase, number, and special character"""
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(BaseModel):
    """Response model for user data"""

    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    """Response model for /me endpoint"""

    user: UserResponse


class Token(BaseModel):
    """Response model for access token"""

    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    """Response model for login/register with token and user info"""

    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    """Data model for token payload"""

    email: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using argon2 with enhanced security"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise ValueError(f"Password verification failed: {str(e)}")


def get_password_hash(password: str) -> str:
    """Generate password hash using argon2 with enhanced security"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token with enhanced security"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Get current authenticated user with enhanced error handling"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with enhanced validation and error handling

    Args:
        user: UserCreate model with email and password

    Returns:
        TokenResponse with access token and user info
    """
    try:
        logger.info(f"Registration attempt for email: {user.email}")

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.warning(
                f"Registration failed - email already registered: {user.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        new_user = User(
            email=user.email, password_hash=get_password_hash(user.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.email}")

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=str(new_user.id),
                email=new_user.email,
                created_at=new_user.created_at,
            ),
        )
    except ValueError as e:
        logger.error(f"Registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate user with email and password with enhanced error handling

    Args:
        form_data: OAuth2PasswordRequestForm with username/email and password

    Returns:
        TokenResponse with access token and user info
    """
    try:
        email = form_data.username
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        logger.info(f"Login attempt for email: {email} from IP: {ip_address}")

        # Check for suspicious activity
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_attempts_from_ip = (
            db.query(FailedLoginAttempt)
            .filter(
                FailedLoginAttempt.ip_address == ip_address,
                FailedLoginAttempt.attempted_at >= one_hour_ago,
            )
            .count()
        )

        if recent_attempts_from_ip > 10:
            logger.warning(
                f"Suspicious activity: {recent_attempts_from_ip} failed attempts from IP {ip_address} in last hour"
            )
            # Could send alert here

        user = db.query(User).filter(User.email == email).first()

        # Check if account is locked
        if user and user.lockout_until and datetime.utcnow() < user.lockout_until:
            logger.warning(
                f"Login attempt on locked account: {email} from IP: {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account is temporarily locked due to too many failed attempts",
            )

        # Verify password
        if not user or not verify_password(form_data.password, user.password_hash):
            # Record failed attempt
            failed_attempt = FailedLoginAttempt(
                user_id=user.id if user else None,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(failed_attempt)

            # Check failed attempts in last 24 hours
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            failed_count = (
                db.query(FailedLoginAttempt)
                .filter(
                    FailedLoginAttempt.email == email,
                    FailedLoginAttempt.attempted_at >= twenty_four_hours_ago,
                )
                .count()
            )

            if failed_count >= 5:
                # Calculate lockout time with exponential backoff
                lockout_minutes = min(
                    60, 1 * (2 ** (failed_count - 5))
                )  # 1, 2, 4, 8, 16, 32, 60...
                lockout_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
                if user:
                    user.lockout_until = lockout_until
                    logger.warning(
                        f"Account locked for user {email} until {lockout_until}"
                    )
                db.commit()  # Commit the failed attempt and lockout

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts. Account locked for {lockout_minutes} minutes.",
                )

            db.commit()  # Commit the failed attempt

            logger.warning(
                f"Login failed - invalid credentials for: {email} from IP: {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Successful login - clear failed attempts for this user
        db.query(FailedLoginAttempt).filter(FailedLoginAttempt.email == email).delete()
        if user.lockout_until:
            user.lockout_until = None
        db.commit()

        logger.info(f"User logged in successfully: {user.email}")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=str(user.id), email=user.email, created_at=user.created_at
            ),
        )
    except ValueError as e:
        logger.error(f"Login authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.get("/me", response_model=MeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information with logging"""
    try:
        logger.info(f"User accessed profile: {current_user.email}")
        return MeResponse(
            user=UserResponse(
                id=str(current_user.id),
                email=current_user.email,
                created_at=current_user.created_at,
            )
        )
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}",
        )


@router.get("/oauth2/{provider}")
async def oauth2_login(provider: str):
    """
    Initiate OAuth2 login flow

    Args:
        provider: OAuth2 provider (google, linkedin)

    Returns:
        Redirect URL for OAuth2 authorization
    """
    if provider not in ["google", "linkedin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth2 provider",
        )

    # Generate state for CSRF protection
    state = oauth2_service.generate_state()

    authorization_url = oauth2_service.get_authorization_url(provider, state)

    if not authorization_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OAuth2 provider {provider} is not configured",
        )

    return {"authorization_url": authorization_url, "state": state}


@router.get("/oauth2/callback/{provider}", response_model=TokenResponse)
async def oauth2_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle OAuth2 callback and create/login user

    Args:
        provider: OAuth2 provider (google, linkedin)
        code: Authorization code from provider
        state: State parameter for CSRF protection

    Returns:
        Access token and user info
    """
    if provider not in ["google", "linkedin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth2 provider",
        )

    # Validate state for CSRF protection
    if not oauth2_service.validate_state(state):
        logger.warning(
            f"OAuth2 state validation failed for provider {provider}, state: {state}, IP: {request.client.host}, User-Agent: {request.headers.get('user-agent')}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter"
        )

    # Get user info from OAuth2 provider
    user_info = await oauth2_service.get_user_info(provider, code)

    if not user_info or not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from OAuth2 provider",
        )

    email = user_info["email"]

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user
        user = User(
            email=email,
            password_hash=get_password_hash(
                secrets.token_urlsafe(32)
            ),  # Random password for OAuth2 users
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id), email=user.email, created_at=user.created_at
        ),
    )


# MFA Endpoints
class MFAEnableRequest(BaseModel):
    """Request model for enabling MFA"""

    token: str


class MFAVerifyRequest(BaseModel):
    """Request model for verifying MFA token"""

    token: str


class MFADisableRequest(BaseModel):
    """Request model for disabling MFA"""

    token: Optional[str] = None


@router.get("/mfa/setup")
async def mfa_setup(current_user: User = Depends(get_current_user)):
    """
    Set up MFA for the current user

    Returns:
        QR code and secret key for TOTP setup
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    # Generate MFA secret
    secret = mfa_service.generate_secret()
    current_user.mfa_secret = secret

    # Generate backup codes
    backup_codes = mfa_service.generate_backup_codes()
    current_user.mfa_backup_codes = backup_codes

    # Generate QR code
    qr_code = mfa_service.generate_qr_code(current_user.email, secret)

    return {"secret": secret, "qr_code": qr_code, "backup_codes": backup_codes}


@router.post("/mfa/enable")
async def mfa_enable(
    request: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enable MFA for the current user

    Args:
        request: MFAEnableRequest with verification token

    Returns:
        Success message
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA setup not initiated"
        )

    # Verify TOTP token
    if not mfa_service.verify_totp(current_user.mfa_secret, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token"
        )

    current_user.mfa_enabled = True
    db.commit()

    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def mfa_disable(
    request: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disable MFA for the current user

    Args:
        request: MFADisableRequest with optional verification token

    Returns:
        Success message
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled"
        )

    # Verify TOTP token if provided
    if request.token:
        if not mfa_service.verify_totp(current_user.mfa_secret, request.token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_backup_codes = None
    db.commit()

    return {"message": "MFA disabled successfully"}


@router.post("/mfa/verify")
async def mfa_verify(
    request: MFAVerifyRequest, current_user: User = Depends(get_current_user)
):
    """
    Verify MFA token

    Args:
        request: MFAVerifyRequest with verification token

    Returns:
        Success message
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled"
        )

    if not mfa_service.verify_totp(current_user.mfa_secret, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token"
        )

    return {"message": "MFA verification successful"}


@router.post("/mfa/verify-backup")
async def mfa_verify_backup(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify MFA backup code

    Args:
        request: MFAVerifyRequest with backup code

    Returns:
        Success message
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled"
        )

    if mfa_service.verify_backup_code(current_user, request.token):
        db.commit()
        return {"message": "Backup code verification successful"}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid backup code"
    )
