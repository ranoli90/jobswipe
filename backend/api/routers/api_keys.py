"""
API Key Management Router

Provides endpoints for managing API keys for internal services.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.main import get_current_user
from backend.api.validators import validate_uuid
from backend.db.database import get_db
from backend.db.models import User
from backend.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/admin/api-keys", tags=["API Keys"])


class CreateApiKeyRequest:
    """Request model for creating an API key"""

    name: str
    service_type: str  # ingestion, automation, analytics, webhook
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    rate_limit: Optional[int] = 1000
    expires_at: Optional[datetime] = None


class ApiKeyResponse:
    """Response model for API key details (without the secret key)"""

    id: str
    key_prefix: str
    name: str
    service_type: str
    permissions: List[str]
    rate_limit: int
    expires_at: Optional[str]
    is_active: bool
    last_used_at: Optional[str]
    usage_count: int
    created_at: str


class ApiKeyWithKeyResponse(ApiKeyResponse):
    """Response model when creating a new key (includes the plain key)"""

    key: str  # Only returned once at creation


# Valid service types for API keys
VALID_SERVICE_TYPES = ["ingestion", "automation", "analytics", "webhook"]


@router.post(
    "/", response_model=ApiKeyWithKeyResponse, status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    request: CreateApiKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new API key for internal service authentication.

    The API key is only returned once at creation time. Store it securely.
    """
    # Validate service type
    if request.service_type not in VALID_SERVICE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service_type. Must be one of: {VALID_SERVICE_TYPES}",
        )

    # Check if user has admin permissions
    if current_user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create API keys",
        )

    service = ApiKeyService(db)
    key_details = service.create_api_key(
        name=request.name,
        service_type=request.service_type,
        created_by=current_user,
        description=request.description,
        permissions=request.permissions,
        rate_limit=request.rate_limit,
        expires_at=request.expires_at,
    )

    return {
        "id": key_details["id"],
        "key": key_details["key"],
        "key_prefix": key_details["key_prefix"],
        "name": key_details["name"],
        "service_type": key_details["service_type"],
        "permissions": key_details["permissions"],
        "rate_limit": key_details["rate_limit"],
        "expires_at": key_details["expires_at"],
        "is_active": True,
        "last_used_at": None,
        "usage_count": 0,
        "created_at": key_details["created_at"],
    }


@router.get("/", response_model=List[ApiKeyResponse])
async def list_api_keys(
    service_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all API keys (admin only).
    """
    if current_user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can list API keys",
        )

    service = ApiKeyService(db)
    keys = service.get_api_keys(service_type=service_type, active_only=active_only)

    return [
        {
            "id": str(key.id),
            "key_prefix": key.key_prefix,
            "name": key.name,
            "service_type": key.service_type,
            "permissions": key.permissions,
            "rate_limit": key.rate_limit,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "is_active": key.is_active,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "usage_count": key.usage_count,
            "created_at": key.created_at.isoformat(),
        }
        for key in keys
    ]


@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific API key.
    """
    if current_user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view API key details",
        )

    # Validate UUID
    if not validate_uuid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid key ID format"
        )

    service = ApiKeyService(db)
    key = service.get_api_key_by_id(key_id)

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    return {
        "id": str(key.id),
        "key_prefix": key.key_prefix,
        "name": key.name,
        "service_type": key.service_type,
        "permissions": key.permissions,
        "rate_limit": key.rate_limit,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "is_active": key.is_active,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "usage_count": key.usage_count,
        "created_at": key.created_at.isoformat(),
    }


@router.post("/{key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke an API key.
    """
    if current_user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can revoke API keys",
        )

    # Validate UUID
    if not validate_uuid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid key ID format"
        )

    service = ApiKeyService(db)
    success = service.revoke_api_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )


@router.post("/{key_id}/rotate", response_model=ApiKeyWithKeyResponse)
async def rotate_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rotate an API key (revoke old and create new).
    """
    if current_user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can rotate API keys",
        )

    # Validate UUID
    if not validate_uuid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid key ID format"
        )

    service = ApiKeyService(db)
    new_key_details = service.rotate_api_key(key_id, current_user)

    if not new_key_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    return {
        "id": new_key_details["id"],
        "key": new_key_details["key"],
        "key_prefix": new_key_details["key_prefix"],
        "name": new_key_details["name"],
        "service_type": new_key_details["service_type"],
        "permissions": new_key_details["permissions"],
        "rate_limit": new_key_details["rate_limit"],
        "expires_at": new_key_details["expires_at"],
        "is_active": True,
        "last_used_at": None,
        "usage_count": 0,
        "created_at": new_key_details["created_at"],
    }


@router.get("/{key_id}/stats")
async def get_api_key_stats(
    key_id: str,
    since: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get usage statistics for an API key.
    """
    if current_user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view API key stats",
        )

    # Validate UUID
    if not validate_uuid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid key ID format"
        )

    service = ApiKeyService(db)

    # Verify key exists
    key = service.get_api_key_by_id(key_id)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    stats = service.get_usage_stats(key_id, since)

    return {
        "key_id": key_id,
        "key_name": key.name,
        "service_type": key.service_type,
        "period_start": since.isoformat() if since else None,
        "period_end": datetime.now(timezone.utc).isoformat(),
        **stats,
    }
