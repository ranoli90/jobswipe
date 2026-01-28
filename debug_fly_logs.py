#!/usr/bin/env python3
"""
Debug Fly.io Logs Parser and Analyzer
Parses fly.io JSON logs and categorizes errors for systematic debugging
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple


def parse_fly_logs(filepath: str) -> List[Dict]:
    """Parse fly.io JSON logs file."""
    logs = []
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fly logs are JSON objects separated by newlines
    # But they might be pretty-printed, so we need to handle that
    depth = 0
    current_obj = ""
    
    for char in content:
        if char == '{':
            if depth == 0:
                current_obj = ""
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                current_obj += char
                try:
                    log = json.loads(current_obj)
                    logs.append(log)
                except json.JSONDecodeError:
                    pass
                current_obj = ""
                continue
        
        if depth > 0:
            current_obj += char
    
    return logs


def categorize_errors(logs: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize errors by type."""
    categories = defaultdict(list)
    
    error_patterns = {
        'pydantic_validation': r'ValidationError|Field required|missing',
        'database': r'database|postgres|sqlite|sqlalchemy|connection|pool',
        'redis': r'redis|cache',
        'memory': r'memory|oom|out of memory|killed',
        'import': r'ImportError|ModuleNotFoundError|No module named',
        'syntax': r'SyntaxError|IndentationError',
        'runtime': r'RuntimeError|Exception|Traceback',
        'config': r'config|setting|environment variable',
        'health_check': r'health|/health',
        'worker': r'celery|worker',
    }
    
    for log in logs:
        msg = log.get('message', '')
        categorized = False
        
        for category, pattern in error_patterns.items():
            if re.search(pattern, msg, re.IGNORECASE):
                categories[category].append(log)
                categorized = True
                break
        
        if not categorized and any(x in msg.lower() for x in ['error', 'failed', 'fatal', 'crash']):
            categories['other_errors'].append(log)
    
    return dict(categories)


def extract_missing_env_vars(logs: List[Dict]) -> Set[str]:
    """Extract missing environment variable names from validation errors."""
    missing = set()
    
    for log in logs:
        msg = log.get('message', '')
        # Look for field names that are mentioned as missing
        if 'Field required' in msg or 'missing' in msg:
            # Try to extract field name from various message formats
            patterns = [
                r'(\w+_api_key)',
                r'(\w+_password)',
                r'(\w+_secret)',
                r'(\w+_url)',
                r'(DATABASE_URL)',
                r'(SECRET_KEY)',
                r'(VAULT_\w+)',
                r'(OAUTH_\w+)',
                r'(ENCRYPTION_\w+)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, msg)
                missing.update(matches)
    
    return missing


def analyze_restart_patterns(logs: List[Dict]) -> Dict:
    """Analyze machine restart patterns."""
    restarts = []
    
    for i, log in enumerate(logs):
        msg = log.get('message', '')
        if 'restarting' in msg.lower() or 'restart count' in msg.lower() or 'exited' in msg.lower():
            restarts.append({
                'timestamp': log.get('timestamp'),
                'instance': log.get('instance'),
                'message': msg,
                'index': i
            })
    
    return {
        'total_restarts': len(restarts),
        'restart_events': restarts
    }


def print_summary(logs: List[Dict], categories: Dict, missing_vars: Set, restart_info: Dict):
    """Print a comprehensive summary."""
    print("=" * 80)
    print("FLY.IO LOGS ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nTotal log entries: {len(logs)}")
    print(f"Unique instances: {len(set(l.get('instance') for l in logs))}")
    
    print("\n" + "-" * 80)
    print("ERROR CATEGORIES")
    print("-" * 80)
    for category, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n{category.upper()}: {len(items)} entries")
        # Show first 3 unique messages
        seen = set()
        for log in items[:10]:
            msg = log.get('message', '')
            if msg not in seen and len(seen) < 3:
                seen.add(msg)
                print(f"  - {msg[:120]}...")
    
    if missing_vars:
        print("\n" + "-" * 80)
        print("MISSING ENVIRONMENT VARIABLES (from validation errors)")
        print("-" * 80)
        for var in sorted(missing_vars):
            print(f"  - {var}")
    
    print("\n" + "-" * 80)
    print("RESTART ANALYSIS")
    print("-" * 80)
    print(f"Total restart events: {restart_info['total_restarts']}")
    for event in restart_info['restart_events'][-5:]:  # Show last 5
        print(f"  [{event['timestamp']}] {event['instance']}: {event['message'][:100]}")
    
    print("\n" + "=" * 80)
    print("CRITICAL FINDINGS")
    print("=" * 80)
    
    # Identify root cause
    if 'pydantic_validation' in categories:
        print("\n🔴 CRITICAL: Pydantic validation errors detected")
        print("   Root cause: Missing required environment variables")
        print("   Impact: Application cannot start")
        print("   Action: Set all required environment variables in fly.io secrets")
    
    if restart_info['total_restarts'] > 5:
        print(f"\n🟠 WARNING: High restart count ({restart_info['total_restarts']})")
        print("   This indicates the app is crashing in a loop")
    
    print("\n" + "=" * 80)


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_fly_logs.py <path_to_logs.json>")
        print("Or: ./flyctl logs --app jobswipe-9obhra -n --json > fly_logs.json")
        sys.exit(1)
    
    filepath = sys.argv[1]
    print(f"Parsing logs from: {filepath}")
    
    logs = parse_fly_logs(filepath)
    print(f"Parsed {len(logs)} log entries")
    
    categories = categorize_errors(logs)
    missing_vars = extract_missing_env_vars(logs)
    restart_info = analyze_restart_patterns(logs)
    
    print_summary(logs, categories, missing_vars, restart_info)
    
    # Save detailed analysis
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'total_logs': len(logs),
        'categories': {k: len(v) for k, v in categories.items()},
        'missing_env_vars': list(missing_vars),
        'restart_info': restart_info,
    }
    
    with open('fly_logs_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print("\nDetailed analysis saved to: fly_logs_analysis.json")


if __name__ == '__main__':
    main()
