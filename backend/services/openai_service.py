"""
OpenAI Integration Service
Provides access to OpenAI API for job matching and semantic analysis.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# Configuration - OpenAI removed as paid service
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
# OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
# OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

# Ollama Configuration (preferred for cost optimization)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "2000"))

# Initialize clients (dynamically) - Ollama only
ollama_client = None


def get_client():
    """Get or create client instance using Ollama (OpenAI removed as paid service)"""
    global ollama_client

    # Try Ollama
    if not ollama_client:
        try:
            ollama_client = OpenAI(
                base_url=OLLAMA_BASE_URL,
                api_key="ollama",  # Ollama doesn't require a real API key
            )
            # Test the connection
            ollama_client.models.list()
            logger.info("Ollama service initialized successfully")
            return ollama_client
        except Exception as e:
            logger.warning(
                f"Ollama not available: {str(e)}. Falling back to rule-based matching."
            )
            ollama_client = None

    return ollama_client


# Initialize client on module load
client = get_client()


class OpenAIService:
    """Service for interacting with OpenAI API"""

    @staticmethod
    def is_available() -> bool:
        """Check if AI service integration is available (Ollama only, OpenAI removed)"""
        # Check Ollama
        try:
            test_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
            test_client.models.list()
            return True
        except Exception:
            return False

    @staticmethod
    async def generate_job_embedding(job_description: str) -> List[float]:
        """
        Generate embedding for a job description using AI API.

        Args:
            job_description: Job description text

        Returns:
            List of floating point numbers representing the embedding
        """
        if not OpenAIService.is_available():
            logger.warning("AI service not available, returning empty embedding")
            return []

        try:
            client = get_client()
            # Use Ollama's embedding model
            model = OLLAMA_EMBEDDING_MODEL
            response = client.embeddings.create(input=job_description, model=model)

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating job embedding: {str(e)}")
            return []

    @staticmethod
    async def generate_profile_embedding(profile: Dict) -> List[float]:
        """
        Generate embedding for a candidate profile using AI API.

        Args:
            profile: Candidate profile dictionary with skills, experience, etc.

        Returns:
            List of floating point numbers representing the embedding
        """
        if not OpenAIService.is_available():
            logger.warning("AI service not available, returning empty embedding")
            return []

        try:
            # Convert profile to text for embedding
            profile_text = OpenAIService._profile_to_text(profile)

            client = get_client()
            # Use Ollama's embedding model
            model = OLLAMA_EMBEDDING_MODEL
            response = client.embeddings.create(input=profile_text, model=model)

            return response.data[0].embedding

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

        # Calculate cosine similarity
        try:
            import numpy as np
            from numpy.linalg import norm

            profile_vec = np.array(profile_embedding)
            job_vec = np.array(job_embedding)

            cosine_similarity = np.dot(profile_vec, job_vec) / (
                norm(profile_vec) * norm(job_vec)
            )

            # Normalize to 0-1 range
            normalized_score = (cosine_similarity + 1) / 2

            return float(normalized_score)

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0

    @staticmethod
    async def analyze_job_match(profile: Dict, job_description: str) -> Dict:
        """
        Analyze job match using OpenAI's GPT model.

        Args:
            profile: Candidate profile
            job_description: Job description

        Returns:
            Dictionary with match analysis and score
        """
        if not OpenAIService.is_available():
            logger.warning("OpenAI service not available, returning default match")
            return {
                "score": 0.5,
                "analysis": "OpenAI service not available",
                "missing_skills": [],
                "matched_skills": [],
                "recommendations": [],
            }

        try:
            prompt = OpenAIService._create_match_analysis_prompt(
                profile, job_description
            )

            client = get_client()
            response = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical recruiter analyzing job fit between a candidate and a job description. "
                        "Provide detailed analysis including: match score (0-1), matched skills, missing skills, "
                        "and recommendations for the candidate. Be honest and realistic.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=OLLAMA_TEMPERATURE,
                max_tokens=OLLAMA_MAX_TOKENS,
            )

            analysis = response.choices[0].message.content

            return OpenAIService._parse_match_analysis(analysis)

        except Exception as e:
            logger.error(f"Error analyzing job match: {str(e)}")
            return {
                "score": 0.5,
                "analysis": f"Error analyzing match: {str(e)}",
                "missing_skills": [],
                "matched_skills": [],
                "recommendations": [],
            }

    @staticmethod
    def _create_match_analysis_prompt(profile: Dict, job_description: str) -> str:
        """Create prompt for job match analysis"""
        profile_text = OpenAIService._profile_to_text(profile)

        prompt = (
            f"Analyze the job fit between this candidate and the job description below.\n\n"
            f"## Candidate Profile:\n{profile_text}\n\n"
            f"## Job Description:\n{job_description}\n\n"
            f"Please provide:\n"
            f"1. A numerical match score between 0 and 1\n"
            f"2. Detailed analysis of the match\n"
            f"3. List of matched skills\n"
            f"4. List of missing or underrepresented skills\n"
            f"5. Recommendations for the candidate\n\n"
            f"Please format your response in JSON with the following structure:\n"
            f"{{\n"
            f'  "score": 0.85,\n'
            f'  "analysis": "Detailed analysis of the match...",\n'
            f'  "matched_skills": ["Python", "FastAPI", "PostgreSQL"],\n'
            f'  "missing_skills": ["React", "Node.js"],\n'
            f'  "recommendations": ["Learn React basics", "Build a Node.js project"]\n'
            f"}}"
        )

        return prompt

    @staticmethod
    def _parse_match_analysis(analysis: str) -> Dict:
        """Parse the OpenAI response into structured data"""
        try:
            import json

            # Extract JSON from response
            json_start = analysis.find("{")
            json_end = analysis.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_str = analysis[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"Error parsing match analysis: {str(e)}")
            logger.debug(f"Raw analysis: {analysis}")

            return {
                "score": 0.5,
                "analysis": analysis,
                "missing_skills": [],
                "matched_skills": [],
                "recommendations": [],
            }

    @staticmethod
    async def extract_job_entities(job_description: str) -> Dict:
        """
        Extract structured entities from job description.

        Args:
            job_description: Job description text

        Returns:
            Dictionary with extracted entities
        """
        if not OpenAIService.is_available():
            return {
                "skills": [],
                "technologies": [],
                "responsibilities": [],
                "requirements": [],
            }

        try:
            prompt = (
                f"Extract structured information from this job description:\n\n"
                f"{job_description}\n\n"
                f"Please extract:\n"
                f"1. Required and preferred skills\n"
                f"2. Technologies and tools mentioned\n"
                f"3. Key responsibilities\n"
                f"4. Minimum requirements (education, experience)\n"
                f"\nFormat your response as JSON."
            )

            response = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that extracts structured information from job descriptions. "
                        "Be precise and only include information explicitly mentioned in the text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=OLLAMA_TEMPERATURE,
                max_tokens=OLLAMA_MAX_TOKENS,
            )

            import json

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error extracting job entities: {str(e)}")
            return {
                "skills": [],
                "technologies": [],
                "responsibilities": [],
                "requirements": [],
            }

    @staticmethod
    async def complete(
        prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        model: str = None,
    ) -> str:
        """
        Complete a text prompt using AI service.

        Args:
            prompt: Text prompt to complete
            temperature: Optional temperature setting (uses default if not provided)
            max_tokens: Optional max tokens setting (uses default if not provided)
            model: Optional model name (uses default Ollama model if not provided)

        Returns:
            Completed text response
        """
        if not OpenAIService.is_available():
            logger.warning("AI service not available, returning empty response")
            return ""

        try:
            client = get_client()
            # Use Ollama model for cost-free operation, with optional overrides
            effective_model = model if model else OLLAMA_MODEL
            effective_temp = (
                temperature if temperature is not None else OLLAMA_TEMPERATURE
            )
            effective_max_tokens = max_tokens if max_tokens else OLLAMA_MAX_TOKENS

            response = client.chat.completions.create(
                model=effective_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides clear, concise, and accurate responses.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=effective_temp,
                max_tokens=effective_max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error completing prompt: {str(e)}")
            return ""

    @staticmethod
    async def analyze_with_openai(prompt: str) -> str:
        """
        Analyze text using AI service (alias for complete method for backward compatibility).

        Args:
            prompt: Text prompt to analyze

        Returns:
            Analysis response
        """
        return await OpenAIService.complete(prompt)


# Singleton instance
openai_service = OpenAIService()
