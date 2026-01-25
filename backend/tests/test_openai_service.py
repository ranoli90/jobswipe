"""
Tests for OpenAI service integration.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.services.openai_service import OpenAIService


class TestOpenAIService:
    """Tests for OpenAI integration service"""
    
    def test_is_available_with_api_key(self):
        """Test that service availability is correctly determined"""
        # Test with API key available
        with patch('backend.services.openai_service.OPENAI_API_KEY', 'test-key'):
            assert OpenAIService.is_available() == True
            
        # Test without API key
        with patch('backend.services.openai_service.OPENAI_API_KEY', None):
            assert OpenAIService.is_available() == False
            
    def test_profile_to_text_conversion(self):
        """Test profile dictionary to text conversion"""
        profile = {
            "full_name": "John Doe",
            "headline": "Senior Software Engineer",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "work_experience": [
                {"position": "Software Engineer", "company": "Tech Corp"},
                {"position": "Junior Developer", "company": "StartUp Inc"}
            ],
            "education": [
                {"degree": "B.S. Computer Science", "school": "University of Example"}
            ]
        }
        
        text = OpenAIService._profile_to_text(profile)
        
        assert "John Doe" in text
        assert "Senior Software Engineer" in text
        assert "Python" in text
        assert "Software Engineer" in text
        assert "University of Example" in text
        
    @pytest.mark.asyncio
    @patch('backend.services.openai_service.client')
    async def test_generate_job_embedding(self, mock_client):
        """Test job embedding generation"""
        # Mock OpenAI API response
        mock_embedding = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_client.embeddings.create.return_value = mock_response
        
        with patch('backend.services.openai_service.OPENAI_API_KEY', 'test-key'):
            embedding = await OpenAIService.generate_job_embedding("Test job description")
            
            assert len(embedding) == 3
            assert embedding == mock_embedding
            mock_client.embeddings.create.assert_called_once()
            
    @pytest.mark.asyncio
    @patch('backend.services.openai_service.client')
    async def test_generate_profile_embedding(self, mock_client):
        """Test profile embedding generation"""
        # Mock OpenAI API response
        mock_embedding = [0.4, 0.5, 0.6]
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]
        mock_client.embeddings.create.return_value = mock_response
        
        profile = {
            "full_name": "John Doe",
            "skills": ["Python", "FastAPI"]
        }
        
        with patch('backend.services.openai_service.OPENAI_API_KEY', 'test-key'):
            embedding = await OpenAIService.generate_profile_embedding(profile)
            
            assert len(embedding) == 3
            assert embedding == mock_embedding
            mock_client.embeddings.create.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity(self):
        """Test semantic similarity calculation"""
        profile_embedding = [1, 0, 0]
        job_embedding = [1, 0, 0]
        
        similarity = await OpenAIService.calculate_semantic_similarity(
            profile_embedding, job_embedding
        )
        
        assert similarity == 1.0
        
        # Test opposite vectors
        job_embedding = [-1, 0, 0]
        similarity = await OpenAIService.calculate_semantic_similarity(
            profile_embedding, job_embedding
        )
        
        assert similarity == 0.0
        
    @pytest.mark.asyncio
    @patch('backend.services.openai_service.client')
    async def test_analyze_job_match(self, mock_client):
        """Test job match analysis"""
        # Mock OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"score": 0.85, "analysis": "Great match", "matched_skills": ["Python"], "missing_skills": ["React"], "recommendations": ["Learn React"]}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        profile = {
            "full_name": "John Doe",
            "skills": ["Python", "FastAPI"]
        }
        
        with patch('backend.services.openai_service.OPENAI_API_KEY', 'test-key'):
            result = await OpenAIService.analyze_job_match(
                profile,
                "We need Python developers with React experience"
            )
            
            assert "score" in result
            assert result["score"] == 0.85
            assert "analysis" in result
            assert "Python" in result["matched_skills"]
            assert "React" in result["missing_skills"]
            assert "Learn React" in result["recommendations"]
            mock_client.chat.completions.create.assert_called_once()
            
    def test_parse_match_analysis(self):
        """Test match analysis parsing"""
        raw_response = """Here's your JSON:
        {
            "score": 0.85,
            "analysis": "Great match between candidate and job",
            "matched_skills": ["Python", "FastAPI"],
            "missing_skills": ["React"],
            "recommendations": ["Learn React basics"]
        }
        """
        
        parsed = OpenAIService._parse_match_analysis(raw_response)
        
        assert parsed["score"] == 0.85
        assert "Python" in parsed["matched_skills"]
        assert "React" in parsed["missing_skills"]
        
    @pytest.mark.asyncio
    async def test_openai_unavailable_fallback(self):
        """Test that service falls back gracefully when OpenAI is unavailable"""
        with patch('backend.services.openai_service.OPENAI_API_KEY', None):
            # Should return fallback values
            embedding = await OpenAIService.generate_job_embedding("Test")
            assert embedding == []
            
            match_result = await OpenAIService.analyze_job_match({}, "Test")
            assert match_result["score"] == 0.5