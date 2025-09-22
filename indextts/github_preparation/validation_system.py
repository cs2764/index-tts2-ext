"""
Comprehensive validation and testing system for GitHub preparation workflow.

This module provides validation for project structure, file operations, documentation
completeness, and installation processes after cleanup operations.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation import (
    FileClassifier, FileType, FileAction,
    SafeFileManager, GitHubPreparation
)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    passed: bool
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    project_root: str
    validation_time: datetime
    overall_passed: bool
    results: List[ValidationResult]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'project_root': self.project_root,
            'validation_time': self.validation_time.isoformat(),
            'overall_passed': self.overall_passed,
            'results': [r.to_dict() for r in self.results],
            'summary': self.summary
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save validation report to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class ProjectStructureValidator:
    """Validates project structure after cleanup operations."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
    
    def validate_core_structure(self) -> ValidationResult:
        """Validate that core project structure is intact."""
        required_files = [
            'pyproject.toml',
            'webui.py',
            'indextts/__init__.py',
            'indextts/infer_v2.py',
            'indextts/cli.py'
        ]
        
        required_dirs = [
            'indextts',
            'tests',
            'checkpoints',
            'examples'
        ]
        
        missing_files = []
        missing_dirs = []
        
        # Check required files
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        # Check required directories
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.is_dir():
                missing_dirs.append(dir_path)
        
        passed = len(missing_files) == 0 and len(missing_dirs) == 0
        
        details = {
            'missing_files': missing_files,
            'missing_directories': missing_dirs,
            'checked_files': len(required_files),
            'checked_directories': len(required_dirs)
        }
        
        if passed:
            message = "All core project structure elements are present"
        else:
            message = f"Missing {len(missing_files)} files and {len(missing_dirs)} directories"
        
        return ValidationResult(
            name="core_structure",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
    
    def validate_package_structure(self) -> ValidationResult:
        """Validate indextts package structure."""
        package_root = self.project_root / 'indextts'
        
        required_modules = [
            '__init__.py',
            'cli.py',
            'infer_v2.py',
            'gpt/__init__.py',
            's2mel/__init__.py',
            'vqvae/__init__.py',
            'BigVGAN/__init__.py',
            'utils/__init__.py'
        ]
        
        missing_modules = []
        
        for module_path in required_modules:
            full_path = package_root / module_path
            if not full_path.exists():
                missing_modules.append(module_path)
        
        passed = len(missing_modules) == 0
        
        details = {
            'missing_modules': missing_modules,
            'checked_modules': len(required_modules),
            'package_root': str(package_root)
        }
        
        message = ("Package structure is complete" if passed 
                  else f"Missing {len(missing_modules)} required modules")
        
        return ValidationResult(
            name="package_structure",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
    
    def validate_test_organization(self) -> ValidationResult:
        """Validate that tests are properly organized."""
        tests_dir = self.project_root / 'tests'
        
        if not tests_dir.exists():
            return ValidationResult(
                name="test_organization",
                passed=False,
                message="Tests directory does not exist",
                details={'tests_directory': str(tests_dir)},
                timestamp=datetime.now()
            )
        
        # Check for test files
        test_files = list(tests_dir.glob('test_*.py'))
        init_file = tests_dir / '__init__.py'
        
        # Check for root-level test files that should have been moved
        root_test_files = list(self.project_root.glob('test_*.py'))
        root_test_files.extend(list(self.project_root.glob('*_test.py')))
        
        passed = len(test_files) > 0 and len(root_test_files) == 0
        
        details = {
            'test_files_count': len(test_files),
            'root_test_files': [str(f.name) for f in root_test_files],
            'has_init_file': init_file.exists(),
            'test_files': [str(f.name) for f in test_files[:10]]  # First 10 for brevity
        }
        
        if passed:
            message = f"Tests properly organized: {len(test_files)} test files in tests/ directory"
        else:
            message = f"Test organization issues: {len(root_test_files)} root-level test files remain"
        
        return ValidationResult(
            name="test_organization",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
    
    def validate_cleanup_completeness(self) -> ValidationResult:
        """Validate that cleanup operations were completed properly."""
        # Check for common temporary/debug files that should be removed
        unwanted_patterns = [
            '*.tmp',
            '*.temp',
            'debug_*.py',
            'debug_*.wav',
            'test_output*.wav',
            '*.log',
            '__pycache__',
            '.pytest_cache'
        ]
        
        found_unwanted = []
        
        for pattern in unwanted_patterns:
            matches = list(self.project_root.rglob(pattern))
            # Filter out files in .git, .venv, and other expected locations
            filtered_matches = [
                m for m in matches 
                if not any(part.startswith('.') and part in ['.git', '.venv', '.pytest_cache'] 
                          for part in m.parts)
            ]
            if filtered_matches:
                found_unwanted.extend(filtered_matches)
        
        passed = len(found_unwanted) == 0
        
        details = {
            'unwanted_files_found': [str(f) for f in found_unwanted],
            'patterns_checked': unwanted_patterns,
            'total_unwanted': len(found_unwanted)
        }
        
        message = ("Cleanup completed successfully" if passed 
                  else f"Found {len(found_unwanted)} files that should have been cleaned up")
        
        return ValidationResult(
            name="cleanup_completeness",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )


class FileClassificationValidator:
    """Validates file classification accuracy and safety."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.classifier = FileClassifier(project_root)
        self.logger = logging.getLogger(__name__)
    
    def validate_classification_accuracy(self) -> ValidationResult:
        """Validate that file classification is accurate."""
        # Test known file types
        test_cases = [
            ('webui.py', FileType.SOURCE_CODE),
            ('pyproject.toml', FileType.CONFIGURATION),
            ('README.md', FileType.DOCUMENTATION),
            ('indextts/__init__.py', FileType.SOURCE_CODE),
            ('tests/test_example.py', FileType.TEST_FILE),
            ('examples/voice_01.wav', FileType.AUDIO_SAMPLE),
            ('debug_output.wav', FileType.TEMPORARY),
            ('.gitignore', FileType.CONFIGURATION),
        ]
        
        correct_classifications = 0
        total_tests = 0
        classification_errors = []
        
        for file_path, expected_type in test_cases:
            full_path = self.project_root / file_path
            if full_path.exists():
                total_tests += 1
                try:
                    classified_type = self.classifier.classify_file(str(full_path))
                    if classified_type == expected_type:
                        correct_classifications += 1
                    else:
                        classification_errors.append({
                            'file': file_path,
                            'expected': expected_type.value,
                            'actual': classified_type.value
                        })
                except Exception as e:
                    classification_errors.append({
                        'file': file_path,
                        'expected': expected_type.value,
                        'error': str(e)
                    })
        
        accuracy = correct_classifications / total_tests if total_tests > 0 else 0
        passed = accuracy >= 0.8  # 80% accuracy threshold
        
        details = {
            'accuracy': accuracy,
            'correct_classifications': correct_classifications,
            'total_tests': total_tests,
            'classification_errors': classification_errors,
            'accuracy_threshold': 0.8
        }
        
        message = f"Classification accuracy: {accuracy:.2%} ({correct_classifications}/{total_tests})"
        
        return ValidationResult(
            name="classification_accuracy",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
    
    def validate_essential_file_protection(self) -> ValidationResult:
        """Validate that essential files are properly protected."""
        essential_files = [
            'webui.py',
            'pyproject.toml',
            'indextts/__init__.py',
            'indextts/infer_v2.py',
            'indextts/cli.py',
            'checkpoints/config.yaml'
        ]
        
        protection_errors = []
        protected_count = 0
        
        for file_path in essential_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    is_essential = self.classifier.is_essential_file(str(full_path))
                    if is_essential:
                        protected_count += 1
                    else:
                        protection_errors.append({
                            'file': file_path,
                            'error': 'Not marked as essential'
                        })
                except Exception as e:
                    protection_errors.append({
                        'file': file_path,
                        'error': str(e)
                    })
        
        passed = len(protection_errors) == 0
        
        details = {
            'protected_files': protected_count,
            'total_essential_files': len(essential_files),
            'protection_errors': protection_errors
        }
        
        message = (f"All {protected_count} essential files properly protected" if passed
                  else f"{len(protection_errors)} essential files not properly protected")
        
        return ValidationResult(
            name="essential_file_protection",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )


class DocumentationValidator:
    """Validates documentation completeness and accuracy."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
    
    def validate_readme_completeness(self) -> ValidationResult:
        """Validate README.md completeness."""
        readme_path = self.project_root / 'README.md'
        
        if not readme_path.exists():
            return ValidationResult(
                name="readme_completeness",
                passed=False,
                message="README.md file does not exist",
                details={'readme_path': str(readme_path)},
                timestamp=datetime.now()
            )
        
        try:
            content = readme_path.read_text(encoding='utf-8')
        except Exception as e:
            return ValidationResult(
                name="readme_completeness",
                passed=False,
                message=f"Failed to read README.md: {e}",
                details={'error': str(e)},
                timestamp=datetime.now()
            )
        
        # Check for required sections
        required_sections = [
            'IndexTTS2',  # Title
            'Installation',
            'Usage',
            'Features',
            'Requirements'
        ]
        
        # Check for bilingual content
        bilingual_indicators = [
            '中文',  # Chinese
            'English',
            '安装',  # Installation in Chinese
            '使用'   # Usage in Chinese
        ]
        
        missing_sections = []
        found_bilingual = []
        
        content_lower = content.lower()
        
        for section in required_sections:
            if section.lower() not in content_lower:
                missing_sections.append(section)
        
        for indicator in bilingual_indicators:
            if indicator in content or indicator.lower() in content_lower:
                found_bilingual.append(indicator)
        
        has_installation_commands = any(cmd in content for cmd in ['uv sync', 'pip install', 'uv run'])
        has_usage_examples = any(example in content for example in ['webui.py', 'cli.py', 'python'])
        
        passed = (len(missing_sections) == 0 and 
                 len(found_bilingual) >= 2 and 
                 has_installation_commands and 
                 has_usage_examples)
        
        details = {
            'missing_sections': missing_sections,
            'bilingual_indicators_found': found_bilingual,
            'has_installation_commands': has_installation_commands,
            'has_usage_examples': has_usage_examples,
            'content_length': len(content),
            'required_sections': required_sections
        }
        
        if passed:
            message = "README.md is complete with bilingual content and proper sections"
        else:
            issues = []
            if missing_sections:
                issues.append(f"{len(missing_sections)} missing sections")
            if len(found_bilingual) < 2:
                issues.append("insufficient bilingual content")
            if not has_installation_commands:
                issues.append("missing installation commands")
            if not has_usage_examples:
                issues.append("missing usage examples")
            message = f"README.md issues: {', '.join(issues)}"
        
        return ValidationResult(
            name="readme_completeness",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
    
    def validate_project_metadata(self) -> ValidationResult:
        """Validate pyproject.toml metadata completeness."""
        pyproject_path = self.project_root / 'pyproject.toml'
        
        if not pyproject_path.exists():
            return ValidationResult(
                name="project_metadata",
                passed=False,
                message="pyproject.toml file does not exist",
                details={'pyproject_path': str(pyproject_path)},
                timestamp=datetime.now()
            )
        
        try:
            # Try tomllib first (Python 3.11+), then fall back to tomli
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    # Fall back to manual parsing for basic validation
                    content = pyproject_path.read_text(encoding='utf-8')
                    # Simple check for required sections
                    has_project = '[project]' in content
                    has_build = '[build-system]' in content
                    
                    if not has_project:
                        return ValidationResult(
                            name="project_metadata",
                            passed=False,
                            message="pyproject.toml missing [project] section",
                            details={'error': 'No [project] section found'},
                            timestamp=datetime.now()
                        )
                    
                    # Return basic validation result
                    return ValidationResult(
                        name="project_metadata",
                        passed=has_project and has_build,
                        message="Basic pyproject.toml structure validation (limited - install tomli for full validation)",
                        details={
                            'has_project_section': has_project,
                            'has_build_section': has_build,
                            'limited_validation': True
                        },
                        timestamp=datetime.now()
                    )
            
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)
        except Exception as e:
            return ValidationResult(
                name="project_metadata",
                passed=False,
                message=f"Failed to parse pyproject.toml: {e}",
                details={'error': str(e)},
                timestamp=datetime.now()
            )
        
        # Check required project metadata
        project_section = data.get('project', {})
        
        required_fields = ['name', 'version', 'description', 'authors']
        optional_fields = ['homepage', 'repository', 'keywords', 'classifiers']
        
        missing_required = []
        missing_optional = []
        
        for field in required_fields:
            if field not in project_section:
                missing_required.append(field)
        
        for field in optional_fields:
            if field not in project_section:
                missing_optional.append(field)
        
        # Check dependencies
        has_dependencies = 'dependencies' in project_section
        has_optional_deps = 'optional-dependencies' in project_section
        
        # Check build system
        build_system = data.get('build-system', {})
        has_build_system = 'requires' in build_system and 'build-backend' in build_system
        
        passed = (len(missing_required) == 0 and 
                 has_dependencies and 
                 has_build_system)
        
        details = {
            'missing_required_fields': missing_required,
            'missing_optional_fields': missing_optional,
            'has_dependencies': has_dependencies,
            'has_optional_dependencies': has_optional_deps,
            'has_build_system': has_build_system,
            'project_name': project_section.get('name'),
            'project_version': project_section.get('version')
        }
        
        if passed:
            message = f"Project metadata complete for {project_section.get('name', 'unknown')} v{project_section.get('version', 'unknown')}"
        else:
            issues = []
            if missing_required:
                issues.append(f"{len(missing_required)} required fields missing")
            if not has_dependencies:
                issues.append("no dependencies specified")
            if not has_build_system:
                issues.append("build system not configured")
            message = f"Project metadata issues: {', '.join(issues)}"
        
        return ValidationResult(
            name="project_metadata",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )


class InstallationValidator:
    """Validates installation process with UV after cleanup."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
    
    def validate_uv_installation(self) -> ValidationResult:
        """Validate that project can be installed with UV."""
        # Check if UV is available
        try:
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return ValidationResult(
                    name="uv_installation",
                    passed=False,
                    message="UV package manager not available",
                    details={'error': 'UV not found in PATH'},
                    timestamp=datetime.now()
                )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return ValidationResult(
                name="uv_installation",
                passed=False,
                message=f"UV not available: {e}",
                details={'error': str(e)},
                timestamp=datetime.now()
            )
        
        # Create temporary directory for installation test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Copy project files to temp directory
                shutil.copytree(self.project_root, temp_path / 'test_project', 
                              ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__', '*.pyc'))
                
                test_project_path = temp_path / 'test_project'
                
                # Try to sync dependencies
                result = subprocess.run(
                    ['uv', 'sync', '--no-dev'],
                    cwd=test_project_path,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                sync_success = result.returncode == 0
                
                # Try to run basic commands if sync succeeded
                run_tests = []
                if sync_success:
                    # Test CLI help
                    cli_result = subprocess.run(
                        ['uv', 'run', 'python', '-m', 'indextts.cli', '--help'],
                        cwd=test_project_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    run_tests.append({
                        'command': 'CLI help',
                        'success': cli_result.returncode == 0,
                        'output': cli_result.stdout[:200] if cli_result.stdout else '',
                        'error': cli_result.stderr[:200] if cli_result.stderr else ''
                    })
                
                passed = sync_success and all(test['success'] for test in run_tests)
                
                details = {
                    'uv_sync_success': sync_success,
                    'uv_sync_output': result.stdout[:500] if result.stdout else '',
                    'uv_sync_error': result.stderr[:500] if result.stderr else '',
                    'run_tests': run_tests,
                    'test_project_path': str(test_project_path)
                }
                
                if passed:
                    message = "Project successfully installs and runs with UV"
                else:
                    if not sync_success:
                        message = f"UV sync failed: {result.stderr[:100] if result.stderr else 'Unknown error'}"
                    else:
                        failed_tests = [t['command'] for t in run_tests if not t['success']]
                        message = f"Installation succeeded but runtime tests failed: {', '.join(failed_tests)}"
                
            except Exception as e:
                passed = False
                message = f"Installation test failed: {e}"
                details = {'error': str(e)}
        
        return ValidationResult(
            name="uv_installation",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
    
    def validate_dependency_resolution(self) -> ValidationResult:
        """Validate that all dependencies can be resolved."""
        pyproject_path = self.project_root / 'pyproject.toml'
        uv_lock_path = self.project_root / 'uv.lock'
        
        if not pyproject_path.exists():
            return ValidationResult(
                name="dependency_resolution",
                passed=False,
                message="pyproject.toml not found",
                details={'pyproject_path': str(pyproject_path)},
                timestamp=datetime.now()
            )
        
        # Check if uv.lock exists and is recent
        lock_exists = uv_lock_path.exists()
        lock_recent = False
        
        if lock_exists:
            lock_mtime = uv_lock_path.stat().st_mtime
            pyproject_mtime = pyproject_path.stat().st_mtime
            lock_recent = lock_mtime >= pyproject_mtime
        
        # Try to resolve dependencies
        try:
            result = subprocess.run(
                ['uv', 'lock', '--dry-run'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            resolution_success = result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            resolution_success = False
            result = type('MockResult', (), {
                'stderr': str(e),
                'stdout': '',
                'returncode': -1
            })()
        
        passed = resolution_success and lock_exists
        
        details = {
            'lock_file_exists': lock_exists,
            'lock_file_recent': lock_recent,
            'resolution_success': resolution_success,
            'resolution_output': result.stdout[:300] if hasattr(result, 'stdout') and result.stdout else '',
            'resolution_error': result.stderr[:300] if hasattr(result, 'stderr') and result.stderr else ''
        }
        
        if passed:
            message = "All dependencies resolve successfully"
        else:
            issues = []
            if not lock_exists:
                issues.append("uv.lock missing")
            if not resolution_success:
                issues.append("dependency resolution failed")
            message = f"Dependency issues: {', '.join(issues)}"
        
        return ValidationResult(
            name="dependency_resolution",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )


class ComprehensiveValidator:
    """Main validation system that orchestrates all validation checks."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Initialize validators
        self.structure_validator = ProjectStructureValidator(project_root)
        self.classification_validator = FileClassificationValidator(project_root)
        self.documentation_validator = DocumentationValidator(project_root)
        self.installation_validator = InstallationValidator(project_root)
    
    def run_all_validations(self) -> ValidationReport:
        """Run all validation checks and generate comprehensive report."""
        self.logger.info(f"Starting comprehensive validation for {self.project_root}")
        
        results = []
        
        # Project structure validations
        self.logger.info("Running project structure validations...")
        results.append(self.structure_validator.validate_core_structure())
        results.append(self.structure_validator.validate_package_structure())
        results.append(self.structure_validator.validate_test_organization())
        results.append(self.structure_validator.validate_cleanup_completeness())
        
        # File classification validations
        self.logger.info("Running file classification validations...")
        results.append(self.classification_validator.validate_classification_accuracy())
        results.append(self.classification_validator.validate_essential_file_protection())
        
        # Documentation validations
        self.logger.info("Running documentation validations...")
        results.append(self.documentation_validator.validate_readme_completeness())
        results.append(self.documentation_validator.validate_project_metadata())
        
        # Installation validations
        self.logger.info("Running installation validations...")
        results.append(self.installation_validator.validate_dependency_resolution())
        # Note: UV installation test is optional and may be skipped in CI environments
        try:
            results.append(self.installation_validator.validate_uv_installation())
        except Exception as e:
            self.logger.warning(f"Skipping UV installation test: {e}")
            results.append(ValidationResult(
                name="uv_installation",
                passed=False,
                message=f"UV installation test skipped: {e}",
                details={'skipped': True, 'reason': str(e)},
                timestamp=datetime.now()
            ))
        
        # Calculate overall result
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        overall_passed = passed_count == total_count
        
        # Generate summary
        summary = {
            'total_validations': total_count,
            'passed_validations': passed_count,
            'failed_validations': total_count - passed_count,
            'success_rate': passed_count / total_count if total_count > 0 else 0,
            'validation_categories': {
                'structure': sum(1 for r in results if r.name.startswith(('core_', 'package_', 'test_', 'cleanup_')) and r.passed),
                'classification': sum(1 for r in results if r.name.startswith(('classification_', 'essential_')) and r.passed),
                'documentation': sum(1 for r in results if r.name.startswith(('readme_', 'project_')) and r.passed),
                'installation': sum(1 for r in results if r.name.startswith(('dependency_', 'uv_')) and r.passed)
            }
        }
        
        self.logger.info(f"Validation complete: {passed_count}/{total_count} checks passed")
        
        return ValidationReport(
            project_root=str(self.project_root),
            validation_time=datetime.now(),
            overall_passed=overall_passed,
            results=results,
            summary=summary
        )
    
    def validate_workflow_integration(self, github_prep: GitHubPreparation) -> ValidationResult:
        """Validate integration with GitHub preparation workflow."""
        try:
            # Test workflow analysis
            analysis_results = github_prep.analyze_project()
            
            # Check that analysis completed successfully
            analysis_success = (
                'total_files' in analysis_results and
                'files_by_action' in analysis_results and
                analysis_results['total_files'] > 0
            )
            
            # Test workflow state
            state_valid = (
                github_prep.workflow_state.total_files_analyzed > 0 and
                len(github_prep.workflow_state.steps) > 0
            )
            
            # Test safety validation
            mock_operations = []  # Empty operations for safety test
            safety_report = github_prep._validate_operation_safety(mock_operations)
            safety_valid = 'is_safe' in safety_report
            
            passed = analysis_success and state_valid and safety_valid
            
            details = {
                'analysis_success': analysis_success,
                'state_valid': state_valid,
                'safety_valid': safety_valid,
                'total_files_analyzed': github_prep.workflow_state.total_files_analyzed,
                'workflow_steps': len(github_prep.workflow_state.steps)
            }
            
            message = ("Workflow integration successful" if passed 
                      else "Workflow integration issues detected")
            
        except Exception as e:
            passed = False
            message = f"Workflow integration test failed: {e}"
            details = {'error': str(e)}
        
        return ValidationResult(
            name="workflow_integration",
            passed=passed,
            message=message,
            details=details,
            timestamp=datetime.now()
        )


def main():
    """Main function for running validation system."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Preparation Validation System')
    parser.add_argument('project_root', help='Path to project root directory')
    parser.add_argument('--output', '-o', help='Output file for validation report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run validation
    validator = ComprehensiveValidator(args.project_root)
    report = validator.run_all_validations()
    
    # Print summary
    print(f"\nValidation Results for {report.project_root}")
    print(f"Overall Status: {'PASSED' if report.overall_passed else 'FAILED'}")
    print(f"Success Rate: {report.summary['success_rate']:.1%}")
    print(f"Passed: {report.summary['passed_validations']}/{report.summary['total_validations']}")
    
    print("\nDetailed Results:")
    for result in report.results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.name}: {result.message}")
    
    # Save report if requested
    if args.output:
        report.save_to_file(args.output)
        print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if report.overall_passed else 1)


if __name__ == "__main__":
    main()