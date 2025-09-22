#!/usr/bin/env python3
"""
Script to restore accidentally deleted test files from recycle bin.
This is a manual recovery script for the test organization process.
"""

import os
import sys
from pathlib import Path


def main():
    """Restore test files from recycle bin if possible."""
    print("Test file restoration script")
    print("=" * 40)
    
    # Check if .deleted directory exists
    deleted_dir = Path('.deleted')
    if deleted_dir.exists():
        print(f"Found .deleted directory with {len(list(deleted_dir.glob('*.py')))} files")
        
        # Restore files from .deleted directory
        for file_path in deleted_dir.glob('*.py'):
            if file_path.name.startswith('test_') or 'test' in file_path.name:
                target_path = Path('.') / file_path.name
                if not target_path.exists():
                    try:
                        file_path.rename(target_path)
                        print(f"Restored: {file_path.name}")
                    except Exception as e:
                        print(f"Failed to restore {file_path.name}: {e}")
                else:
                    print(f"Target already exists, skipping: {file_path.name}")
    else:
        print("No .deleted directory found.")
        print("Files were likely sent to system recycle bin.")
        print("Please manually restore the following files from your recycle bin:")
        
        # List of files that should be restored
        important_tests = [
            'test_regression_comprehensive.py',
            'test_auto_save_components.py',
            'test_webui_integration.py',
            'test_file_classifier.py',
            'test_safe_file_manager.py',
            'test_test_organizer.py'
        ]
        
        for test_file in important_tests:
            print(f"  - {test_file}")
    
    print("\nRecommendation: Run a more conservative test organization next time.")


if __name__ == "__main__":
    main()