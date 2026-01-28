"""
Unit tests for EmbeddingService
"""

import asyncio
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for EmbeddingService"""

    @pytest.fixture(autouse=True)
    def reset_model(self):
        """Reset the model before each test"""
        EmbeddingService._model = None

    @patch("backend.services.embedding_service.redis")
    def test_is_available_no_model(self, mock_redis):
        """Test is_available when model is not loaded"""
        assert EmbeddingService.is_available() is False

    @patch("backend.services.embedding_service.redis")
    @patch("backend.services.embedding_service.SentenceTransformer")
    def test_is_available_with_model(self, mock_sentence_transformer, mock_redis):
        """Test is_available when model is loaded"""
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        EmbeddingService._model = mock_model

        assert EmbeddingService.is_available() is True

    @patch("backend.services.embedding_service.redis")
    @patch("backend.services.embedding_service.SentenceTransformer")
    def test_get_model_success(self, mock_sentence_transformer, mock_redis):
        """Test get_model successful loading"""
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model

        model = EmbeddingService.get_model()

        assert model == mock_model
        mock_sentence_transformer.assert_called_once_with(
            "all-MiniLM-L6-v2", cache_folder="./models"
        )

    @patch("backend.services.embedding_service.redis")
    @patch("backend.services.embedding_service.SentenceTransformer")
    def test_get_model_import_error(self, mock_sentence_transformer, mock_redis):
        """Test get_model when SentenceTransformer import fails"""
        mock_sentence_transformer.side_effect = ImportError("No module")

        model = EmbeddingService.get_model()

        assert model is None

    @patch("backend.services.embedding_service.redis")
    @patch("backend.services.embedding_service.SentenceTransformer")
    def test_get_model_exception(self, mock_sentence_transformer, mock_redis):
        """Test get_model when loading fails"""
        mock_sentence_transformer.side_effect = Exception("Load failed")

        model = EmbeddingService.get_model()

        assert model is None

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.redis_client")
    @patch("backend.services.embedding_service.EmbeddingService.get_model")
    async def test_generate_job_embedding_success(
        self, mock_get_model, mock_redis_client
    ):
        """Test generate_job_embedding successful case"""
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model

        # Mock encoding
        mock_embedding = np.array([[0.1, 0.2, 0.3]])
        mock_model.encode = MagicMock(return_value=mock_embedding)

        # Mock redis not having cache
        mock_redis_client.get.return_value = None
        mock_redis_client.setex = MagicMock()

        result = await EmbeddingService.generate_job_embedding("test job description")

        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with("test job description")
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.redis_client")
    @patch("backend.services.embedding_service.EmbeddingService.get_model")
    async def test_generate_job_embedding_cached(
        self, mock_get_model, mock_redis_client
    ):
        """Test generate_job_embedding with cache hit"""
        mock_get_model.return_value = MagicMock()

        cached_embedding = [0.4, 0.5, 0.6]
        mock_redis_client.get.return_value = json.dumps(cached_embedding)

        result = await EmbeddingService.generate_job_embedding("test job")

        assert result == cached_embedding
        # Should not call model.encode since cache hit
        mock_get_model.return_value.encode.assert_not_called()

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.redis_client")
    @patch("backend.services.embedding_service.EmbeddingService.get_model")
    async def test_generate_job_embedding_service_unavailable(
        self, mock_get_model, mock_redis_client
    ):
        """Test generate_job_embedding when service unavailable"""
        mock_get_model.return_value = None

        result = await EmbeddingService.generate_job_embedding("test job")

        assert result == []

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.redis_client")
    @patch("backend.services.embedding_service.EmbeddingService.get_model")
    async def test_generate_job_embedding_exception(
        self, mock_get_model, mock_redis_client
    ):
        """Test generate_job_embedding with encoding exception"""
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        mock_redis_client.get.return_value = None

        mock_model.encode.side_effect = Exception("Encoding failed")

        result = await EmbeddingService.generate_job_embedding("test job")

        assert result == []

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.redis_client")
    @patch("backend.services.embedding_service.EmbeddingService.get_model")
    async def test_generate_profile_embedding_success(
        self, mock_get_model, mock_redis_client
    ):
        """Test generate_profile_embedding successful case"""
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model

        mock_embedding = np.array([[0.1, 0.2, 0.3]])
        mock_model.encode = MagicMock(return_value=mock_embedding)

        mock_redis_client.get.return_value = None
        mock_redis_client.setex = MagicMock()

        profile = {
            "full_name": "John Doe",
            "headline": "Software Engineer",
            "skills": ["Python", "JavaScript"],
            "work_experience": [{"position": "Developer", "company": "Tech Corp"}],
            "education": [{"degree": "BS CS", "school": "University"}],
        }

        result = await EmbeddingService.generate_profile_embedding(profile)

        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once()
        mock_redis_client.setex.assert_called_once()

    def test_profile_to_text_complete(self):
        """Test _profile_to_text with complete profile"""
        profile = {
            "full_name": "John Doe",
            "headline": "Software Engineer",
            "skills": ["Python", "JavaScript"],
            "work_experience": [
                {"position": "Senior Developer", "company": "Tech Corp"},
                {"position": "Junior Developer", "company": "Startup Inc"},
            ],
            "education": [
                {"degree": "Bachelor of Science", "school": "State University"},
                {"degree": "Master of Science", "school": "Tech University"},
            ],
        }

        text = EmbeddingService._profile_to_text(profile)

        assert "Name: John Doe" in text
        assert "Headline: Software Engineer" in text
        assert "Skills: Python, JavaScript" in text
        assert (
            "Experience: Senior Developer at Tech Corp, Junior Developer at Startup Inc"
            in text
        )
        assert (
            "Education: Bachelor of Science from State University, Master of Science from Tech University"
            in text
        )

    def test_profile_to_text_minimal(self):
        """Test _profile_to_text with minimal profile"""
        profile = {}

        text = EmbeddingService._profile_to_text(profile)

        assert text == ""

    def test_profile_to_text_partial(self):
        """Test _profile_to_text with partial profile"""
        profile = {
            "skills": ["Python"],
            "work_experience": [{"position": "Developer"}],
            "education": [{"degree": "BS"}],
        }

        text = EmbeddingService._profile_to_text(profile)

        assert "Skills: Python" in text
        assert "Experience: Developer" in text
        assert "Education: BS" in text

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_success(self):
        """Test calculate_semantic_similarity successful case"""
        profile_emb = [0.1, 0.2, 0.3]
        job_emb = [0.1, 0.2, 0.4]

        result = await EmbeddingService.calculate_semantic_similarity(
            profile_emb, job_emb
        )

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_empty_profile(self):
        """Test calculate_semantic_similarity with empty profile embedding"""
        profile_emb = []
        job_emb = [0.1, 0.2, 0.3]

        result = await EmbeddingService.calculate_semantic_similarity(
            profile_emb, job_emb
        )

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_empty_job(self):
        """Test calculate_semantic_similarity with empty job embedding"""
        profile_emb = [0.1, 0.2, 0.3]
        job_emb = []

        result = await EmbeddingService.calculate_semantic_similarity(
            profile_emb, job_emb
        )

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_exception(self):
        """Test calculate_semantic_similarity with exception"""
        profile_emb = [0.1, 0.2, 0.3]
        job_emb = [0.1, 0.2, 0.3]

        # Mock cosine_similarity to raise exception
        with patch(
            "backend.services.embedding_service.cosine_similarity",
            side_effect=Exception("Calc failed"),
        ):
            result = await EmbeddingService.calculate_semantic_similarity(
                profile_emb, job_emb
            )

            assert result == 0.0

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.EmbeddingService.is_available")
    @patch(
        "backend.services.embedding_service.EmbeddingService.generate_profile_embedding"
    )
    @patch("backend.services.embedding_service.EmbeddingService.generate_job_embedding")
    @patch(
        "backend.services.embedding_service.EmbeddingService.calculate_semantic_similarity"
    )
    async def test_analyze_job_match_success(
        self, mock_calc_sim, mock_gen_job_emb, mock_gen_prof_emb, mock_is_available
    ):
        """Test analyze_job_match successful case"""
        mock_is_available.return_value = True
        mock_gen_prof_emb.return_value = [0.1, 0.2, 0.3]
        mock_gen_job_emb.return_value = [0.1, 0.2, 0.4]
        mock_calc_sim.return_value = 0.8

        profile = {"full_name": "John Doe", "skills": ["Python", "JavaScript"]}
        job_desc = "Looking for Python developer with JavaScript skills"

        result = await EmbeddingService.analyze_job_match(profile, job_desc)

        assert result["score"] == 0.8
        assert "analysis" in result
        assert "matched_skills" in result
        assert "missing_skills" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.EmbeddingService.is_available")
    async def test_analyze_job_match_service_unavailable(self, mock_is_available):
        """Test analyze_job_match when service unavailable"""
        mock_is_available.return_value = False

        profile = {"skills": ["Python"]}
        job_desc = "Python job"

        result = await EmbeddingService.analyze_job_match(profile, job_desc)

        assert result["score"] == 0.5
        assert result["analysis"] == "Embedding service not available"
        assert result["matched_skills"] == []
        assert result["missing_skills"] == []
        assert result["recommendations"] == []

    @pytest.mark.asyncio
    @patch("backend.services.embedding_service.EmbeddingService.is_available")
    @patch(
        "backend.services.embedding_service.EmbeddingService.generate_profile_embedding"
    )
    async def test_analyze_job_match_exception(
        self, mock_gen_prof_emb, mock_is_available
    ):
        """Test analyze_job_match with exception"""
        mock_is_available.return_value = True
        mock_gen_prof_emb.side_effect = Exception("Generation failed")

        profile = {"skills": ["Python"]}
        job_desc = "Python job"

        result = await EmbeddingService.analyze_job_match(profile, job_desc)

        assert result["score"] == 0.5
        assert "Error analyzing match" in result["analysis"]
