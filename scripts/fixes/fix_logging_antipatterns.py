#!/usr/bin/env python3
"""
Automated script to fix logging f-string interpolation antipatterns.
Replaces f-string logging with lazy % formatting for better performance.
"""

import re
import os
import sys
from pathlib import Path

def fix_logging_antipatterns(file_path):
    """Fix logging f-string interpolation in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match logging calls with f-strings
        # Matches: logger.debug(f"message {var}")
        # Also matches: logging.info(f"message {var}")
        pattern = r'(\b(?:logger|logging)\.(?:debug|info|warning|error|critical|exception)\s*\()\s*f["\'](.*?)["\']'
        
        def replace_fstring(match):
            """Replace f-string with % formatting."""
            logger_call = match.group(1)
            fstring_content = match.group(2)
            
            # Simple replacement - convert f"text {var}" to "text %s" % var
            # This is a basic conversion and may need manual review
            if '{' in fstring_content and '}' in fstring_content:
                # Extract variables from f-string
                variables = []
                simplified_content = fstring_content
                
                # Replace {var} with %s and collect variables
                while True:
                    start = simplified_content.find('{')
                    if start == -1:
                        break
                    end = simplified_content.find('}', start)
                    if end == -1:
                        break
                    
                    var_name = simplified_content[start+1:end].strip()
                    variables.append(var_name)
                    simplified_content = simplified_content[:start] + '%s' + simplified_content[end+1:]
                
                if variables:
                    return f"{logger_call}\"{simplified_content}\" % ({', '.join(variables)})"
                else:
                    # No variables found, remove f prefix
                    return f"{logger_call}\"{fstring_content}\""
            else:
                # No variables, just remove f prefix
                return f"{logger_call}\"{fstring_content}\""
        
        # Replace all occurrences
        new_content = re.sub(pattern, replace_fstring, content, flags=re.DOTALL)
        
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
        if fix_logging_antipatterns(file_path):
            modified_count += 1
            print(f"Modified: {file_path}")
    
    print(f"\nCompleted. Modified {modified_count} files.")
    
    if modified_count > 0:
        print("\nNote: This script performs basic f-string to % formatting conversion.")
        print("Some complex f-strings may require manual review and adjustment.")

if __name__ == "__main__":
    main()