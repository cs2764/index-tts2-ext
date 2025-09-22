"""
Demonstration script for the GitHub preparation validation system.

This script shows how the validation system works and provides examples
of its capabilities.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.validation_system import (
    ComprehensiveValidator, ProjectStructureValidator,
    FileClassificationValidator, DocumentationValidator,
    InstallationValidator
)


def create_demo_project():
    """Create a demonstration project structure."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    
    print(f"📁 Creating demo project at: {project_path}")
    
    # Create basic project structure
    pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "demo-project"
version = "1.0.0"
description = "Demo project for validation testing"
authors = [{name = "Demo Team", email = "demo@example.com"}]
dependencies = ["requests>=2.25.0"]
homepage = "https://github.com/demo/demo-project"
"""
    (project_path / 'pyproject.toml').write_text(pyproject_content)
    (project_path / 'webui.py').write_text('# Demo web UI\nprint("Demo WebUI")')
    
    # Create indextts package structure
    indextts_dir = project_path / 'indextts'
    indextts_dir.mkdir()
    (indextts_dir / '__init__.py').write_text('"""Demo package."""\n__version__ = "1.0.0"')
    (indextts_dir / 'infer_v2.py').write_text('# Demo inference\nclass DemoTTS: pass')
    (indextts_dir / 'cli.py').write_text('# Demo CLI\ndef main(): pass')
    
    # Create subpackages
    for subpkg in ['gpt', 's2mel', 'vqvae', 'BigVGAN', 'utils']:
        subdir = indextts_dir / subpkg
        subdir.mkdir()
        (subdir / '__init__.py').write_text(f'# {subpkg} module')
    
    # Create directories
    (project_path / 'tests').mkdir()
    (project_path / 'checkpoints').mkdir()
    (project_path / 'examples').mkdir()
    
    # Create proper test files
    tests_dir = project_path / 'tests'
    (tests_dir / '__init__.py').touch()
    (tests_dir / 'test_demo.py').write_text('# Demo test\ndef test_demo(): pass')
    
    # Create README
    readme_content = """
# Demo Project

This is a demonstration project for validation testing.

## Installation

```bash
uv sync
```

## Usage

```bash
uv run webui.py
```

## Features

- Demo feature 1
- Demo feature 2

---

# 中文文档

这是一个演示项目。

## 安装

```bash
uv sync
```

## 使用

```bash
uv run webui.py
```
"""
    (project_path / 'README.md').write_text(readme_content, encoding='utf-8')
    
    return project_path


def demo_project_structure_validation(project_path):
    """Demonstrate project structure validation."""
    print("\n🏗️  DEMONSTRATING PROJECT STRUCTURE VALIDATION")
    print("=" * 60)
    
    validator = ProjectStructureValidator(str(project_path))
    
    # Test core structure
    result = validator.validate_core_structure()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Core Structure: {status}")
    print(f"  Message: {result.message}")
    if result.details.get('missing_files'):
        print(f"  Missing files: {result.details['missing_files']}")
    
    # Test package structure
    result = validator.validate_package_structure()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Package Structure: {status}")
    print(f"  Message: {result.message}")
    
    # Test test organization
    result = validator.validate_test_organization()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Test Organization: {status}")
    print(f"  Message: {result.message}")
    print(f"  Test files found: {result.details.get('test_files_count', 0)}")
    
    # Test cleanup completeness
    result = validator.validate_cleanup_completeness()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Cleanup Completeness: {status}")
    print(f"  Message: {result.message}")
    if result.details.get('unwanted_files_found'):
        print(f"  Unwanted files: {len(result.details['unwanted_files_found'])}")


def demo_file_classification_validation(project_path):
    """Demonstrate file classification validation."""
    print("\n📂 DEMONSTRATING FILE CLASSIFICATION VALIDATION")
    print("=" * 60)
    
    validator = FileClassificationValidator(str(project_path))
    
    # Test classification accuracy
    result = validator.validate_classification_accuracy()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Classification Accuracy: {status}")
    print(f"  Message: {result.message}")
    print(f"  Accuracy: {result.details.get('accuracy', 0):.1%}")
    print(f"  Tests run: {result.details.get('total_tests', 0)}")
    
    # Test essential file protection
    result = validator.validate_essential_file_protection()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Essential File Protection: {status}")
    print(f"  Message: {result.message}")
    print(f"  Protected files: {result.details.get('protected_files', 0)}")


def demo_documentation_validation(project_path):
    """Demonstrate documentation validation."""
    print("\n📚 DEMONSTRATING DOCUMENTATION VALIDATION")
    print("=" * 60)
    
    validator = DocumentationValidator(str(project_path))
    
    # Test README completeness
    result = validator.validate_readme_completeness()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"README Completeness: {status}")
    print(f"  Message: {result.message}")
    print(f"  Has installation commands: {result.details.get('has_installation_commands', False)}")
    print(f"  Has usage examples: {result.details.get('has_usage_examples', False)}")
    print(f"  Bilingual indicators: {len(result.details.get('bilingual_indicators_found', []))}")
    
    # Test project metadata
    result = validator.validate_project_metadata()
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print(f"Project Metadata: {status}")
    print(f"  Message: {result.message}")
    if result.details.get('project_name'):
        print(f"  Project: {result.details['project_name']} v{result.details.get('project_version', 'unknown')}")


def demo_comprehensive_validation(project_path):
    """Demonstrate comprehensive validation."""
    print("\n🎯 DEMONSTRATING COMPREHENSIVE VALIDATION")
    print("=" * 60)
    
    validator = ComprehensiveValidator(str(project_path))
    
    print("Running all validations...")
    report = validator.run_all_validations()
    
    print(f"\nValidation Results:")
    print(f"Overall Status: {'✅ PASSED' if report.overall_passed else '❌ FAILED'}")
    print(f"Success Rate: {report.summary['success_rate']:.1%}")
    print(f"Passed: {report.summary['passed_validations']}/{report.summary['total_validations']}")
    
    print(f"\nDetailed Results:")
    for result in report.results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.name}: {result.message}")
    
    print(f"\nCategory Summary:")
    categories = report.summary['validation_categories']
    for category, count in categories.items():
        print(f"  {category}: {count} passed")
    
    return report


def main():
    """Main demonstration function."""
    print("🚀 GITHUB PREPARATION VALIDATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    print(f"Start time: {datetime.now()}")
    
    # Create demo project
    project_path = create_demo_project()
    
    try:
        # Run individual validation demonstrations
        demo_project_structure_validation(project_path)
        demo_file_classification_validation(project_path)
        demo_documentation_validation(project_path)
        
        # Run comprehensive validation
        report = demo_comprehensive_validation(project_path)
        
        # Save report
        report_file = Path('demo_validation_report.json')
        report.save_to_file(str(report_file))
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        print(f"\n🎉 Demonstration completed successfully!")
        print(f"Demo project created at: {project_path}")
        print("You can examine the project structure and validation results.")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Demonstration failed: {e}")
        return 1
        
    finally:
        # Cleanup (optional - comment out to keep demo project)
        try:
            shutil.rmtree(project_path)
            print(f"\n🧹 Cleaned up demo project at: {project_path}")
        except Exception as e:
            print(f"\n⚠️  Could not clean up demo project: {e}")


if __name__ == "__main__":
    sys.exit(main())