"""
Tests for the comprehensive validation system.

This module tests all validation components including project structure,
file classification, documentation, and installation validation.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.validation_system import (
    ValidationResult, ValidationReport,
    ProjectStructureValidator, FileClassificationValidator,
    DocumentationValidator, InstallationValidator,
    ComprehensiveValidator
)
from indextts.github_preparation import GitHubPreparation, FileType


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation and serialization."""
        timestamp = datetime.now()
        result = ValidationResult(
            name="test_validation",
            passed=True,
            message="Test passed",
            details={"key": "value"},
            timestamp=timestamp
        )
        
        assert result.name == "test_validation"
        assert result.passed is True
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
        assert result.timestamp == timestamp
        
        # Test serialization
        result_dict = result.to_dict()
        assert result_dict['name'] == "test_validation"
        assert result_dict['passed'] is True
        assert result_dict['timestamp'] == timestamp.isoformat()


class TestValidationReport:
    """Test cases for ValidationReport dataclass."""
    
    def test_validation_report_creation(self):
        """Test ValidationReport creation and serialization."""
        timestamp = datetime.now()
        results = [
            ValidationResult("test1", True, "Pass", {}, timestamp),
            ValidationResult("test2", False, "Fail", {}, timestamp)
        ]
        
        report = ValidationReport(
            project_root="/test/path",
            validation_time=timestamp,
            overall_passed=False,
            results=results,
            summary={"total": 2, "passed": 1}
        )
        
        assert report.project_root == "/test/path"
        assert report.overall_passed is False
        assert len(report.results) == 2
        assert report.summary["total"] == 2
        
        # Test serialization
        report_dict = report.to_dict()
        assert report_dict['project_root'] == "/test/path"
        assert len(report_dict['results']) == 2
    
    def test_save_to_file(self):
        """Test saving validation report to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            timestamp = datetime.now()
            report = ValidationReport(
                project_root="/test",
                validation_time=timestamp,
                overall_passed=True,
                results=[],
                summary={}
            )
            
            report.save_to_file(filepath)
            
            # Verify file was created and contains valid JSON
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert data['project_root'] == "/test"
            assert 'validation_time' in data
            
        finally:
            Path(filepath).unlink(missing_ok=True)


class TestProjectStructureValidator:
    """Test cases for ProjectStructureValidator."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create basic project structure
        (project_path / 'pyproject.toml').write_text('[project]\nname = "test"')
        (project_path / 'webui.py').touch()
        
        # Create indextts package
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        (indextts_dir / '__init__.py').touch()
        (indextts_dir / 'infer_v2.py').touch()
        (indextts_dir / 'cli.py').touch()
        
        # Create subpackages
        for subpkg in ['gpt', 's2mel', 'vqvae', 'BigVGAN', 'utils']:
            subdir = indextts_dir / subpkg
            subdir.mkdir()
            (subdir / '__init__.py').touch()
        
        # Create other directories
        (project_path / 'tests').mkdir()
        (project_path / 'checkpoints').mkdir()
        (project_path / 'examples').mkdir()
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_validate_core_structure_complete(self, temp_project):
        """Test core structure validation with complete project."""
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_core_structure()
        
        assert result.passed is True
        assert result.name == "core_structure"
        assert "All core project structure elements are present" in result.message
        assert result.details['missing_files'] == []
        assert result.details['missing_directories'] == []
    
    def test_validate_core_structure_missing_files(self, temp_project):
        """Test core structure validation with missing files."""
        # Remove a required file
        (temp_project / 'webui.py').unlink()
        
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_core_structure()
        
        assert result.passed is False
        assert 'webui.py' in result.details['missing_files']
    
    def test_validate_package_structure_complete(self, temp_project):
        """Test package structure validation with complete package."""
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_package_structure()
        
        assert result.passed is True
        assert result.name == "package_structure"
        assert "Package structure is complete" in result.message
        assert result.details['missing_modules'] == []
    
    def test_validate_package_structure_missing_modules(self, temp_project):
        """Test package structure validation with missing modules."""
        # Remove a required module
        (temp_project / 'indextts' / 'gpt' / '__init__.py').unlink()
        
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_package_structure()
        
        assert result.passed is False
        assert 'gpt/__init__.py' in result.details['missing_modules']
    
    def test_validate_test_organization_good(self, temp_project):
        """Test test organization validation with properly organized tests."""
        tests_dir = temp_project / 'tests'
        (tests_dir / '__init__.py').touch()
        (tests_dir / 'test_example.py').touch()
        (tests_dir / 'test_another.py').touch()
        
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_test_organization()
        
        assert result.passed is True
        assert result.details['test_files_count'] == 2
        assert result.details['root_test_files'] == []
    
    def test_validate_test_organization_root_tests(self, temp_project):
        """Test test organization validation with root-level test files."""
        # Create root-level test files
        (temp_project / 'test_root.py').touch()
        (temp_project / 'example_test.py').touch()
        
        # Create tests directory with some tests
        tests_dir = temp_project / 'tests'
        (tests_dir / 'test_example.py').touch()
        
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_test_organization()
        
        assert result.passed is False
        assert len(result.details['root_test_files']) == 2
        assert 'test_root.py' in result.details['root_test_files']
    
    def test_validate_cleanup_completeness_clean(self, temp_project):
        """Test cleanup completeness validation with clean project."""
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_cleanup_completeness()
        
        assert result.passed is True
        assert result.details['total_unwanted'] == 0
    
    def test_validate_cleanup_completeness_unwanted_files(self, temp_project):
        """Test cleanup completeness validation with unwanted files."""
        # Create unwanted files
        (temp_project / 'debug_output.wav').touch()
        (temp_project / 'temp_file.tmp').touch()
        (temp_project / 'debug_script.py').touch()
        
        validator = ProjectStructureValidator(str(temp_project))
        result = validator.validate_cleanup_completeness()
        
        assert result.passed is False
        assert result.details['total_unwanted'] == 3


class TestFileClassificationValidator:
    """Test cases for FileClassificationValidator."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with various file types."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create files of different types
        (project_path / 'webui.py').touch()
        (project_path / 'pyproject.toml').touch()
        (project_path / 'README.md').touch()
        (project_path / '.gitignore').touch()
        
        # Create indextts package
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        (indextts_dir / '__init__.py').touch()
        
        # Create tests
        tests_dir = project_path / 'tests'
        tests_dir.mkdir()
        (tests_dir / 'test_example.py').touch()
        
        # Create examples
        examples_dir = project_path / 'examples'
        examples_dir.mkdir()
        (examples_dir / 'voice_01.wav').touch()
        
        # Create temporary files
        (project_path / 'debug_output.wav').touch()
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    def test_validate_classification_accuracy(self, temp_project):
        """Test file classification accuracy validation."""
        validator = FileClassificationValidator(str(temp_project))
        result = validator.validate_classification_accuracy()
        
        assert result.name == "classification_accuracy"
        assert 'accuracy' in result.details
        assert result.details['accuracy'] >= 0  # Should have some accuracy
        assert result.details['total_tests'] > 0
    
    def test_validate_essential_file_protection(self, temp_project):
        """Test essential file protection validation."""
        validator = FileClassificationValidator(str(temp_project))
        result = validator.validate_essential_file_protection()
        
        assert result.name == "essential_file_protection"
        assert 'protected_files' in result.details
        assert 'protection_errors' in result.details


class TestDocumentationValidator:
    """Test cases for DocumentationValidator."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for documentation testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    def test_validate_readme_missing(self, temp_project):
        """Test README validation when file is missing."""
        validator = DocumentationValidator(str(temp_project))
        result = validator.validate_readme_completeness()
        
        assert result.passed is False
        assert result.name == "readme_completeness"
        assert "does not exist" in result.message
    
    def test_validate_readme_complete(self, temp_project):
        """Test README validation with complete content."""
        readme_content = """
# IndexTTS2

IndexTTS2 is a breakthrough text-to-speech system.

## Features

- Zero-shot voice cloning
- Emotional expression control

## Installation

Install using UV package manager:

```bash
uv sync --all-extras
```

## Usage

Run the web UI:

```bash
uv run webui.py
```

Use the CLI:

```bash
uv run indextts/cli.py "Hello world" -v examples/voice_01.wav
```

## Requirements

- Python 3.10+
- PyTorch 2.8+

---

# 中文文档

## 安装

使用 UV 包管理器安装：

```bash
uv sync --all-extras
```

## 使用

运行网页界面：

```bash
uv run webui.py
```
"""
        
        (temp_project / 'README.md').write_text(readme_content, encoding='utf-8')
        
        validator = DocumentationValidator(str(temp_project))
        result = validator.validate_readme_completeness()
        
        assert result.passed is True
        assert result.name == "readme_completeness"
        assert result.details['has_installation_commands'] is True
        assert result.details['has_usage_examples'] is True
        assert len(result.details['bilingual_indicators_found']) >= 2
    
    def test_validate_readme_incomplete(self, temp_project):
        """Test README validation with incomplete content."""
        readme_content = """
# IndexTTS2

This is a basic README without proper sections.
"""
        
        (temp_project / 'README.md').write_text(readme_content, encoding='utf-8')
        
        validator = DocumentationValidator(str(temp_project))
        result = validator.validate_readme_completeness()
        
        assert result.passed is False
        assert len(result.details['missing_sections']) > 0
        assert result.details['has_installation_commands'] is False
    
    def test_validate_project_metadata_missing(self, temp_project):
        """Test project metadata validation when file is missing."""
        validator = DocumentationValidator(str(temp_project))
        result = validator.validate_project_metadata()
        
        assert result.passed is False
        assert result.name == "project_metadata"
        assert "does not exist" in result.message
    
    def test_validate_project_metadata_complete(self, temp_project):
        """Test project metadata validation with complete metadata."""
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "indextts"
version = "2.0.0"
description = "IndexTTS2: Breakthrough text-to-speech system"
authors = [
    {name = "IndexTeam", email = "team@index.com"}
]
dependencies = [
    "torch>=2.8.0",
    "torchaudio>=2.8.0",
    "gradio>=5.44.0"
]
homepage = "https://github.com/IndexTeam/IndexTTS-2"
repository = "https://github.com/IndexTeam/IndexTTS-2"

[project.optional-dependencies]
webui = ["gradio>=5.44.0"]
"""
        
        (temp_project / 'pyproject.toml').write_text(pyproject_content)
        
        validator = DocumentationValidator(str(temp_project))
        result = validator.validate_project_metadata()
        
        assert result.passed is True
        assert result.name == "project_metadata"
        assert result.details['missing_required_fields'] == []
        assert result.details['has_dependencies'] is True
        assert result.details['has_build_system'] is True
    
    def test_validate_project_metadata_incomplete(self, temp_project):
        """Test project metadata validation with incomplete metadata."""
        pyproject_content = """
[project]
name = "indextts"
# Missing version, description, authors, dependencies
"""
        
        (temp_project / 'pyproject.toml').write_text(pyproject_content)
        
        validator = DocumentationValidator(str(temp_project))
        result = validator.validate_project_metadata()
        
        assert result.passed is False
        assert len(result.details['missing_required_fields']) > 0
        assert result.details['has_dependencies'] is False


class TestInstallationValidator:
    """Test cases for InstallationValidator."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for installation testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create minimal project structure
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
version = "1.0.0"
description = "Test project"
dependencies = ["requests"]
"""
        (project_path / 'pyproject.toml').write_text(pyproject_content)
        
        # Create package structure
        pkg_dir = project_path / 'indextts'
        pkg_dir.mkdir()
        (pkg_dir / '__init__.py').touch()
        (pkg_dir / 'cli.py').write_text("""
import sys
def main():
    if '--help' in sys.argv:
        print("CLI Help")
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    @patch('subprocess.run')
    def test_validate_dependency_resolution_success(self, mock_run, temp_project):
        """Test dependency resolution validation with successful resolution."""
        # Mock successful uv lock command
        mock_run.return_value = Mock(returncode=0, stdout="Dependencies resolved", stderr="")
        
        # Create uv.lock file
        (temp_project / 'uv.lock').touch()
        
        validator = InstallationValidator(str(temp_project))
        result = validator.validate_dependency_resolution()
        
        assert result.passed is True
        assert result.name == "dependency_resolution"
        assert result.details['lock_file_exists'] is True
        assert result.details['resolution_success'] is True
    
    @patch('subprocess.run')
    def test_validate_dependency_resolution_failure(self, mock_run, temp_project):
        """Test dependency resolution validation with resolution failure."""
        # Mock failed uv lock command
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Resolution failed")
        
        validator = InstallationValidator(str(temp_project))
        result = validator.validate_dependency_resolution()
        
        assert result.passed is False
        assert result.details['resolution_success'] is False
        assert "Resolution failed" in result.details['resolution_error']
    
    @patch('subprocess.run')
    def test_validate_uv_installation_success(self, mock_run, temp_project):
        """Test UV installation validation with successful installation."""
        # Mock UV commands
        def mock_subprocess(cmd, **kwargs):
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                return Mock(returncode=0, stdout="Sync successful", stderr="")
            elif 'cli.py' in ' '.join(cmd):
                return Mock(returncode=0, stdout="CLI Help", stderr="")
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        validator = InstallationValidator(str(temp_project))
        result = validator.validate_uv_installation()
        
        assert result.passed is True
        assert result.name == "uv_installation"
        assert result.details['uv_sync_success'] is True
    
    @patch('subprocess.run')
    def test_validate_uv_installation_uv_not_available(self, mock_run, temp_project):
        """Test UV installation validation when UV is not available."""
        # Mock UV not found
        mock_run.side_effect = FileNotFoundError("uv not found")
        
        validator = InstallationValidator(str(temp_project))
        result = validator.validate_uv_installation()
        
        assert result.passed is False
        assert "UV not available" in result.message


class TestComprehensiveValidator:
    """Test cases for ComprehensiveValidator."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a comprehensive temporary project for testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create complete project structure
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "indextts"
version = "2.0.0"
description = "IndexTTS2: Breakthrough text-to-speech system"
authors = [{name = "IndexTeam"}]
dependencies = ["torch>=2.8.0"]
"""
        (project_path / 'pyproject.toml').write_text(pyproject_content)
        (project_path / 'webui.py').touch()
        
        # Create README
        readme_content = """
# IndexTTS2

## Installation
uv sync --all-extras

## Usage
uv run webui.py

## Features
- Voice cloning

# 中文
## 安装
uv sync --all-extras
"""
        (project_path / 'README.md').write_text(readme_content, encoding='utf-8')
        
        # Create package structure
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        (indextts_dir / '__init__.py').touch()
        (indextts_dir / 'infer_v2.py').touch()
        (indextts_dir / 'cli.py').touch()
        
        for subpkg in ['gpt', 's2mel', 'vqvae', 'BigVGAN', 'utils']:
            subdir = indextts_dir / subpkg
            subdir.mkdir()
            (subdir / '__init__.py').touch()
        
        # Create other directories
        (project_path / 'tests').mkdir()
        (project_path / 'checkpoints').mkdir()
        (project_path / 'examples').mkdir()
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    @patch('subprocess.run')
    def test_run_all_validations(self, mock_run, temp_project):
        """Test running all validations."""
        # Mock subprocess calls
        mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
        
        validator = ComprehensiveValidator(str(temp_project))
        report = validator.run_all_validations()
        
        assert isinstance(report, ValidationReport)
        assert report.project_root == str(temp_project)
        assert len(report.results) > 0
        assert 'total_validations' in report.summary
        assert 'passed_validations' in report.summary
        assert 'validation_categories' in report.summary
    
    def test_validate_workflow_integration(self, temp_project):
        """Test workflow integration validation."""
        validator = ComprehensiveValidator(str(temp_project))
        
        # Create mock GitHub preparation instance
        github_prep = Mock()
        github_prep.analyze_project.return_value = {
            'total_files': 10,
            'files_by_action': {'keep': 8, 'delete': 2},
            'files_by_type': {'source': 5, 'test': 3, 'temp': 2}
        }
        github_prep.workflow_state.total_files_analyzed = 10
        github_prep.workflow_state.steps = [Mock()]
        github_prep._validate_operation_safety.return_value = {'is_safe': True}
        
        result = validator.validate_workflow_integration(github_prep)
        
        assert result.name == "workflow_integration"
        assert result.passed is True
        assert result.details['analysis_success'] is True
        assert result.details['state_valid'] is True
        assert result.details['safety_valid'] is True


class TestIntegrationWorkflow:
    """Integration tests for complete cleanup workflow validation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a realistic project structure for integration testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create realistic project structure with issues to clean up
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "indextts"
version = "1.0.0"
description = "IndexTTS2 project"
authors = [{name = "Team"}]
dependencies = ["torch", "gradio"]
"""
        (project_path / 'pyproject.toml').write_text(pyproject_content)
        (project_path / 'webui.py').touch()
        
        # Create indextts package
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        (indextts_dir / '__init__.py').touch()
        (indextts_dir / 'infer_v2.py').touch()
        (indextts_dir / 'cli.py').touch()
        
        for subpkg in ['gpt', 's2mel', 'vqvae', 'BigVGAN', 'utils']:
            subdir = indextts_dir / subpkg
            subdir.mkdir()
            (subdir / '__init__.py').touch()
        
        # Create directories
        (project_path / 'tests').mkdir()
        (project_path / 'checkpoints').mkdir()
        (project_path / 'examples').mkdir()
        
        # Create files that need cleanup
        (project_path / 'debug_output.wav').touch()
        (project_path / 'test_root_level.py').touch()
        (project_path / 'temp_file.tmp').touch()
        
        # Create proper test files
        (project_path / 'tests' / 'test_example.py').touch()
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    def test_complete_workflow_validation(self, temp_project):
        """Test validation of complete GitHub preparation workflow."""
        # Create GitHub preparation instance
        github_prep = GitHubPreparation(
            project_root=str(temp_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Run analysis
        analysis_results = github_prep.analyze_project()
        
        # Validate that analysis found issues
        assert analysis_results['total_files'] > 0
        assert 'files_by_action' in analysis_results
        
        # Create comprehensive validator
        validator = ComprehensiveValidator(str(temp_project))
        
        # Test workflow integration
        integration_result = validator.validate_workflow_integration(github_prep)
        assert integration_result.passed is True
        
        # Run full validation suite
        report = validator.run_all_validations()
        
        # Check that validation identified issues that need fixing
        structure_results = [r for r in report.results if r.name.startswith(('core_', 'package_', 'test_', 'cleanup_'))]
        assert len(structure_results) > 0
        
        # Some validations should fail due to cleanup issues
        cleanup_result = next((r for r in report.results if r.name == 'cleanup_completeness'), None)
        assert cleanup_result is not None
        # Should fail because we have unwanted files
        assert cleanup_result.passed is False
        
        # Test organization should fail due to root-level test file
        test_org_result = next((r for r in report.results if r.name == 'test_organization'), None)
        assert test_org_result is not None
        assert test_org_result.passed is False
    
    @patch('subprocess.run')
    def test_post_cleanup_validation(self, mock_run, temp_project):
        """Test validation after cleanup operations are completed."""
        # Mock successful subprocess calls
        mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
        
        # Simulate cleanup by removing unwanted files
        (temp_project / 'debug_output.wav').unlink()
        (temp_project / 'temp_file.tmp').unlink()
        
        # Move root-level test file to tests directory
        (temp_project / 'test_root_level.py').rename(temp_project / 'tests' / 'test_root_level.py')
        
        # Create proper README
        readme_content = """
# IndexTTS2

## Installation
uv sync --all-extras

## Usage  
uv run webui.py

## Features
- Voice cloning

# 中文
## 安装
uv sync --all-extras
"""
        (temp_project / 'README.md').write_text(readme_content, encoding='utf-8')
        
        # Update pyproject.toml with complete metadata
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "indextts"
version = "2.0.0"
description = "IndexTTS2: Breakthrough text-to-speech system"
authors = [{name = "IndexTeam"}]
dependencies = ["torch>=2.8.0", "gradio>=5.44.0"]
homepage = "https://github.com/IndexTeam/IndexTTS-2"
"""
        (temp_project / 'pyproject.toml').write_text(pyproject_content)
        
        # Run validation after cleanup
        validator = ComprehensiveValidator(str(temp_project))
        report = validator.run_all_validations()
        
        # Most validations should now pass
        passed_count = sum(1 for r in report.results if r.passed)
        total_count = len(report.results)
        
        # Should have high success rate after cleanup
        success_rate = passed_count / total_count
        assert success_rate >= 0.6  # At least 60% should pass
        
        # Specific validations that should pass after cleanup
        cleanup_result = next((r for r in report.results if r.name == 'cleanup_completeness'), None)
        assert cleanup_result is not None
        assert cleanup_result.passed is True
        
        test_org_result = next((r for r in report.results if r.name == 'test_organization'), None)
        assert test_org_result is not None
        assert test_org_result.passed is True
        
        readme_result = next((r for r in report.results if r.name == 'readme_completeness'), None)
        assert readme_result is not None
        assert readme_result.passed is True


if __name__ == "__main__":
    pytest.main([__file__])