#!/usr/bin/env python3
"""Run a single test without pytest to get debug output"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from unittest.mock import MagicMock, patch

from backend.services.job_ingestion_service import JobIngestionService


async def run_test():
    print("=== Running test_ingest_jobs_from_sources ===")

    service = JobIngestionService()

    with patch(
        "backend.services.job_ingestion_service.JobIngestionService.ingest_greenhouse_jobs"
    ) as mock_ingest_greenhouse, patch(
        "backend.services.job_ingestion_service.JobIngestionService.ingest_lever_jobs"
    ) as mock_ingest_lever:

        # Setup mocks
        mock_ingest_greenhouse.return_value = [
            {"id": "1", "title": "Software Engineer", "source": "greenhouse"}
        ]
        mock_ingest_lever.return_value = [
            {"id": "2", "title": "Data Scientist", "source": "lever"}
        ]

        print("Mocks setup successfully")

        # Call method
        try:
            print("Calling ingest_jobs_from_sources...")
            jobs = await service.ingest_jobs_from_sources()
            print(f"Call successful, returned {len(jobs)} jobs")

            print("\n=== Assertions ===")
            if len(jobs) == 2:
                print("✅ Assertion passed: len(jobs) == 2")
            else:
                print(f"❌ Assertion failed: len(jobs) == 2, got {len(jobs)}")

            if any(job["id"] == "1" for job in jobs):
                print("✅ Assertion passed: Job with id '1' found")
            else:
                print("❌ Assertion failed: Job with id '1' not found")

            if any(job["id"] == "2" for job in jobs):
                print("✅ Assertion passed: Job with id '2' found")
            else:
                print("❌ Assertion failed: Job with id '2' not found")

            if mock_ingest_greenhouse.called:
                print(
                    f"✅ Assertion passed: mock_ingest_greenhouse called {mock_ingest_greenhouse.call_count} times"
                )
            else:
                print("❌ Assertion failed: mock_ingest_greenhouse not called")

            if mock_ingest_lever.called:
                print(
                    f"✅ Assertion passed: mock_ingest_lever called {mock_ingest_lever.call_count} times"
                )
            else:
                print("❌ Assertion failed: mock_ingest_lever not called")

            print("\n=== Call Details ===")
            if mock_ingest_greenhouse.called:
                print(
                    f"  mock_ingest_greenhouse.call_args: {mock_ingest_greenhouse.call_args}"
                )
            if mock_ingest_lever.called:
                print(f"  mock_ingest_lever.call_args: {mock_ingest_lever.call_args}")

        except Exception as e:
            print(f"\n❌ Error during test: {type(e).__name__}: {e}")
            import traceback

            print(traceback.format_exc())


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"❌ Error running test: {type(e).__name__}: {e}")
        import traceback

        print(traceback.format_exc())
