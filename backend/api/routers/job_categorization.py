"""
Job Categorization Router

Provides endpoints for managing job categorization operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict
from pydantic import BaseModel
import logging
import os

from backend.services.job_categorization import JobCategorizationService, categorize_all_jobs, get_category_distribution
from backend.api.routers.auth import get_current_user
from backend.db.models import User

router = APIRouter(prefix="/api/categorize", tags=["categorization"])
logger = logging.getLogger(__name__)

security = HTTPBearer()

# API key for categorization operations (separate from user authentication)
CATEGORIZATION_API_KEY = os.getenv("CATEGORIZATION_API_KEY", "default-categorization-key")

categorization_service = JobCategorizationService()


class CategorizationResponse(BaseModel):
    """Response model for categorization operations"""
    success: bool
    message: str
    jobs_categorized: int
    categories: List[Dict]


class CategoryDistribution(BaseModel):
    """Response model for category distribution"""
    success: bool
    message: str
    distribution: Dict[str, int]


@router.post("/all")
async def categorize_all(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Categorize all jobs in the database.
    
    Args:
        credentials: API key for authentication
        
    Returns:
        Categorization response
    """
    # Validate API key
    if credentials.credentials != CATEGORIZATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid categorization API key"
        )
        
    logger.info("Categorizing all jobs")
    
    try:
        results = categorize_all_jobs()
        
        # Count jobs per category
        category_counts = {}
        for result in results:
            category = result["category"]
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
            
        return {
            "success": True,
            "message": f"Successfully categorized {len(results)} jobs",
            "jobs_categorized": len(results),
            "category_counts": category_counts
        }
        
    except Exception as e:
        logger.error(f"Error categorizing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to categorize jobs: {str(e)}"
        )


@router.get("/distribution")
async def get_distribution(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get category distribution of jobs.
    
    Args:
        credentials: API key for authentication
        
    Returns:
        Category distribution
    """
    # Validate API key
    if credentials.credentials != CATEGORIZATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid categorization API key"
        )
        
    logger.info("Getting category distribution")
    
    try:
        distribution = get_category_distribution()
        
        return {
            "success": True,
            "message": "Category distribution retrieved successfully",
            "distribution": distribution
        }
        
    except Exception as e:
        logger.error(f"Error getting category distribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category distribution: {str(e)}"
        )


@router.post("/run")
async def run_categorization(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Run complete categorization process.
    
    Args:
        credentials: API key for authentication
        
    Returns:
        Categorization response
    """
    # Validate API key
    if credentials.credentials != CATEGORIZATION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid categorization API key"
        )
        
    logger.info("Running categorization process")
    
    try:
        results = categorization_service.categorize_all_jobs()
        
        # Count jobs per category
        category_counts = {}
        for result in results:
            category = result["category"]
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
            
        return {
            "success": True,
            "message": f"Successfully categorized {len(results)} jobs",
            "jobs_categorized": len(results),
            "category_counts": category_counts
        }
        
    except Exception as e:
        logger.error(f"Error running categorization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run categorization: {str(e)}"
        )