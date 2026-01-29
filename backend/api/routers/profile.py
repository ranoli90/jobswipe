"""
Profile Router

Handles candidate profile management including resume upload and parsing.
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.middleware.file_validation import validate_resume_file
from backend.api.routers.auth import get_current_user
from api.validators import (name_validator, phone_validator,
                                    string_validator)
from backend.db.database import get_db
from backend.db.models import CandidateProfile, User
from services.resume_parser_enhanced import parse_resume_enhanced
from services.storage import upload_file

router = APIRouter()

logger = logging.getLogger(__name__)


class CandidateProfilePreferences(BaseModel):
    """Request model for candidate preferences"""

    job_types: Optional[list] = None
    remote_preference: Optional[str] = None
    experience_level: Optional[str] = None


class CandidateProfileUpdate(BaseModel):
    """Request model for updating candidate profile"""

    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    skills: Optional[list] = None
    experience: Optional[list] = None
    education: Optional[list] = None
    preferences: Optional[CandidateProfilePreferences] = None

    # Add validators
    _full_name_validator = name_validator("full_name")
    _phone_validator = phone_validator()
    _location_validator = string_validator("location")
    _headline_validator = string_validator("headline")


class CandidateProfileResponse(BaseModel):
    """Response model for candidate profile"""

    id: str
    full_name: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    headline: Optional[str]
    work_experience: Optional[list]
    education: Optional[list]
    skills: Optional[list]
    resume_file_url: Optional[str]
    parsed_at: Optional[str]
    preferences: Optional[CandidateProfilePreferences] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, profile):
        obj = super().from_orm(profile)
        # Map database fields to preferences
        if profile.job_types or profile.remote_preference or profile.experience_level:
            obj.preferences = CandidateProfilePreferences(
                job_types=profile.job_types,
                remote_preference=profile.remote_preference,
                experience_level=profile.experience_level,
            )
        return obj


@router.post("/resume", response_model=CandidateProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload and parse resume file.

    Args:
        file: Resume file (PDF/DOCX)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message and parsed profile
    """
    try:
        # Validate file upload
        await validate_file_upload(file)

        # Read file content
        file_content = await file.read()

        # Upload to storage
        file_path = f"resumes/{current_user.id}/{file.filename}"
        upload_file(file_path, file_content)

        # Parse resume
        parsed_data = await parse_resume_enhanced(file_content, file.filename)

        # Get or create candidate profile
        profile = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = CandidateProfile(user_id=current_user.id)

        # Update profile with parsed data
        profile.full_name = parsed_data.get("full_name", profile.full_name)
        profile.phone = parsed_data.get("phone", profile.phone)
        profile.location = parsed_data.get("location", profile.location)
        profile.headline = parsed_data.get("headline", profile.headline)
        profile.work_experience = parsed_data.get(
            "work_experience", profile.work_experience
        )
        profile.education = parsed_data.get("education", profile.education)
        profile.skills = parsed_data.get("skills", profile.skills)
        profile.resume_file_url = file_path
        profile.parsed_at = parsed_data.get("parsed_at")

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return CandidateProfileResponse.from_orm(profile)

    except Exception as e:
        logger.error("Error uploading resume for user %s: %s", ('current_user.id', 'str(e)'))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and parse resume",
        )


@router.get("/", response_model=CandidateProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get current user's candidate profile.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Candidate profile
    """
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please upload a resume first.",
        )

    return CandidateProfileResponse.from_orm(profile)


@router.put("/", response_model=CandidateProfileResponse)
async def update_profile(
    profile_data: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update candidate profile.

    Args:
        profile_data: Profile update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated candidate profile
    """
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        profile = CandidateProfile(user_id=current_user.id)

    # Update fields
    if profile_data.full_name is not None:
        profile.full_name = profile_data.full_name
    if profile_data.phone is not None:
        profile.phone = profile_data.phone
    if profile_data.location is not None:
        profile.location = profile_data.location
    if profile_data.headline is not None:
        profile.headline = profile_data.headline
    if profile_data.skills is not None:
        profile.skills = profile_data.skills
    if profile_data.experience is not None:
        profile.work_experience = profile_data.experience
    if profile_data.education is not None:
        profile.education = profile_data.education

    # Update preferences
    if profile_data.preferences is not None:
        if profile_data.preferences.job_types is not None:
            profile.job_types = profile_data.preferences.job_types
        if profile_data.preferences.remote_preference is not None:
            profile.remote_preference = profile_data.preferences.remote_preference
        if profile_data.preferences.experience_level is not None:
            profile.experience_level = profile_data.preferences.experience_level

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return CandidateProfileResponse.from_orm(profile)
