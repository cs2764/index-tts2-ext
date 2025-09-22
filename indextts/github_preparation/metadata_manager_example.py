#!/usr/bin/env python3
"""
Example usage of MetadataManager for GitHub preparation.

This script demonstrates how to validate and update project metadata
in pyproject.toml for GitHub repository preparation.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.metadata_manager import MetadataManager


def main():
    """Demonstrate metadata management workflow."""
    print("IndexTTS2 Project Metadata Management")
    print("=" * 50)
    
    # Initialize metadata manager
    manager = MetadataManager(project_root)
    
    try:
        # Load current metadata
        print("\n1. Loading current metadata...")
        metadata = manager.load_current_metadata()
        print(f"   Project: {metadata.name} v{metadata.version}")
        print(f"   Description: {metadata.description[:100]}...")
        
        # Validate current metadata
        print("\n2. Validating current metadata...")
        issues = manager.validate_metadata()
        if issues:
            print("   Validation issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("   No validation issues found.")
            
        # Perform complete validation and update
        print("\n3. Applying metadata updates...")
        results = manager.validate_and_update()
        
        if results['success']:
            print("   ✓ Metadata update completed successfully!")
            
            if results['updates_applied']:
                print("   Updates applied:")
                for update in results['updates_applied']:
                    print(f"   - {update}")
            else:
                print("   No updates were necessary.")
                
            if results['validation_issues']:
                print("   Validation issues (resolved by updates):")
                for issue in results['validation_issues']:
                    print(f"   - {issue}")
                    
        else:
            print("   ✗ Metadata update failed!")
            if 'error' in results:
                print(f"   Error: {results['error']}")
                
        # Display final metadata summary
        print("\n4. Final metadata summary:")
        final_metadata = manager.load_current_metadata()
        print(f"   Name: {final_metadata.name}")
        print(f"   Version: {final_metadata.version}")
        print(f"   Description: {final_metadata.description[:150]}...")
        print(f"   URLs: {list(final_metadata.urls.keys())}")
        print(f"   Entry points: {list(final_metadata.scripts.keys())}")
        print(f"   Dependencies: {len(final_metadata.dependencies)} main, "
              f"{sum(len(deps) for deps in final_metadata.optional_dependencies.values())} optional")
        
    except Exception as e:
        print(f"Error during metadata management: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())