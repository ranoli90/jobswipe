"""
Free Embedding Service using Sentence Transformers
Provides local embeddings for job matching and semantic analysis.
"""

import logging
from typing import List, Dict, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")  # Fast and free model
CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./models")

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
                logger.info(f"Loaded embedding model: {MODEL_NAME}")
            except ImportError:
                logger.warning("Sentence Transformers library not installed")
                cls._model = None
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
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

        try:
            model = EmbeddingService.get_model()
            embedding = model.encode(job_description)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating job embedding: {str(e)}")
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

        try:
            profile_text = EmbeddingService._profile_to_text(profile)
            model = EmbeddingService.get_model()
            embedding = model.encode(profile_text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating profile embedding: {str(e)}")
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
            skills_text = ", ".join(profile['skills'])
            parts.append(f"Skills: {skills_text}")

        if profile.get("work_experience"):
            experience_text = []
            for exp in profile['work_experience']:
                if exp.get("position") and exp.get("company"):
                    experience_text.append(f"{exp['position']} at {exp['company']}")
            if experience_text:
                parts.append(f"Experience: {', '.join(experience_text)}")

        if profile.get("education"):
            education_text = []
            for edu in profile['education']:
                if edu.get("degree") and edu.get("school"):
                    education_text.append(f"{edu['degree']} from {edu['school']}")
            if education_text:
                parts.append(f"Education: {', '.join(education_text)}")

        return "\n".join(parts)

    @staticmethod
    async def calculate_semantic_similarity(
        profile_embedding: List[float],
        job_embedding: List[float]
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
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0

    @staticmethod
    async def analyze_job_match(
        profile: Dict,
        job_description: str
    ) -> Dict:
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
                "recommendations": []
            }

        try:
            # Generate embeddings
            profile_embedding = await EmbeddingService.generate_profile_embedding(profile)
            job_embedding = await EmbeddingService.generate_job_embedding(job_description)

            # Calculate similarity score
            score = await EmbeddingService.calculate_semantic_similarity(profile_embedding, job_embedding)

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
                "recommendations": ["Improve skills in missing areas"] if missing_skills else []
            }

        except Exception as e:
            logger.error(f"Error analyzing job match: {str(e)}")
            return {
                "score": 0.5,
                "analysis": f"Error analyzing match: {str(e)}",
                "missing_skills": [],
                "matched_skills": [],
                "recommendations": []
            }