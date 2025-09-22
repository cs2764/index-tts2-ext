#!/usr/bin/env python3
"""
Example usage of the GitHubPreparation workflow.

This script demonstrates how to use the comprehensive GitHub preparation workflow
for the IndexTTS2 project, including safety checks, progress reporting, and
rollback capabilities.
"""

import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation import GitHubPreparation


def progress_callback(step_name: str, progress: float, message: str):
    """Progress callback function for reporting workflow progress."""
    print(f"[{step_name}] {progress:5.1f}% - {message}")


def main():
    """Main function demonstrating GitHub preparation workflow."""
    parser = argparse.ArgumentParser(description="GitHub Preparation Workflow for IndexTTS2")
    parser.add_argument("--project-root", default=".", help="Path to project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Simulate operations without executing them")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--skip-confirmation", action="store_true", help="Skip safety confirmation prompts")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze project, don't execute cleanup")
    parser.add_argument("--rollback", action="store_true", help="Attempt to rollback previous changes")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("IndexTTS2 GitHub Preparation Workflow")
    print("=" * 60)
    print()
    
    # Initialize the GitHub preparation workflow
    github_prep = GitHubPreparation(
        project_root=args.project_root,
        dry_run=args.dry_run,
        backup_enabled=not args.no_backup
    )
    
    # Set progress callback
    github_prep.set_progress_callback(progress_callback)
    
    try:
        if args.rollback:
            print("🔄 Attempting to rollback previous changes...")
            rollback_results = github_prep.rollback_changes()
            
            if rollback_results['success']:
                print("✅ Rollback completed successfully")
                print(f"File operations rolled back: {rollback_results['file_operations']}")
                if rollback_results.get('limitations'):
                    print("\n⚠️  Rollback limitations:")
                    for limitation in rollback_results['limitations']:
                        print(f"   - {limitation}")
            else:
                print(f"❌ Rollback failed: {rollback_results.get('error', 'Unknown error')}")
            
            return
        
        # Step 1: Validate project structure
        print("🔍 Validating project structure...")
        is_valid, issues = github_prep.validate_project_structure()
        
        if not is_valid:
            print("❌ Project validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            print("\nPlease fix these issues before proceeding.")
            return 1
        
        print("✅ Project structure validation passed")
        print()
        
        # Step 2: Analyze project
        print("📊 Analyzing project structure...")
        analysis_results = github_prep.analyze_project()
        
        print(f"📈 Analysis Results:")
        print(f"   - Total files: {analysis_results['total_files']}")
        print(f"   - Planned operations: {analysis_results['planned_operations']}")
        print()
        
        # Display files by action
        print("📋 Files by Action:")
        for action, count in analysis_results['files_by_action'].items():
            if count > 0:
                print(f"   - {action.replace('_', ' ').title()}: {count} files")
        print()
        
        # Display safety report
        safety_report = analysis_results['safety_report']
        if safety_report['is_safe']:
            print("✅ Safety validation passed")
        else:
            print("⚠️  Safety validation warnings:")
            for warning in safety_report.get('warnings', []):
                print(f"   - {warning}")
            for error in safety_report.get('errors', []):
                print(f"   - ❌ {error}")
        print()
        
        # If analyze-only mode, stop here
        if args.analyze_only:
            print("📄 Analysis complete. Use --analyze-only=false to execute cleanup.")
            
            # Save analysis report
            report_file = Path(args.project_root) / "github_preparation_analysis.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(analysis_results['classification_report'])
            print(f"📄 Analysis report saved to: {report_file}")
            
            return 0
        
        # Step 3: Safety confirmation
        if not args.skip_confirmation and not args.dry_run:
            if not safety_report['is_safe']:
                print("❌ Cannot proceed due to safety validation errors.")
                return 1
            
            print("⚠️  This will modify your project files. Continue? (y/N): ", end="")
            response = input().strip().lower()
            if response not in ['y', 'yes']:
                print("Operation cancelled by user.")
                return 0
        
        # Step 4: Execute workflow
        print("🚀 Executing GitHub preparation workflow...")
        print()
        
        workflow_results = github_prep.execute_cleanup_workflow(
            skip_confirmation=args.skip_confirmation
        )
        
        if workflow_results['success']:
            print("✅ GitHub preparation workflow completed successfully!")
            print()
            
            # Display results summary
            print("📊 Results Summary:")
            if workflow_results.get('backup_path'):
                print(f"   - Backup created: {workflow_results['backup_path']}")
            
            cleanup_stats = workflow_results['cleanup_results']['operations_stats']
            print(f"   - Operations completed: {cleanup_stats['completed']}")
            print(f"   - Operations failed: {cleanup_stats['failed']}")
            
            if workflow_results.get('version_update', {}).get('new_version'):
                print(f"   - Version updated to: {workflow_results['version_update']['new_version']}")
            
            print(f"   - Documentation updated: {len(workflow_results['documentation']['updated_files'])} files")
            print(f"   - GitIgnore patterns added: {len(workflow_results['gitignore_update']['added_patterns'])}")
            print()
            
            # Final validation
            final_validation = workflow_results['final_validation']
            if final_validation.get('structure_valid', False):
                print("✅ Final validation passed - project is ready for GitHub!")
            else:
                print("⚠️  Final validation issues:")
                for issue in final_validation.get('issues', []):
                    print(f"   - {issue}")
            
        else:
            print("❌ GitHub preparation workflow failed!")
            return 1
        
        # Save workflow report
        report = github_prep.generate_workflow_report()
        report_file = Path(args.project_root) / "github_preparation_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Workflow report saved to: {report_file}")
        
        # Save workflow state
        state_file = github_prep.save_workflow_state()
        print(f"💾 Workflow state saved to: {state_file}")
        
        print()
        print("🎉 GitHub preparation complete! Your project is ready for upload.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Try to save workflow state even on error
        try:
            state_file = github_prep.save_workflow_state()
            print(f"💾 Workflow state saved to: {state_file}")
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())