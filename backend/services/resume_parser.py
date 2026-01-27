"""
Resume Parser Service

Handles resume parsing for PDF and DOCX files using text extraction and NLP.
Integrates with OpenAI for advanced semantic analysis.
"""

import io
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import docx  # python-docx for DOCX parsing
import fitz  # PyMuPDF for PDF parsing
import pytesseract
import spacy
from PIL import Image

from .openai_service import openai_service

logger = logging.getLogger(__name__)


# Load spaCy model for NLP
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning("Could not load spaCy model: %s", e)
    nlp = None


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file.

    Args:
        file_content: PDF file content as bytes

    Returns:
        Extracted text
    """
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = []

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text.append(page_text)

        return "\n".join(text)

    except Exception as e:
        logger.error("Error parsing PDF: %s", str(e))
        raise


def extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text from DOCX file.

    Args:
        file_content: DOCX file content as bytes

    Returns:
        Extracted text
    """
    try:
        import io

        doc = docx.Document(io.BytesIO(file_content))
        text = []

        for para in doc.paragraphs:
            if para.text.strip():
                text.append(para.text)

        return "\n".join(text)

    except Exception as e:
        logger.error("Error parsing DOCX: %s", str(e))
        raise


def extract_text_from_image(file_content: bytes) -> str:
    """
    Extract text from image file using Tesseract OCR.

    Args:
        file_content: Image file content as bytes

    Returns:
        Extracted text
    """
    try:
        image = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(image)
        return text

    except Exception as e:
        logger.error("Error parsing image with OCR: %s", str(e))
        raise


def parse_email(text: str) -> Optional[str]:
    """
    Extract email from text using regex.

    Args:
        text: Text to search

    Returns:
        Email address or None
    """
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(email_pattern, text)

    if matches:
        return matches[0]
    return None


def parse_phone(text: str) -> Optional[str]:
    """
    Extract phone number from text using regex.

    Args:
        text: Text to search

    Returns:
        Phone number or None
    """
    phone_pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    matches = re.findall(phone_pattern, text)

    if matches:
        return re.sub(r"[^\d+]", "", matches[0])
    return None


def extract_entities(text: str) -> dict:
    """
    Extract entities using spaCy.

    Args:
        text: Text to analyze

    Returns:
        Dictionary of extracted entities
    """
    if not nlp:
        return {}

    doc = nlp(text)

    entities = {"people": [], "organizations": [], "locations": []}

    for ent in doc.ents:
        if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
            entities["people"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["organizations"].append(ent.text)
        elif ent.label_ in {"GPE", "LOC"}:
            entities["locations"].append(ent.text)

    return entities


def parse_work_experience(text: str) -> list:
    """
    Parse work experience from resume text.

    Args:
        text: Resume text

    Returns:
        List of work experience entries
    """
    experience_keywords = [
        "experience",
        "employment",
        "work history",
        "professional experience",
    ]

    for keyword in experience_keywords:
        keyword_indices = []
        idx = -1

        while True:
            idx = text.lower().find(keyword, idx + 1)
            if idx == -1:
                break
            keyword_indices.append(idx)

        if keyword_indices:
            break

    if not keyword_indices:
        return []

    # Find next section to determine experience boundaries
    section_keywords = ["education", "skills", "certifications", "projects", "awards"]
    end_idx = len(text)

    for section_keyword in section_keywords:
        section_idx = text.lower().find(section_keyword, keyword_indices[0])
        if section_idx != -1 and section_idx < end_idx:
            end_idx = section_idx

    experience_text = text[keyword_indices[0] : end_idx]

    # Extract positions (simple keyword extraction for MVP)
    positions = []
    job_titles = [
        "software engineer",
        "developer",
        "engineer",
        "analyst",
        "manager",
        "director",
    ]

    for title in job_titles:
        for match in re.finditer(title, experience_text.lower()):
            start = match.start()
            # Find company name (simple approach)
            company_start = start + len(title) + 1
            company_end = experience_text.find("\n", company_start)

            if company_end != -1:
                company_text = experience_text[company_start:company_end].strip()

                if len(company_text) > 2 and len(company_text) < 50:
                    positions.append(
                        {
                            "position": title.title(),
                            "company": company_text,
                            "start_date": "2020",
                            "end_date": "2024",
                        }
                    )

    return positions


def parse_education(text: str) -> list:
    """
    Parse education information from resume text.

    Args:
        text: Resume text

    Returns:
        List of education entries
    """
    education_keywords = ["education", "degrees", "university", "college", "school"]

    for keyword in education_keywords:
        keyword_indices = []
        idx = -1

        while True:
            idx = text.lower().find(keyword, idx + 1)
            if idx == -1:
                break
            keyword_indices.append(idx)

        if keyword_indices:
            break

    if not keyword_indices:
        return []

    end_idx = len(text)
    next_section_keywords = ["experience", "skills", "certifications", "projects"]

    for section_keyword in next_section_keywords:
        section_idx = text.lower().find(section_keyword, keyword_indices[0])
        if section_idx != -1 and section_idx < end_idx:
            end_idx = section_idx

    education_text = text[keyword_indices[0] : end_idx]

    degrees = []
    degree_types = ["bachelor", "b.s.", "b.a.", "master", "m.s.", "ph.d.", "doctorate"]

    for degree in degree_types:
        for match in re.finditer(degree, education_text.lower()):
            degrees.append(
                {
                    "degree": degree.title(),
                    "school": "University",  # Simple default
                    "graduation_year": "2020",
                }
            )

    return degrees


def parse_skills(text: str) -> list:
    """
    Parse skills from resume text.

    Args:
        text: Resume text

    Returns:
        List of skills
    """
    skills_keywords = [
        "skills",
        "technical skills",
        "programming languages",
        "technologies",
    ]

    for keyword in skills_keywords:
        keyword_indices = []
        idx = -1

        while True:
            idx = text.lower().find(keyword, idx + 1)
            if idx == -1:
                break
            keyword_indices.append(idx)

        if keyword_indices:
            break

    if not keyword_indices:
        return []

    end_idx = len(text)
    next_section_keywords = ["experience", "education", "certifications", "projects"]

    for section_keyword in next_section_keywords:
        section_idx = text.lower().find(section_keyword, keyword_indices[0])
        if section_idx != -1 and section_idx < end_idx:
            end_idx = section_idx

    skills_text = text[keyword_indices[0] : end_idx]

    # Common programming languages and technologies for extraction
    common_skills = [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "go",
        "rust",
        "react",
        "angular",
        "vue",
        "node.js",
        "express",
        "django",
        "flask",
        "sql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "aws",
        "azure",
        "gcp",
    ]

    extracted_skills = []
    for skill in common_skills:
        if skill.lower() in skills_text.lower():
            extracted_skills.append(skill)

    return list(set(extracted_skills))


def parse_resume_with_openai(text: str) -> dict:
    """
    Parse resume using OpenAI's advanced semantic analysis.

    Args:
        text: Extracted resume text

    Returns:
        Dictionary of parsed resume data with AI enhancement
    """
    try:
        prompt = f"""Please analyze the following resume text and extract the following information in JSON format:
        
        1. full_name: The candidate's full name
        2. email: Email address
        3. phone: Phone number
        4. work_experience: List of work experience entries with:
           - position: Job title
           - company: Company name
           - start_date: Start date
           - end_date: End date (or "Present" if current)
           - description: Job responsibilities and achievements
        5. education: List of education entries with:
           - degree: Degree type (e.g., B.S., Master's, PhD)
           - major: Field of study
           - school: School/university name
           - graduation_year: Year of graduation
        6. skills: List of technical skills, programming languages, and technologies
        7. certifications: List of certifications
        8. projects: List of notable projects with descriptions
        9. summary: A brief professional summary
        
        Resume text:
        {text}
        
        Please return only valid JSON. Do not include any other text.
        """

        response = openai_service.analyze_with_openai(prompt)

        if response and "analysis" in response:
            try:
                parsed_data = json.loads(response["analysis"])
                return parsed_data
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse OpenAI JSON response: %s", e)
                return {}

        return {}

    except Exception as e:
        logger.warning("OpenAI resume parsing failed: %s", e)
        return {}


def parse_resume(file_content: bytes, filename: str) -> dict:
    """
    Parse resume from file content.

    Args:
        file_content: File content as bytes
        filename: Original filename

    Returns:
        Dictionary of parsed resume data
    """
    try:
        if filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_content)
        elif filename.lower().endswith(".docx"):
            text = extract_text_from_docx(file_content)
        elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            text = extract_text_from_image(file_content)
        

        raise ValueError("Unsupported file type")

        # First, try AI-powered parsing with OpenAI
        ai_parsed_data = parse_resume_with_openai(text)

        # Fallback to traditional parsing if AI fails
        if not ai_parsed_data:
            logger.warning("AI parsing failed, falling back to traditional methods")

            # Parse contact information
            email = parse_email(text)
            phone = parse_phone(text)

            # Extract entities
            entities = extract_entities(text)

            # Parse sections
            work_experience = parse_work_experience(text)
            education = parse_education(text)
            skills = parse_skills(text)

            # Determine name from entities or filename
            name = None
            if entities.get("people"):
                name = entities["people"][0]
            else:
                # Try to extract name from filename
                filename_clean = re.sub(r"[^\w\s]", "", filename.split(".")[0])
                if len(filename_clean.split()) >= 2:
                    name = filename_clean

            ai_parsed_data = {
                "full_name": name,
                "email": email,
                "phone": phone,
                "work_experience": work_experience,
                "education": education,
                "skills": skills,
                "certifications": [],
                "projects": [],
                "summary": "",
            }

        # Add additional fields
        ai_parsed_data["parsed_at"] = datetime.now(timezone.utc).isoformat()
        ai_parsed_data["raw_text"] = text[:1000]  # Truncate for storage
        ai_parsed_data["ai_enhanced"] = True

        logger.info("Successfully parsed resume: %s", ai_parsed_data.get("full_name", "Unknown"))
        )

        return ai_parsed_data

    except Exception as e:
        logger.error("Error parsing resume: %s", str(e))
        raise
