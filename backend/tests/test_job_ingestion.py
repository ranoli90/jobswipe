"""
Tests for the job ingestion service with free, open-source job sources.
"""

import pytest
import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.job_ingestion_service import JobIngestionService


class TestJobIngestionService:
    """Tests for the job ingestion service with free job sources"""
    
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.JobIngestionService.ingest_rss_feed', new_callable=AsyncMock)
    @patch('backend.services.job_ingestion_service.JobIngestionService.ingest_scraped_jobs', new_callable=AsyncMock)
    async def test_ingest_jobs_from_sources(self, mock_scrape, mock_rss):
        """Test that jobs are ingested from all sources"""
        mock_rss.return_value = [
            {"id": "1", "title": "Software Engineer", "source": "rss"}
        ]
        mock_scrape.return_value = [
            {"id": "2", "title": "Data Scientist", "source": "scraped"}
        ]
        
        service = JobIngestionService()
        
        jobs = await service.ingest_jobs_from_sources()
        
        assert len(jobs) == 7
        assert any(job["id"] == "1" for job in jobs)
        assert any(job["id"] == "2" for job in jobs)
        assert len([j for j in jobs if j["source"] == "rss"]) == 6
        assert len([j for j in jobs if j["source"] == "scraped"]) == 1
        
    @pytest.mark.asyncio
    async def test_ingest_rss_feed_mocked(self):
        """Test RSS feed ingestion with mocked session"""
        with patch('backend.services.job_ingestion_service.feedparser.parse') as mock_parse:
            # Mock the feedparser result to act like a real feedparser object
            mock_feed = MagicMock()
            mock_feed.entries = [
                MagicMock(
                    title='Software Engineer',
                    link='https://example.com/job1',
                    summary='Remote software engineer position with competitive salary',
                    published='2024-01-01T00:00:00Z',
                    source=MagicMock(title='Example Company')
                )
            ]
            mock_parse.return_value = mock_feed
            
            with patch('backend.services.job_ingestion_service.aiohttp.ClientSession') as mock_session:
                mock_session_instance = MagicMock()
                
                class MockResponse:
                    def raise_for_status(self):
                        pass
                        
                    async def text(self):
                        return ''
                        
                    async def __aenter__(self):
                        return self
                        
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        pass
                
                mock_session_instance.get = MagicMock(return_value=MockResponse())
                mock_session.return_value.__aenter__.return_value = mock_session_instance
                
                service = JobIngestionService()
                
                jobs = await service.ingest_rss_feed({
                    "url": "https://example.com/feed",
                    "category": "software"
                })
                
                assert len(jobs) == 1
                assert jobs[0]["title"] == "Software Engineer"
                assert jobs[0]["source"] == "software"
                
    @pytest.mark.asyncio
    async def test_ingest_scraped_jobs_mocked(self):
        """Test company career page scraping with mocked session"""
        mock_html = '''
        <html>
            <body>
                <a href="/careers/software-engineer" class="job-link">Software Engineer</a>
                <a href="/careers/data-scientist" class="job-link">Data Scientist</a>
                <a href="/careers/marketing" class="job-link">Marketing Manager</a>
            </body>
        </html>
        '''
        
        with patch('backend.services.job_ingestion_service.aiohttp.ClientSession') as mock_session:
            mock_session_instance = MagicMock()
            
            class MockResponse:
                def raise_for_status(self):
                    pass
                    
                async def text(self):
                    return mock_html
                    
                async def __aenter__(self):
                    return self
                    
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            mock_session_instance.get = MagicMock(return_value=MockResponse())
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            service = JobIngestionService()
            
            jobs = await service.ingest_scraped_jobs({
                "companies": [
                    {
                        "name": "example",
                        "url": "https://example.com/careers",
                        "job_selector": "a.job-link"
                    }
                ]
            })
            
            assert len(jobs) == 2
            assert any(job["title"] == "Software Engineer" for job in jobs)
            assert any(job["title"] == "Data Scientist" for job in jobs)
                
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.get_db')
    async def test_process_job(self, mock_get_db):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock the generator behavior of get_db()
        def mock_db_generator():
            yield mock_session
            
        mock_get_db.return_value = mock_db_generator()
        
        service = JobIngestionService()
        
        await service.process_job({
            "id": "1",
            "title": "Software Engineer",
            "company": "Example Inc",
            "location": "Remote",
            "description": "Great job opportunity with competitive salary and benefits. " * 20,
            "url": "https://example.com/job1",
            "source": "rss",
            "salary_range": "$100K - $150K",
            "type": "software",
            "created_at": "2024-01-01T00:00:00Z"
        })
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.get_db')
    async def test_process_existing_job(self, mock_get_db):
        mock_job = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock the generator behavior of get_db()
        def mock_db_generator():
            yield mock_session
            
        mock_get_db.return_value = mock_db_generator()
        
        service = JobIngestionService()
        
        await service.process_job({
            "id": "1",
            "title": "Updated Job Title",
            "company": "Example Inc",
            "location": "Remote",
            "description": "Updated job description. " * 20,
            "url": "https://example.com/job1",
            "source": "rss",
            "salary_range": "$100K - $150K",
            "type": "software",
            "created_at": "2024-01-01T00:00:00Z"
        })
        
        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()
        
    @pytest.mark.asyncio
    @patch('backend.services.job_ingestion_service.JobIngestionService.ingest_jobs_from_sources')
    @patch('backend.services.job_ingestion_service.JobIngestionService.process_jobs_batch')
    async def test_run_once(self, mock_process_batch, mock_ingest):
        mock_ingest.return_value = [
            {"id": "1", "title": "Software Engineer", "source": "rss"}
        ]
        mock_process_batch.return_value = (1, 0)
        
        service = JobIngestionService()
        
        await service.run_once()
        
        mock_ingest.assert_called_once()
        mock_process_batch.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        with patch('backend.services.job_ingestion_service.aiohttp.ClientSession') as mock_session:
            mock_session_instance = MagicMock()
            
            class MockResponse:
                async def __aenter__(self):
                    raise Exception("API Connection Error")
                    
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            mock_session_instance.get = MagicMock(return_value=MockResponse())
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            
            service = JobIngestionService()
            
            jobs = await service.ingest_rss_feed({
                "url": "https://example.com/invalid-feed",
                "category": "software"
            })
            
            assert len(jobs) == 0