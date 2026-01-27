"""
Free Embedding Service using Sentence Transformers
Provides local embeddings for job matching and semantic analysis.
"""

import hashlib
import json
import logging
import os
from typing import Dict, List, Optional

import numpy as np
import redis
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")  # Fast and free model
CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./models")

# Redis for caching embeddings
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True
)


class EmbeddingService:
    """Service for generating embeddings using Sentence Transformers"""

    _model = None

    @classmethod
    def get_model(cls):
        """Get or load the embedding model"""
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                cls._model = SentenceTransformer(MODEL_NAME, cache_folder=CACHE_DIR)
                logger.info("Loaded embedding model: %s", MODEL_NAME)
            except ImportError:
                logger.warning("Sentence Transformers library not installed")
                cls._model = None
            except Exception as e:
                logger.error("Failed to load embedding model: %s", e)
                cls._model = None
        return cls._model

    @staticmethod
    def is_available() -> bool:
        """Check if embedding service is available"""
        return EmbeddingService.get_model() is not None

    @staticmethod
    async def generate_job_embedding(job_description: str) -> List[float]:
        """
        Generate embedding for a job description.

        Args:
            job_description: Job description text

        Returns:
            List of floating point numbers representing the embedding
        """
        if not EmbeddingService.is_available():
            logger.warning("Embedding service not available")
            return []

        # Create cache key
        cache_key = f"job_embedding:{hashlib.md5(job_description.encode()).hexdigest()}"
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Redis not available, continue

        try:
            model = EmbeddingService.get_model()
            embedding = await asyncio.to_thread(model.encode, job_description)
            embedding_list = await asyncio.to_thread(embedding.tolist)

            # Cache the result
            try:
                redis_client.setex(
                    cache_key, 3600, json.dumps(embedding_list)
                )  # Cache for 1 hour
            except Exception:
                pass  # Ignore cache errors

            return embedding_list
        except Exception as e:
            logger.error("Error generating job embedding: %s", str(e))
            return []

    @staticmethod
    async def generate_profile_embedding(profile: Dict) -> List[float]:
        """
        Generate embedding for a candidate profile.

        Args:
            profile: Candidate profile dictionary

        Returns:
            List of floating point numbers representing the embedding
        """
        if not EmbeddingService.is_available():
            logger.warning("Embedding service not available")
            return []

        profile_text = EmbeddingService._profile_to_text(profile)
        # Create cache key
        cache_key = (
            f"profile_embedding:{hashlib.md5(profile_text.encode()).hexdigest()}"
        )
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Redis not available, continue

        try:
            model = EmbeddingService.get_model()
            embedding = await asyncio.to_thread(model.encode, profile_text)
            embedding_list = await asyncio.to_thread(embedding.tolist)

            # Cache the result
            try:
                redis_client.setex(
                    cache_key, 3600, json.dumps(embedding_list)
                )  # Cache for 1 hour
            except Exception:
                pass  # Ignore cache errors

            return embedding_list
        except Exception as e:
            logger.error("Error generating profile embedding: %s", str(e))
            return []

    @staticmethod
    def _profile_to_text(profile: Dict) -> str:
        """Convert profile dictionary to text for embedding"""
        parts = []

        if profile.get("full_name"):
            parts.append(f"Name: {profile['full_name']}")

        if profile.get("headline"):
            parts.append(f"Headline: {profile['headline']}")

        if profile.get("skills"):
            skills_text = ", ".join(profile["skills"])
            parts.append(f"Skills: {skills_text}")

        if profile.get("work_experience"):
            experience_text = []
            for exp in profile["work_experience"]:
                if exp.get("position") and exp.get("company"):
                    experience_text.append(f"{exp['position']} at {exp['company']}")
            if experience_text:
                parts.append(f"Experience: {', '.join(experience_text)}")

        if profile.get("education"):
            education_text = []
            for edu in profile["education"]:
                if edu.get("degree") and edu.get("school"):
                    education_text.append(f"{edu['degree']} from {edu['school']}")
            if education_text:
                parts.append(f"Education: {', '.join(education_text)}")

        return "\n".join(parts)

    @staticmethod
    async def calculate_semantic_similarity(
        profile_embedding: List[float], job_embedding: List[float]
    ) -> float:
        """
        Calculate semantic similarity between profile and job embeddings.

        Args:
            profile_embedding: Candidate profile embedding
            job_embedding: Job description embedding

        Returns:
            Similarity score between 0 and 1
        """
        if not profile_embedding or not job_embedding:
            return 0.0

        try:
            profile_vec = np.array(profile_embedding).reshape(1, -1)
            job_vec = np.array(job_embedding).reshape(1, -1)

            similarity = cosine_similarity(profile_vec, job_vec)[0][0]

            # Normalize to 0-1 (cosine is -1 to 1, but for text it's usually positive)
            normalized_score = (similarity + 1) / 2

            return float(normalized_score)

        except Exception as e:
            logger.error("Error calculating semantic similarity: %s", str(e))
            return 0.0

    @staticmethod
    async def analyze_job_match(profile: Dict, job_description: str) -> Dict:
        """
        Analyze job match using embeddings and rule-based analysis.

        Args:
            profile: Candidate profile
            job_description: Job description

        Returns:
            Dictionary with match analysis and score
        """
        if not EmbeddingService.is_available():
            logger.warning("Embedding service not available")
            return {
                "score": 0.5,
                "analysis": "Embedding service not available",
                "missing_skills": [],
                "matched_skills": [],
                "recommendations": [],
            }

        try:
            # Generate embeddings
            profile_embedding = await EmbeddingService.generate_profile_embedding(
                profile
            )
            job_embedding = await EmbeddingService.generate_job_embedding(
                job_description
            )

            # Calculate similarity score
            score = await EmbeddingService.calculate_semantic_similarity(
                profile_embedding, job_embedding
            )

            # Rule-based analysis
            profile_skills = set(profile.get("skills", []))
            job_words = set(job_description.lower().split())
            matched_skills = profile_skills.intersection(job_words)
            missing_skills = profile_skills - matched_skills

            analysis = f"Semantic similarity score: {score:.2f}. Matched skills: {list(matched_skills)}"

            return {
                "score": score,
                "analysis": analysis,
                "matched_skills": list(matched_skills),
                "missing_skills": list(missing_skills),
                "recommendations": (
                    ["Improve skills in missing areas"] if missing_skills else []
                ),
            }

        except Exception as e:
            logger.error("Error analyzing job match: %s", str(e))
            return {
                "score": 0.5,
                "analysis": f"Error analyzing match: {str(e)}",
                "missing_skills": [],
                "matched_skills": [],
                "recommendations": [],
            }
