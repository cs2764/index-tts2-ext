"""
Example usage of SafeFileManager for GitHub preparation.

This script demonstrates how to use the SafeFileManager class
to safely clean up and organize project files for GitHub upload.
"""

import sys
from pathlib import Path

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.file_classifier import FileClassifier
from indextts.github_preparation.safe_file_manager import SafeFileManager


def main():
    """Demonstrate SafeFileManager usage."""
    
    # Initialize with project root (use dry run for safety)
    project_root = Path(__file__).parent.parent.parent
    manager = SafeFileManager(str(project_root), dry_run=True)
    
    print("=== GitHub Preparation - Safe File Management Demo ===")
    print(f"Project root: {project_root}")
    print(f"Dry run mode: {manager.dry_run}")
    print()
    
    # Step 1: Scan and classify all files
    print("Step 1: Scanning and classifying project files...")
    file_infos = manager.classifier.scan_project()
    print(f"Found {len(file_infos)} files to analyze")
    print()
    
    # Step 2: Generate classification report
    print("Step 2: Generating classification report...")
    report = manager.classifier.generate_cleanup_report(file_infos)
    print("Classification report generated (first 20 lines):")
    print("\n".join(report.split("\n")[:20]))
    print("...")
    print()
    
    # Step 3: Plan operations
    print("Step 3: Planning file operations...")
    operations = manager.plan_operations(file_infos)
    print(f"Planned {len(operations)} operations")
    
    # Show operation summary
    by_action = {}
    for op in operations:
        action = op.action.value
        if action not in by_action:
            by_action[action] = 0
        by_action[action] += 1
    
    for action, count in by_action.items():
        print(f"  - {action.replace('_', ' ').title()}: {count} files")
    print()
    
    # Step 4: Execute operations (dry run)
    print("Step 4: Executing operations (dry run)...")
    stats = manager.execute_operations()
    print(f"Execution stats: {stats}")
    print()
    
    # Step 5: Organize test files specifically
    print("Step 5: Organizing test files...")
    test_stats = manager.organize_test_files()
    print(f"Test organization stats: {test_stats}")
    print()
    
    # Step 6: Clean up temporary files
    print("Step 6: Cleaning up temporary files...")
    cleanup_stats = manager.cleanup_temporary_files()
    print(f"Cleanup stats: {cleanup_stats}")
    print()
    
    # Step 7: Identify user content to preserve
    print("Step 7: Identifying user content to preserve...")
    user_files = manager.preserve_user_content()
    print(f"Found {len(user_files)} user files to preserve locally")
    if user_files:
        print("Examples:")
        for file_path in user_files[:5]:  # Show first 5
            print(f"  - {file_path}")
        if len(user_files) > 5:
            print(f"  ... and {len(user_files) - 5} more")
    print()
    
    # Step 8: Generate operation report
    print("Step 8: Generating operation report...")
    operation_report = manager.generate_operation_report()
    print("Operation report generated:")
    print(operation_report)
    
    print("=== Demo completed successfully ===")
    print()
    print("To run with actual file operations (not dry run):")
    print("1. Change dry_run=False in SafeFileManager initialization")
    print("2. Ensure you have backups of important files")
    print("3. Install send2trash library: pip install send2trash")
    print("4. Run the script again")


if __name__ == "__main__":
    main()