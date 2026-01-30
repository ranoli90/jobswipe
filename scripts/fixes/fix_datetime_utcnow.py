#!/usr/bin/env python3
"""
Automated script to fix datetime.utcnow() usage with timezone-aware alternatives.
"""

import re
import os
import sys
from pathlib import Path

def fix_datetime_utcnow_antipatterns(file_path):
    """Fix datetime.utcnow() usage in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match datetime.utcnow() calls
        pattern = r'(\bdatetime\.utcnow\s*\()\s*\)'
        
        # Replacement with timezone-aware alternative
        replacement = r'\1datetime.now(timezone.utc))'
        
        # Check if datetime and timezone are imported
        has_datetime_import = re.search(r'\bimport\s+datetime', content)
        has_timezone_import = re.search(r'\bfrom\s+datetime\s+import.*\btimezone\b', content)
        
        # Add imports if needed
        if has_datetime_import and not has_timezone_import:
            # Add timezone import after datetime import
            content = re.sub(r'(\bimport\s+datetime\s*)', r'\1\nfrom datetime import timezone', content)
        elif not has_datetime_import:
            # Add both imports at the top
            content = 'import datetime\nfrom datetime import timezone\n' + content
        
        # Replace all datetime.utcnow() calls
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files."""
    # Get all Python files in the backend directory
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print(f"Directory {backend_dir} does not exist")
        return
    
    python_files = []
    
    # Find all Python files
    for root, _, files in os.walk(backend_dir):
        # Skip venv directory
        if 'venv' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to process")
    
    modified_count = 0
    
    # Process each file
    for file_path in python_files:
        if fix_datetime_utcnow_antipatterns(file_path):
            modified_count += 1
            print(f"Modified: {file_path}")
    
    print(f"\nCompleted. Modified {modified_count} files.")
    print("\nNote: This script replaces datetime.utcnow() with datetime.now(timezone.utc).")
    print("Manual review is recommended to ensure the timezone handling is appropriate.")

if __name__ == "__main__":
    main()