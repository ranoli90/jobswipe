#!/usr/bin/env python3
"""
Script to fix singleton comparisons.
Replaces '== True' with 'is True' and '== False' with 'is False'.
"""

import os
import re

def fix_singleton_comparisons(file_path):
    """Fix singleton comparisons in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    original_content = content

    # Replace == True with is True
    content = re.sub(r'== True\b', 'is True', content)

    # Replace == False with is False
    content = re.sub(r'== False\b', 'is False', content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix singleton comparisons in all Python files."""
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
        if fix_singleton_comparisons(file_path):
            print(f"Fixed singleton comparisons in: {file_path}")
            fixed_count += 1

    print(f"Fixed singleton comparisons in {fixed_count} files")

if __name__ == '__main__':
    main()