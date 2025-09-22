"""
Example usage of GitIgnoreManager

This script demonstrates how to use the GitIgnoreManager to update .gitignore
files with proper exclusion patterns for the IndexTTS2 project.
"""

import logging
from pathlib import Path
from indextts.github_preparation.gitignore_manager import GitIgnoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Demonstrate GitIgnoreManager functionality."""
    print("🔧 GitIgnore Manager Example")
    print("=" * 50)
    
    # Initialize manager
    manager = GitIgnoreManager(".")
    
    # Get status report
    print("\n📊 Current Status:")
    status = manager.get_status_report()
    print(f"  .gitignore exists: {status['gitignore_exists']}")
    print(f"  Required patterns: {status['total_required_patterns']}")
    print(f"  Current patterns: {status['current_patterns_count']}")
    print(f"  Missing patterns: {status['missing_patterns_count']}")
    print(f"  Is complete: {status['is_complete']}")
    
    # Show missing patterns
    if status['missing_patterns']:
        print(f"\n⚠️  Missing Patterns ({len(status['missing_patterns'])}):")
        for pattern in status['missing_patterns'][:10]:  # Show first 10
            print(f"  - {pattern}")
        if len(status['missing_patterns']) > 10:
            print(f"  ... and {len(status['missing_patterns']) - 10} more")
    
    # Validate current gitignore
    print("\n🔍 Validation:")
    is_valid = manager.validate_gitignore()
    
    if not is_valid:
        # Show what would be changed (dry run)
        print("\n🧪 Dry Run Preview:")
        manager.update_gitignore(dry_run=True)
        
        # Ask user if they want to proceed
        print("\n❓ Would you like to update .gitignore? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                print("\n🔄 Updating .gitignore...")
                success = manager.update_gitignore()
                if success:
                    print("✅ .gitignore updated successfully!")
                    
                    # Show final status
                    final_status = manager.get_status_report()
                    print(f"📈 Final status: {final_status['missing_patterns_count']} missing patterns")
                else:
                    print("❌ Failed to update .gitignore")
            else:
                print("⏭️  Skipping update")
        except KeyboardInterrupt:
            print("\n⏭️  Skipping update")
    else:
        print("✅ .gitignore is already properly configured!")
    
    # Show some example patterns by category
    print("\n📋 Example Required Patterns by Category:")
    patterns = manager.get_required_patterns()
    
    categories = {
        "User Content": [p for p in patterns if any(x in p for x in ['/outputs/', '/prompts/', '/logs/'])],
        "Python Cache": [p for p in patterns if any(x in p for x in ['__pycache__', '*.py', '.mypy_cache'])],
        "Model Files": [p for p in patterns if '/checkpoints/' in p or '/cache/' in p],
        "Temp Files": [p for p in patterns if any(x in p for x in ['*.tmp', 'debug_', '*.bak'])]
    }
    
    for category, cat_patterns in categories.items():
        if cat_patterns:
            print(f"\n  {category}:")
            for pattern in sorted(cat_patterns)[:3]:  # Show first 3
                print(f"    - {pattern}")
            if len(cat_patterns) > 3:
                print(f"    ... and {len(cat_patterns) - 3} more")


if __name__ == "__main__":
    main()