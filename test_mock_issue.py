import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from unittest.mock import patch, MagicMock
from backend.services.job_ingestion_service import JobIngestionService
import asyncio

async def test_mock():
    service = JobIngestionService()
    
    mock_ingest_greenhouse = MagicMock()
    mock_ingest_greenhouse.return_value = [{'id': '1', 'title': 'Software Engineer', 'source': 'greenhouse'}]
    
    mock_ingest_lever = MagicMock()
    mock_ingest_lever.return_value = [{'id': '2', 'title': 'Data Scientist', 'source': 'lever'}]
    
    # Monkey patch the methods
    service.ingest_greenhouse_jobs = mock_ingest_greenhouse
    service.ingest_lever_jobs = mock_ingest_lever
    
    jobs = await service.ingest_jobs_from_sources()
    print('Jobs returned:', jobs)
    print('Number of jobs:', len(jobs))
    
asyncio.run(test_mock())
