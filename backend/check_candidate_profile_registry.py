from db.database import Base
from db.models import CandidateProfile as ModelCandidateProfile

print("Base metadata:", Base.metadata)
print("Model CandidateProfile:", ModelCandidateProfile)

print("\nAll classes in registry:")
for name, cls in Base.registry._class_registry.items():
    print(f"{name}: {cls}")
