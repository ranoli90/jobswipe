#!/usr/bin/env python3
"""Debug matching consistency"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import MagicMock
from backend.services.matching import calculate_job_score

def create_mock_job(title="Test Job", description="", company="Test Company"):
    job = MagicMock()
    job.title = title
    job.description = description
    job.company = company
    job.location = "San Francisco"
    return job

def create_mock_profile(skills=None, experience=None, education=None):
    profile = MagicMock()
    profile.full_name = "John Doe"
    profile.headline = "Software Engineer"
    profile.skills = skills or []
    profile.work_experience = experience or []
    profile.education = education or []
    profile.location = "San Francisco"
    return profile

async def test_consistency():
    print("=== Testing scoring consistency ===")

    job = create_mock_job(description="We need Python developers with experience in FastAPI")
    profile = create_mock_profile(skills=["Python", "FastAPI"])

    print("Job description:", job.description)
    print("Profile skills:", profile.skills)

    score1 = await calculate_job_score(job, profile)
    print(f"First score: {score1}")

    score2 = await calculate_job_score(job, profile)
    print(f"Second score: {score2}")

    diff = abs(score1 - score2)
    print(f"Difference: {diff}")

    if diff < 0.01:
        print("✅ Consistent")
    else:
        print("❌ Inconsistent")

async def test_correlation():
    print("\n=== Testing skill correlation ===")

    job_desc = "We need developers"
    skills = ["Python", "FastAPI", "React"]

    profile1 = create_mock_profile(skills=skills)
    profile2 = create_mock_profile(skills=[])

    job = create_mock_job(description=job_desc)

    score_with = await calculate_job_score(job, profile1)
    print(f"Score with skills: {score_with}")

    job_with_skills = create_mock_job(description=f"{job_desc} {' '.join(skills)}")
    score_overlap = await calculate_job_score(job_with_skills, profile1)
    print(f"Score with overlap: {score_overlap}")

    if score_overlap >= score_with:
        print("✅ Correlation holds")
    else:
        print("❌ Correlation fails")

if __name__ == "__main__":
    asyncio.run(test_consistency())
    asyncio.run(test_correlation())