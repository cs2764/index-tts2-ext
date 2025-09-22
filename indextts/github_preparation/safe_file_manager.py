"""
Safe file management operations for GitHub preparation.

This module provides safe file operations including recycle bin functionality,
file organization, and validation to prevent deletion of essential files.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass

try:
    from send2trash import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False
    send2trash = None

from .file_classifier import FileClassifier, FileInfo, FileAction, FileType


@dataclass
class FileOperation:
    """Represents a file operation to be performed."""
    source_path: str
    target_path: Optional[str]
    action: FileAction
    file_info: FileInfo
    completed: bool = False
    error: Optional[str] = None


class SafeFileManager:
    """
    Safe file management system with recycle bin functionality.
    
    Provides secure file operations including moving files to recycle bin,
    organizing test files, and validating operations to prevent deletion
    of essential files.
    """
    
    def __init__(self, project_root: str, dry_run: bool = False):
        """
        Initialize the safe file manager.
        
        Args:
            project_root: Path to the project root directory
            dry_run: If True, only simulate operations without executing them
        """
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self.logger = self._setup_logger()
        
        # Initialize file classifier
        self.classifier = FileClassifier(str(self.project_root))
        
        # Track operations
        self.operations: List[FileOperation] = []
        self.completed_operations: List[FileOperation] = []
        self.failed_operations: List[FileOperation] = []
        
        # Safety validation
        self._init_safety_rules()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for file operations."""
        logger = logging.getLogger('SafeFileManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_safety_rules(self):
        """Initialize safety rules for file operations."""
        
        # Files that should never be deleted or moved
        self.protected_files = {
            'webui.py',
            'pyproject.toml',
            'uv.lock',
            'LICENSE',
            '.gitignore',
            '.gitattributes',
            '.python-version'
        }
        
        # Directories that should never be touched
        self.protected_directories = {
            '.git',
            '.venv',
            'venv',
            'env',
            'indextts'  # Core package directory
        }
        
        # File extensions that are always safe to delete
        self.safe_delete_extensions = {
            '.pyc', '.pyo', '.pyd',  # Python compiled
            '.log',                   # Log files
            '.tmp', '.temp',         # Temporary files
            '.bak', '.backup'        # Backup files
        }
        
        # Patterns for files that should be preserved locally
        self.preserve_local_patterns = {
            r'outputs/.*',
            r'prompts/.*',
            r'logs/.*',
            r'checkpoints/.*\.(pth|pt|bin|safetensors)',
            r'.*\.cache/.*'
        }
    
    def validate_operation(self, file_info: FileInfo) -> Tuple[bool, str]:
        """
        Validate if a file operation is safe to perform.
        
        Args:
            file_info: FileInfo object describing the operation
            
        Returns:
            Tuple of (is_safe, reason)
        """
        file_path = Path(file_info.path)
        
        # Check if file is in protected list
        if file_path.name in self.protected_files:
            return False, f"File {file_path.name} is protected and cannot be modified"
        
        # Check if file is in protected directory
        for protected_dir in self.protected_directories:
            if str(file_path).startswith(protected_dir + '/') or str(file_path).startswith(protected_dir + '\\'):
                return False, f"File is in protected directory {protected_dir}"
        
        # Check action-specific validations
        if file_info.action == FileAction.DELETE:
            return self._validate_delete_operation(file_info)
        elif file_info.action == FileAction.RELOCATE:
            return self._validate_relocate_operation(file_info)
        elif file_info.action == FileAction.NEVER_TOUCH:
            return False, "File is marked as never touch"
        
        return True, "Operation is safe"
    
    def _validate_delete_operation(self, file_info: FileInfo) -> Tuple[bool, str]:
        """Validate a delete operation."""
        
        # Never delete essential files
        if file_info.is_essential:
            return False, "Cannot delete essential file"
        
        # Check if file type is safe to delete
        safe_delete_types = {
            FileType.TEMPORARY,
            FileType.DEBUG,
            FileType.CACHE
        }
        
        if file_info.file_type not in safe_delete_types:
            # Check if extension is safe to delete
            file_path = Path(file_info.path)
            if file_path.suffix.lower() not in self.safe_delete_extensions:
                return False, f"File type {file_info.file_type.value} is not safe to delete"
        
        return True, "Delete operation is safe"
    
    def _validate_relocate_operation(self, file_info: FileInfo) -> Tuple[bool, str]:
        """Validate a relocate operation."""
        
        if not file_info.target_location:
            return False, "No target location specified for relocation"
        
        target_path = self.project_root / file_info.target_location
        
        # Check if target directory exists or can be created
        target_dir = target_path.parent
        if not target_dir.exists():
            try:
                if not self.dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create target directory: {e}"
        
        # Check if target file already exists
        if target_path.exists():
            return False, f"Target file already exists: {file_info.target_location}"
        
        return True, "Relocate operation is safe"
    
    def plan_operations(self, file_infos: List[FileInfo]) -> List[FileOperation]:
        """
        Plan file operations based on file classifications.
        
        Args:
            file_infos: List of classified files
            
        Returns:
            List of planned operations
        """
        operations = []
        
        for file_info in file_infos:
            # Skip files that should be kept as-is
            if file_info.action in {FileAction.KEEP, FileAction.NEVER_TOUCH, FileAction.PRESERVE_LOCAL}:
                continue
            
            # Validate operation
            is_safe, reason = self.validate_operation(file_info)
            if not is_safe:
                self.logger.warning(f"Skipping unsafe operation on {file_info.path}: {reason}")
                continue
            
            # Create operation
            source_path = str(self.project_root / file_info.path)
            target_path = None
            
            if file_info.action == FileAction.RELOCATE and file_info.target_location:
                target_path = str(self.project_root / file_info.target_location)
            
            operation = FileOperation(
                source_path=source_path,
                target_path=target_path,
                action=file_info.action,
                file_info=file_info
            )
            
            operations.append(operation)
        
        self.operations = operations
        return operations
    
    def execute_operations(self, operations: Optional[List[FileOperation]] = None) -> Dict[str, int]:
        """
        Execute planned file operations.
        
        Args:
            operations: List of operations to execute (uses self.operations if None)
            
        Returns:
            Dictionary with operation statistics
        """
        if operations is None:
            operations = self.operations
        
        stats = {
            'total': len(operations),
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for operation in operations:
            try:
                success = self._execute_single_operation(operation)
                if success:
                    stats['completed'] += 1
                    self.completed_operations.append(operation)
                else:
                    stats['failed'] += 1
                    self.failed_operations.append(operation)
            except Exception as e:
                self.logger.error(f"Error executing operation on {operation.source_path}: {e}")
                operation.error = str(e)
                stats['failed'] += 1
                self.failed_operations.append(operation)
        
        return stats
    
    def _execute_single_operation(self, operation: FileOperation) -> bool:
        """
        Execute a single file operation.
        
        Args:
            operation: FileOperation to execute
            
        Returns:
            True if successful, False otherwise
        """
        source_path = Path(operation.source_path)
        
        # Check if source file exists
        if not source_path.exists():
            self.logger.warning(f"Source file does not exist: {source_path}")
            operation.error = "Source file does not exist"
            return False
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would execute {operation.action.value} on {source_path}")
            operation.completed = True
            return True
        
        try:
            if operation.action == FileAction.DELETE:
                return self._delete_file(source_path)
            elif operation.action == FileAction.RELOCATE:
                return self._relocate_file(source_path, Path(operation.target_path))
            else:
                self.logger.warning(f"Unknown action: {operation.action}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to execute {operation.action.value} on {source_path}: {e}")
            operation.error = str(e)
            return False
    
    def _delete_file(self, file_path: Path) -> bool:
        """
        Safely delete a file using recycle bin if available.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if SEND2TRASH_AVAILABLE:
                send2trash(str(file_path))
                self.logger.info(f"Moved to recycle bin: {file_path}")
            else:
                # Fallback: move to a .deleted directory
                deleted_dir = self.project_root / '.deleted'
                deleted_dir.mkdir(exist_ok=True)
                
                # Create unique name if file already exists in deleted dir
                target_name = file_path.name
                counter = 1
                while (deleted_dir / target_name).exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    target_name = f"{stem}_{counter}{suffix}"
                    counter += 1
                
                target_path = deleted_dir / target_name
                shutil.move(str(file_path), str(target_path))
                self.logger.info(f"Moved to .deleted directory: {file_path} -> {target_path}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete {file_path}: {e}")
            return False
    
    def _relocate_file(self, source_path: Path, target_path: Path) -> bool:
        """
        Relocate a file to a new location.
        
        Args:
            source_path: Current file path
            target_path: Target file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create target directory if it doesn't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(target_path))
            self.logger.info(f"Relocated: {source_path} -> {target_path}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to relocate {source_path} to {target_path}: {e}")
            return False
    
    def organize_test_files(self) -> Dict[str, int]:
        """
        Organize test files by moving root-level test files to tests/ directory.
        
        Returns:
            Dictionary with organization statistics
        """
        self.logger.info("Starting test file organization...")
        
        # Scan for test files
        file_infos = self.classifier.scan_project()
        test_files = [fi for fi in file_infos if fi.file_type == FileType.TEST_FILE]
        
        # Filter for root-level test files that need relocation
        root_test_files = [
            fi for fi in test_files 
            if fi.action == FileAction.RELOCATE and fi.target_location
        ]
        
        if not root_test_files:
            self.logger.info("No root-level test files found to organize")
            return {'total': 0, 'completed': 0, 'failed': 0}
        
        # Plan and execute operations
        operations = self.plan_operations(root_test_files)
        stats = self.execute_operations(operations)
        
        self.logger.info(f"Test file organization completed: {stats}")
        return stats
    
    def cleanup_temporary_files(self) -> Dict[str, int]:
        """
        Clean up temporary and debug files.
        
        Returns:
            Dictionary with cleanup statistics
        """
        self.logger.info("Starting temporary file cleanup...")
        
        # Scan for temporary and debug files
        file_infos = self.classifier.scan_project()
        temp_files = [
            fi for fi in file_infos 
            if fi.file_type in {FileType.TEMPORARY, FileType.DEBUG, FileType.CACHE}
            and fi.action == FileAction.DELETE
        ]
        
        if not temp_files:
            self.logger.info("No temporary files found to clean up")
            return {'total': 0, 'completed': 0, 'failed': 0}
        
        # Plan and execute operations
        operations = self.plan_operations(temp_files)
        stats = self.execute_operations(operations)
        
        self.logger.info(f"Temporary file cleanup completed: {stats}")
        return stats
    
    def preserve_user_content(self) -> List[str]:
        """
        Identify user-generated content that should be preserved locally.
        
        Returns:
            List of file paths that should be preserved locally
        """
        self.logger.info("Identifying user content to preserve...")
        
        # Scan for user-generated content
        file_infos = self.classifier.scan_project()
        user_files = [
            fi.path for fi in file_infos 
            if fi.should_preserve_locally or fi.action == FileAction.PRESERVE_LOCAL
        ]
        
        self.logger.info(f"Found {len(user_files)} files to preserve locally")
        return user_files
    
    def generate_operation_report(self) -> str:
        """
        Generate a report of all file operations.
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("# Safe File Manager - Operation Report")
        report.append("")
        
        # Summary
        total_ops = len(self.completed_operations) + len(self.failed_operations)
        report.append("## Summary")
        report.append(f"Total operations: {total_ops}")
        report.append(f"Completed: {len(self.completed_operations)}")
        report.append(f"Failed: {len(self.failed_operations)}")
        report.append("")
        
        # Completed operations
        if self.completed_operations:
            report.append("## Completed Operations")
            for op in self.completed_operations:
                action_desc = op.action.value.replace('_', ' ').title()
                if op.target_path:
                    report.append(f"- {action_desc}: {op.source_path} -> {op.target_path}")
                else:
                    report.append(f"- {action_desc}: {op.source_path}")
            report.append("")
        
        # Failed operations
        if self.failed_operations:
            report.append("## Failed Operations")
            for op in self.failed_operations:
                action_desc = op.action.value.replace('_', ' ').title()
                error_msg = op.error or "Unknown error"
                report.append(f"- {action_desc}: {op.source_path} - Error: {error_msg}")
            report.append("")
        
        return "\n".join(report)
    
    def rollback_operations(self) -> Dict[str, int]:
        """
        Attempt to rollback completed operations (limited support).
        
        Note: This only works for relocate operations and files in .deleted directory.
        Files sent to system recycle bin cannot be automatically restored.
        
        Returns:
            Dictionary with rollback statistics
        """
        self.logger.info("Attempting to rollback operations...")
        
        stats = {'total': 0, 'completed': 0, 'failed': 0}
        
        for operation in self.completed_operations:
            stats['total'] += 1
            
            try:
                if operation.action == FileAction.RELOCATE and operation.target_path:
                    # Move file back to original location
                    target_path = Path(operation.target_path)
                    source_path = Path(operation.source_path)
                    
                    if target_path.exists():
                        if not self.dry_run:
                            shutil.move(str(target_path), str(source_path))
                        self.logger.info(f"Rolled back relocation: {target_path} -> {source_path}")
                        stats['completed'] += 1
                    else:
                        self.logger.warning(f"Cannot rollback, target file not found: {target_path}")
                        stats['failed'] += 1
                
                elif operation.action == FileAction.DELETE:
                    # Try to restore from .deleted directory
                    deleted_dir = self.project_root / '.deleted'
                    original_path = Path(operation.source_path)
                    deleted_path = deleted_dir / original_path.name
                    
                    if deleted_path.exists():
                        if not self.dry_run:
                            shutil.move(str(deleted_path), str(original_path))
                        self.logger.info(f"Restored from .deleted: {deleted_path} -> {original_path}")
                        stats['completed'] += 1
                    else:
                        self.logger.warning(f"Cannot restore, file was sent to system recycle bin: {original_path}")
                        stats['failed'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to rollback operation: {e}")
                stats['failed'] += 1
        
        self.logger.info(f"Rollback completed: {stats}")
        return stats