"""
Unit tests for Matching Service
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.matching import (calculate_job_score, compute_bm25_score,
                                       get_job_matches_for_profile,
                                       get_job_recommendations_for_profile,
                                       get_personalized_jobs, preprocess_text)


class TestMatchingService:
    """Test cases for Matching Service"""

    def test_preprocess_text_normal(self):
        """Test preprocess_text with normal text"""
        text = "The quick brown fox jumps over the lazy dog!"
        result = preprocess_text(text)

        # Should remove stopwords and punctuation, convert to lowercase
        expected = ["quick", "brown", "fox", "jumps", "lazy", "dog"]
        assert result == expected

    def test_preprocess_text_empty(self):
        """Test preprocess_text with empty text"""
        result = preprocess_text("")
        assert result == []

    def test_preprocess_text_none(self):
        """Test preprocess_text with None"""
        result = preprocess_text(None)
        assert result == []

    def test_preprocess_text_only_stopwords(self):
        """Test preprocess_text with only stopwords"""
        text = "the and for with you your our we is are to in on at of"
        result = preprocess_text(text)
        assert result == []

    def test_preprocess_text_short_words(self):
        """Test preprocess_text filtering short words"""
        text = "a an I to hi"  # All <= 2 chars or stopwords
        result = preprocess_text(text)
        assert result == []

    def test_compute_bm25_score_perfect_match(self):
        """Test compute_bm25_score with perfect match"""
        # Mock job and profile
        mock_job = MagicMock()
        mock_job.title = "Python Developer"
        mock_job.description = "Python Django developer needed"
        mock_job.company = "Tech Corp"

        mock_profile = MagicMock()
        mock_profile.skills = ["Python", "Django"]
        mock_profile.work_experience = [{"position": "Developer"}]
        mock_profile.education = [{"degree": "BS Computer Science"}]
        mock_profile.headline = "Python Developer"

        score = compute_bm25_score(mock_job, mock_profile)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_compute_bm25_score_no_match(self):
        """Test compute_bm25_score with no match"""
        mock_job = MagicMock()
        mock_job.title = "Java Developer"
        mock_job.description = "Java Spring developer needed"
        mock_job.company = "Tech Corp"

        mock_profile = MagicMock()
        mock_profile.skills = ["Python", "Django"]
        mock_profile.work_experience = []
        mock_profile.education = []
        mock_profile.headline = ""

        score = compute_bm25_score(mock_job, mock_profile)

        assert score == 0.0

    def test_compute_bm25_score_empty_profile(self):
        """Test compute_bm25_score with empty profile"""
        mock_job = MagicMock()
        mock_job.title = "Developer"
        mock_job.description = "Developer needed"
        mock_job.company = "Tech Corp"

        mock_profile = MagicMock()
        mock_profile.skills = []
        mock_profile.work_experience = []
        mock_profile.education = []
        mock_profile.headline = ""

        score = compute_bm25_score(mock_job, mock_profile)

        assert score == 0.0

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    async def test_get_personalized_jobs_success(self, mock_get_db):
        """Test get_personalized_jobs successful case"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        user_id = uuid.uuid4()

        # Mock profile exists
        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]
        mock_profile.location = "San Francisco"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile

        # Mock jobs
        mock_job1 = MagicMock()
        mock_job1.id = "job1"
        mock_job1.description = "Python developer job"
        mock_job1.location = "San Francisco"

        mock_job2 = MagicMock()
        mock_job2.id = "job2"
        mock_job2.description = "Java developer job"
        mock_job2.location = "New York"

        mock_db.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = [
            mock_job1,
            mock_job2,
        ]

        # Mock no interactions
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Mock calculate_job_score
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = [0.8, 0.3]  # Higher score for job1

            result = await get_personalized_jobs(user_id, page_size=2, db=mock_db)

            assert len(result) == 2
            assert result[0]["score"] == 0.8
            assert result[1]["score"] == 0.3
            # Should be sorted by score descending
            assert result[0]["score"] >= result[1]["score"]

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    async def test_get_personalized_jobs_no_profile(self, mock_get_db):
        """Test get_personalized_jobs when no profile exists"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        user_id = uuid.uuid4()

        # Mock no profile
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock jobs
        mock_jobs = [MagicMock(), MagicMock()]
        mock_db.query.return_value.order_by.return_value.all.return_value = mock_jobs

        result = await get_personalized_jobs(user_id, db=mock_db)

        assert len(result) == 2
        # Should return latest jobs when no profile

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    async def test_get_personalized_jobs_with_cursor(self, mock_get_db):
        """Test get_personalized_jobs with cursor pagination"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        user_id = uuid.uuid4()

        # Mock profile
        mock_profile = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile

        # Mock jobs with cursor filter
        mock_jobs = [MagicMock()]
        mock_db.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            mock_jobs
        )

        # Mock no interactions
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.return_value = 0.5

            result = await get_personalized_jobs(
                user_id, cursor="cursor123", db=mock_db
            )

            # Should filter by cursor
            mock_db.query.return_value.filter.assert_any_call(
                mock_db.query.return_value.filter.return_value.or_().order_by().id
                > "cursor123"
            )

    @pytest.mark.asyncio
    @patch("backend.services.matching.embedding_service")
    async def test_calculate_job_score_full(self, mock_embedding_service):
        """Test calculate_job_score with all components"""
        mock_job = MagicMock()
        mock_job.title = "Python Developer"
        mock_job.description = "Python Django developer needed"
        mock_job.company = "Tech Corp"
        mock_job.location = "San Francisco"

        mock_profile = MagicMock()
        mock_profile.skills = ["Python", "Django"]
        mock_profile.location = "San Francisco"
        mock_profile.work_experience = [{"position": "Python Developer"}]

        # Mock embedding service available
        mock_embedding_service.is_available.return_value = True

        # Mock embedding generation and similarity
        with patch(
            "backend.services.matching.EmbeddingService"
        ) as mock_emb_service_class:
            mock_emb_instance = MagicMock()
            mock_emb_service_class.return_value = mock_emb_instance

            mock_emb_instance.generate_profile_embedding = AsyncMock(
                return_value=[0.1, 0.2, 0.3]
            )
            mock_emb_instance.generate_job_embedding = AsyncMock(
                return_value=[0.1, 0.2, 0.4]
            )
            mock_emb_instance.calculate_semantic_similarity = AsyncMock(
                return_value=0.8
            )
            mock_emb_instance.analyze_job_match = AsyncMock(return_value={"score": 0.7})

            score = await calculate_job_score(mock_job, mock_profile)

            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
            # Should include BM25 (0.5), embedding (0.3), skill match (0.1), location match (0.05), experience match (0.05)

    @pytest.mark.asyncio
    @patch("backend.services.matching.embedding_service")
    async def test_calculate_job_score_no_embedding(self, mock_embedding_service):
        """Test calculate_job_score when embedding service unavailable"""
        mock_job = MagicMock()
        mock_job.title = "Python Developer"
        mock_job.description = "Python Django developer needed"
        mock_job.company = "Tech Corp"

        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]
        mock_profile.location = None
        mock_profile.work_experience = []

        # Mock embedding service unavailable
        mock_embedding_service.is_available.return_value = False

        score = await calculate_job_score(mock_job, mock_profile)

        assert isinstance(score, float)
        # Should only include BM25 score (0.5 weight)

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    @patch("backend.services.matching.tracer")
    async def test_get_job_matches_for_profile_success(self, mock_tracer, mock_get_db):
        """Test get_job_matches_for_profile successful case"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_profile = MagicMock()
        mock_profile.id = 123
        mock_profile.skills = ["Python"]

        # Mock span
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Mock jobs
        mock_job1 = MagicMock()
        mock_job1.description = "Python developer"
        mock_job2 = MagicMock()
        mock_job2.description = "Java developer"

        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_job1,
            mock_job2,
        ]

        # Mock calculate_job_score
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = [0.8, 0.3]

            result = await get_job_matches_for_profile(
                mock_profile, limit=10, db=mock_db
            )

            assert len(result) == 2
            assert result[0]["score"] == 0.8
            assert result[1]["score"] == 0.3
            assert result[0]["metadata"]["has_skill_match"] is True
            assert result[1]["metadata"]["has_skill_match"] is False

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    @patch("backend.services.matching.tracer")
    async def test_get_job_matches_for_profile_with_min_score(
        self, mock_tracer, mock_get_db
    ):
        """Test get_job_matches_for_profile with minimum score filter"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_profile = MagicMock()
        mock_profile.id = 123

        # Mock span
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Mock jobs
        mock_job1 = MagicMock()
        mock_job1.description = "High match job"
        mock_job2 = MagicMock()
        mock_job2.description = "Low match job"

        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_job1,
            mock_job2,
        ]

        # Mock calculate_job_score
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = [0.9, 0.4]  # One above, one below threshold

            result = await get_job_matches_for_profile(
                mock_profile, min_score=0.5, db=mock_db
            )

            assert len(result) == 1
            assert result[0]["score"] == 0.9

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    @patch("backend.services.matching.tracer")
    async def test_get_job_matches_for_profile_pagination(
        self, mock_tracer, mock_get_db
    ):
        """Test get_job_matches_for_profile with pagination"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_profile = MagicMock()
        mock_profile.id = 123

        # Mock span
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Mock many jobs
        mock_jobs = [MagicMock() for _ in range(50)]
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_jobs
        )

        # Mock calculate_job_score
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.return_value = 0.7

            result = await get_job_matches_for_profile(
                mock_profile, limit=10, offset=20, db=mock_db
            )

            assert len(result) == 10  # Should return only the paginated results

    @pytest.mark.asyncio
    @patch("backend.services.matching.get_db")
    @patch("backend.services.matching.tracer")
    async def test_get_job_matches_for_profile_exception(
        self, mock_tracer, mock_get_db
    ):
        """Test get_job_matches_for_profile with exception"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_profile = MagicMock()
        mock_profile.id = 123

        # Mock span
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Mock database query to raise exception
        mock_db.query.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await get_job_matches_for_profile(mock_profile, db=mock_db)

        # Should record exception in span
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()

    def test_get_job_recommendations_for_profile_success(self):
        """Test get_job_recommendations_for_profile successful case"""
        mock_profile = MagicMock()
        mock_profile.id = 123
        mock_profile.skills = ["Python"]

        # Mock database
        mock_db = MagicMock()

        # Mock jobs
        mock_job1 = MagicMock()
        mock_job1.description = "Python job"
        mock_job2 = MagicMock()
        mock_job2.description = "Another Python job"

        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_job1,
            mock_job2,
        ]

        with patch("backend.services.matching.get_db", return_value=mock_db):
            with patch(
                "backend.services.matching.calculate_job_score"
            ) as mock_calc_score:
                mock_calc_score.side_effect = [0.8, 0.6]

                result = get_job_recommendations_for_profile(mock_profile, limit=5)

                assert len(result) == 2
                assert result[0]["score"] == 0.8
                assert result[1]["score"] == 0.6
                # Should be sorted by score descending

    def test_get_job_recommendations_for_profile_exception(self):
        """Test get_job_recommendations_for_profile with exception"""
        mock_profile = MagicMock()
        mock_profile.id = 123

        # Mock database to raise exception
        with patch("backend.services.matching.get_db") as mock_get_db:
            mock_get_db.return_value.query.side_effect = Exception("DB error")

            with pytest.raises(Exception):
                get_job_recommendations_for_profile(mock_profile)
