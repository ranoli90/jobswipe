#!/usr/bin/env python3
"""
Automated script to remove unnecessary else statements after return.
"""

import re
import os
import sys
from pathlib import Path

def fix_else_return_antipatterns(file_path):
    """Fix unnecessary else statements after return in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match else statements after return
        # This pattern looks for:
        # return something
        # else:
        #     more code
        pattern = r'(\n\s*return\s+.*?\n\s*else:\s*\n)(\s+.*?)(?=\n\s*(?:def|class|if|elif|else|for|while|try|except|finally|with|return|#|$))'
        
        def remove_unnecessary_else(match):
            """Remove the else statement and de-indent the code."""
            before_else = match.group(1)
            else_content = match.group(2)
            
            # Remove the else: line and de-indent the content
            lines = else_content.split('\n')
            deindented_lines = []
            
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Remove one level of indentation (assuming 4 spaces)
                    if line.startswith('    '):
                        deindented_lines.append(line[4:])
                    elif line.startswith('  '):
                        deindented_lines.append(line[2:])
                    else:
                        deindented_lines.append(line)
                else:
                    deindented_lines.append(line)
            
            return before_else.replace('else:', '') + '\n' + '\n'.join(deindented_lines)
        
        # Replace all occurrences
        new_content = re.sub(pattern, remove_unnecessary_else, content, flags=re.DOTALL)
        
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
        if fix_else_return_antipatterns(file_path):
            modified_count += 1
            print(f"Modified: {file_path}")
    
    print(f"\nCompleted. Modified {modified_count} files.")
    print("\nNote: This script removes unnecessary else statements after return.")
    print("Manual review is recommended to ensure the logic remains correct.")

if __name__ == "__main__":
    main()