
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from unittest.mock import MagicMock
from services.application_service import run_application_task

async def debug():
    print("Debugging run_application_task")
    
    # Mock DB session
    mock_db_session = MagicMock()
    
    # Mock task
    mock_task = MagicMock()
    mock_task.id = "task-123"
    mock_task.user_id = "user-123"
    mock_task.job_id = "job-456"
    mock_task.status = "queued"
    mock_task.attempt_count = 0
    
    # Mock job
    mock_job = MagicMock()
    mock_job.source = "greenhouse"
    mock_job.apply_url = "https://greenhouse.example.com/apply"
    print(f"DEBUG: job.source = '{mock_job.source}'")
    print(f"DEBUG: type(job.source) = '{type(mock_job.source)}'")
    
    # Mock profile
    mock_profile = MagicMock()
    mock_profile.full_name = "John Doe"
    mock_profile.email = "john@example.com"
    mock_profile.phone = "123-456-7890"
    mock_profile.location = "San Francisco"
    mock_profile.resume_file_url = "https://storage.example.com/resume.pdf"
    
    # Setup mock returns
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_task, mock_job, mock_profile
    ]
    
    try:
        # Import and run the function
        result = await run_application_task("task-123", mock_db_session)
        print(f"DEBUG: Result = {result}")
        print(f"DEBUG: Task status = {mock_task.status}")
        if hasattr(mock_task, 'last_error'):
            print(f"DEBUG: Task error = {mock_task.last_error}")
            
    except Exception as e:
        print(f"DEBUG: Exception = {type(e).__name__}: {e}")
        import traceback
        print(f"DEBUG: Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug())
