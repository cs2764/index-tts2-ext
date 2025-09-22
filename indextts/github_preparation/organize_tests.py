#!/usr/bin/env python3
"""
Script to organize test files for GitHub preparation.

This script identifies root-level test files, consolidates redundant tests,
and moves essential tests to the proper tests/ directory structure.
"""

import sys
from pathlib import Path
from .test_organizer import TestOrganizer


def main():
    """Execute test file organization."""
    print("Starting test file organization...")
    print("=" * 50)
    
    # Initialize organizer
    organizer = TestOrganizer(".")
    
    # Execute organization
    try:
        results = organizer.organize_test_files()
        
        # Generate and display report
        report = organizer.generate_organization_report(results)
        print(report)
        
        # Save report to file
        report_path = Path("test_organization_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nDetailed report saved to: {report_path}")
        
        # Summary
        print("\n" + "=" * 50)
        print("ORGANIZATION COMPLETE")
        print(f"Files moved: {len(results['moved_files'])}")
        print(f"Files removed: {len(results['removed_files'])}")
        print(f"Errors: {len(results['errors'])}")
        
        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error during organization: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())