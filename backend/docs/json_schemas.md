# JSON Field Schemas for Candidate Profile

This document defines the expected JSON schema for the `candidate_profiles` table's JSON fields.

## Overview

The `candidate_profiles` table contains three JSON fields:
- `work_experience`: Array of work experience objects
- `education`: Array of education objects
- `skills`: Array of skill objects or strings

## JSON Schemas

### Work Experience Schema

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["company", "position"],
    "properties": {
      "company": {
        "type": "string",
        "description": "Name of the company"
      },
      "position": {
        "type": "string", 
        "description": "Job title or position"
      },
      "location": {
        "type": "string",
        "description": "Location of the job (city, state, country)"
      },
      "start_date": {
        "type": "string",
        "format": "date",
        "description": "Start date in YYYY-MM format"
      },
      "end_date": {
        "type": "string",
        "format": "date",
        "description": "End date in YYYY-MM format, or 'present' for current position"
      },
      "description": {
        "type": "string",
        "description": "Job description or responsibilities"
      },
      "achievements": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of key achievements"
      },
      "technologies": {
        "type": "array", 
        "items": {"type": "string"},
        "description": "Technologies used at this job"
      }
    }
  }
}
```

**Example:**
```json
[
  {
    "company": "Acme Corporation",
    "position": "Senior Software Engineer",
    "location": "San Francisco, CA",
    "start_date": "2021-03",
    "end_date": "present",
    "description": "Led development of microservices architecture",
    "achievements": [
      "Improved system performance by 40%",
      "Mentored 5 junior developers"
    ],
    "technologies": ["Python", "AWS", "Kubernetes", "PostgreSQL"]
  }
]
```

### Education Schema

```json
{
  "type": "array", 
  "items": {
    "type": "object",
    "required": ["school"],
    "properties": {
      "school": {
        "type": "string",
        "description": "Name of the educational institution"
      },
      "degree": {
        "type": "string",
        "description": "Degree obtained (e.g., 'Bachelor of Science', 'Master of Engineering')"
      },
      "field": {
        "type": "string", 
        "description": "Field of study (e.g., 'Computer Science', 'Software Engineering')"
      },
      "location": {
        "type": "string",
        "description": "Location of the institution"
      },
      "start_date": {
        "type": "string",
        "format": "date",
        "description": "Start date in YYYY-MM format"
      },
      "end_date": {
        "type": "string",
        "format": "date", 
        "description": "End date in YYYY-MM format or 'expected' for ongoing"
      },
      "gpa": {
        "type": "number",
        "description": "Grade point average (optional)"
      },
      "relevant_coursework": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of relevant courses"
      },
      "honors": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Academic honors or awards"
      }
    }
  }
}
```

**Example:**
```json
[
  {
    "school": "Stanford University",
    "degree": "Master of Science",
    "field": "Computer Science",
    "location": "Stanford, CA",
    "start_date": "2019-09",
    "end_date": "2021-06",
    "gpa": 3.9,
    "relevant_coursework": [
      "Machine Learning",
      "Distributed Systems",
      "Algorithms"
    ],
    "honors": ["Dean's List", "Graduate Fellowship"]
  }
]
```

### Skills Schema

The `skills` field can be stored in two formats:

#### Format 1: Simple String Array (Legacy)
```json
{
  "type": "array",
  "items": {"type": "string"}
}
```

**Example:**
```json
["Python", "JavaScript", "React", "AWS", "Docker"]
```

#### Format 2: Structured Skills Array (Recommended)
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Skill name"
      },
      "category": {
        "type": "string",
        "enum": ["language", "framework", "library", "tool", "database", "cloud", "soft_skill"],
        "description": "Category of the skill"
      },
      "level": {
        "type": "string",
        "enum": ["beginner", "intermediate", "advanced", "expert"],
        "description": "Proficiency level"
      },
      "years_experience": {
        "type": "number",
        "description": "Years of experience with this skill"
      },
      "verified": {
        "type": "boolean",
        "description": "Whether the skill has been verified (e.g., through certifications)"
      }
    }
  }
}
```

**Example:**
```json
[
  {
    "name": "Python",
    "category": "language",
    "level": "expert",
    "years_experience": 8,
    "verified": true
  },
  {
    "name": "React",
    "category": "framework",
    "level": "advanced",
    "years_experience": 4,
    "verified": false
  }
]
```

## Validation Functions

### Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class WorkExperienceItem(BaseModel):
    company: str
    position: str
    location: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM format
    end_date: Optional[str] = None    # YYYY-MM or 'present'
    description: Optional[str] = None
    achievements: Optional[List[str]] = None
    technologies: Optional[List[str]] = None

class EducationItem(BaseModel):
    school: str
    degree: Optional[str] = None
    field: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    relevant_coursework: Optional[List[str]] = None
    honors: Optional[List[str]] = None

class SkillItem(BaseModel):
    name: str
    category: Optional[str] = None
    level: Optional[str] = None
    years_experience: Optional[float] = None
    verified: Optional[bool] = False

class CandidateProfileData(BaseModel):
    work_experience: Optional[List[WorkExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    skills: Optional[List] = None  # Can be List[str] or List[SkillItem]
```

## Migration Notes

When updating the schema, follow these steps:

1. **Create a new migration** using Alembic
2. **Update the Pydantic models** in the API validators
3. **Update the resume parser** to output the new format
4. **Add data migration** to convert existing data to the new format
5. **Update documentation** and examples

## Backward Compatibility

The system maintains backward compatibility by:
1. Accepting both legacy (string array) and new (object array) formats for skills
2. Converting legacy format to new format during profile updates
3. Providing default values for optional fields
4. Gracefully handling missing fields

## Future Enhancements

Potential improvements for future versions:
- Add schema versioning
- Implement JSON Schema validation at the database level
- Add indexes for common query patterns
- Consider separating into normalized tables for complex queries
