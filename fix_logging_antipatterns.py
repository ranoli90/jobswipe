#!/usr/bin/env python3
"""
Script to fix logging f-string interpolation antipatterns.
Replaces f-string logging with lazy formatting using % or .format().
"""

import os
import re
import glob
from pathlib import Path

def fix_logging_fstrings(file_path):
    """Fix logging f-string interpolation in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return False

    original_content = content

    # Pattern to match logger.method(f"...{var}...")
    # This is complex because we need to handle nested braces and multiple variables
    pattern = r'(logger\.(info|error|warning|debug|critical))\(f(["\'])(.*?)\3\)'

    def replace_fstring(match):
        logger_call = match.group(1)
        quote_type = match.group(3)
        fstring_content = match.group(4)

        # If no variables in f-string, just remove the f prefix
        if '{' not in fstring_content:
            return f'{logger_call}({quote_type}{fstring_content}{quote_type})'

        # Convert f-string to % formatting
        # Simple case: single variable
        if fstring_content.count('{') == 1 and fstring_content.count('}') == 1:
            var_match = re.search(r'\{([^}]+)\}', fstring_content)
            if var_match:
                var_name = var_match.group(1)
                template = fstring_content.replace(f'{{{var_name}}}', '%s')
                return f'{logger_call}({quote_type}{template}{quote_type}, {var_name})'

        # Multiple variables - use % formatting with tuple
        variables = []
        template = fstring_content
        for match in re.finditer(r'\{([^}]+)\}', fstring_content):
            var_name = match.group(1)
            variables.append(var_name)
            template = template.replace(f'{{{var_name}}}', '%s', 1)

        if variables:
            if len(variables) == 1:
                return f'{logger_call}({quote_type}{template}{quote_type}, {variables[0]})'
            else:
                return f'{logger_call}({quote_type}{template}{quote_type}, {tuple(variables)})'

        # Fallback: just remove f prefix if we can't parse
        return f'{logger_call}({quote_type}{fstring_content}{quote_type})'

    # Apply the replacement
    content = re.sub(pattern, replace_fstring, content, flags=re.DOTALL)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix logging antipatterns in all Python files."""
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
        if fix_logging_fstrings(file_path):
            print(f"Fixed logging in: {file_path}")
            fixed_count += 1

    print(f"Fixed logging antipatterns in {fixed_count} files")

if __name__ == '__main__':
    main()