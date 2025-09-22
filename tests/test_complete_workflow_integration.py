"""
Integration tests for the complete GitHub preparation cleanup workflow.

This module tests the end-to-end workflow including file analysis, cleanup operations,
documentation generation, and final validation.
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

from indextts.github_preparation import (
    GitHubPreparation, FileClassifier, SafeFileManager,
    VersionManager, DocumentationGenerator, GitIgnoreManager,
    MetadataManager
)
from indextts.github_preparation.validation_system import (
    ComprehensiveValidator, ValidationReport
)


class TestCompleteWorkflowIntegration:
    """Integration tests for complete GitHub preparation workflow."""
    
    @pytest.fixture
    def realistic_project(self):
        """Create a realistic project structure with various issues to clean up."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create basic project files
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
        (project_path / 'webui.py').write_text('# Web UI entry point\nprint("WebUI")')
        (project_path / '.gitignore').write_text('__pycache__/\n*.pyc')
        (project_path / '.gitattributes').touch()
        
        # Create indextts package structure
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        (indextts_dir / '__init__.py').write_text('"""IndexTTS2 package."""\n__version__ = "1.0.0"')
        (indextts_dir / 'infer_v2.py').write_text('# IndexTTS2 inference\nclass IndexTTS2: pass')
        (indextts_dir / 'cli.py').write_text('# CLI interface\ndef main(): pass')
        
        # Create subpackages
        for subpkg in ['gpt', 's2mel', 'vqvae', 'BigVGAN', 'utils']:
            subdir = indextts_dir / subpkg
            subdir.mkdir()
            (subdir / '__init__.py').write_text(f'# {subpkg} module')
            if subpkg == 'utils':
                (subdir / 'audio.py').write_text('# Audio utilities')
                (subdir / 'text.py').write_text('# Text utilities')
        
        # Create directories
        (project_path / 'tests').mkdir()
        (project_path / 'checkpoints').mkdir()
        (project_path / 'examples').mkdir()
        (project_path / 'docs').mkdir()
        (project_path / 'assets').mkdir()
        
        # Create checkpoints config
        (project_path / 'checkpoints' / 'config.yaml').write_text("""
model:
  name: IndexTTS2
  version: 2.0
""")
        
        # Create example files
        examples_dir = project_path / 'examples'
        for i in range(1, 4):
            (examples_dir / f'voice_{i:02d}.wav').touch()
        (examples_dir / 'cases.jsonl').write_text('{"text": "Hello", "voice": "voice_01.wav"}')
        
        # Create proper test files in tests directory
        tests_dir = project_path / 'tests'
        (tests_dir / '__init__.py').touch()
        (tests_dir / 'test_file_classifier.py').write_text('# Test file classifier')
        (tests_dir / 'test_safe_file_manager.py').write_text('# Test safe file manager')
        
        # Create files that need cleanup (problematic files)
        cleanup_files = [
            'debug_output.wav',
            'test_output.wav', 
            'debug_script.py',
            'temp_file.tmp',
            'old_backup.bak',
            'test_root_level.py',  # Should be moved to tests/
            'example_test.py',     # Should be moved to tests/
        ]
        
        for filename in cleanup_files:
            (project_path / filename).write_text(f'# {filename} - should be cleaned up')
        
        # Create unwanted directories
        (project_path / '__pycache__').mkdir()
        (project_path / '__pycache__' / 'module.pyc').touch()
        
        cache_dir = project_path / '.pytest_cache'
        cache_dir.mkdir()
        (cache_dir / 'cache.json').write_text('{}')
        
        # Create logs directory with log files
        logs_dir = project_path / 'logs'
        logs_dir.mkdir()
        (logs_dir / 'debug.log').write_text('Debug log content')
        (logs_dir / 'error.log').write_text('Error log content')
        
        # Create outputs directory (should be preserved but empty)
        outputs_dir = project_path / 'outputs'
        outputs_dir.mkdir()
        (outputs_dir / 'generated_audio.wav').write_text('# Generated audio file')
        
        # Create basic README that needs updating
        (project_path / 'README.md').write_text("""
# IndexTTS2

Basic project description.

## Installation

pip install -e .

## Usage

python webui.py
""")
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_workflow_analysis_phase(self, realistic_project):
        """Test the analysis phase of the workflow."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Run analysis
        analysis_results = github_prep.analyze_project()
        
        # Verify analysis results structure
        assert 'total_files' in analysis_results
        assert 'files_by_action' in analysis_results
        assert 'files_by_type' in analysis_results
        assert 'planned_operations' in analysis_results
        assert 'classification_report' in analysis_results
        assert 'safety_report' in analysis_results
        
        # Should have found files to process
        assert analysis_results['total_files'] > 0
        
        # Should have identified files for different actions
        files_by_action = analysis_results['files_by_action']
        assert 'DELETE' in files_by_action or 'RELOCATE' in files_by_action
        
        # Should have identified different file types
        files_by_type = analysis_results['files_by_type']
        assert len(files_by_type) > 0
        
        # Safety report should indicate operations are safe
        safety_report = analysis_results['safety_report']
        assert 'is_safe' in safety_report
        
        # Workflow state should be updated
        assert github_prep.workflow_state.total_files_analyzed > 0
        assert len(github_prep.workflow_state.steps) > 0
        
        # Should have found problematic files
        planned_ops = analysis_results['planned_operations']
        delete_ops = [op for op in planned_ops if op.action.name == 'DELETE']
        relocate_ops = [op for op in planned_ops if op.action.name == 'RELOCATE']
        
        # Should have files to delete (debug, temp files)
        assert len(delete_ops) > 0
        
        # Should have test files to relocate
        assert len(relocate_ops) > 0
    
    @patch('indextts.github_preparation.safe_file_manager.send2trash')
    def test_workflow_cleanup_phase(self, mock_send2trash, realistic_project):
        """Test the cleanup phase of the workflow."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=False,  # Allow actual operations for this test
            backup_enabled=False
        )
        
        # Mock send2trash to prevent actual deletion
        mock_send2trash.return_value = None
        
        # Run analysis first
        analysis_results = github_prep.analyze_project()
        
        # Execute cleanup operations
        cleanup_results = github_prep._execute_file_operations(
            analysis_results['planned_operations']
        )
        
        # Verify cleanup results
        assert 'operations_completed' in cleanup_results
        assert 'operations_failed' in cleanup_results
        assert 'total_operations' in cleanup_results
        
        # Should have completed some operations
        assert cleanup_results['operations_completed'] >= 0
        
        # Should have low failure rate
        if cleanup_results['total_operations'] > 0:
            failure_rate = cleanup_results['operations_failed'] / cleanup_results['total_operations']
            assert failure_rate <= 0.1  # Less than 10% failure rate
        
        # Verify that send2trash was called for delete operations
        delete_ops = [op for op in analysis_results['planned_operations'] 
                     if op.action.name == 'DELETE']
        if delete_ops:
            assert mock_send2trash.called
    
    def test_workflow_documentation_phase(self, realistic_project):
        """Test the documentation generation phase."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Test documentation generation
        doc_results = github_prep._generate_documentation()
        
        # Verify documentation results
        assert 'updated_files' in doc_results
        assert 'readme_updated' in doc_results
        assert 'system_docs_created' in doc_results
        
        # Should have updated README
        assert doc_results['readme_updated'] is True
        
        # Check that README was actually updated
        readme_path = realistic_project / 'README.md'
        readme_content = readme_path.read_text(encoding='utf-8')
        
        # Should contain UV installation instructions
        assert 'uv sync' in readme_content or 'uv run' in readme_content
        
        # Should contain bilingual content indicators
        assert '中文' in readme_content or 'Chinese' in readme_content
    
    def test_workflow_version_management_phase(self, realistic_project):
        """Test the version management phase."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Test version update
        version_results = github_prep._update_version_info()
        
        # Verify version results
        assert 'old_version' in version_results
        assert 'new_version' in version_results
        assert 'version_updated' in version_results
        
        # Should have updated version
        assert version_results['version_updated'] is True
        assert version_results['old_version'] != version_results['new_version']
        
        # New version should include current date
        new_version = version_results['new_version']
        current_year = str(datetime.now().year)
        assert current_year in new_version
    
    def test_workflow_gitignore_phase(self, realistic_project):
        """Test the .gitignore update phase."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Test gitignore update
        gitignore_results = github_prep._update_gitignore()
        
        # Verify gitignore results
        assert 'added_patterns' in gitignore_results
        assert 'updated_gitignore' in gitignore_results
        
        # Should have added patterns
        assert len(gitignore_results['added_patterns']) > 0
        
        # Check that .gitignore was updated
        gitignore_path = realistic_project / '.gitignore'
        gitignore_content = gitignore_path.read_text()
        
        # Should contain important patterns
        expected_patterns = ['outputs/', 'logs/', '*.log', '__pycache__/']
        for pattern in expected_patterns:
            assert pattern in gitignore_content
    
    def test_complete_workflow_execution(self, realistic_project):
        """Test complete end-to-end workflow execution."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Execute complete workflow
        results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        
        # Verify overall results
        assert results['success'] is True
        assert 'analysis_results' in results
        assert 'cleanup_results' in results
        assert 'documentation_results' in results
        assert 'version_results' in results
        assert 'gitignore_results' in results
        assert 'workflow_state' in results
        
        # Verify workflow state
        workflow_state = results['workflow_state']
        assert workflow_state['total_files_analyzed'] > 0
        assert workflow_state['operations_planned'] >= 0
        assert len(workflow_state['steps']) > 0
        
        # All major steps should be completed
        step_names = [step['name'] for step in workflow_state['steps']]
        expected_steps = [
            'analyze_project',
            'execute_file_operations', 
            'generate_documentation',
            'update_version_info',
            'update_gitignore'
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_names
        
        # All steps should be completed successfully
        for step in workflow_state['steps']:
            assert step['completed'] is True
            assert step['error'] is None
    
    def test_workflow_with_validation(self, realistic_project):
        """Test workflow execution followed by comprehensive validation."""
        # Execute workflow
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        workflow_results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        assert workflow_results['success'] is True
        
        # Run comprehensive validation
        validator = ComprehensiveValidator(str(realistic_project))
        validation_report = validator.run_all_validations()
        
        # Verify validation report structure
        assert isinstance(validation_report, ValidationReport)
        assert validation_report.project_root == str(realistic_project)
        assert len(validation_report.results) > 0
        
        # Check validation categories
        summary = validation_report.summary
        assert 'total_validations' in summary
        assert 'passed_validations' in summary
        assert 'validation_categories' in summary
        
        # Should have reasonable success rate
        success_rate = summary['success_rate']
        assert success_rate >= 0.5  # At least 50% should pass
        
        # Test workflow integration validation
        integration_result = validator.validate_workflow_integration(github_prep)
        assert integration_result.passed is True
        assert integration_result.name == "workflow_integration"
    
    def test_workflow_error_handling(self, realistic_project):
        """Test workflow error handling and recovery."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Test with invalid project root
        invalid_prep = GitHubPreparation(
            project_root="/nonexistent/path",
            dry_run=True,
            backup_enabled=False
        )
        
        # Should handle invalid project gracefully
        with pytest.raises(Exception):
            invalid_prep.analyze_project()
        
        # Test error recording in workflow state
        assert len(invalid_prep.workflow_state.steps) > 0
        error_step = invalid_prep.workflow_state.steps[-1]
        assert error_step.error is not None
    
    def test_workflow_rollback_functionality(self, realistic_project):
        """Test workflow rollback functionality."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Execute workflow to create operations to rollback
        workflow_results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        assert workflow_results['success'] is True
        
        # Test rollback
        rollback_results = github_prep.rollback_changes()
        
        # Verify rollback results
        assert 'success' in rollback_results
        assert 'file_operations' in rollback_results
        assert 'limitations' in rollback_results
        
        # In dry run mode, rollback should indicate limitations
        assert len(rollback_results['limitations']) > 0
    
    def test_workflow_state_persistence(self, realistic_project):
        """Test workflow state saving and loading."""
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Execute workflow
        workflow_results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        assert workflow_results['success'] is True
        
        # Save workflow state
        state_file = github_prep.save_workflow_state()
        assert Path(state_file).exists()
        
        # Verify state file content
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        assert 'project_root' in state_data
        assert 'start_time' in state_data
        assert 'steps' in state_data
        assert 'total_files_analyzed' in state_data
        
        # Should have recorded all workflow steps
        assert len(state_data['steps']) > 0
        
        # Generate workflow report
        report = github_prep.generate_workflow_report()
        assert isinstance(report, str)
        assert "GitHub Preparation Workflow Report" in report
        assert str(realistic_project) in report
    
    @patch('subprocess.run')
    def test_workflow_with_uv_validation(self, mock_run, realistic_project):
        """Test workflow with UV installation validation."""
        # Mock UV commands to simulate successful installation
        def mock_subprocess(cmd, **kwargs):
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                return Mock(returncode=0, stdout="Dependencies synced", stderr="")
            elif cmd[0:2] == ['uv', 'lock']:
                return Mock(returncode=0, stdout="Dependencies locked", stderr="")
            elif 'cli.py' in ' '.join(cmd):
                return Mock(returncode=0, stdout="CLI Help", stderr="")
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        # Execute workflow
        github_prep = GitHubPreparation(
            project_root=str(realistic_project),
            dry_run=True,
            backup_enabled=False
        )
        
        workflow_results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        assert workflow_results['success'] is True
        
        # Run validation including UV tests
        validator = ComprehensiveValidator(str(realistic_project))
        validation_report = validator.run_all_validations()
        
        # Find UV-related validation results
        uv_results = [r for r in validation_report.results 
                     if r.name in ['dependency_resolution', 'uv_installation']]
        
        # Should have UV validation results
        assert len(uv_results) > 0
        
        # UV validations should pass with mocked commands
        for result in uv_results:
            if not result.details.get('skipped', False):
                assert result.passed is True


class TestWorkflowPerformance:
    """Performance and scalability tests for the workflow."""
    
    @pytest.fixture
    def large_project(self):
        """Create a larger project structure for performance testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create basic structure
        (project_path / 'pyproject.toml').write_text('[project]\nname="test"\nversion="1.0.0"')
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
        
        # Create many files to test performance
        tests_dir = project_path / 'tests'
        tests_dir.mkdir()
        
        # Create 100 test files
        for i in range(100):
            (tests_dir / f'test_module_{i:03d}.py').write_text(f'# Test module {i}')
        
        # Create many temporary files
        for i in range(50):
            (project_path / f'debug_file_{i:03d}.tmp').touch()
            (project_path / f'temp_output_{i:03d}.wav').touch()
        
        # Create nested directory structure
        for i in range(10):
            nested_dir = project_path / f'nested_{i}'
            nested_dir.mkdir()
            for j in range(10):
                (nested_dir / f'file_{j}.py').touch()
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    def test_workflow_performance_large_project(self, large_project):
        """Test workflow performance with large project."""
        import time
        
        github_prep = GitHubPreparation(
            project_root=str(large_project),
            dry_run=True,
            backup_enabled=False
        )
        
        # Measure analysis time
        start_time = time.time()
        analysis_results = github_prep.analyze_project()
        analysis_time = time.time() - start_time
        
        # Should complete analysis in reasonable time (< 30 seconds)
        assert analysis_time < 30.0
        
        # Should have analyzed many files
        assert analysis_results['total_files'] > 100
        
        # Measure complete workflow time
        start_time = time.time()
        workflow_results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        workflow_time = time.time() - start_time
        
        # Should complete workflow in reasonable time (< 60 seconds)
        assert workflow_time < 60.0
        assert workflow_results['success'] is True
    
    def test_validation_performance_large_project(self, large_project):
        """Test validation performance with large project."""
        import time
        
        validator = ComprehensiveValidator(str(large_project))
        
        # Measure validation time
        start_time = time.time()
        validation_report = validator.run_all_validations()
        validation_time = time.time() - start_time
        
        # Should complete validation in reasonable time (< 30 seconds)
        assert validation_time < 30.0
        
        # Should have run all validations
        assert len(validation_report.results) > 0
        assert validation_report.summary['total_validations'] > 0


if __name__ == "__main__":
    pytest.main([__file__])