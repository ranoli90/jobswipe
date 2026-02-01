"""
GDPR and CCPA Compliance API Router

This router provides API endpoints for GDPR and CCPA compliance features including:
- Data export (GDPR Article 20 / CCPA right to know)
- Account deletion (GDPR Article 17 / CCPA right to delete)
- Consent management
- Privacy policy and data retention information
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.routers.auth import get_current_user
from backend.db.database import get_db
from backend.db.models import User
from backend.services.compliance_service import (
    ComplianceService,
    ConsentType,
    get_compliance_service,
)

# Configure logging
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

router = APIRouter(prefix="/compliance", tags=["compliance"])


# ==================== Request/Response Models ====================

class ConsentUpdateRequest(BaseModel):
    """Request model for updating consent"""
    consent_type: str = Field(..., description="Type of consent (e.g., 'marketing_emails', 'analytics_cookies')")
    granted: bool = Field(..., description="True to grant consent, False to revoke")
    version: str = Field(default="1.0", description="Version of the consent terms")


class ConsentStatusResponse(BaseModel):
    """Response model for consent status"""
    consent_type: str
    status: str
    granted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    version: Optional[str] = None


class DataExportRequestResponse(BaseModel):
    """Response model for data export request"""
    id: str
    status: str
    format: str
    requested_at: str
    completed_at: Optional[str] = None
    expires_at: Optional[str] = None
    message: str


class DataDeletionRequestResponse(BaseModel):
    """Response model for data deletion request"""
    id: str
    status: str
    requested_at: str
    grace_period_end: Optional[str] = None
    message: str


class DataDeletionRequestBody(BaseModel):
    """Request body for data deletion"""
    reason: Optional[str] = Field(None, description="Optional reason for deletion")


class PrivacyPolicyInfoResponse(BaseModel):
    """Response model for privacy policy information"""
    version: str
    last_updated: str
    contact_email: str
    data_controller: Dict[str, str]
    legal_bases: List[Dict[str, Any]]
    user_rights: Dict[str, List[str]]
    cookies: Dict[str, List[str]]


class DataRetentionInfoResponse(BaseModel):
    """Response model for data retention information"""
    version: str
    last_updated: str
    retention_periods: Dict[str, Dict[str, Any]]
    automatic_deletion: bool
    deletion_schedule: str


class ConsentStatusSummaryResponse(BaseModel):
    """Response model for all consent status"""
    user_id: str
    consents: Dict[str, ConsentStatusResponse]
    all_granted: bool


# ==================== Helper Functions ====================

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ==================== API Endpoints ====================

@router.get(
    "/export/data",
    response_class=PlainTextResponse,
    summary="Export user data (GDPR Article 20 / CCPA)",
    description="Download all user data in JSON format. This implements the right to data portability under GDPR and the right to know under CCPA.",
)
async def export_user_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export all user data in machine-readable JSON format.
    
    This endpoint implements:
    - GDPR Article 20: Right to data portability
    - CCPA: Right to know what personal information is collected
    
    The export includes:
    - Account information
    - Profile data
    - Job interactions
    - Application history
    - Notifications
    - Consent history
    - Login history
    
    Returns:
        JSON file containing all user data
    """
    compliance_service = get_compliance_service(db)
    
    # Get or create export request
    export_request = compliance_service.request_data_export(
        user_id=current_user.id,
        format="json",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    
    # If export is already completed, return the data
    if export_request.status == "completed" and export_request.export_data:
        # Log download
        compliance_service._log_compliance_action(
            user_id=current_user.id,
            action="data_export_downloaded",
            details={"export_id": str(export_request.id)},
            ip_address=get_client_ip(request),
        )
        
        return PlainTextResponse(
            content=export_request.export_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=jobswipe_data_export_{current_user.id}.json"
            },
        )
    
    # Process the export
    export_data = compliance_service.process_data_export(export_request.id)
    
    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate data export",
        )
    
    return PlainTextResponse(
        content=export_data,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=jobswipe_data_export_{current_user.id}.json"
        },
    )


@router.post(
    "/export/request",
    response_model=DataExportRequestResponse,
    summary="Request data export",
    description="Request a data export. The export will be processed asynchronously and can be downloaded using the /export/data endpoint.",
)
async def request_data_export(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request a data export for later download.
    
    This creates an export request that will be processed. Once completed,
    the data can be downloaded using the GET /export/data endpoint.
    
    Returns:
        Export request details including status and estimated completion
    """
    compliance_service = get_compliance_service(db)
    
    export_request = compliance_service.request_data_export(
        user_id=current_user.id,
        format="json",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    
    message = (
        "Export is being processed" if export_request.status == "pending"
        else "Export is ready for download" if export_request.status == "completed"
        else f"Export status: {export_request.status}"
    )
    
    return DataExportRequestResponse(
        id=str(export_request.id),
        status=export_request.status,
        format=export_request.format,
        requested_at=export_request.requested_at.isoformat() if export_request.requested_at else None,
        completed_at=export_request.completed_at.isoformat() if export_request.completed_at else None,
        expires_at=export_request.expires_at.isoformat() if export_request.expires_at else None,
        message=message,
    )


@router.post(
    "/deletion/request",
    response_model=DataDeletionRequestResponse,
    summary="Request account deletion (GDPR Article 17 / CCPA)",
    description="Request deletion of all personal data. This initiates a 30-day grace period during which the request can be cancelled.",
)
async def request_data_deletion(
    request: Request,
    body: DataDeletionRequestBody = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request deletion of all personal data.
    
    This endpoint implements:
    - GDPR Article 17: Right to erasure (right to be forgotten)
    - CCPA: Right to delete personal information
    
    The deletion process:
    1. Creates a deletion request with PENDING status
    2. Enters a 30-day grace period where the user can cancel
    3. After grace period, data is anonymized (not hard-deleted) to maintain referential integrity
    4. All PII is removed or obfuscated
    
    Returns:
        Deletion request details including grace period end date
    """
    compliance_service = get_compliance_service(db)
    
    deletion_request = compliance_service.request_data_deletion(
        user_id=current_user.id,
        reason=body.reason if body else None,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    
    security_logger.warning(
        f"Account deletion requested for user {current_user.id}",
        extra={
            "user_id": str(current_user.id),
            "deletion_id": str(deletion_request.id),
            "ip": get_client_ip(request),
        },
    )
    
    return DataDeletionRequestResponse(
        id=str(deletion_request.id),
        status=deletion_request.status,
        requested_at=deletion_request.requested_at.isoformat() if deletion_request.requested_at else None,
        grace_period_end=deletion_request.grace_period_end.isoformat() if deletion_request.grace_period_end else None,
        message=(
            f"Your account deletion request has been received. "
            f"You have until {deletion_request.grace_period_end.strftime('%Y-%m-%d')} to cancel this request. "
            f"After that date, your personal data will be permanently anonymized."
        ),
    )


@router.post(
    "/deletion/cancel/{deletion_id}",
    summary="Cancel account deletion request",
    description="Cancel a pending account deletion request during the 30-day grace period.",
)
async def cancel_deletion_request(
    deletion_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a pending account deletion request.
    
    This can only be done during the 30-day grace period.
    Once the grace period expires, the deletion cannot be cancelled.
    
    Args:
        deletion_id: The ID of the deletion request to cancel
        
    Returns:
        Success message if cancelled, error if not found or already processed
    """
    compliance_service = get_compliance_service(db)
    
    try:
        deletion_uuid = UUID(deletion_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid deletion request ID",
        )
    
    success = compliance_service.cancel_deletion_request(
        deletion_request_id=deletion_uuid,
        user_id=current_user.id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deletion request not found or cannot be cancelled (may already be processed or outside grace period)",
        )
    
    security_logger.info(
        f"Account deletion cancelled for user {current_user.id}",
        extra={
            "user_id": str(current_user.id),
            "deletion_id": deletion_id,
            "ip": get_client_ip(request),
        },
    )
    
    return {"message": "Account deletion request has been cancelled successfully"}


@router.get(
    "/consent",
    response_model=ConsentStatusSummaryResponse,
    summary="Get current consent status",
    description="Get the current consent status for all consent types for the authenticated user.",
)
async def get_consent_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all current consent status for the authenticated user.
    
    Returns:
        Summary of all consent types and their current status
    """
    compliance_service = get_compliance_service(db)
    
    consents = compliance_service.get_user_consents(current_user.id)
    
    # Check if all required consents are granted
    required_consents = [
        ConsentType.TERMS_OF_SERVICE.value,
        ConsentType.PRIVACY_POLICY.value,
        ConsentType.DATA_PROCESSING.value,
    ]
    
    all_granted = all(
        consents.get(consent, {}).get("status") == "granted"
        for consent in required_consents
    )
    
    return ConsentStatusSummaryResponse(
        user_id=str(current_user.id),
        consents={
            k: ConsentStatusResponse(**v)
            for k, v in consents.items()
        },
        all_granted=all_granted,
    )


@router.post(
    "/consent",
    response_model=ConsentStatusResponse,
    summary="Update consent preferences",
    description="Update consent for a specific consent type. This allows granular control over data processing consent.",
)
async def update_consent(
    consent_update: ConsentUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update consent for a specific consent type.
    
    This allows users to grant or revoke consent for specific data processing activities.
    
    Consent types:
    - terms_of_service: Required for using the service
    - privacy_policy: Required for using the service
    - data_processing: Required for core service functionality
    - marketing_emails: Optional marketing communications
    - analytics_cookies: Optional analytics tracking
    - marketing_cookies: Optional marketing/advertising cookies
    - third_party_sharing: Optional sharing with third parties
    
    Returns:
        Updated consent status
    """
    compliance_service = get_compliance_service(db)
    
    # Validate consent type
    try:
        consent_type = ConsentType(consent_update.consent_type)
    except ValueError:
        valid_types = [ct.value for ct in ConsentType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid consent type. Valid types: {', '.join(valid_types)}",
        )
    
    # Prevent revoking required consents
    required_consents = [
        ConsentType.TERMS_OF_SERVICE,
        ConsentType.PRIVACY_POLICY,
        ConsentType.DATA_PROCESSING,
    ]
    
    if consent_type in required_consents and not consent_update.granted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke required consent: {consent_type.value}",
        )
    
    consent = compliance_service.update_consent(
        user_id=current_user.id,
        consent_type=consent_type,
        granted=consent_update.granted,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        consent_version=consent_update.version,
    )
    
    security_logger.info(
        f"Consent updated for user {current_user.id}: {consent_type.value} = {consent_update.granted}",
        extra={
            "user_id": str(current_user.id),
            "consent_type": consent_type.value,
            "granted": consent_update.granted,
            "ip": get_client_ip(request),
        },
    )
    
    return ConsentStatusResponse(
        consent_type=consent.consent_type,
        status=consent.status,
        granted_at=consent.granted_at.isoformat() if consent.granted_at else None,
        revoked_at=consent.revoked_at.isoformat() if consent.revoked_at else None,
        version=consent.consent_version,
    )


@router.get(
    "/privacy-policy",
    response_model=PrivacyPolicyInfoResponse,
    summary="Get privacy policy information",
    description="Get detailed information about the privacy policy, legal bases for processing, and user rights under GDPR and CCPA.",
)
async def get_privacy_policy_info(
    db: Session = Depends(get_db),
):
    """
    Get privacy policy information.
    
    Returns:
        Privacy policy details including:
        - Data controller information
        - Legal bases for processing
        - User rights under GDPR and CCPA
        - Cookie categories
    """
    compliance_service = get_compliance_service(db)
    
    return compliance_service.get_privacy_policy_info()


@router.get(
    "/data-retention",
    response_model=DataRetentionInfoResponse,
    summary="Get data retention information",
    description="Get detailed information about data retention periods for different data types.",
)
async def get_data_retention_info(
    db: Session = Depends(get_db),
):
    """
    Get data retention policy information.
    
    Returns:
        Data retention details including:
        - Retention periods for each data type
        - Legal basis for retention
        - Automatic deletion schedule
    """
    compliance_service = get_compliance_service(db)
    
    return compliance_service.get_data_retention_info()


@router.get(
    "/audit-log",
    summary="Get compliance audit log",
    description="Get audit log entries for compliance-related actions performed by the authenticated user.",
)
async def get_compliance_audit_log(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get compliance audit log for the authenticated user.
    
    This shows all compliance-related actions performed by or on behalf of the user,
    including data exports, deletion requests, and consent changes.
    
    Args:
        limit: Maximum number of log entries to return (default: 100)
        
    Returns:
        List of audit log entries
    """
    compliance_service = get_compliance_service(db)
    
    logs = compliance_service.get_audit_logs(
        user_id=current_user.id,
        limit=limit,
    )
    
    return {
        "user_id": str(current_user.id),
        "logs": [
            {
                "id": str(log.id),
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "count": len(logs),
    }


# ==================== Admin Endpoints ====================

@router.post(
    "/admin/enforce-retention",
    summary="[Admin] Enforce data retention policies",
    description="Manually trigger enforcement of data retention policies. This endpoint is restricted to admin users.",
    include_in_schema=False,  # Hide from public API docs
)
async def enforce_retention_policies(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually enforce data retention policies.
    
    This endpoint is restricted to admin users and triggers:
    - Deletion of expired export files
    - Deletion of old audit logs
    - Deletion of old failed login attempts
    
    Returns:
        Count of deleted records by type
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    compliance_service = get_compliance_service(db)
    
    deleted_counts = compliance_service.enforce_retention_policies()
    
    security_logger.warning(
        f"Retention policies enforced by admin {current_user.id}",
        extra={
            "admin_id": str(current_user.id),
            "deleted_counts": deleted_counts,
            "ip": get_client_ip(request),
        },
    )
    
    return {
        "message": "Retention policies enforced successfully",
        "deleted_counts": deleted_counts,
        "enforced_at": datetime.utcnow().isoformat(),
    }
