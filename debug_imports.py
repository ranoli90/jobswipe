import sys
import os

# Add the backend directory to Python path
BACKEND_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, BACKEND_DIR)

# Test 1: Import from backend.db.models
print("=== Testing import from backend.db.models ===")
try:
    from backend.db.models import CandidateProfile
    print(f"Imported: {CandidateProfile}")
    print(f"Module: {CandidateProfile.__module__}")
    print(f"File: {CandidateProfile.__module__.__file__ if hasattr(CandidateProfile.__module__, '__file__') else getattr(sys.modules[CandidateProfile.__module__], '__file__', 'Unknown')}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Testing import from db.models ===")
try:
    from db.models import CandidateProfile as CandidateProfile2
    print(f"Imported: {CandidateProfile2}")
    print(f"Module: {CandidateProfile2.__module__}")
    print(f"File: {CandidateProfile2.__module__.__file__ if hasattr(CandidateProfile2.__module__, '__file__') else getattr(sys.modules[CandidateProfile2.__module__], '__file__', 'Unknown')}")
except Exception as e:
    print(f"Error: {e}")
