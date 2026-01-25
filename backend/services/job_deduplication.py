"""
Job Deduplication Service

Provides job deduplication using fuzzy matching techniques.
"""

import logging
from typing import List, Dict, Tuple
from datetime import datetime
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from backend.db.models import Job
from db.database import get_db

logger = logging.getLogger(__name__)

# Deduplication configuration
MIN_TITLE_SIMILARITY = 85
MIN_COMPANY_SIMILARITY = 80
MIN_DESCRIPTION_SIMILARITY = 70
MAX_DUPLICATE_WINDOW_DAYS = 30


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
        
    # Lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def calculate_job_similarity(job1: Job, job2: Job) -> Dict[str, float]:
    """
    Calculate similarity between two jobs.
    
    Args:
        job1: First job
        job2: Second job
        
    Returns:
        Dictionary with similarity scores
    """
    # Normalize fields
    title1 = normalize_text(job1.title)
    title2 = normalize_text(job2.title)
    company1 = normalize_text(job1.company)
    company2 = normalize_text(job2.company)
    desc1 = normalize_text(job1.description[:500])  # Use first 500 chars
    desc2 = normalize_text(job2.description[:500])
    
    # Calculate similarity scores
    title_score = fuzz.token_sort_ratio(title1, title2)
    company_score = fuzz.token_sort_ratio(company1, company2) if company1 and company2 else 0
    desc_score = fuzz.token_sort_ratio(desc1, desc2) if desc1 and desc2 else 0
    
    return {
        "title": title_score,
        "company": company_score,
        "description": desc_score,
        "overall": (title_score * 0.4 + company_score * 0.2 + desc_score * 0.4)
    }


def is_duplicate(job1: Job, job2: Job) -> Tuple[bool, Dict[str, float]]:
    """
    Determine if two jobs are duplicates.
    
    Args:
        job1: First job
        job2: Second job
        
    Returns:
        Tuple indicating if duplicate and similarity scores
    """
    # Check if jobs are from the same source and external_id
    if job1.source == job2.source and job1.external_id == job2.external_id:
        return False, {"title": 100, "company": 100, "description": 100, "overall": 100}
        
    # Check similarity scores
    scores = calculate_job_similarity(job1, job2)
    
    # Determine if duplicate based on thresholds
    is_dup = (
        scores["title"] >= MIN_TITLE_SIMILARITY and
        (scores["company"] >= MIN_COMPANY_SIMILARITY or scores["description"] >= MIN_DESCRIPTION_SIMILARITY)
    )
    
    return is_dup, scores


def find_duplicates(jobs: List[Job]) -> List[List[Tuple[Job, float]]]:
    """
    Find duplicate jobs in a list.
    
    Args:
        jobs: List of jobs to check
        
    Returns:
        List of duplicate groups
    """
    duplicates = []
    checked_indices = set()
    
    for i, job1 in enumerate(jobs):
        if i in checked_indices:
            continue
            
        duplicate_group = []
        
        for j, job2 in enumerate(jobs):
            if i == j or j in checked_indices:
                continue
                
            is_dup, scores = is_duplicate(job1, job2)
            
            if is_dup:
                duplicate_group.append((job2, scores["overall"]))
                checked_indices.add(j)
                
        if duplicate_group:
            duplicate_group.insert(0, (job1, 100.0))  # Original job
            duplicates.append(duplicate_group)
            
        checked_indices.add(i)
        
    return duplicates


def deduplicate_jobs(jobs: List[Job]) -> Tuple[List[Job], List[List[Tuple[Job, float]]]]:
    """
    Deduplicate a list of jobs.
    
    Args:
        jobs: List of jobs to deduplicate
        
    Returns:
        Tuple of unique jobs and duplicate groups
    """
    duplicate_groups = find_duplicates(jobs)
    
    # Collect unique jobs (first job from each duplicate group)
    unique_jobs = []
    all_duplicate_ids = set()
    
    for group in duplicate_groups:
        unique_jobs.append(group[0][0])
        for job, _ in group[1:]:
            all_duplicate_ids.add(job.id)
            
    # Add jobs that have no duplicates
    for job in jobs:
        if job.id not in all_duplicate_ids and job not in unique_jobs:
            unique_jobs.append(job)
            
    return unique_jobs, duplicate_groups


def find_duplicates_in_db() -> List[List[Tuple[Job, float]]]:
    """
    Find duplicate jobs in the database.
    
    Returns:
        List of duplicate groups
    """
    db = next(get_db())
    
    try:
        # Get all jobs from the last 30 days
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=MAX_DUPLICATE_WINDOW_DAYS)
        jobs = db.query(Job).filter(Job.created_at >= cutoff_date).all()
        
        logger.info(f"Checking {len(jobs)} jobs for duplicates (last {MAX_DUPLICATE_WINDOW_DAYS} days)")
        
        duplicates = find_duplicates(jobs)
        
        logger.info(f"Found {len(duplicates)} duplicate groups")
        
        return duplicates
        
    except Exception as e:
        logger.error(f"Error finding duplicates in database: {e}")
        raise
    finally:
        db.close()


def remove_duplicates(duplicate_groups: List[List[Tuple[Job, float]]]) -> int:
    """
    Remove duplicate jobs from the database.
    
    Args:
        duplicate_groups: List of duplicate groups
        
    Returns:
        Number of duplicates removed
    """
    db = next(get_db())
    removed_count = 0
    
    try:
        for group in duplicate_groups:
            # Keep only the first job (original)
            for job, _ in group[1:]:
                db.delete(job)
                removed_count += 1
                
        db.commit()
        logger.info(f"Removed {removed_count} duplicate jobs")
        
        return removed_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing duplicates: {e}")
        raise
    finally:
        db.close()


class JobDeduplicationService:
    """Service for job deduplication"""
    
    def __init__(self):
        pass
        
    def find_duplicates(self) -> List[List[Tuple[Job, float]]]:
        """Find duplicate jobs in database"""
        return find_duplicates_in_db()
        
    def remove_duplicates(self, duplicate_groups: List[List[Tuple[Job, float]]]) -> int:
        """Remove duplicate jobs from database"""
        return remove_duplicates(duplicate_groups)
        
    def deduplicate(self) -> Tuple[int, List[List[Tuple[Job, float]]]]:
        """
        Run full deduplication process.
        
        Returns:
            Tuple of number of duplicates removed and duplicate groups
        """
        duplicate_groups = self.find_duplicates()
        removed_count = self.remove_duplicates(duplicate_groups)
        
        return removed_count, duplicate_groups