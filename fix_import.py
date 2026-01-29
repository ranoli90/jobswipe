
with open('/home/brooketogo98/jobswipe/backend/services/matching.py', 'r') as f:
    content = f.read()

# Replace the specific import
fixed_content = content.replace('from db.database import get_db', 'from backend.db.database import get_db')

with open('/home/brooketogo98/jobswipe/backend/services/matching.py', 'w') as f:
    f.write(fixed_content)

print("Import fixed!")
