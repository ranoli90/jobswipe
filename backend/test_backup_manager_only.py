#!/usr/bin/env python3
"""
Simple test script to verify backup manager functionality
without requiring the full JobSwipe application context.
"""

import sys
import os

# Add backup directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def test_load_config():
    """Test loading backup manager configuration"""
    try:
        from backup.backup_manager import load_config
        
        # Test default config
        config = load_config()
        assert config["backup"]["base_dir"] == "/var/backups/postgres"
        assert config["database"]["port"] == 5432
        assert config["encryption"]["enabled"] is True
        
        print("✓ Default configuration loaded successfully")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load config: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_run_command():
    """Test running shell commands"""
    try:
        from backup.backup_manager import run_command
        
        # Test simple command
