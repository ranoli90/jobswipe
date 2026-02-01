"""
Text Processing Utilities
Provides shared text processing functions for the JobSwipe application.
"""

from typing import Dict


def profile_to_text(profile: Dict) -> str:
    """Convert profile dictionary to text for embedding"""
    parts = []

    if profile.get("full_name"):
        parts.append(f"Name: {profile['full_name']}")

    if profile.get("headline"):
        parts.append(f"Headline: {profile['headline']}")

    if profile.get("skills"):
        skills_text = ", ".join(profile["skills"])
        parts.append(f"Skills: {skills_text}")

    if profile.get("work_experience"):
        experience_text = [
            f"{exp['position']} at {exp['company']}"
            for exp in profile["work_experience"]
            if exp.get("position") and exp.get("company")
        ]
        if experience_text:
            parts.append(f"Experience: {', '.join(experience_text)}")

    if profile.get("education"):
        education_text = [
            f"{edu['degree']} from {edu['school']}"
            for edu in profile["education"]
            if edu.get("degree") and edu.get("school")
        ]
        if education_text:
            parts.append(f"Education: {', '.join(education_text)}")

    return "\n".join(parts)
