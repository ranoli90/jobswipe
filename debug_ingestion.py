#!/usr/bin/env python3
"""Debug script for job ingestion service"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
from backend.services.job_ingestion_service import JobIngestionService

async def debug_test_ingest_jobs():
    print("Debugging test_ingest_jobs_from_sources")
    
    # Create the service instance
    service = JobIngestionService()
    print(f"Service created: {service}")
    print(f"JOB_SOURCES: {service.JOB_SOURCES}")
    print(f"JOB_TYPES: {service.JOB_TYPES}")
    
    # Patch the methods
    with patch('backend.services.job_ingestion_service.JobIngestionService.ingest_greenhouse_jobs') as mock_ingest_greenhouse, \
         patch('backend.services.job_ingestion_service.JobIngestionService.ingest_lever_jobs') as mock_ingest_lever:
        
        # Setup mocks
        mock_ingest_greenhouse.return_value = [
            {"id": "1", "title": "Software Engineer", "source": "greenhouse"}
        ]
        mock_ingest_lever.return_value = [
            {"id": "2", "title": "Data Scientist", "source": "lever"}
        ]
        
        print("Mocks setup")
        
        # Call the method
        print("Calling ingest_jobs_from_sources...")
        jobs = await service.ingest_jobs_from_sources()
        
        print(f"Jobs returned: {len(jobs)} jobs")
        print(f"Jobs: {jobs}")
        
        # Verify calls
        print(f"mock_ingest_greenhouse.called: {mock_ingest_greenhouse.called}")
        print(f"mock_ingest_lever.called: {mock_ingest_lever.called}")
        
        if mock_ingest_greenhouse.called:
            print(f"mock_ingest_greenhouse.call_args: {mock_ingest_greenhouse.call_args}")
        if mock_ingest_lever.called:
            print(f"mock_ingest_lever.call_args: {mock_ingest_lever.call_args}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_test_ingest_jobs())
