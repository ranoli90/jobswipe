"""
Cover Letter Generation Service
Handles LLM-based cover letter generation with strict constraints and validation.
"""

from typing import Optional

from backend.services.openai_service import OLLAMA_MODEL, OpenAIService

# Constants for cover letter generation
MAX_SKILLS_TO_INCLUDE = 8
MAX_EXPERIENCE_ENTRIES = 3
MAX_WORDS = 180
MAX_CHARACTERS = 1500
TRUNCATION_SUFFIX = "..."
TRUNCATED_CHARACTER_LIMIT = MAX_CHARACTERS - len(TRUNCATION_SUFFIX)
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 300

# Initialize OpenAI service (now using Ollama for cost-free operation)
openai_service = OpenAIService()


def create_cover_letter_prompt(job_desc: str, profile: dict) -> str:
    """
    Create a strict, constrained prompt for cover letter generation.

    Args:
        job_desc: Job description text
        profile: Candidate profile data

    Returns:
        Structured prompt for LLM
    """
    skills_text = ", ".join(profile.get("skills", [])[:MAX_SKILLS_TO_INCLUDE])
    experience_text = []
    for exp in profile.get("work_experience", [])[:MAX_EXPERIENCE_ENTRIES]:
        if exp.get("position") and exp.get("company"):
            experience_text.append(f"{exp['position']} at {exp['company']}")

    return (
        f"Write a concise cover letter (<= {MAX_WORDS} words). "
        "Use the candidate's experience and top skills; avoid extra PII. "
        "Focus on relevant qualifications for the specific job. "
        "Keep it professional and tailored to the position. "
        "\n\n"
        f"Candidate Headline: {profile.get('headline', '')}\n"
        f"Candidate Skills: {skills_text}\n"
        f"Candidate Experience: {', '.join(experience_text)}\n"
        "\n"
        f"Job Description:\n{job_desc}\n"
        "\n"
        "Requirements:\n"
        f"- Max {MAX_WORDS} words\n"
        "- No personal identifiable information beyond what's provided\n"
        "- Professional tone\n"
        "- Tailored to the specific job\n"
        "- Highlight relevant skills and experience\n"
    )


def validate_cover_letter(text: str) -> str:
    """
    Validate and clean generated cover letter.

    Args:
        text: Raw LLM output

    Returns:
        Validated and cleaned cover letter
    """
    # Strip whitespace
    text = text.strip()

    # Hard cap at maximum characters
    if len(text) > MAX_CHARACTERS:
        text = text[:TRUNCATED_CHARACTER_LIMIT] + TRUNCATION_SUFFIX

    # Remove any potential PII patterns (email, phone, address)
    import re

    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[email]", text
    )
    text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[phone]", text)
    text = re.sub(r"\b\d{1,5}\s+\w+\s+\w+", "[address]", text)

    return text


def generate_cover_letter(job_desc: str, profile: dict) -> Optional[str]:
    """
    Generate a validated cover letter using LLM with strict constraints.

    Args:
        job_desc: Job description text
        profile: Candidate profile data

    Returns:
        Validated cover letter or None if generation fails
    """
    try:
        if not openai_service.is_available():
            return None

        prompt = create_cover_letter_prompt(job_desc, profile)
        raw_response = openai_service.complete(
            prompt,
            temperature=LLM_TEMPERATURE,  # Low temperature for deterministic output
            max_tokens=LLM_MAX_TOKENS,  # Strict token limit
            model=OLLAMA_MODEL,  # Using free Ollama model instead of paid gpt-3.5-turbo
        )

        return validate_cover_letter(raw_response)

    except Exception as e:
        import logging

        logging.error(f"Error generating cover letter: {str(e)}")
        return None


class CoverLetterService:
    """Service for generating cover letters"""

    def create_cover_letter_prompt(self, job_desc: str, profile: dict) -> str:
        return create_cover_letter_prompt(job_desc, profile)

    def validate_cover_letter(self, text: str) -> str:
        return validate_cover_letter(text)

    def generate_cover_letter(self, job_desc: str, profile: dict) -> Optional[str]:
        return generate_cover_letter(job_desc, profile)

    def generate_cover_letter_from_template(
        self, template: str, job_desc: str, profile: dict
    ) -> Optional[str]:
        return generate_cover_letter_from_template(template, job_desc, profile)


# Create singleton instance
cover_letter_service = CoverLetterService()


def generate_cover_letter_from_template(
    template: str, job_desc: str, profile: dict
) -> Optional[str]:
    """
    Generate a cover letter from user-defined template.

    Args:
        template: User's cover letter template
        job_desc: Job description text
        profile: Candidate profile data

    Returns:
        Generated cover letter or None if generation fails
    """
    try:
        # Replace placeholders in template
        result = template.replace("{name}", profile.get("full_name", ""))
        result = result.replace(
            "{job_title}", job_desc.split("\n")[0] if job_desc else ""
        )
        result = result.replace("{company}", profile.get("company", ""))

        return validate_cover_letter(result)

    except Exception as e:
        import logging

        logging.error(f"Error generating cover letter from template: {str(e)}")
        return None
