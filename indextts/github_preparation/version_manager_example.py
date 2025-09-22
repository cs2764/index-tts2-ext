"""
Example usage of the VersionManager class for GitHub preparation.

This script demonstrates how to use the VersionManager to:
1. Check current version
2. Increment version with date suffix
3. Update pyproject.toml with new metadata
4. Validate version consistency
5. Generate changelog entries
"""

from pathlib import Path
from indextts.github_preparation.version_manager import VersionManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Demonstrate VersionManager functionality."""
    
    # Initialize version manager for current project
    vm = VersionManager()
    
    print("=== IndexTTS2 Version Management Demo ===\n")
    
    # 1. Check current version
    try:
        current_version = vm.get_current_version()
        print(f"Current version: {current_version}")
    except Exception as e:
        print(f"Error getting current version: {e}")
        return
    
    # 2. Show what the next version would be
    try:
        next_patch = vm.increment_version('patch')
        next_minor = vm.increment_version('minor')
        next_major = vm.increment_version('major')
        
        print(f"Next patch version would be: {next_patch}")
        print(f"Next minor version would be: {next_minor}")
        print(f"Next major version would be: {next_major}")
    except Exception as e:
        print(f"Error calculating next versions: {e}")
    
    # 3. Validate current version consistency
    print("\n=== Version Consistency Check ===")
    issues = vm.validate_version_consistency()
    if issues:
        print("Version consistency issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ No version consistency issues found")
    
    # 4. Show current project metadata
    print("\n=== Current Project Metadata ===")
    try:
        metadata = vm.get_project_metadata()
        print(f"Name: {metadata.get('name', 'N/A')}")
        print(f"Version: {metadata.get('version', 'N/A')}")
        print(f"Description: {metadata.get('description', 'N/A')}")
        
        authors = metadata.get('authors', [])
        if authors:
            print("Authors:")
            for author in authors:
                if isinstance(author, dict):
                    print(f"  - {author.get('name', 'Unknown')}")
                else:
                    print(f"  - {author}")
        
        urls = metadata.get('urls', {})
        if urls:
            print("URLs:")
            for key, url in urls.items():
                print(f"  - {key}: {url}")
                
    except Exception as e:
        print(f"Error getting project metadata: {e}")
    
    # 5. Generate sample changelog entry
    print("\n=== Sample Changelog Entry ===")
    try:
        sample_changes = [
            "Prepared project for GitHub release",
            "Cleaned up development artifacts",
            "Updated documentation and metadata",
            "Organized test files and project structure"
        ]
        
        changelog_entry = vm.generate_changelog_entry(
            current_version, 
            sample_changes
        )
        print("Generated changelog entry:")
        print(changelog_entry)
        
    except Exception as e:
        print(f"Error generating changelog entry: {e}")
    
    print("\n=== Demo Complete ===")
    print("To actually update the version, use:")
    print("  vm.update_pyproject_toml()")
    print("  vm.update_changelog()")


if __name__ == '__main__':
    main()