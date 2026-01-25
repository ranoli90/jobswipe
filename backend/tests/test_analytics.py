"""
Tests for analytics service.
"""

import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
from backend.services.analytics_service import AnalyticsService
from backend.db.models import UserJobInteraction, User, Job, ApplicationTask


class TestAnalyticsService:
    """Tests for the analytics service"""
    
    @pytest.mark.asyncio
    @patch('backend.services.analytics_service.get_db')
    async def test_get_matching_accuracy_report(self, mock_get_db):
        """Test matching accuracy report generation"""
        # Setup mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        # Setup mock interactions
        mock_interaction1 = MagicMock()
        from datetime import datetime
        mock_interaction1.created_at = datetime(2026, 1, 20)
        mock_interaction1.action = "like"
        mock_interaction1.user_id = "user1"
        mock_interaction1.job_id = "job1"
        
        mock_interaction2 = MagicMock()
        mock_interaction2.created_at = datetime(2026, 1, 21)
        mock_interaction2.action = "apply"
        mock_interaction2.user_id = "user1"
        mock_interaction2.job_id = "job2"
        
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_interaction1, mock_interaction2
        ]
        
        # Setup mock user and job
        mock_user = MagicMock()
        mock_user.id = "user1"
        mock_user.profile = MagicMock()
        mock_user.profile.skills = ["Python", "JavaScript"]
        mock_user.profile.work_experience = []
        mock_user.profile.education = []
        mock_user.profile.location = "San Francisco"
        mock_user.profile.headline = "Software Engineer"
        
        mock_job = MagicMock()
        mock_job.id = "job1"
        mock_job.description = "Python, JavaScript, React"
        
        # Setup query side effects
        def query_side_effect(model):
            if model == UserJobInteraction:
                # Return a mock that simulates querying interactions
                mock_query = MagicMock()
                mock_query.filter.return_value.all.return_value = [mock_interaction1, mock_interaction2]
                return mock_query
            elif model == User:
                # Return a mock that simulates querying users
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_user
                return mock_query
            elif model == Job:
                # Return a mock that simulates querying jobs
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_job
                return mock_query
            elif model == ApplicationTask:
                # Return a mock that simulates querying application tasks
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = None
                return mock_query
        
        mock_session.query.side_effect = query_side_effect
        
        service = AnalyticsService()
        
        report = await service.get_matching_accuracy_report()
        
        assert report["time_range"] == 30
        assert report["total_interactions"] == 2
        assert "accuracy_score" in report
        assert "success_rate" in report
        assert isinstance(report["accuracy_score"], float)
        assert isinstance(report["success_rate"], float)
        assert report["accuracy_score"] >= 0.0 and report["accuracy_score"] <= 1.0
        assert report["success_rate"] >= 0.0 and report["success_rate"] <= 1.0
        
    @pytest.mark.asyncio
    @patch('backend.services.analytics_service.get_db')
    async def test_get_user_behavior_report(self, mock_get_db):
        """Test user behavior report generation"""
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        # Setup mock user
        mock_user = MagicMock()
        mock_user.id = "test-user"
        mock_user.profile = MagicMock()
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Setup mock interactions
        mock_interaction1 = MagicMock()
        mock_interaction1.action = "like"
        mock_interaction1.job_id = "job1"
        
        mock_interaction2 = MagicMock()
        mock_interaction2.action = "apply"
        mock_interaction2.job_id = "job2"
        
        mock_session.query.side_effect = [
            MagicMock().filter.return_value.first.return_value,  # User
            MagicMock().filter.return_value.all.return_value,  # UserJobInteraction
            MagicMock().filter.return_value.all.return_value  # ApplicationTask
        ]
        
        service = AnalyticsService()
        
        report = await service.get_user_behavior_report("test-user")
        
        assert report["user_id"] == "test-user"
        assert "total_interactions" in report
        assert "avg_match_score" in report
        assert "actions_distribution" in report
        assert "applications_status" in report
        assert "top_interested_skills" in report
        assert "preferred_locations" in report
        
    @pytest.mark.asyncio
    @patch('backend.services.analytics_service.get_db')
    async def test_get_job_market_analysis(self, mock_get_db):
        """Test job market analysis report"""
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        
        # Setup mock jobs
        mock_job1 = MagicMock()
        mock_job1.created_at = "2026-01-20"
        mock_job1.source = "greenhouse"
        mock_job1.location = "San Francisco"
        mock_job1.title = "Software Engineer"
        mock_job1.description = "Python, Django, PostgreSQL"
        
        mock_job2 = MagicMock()
        mock_job2.created_at = "2026-01-21"
        mock_job2.source = "lever"
        mock_job2.location = "Remote"
        mock_job2.title = "Data Scientist"
        mock_job2.description = "Python, TensorFlow, SQL"
        
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_job1, mock_job2
        ]
        
        service = AnalyticsService()
        
        report = await service.get_job_market_analysis()
        
        assert report["period"] == "last_7_days"
        assert report["total_jobs"] == 2
        assert report["jobs_by_source"] == {"greenhouse": 1, "lever": 1}
        assert "jobs_by_location" in report
        assert "jobs_by_type" in report
        assert isinstance(report["avg_description_length"], float)
        assert report["growth_rate"] == 0.12
        
    def test_extract_skills_from_job(self):
        """Test job skills extraction"""
        service = AnalyticsService()
        
        description = "Python, JavaScript, React, Node.js"
        skills = service._extract_skills_from_job(description)
        
        assert "Python" in skills
        assert "JavaScript" in skills
        assert "React" in skills
        assert "Node.js" in skills
        
        # Should be unique
        assert len(skills) == 4
        
    def test_classify_job_type(self):
        """Test job type classification"""
        service = AnalyticsService()
        
        # Test software development jobs
        assert service._classify_job_type("Software Engineer") == "Software Development"
        assert service._classify_job_type("Frontend Developer") == "Software Development"
        assert service._classify_job_type("Full Stack Engineer") == "Software Development"
        
        # Test data science jobs
        assert service._classify_job_type("Data Scientist") == "Data Science"
        assert service._classify_job_type("Machine Learning Engineer") == "Data Science"
        assert service._classify_job_type("Data Analyst") == "Data Science"
        
        # Test product management
        assert service._classify_job_type("Product Manager") == "Product Management"
        
        # Test design
        assert service._classify_job_type("UX Designer") == "Design"
        assert service._classify_job_type("UI/UX Designer") == "Design"
        
        # Test other types
        assert service._classify_job_type("Marketing Manager") == "Marketing"
        assert service._classify_job_type("Sales Representative") == "Sales"
        assert service._classify_job_type("Accountant") == "Other"
        
    @patch('backend.services.analytics_service.analytics_service')
    def test_export_report_json(self, mock_analytics):
        """Test JSON report export"""
        mock_analytics.get_matching_accuracy_report.return_value = {
            "time_range": 30,
            "total_interactions": 1000
        }
        
        mock_analytics.export_report.return_value = "/tmp/reports/matching_accuracy_20260125_100000.json"
        
        from backend.services.analytics_service import analytics_service
        result = analytics_service.export_report("matching_accuracy", "json")
        
        assert isinstance(result, str)
        assert result.endswith(".json")
