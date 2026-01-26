"""
OpenAI Integration Service
Provides access to OpenAI API for job matching and semantic analysis.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

# Initialize OpenAI client (dynamically)
client = None
def get_client():
    """Get or create OpenAI client instance"""
    global client
    api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
    if api_key and not client:
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI service initialized")
    elif not api_key:
        logger.warning("OpenAI API key not configured. Falling back to rule-based matching.")
    return client

# Initialize client on module load if API key is available
client = get_client()


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if OpenAI integration is available"""
        return bool(OPENAI_API_KEY)
    
    @staticmethod
    async def generate_job_embedding(job_description: str) -> List[float]:
        """
        Generate embedding for a job description using OpenAI API.
        
        Args:
            job_description: Job description text
            
        Returns:
            List of floating point numbers representing the embedding
        """
        if not OpenAIService.is_available():
            logger.warning("OpenAI service not available, returning empty embedding")
            return []
            
        try:
            client = get_client()
            response = client.embeddings.create(
                input=job_description,
                model="text-embedding-ada-002"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating job embedding: {str(e)}")
            return []
    
    @staticmethod
    async def generate_profile_embedding(profile: Dict) -> List[float]:
        """
        Generate embedding for a candidate profile using OpenAI API.
        
        Args:
            profile: Candidate profile dictionary with skills, experience, etc.
            
        Returns:
            List of floating point numbers representing the embedding
        """
        if not OpenAIService.is_available():
            logger.warning("OpenAI service not available, returning empty embedding")
            return []
            
        try:
            # Convert profile to text for embedding
            profile_text = OpenAIService._profile_to_text(profile)
            
            client = get_client()
            response = client.embeddings.create(
                input=profile_text,
                model="text-embedding-ada-002"
            )
            
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
            
        # Calculate cosine similarity
        try:
            import numpy as np
            from numpy.linalg import norm
            
            profile_vec = np.array(profile_embedding)
            job_vec = np.array(job_embedding)
            
            cosine_similarity = np.dot(profile_vec, job_vec) / (norm(profile_vec) * norm(job_vec))
            
            # Normalize to 0-1 range
            normalized_score = (cosine_similarity + 1) / 2
            
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
                "recommendations": []
            }
            
        try:
            prompt = OpenAIService._create_match_analysis_prompt(profile, job_description)
            
            client = get_client()
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical recruiter analyzing job fit between a candidate and a job description. "
                                  "Provide detailed analysis including: match score (0-1), matched skills, missing skills, "
                                  "and recommendations for the candidate. Be honest and realistic."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS
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
                "recommendations": []
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
            f"  \"score\": 0.85,\n"
            f"  \"analysis\": \"Detailed analysis of the match...\",\n"
            f"  \"matched_skills\": [\"Python\", \"FastAPI\", \"PostgreSQL\"],\n"
            f"  \"missing_skills\": [\"React\", \"Node.js\"],\n"
            f"  \"recommendations\": [\"Learn React basics\", \"Build a Node.js project\"]\n"
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
                "recommendations": []
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
                "requirements": []
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
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that extracts structured information from job descriptions. "
                                  "Be precise and only include information explicitly mentioned in the text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error extracting job entities: {str(e)}")
            return {
                "skills": [],
                "technologies": [],
                "responsibilities": [],
                "requirements": []
            }


# Singleton instance
openai_service = OpenAIService()
