"""
Analytics Router

Provides endpoints for accessing advanced analytics and reporting features.
"""

import logging
import os
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.api.routers.auth import get_current_user
from backend.config import settings
from backend.db.models import User
from backend.services.analytics_service import analytics_service
from backend.services.job_ingestion_service import job_ingestion_service

router = APIRouter()
logger = logging.getLogger(__name__)

security = HTTPBearer()

# API key for analytics operations
ANALYTICS_API_KEY = settings.analytics_api_key


class ReportRequest(BaseModel):
    """Request model for report generation"""

    report_type: str
    time_range: int = 30
    format: str = "json"


class ReportResponse(BaseModel):
    """Response model for report generation"""

    success: bool
    report_type: str
    time_range: int
    format: str
    file_path: str
    file_name: str
    size: int
    generated_at: str


class AnalyticsMetrics(BaseModel):
    """Response model for analytics metrics"""

    total_users: int
    total_jobs: int
    total_interactions: int
    total_applications: int
    avg_match_score: float
    success_rate: float
    daily_growth: float


@router.get("/metrics", response_model=AnalyticsMetrics)
async def get_analytics_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get overall analytics metrics.

    Returns:
        Summary of key analytics metrics
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        # This is a placeholder. In a real implementation, this would query the database
        return AnalyticsMetrics(
            total_users=1250,
            total_jobs=5000,
            total_interactions=35000,
            total_applications=4200,
            avg_match_score=0.78,
            success_rate=0.65,
            daily_growth=0.08,
        )

    except Exception as e:
        logger.error("Error retrieving analytics metrics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics metrics: {str(e)}",
        )


@router.post("/generate-report", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an analytics report.

    Args:
        request: Report generation parameters

    Returns:
        Report response with download information
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    valid_report_types = ["matching_accuracy", "user_behavior", "job_market"]
    if request.report_type not in valid_report_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type. Valid types: {', '.join(valid_report_types)}",
        )

    valid_formats = ["json", "csv", "html"]
    if request.format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Valid formats: {', '.join(valid_formats)}",
        )

    try:
        logger.info(
            f"Generating {request.report_type} report in {request.format} format"
        )

        # Generate report
        file_path = await analytics_service.export_report(
            report_type=request.report_type, format=request.format
        )

        # Get file information
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        return ReportResponse(
            success=True,
            report_type=request.report_type,
            time_range=request.time_range,
            format=request.format,
            file_path=file_path,
            file_name=file_name,
            size=file_size,
            generated_at="2026-01-25T00:00:00Z",  # Mock timestamp
        )

    except Exception as e:
        logger.error("Error generating report: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.get("/download-report/{file_path:path}")
async def download_report(
    file_path: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Download a generated report.

    Args:
        file_path: Path to the report file

    Returns:
        File response for download
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found"
            )

        file_name = os.path.basename(file_path)

        return FileResponse(
            path=file_path, filename=file_name, media_type="application/octet-stream"
        )

    except Exception as e:
        logger.error("Error downloading report: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report: {str(e)}",
        )


@router.get("/matching-accuracy/{time_range}")
async def get_matching_accuracy_report(
    time_range: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get matching accuracy report.

    Args:
        time_range: Number of days to include in the report

    Returns:
        Matching accuracy report
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        report = await analytics_service.get_matching_accuracy_report(time_range)
        return report

    except Exception as e:
        logger.error("Error retrieving matching accuracy report: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve matching accuracy report: {str(e)}",
        )


@router.get("/user-behavior/{user_id}")
async def get_user_behavior_report(
    user_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get user behavior report.

    Args:
        user_id: ID of the user

    Returns:
        User behavior report
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        report = await analytics_service.get_user_behavior_report(user_id)
        return report

    except Exception as e:
        logger.error("Error retrieving user behavior report: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user behavior report: {str(e)}",
        )


@router.get("/job-market-analysis")
async def get_job_market_analysis(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get job market analysis.

    Returns:
        Job market analysis report
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        report = await analytics_service.get_job_market_analysis()
        return report

    except Exception as e:
        logger.error("Error retrieving job market analysis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job market analysis: {str(e)}",
        )


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get dashboard summary with key metrics for real-time monitoring.

    Returns:
        Dashboard summary with key metrics
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        summary = await analytics_service.get_dashboard_summary()
        return summary

    except Exception as e:
        logger.error("Error retrieving dashboard summary: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard summary: {str(e)}",
        )


@router.get("/engagement-trends")
async def get_engagement_trends(
    days: int = 30,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get user engagement trends over time.

    Args:
        days: Number of days to analyze

    Returns:
        Engagement trends data
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        trends = await analytics_service.get_engagement_trends(days)
        return trends

    except Exception as e:
        logger.error("Error retrieving engagement trends: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagement trends: {str(e)}",
        )


@router.get("/job-performance/{job_id}")
async def get_job_performance(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get performance metrics for a specific job.

    Args:
        job_id: ID of the job

    Returns:
        Job performance metrics
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        performance = await analytics_service.get_job_performance(job_id)
        return performance

    except Exception as e:
        logger.error("Error retrieving job performance: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job performance: {str(e)}",
        )


@router.get("/application-funnel")
async def get_application_funnel(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    Get application funnel analytics showing conversion rates.

    Returns:
        Application funnel data
    """
    if credentials.credentials != ANALYTICS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid analytics API key"
        )

    try:
        funnel = await analytics_service.get_application_funnel()
        return funnel

    except Exception as e:
        logger.error("Error retrieving application funnel: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application funnel: {str(e)}",
        )
