"""
Enhanced Resume Parser Service with AI Integration

Provides advanced resume parsing capabilities using OpenAI and spaCy.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import docx  # python-docx for DOCX parsing
import fitz  # PyMuPDF for PDF parsing
import spacy

# Removed OpenAI import for free alternative

logger = logging.getLogger(__name__)

# Lazy loaded spaCy model
_nlp = None


def get_spacy_model():
    """Lazy load spaCy model when first needed"""
    global _nlp
    if _nlp is not None:
        return _nlp

    # Check if we're in a test environment to skip loading
    if (
        os.getenv("TEST_ENV")
        or "pytest" in os.path.basename(os.environ.get("PYTHONPATH", ""))
        or "pytest" in os.environ.get("PYTEST_CURRENT_TEST", "")
    ):
        logger.info("Skipping spaCy model load in test environment")
        _nlp = None
        return None

    try:
        _nlp = spacy.load(
            "en_core_web_sm"
        )  # Use small model instead of large transformer
        logger.info("Loaded spaCy small model")
    except Exception as e:
        logger.error("Could not load spaCy model: %s", e)
        _nlp = None
    return _nlp


# Using spaCy for free NLP processing


class EnhancedResumeParser:
    """Enhanced resume parser with AI capabilities"""

    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file using PyMuPDF"""
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

    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file using python-docx"""
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

    @staticmethod
    def parse_basic_info(text: str) -> Dict:
        """Parse basic contact information using regex"""
        # Email
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        emails = re.findall(email_pattern, text)

        # Phone number
        phone_pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        phones = re.findall(phone_pattern, text)
        phones = [re.sub(r"[^\d+]", "", phone) for phone in phones]

        return {
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
        }

    @staticmethod
    def extract_entities_spacy(text: str) -> Dict:
        """Extract entities using spaCy"""
        nlp = get_spacy_model()
        if not nlp:
            logger.warning("spaCy not available, skipping entity extraction")
            return {"names": [], "organizations": [], "locations": [], "dates": []}

        doc = nlp(text)

        entities = {"names": [], "organizations": [], "locations": [], "dates": []}

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["names"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_ == "GPE" or ent.label_ == "LOC":
                entities["locations"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)

        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    @staticmethod
    async def extract_entities_ai(text: str) -> Dict:
        """Extract structured information using spaCy NLP"""
        nlp = get_spacy_model()
        if not nlp:
            logger.warning("spaCy model not available, skipping AI extraction")
            return {}

        try:
            doc = nlp(text)

            # Extract entities
            entities = {
                "full_name": "",
                "contact": {},
                "summary": "",
                "work_experience": [],
                "education": [],
                "skills": [],
                "projects": [],
            }

            # Extract name (PERSON entities)
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                entities["full_name"] = persons[0]

            # Extract organizations (ORG entities) for companies
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

            # Extract email and phone using regex
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"

            emails = re.findall(email_pattern, text)
            phones = re.findall(phone_pattern, text)

            entities["contact"] = {
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else "",
            }

            # Extract skills using keyword matching
            entities["skills"] = EnhancedResumeParser.extract_skills(text)

            # Simple extraction for work experience and education using patterns
            # This is a basic implementation; can be enhanced with more rules
            lines = text.split("\n")
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if "experience" in line.lower() or "work" in line.lower():
                    current_section = "experience"
                elif "education" in line.lower():
                    current_section = "education"
                elif current_section == "experience" and orgs:
                    # Simple: assume lines with orgs are experience
                    entities["work_experience"].append(
                        {"company": orgs[0], "position": line}
                    )
                elif current_section == "education":
                    entities["education"].append({"school": line})

            return entities

        except Exception as e:
            logger.error("Error extracting entities with spaCy: %s", str(e))
            return {}

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common technical skills for filtering
        technical_skills = [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C++",
            "C#",
            "Go",
            "Rust",
            "React",
            "Angular",
            "Vue",
            "Node.js",
            "Express",
            "Django",
            "Flask",
            "SQL",
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Redis",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "Kubernetes",
            "Git",
            "HTML",
            "CSS",
            "REST",
            "GraphQL",
            "API",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Computer Vision",
            "Data Science",
            "TensorFlow",
            "PyTorch",
            "Scikit-learn",
            "Pandas",
            "NumPy",
            "Spark",
            "DevOps",
            "CI/CD",
            "Jenkins",
            "GitLab",
            "AWS Lambda",
            "Serverless",
        ]

        extracted_skills = []

        for skill in technical_skills:
            # Case-insensitive match
            if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
                extracted_skills.append(skill)

        return list(set(extracted_skills))

    @staticmethod
    def extract_experience(text: str) -> List[Dict]:
        """Extract work experience using keyword matching"""
        experience_keywords = ["experience", "employment", "work history"]
        section_start = -1

        for keyword in experience_keywords:
            idx = text.lower().find(keyword.lower())
            if idx != -1:
                section_start = idx
                break

        if section_start == -1:
            return []

        # Find section end
        section_end = len(text)
        end_keywords = ["education", "skills", "certifications", "projects"]

        for keyword in end_keywords:
            idx = text.lower().find(keyword.lower(), section_start)
            if idx != -1 and idx < section_end:
                section_end = idx

        experience_text = text[section_start:section_end]

        # Extract company/position blocks
        experiences = []
        lines = experience_text.split("\n")

        current_exp = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristic for detecting experience blocks
            if any(word in line.lower() for word in ["inc", "llc", "corp", "company"]):
                if current_exp:
                    experiences.append(current_exp)
                    current_exp = {}
                current_exp["company"] = line
            elif re.search(r"\b(?:20|19)\d{2}", line):
                current_exp["dates"] = line
            else:
                if "position" not in current_exp:
                    current_exp["position"] = line
                else:
                    if "responsibilities" not in current_exp:
                        current_exp["responsibilities"] = []
                    current_exp["responsibilities"].append(line)

        if current_exp:
            experiences.append(current_exp)

        return experiences

    @staticmethod
    def extract_education(text: str) -> List[Dict]:
        """Extract education information using keyword matching"""
        education_keywords = ["education", "degrees", "university", "college"]
        section_start = -1

        for keyword in education_keywords:
            idx = text.lower().find(keyword.lower())
            if idx != -1:
                section_start = idx
                break

        if section_start == -1:
            return []

        section_end = len(text)
        end_keywords = ["experience", "skills", "certifications", "projects"]

        for keyword in end_keywords:
            idx = text.lower().find(keyword.lower(), section_start)
            if idx != -1 and idx < section_end:
                section_end = idx

        education_text = text[section_start:section_end]

        educations = []
        lines = education_text.split("\n")

        current_edu = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(
                word in line.lower() for word in ["bachelor", "master", "phd", "degree"]
            ):
                current_edu["degree"] = line
            elif any(
                word in line.lower() for word in ["university", "college", "school"]
            ):
                current_edu["school"] = line
            elif re.search(r"\b(?:20|19)\d{2}", line):
                current_edu["graduation_year"] = line

            if len(current_edu) >= 2:
                educations.append(current_edu)
                current_edu = {}

        if current_edu:
            educations.append(current_edu)

        return educations

    @staticmethod
    async def parse_resume(file_content: bytes, filename: str) -> Dict:
        """
        Parse resume from file content with enhanced AI capabilities.

        Args:
            file_content: File content as bytes
            filename: Original filename

        Returns:
            Dictionary with parsed resume data
        """
        try:
            # Extract text based on file type
            if filename.lower().endswith(".pdf"):
                text = EnhancedResumeParser.extract_text_from_pdf(file_content)
            elif filename.lower().endswith(".docx"):
                text = EnhancedResumeParser.extract_text_from_docx(file_content)
            else:
                raise ValueError(f"Unsupported file type: {filename}")

            logger.info("Extracted %s characters from resume", len(text))

            # Parse basic information
            basic_info = EnhancedResumeParser.parse_basic_info(text)

            # Extract entities with spaCy
            entities = EnhancedResumeParser.extract_entities_spacy(text)

            # Extract skills and sections
            skills = EnhancedResumeParser.extract_skills(text)
            experience = EnhancedResumeParser.extract_experience(text)
            education = EnhancedResumeParser.extract_education(text)

            # AI extraction
            ai_data = await EnhancedResumeParser.extract_entities_ai(text)

            # Combine results with AI taking priority
            parsed_data = {
                "full_name": ai_data.get("full_name")
                or (entities["names"][0] if entities["names"] else None),
                "email": ai_data.get("email") or basic_info.get("email"),
                "phone": ai_data.get("phone") or basic_info.get("phone"),
                "summary": ai_data.get("summary") or ai_data.get("objective"),
                "work_experience": ai_data.get("work_experience") or experience,
                "education": ai_data.get("education") or education,
                "skills": ai_data.get("skills") or skills,
                "projects": ai_data.get("projects", []),
                "certifications": ai_data.get("certifications", []),
                "entities": entities,
                "raw_text": text[:2000],  # Truncate for storage
                "parsed_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info("Successfully parsed resume: %s", parsed_data['full_name'])

            return parsed_data

        except Exception as e:
            logger.error("Error parsing resume: %s", str(e))
            raise


# Singleton instance
enhanced_resume_parser = EnhancedResumeParser()


# Helper function for convenience
async def parse_resume_enhanced(file_content: bytes, filename: str) -> Dict:
    """Convenience function to use the enhanced resume parser"""
    return await EnhancedResumeParser.parse_resume(file_content, filename)
