"""
Simple tests for job ingestion service without external dependencies.
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.job_ingestion_service import JobIngestionService


class TestJobIngestionServiceSimple:
    """Simple tests for the job ingestion service without external dependencies"""
    
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.JobIngestionService.ingest_greenhouse_jobs', new_callable=AsyncMock)
    @patch('backend.services.job_ingestion_service.JobIngestionService.ingest_lever_jobs', new_callable=AsyncMock)
    async def test_ingest_jobs_from_sources(
        self, mock_ingest_lever, mock_ingest_greenhouse
    ):
        """Test that jobs are ingested from all sources"""
        # Setup mocks
        mock_ingest_greenhouse.return_value = [
            {"id": "1", "title": "Software Engineer", "source": "greenhouse"}
        ]
        mock_ingest_lever.return_value = [
            {"id": "2", "title": "Data Scientist", "source": "lever"}
        ]
        
        service = JobIngestionService()
        jobs = await service.ingest_jobs_from_sources()
        
        assert len(jobs) == 2
        assert any(job["id"] == "1" for job in jobs)
        assert any(job["id"] == "2" for job in jobs)
        mock_ingest_greenhouse.assert_called_once()
        mock_ingest_lever.assert_called_once()
        
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.aiohttp.ClientSession')
    async def test_ingest_greenhouse_jobs(self, mock_session):
        """Test Greenhouse API job ingestion"""
        # Mock session and response
        mock_session_instance = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = asyncio.Future()
        mock_response.json.return_value.set_result({
            "jobs": [
                {
                    "id": "123",
                    "title": "Software Engineer",
                    "location": {"name": "San Francisco"},
                    "content": "Python, JavaScript, React",
                    "absolute_url": "https://example.com/job/123",
                    "metadata": {
                        "salary_range": "$100k-$150k",
                        "type": "Full-time"
                    }
                },
                {
                    "id": "456",
                    "title": "Sales Manager",
                    "location": {"name": "New York"},
                    "content": "Sales experience required",
                    "absolute_url": "https://example.com/job/456",
                    "metadata": {}
                }
            ]
        })
        
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        
        service = JobIngestionService()
        jobs = await service.ingest_greenhouse_jobs({
            "api_url": "https://boards-api.greenhouse.io/v1/boards/",
            "companies": ["test-company"]
        })
        
        assert len(jobs) == 1  # Only software engineer should be included
        assert jobs[0]["id"] == "123"
        assert jobs[0]["title"] == "Software Engineer"
        assert jobs[0]["location"] == "San Francisco"
        assert "Python" in jobs[0]["description"]
        
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.aiohttp.ClientSession')
    async def test_ingest_lever_jobs(self, mock_session):
        """Test Lever API job ingestion"""
        # Mock session and response
        mock_session_instance = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = asyncio.Future()
        mock_response.json.return_value.set_result({
            "data": [
                {
                    "id": "789",
                    "text": {
                        "position": "Data Scientist"
                    },
                    "categories": {
                        "location": "Remote",
                        "type": "Full-time"
                    },
                    "description": "Machine learning, Python, SQL",
                    "hostedUrl": "https://example.com/lever-job",
                    "compensationRange": {
                        "label": "$120k-$160k"
                    }
                },
                {
                    "id": "012",
                    "text": {
                        "position": "Marketing Specialist"
                    },
                    "categories": {
                        "location": "Chicago",
                        "type": "Full-time"
                    },
                    "description": "Marketing experience required",
                    "hostedUrl": "https://example.com/marketing-job",
                    "compensationRange": {}
                }
            ]
        })
        
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        
        service = JobIngestionService()
        jobs = await service.ingest_lever_jobs({
            "api_url": "https://api.lever.co/v0/postings/",
            "companies": ["test-company"]
        })
        
        assert len(jobs) == 1  # Only data scientist should be included
        assert jobs[0]["id"] == "789"
        assert jobs[0]["title"] == "Data Scientist"
        assert jobs[0]["location"] == "Remote"
        assert "Machine learning" in jobs[0]["description"]
        
    def test_job_sources_configuration(self):
        """Test that job sources are correctly configured"""
        service = JobIngestionService()
        
        assert "greenhouse" in JobIngestionService.JOB_SOURCES
        assert "lever" in JobIngestionService.JOB_SOURCES
        
        greenhouse_config = JobIngestionService.JOB_SOURCES["greenhouse"]
        assert "api_url" in greenhouse_config
        assert "companies" in greenhouse_config
        assert len(greenhouse_config["companies"]) > 0
        
        lever_config = JobIngestionService.JOB_SOURCES["lever"]
        assert "api_url" in lever_config
        assert "companies" in lever_config
        assert len(lever_config["companies"]) > 0
        
    def test_job_types_configuration(self):
        """Test that job types are correctly configured"""
        service = JobIngestionService()
        
        assert len(JobIngestionService.JOB_TYPES) > 0
        assert "Software Engineer" in JobIngestionService.JOB_TYPES
        assert "Data Scientist" in JobIngestionService.JOB_TYPES
        assert "Product Manager" in JobIngestionService.JOB_TYPES
        
    def test_source_companies_configuration(self):
        """Test that companies are configured for each source"""
        service = JobIngestionService()
        
        greenhouse_companies = JobIngestionService.JOB_SOURCES["greenhouse"]["companies"]
        assert len(greenhouse_companies) >= 3
        assert any("airbnb" in company.lower() for company in greenhouse_companies)
        assert any("uber" in company.lower() for company in greenhouse_companies)
        
        lever_companies = JobIngestionService.JOB_SOURCES["lever"]["companies"]
        assert len(lever_companies) >= 3
        assert any("github" in company.lower() for company in lever_companies)
        assert any("slack" in company.lower() for company in lever_companies)
