"""
Tests for the GitHubPreparation comprehensive workflow.

This module tests the main GitHubPreparation class that orchestrates all cleanup operations,
including safety checks, validation, progress reporting, and rollback mechanisms.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation import (
    GitHubPreparation, WorkflowStep, WorkflowState,
    FileClassifier, FileInfo, FileType, FileAction
)


class TestGitHubPreparation:
    """Test cases for GitHubPreparation class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create basic project structure
        (project_path / 'indextts').mkdir()
        (project_path / 'indextts' / '__init__.py').touch()
        (project_path / 'indextts' / 'infer_v2.py').touch()
        (project_path / 'webui.py').touch()
        (project_path / 'pyproject.toml').write_text("""
[project]
name = "indextts"
version = "1.0.0"
description = "Test project"
""")
        (project_path / '.gitignore').touch()
        (project_path / '.gitattributes').touch()
        
        # Create some test files
        (project_path / 'test_example.py').touch()
        (project_path / 'debug_output.wav').touch()
        (project_path / 'temp_file.tmp').touch()
        
        # Create directories
        (project_path / 'tests').mkdir()
        (project_path / 'outputs').mkdir()
        (project_path / 'logs').mkdir()
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def github_prep(self, temp_project):
        """Create GitHubPreparation instance for testing."""
        prep = GitHubPreparation(
            project_root=str(temp_project),
            dry_run=True,  # Always use dry run in tests
            backup_enabled=False  # Disable backup in tests
        )
        yield prep
        # Cleanup to prevent file handle issues
        prep.cleanup()
    
    def test_initialization(self, temp_project):
        """Test GitHubPreparation initialization."""
        github_prep = GitHubPreparation(
            project_root=str(temp_project),
            dry_run=True,
            backup_enabled=False
        )
        
        assert github_prep.project_root == temp_project
        assert github_prep.dry_run is True
        assert github_prep.backup_enabled is False
        assert isinstance(github_prep.file_classifier, FileClassifier)
        assert github_prep.workflow_state.project_root == str(temp_project)
    
    def test_validate_project_structure_valid(self, github_prep):
        """Test project structure validation with valid project."""
        is_valid, issues = github_prep.validate_project_structure()
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_project_structure_invalid(self, temp_project):
        """Test project structure validation with invalid project."""
        # Remove required file
        (temp_project / 'webui.py').unlink()
        
        github_prep = GitHubPreparation(
            project_root=str(temp_project),
            dry_run=True,
            backup_enabled=False
        )
        
        is_valid, issues = github_prep.validate_project_structure()
        
        assert is_valid is False
        assert len(issues) > 0
        assert any('webui.py' in issue for issue in issues)
    
    def test_progress_callback(self, github_prep):
        """Test progress callback functionality."""
        progress_calls = []
        
        def mock_callback(step_name, progress, message):
            progress_calls.append((step_name, progress, message))
        
        github_prep.set_progress_callback(mock_callback)
        github_prep._report_progress("Test", 50.0, "Test message")
        
        assert len(progress_calls) == 1
        assert progress_calls[0] == ("Test", 50.0, "Test message")
    
    def test_analyze_project(self, github_prep):
        """Test project analysis functionality."""
        analysis_results = github_prep.analyze_project()
        
        assert 'total_files' in analysis_results
        assert 'files_by_action' in analysis_results
        assert 'files_by_type' in analysis_results
        assert 'planned_operations' in analysis_results
        assert 'classification_report' in analysis_results
        assert 'safety_report' in analysis_results
        
        # Check that files were analyzed
        assert analysis_results['total_files'] > 0
        
        # Check workflow state was updated
        assert github_prep.workflow_state.total_files_analyzed > 0
        assert len(github_prep.workflow_state.steps) > 0
    
    def test_validate_operation_safety(self, github_prep):
        """Test operation safety validation."""
        # Create mock operations
        mock_operations = [
            Mock(action=FileAction.DELETE, source_path="test_file.tmp"),
            Mock(action=FileAction.RELOCATE, source_path="test_example.py"),
        ]
        
        github_prep.workflow_state.total_files_analyzed = 10
        safety_report = github_prep._validate_operation_safety(mock_operations)
        
        assert 'is_safe' in safety_report
        assert 'warnings' in safety_report
        assert 'errors' in safety_report
        assert 'statistics' in safety_report
        
        # Should be safe with small number of operations
        assert safety_report['is_safe'] is True
    
    def test_validate_operation_safety_unsafe(self, github_prep):
        """Test operation safety validation with unsafe operations."""
        # Create many delete operations to exceed threshold
        mock_operations = [
            Mock(action=FileAction.DELETE, source_path=f"file_{i}.tmp")
            for i in range(150)  # Exceeds max_delete_count threshold
        ]
        
        github_prep.workflow_state.total_files_analyzed = 200
        safety_report = github_prep._validate_operation_safety(mock_operations)
        
        assert safety_report['is_safe'] is False
        assert len(safety_report['errors']) > 0
    
    @patch('indextts.github_preparation.github_preparation.GitHubPreparation._update_version_info')
    @patch('indextts.github_preparation.github_preparation.GitHubPreparation._generate_documentation')
    @patch('indextts.github_preparation.github_preparation.GitHubPreparation._update_gitignore')
    def test_execute_cleanup_workflow(self, mock_gitignore, mock_docs, mock_version, github_prep):
        """Test complete workflow execution."""
        # Mock the component methods
        mock_version.return_value = {'old_version': '1.0.0', 'new_version': '1.0.1'}
        mock_docs.return_value = {'updated_files': ['README.md']}
        mock_gitignore.return_value = {'added_patterns': ['*.log']}
        
        # Execute workflow
        results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        
        assert results['success'] is True
        assert 'analysis_results' in results
        assert 'cleanup_results' in results
        assert 'workflow_state' in results
        
        # Check that workflow state was updated
        assert github_prep.workflow_state.end_time is not None
        assert github_prep.workflow_state.rollback_available is True
    
    def test_workflow_step_tracking(self, github_prep):
        """Test that workflow steps are properly tracked."""
        # Execute analysis to create workflow steps
        github_prep.analyze_project()
        
        assert len(github_prep.workflow_state.steps) > 0
        
        step = github_prep.workflow_state.steps[0]
        assert isinstance(step, WorkflowStep)
        assert step.name == "analyze_project"
        assert step.completed is True
        assert step.start_time is not None
        assert step.end_time is not None
    
    def test_generate_workflow_report(self, github_prep):
        """Test workflow report generation."""
        # Execute some operations to populate workflow state
        github_prep.analyze_project()
        
        report = github_prep.generate_workflow_report()
        
        assert isinstance(report, str)
        assert "GitHub Preparation Workflow Report" in report
        assert str(github_prep.project_root) in report
        assert "Summary" in report
        assert "Workflow Steps" in report
    
    def test_save_workflow_state(self, github_prep, temp_project):
        """Test workflow state saving."""
        # Execute some operations to populate workflow state
        github_prep.analyze_project()
        
        # Save state
        state_file = github_prep.save_workflow_state()
        
        assert Path(state_file).exists()
        assert state_file.endswith('.json')
        
        # Verify file content
        import json
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        assert 'project_root' in state_data
        assert 'start_time' in state_data
        assert 'steps' in state_data
    
    def test_rollback_changes(self, github_prep):
        """Test rollback functionality."""
        # Mock some completed operations
        github_prep.safe_file_manager.completed_operations = [
            Mock(action=FileAction.RELOCATE, source_path="test.py", target_path="tests/test.py")
        ]
        
        with patch.object(github_prep.safe_file_manager, 'rollback_operations') as mock_rollback:
            mock_rollback.return_value = {'total': 1, 'completed': 1, 'failed': 0}
            
            results = github_prep.rollback_changes()
            
            assert results['success'] is True
            assert 'file_operations' in results
            assert 'limitations' in results
            mock_rollback.assert_called_once()
    
    def test_error_handling_in_workflow(self, github_prep):
        """Test error handling during workflow execution."""
        # Mock a component to raise an exception
        with patch.object(github_prep.file_classifier, 'scan_project') as mock_scan:
            mock_scan.side_effect = Exception("Test error")
            
            with pytest.raises(Exception, match="Test error"):
                github_prep.analyze_project()
            
            # Check that error was recorded in workflow state
            assert len(github_prep.workflow_state.steps) > 0
            step = github_prep.workflow_state.steps[-1]
            assert step.error is not None
            assert "Test error" in step.error
    
    def test_dry_run_mode(self, github_prep):
        """Test that dry run mode prevents actual file operations."""
        assert github_prep.dry_run is True
        assert github_prep.safe_file_manager.dry_run is True
        
        # Execute workflow - should not modify any files
        results = github_prep.execute_cleanup_workflow(skip_confirmation=True)
        
        # Should complete successfully without modifying files
        assert results['success'] is True
    
    def test_backup_creation_disabled(self, github_prep):
        """Test backup creation when disabled."""
        assert github_prep.backup_enabled is False
        
        backup_path = github_prep.create_backup()
        
        assert backup_path is None
    
    def test_backup_creation_enabled(self, temp_project):
        """Test backup creation when enabled."""
        github_prep = GitHubPreparation(
            project_root=str(temp_project),
            dry_run=True,
            backup_enabled=True
        )
        
        backup_path = github_prep.create_backup()
        
        # In dry run mode, backup should still be created
        assert backup_path is not None
        # Note: In dry run mode, files aren't actually copied


class TestWorkflowStep:
    """Test cases for WorkflowStep dataclass."""
    
    def test_workflow_step_creation(self):
        """Test WorkflowStep creation and initialization."""
        step = WorkflowStep(
            name="test_step",
            description="Test step description"
        )
        
        assert step.name == "test_step"
        assert step.description == "Test step description"
        assert step.completed is False
        assert step.error is None
        assert step.start_time is None
        assert step.end_time is None
        assert step.details == {}
    
    def test_workflow_step_with_details(self):
        """Test WorkflowStep with custom details."""
        details = {"files_processed": 10, "errors": 0}
        step = WorkflowStep(
            name="test_step",
            description="Test step",
            details=details
        )
        
        assert step.details == details


class TestWorkflowState:
    """Test cases for WorkflowState dataclass."""
    
    def test_workflow_state_creation(self):
        """Test WorkflowState creation and initialization."""
        start_time = datetime.now()
        state = WorkflowState(
            project_root="/test/path",
            start_time=start_time
        )
        
        assert state.project_root == "/test/path"
        assert state.start_time == start_time
        assert state.end_time is None
        assert state.steps == []
        assert state.total_files_analyzed == 0
        assert state.operations_planned == 0
        assert state.operations_completed == 0
        assert state.operations_failed == 0
        assert state.rollback_available is False


if __name__ == "__main__":
    pytest.main([__file__])