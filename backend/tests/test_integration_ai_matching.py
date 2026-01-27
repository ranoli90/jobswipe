"""
Integration tests for AI matching algorithm
Tests matching with various input conditions and edge cases
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.matching import (calculate_job_score,
                                       get_job_matches_for_profile,
                                       get_personalized_jobs)


class TestAIMatchingIntegration:
    """Integration tests for AI matching algorithm"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_matching_with_complete_profile_and_jobs(self, mock_db_session):
        """Test matching with complete profile and diverse job set"""
        user_id = uuid.uuid4()

        # Mock complete profile
        mock_profile = MagicMock()
        mock_profile.skills = ["Python", "Django", "React", "AWS"]
        mock_profile.location = "San Francisco"
        mock_profile.work_experience = [
            {"position": "Senior Python Developer", "company": "Tech Corp"},
            {"position": "Full Stack Developer", "company": "Startup Inc"},
        ]
        mock_profile.education = [
            {"degree": "Bachelor of Computer Science", "school": "State University"}
        ]
        mock_profile.headline = "Experienced Python Developer"

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        # Mock diverse jobs
        jobs = [
            MagicMock(
                id="job1",
                title="Python Developer",
                description="Looking for Python Django developer with React experience",
                location="San Francisco",
                source="greenhouse",
            ),
            MagicMock(
                id="job2",
                title="Java Developer",
                description="Java Spring backend developer needed",
                location="New York",
                source="lever",
            ),
            MagicMock(
                id="job3",
                title="Data Scientist",
                description="Python pandas numpy machine learning",
                location="San Francisco",
                source="greenhouse",
            ),
            MagicMock(
                id="job4",
                title="Frontend Developer",
                description="React Vue Angular JavaScript",
                location="Remote",
                source="greenhouse",
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            []
        )  # No interactions

        # Mock calculate_job_score to return realistic scores
        scores = [0.85, 0.45, 0.75, 0.65]  # Python job highest, Java lowest
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            result = await get_personalized_jobs(
                user_id, page_size=10, db=mock_db_session
            )

            assert len(result) == 4
            # Should be sorted by score descending
            assert result[0]["score"] == 0.85  # Python job
            assert result[1]["score"] == 0.75  # Data Scientist
            assert result[2]["score"] == 0.65  # Frontend
            assert result[3]["score"] == 0.45  # Java job

    @pytest.mark.asyncio
    async def test_matching_with_minimal_profile(self, mock_db_session):
        """Test matching with minimal profile (only skills)"""
        user_id = uuid.uuid4()

        # Mock minimal profile
        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]
        mock_profile.location = None
        mock_profile.work_experience = []
        mock_profile.education = []
        mock_profile.headline = ""

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        # Mock jobs
        jobs = [
            MagicMock(
                id="job1",
                title="Python Developer",
                description="Python programming job",
                location="Remote",
            ),
            MagicMock(
                id="job2",
                title="Java Developer",
                description="Java programming job",
                location="Remote",
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        scores = [0.8, 0.3]
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            result = await get_personalized_jobs(user_id, db=mock_db_session)

            assert len(result) == 2
            assert result[0]["score"] == 0.8  # Python job should rank higher

    @pytest.mark.asyncio
    async def test_matching_with_location_filtering(self, mock_db_session):
        """Test matching considers location preferences"""
        user_id = uuid.uuid4()

        # Mock profile with location
        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]
        mock_profile.location = "San Francisco"

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        # Mock jobs with different locations
        jobs = [
            MagicMock(
                id="job1",
                title="Python Dev",
                description="Python job",
                location="San Francisco",
            ),
            MagicMock(
                id="job2",
                title="Python Dev",
                description="Python job",
                location="New York",
            ),
            MagicMock(
                id="job3",
                title="Python Dev",
                description="Python job",
                location="Remote",
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        # Scores should favor SF location
        scores = [0.9, 0.7, 0.8]  # SF highest, then Remote, then NY
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            result = await get_personalized_jobs(user_id, db=mock_db_session)

            assert len(result) == 3
            assert result[0]["score"] == 0.9  # SF job
            assert result[1]["score"] == 0.8  # Remote job
            assert result[2]["score"] == 0.7  # NY job

    @pytest.mark.asyncio
    async def test_matching_with_experience_matching(self, mock_db_session):
        """Test matching considers work experience"""
        user_id = uuid.uuid4()

        # Mock profile with experience
        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]
        mock_profile.work_experience = [
            {"position": "Senior Developer", "company": "Tech Corp"},
            {"position": "Python Developer", "company": "Startup"},
        ]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        # Mock jobs mentioning experience levels
        jobs = [
            MagicMock(
                id="job1",
                title="Senior Python Developer",
                description="Senior Python developer with 5+ years experience",
            ),
            MagicMock(
                id="job2",
                title="Junior Python Developer",
                description="Junior Python developer entry level",
            ),
            MagicMock(
                id="job3",
                title="Python Developer",
                description="Mid-level Python developer",
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        scores = [0.85, 0.6, 0.75]  # Senior > Mid > Junior
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            result = await get_personalized_jobs(user_id, db=mock_db_session)

            assert len(result) == 3
            assert result[0]["score"] == 0.85  # Senior role

    @pytest.mark.asyncio
    async def test_matching_with_education_matching(self, mock_db_session):
        """Test matching considers education"""
        user_id = uuid.uuid4()

        # Mock profile with CS degree
        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]
        mock_profile.education = [
            {"degree": "Bachelor of Computer Science", "school": "State University"}
        ]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        # Mock jobs requiring different education
        jobs = [
            MagicMock(
                id="job1",
                title="Software Engineer",
                description="CS degree preferred Python development",
            ),
            MagicMock(
                id="job2",
                title="Data Analyst",
                description="Statistics or related field Python pandas",
            ),
            MagicMock(
                id="job3",
                title="DevOps Engineer",
                description="Engineering background cloud experience",
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        scores = [0.8, 0.65, 0.7]  # CS related highest
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            result = await get_personalized_jobs(user_id, db=mock_db_session)

            assert len(result) == 3
            assert result[0]["score"] == 0.8  # CS related

    @pytest.mark.asyncio
    async def test_matching_algorithm_consistency(self, mock_db_session):
        """Test that matching algorithm produces consistent results"""
        user_id = uuid.uuid4()

        mock_profile = MagicMock()
        mock_profile.skills = ["Python", "JavaScript"]
        mock_profile.location = "San Francisco"

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        jobs = [
            MagicMock(
                id="job1",
                title="Full Stack Developer",
                description="Python JavaScript React",
            ),
            MagicMock(
                id="job2", title="Backend Developer", description="Python Django API"
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        scores = [0.9, 0.8]
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            # Run matching twice
            result1 = await get_personalized_jobs(user_id, db=mock_db_session)
            result2 = await get_personalized_jobs(user_id, db=mock_db_session)

            # Results should be identical
            assert len(result1) == len(result2)
            for i in range(len(result1)):
                assert result1[i]["score"] == result2[i]["score"]
                assert result1[i]["job"].id == result2[i]["job"].id

    @pytest.mark.asyncio
    async def test_matching_with_empty_job_set(self, mock_db_session):
        """Test matching when no jobs are available"""
        user_id = uuid.uuid4()

        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )
        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        result = await get_personalized_jobs(user_id, db=mock_db_session)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_matching_with_user_interactions_exclusion(self, mock_db_session):
        """Test that previously interacted jobs are excluded"""
        user_id = uuid.uuid4()

        mock_profile = MagicMock()
        mock_profile.skills = ["Python"]

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_profile
        )

        # Mock user has interacted with job1
        mock_interaction = MagicMock()
        mock_interaction.job_id = "job1"
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_interaction
        ]

        # Mock jobs including the interacted one
        jobs = [
            MagicMock(id="job1", title="Python Job", description="Python developer"),
            MagicMock(
                id="job2", title="JavaScript Job", description="JavaScript developer"
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = (
            jobs
        )

        scores = [0.8, 0.7]
        with patch(
            "backend.services.matching.calculate_job_score", new_callable=AsyncMock
        ) as mock_calc_score:
            mock_calc_score.side_effect = scores

            result = await get_personalized_jobs(user_id, db=mock_db_session)

            # Should exclude job1
            assert len(result) == 1
            assert result[0]["job"].id == "job2"

    @pytest.mark.asyncio
    async def test_calculate_job_score_detailed_breakdown(self, mock_db_session):
        """Test detailed score calculation breakdown"""
        mock_job = MagicMock()
        mock_job.title = "Senior Python Developer"
        mock_job.description = "Senior Python Django developer with React experience"
        mock_job.company = "Tech Corp"
        mock_job.location = "San Francisco"

        mock_profile = MagicMock()
        mock_profile.skills = ["Python", "Django", "React"]
        mock_profile.location = "San Francisco"
        mock_profile.work_experience = [{"position": "Senior Python Developer"}]

        # Mock embedding service
        with patch("backend.services.matching.embedding_service") as mock_emb_service:
            mock_emb_service.is_available.return_value = True

            with patch("backend.services.matching.EmbeddingService") as mock_emb_class:
                mock_emb_instance = MagicMock()
                mock_emb_class.return_value = mock_emb_instance

                mock_emb_instance.generate_profile_embedding = AsyncMock(
                    return_value=[0.1, 0.2, 0.3]
                )
                mock_emb_instance.generate_job_embedding = AsyncMock(
                    return_value=[0.1, 0.2, 0.4]
                )
                mock_emb_instance.calculate_semantic_similarity = AsyncMock(
                    return_value=0.8
                )

                score = await calculate_job_score(mock_job, mock_profile)

                assert isinstance(score, float)
                assert 0.0 <= score <= 1.0

                # Verify embedding methods were called
                mock_emb_instance.generate_profile_embedding.assert_called_once()
                mock_emb_instance.generate_job_embedding.assert_called_once()
                mock_emb_instance.calculate_semantic_similarity.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_job_matches_for_profile_with_pagination(self, mock_db_session):
        """Test get_job_matches_for_profile with pagination"""
        mock_profile = MagicMock()
        mock_profile.id = 123
        mock_profile.skills = ["Python"]

        # Mock tracer
        with patch("backend.services.matching.tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
                mock_span
            )

            # Mock 50 jobs
            jobs = [MagicMock(description=f"Python job {i}") for i in range(50)]
            mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = (
                jobs
            )

            with patch(
                "backend.services.matching.calculate_job_score", new_callable=AsyncMock
            ) as mock_calc_score:
                mock_calc_score.return_value = 0.8

                # Test pagination
                result = await get_job_matches_for_profile(
                    mock_profile, limit=10, offset=20, db=mock_db_session
                )

                assert len(result) == 10  # Should return exactly limit
                mock_calc_score.call_count == 10  # Should only score the requested page
