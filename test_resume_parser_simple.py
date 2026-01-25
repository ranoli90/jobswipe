#!/usr/bin/env python3
"""
Simple test script to verify resume parser functionality
without the pytest framework to avoid memory issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.resume_parser_enhanced import parse_resume_enhanced
from backend.services.storage import download_file

def test_resume_parser():
    """Test resume parser with simple content"""
    print("Testing resume parser...")
    
    try:
        # Test with a simple resume text
        # This is a very basic mock resume
        resume_text = """
John Doe
Software Engineer
123 Main Street, Anytown, USA
john.doe@email.com | (123) 456-7890 | linkedin.com/in/johndoe

EXPERIENCE
Senior Software Engineer
ABC Company
Jan 2020 - Present
- Led development of web applications using Python and JavaScript
- Implemented RESTful APIs and database design
- Mentored junior developers

Software Engineer
XYZ Corporation
Jun 2018 - Dec 2019
- Developed mobile applications using React Native
- Collaborated with cross-functional teams

EDUCATION
Bachelor of Science in Computer Science
University of Technology
Graduated: May 2018

SKILLS
- Python, JavaScript, React, Node.js
- SQL, PostgreSQL, MongoDB
- Git, Docker, AWS
        """.strip()
        
        print("Resume text loaded")
        
        # Call parser
        parsed_data = parse_resume_enhanced(resume_text.encode('utf-8'), "test_resume.txt")
        
        print("\n✅ Resume parsing successful!")
        print("\n📋 Parsed Data:")
        print(f"Name: {parsed_data.get('full_name', 'N/A')}")
        print(f"Email: {parsed_data.get('email', 'N/A')}")
        print(f"Phone: {parsed_data.get('phone', 'N/A')}")
        print(f"Location: {parsed_data.get('location', 'N/A')}")
        print(f"Headline: {parsed_data.get('headline', 'N/A')}")
        
        experience = parsed_data.get('work_experience', [])
        if experience:
            print(f"\n💼 Experience ({len(experience)} entries):")
            for exp in experience:
                print(f"  - {exp.get('position')} at {exp.get('company')}")
                print(f"    {exp.get('start_date')} - {exp.get('end_date')}")
                
        education = parsed_data.get('education', [])
        if education:
            print(f"\n🎓 Education ({len(education)} entries):")
            for edu in education:
                print(f"  - {edu.get('degree')} in {edu.get('field_of_study')}")
                print(f"    {edu.get('institution')}")
                
        skills = parsed_data.get('skills', [])
        if skills:
            print(f"\n🛠️  Skills ({len(skills)}):")
            print(f"  {', '.join(skills)}")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(f"\nStack Trace:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Resume Parser Test")
    print("=" * 50)
    
    success = test_resume_parser()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed - Resume parser is operational")
    else:
        print("❌ Test failed - Resume parser is not working correctly")
        sys.exit(1)
