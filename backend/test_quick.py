#!/usr/bin/env python3
"""Quick test script to verify the implementation"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
from services.openai_service import OpenAIService


async def test_basic_functionality():
    """Test basic functionality"""
    print("Testing OpenAI service...")
    
    # Test API availability detection
    with patch('services.openai_service.OPENAI_API_KEY', 'test-key'):
        assert OpenAIService.is_available() == True
        print("✅ API availability check: PASSED")
        
    with patch('services.openai_service.OPENAI_API_KEY', None):
        assert OpenAIService.is_available() == False
        print("✅ API unavailability check: PASSED")
        
    # Test profile conversion
    profile = {
        "full_name": "John Doe",
        "headline": "Senior Software Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "work_experience": [
            {"position": "Software Engineer", "company": "Tech Corp"},
            {"position": "Junior Developer", "company": "StartUp Inc"}
        ],
        "education": [
            {"degree": "B.S. Computer Science", "school": "University of Example"}
        ]
    }
    
    text = OpenAIService._profile_to_text(profile)
    
    assert "John Doe" in text
    assert "Senior Software Engineer" in text
    assert "Python" in text
    assert "Software Engineer" in text
    assert "University of Example" in text
    print("✅ Profile conversion: PASSED")
    
    # Test fallback behavior
    with patch('services.openai_service.OPENAI_API_KEY', None):
        embedding = await OpenAIService.generate_job_embedding("Test job description")
        assert embedding == []
        print("✅ Job embedding fallback: PASSED")
        
        profile_embedding = await OpenAIService.generate_profile_embedding(profile)
        assert profile_embedding == []
        print("✅ Profile embedding fallback: PASSED")
        
        match_result = await OpenAIService.analyze_job_match(profile, "Test job")
        assert "score" in match_result
        assert 0.0 <= match_result["score"] <= 1.0
        print("✅ Match analysis fallback: PASSED")
        
    print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
