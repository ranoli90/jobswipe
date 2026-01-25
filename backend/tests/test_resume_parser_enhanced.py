"""
Tests for the enhanced resume parser service.
"""

import pytest
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
from backend.services.resume_parser_enhanced import EnhancedResumeParser, parse_resume_enhanced


class TestEnhancedResumeParser:
    """Tests for the enhanced resume parser"""
    
    @pytest.mark.asyncio
    @patch('backend.services.resume_parser_enhanced.EnhancedResumeParser.parse_resume')
    async def test_parse_resume_pdf(self, mock_parse_resume):
        """Test parsing a PDF resume with all mocks"""
        mock_parse_resume.return_value = {
            "full_name": "John Doe",
            "email": "test@example.com",
            "phone": "1234567890",
            "summary": "Software Engineer with 5 years experience",
            "work_experience": [{"company": "Tech Corp", "position": "Developer"}],
            "education": [{"degree": "Bachelor", "school": "University"}],
            "skills": ["Python", "JavaScript"],
            "projects": [],
            "certifications": []
        }
        
        data = await parse_resume_enhanced(b"test content", "resume.pdf")
        
        assert data["full_name"] == "John Doe"
        assert data["email"] == "test@example.com"
        assert data["phone"] == "1234567890"
        assert data["summary"] == "Software Engineer with 5 years experience"
        assert "Python" in data["skills"]
        assert "JavaScript" in data["skills"]
        assert len(data["work_experience"]) == 1
        
    @pytest.mark.asyncio
    @patch('backend.services.resume_parser_enhanced.EnhancedResumeParser.parse_resume')
    async def test_parse_resume_docx(self, mock_parse_resume):
        """Test parsing a DOCX resume with all mocks"""
        mock_parse_resume.return_value = {
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "0987654321",
            "summary": "Data Scientist specializing in ML",
            "work_experience": [{"company": "Data Inc", "position": "Data Scientist"}],
            "education": [{"degree": "Master", "school": "Tech University"}],
            "skills": ["Python", "TensorFlow"],
            "projects": [],
            "certifications": []
        }
        
        data = await parse_resume_enhanced(b"test content", "resume.docx")
        
        assert data["full_name"] == "Jane Smith"
        assert data["email"] == "jane@example.com"
        assert data["phone"] == "0987654321"
        assert data["summary"] == "Data Scientist specializing in ML"
        assert "Python" in data["skills"]
        assert "TensorFlow" in data["skills"]
        assert len(data["work_experience"]) == 1
        
    def test_parse_basic_info(self):
        """Test basic info parsing"""
        text = """
        John Doe
        john.doe@example.com
        123-456-7890
        """
        
        info = EnhancedResumeParser.parse_basic_info(text)
        
        assert info["email"] == "john.doe@example.com"
        assert info["phone"] == "1234567890"
        
    def test_extract_skills(self):
        """Test skill extraction"""
        text = """
        Skills: Python, Java, JavaScript, React
        Technical Skills: Python, Docker, Kubernetes
        """
        
        skills = EnhancedResumeParser.extract_skills(text)
        
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "React" in skills
        assert "Docker" in skills
        assert "Kubernetes" in skills
        
    @pytest.mark.asyncio
    @patch('backend.services.resume_parser_enhanced.get_spacy_model')
    async def test_ai_entity_extraction(self, mock_get_spacy_model):
        """Test AI entity extraction"""
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        
        # Mock spaCy entity extraction
        mock_ent1 = MagicMock()
        mock_ent1.label_ = "PERSON"
        mock_ent1.text = "Test User"
        
        mock_ent2 = MagicMock()
        mock_ent2.label_ = "ORG"
        mock_ent2.text = "Tech Company"
        
        mock_doc.ents = [mock_ent1, mock_ent2]
        mock_nlp.return_value = mock_doc
        
        mock_get_spacy_model.return_value = mock_nlp
        
        text = """
        Test User
        test@example.com
        123-456-7890
        Tech Company
        """
        entities = await EnhancedResumeParser.extract_entities_ai(text)
        
        assert entities["full_name"] == "Test User"
        assert entities["contact"]["email"] == "test@example.com"
        assert entities["contact"]["phone"] == "123-456-7890"
            
    @pytest.mark.asyncio
    @patch('backend.services.resume_parser_enhanced.get_spacy_model')
    async def test_ai_fallback(self, mock_get_spacy_model):
        """Test fallback when spaCy model is unavailable"""
        mock_get_spacy_model.return_value = None
        
        text = "Test resume content"
        entities = await EnhancedResumeParser.extract_entities_ai(text)
        
        assert entities == {}