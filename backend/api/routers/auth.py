"""
Authentication and Authorization Router

Handles user registration, login, and authentication.
"""

import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator, ConfigDict
from sqlalchemy.orm import Session

from backend.api.validators import email_validator
from backend.config import settings
from backend.db.database import get_db
from backend.db.models import FailedLoginAttempt, User
from backend.services.mfa_service import mfa_service
from backend.services.oauth2_service import oauth2_service
from backend.services.notification_service import NotificationService

# Configure logging
logger = logging.getLogger(__name__)


router = APIRouter()

# Initialize notification service
notification_service = NotificationService()

# Security configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(
    schemes=["argon2", "pbkdf2-sha256"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=8,
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Initialize Redis client for token blacklist
try:
    redis_client = redis.Redis(
        host=settings.redis_url.split("://")[1].split("/")[0],
        port=int(settings.redis_url.split(":")[2].split("/")[0]),
        decode_responses=True,
        socket_connect_timeout=5,
    )
    redis_client.ping()  # Test connection
except Exception:
    redis_client = None
    logger.warning("Redis unavailable - token blacklist disabled")


class UserCreate(BaseModel):
    """Request model for user registration with enhanced validation"""

    email: str
    password: str

    # Use common validators
    _email_validator = email_validator()

    @field_validator("password")
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

    model_config = ConfigDict(from_attributes=True)


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
    refresh_token: str
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT refresh token with longer expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
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

        # Check if token is in blacklist
        if redis_client:
            try:
                if redis_client.get(f"token_blacklist:{token}"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has been revoked",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            except Exception as e:
                logger.error("Redis blacklist check failed: %s", str(e))

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


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint",
        )
    return current_user


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
        logger.info("Registration attempt for email: %s", user.email)

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.warning("Registration failed - email already registered: %s", user.email)
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

        logger.info("User registered successfully: %s", new_user.email)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )
        # Create refresh token
        refresh_token = create_refresh_token(data={"sub": new_user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=str(new_user.id),
                email=new_user.email,
                created_at=new_user.created_at,
            ),
        )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except ValueError as e:
        logger.error("Registration validation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        logger.error("Registration failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later.",
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

        logger.info("Login attempt for email: %s from IP: %s", email, ip_address)

        # Check for suspicious activity
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_attempts_from_ip = (
            db.query(FailedLoginAttempt)
            .filter(
                FailedLoginAttempt.ip_address == ip_address,
                FailedLoginAttempt.attempted_at >= one_hour_ago,
            )
            .count()
        )

        if recent_attempts_from_ip > 10:
            logger.warning("Suspicious activity: %d failed attempts from IP %s in last hour", recent_attempts_from_ip, ip_address)
            # Could send alert here

        user = db.query(User).filter(User.email == email).first()

        # Check if account is locked
        if user and user.lockout_until and datetime.now(timezone.utc) < user.lockout_until:
            logger.warning("Login attempt on locked account: %s from IP: %s", email, ip_address)
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
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
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
                lockout_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
                if user:
                    user.lockout_until = lockout_until
                    logger.warning("Account locked for user %s until %s", email, lockout_until)
                db.commit()  # Commit the failed attempt and lockout

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts. Account locked for {lockout_minutes} minutes.",
                )

            db.commit()  # Commit the failed attempt

            logger.warning("Login failed - invalid credentials for: %s from IP: %s", email, ip_address)
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

        logger.info("User logged in successfully: %s", user.email)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        # Create refresh token
        refresh_token = create_refresh_token(data={"sub": user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=str(user.id), email=user.email, created_at=user.created_at
            ),
        )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except ValueError as e:
        logger.error("Login authentication error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Login failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later.",
        )


@router.get("/me", response_model=MeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information with logging"""
    try:
        logger.info("User accessed profile: %s", current_user.email)
        return MeResponse(
            user=UserResponse(
                id=str(current_user.id),
                email=current_user.email,
                created_at=current_user.created_at,
            )
        )
    except Exception as e:
        logger.error("Failed to get user profile: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}",
        )


# ... rest of the code remains the same ...
