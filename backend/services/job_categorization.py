"""
Job Categorization Service

Provides job categorization using NLP techniques.
"""

import logging
from typing import List, Dict, Tuple
import spacy
from backend.db.models import Job
from backend.db.database import get_db

logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("en_core_web_sm model not found. Installing...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Job categories and keywords
JOB_CATEGORIES = {
    "software": [
        "software engineer", "developer", "programmer", "full stack", "frontend", 
        "backend", "devops", "cloud", "software developer", "engineer", "code"
    ],
    "data": [
        "data scientist", "data analyst", "machine learning", "ml", "ai", 
        "data engineer", "business intelligence", "bi", "data analytics"
    ],
    "product": [
        "product manager", "product owner", "pm", "product designer", "ux", "ui"
    ],
    "design": [
        "ux designer", "ui designer", "ux/ui", "interaction designer", 
        "visual designer", "graphic designer"
    ],
    "marketing": [
        "marketing manager", "digital marketing", "content marketing", 
        "product marketing", "marketing specialist"
    ],
    "sales": [
        "sales manager", "account executive", "sales representative", 
        "business development", "bdr", "sdr"
    ],
    "operations": [
        "operations manager", "project manager", "pmo", "operations specialist", 
        "business operations"
    ],
    "finance": [
        "financial analyst", "accountant", "finance manager", "controller", 
        "financial planning", "fp&a"
    ],
    "hr": [
        "human resources", "hr manager", "recruiter", "talent acquisition", 
        "hr business partner", "people operations"
    ],
    "customer_success": [
        "customer success manager", "account manager", "client success", 
        "customer support"
    ]
}


def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from job text.
    
    Args:
        text: Job title or description
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
        
    doc = nlp(text.lower())
    keywords = []
    
    # Extract nouns and proper nouns
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2:
            keywords.append(token.text)
            
    return list(set(keywords))


def determine_category(title: str, description: str) -> Tuple[str, float]:
    """
    Determine job category based on title and description.
    
    Args:
        title: Job title
        description: Job description
        
    Returns:
        Tuple of category and confidence score
    """
    # Combine title and description
    combined_text = f"{title} {description}"
    
    # Extract keywords
    keywords = extract_keywords(combined_text)
    
    # Calculate category scores
    category_scores = {category: 0 for category in JOB_CATEGORIES}
    
    for category, category_keywords in JOB_CATEGORIES.items():
        for keyword in category_keywords:
            if keyword.lower() in combined_text.lower():
                # Give higher weight to keywords in title
                if keyword.lower() in title.lower():
                    category_scores[category] += 2
                else:
                    category_scores[category] += 1
    
    # Find category with highest score
    max_score = max(category_scores.values())
    
    if max_score == 0:
        return "other", 0.5
        
    # Calculate confidence
    total_score = sum(category_scores.values())
    category = max(category_scores.items(), key=lambda x: x[1])[0]
    confidence = max_score / total_score
    
    return category, confidence


def categorize_job(job: Job) -> Dict[str, any]:
    """
    Categorize a single job.
    
    Args:
        job: Job object
        
    Returns:
        Dictionary with category information
    """
    category, confidence = determine_category(job.title, job.description)
    
    return {
        "category": category,
        "confidence": round(confidence, 2),
        "keywords": extract_keywords(f"{job.title} {job.description}")
    }


def categorize_jobs(jobs: List[Job]) -> List[Dict[str, any]]:
    """
    Categorize multiple jobs.
    
    Args:
        jobs: List of job objects
        
    Returns:
        List of categorized job dictionaries
    """
    results = []
    
    for job in jobs:
        category_info = categorize_job(job)
        results.append({
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "category": category_info["category"],
            "confidence": category_info["confidence"],
            "keywords": category_info["keywords"]
        })
        
    return results


def categorize_all_jobs() -> List[Dict[str, any]]:
    """
    Categorize all jobs in the database.
    
    Returns:
        List of categorized job dictionaries
    """
    db = next(get_db())
    
    try:
        jobs = db.query(Job).all()
        logger.info(f"Categorizing {len(jobs)} jobs")
        
        results = categorize_jobs(jobs)
        
        # Update jobs with categories
        for result in results:
            job = db.query(Job).filter(Job.id == result["job_id"]).first()
            if job:
                # Store category in raw_json or create new field
                if job.raw_json is None:
                    job.raw_json = {}
                job.raw_json["category"] = result["category"]
                job.raw_json["category_confidence"] = result["confidence"]
                job.raw_json["category_keywords"] = result["keywords"]
                
        db.commit()
        logger.info(f"Successfully categorized {len(results)} jobs")
        
        return results
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error categorizing jobs: {e}")
        raise
    finally:
        db.close()


def get_category_distribution() -> Dict[str, int]:
    """
    Get category distribution of jobs.
    
    Returns:
        Dictionary with category counts
    """
    db = next(get_db())
    
    try:
        jobs = db.query(Job).all()
        categorized_jobs = categorize_jobs(jobs)
        
        distribution = {category: 0 for category in JOB_CATEGORIES}
        distribution["other"] = 0
        
        for job in categorized_jobs:
            if job["category"] in distribution:
                distribution[job["category"]] += 1
            else:
                distribution["other"] += 1
                
        return distribution
        
    except Exception as e:
        logger.error(f"Error getting category distribution: {e}")
        raise
    finally:
        db.close()


class JobCategorizationService:
    """Service for job categorization"""
    
    def __init__(self):
        pass
        
    def categorize_job(self, job: Job) -> Dict[str, any]:
        """Categorize a single job"""
        return categorize_job(job)
        
    def categorize_jobs(self, jobs: List[Job]) -> List[Dict[str, any]]:
        """Categorize multiple jobs"""
        return categorize_jobs(jobs)
        
    def categorize_all_jobs(self) -> List[Dict[str, any]]:
        """Categorize all jobs in database"""
        return categorize_all_jobs()
        
    def get_category_distribution(self) -> Dict[str, int]:
        """Get category distribution"""
        return get_category_distribution()