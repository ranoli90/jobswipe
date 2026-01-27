#!/usr/bin/env python3
"""
Script to fix datetime.utcnow() usage with timezone-aware alternatives.
Replaces datetime.utcnow() with datetime.now(timezone.utc)
"""

import os
import re
from pathlib import Path

def fix_datetime_utcnow(file_path):
    """Fix datetime.utcnow() usage in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    original_content = content

    # Replace datetime.utcnow() with datetime.now(timezone.utc)
    # But we need to make sure timezone is imported
    content = re.sub(r'\bdatetime\.utcnow\(\)', 'datetime.now(timezone.utc)', content)

    # Also handle the full path
    content = re.sub(r'\bdatetime\.datetime\.utcnow\(\)', 'datetime.now(timezone.utc)', content)

    # Check if we need to add timezone import
    if 'datetime.now(timezone.utc)' in content and 'from datetime import' not in content:
        # Look for existing datetime imports
        datetime_import_pattern = r'^(from datetime import.*|import datetime)'
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.match(datetime_import_pattern, line.strip()):
                # Add timezone to the import
                if 'timezone' not in line:
                    lines[i] = line.rstrip() + ', timezone'
                    content = '\n'.join(lines)
                break
        else:
            # No datetime import found, add one
            lines.insert(0, 'from datetime import datetime, timezone')
            content = '\n'.join(lines)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix datetime.utcnow() usage in all Python files."""
    # Find all Python files in backend directory (exclude venv)
    python_files = []
    for root, dirs, files in os.walk('backend'):
        # Skip venv directory
        if 'venv' in dirs:
            dirs.remove('venv')
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    fixed_count = 0
    for file_path in python_files:
        if fix_datetime_utcnow(file_path):
            print(f"Fixed datetime.utcnow in: {file_path}")
            fixed_count += 1

    print(f"Fixed datetime.utcnow usage in {fixed_count} files")

if __name__ == '__main__':
    main()