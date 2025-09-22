#!/usr/bin/env python3
"""
Demonstration of the GitHubPreparation comprehensive workflow.

This script shows how to use the GitHubPreparation class to analyze and prepare
the IndexTTS2 project for GitHub upload with safety checks and progress reporting.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation import GitHubPreparation


def demo_analysis_only():
    """Demonstrate project analysis without executing cleanup."""
    print("=" * 60)
    print("GitHub Preparation - Analysis Demo")
    print("=" * 60)
    
    # Initialize with dry run mode for safety
    github_prep = GitHubPreparation(
        project_root=".",
        dry_run=True,
        backup_enabled=False
    )
    
    # Set up progress callback
    def progress_callback(step_name, progress, message):
        print(f"[{step_name}] {progress:5.1f}% - {message}")
    
    github_prep.set_progress_callback(progress_callback)
    
    try:
        print("\n🔍 Validating project structure...")
        is_valid, issues = github_prep.validate_project_structure()
        
        if not is_valid:
            print("❌ Project validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            return
        
        print("✅ Project structure validation passed")
        
        print("\n📊 Analyzing project...")
        analysis_results = github_prep.analyze_project()
        
        print(f"\n📈 Analysis Results:")
        print(f"   - Total files: {analysis_results['total_files']}")
        print(f"   - Planned operations: {analysis_results['planned_operations']}")
        
        print(f"\n📋 Files by Action:")
        for action, count in analysis_results['files_by_action'].items():
            if count > 0:
                print(f"   - {action.replace('_', ' ').title()}: {count} files")
        
        print(f"\n📂 Files by Type:")
        for file_type, count in analysis_results['files_by_type'].items():
            if count > 0:
                print(f"   - {file_type.replace('_', ' ').title()}: {count} files")
        
        # Safety report
        safety_report = analysis_results['safety_report']
        print(f"\n🛡️  Safety Report:")
        print(f"   - Is Safe: {safety_report['is_safe']}")
        print(f"   - Delete Operations: {safety_report['statistics']['delete_operations']}")
        print(f"   - Delete Percentage: {safety_report['statistics']['delete_percentage']:.1f}%")
        
        if safety_report['warnings']:
            print("   - Warnings:")
            for warning in safety_report['warnings']:
                print(f"     • {warning}")
        
        if safety_report['errors']:
            print("   - Errors:")
            for error in safety_report['errors']:
                print(f"     • {error}")
        
        # Generate and save report
        report = github_prep.generate_workflow_report()
        report_file = "github_preparation_demo_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Save classification report
        classification_file = "github_preparation_classification.md"
        with open(classification_file, 'w', encoding='utf-8') as f:
            f.write(analysis_results['classification_report'])
        print(f"📄 Classification report saved to: {classification_file}")
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
    finally:
        # Clean up resources
        github_prep.cleanup()


def demo_workflow_steps():
    """Demonstrate individual workflow steps."""
    print("\n" + "=" * 60)
    print("GitHub Preparation - Workflow Steps Demo")
    print("=" * 60)
    
    github_prep = GitHubPreparation(
        project_root=".",
        dry_run=True,
        backup_enabled=False
    )
    
    try:
        print("\n📋 Workflow Steps:")
        
        # Step 1: File Classification
        print("\n1. File Classification")
        file_infos = github_prep.file_classifier.scan_project()
        files_by_type = github_prep.file_classifier.get_files_by_type(file_infos)
        
        for file_type, files in files_by_type.items():
            if len(files) > 0:
                print(f"   - {file_type.value}: {len(files)} files")
                # Show a few examples
                for i, file_info in enumerate(files[:3]):
                    print(f"     • {file_info.path} ({file_info.action.value})")
                if len(files) > 3:
                    print(f"     • ... and {len(files) - 3} more")
        
        # Step 2: Safety Validation
        print("\n2. Safety Validation")
        operations = github_prep.safe_file_manager.plan_operations(file_infos)
        safety_report = github_prep._validate_operation_safety(operations)
        
        print(f"   - Total operations planned: {len(operations)}")
        print(f"   - Safety validation: {'✅ PASS' if safety_report['is_safe'] else '❌ FAIL'}")
        
        # Step 3: Operation Planning
        print("\n3. Operation Planning")
        files_by_action = github_prep.file_classifier.get_files_by_action(file_infos)
        
        for action, files in files_by_action.items():
            if len(files) > 0:
                print(f"   - {action.value}: {len(files)} files")
        
        print("\n✅ Workflow steps demonstration complete!")
        
    except Exception as e:
        print(f"\n❌ Error during workflow demo: {e}")
    finally:
        github_prep.cleanup()


def main():
    """Main demonstration function."""
    print("IndexTTS2 GitHub Preparation Workflow Demonstration")
    print("This demo shows the comprehensive cleanup workflow capabilities.")
    
    # Demo 1: Analysis only
    demo_analysis_only()
    
    # Demo 2: Workflow steps
    demo_workflow_steps()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTo run the actual cleanup workflow:")
    print("python indextts/github_preparation/github_preparation_example.py --dry-run")
    print("\nTo run with real file operations (BE CAREFUL!):")
    print("python indextts/github_preparation/github_preparation_example.py")


if __name__ == "__main__":
    main()