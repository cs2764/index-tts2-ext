#!/usr/bin/env python3
"""
Script to clean up duplicate test files that exist in both root and tests/ directory.
"""

import os
from pathlib import Path

try:
    from send2trash import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False
    send2trash = None


def cleanup_duplicate_tests():
    """Remove root-level test files that already exist in tests/ directory."""
    project_root = Path('.')
    tests_dir = project_root / 'tests'
    
    if not tests_dir.exists():
        print("No tests/ directory found")
        return
    
    # Get list of test files in tests/ directory
    tests_files = set(f.name for f in tests_dir.glob('test_*.py'))
    
    # Find root-level test files that have duplicates in tests/
    root_test_files = list(project_root.glob('test_*.py'))
    duplicates = [f for f in root_test_files if f.name in tests_files]
    
    print(f"Found {len(duplicates)} duplicate test files in root directory:")
    
    removed_count = 0
    for duplicate in duplicates:
        print(f"  - {duplicate.name}")
        
        # Verify the file in tests/ directory exists and has content
        tests_version = tests_dir / duplicate.name
        if tests_version.exists() and tests_version.stat().st_size > 0:
            try:
                if SEND2TRASH_AVAILABLE:
                    send2trash(str(duplicate))
                    print(f"    Moved to recycle bin: {duplicate.name}")
                else:
                    # Move to .deleted directory
                    deleted_dir = project_root / '.deleted'
                    deleted_dir.mkdir(exist_ok=True)
                    duplicate.rename(deleted_dir / duplicate.name)
                    print(f"    Moved to .deleted/: {duplicate.name}")
                
                removed_count += 1
            except Exception as e:
                print(f"    Error removing {duplicate.name}: {e}")
        else:
            print(f"    Skipping {duplicate.name} - tests/ version is empty or missing")
    
    print(f"\nRemoved {removed_count} duplicate test files from root directory")
    return removed_count


def main():
    """Execute duplicate cleanup."""
    print("Cleaning up duplicate test files...")
    print("=" * 40)
    
    removed_count = cleanup_duplicate_tests()
    
    if removed_count > 0:
        print(f"\nSuccessfully cleaned up {removed_count} duplicate test files")
        print("All test files are now properly organized in the tests/ directory")
    else:
        print("\nNo duplicate test files found to clean up")
    
    return 0


if __name__ == "__main__":
    exit(main())