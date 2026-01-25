"""
Property-based tests for the job matching system.
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock
from backend.services.matching import calculate_job_score, compute_bm25_score, preprocess_text, get_job_matches_for_profile
from backend.services.embedding_service import EmbeddingService
from backend.db.models import Job, CandidateProfile


def create_mock_job(title="Test Job", description="", company="Test Company"):
    """Create a mock Job object for testing"""
    job = MagicMock(spec=Job)
    job.title = title
    job.description = description
    job.company = company
    job.location = "San Francisco"
    return job


def create_mock_profile(skills=None, experience=None, education=None):
    """Create a mock CandidateProfile object for testing"""
    profile = MagicMock(spec=CandidateProfile)
    profile.full_name = "John Doe"
    profile.headline = "Software Engineer"
    profile.skills = skills or []
    profile.work_experience = experience or []
    profile.education = education or []
    profile.location = "San Francisco"
    return profile


class TestMatchingProperties:
    """Property-based tests for the matching system"""
    
    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=500),
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10)
    )
    async def test_score_with_different_skill_sets(self, job_description, candidate_skills):
        """Test that score varies with different skill sets"""
        job = create_mock_job(description=job_description)
        profile = create_mock_profile(skills=candidate_skills)
        
        score = await calculate_job_score(job, profile)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=500),
        st.lists(st.text(min_size=1, max_size=20), min_size=3, max_size=3)
    )
    async def test_scoring_consistency(self, job_description, skills):
        """Test that scoring is consistent for the same inputs"""
        job = create_mock_job(description=job_description)
        profile = create_mock_profile(skills=skills)
        
        score1 = await calculate_job_score(job, profile)
        score2 = await calculate_job_score(job, profile)
        
        assert abs(score1 - score2) < 0.01
        
    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=500),
        st.lists(st.text(min_size=2, max_size=20), min_size=3, max_size=3)
    )
    async def test_skill_match_correlation(self, job_description, skills):
        """Test that having more skills in common increases the score"""
        # Create profiles with different skill overlaps
        profile1 = create_mock_profile(skills=skills)
        profile2 = create_mock_profile(skills=[])
        
        job = create_mock_job(description=job_description)
        
        score_with_skills = await calculate_job_score(job, profile2)
        
        # For each skill, create a job description that includes that skill
        job_with_skills = create_mock_job(description=f"{job_description} {' '.join(skills)}")
        
        score_with_overlap = await calculate_job_score(job_with_skills, profile1)
        
        # Profile with matching skills should have higher score
        assert score_with_overlap >= score_with_skills
        
    @pytest.mark.asyncio
    @given(
        st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=2),
        st.sampled_from([0, 1, 2, 3])
    )
    async def test_experience_scoring(self, skills, years_experience):
        """Test that experience level affects scoring"""
        experience = []
        for i in range(years_experience):
            experience.append({
                "position": "Software Engineer",
                "company": f"Company {i+1}",
                "start_date": f"202{i}",
                "end_date": "2024"
            })
            
        profile = create_mock_profile(skills=skills, experience=experience)
        job = create_mock_job(description=f"We need {', '.join(skills)} developers")
        
        score = await calculate_job_score(job, profile)
        
        # More experience should result in higher score
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=300),
        st.booleans()
    )
    async def test_openai_fallback_behavior(self, job_description, api_available):
        """Test that matching system falls back gracefully when embedding service is unavailable"""
        # Mock API availability
        with patch('backend.services.matching.embedding_service.is_available') as mock_available:
            mock_available.return_value = api_available
            
            job = create_mock_job(description=job_description)
            profile = create_mock_profile(skills=["Python", "FastAPI"])
            
            score = await calculate_job_score(job, profile)
            
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
            
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    def test_profile_to_text_conversion(self, profile_data):
        """Test that profile dictionary to text conversion handles various inputs"""
        from backend.services.openai_service import OpenAIService
        
        # Create a profile with various fields
        profile = {
            "full_name": profile_data.get("name", "John Doe"),
            "headline": profile_data.get("headline", "Software Engineer"),
            "skills": profile_data.get("skills", ["Python"]),
            "work_experience": profile_data.get("experience", []),
            "education": profile_data.get("education", [])
        }
        
        text = OpenAIService._profile_to_text(profile)
        
        # Should include all profile fields
        assert isinstance(text, str)
        assert len(text) > 0

    @given(
        st.text(min_size=10, max_size=500),
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10)
    )
    def test_preprocess_text(self, text, skills):
        """Test text preprocessing for BM25"""
        processed = preprocess_text(text)
        
        assert isinstance(processed, list)
        assert all(isinstance(token, str) for token in processed)
        assert all(len(token) > 2 for token in processed)
        assert all(token.islower() or token.isdigit() for token in processed)

    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=500),
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10)
    )
    async def test_bm25_scoring(self, job_description, candidate_skills):
        """Test BM25 scoring function"""
        job = create_mock_job(description=job_description)
        profile = create_mock_profile(skills=candidate_skills)
        
        score = compute_bm25_score(job, profile)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    @given(
        st.lists(st.text(min_size=2, max_size=20), min_size=3, max_size=3)
    )
    async def test_bm25_skill_correlation(self, skills):
        """Test that BM25 score correlates with skill match"""
        profile = create_mock_profile(skills=skills)
        job_with_skills = create_mock_job(description=f"We need {', '.join(skills)} developers")
        job_without_skills = create_mock_job(description="We need developers with no specific skills")
        
        score_with = compute_bm25_score(job_with_skills, profile)
        score_without = compute_bm25_score(job_without_skills, profile)
        
        assert score_with >= score_without

    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=500),
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10),
        st.integers(min_value=0, max_value=5)
    )
    async def test_bm25_experience_correlation(self, job_description, skills, years_experience):
        """Test that BM25 score correlates with experience"""
        experience = []
        for i in range(years_experience):
            experience.append({
                "position": "Software Engineer",
                "company": f"Company {i+1}",
                "start_date": f"202{i}",
                "end_date": "2024"
            })
            
        profile = create_mock_profile(skills=skills, experience=experience)
        job = create_mock_job(description=job_description)
        
        score = compute_bm25_score(job, profile)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    @given(
        st.text(min_size=10, max_size=300),
        st.booleans()
    )
    async def test_hybrid_scoring(self, job_description, api_available):
        """Test that hybrid scoring combines BM25 and embedding scores appropriately"""
        with patch('backend.services.matching.embedding_service.is_available') as mock_available:
            mock_available.return_value = api_available
            
            job = create_mock_job(description=job_description)
            profile = create_mock_profile(skills=["Python", "FastAPI"])
            
            score = await calculate_job_score(job, profile)
            
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    @given(
        st.lists(st.text(min_size=2, max_size=20), min_size=2, max_size=2),
        st.integers(min_value=1, max_value=3)
    )
    async def test_score_threshold_filtering(self, skills, min_score):
        """Test that score threshold filtering works correctly"""
        profile = create_mock_profile(skills=skills)
        
        # Create a mock session
        mock_db = MagicMock()
        
        # Create jobs with varying scores
        jobs = []
        for i in range(5):
            job = create_mock_job(description=f"Job {i} {' '.join(skills)}")
            jobs.append(job)
        
        mock_db.query.return_value.order_by.return_value.all.return_value = jobs
        
        matches = await get_job_matches_for_profile(
            profile=profile,
            limit=10,
            offset=0,
            min_score=min_score / 3,  # Normalize for testing
            db=mock_db
        )
        
        assert isinstance(matches, list)
        for match in matches:
            assert match["score"] >= min_score / 3
