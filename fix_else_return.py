#!/usr/bin/env python3
"""
Script to fix unnecessary else statements after return.
Removes else blocks that follow return statements.
"""

import os
import re
from pathlib import Path

def fix_else_return(file_path):
    """Fix unnecessary else after return in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    original_content = content

    # Pattern to match:
    # if condition:
    #     return something
    # else:
    #     code...
    #
    # Should become:
    # if condition:
    #     return something
    # code...

    # This regex is complex because we need to handle indentation and nested structures
    # Look for return followed by else at the same indentation level
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line contains a return statement
        if re.search(r'\breturn\b', line):
            # Look ahead for an else at the same indentation level
            return_indent = len(line) - len(line.lstrip())
            j = i + 1

            # Skip blank lines and comments
            while j < len(lines) and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                j += 1

            if j < len(lines) and lines[j].strip().startswith('else:'):
                else_indent = len(lines[j]) - len(lines[j].lstrip())
                if else_indent == return_indent:
                    # Found unnecessary else after return
                    # Remove the else line and de-indent the following block
                    i = j + 1  # Skip the else line
                    # Find the end of the else block (next line with same or less indentation)
                    block_start = i
                    while i < len(lines):
                        current_indent = len(lines[i]) - len(lines[i].lstrip()) if lines[i].strip() else float('inf')
                        if current_indent <= return_indent and lines[i].strip():
                            break
                        # De-indent this line
                        if lines[i].strip():  # Only de-indent non-empty lines
                            # Remove one level of indentation (4 spaces)
                            if lines[i].startswith('    '):
                                lines[i] = lines[i][4:]
                        i += 1
                    # Add the lines up to the end of the else block
                    new_lines.extend(lines[block_start:i])
                    continue

        new_lines.append(line)
        i += 1

    new_content = '\n'.join(new_lines)

    if new_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Main function to fix else-return antipatterns in all Python files."""
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
        if fix_else_return(file_path):
            print(f"Fixed else-return in: {file_path}")
            fixed_count += 1

    print(f"Fixed else-return antipatterns in {fixed_count} files")

if __name__ == '__main__':
    main()