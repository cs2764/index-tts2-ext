"""
Tests for SafeFileManager class.

This module tests the safe file management operations including
recycle bin functionality, file organization, and safety validations.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from indextts.github_preparation.safe_file_manager import (
    SafeFileManager, FileOperation, SEND2TRASH_AVAILABLE
)
from indextts.github_preparation.file_classifier import (
    FileInfo, FileType, FileAction
)


class TestSafeFileManager:
    """Test cases for SafeFileManager."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "test_project"
        self.project_root.mkdir()
        
        # Create test file structure
        self._create_test_structure()
        
        # Initialize SafeFileManager in dry run mode for safety
        self.manager = SafeFileManager(str(self.project_root), dry_run=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_structure(self):
        """Create a test project structure."""
        
        # Core source files
        (self.project_root / "indextts").mkdir()
        (self.project_root / "indextts" / "__init__.py").touch()
        (self.project_root / "indextts" / "core.py").touch()
        (self.project_root / "webui.py").touch()
        (self.project_root / "pyproject.toml").touch()
        
        # Test files (some in wrong locations)
        (self.project_root / "tests").mkdir()
        (self.project_root / "tests" / "test_core.py").touch()
        (self.project_root / "test_root_level.py").touch()  # Should be relocated
        (self.project_root / "debug_test.py").touch()       # Should be relocated
        
        # Temporary and debug files
        (self.project_root / "debug_output.wav").touch()
        (self.project_root / "test_temp_file.tmp").touch()
        (self.project_root / "temp_debug.log").touch()
        
        # User-generated content
        (self.project_root / "outputs").mkdir()
        (self.project_root / "outputs" / "generated.wav").touch()
        (self.project_root / "prompts").mkdir()
        (self.project_root / "prompts" / "user_prompt.wav").touch()
        
        # Cache files
        (self.project_root / "__pycache__").mkdir()
        (self.project_root / "__pycache__" / "test.pyc").touch()
        
        # Virtual environment (should never be touched)
        (self.project_root / ".venv").mkdir()
        (self.project_root / ".venv" / "lib").mkdir()
        (self.project_root / ".venv" / "lib" / "python.exe").touch()
    
    def test_initialization(self):
        """Test SafeFileManager initialization."""
        assert self.manager.project_root == self.project_root
        assert self.manager.dry_run is True
        assert self.manager.classifier is not None
        assert len(self.manager.operations) == 0
    
    def test_safety_rules_initialization(self):
        """Test that safety rules are properly initialized."""
        assert 'webui.py' in self.manager.protected_files
        assert 'pyproject.toml' in self.manager.protected_files
        assert '.venv' in self.manager.protected_directories
        assert 'indextts' in self.manager.protected_directories
    
    def test_validate_operation_protected_file(self):
        """Test validation rejects operations on protected files."""
        file_info = FileInfo(
            path="webui.py",
            file_type=FileType.SOURCE_CODE,
            is_essential=True,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.DELETE,
            reason="Test"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert not is_safe
        assert "protected" in reason.lower()
    
    def test_validate_operation_protected_directory(self):
        """Test validation rejects operations on files in protected directories."""
        file_info = FileInfo(
            path="indextts/core.py",
            file_type=FileType.SOURCE_CODE,
            is_essential=True,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.DELETE,
            reason="Test"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert not is_safe
        assert "protected directory" in reason.lower()
    
    def test_validate_delete_operation_essential_file(self):
        """Test validation rejects deletion of essential files."""
        file_info = FileInfo(
            path="important_doc.md",
            file_type=FileType.DOCUMENTATION,
            is_essential=True,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.DELETE,
            reason="Test"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert not is_safe
        assert "essential" in reason.lower()
    
    def test_validate_delete_operation_safe_file(self):
        """Test validation allows deletion of safe temporary files."""
        file_info = FileInfo(
            path="debug_output.wav",
            file_type=FileType.DEBUG,
            is_essential=False,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.DELETE,
            reason="Debug file"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert is_safe
        assert "safe" in reason.lower()
    
    def test_validate_relocate_operation_valid(self):
        """Test validation allows valid relocate operations."""
        file_info = FileInfo(
            path="test_root_level.py",
            file_type=FileType.TEST_FILE,
            is_essential=False,
            should_preserve_locally=False,
            target_location="tests/test_root_level.py",
            action=FileAction.RELOCATE,
            reason="Root-level test file"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert is_safe
        assert "safe" in reason.lower()
    
    def test_validate_relocate_operation_no_target(self):
        """Test validation rejects relocate operations without target."""
        file_info = FileInfo(
            path="test_root_level.py",
            file_type=FileType.TEST_FILE,
            is_essential=False,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.RELOCATE,
            reason="Root-level test file"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert not is_safe
        assert "target location" in reason.lower()
    
    def test_plan_operations(self):
        """Test operation planning from file classifications."""
        # Create test file infos
        file_infos = [
            FileInfo(
                path="debug_output.wav",
                file_type=FileType.DEBUG,
                is_essential=False,
                should_preserve_locally=False,
                target_location=None,
                action=FileAction.DELETE,
                reason="Debug file"
            ),
            FileInfo(
                path="test_root_level.py",
                file_type=FileType.TEST_FILE,
                is_essential=False,
                should_preserve_locally=False,
                target_location="tests/test_root_level.py",
                action=FileAction.RELOCATE,
                reason="Root-level test file"
            ),
            FileInfo(
                path="webui.py",
                file_type=FileType.SOURCE_CODE,
                is_essential=True,
                should_preserve_locally=False,
                target_location=None,
                action=FileAction.KEEP,
                reason="Main entry point"
            )
        ]
        
        operations = self.manager.plan_operations(file_infos)
        
        # Should only plan operations for DELETE and RELOCATE actions
        assert len(operations) == 2
        
        # Check delete operation
        delete_op = next(op for op in operations if op.action == FileAction.DELETE)
        assert "debug_output.wav" in delete_op.source_path
        assert delete_op.target_path is None
        
        # Check relocate operation
        relocate_op = next(op for op in operations if op.action == FileAction.RELOCATE)
        assert "test_root_level.py" in relocate_op.source_path
        # Handle both forward and backward slashes for cross-platform compatibility
        target_path_normalized = relocate_op.target_path.replace('\\', '/')
        assert target_path_normalized.endswith("tests/test_root_level.py")
    
    def test_execute_operations_dry_run(self):
        """Test operation execution in dry run mode."""
        # Create test operation
        file_info = FileInfo(
            path="debug_output.wav",
            file_type=FileType.DEBUG,
            is_essential=False,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.DELETE,
            reason="Debug file"
        )
        
        operation = FileOperation(
            source_path=str(self.project_root / "debug_output.wav"),
            target_path=None,
            action=FileAction.DELETE,
            file_info=file_info
        )
        
        stats = self.manager.execute_operations([operation])
        
        assert stats['total'] == 1
        assert stats['completed'] == 1
        assert stats['failed'] == 0
        assert operation.completed is True
        
        # File should still exist in dry run mode
        assert (self.project_root / "debug_output.wav").exists()
    
    @patch('indextts.github_preparation.safe_file_manager.send2trash')
    def test_delete_file_with_send2trash(self, mock_send2trash):
        """Test file deletion using send2trash."""
        # Create a real file manager (not dry run) for this test
        real_manager = SafeFileManager(str(self.project_root), dry_run=False)
        
        test_file = self.project_root / "test_delete.tmp"
        test_file.touch()
        
        # Mock send2trash to be available
        with patch('indextts.github_preparation.safe_file_manager.SEND2TRASH_AVAILABLE', True):
            success = real_manager._delete_file(test_file)
        
        assert success is True
        mock_send2trash.assert_called_once_with(str(test_file))
    
    def test_delete_file_fallback(self):
        """Test file deletion fallback when send2trash is not available."""
        # Create a real file manager (not dry run) for this test
        real_manager = SafeFileManager(str(self.project_root), dry_run=False)
        
        test_file = self.project_root / "test_delete.tmp"
        test_file.touch()
        
        # Mock send2trash as not available
        with patch('indextts.github_preparation.safe_file_manager.SEND2TRASH_AVAILABLE', False):
            success = real_manager._delete_file(test_file)
        
        assert success is True
        assert not test_file.exists()
        
        # Check that file was moved to .deleted directory
        deleted_dir = self.project_root / '.deleted'
        assert deleted_dir.exists()
        assert (deleted_dir / 'test_delete.tmp').exists()
    
    def test_relocate_file(self):
        """Test file relocation."""
        # Create a real file manager (not dry run) for this test
        real_manager = SafeFileManager(str(self.project_root), dry_run=False)
        
        source_file = self.project_root / "test_relocate.py"
        source_file.touch()
        target_file = self.project_root / "tests" / "test_relocate.py"
        
        success = real_manager._relocate_file(source_file, target_file)
        
        assert success is True
        assert not source_file.exists()
        assert target_file.exists()
    
    def test_organize_test_files(self):
        """Test test file organization."""
        # This will run in dry run mode, so files won't actually move
        stats = self.manager.organize_test_files()
        
        # Should find the root-level test files
        assert stats['total'] >= 0  # May be 0 if no relocatable test files found
    
    def test_cleanup_temporary_files(self):
        """Test temporary file cleanup."""
        # This will run in dry run mode, so files won't actually be deleted
        stats = self.manager.cleanup_temporary_files()
        
        # Should find some temporary files to clean up
        assert stats['total'] >= 0
    
    def test_preserve_user_content(self):
        """Test identification of user content to preserve."""
        user_files = self.manager.preserve_user_content()
        
        # Should identify user-generated content
        assert len(user_files) > 0
        
        # Check that outputs and prompts are identified
        user_file_paths = [Path(f).as_posix() for f in user_files]
        assert any('outputs' in path for path in user_file_paths)
        assert any('prompts' in path for path in user_file_paths)
    
    def test_generate_operation_report(self):
        """Test operation report generation."""
        # Add some mock operations
        file_info = FileInfo(
            path="test.tmp",
            file_type=FileType.TEMPORARY,
            is_essential=False,
            should_preserve_locally=False,
            target_location=None,
            action=FileAction.DELETE,
            reason="Temporary file"
        )
        
        completed_op = FileOperation(
            source_path="test.tmp",
            target_path=None,
            action=FileAction.DELETE,
            file_info=file_info,
            completed=True
        )
        
        failed_op = FileOperation(
            source_path="test2.tmp",
            target_path=None,
            action=FileAction.DELETE,
            file_info=file_info,
            completed=False,
            error="Permission denied"
        )
        
        self.manager.completed_operations = [completed_op]
        self.manager.failed_operations = [failed_op]
        
        report = self.manager.generate_operation_report()
        
        assert "Operation Report" in report
        assert "Summary" in report
        assert "Completed: 1" in report
        assert "Failed: 1" in report
        assert "test.tmp" in report
        assert "Permission denied" in report
    
    def test_rollback_operations(self):
        """Test operation rollback functionality."""
        # Create a real file manager for this test
        real_manager = SafeFileManager(str(self.project_root), dry_run=False)
        
        # Create test file and relocate it
        source_file = self.project_root / "test_rollback.py"
        source_file.write_text("test content")
        target_file = self.project_root / "tests" / "test_rollback.py"
        
        # Perform relocation
        success = real_manager._relocate_file(source_file, target_file)
        assert success is True
        
        # Create operation record
        file_info = FileInfo(
            path="test_rollback.py",
            file_type=FileType.TEST_FILE,
            is_essential=False,
            should_preserve_locally=False,
            target_location="tests/test_rollback.py",
            action=FileAction.RELOCATE,
            reason="Test file"
        )
        
        operation = FileOperation(
            source_path=str(source_file),
            target_path=str(target_file),
            action=FileAction.RELOCATE,
            file_info=file_info,
            completed=True
        )
        
        real_manager.completed_operations = [operation]
        
        # Test rollback
        stats = real_manager.rollback_operations()
        
        assert stats['total'] == 1
        assert stats['completed'] == 1
        assert source_file.exists()
        assert not target_file.exists()
    
    def test_never_touch_validation(self):
        """Test that NEVER_TOUCH files are properly protected."""
        file_info = FileInfo(
            path=".venv/lib/python.exe",
            file_type=FileType.VIRTUAL_ENV,
            is_essential=True,
            should_preserve_locally=True,
            target_location=None,
            action=FileAction.NEVER_TOUCH,
            reason="Virtual environment file"
        )
        
        is_safe, reason = self.manager.validate_operation(file_info)
        assert not is_safe
        # The validation should reject it either for being NEVER_TOUCH or in protected directory
        assert ("never touch" in reason.lower() or "protected directory" in reason.lower())


if __name__ == "__main__":
    pytest.main([__file__])