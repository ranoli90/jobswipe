"""
Job Matching Service

Handles job recommendations and matching using hybrid BM25 + embeddings + rule-based approach.
"""

import json
import logging
import math
import time
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from opentelemetry import trace
from sqlalchemy import or_

from backend.db.database import get_db
from backend.db.models import CandidateProfile, Job, UserJobInteraction
from backend.metrics import (get_metrics_score_range, job_matching_duration,
                             job_matching_requests_total, jobs_matched_total)
from backend.services.embedding_service import EmbeddingService
from backend.tracing import get_tracer

tracer = get_tracer(__name__)

logger = logging.getLogger(__name__)

# Initialize Embedding service
embedding_service = EmbeddingService()

# BM25 Parameters
BM25_K1 = 1.5
BM25_B = 0.75
BM25_EPSILON = 0.25


def preprocess_text(text: str) -> List[str]:
    """Preprocess text for BM25 matching"""
    if not text:
        return []
    # Remove non-printable characters and special characters
    import re

    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    # Convert to lowercase, remove punctuation, and split into tokens
    text = text.lower()
    # Remove punctuation
    import string

    text = text.translate(str.maketrans("", "", string.punctuation))
    # Split into tokens
    tokens = text.split()
    # Remove stopwords (simple version)
    stopwords = set(
        [
            "the",
            "and",
            "for",
            "with",
            "you",
            "your",
            "our",
            "we",
            "is",
            "are",
            "to",
            "in",
            "on",
            "at",
            "of",
        ]
    )
    return [token for token in tokens if token not in stopwords and len(token) > 2]


def compute_bm25_score(job: Job, profile: CandidateProfile) -> float:
    """
    Compute BM25 score between a job and candidate profile

    Args:
        job: Job to score
        profile: Candidate profile

    Returns:
        BM25 score (0.0 - 1.0)
    """
    # Get job text content
    job_text = f"{job.title} {job.description} {job.company}"
    job_tokens = preprocess_text(job_text)

    # Get profile text content
    profile_text = []
    if profile.skills:
        profile_text.extend(profile.skills)
    if profile.work_experience:
        for exp in profile.work_experience:
            if exp.get("position"):
                profile_text.append(exp["position"])
            if exp.get("company"):
                profile_text.append(exp["company"])
    if profile.education:
        for edu in profile.education:
            if edu.get("degree"):
                profile_text.append(edu["degree"])
            if edu.get("school"):
                profile_text.append(edu["school"])
    if profile.headline:
        profile_text.append(profile.headline)

    profile_text = " ".join(profile_text)
    profile_tokens = preprocess_text(profile_text)

    # If no meaningful tokens, return 0
    if not job_tokens or not profile_tokens:
        return 0.0

    # Calculate term frequencies
    job_tf = Counter(job_tokens)
    profile_tf = Counter(profile_tokens)

    # Calculate document length
    job_length = len(job_tokens)
    avg_document_length = 200  # Assumed average document length

    # Calculate BM25 score
    score = 0.0
    for term, freq in profile_tf.items():
        if term not in job_tf:
            continue

        # Term frequency in job
        tf = job_tf[term]

        # Calculate numerator and denominator
        numerator = tf * (BM25_K1 + 1)
        denominator = tf + BM25_K1 * (
            1 - BM25_B + BM25_B * (job_length / avg_document_length)
        )

        # Add to score
        score += freq * (numerator / denominator)

    # Normalize score
    max_possible_score = len(profile_tokens) * (BM25_K1 + 1)
    normalized_score = score / (max_possible_score if max_possible_score > 0 else 1)

    return min(1.0, normalized_score)


import uuid


async def get_personalized_jobs(
    user_id: uuid.UUID, cursor: Optional[str] = None, page_size: int = 20, db=None
) -> List[Dict]:
        """
        Get personalized job recommendations for a user.
    
        Args:
            user_id: User ID
            cursor: Optional cursor for pagination
            page_size: Number of jobs to return per page
            db: Database session
    
        Returns:
            List of matched jobs with scores
        """
        if db is None:
            db = next(get_db())
    
        try:
            # Get candidate profile
            profile = (
                db.query(CandidateProfile)
                .filter(CandidateProfile.user_id == user_id)
                .first()
            )
    
            if not profile:
                # If no profile, return latest jobs
                query = db.query(Job).order_by(Job.created_at.desc())
                jobs = query.limit(page_size).all()
                return [{"id": str(job.id), "score": 0.0} for job in jobs]
    
            # Hybrid matching approach
            query = db.query(Job)
    
            # Rule-based filters
            if profile.skills:
                # Filter by skills (simple keyword matching for MVP)
                skill_filters = [
                    Job.description.ilike("%" + skill + "%") for skill in profile.skills
                ]
                if skill_filters:
                    query = query.filter(or_(*skill_filters))

            if profile.location:
                # Filter by location proximity (simple string matching for MVP)
                query = query.filter(Job.location.ilike("%" + profile.location + "%"))

            query = query.order_by(Job.created_at.desc())

            # Exclude jobs user has already interacted with
            interacted_job_ids = [
                interaction.job_id
                for interaction in db.query(UserJobInteraction)
                .filter(UserJobInteraction.user_id == user_id)
                .all()
            ]

            query = query.filter(Job.id.notin_(interacted_job_ids))

            # Pagination
            if cursor:
                query = query.filter(Job.id > cursor)

            jobs = query.limit(page_size).all()

            logger.info("Found %d jobs for user %s", len(jobs), user_id)

            # Calculate scores for each job
            scored_jobs = []
            for job in jobs:
                score = await calculate_job_score(job, profile)
                scored_jobs.append({"job": job, "score": score})

            # Sort jobs by score descending
            scored_jobs.sort(key=lambda x: x["score"], reverse=True)

            logger.info("Returning %d jobs sorted by score", len(scored_jobs))

            return scored_jobs

        except Exception as e:
            logger.error("Error getting personalized jobs for user %s: %s", user_id, str(e))
            raise


async def calculate_job_score(job: Job, profile: CandidateProfile) -> float:
    """
    Calculate job match score for a candidate profile using hybrid approach.

    Args:
        job: Job to score
        profile: Candidate profile

    Returns:
        Match score (0.0 - 1.0)
    """
    score = 0.0

    # BM25 scoring (primary method)
    bm25_score = compute_bm25_score(job, profile)
    score += bm25_score * 0.5
    logger.info("BM25 score: %.2f", bm25_score)

    # Semantic matching with embeddings
    if embedding_service.is_available() and job.description:
        logger.info("Calculating semantic similarity with embeddings")

        # Convert profile to dictionary for embedding service
        profile_dict = {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "skills": profile.skills or [],
            "work_experience": profile.work_experience or [],
            "education": profile.education or [],
        }

        # Get match analysis from embedding service
        match_analysis = await embedding_service.analyze_job_match(
            profile_dict, job.description
        )

        # Use embedding score if available
        if "score" in match_analysis:
            semantic_score = match_analysis["score"]
            score += semantic_score * 0.3
            logger.info(f"Embedding semantic score: {float(semantic_score):.2f}")

    # Rule-based matching (for additional features)
    logger.info("Adding rule-based matching components")

    # Skill matching
    if profile.skills and job.description:
        skill_matches = 0
        for skill in profile.skills:
            if skill.lower() in job.description.lower():
                skill_matches += 1

        if skill_matches > 0:
            skill_score = (skill_matches / len(profile.skills)) * 0.1
            score += skill_score
            logger.info("Skill match score: %.2f", skill_score)

    # Location matching
    if profile.location and job.location:
        if profile.location.lower() in job.location.lower():
            location_score = 0.05
            score += location_score
            logger.info("Location match score: %.2f", location_score)

    # Experience matching (simple keyword based)
    if profile.work_experience and job.description:
        experience_matches = 0
        for exp in profile.work_experience:
            if (
                exp.get("position")
                and exp["position"].lower() in job.description.lower()
            ):
                experience_matches += 1

        if experience_matches > 0:
            experience_score = (
                experience_matches / len(profile.work_experience)
            ) * 0.05
            score += experience_score
            logger.info("Experience match score: %.2f", experience_score)

    final_score = min(1.0, score)
    logger.info("Final job match score: %.2f", final_score)

    return final_score


async def get_job_matches_for_profile(
    profile: CandidateProfile,
    limit: int = 20,
    offset: int = 0,
    min_score: float = 0.0,
    db=None,
) -> List[Dict]:
    """
    Get job matches for a candidate profile with scoring and filtering.

    Args:
        profile: Candidate profile
        limit: Number of matches to return (default: 20)
        offset: Offset for pagination (default: 0)
        min_score: Minimum score threshold (default: 0.0)
        db: Database session

    Returns:
        List of matched jobs with scores and metadata
    """
    start_time = time.time()

    with tracer.start_as_current_span("get_job_matches_for_profile") as span:
        span.set_attribute("profile.id", str(profile.id))
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)
        span.set_attribute("min_score", min_score)

        if db is None:
            db = next(get_db())

        try:
            # Get recent jobs (limit to 1000 for performance)
            jobs = db.query(Job).order_by(Job.created_at.desc()).limit(1000).all()

            # Calculate scores for all jobs
            scored_jobs = []
            for job in jobs:
                score = await calculate_job_score(job, profile)
                if score >= min_score:
                    scored_jobs.append(
                        {
                            "job": job,
                            "score": score,
                            "metadata": {
                                "bm25_score": compute_bm25_score(job, profile),
                                "has_skill_match": any(
                                    skill.lower() in job.description.lower()
                                    for skill in (profile.skills or [])
                                ),
                                "has_location_match": bool(
                                    profile.location
                                    and job.location
                                    and profile.location.lower() in job.location.lower()
                                ),
                            },
                        }
                    )

            # Sort by score descending
            scored_jobs.sort(key=lambda x: x["score"], reverse=True)

            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            paginated_jobs = scored_jobs[start_idx:end_idx]

            # Record metrics
            duration = time.time() - start_time
            job_matching_duration.observe(duration)
            job_matching_requests_total.labels(result="success").inc()

            # Record score distribution
            for job_data in paginated_jobs:
                score_range = get_metrics_score_range(job_data["score"])
                jobs_matched_total.labels(score_range=score_range).inc()

            span.set_attribute("matches.found", len(paginated_jobs))
            span.set_attribute("matches.total", len(scored_jobs))

            logger.info("Found %d matches out of %d total jobs for profile %s", len(paginated_jobs), len(scored_jobs), profile.id)

            return paginated_jobs

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            job_matching_duration.observe(duration)
            job_matching_requests_total.labels(result="error").inc()

            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            logger.error("Error getting job matches for profile %s: %s", profile.id, str(e))
            raise


def get_job_recommendations_for_profile(
    profile: CandidateProfile, limit: int = 20
) -> List[dict]:
    """
    Get job recommendations with scores for a candidate profile.

    Args:
        profile: Candidate profile
        limit: Number of recommendations to return

    Returns:
        List of jobs with scores
    """
    db = next(get_db())

    try:
        jobs = db.query(Job).order_by(Job.created_at.desc()).limit(100).all()

        recommended_jobs = []
        for job in jobs:
            score = calculate_job_score(job, profile)
            recommended_jobs.append({"job": job, "score": score})

        # Sort by score descending
        recommended_jobs.sort(key=lambda x: x["score"], reverse=True)

        # Return top N recommendations
        return recommended_jobs[:limit]

    except Exception as e:
        logger.error("Error getting recommendations for profile %s: %s", profile.id, str(e))
        raise
    finally:
        db.close()
