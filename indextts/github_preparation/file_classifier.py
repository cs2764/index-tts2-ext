"""
File classification system for GitHub preparation.

This module provides comprehensive file classification capabilities to categorize
project files by type, importance, and appropriate handling for GitHub upload.
"""

import os
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


class FileType(Enum):
    """File type classifications."""
    SOURCE_CODE = "source_code"
    TEST_FILE = "test_file"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    MODEL_CHECKPOINT = "model_checkpoint"
    AUDIO_SAMPLE = "audio_sample"
    USER_GENERATED = "user_generated"
    TEMPORARY = "temporary"
    DEBUG = "debug"
    VIRTUAL_ENV = "virtual_env"
    GIT_METADATA = "git_metadata"
    BUILD_ARTIFACT = "build_artifact"
    CACHE = "cache"
    LOG_FILE = "log_file"
    ASSET = "asset"
    UNKNOWN = "unknown"


class FileAction(Enum):
    """Actions to take with files."""
    KEEP = "keep"                    # Keep in repository
    MOVE = "move"                    # Move to different location
    DELETE = "delete"                # Safe delete (recycle bin)
    RELOCATE = "relocate"            # Move to proper directory
    PRESERVE_LOCAL = "preserve_local" # Keep locally but exclude from git
    NEVER_TOUCH = "never_touch"      # Never modify (critical files)


@dataclass
class FileInfo:
    """Information about a classified file."""
    path: str
    file_type: FileType
    is_essential: bool
    should_preserve_locally: bool
    target_location: Optional[str]
    action: FileAction
    reason: str  # Explanation for the classification


class FileClassifier:
    """
    Comprehensive file classifier for IndexTTS2 project.
    
    Categorizes files by type and importance, determining appropriate
    actions for GitHub preparation while ensuring safety and preservation
    of essential functionality.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the file classifier.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root).resolve()
        self._init_classification_rules()
    
    def _init_classification_rules(self):
        """Initialize file classification rules and patterns."""
        
        # Essential source code patterns (handle both / and \ path separators)
        self.source_patterns = {
            r'indextts[/\\].*\.py$': 'Core package source code',
            r'webui\.py$': 'Main web UI entry point',
            r'pyproject\.toml$': 'Package configuration',
            r'uv\.lock$': 'Dependency lock file',
            r'LICENSE.*$': 'License files',
            r'MANIFEST\.in$': 'Package manifest'
        }
        
        # Test file patterns (handle both / and \ path separators)
        self.test_patterns = {
            r'tests[/\\].*\.py$': 'Organized test files',
            r'test_.*\.py$': 'Root-level test files (need relocation)',
            r'.*_test\.py$': 'Test files (need relocation)',
            r'examples[/\\]cases\.jsonl$': 'Test case definitions'
        }
        
        # Documentation patterns
        self.doc_patterns = {
            r'docs[/\\].*\.(md|rst|txt)$': 'Documentation files',
            r'.*README.*\.(md|rst|txt)$': 'README documentation',
            r'.*GUIDE.*\.(md|rst|txt)$': 'Guide documentation',
            r'.*SUMMARY.*\.md$': 'Summary documentation',
            r'.*\.md$': 'Markdown documentation',
            r'DISCLAIMER$': 'Legal disclaimer',
            r'WARP\.md$': 'Project documentation'
        }
        
        # Configuration patterns
        self.config_patterns = {
            r'config[/\\].*\.yaml$': 'Configuration files',
            r'checkpoints[/\\]config\.yaml$': 'Model configuration',
            r'\.gitignore$': 'Git ignore configuration',
            r'\.gitattributes$': 'Git attributes configuration',
            r'\.python-version$': 'Python version specification'
        }
        
        # Model and checkpoint patterns
        self.model_patterns = {
            r'checkpoints[/\\].*\.(pth|pt|bin|safetensors)$': 'Model checkpoints',
            r'checkpoints[/\\].*\.model$': 'Model files',
            r'checkpoints[/\\]qwen.*$': 'Qwen emotion model',
            r'checkpoints[/\\]\.cache[/\\].*$': 'Model cache files'
        }
        
        # Audio sample patterns
        self.audio_patterns = {
            r'examples[/\\].*\.(wav|mp3|flac)$': 'Example audio files',
            r'samples[/\\].*\.(wav|mp3|flac)$': 'Sample audio files',
            r'tests[/\\].*\.(wav|mp3)$': 'Test audio files'
        }
        
        # User-generated content patterns
        self.user_generated_patterns = {
            r'outputs[/\\].*$': 'Generated audio outputs',
            r'prompts[/\\].*$': 'User-uploaded prompts',
            r'logs[/\\].*$': 'Log files'
        }
        
        # Temporary and debug patterns
        self.temp_patterns = {
            r'test_.*\.(wav|mp3)$': 'Test output files',
            r'multiple_test_.*$': 'Multiple test files',
            r'test_improved_.*$': 'Test improvement files',
            r'test_indentation_.*$': 'Test indentation files'
        }
        
        # Debug patterns (separate from temp for better classification)
        self.debug_patterns = {
            r'debug_.*\.(py|wav|mp3)$': 'Debug files',
            r'.*_debug.*\.(wav|mp3)$': 'Debug audio files'
        }
        
        # Virtual environment patterns
        self.venv_patterns = {
            r'\.venv[/\\].*$': 'Virtual environment',
            r'venv[/\\].*$': 'Virtual environment',
            r'env[/\\].*$': 'Virtual environment'
        }
        
        # Cache and build patterns
        self.cache_patterns = {
            r'__pycache__[/\\].*$': 'Python cache',
            r'\.pytest_cache[/\\].*$': 'Pytest cache',
            r'\.cache[/\\].*$': 'General cache',
            r'build[/\\].*$': 'Build artifacts',
            r'dist[/\\].*$': 'Distribution artifacts',
            r'.*\.egg-info[/\\].*$': 'Egg info'
        }
        
        # Git metadata patterns
        self.git_patterns = {
            r'\.git[/\\].*$': 'Git metadata'
        }
        
        # Asset patterns
        self.asset_patterns = {
            r'assets[/\\].*\.(png|jpg|jpeg|gif|svg|mp4)$': 'Project assets',
            r'archive[/\\].*$': 'Archived files'
        }
        
        # Script patterns
        self.script_patterns = {
            r'scripts[/\\].*\.py$': 'Utility scripts',
            r'scripts[/\\].*\.bat$': 'Batch scripts',
            r'tools[/\\].*\.py$': 'Tool scripts'
        }
        
        # Files that should never be touched
        self.never_touch_patterns = {
            r'\.venv[/\\].*$': 'Virtual environment - critical',
            r'venv[/\\].*$': 'Virtual environment - critical',
            r'env[/\\].*$': 'Virtual environment - critical',
            r'\.git[/\\].*$': 'Git metadata - critical',
            r'indextts[/\\].*\.py$': 'Core source code - critical',
            r'webui\.py$': 'Main entry point - critical',
            r'pyproject\.toml$': 'Package config - critical',
            r'uv\.lock$': 'Dependency lock - critical'
        }
    
    def classify_file(self, file_path: str) -> FileInfo:
        """
        Classify a single file and determine appropriate action.
        
        Args:
            file_path: Path to the file relative to project root
            
        Returns:
            FileInfo object with classification details
        """
        rel_path = str(Path(file_path).relative_to(self.project_root))
        
        # Check if file should never be touched
        if self._matches_patterns(rel_path, self.never_touch_patterns):
            return FileInfo(
                path=rel_path,
                file_type=self._get_file_type(rel_path),
                is_essential=True,
                should_preserve_locally=True,
                target_location=None,
                action=FileAction.NEVER_TOUCH,
                reason=self._get_match_reason(rel_path, self.never_touch_patterns)
            )
        
        # Classify by type and determine action
        file_type = self._get_file_type(rel_path)
        is_essential = self._is_essential(rel_path, file_type)
        should_preserve_locally = self._should_preserve_locally(rel_path, file_type)
        action, target_location = self._determine_action(rel_path, file_type)
        reason = self._get_classification_reason(rel_path, file_type)
        
        return FileInfo(
            path=rel_path,
            file_type=file_type,
            is_essential=is_essential,
            should_preserve_locally=should_preserve_locally,
            target_location=target_location,
            action=action,
            reason=reason
        )
    
    def scan_project(self) -> List[FileInfo]:
        """
        Scan the entire project and classify all files.
        
        Returns:
            List of FileInfo objects for all files in the project
        """
        file_infos = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories entirely
            dirs[:] = [d for d in dirs if not self._should_skip_directory(d)]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    file_info = self.classify_file(str(file_path))
                    file_infos.append(file_info)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Warning: Could not classify {file_path}: {e}")
        
        return file_infos
    
    def _get_file_type(self, rel_path: str) -> FileType:
        """Determine the file type based on patterns."""
        
        # Normalize path separators for consistent matching
        normalized_path = rel_path.replace('\\', '/')
        
        # Check debug patterns first (most specific)
        if self._matches_patterns(normalized_path, self.debug_patterns):
            return FileType.DEBUG
        elif self._matches_patterns(normalized_path, self.temp_patterns):
            return FileType.TEMPORARY
        elif self._matches_patterns(normalized_path, self.venv_patterns):
            return FileType.VIRTUAL_ENV
        elif self._matches_patterns(normalized_path, self.cache_patterns):
            return FileType.CACHE
        elif self._matches_patterns(normalized_path, self.git_patterns):
            return FileType.GIT_METADATA
        elif self._matches_patterns(normalized_path, self.user_generated_patterns):
            return FileType.USER_GENERATED
        elif self._matches_patterns(normalized_path, self.model_patterns):
            return FileType.MODEL_CHECKPOINT
        elif self._matches_patterns(normalized_path, self.audio_patterns):
            return FileType.AUDIO_SAMPLE
        elif self._matches_patterns(normalized_path, self.test_patterns):
            return FileType.TEST_FILE
        elif self._matches_patterns(normalized_path, self.doc_patterns):
            return FileType.DOCUMENTATION
        elif self._matches_patterns(normalized_path, self.config_patterns):
            return FileType.CONFIGURATION
        elif self._matches_patterns(normalized_path, self.source_patterns):
            return FileType.SOURCE_CODE
        elif self._matches_patterns(normalized_path, self.script_patterns):
            return FileType.SOURCE_CODE  # Scripts are also source code
        elif self._matches_patterns(normalized_path, self.asset_patterns):
            return FileType.ASSET
        elif rel_path.endswith('.log'):
            return FileType.LOG_FILE
        else:
            return FileType.UNKNOWN
    
    def _is_essential(self, rel_path: str, file_type: FileType) -> bool:
        """Determine if a file is essential for the project."""
        
        essential_types = {
            FileType.SOURCE_CODE,
            FileType.CONFIGURATION,
            FileType.DOCUMENTATION,
            FileType.AUDIO_SAMPLE,
            FileType.ASSET
        }
        
        if file_type in essential_types:
            return True
        
        # Special cases for essential files
        essential_files = {
            'README.md', 'LICENSE', 'pyproject.toml', 'uv.lock',
            'webui.py', '.gitignore', '.gitattributes'
        }
        
        return Path(rel_path).name in essential_files
    
    def _should_preserve_locally(self, rel_path: str, file_type: FileType) -> bool:
        """Determine if a file should be preserved locally but excluded from git."""
        
        preserve_local_types = {
            FileType.USER_GENERATED,
            FileType.MODEL_CHECKPOINT,
            FileType.CACHE,
            FileType.LOG_FILE,
            FileType.VIRTUAL_ENV
        }
        
        return file_type in preserve_local_types
    
    def _determine_action(self, rel_path: str, file_type: FileType) -> Tuple[FileAction, Optional[str]]:
        """Determine the appropriate action for a file."""
        
        # Root-level test files should be relocated
        if (file_type == FileType.TEST_FILE and 
            not rel_path.startswith('tests/') and 
            (rel_path.startswith('test_') or rel_path.endswith('_test.py'))):
            return FileAction.RELOCATE, f"tests/{Path(rel_path).name}"
        
        # Temporary and debug files should be deleted
        if file_type in {FileType.TEMPORARY, FileType.DEBUG}:
            return FileAction.DELETE, None
        
        # Cache files should be deleted
        if file_type == FileType.CACHE:
            return FileAction.DELETE, None
        
        # User-generated content should be preserved locally but excluded from git
        if file_type == FileType.USER_GENERATED:
            return FileAction.PRESERVE_LOCAL, None
        
        # Model checkpoints should be preserved locally but excluded from git
        if file_type == FileType.MODEL_CHECKPOINT:
            return FileAction.PRESERVE_LOCAL, None
        
        # Virtual environment should never be touched
        if file_type == FileType.VIRTUAL_ENV:
            return FileAction.NEVER_TOUCH, None
        
        # Git metadata should never be touched
        if file_type == FileType.GIT_METADATA:
            return FileAction.NEVER_TOUCH, None
        
        # Essential files should be kept
        if self._is_essential(rel_path, file_type):
            return FileAction.KEEP, None
        
        # Unknown files - be conservative and keep them
        return FileAction.KEEP, None
    
    def _matches_patterns(self, rel_path: str, patterns: Dict[str, str]) -> bool:
        """Check if a path matches any of the given patterns."""
        # Normalize path separators for consistent matching
        normalized_path = rel_path.replace('\\', '/')
        
        for pattern in patterns.keys():
            # Convert pattern to handle both separators
            normalized_pattern = pattern.replace('[/\\\\]', '/')
            if re.match(normalized_pattern, normalized_path):
                return True
        return False
    
    def _get_match_reason(self, rel_path: str, patterns: Dict[str, str]) -> str:
        """Get the reason for a pattern match."""
        # Normalize path separators for consistent matching
        normalized_path = rel_path.replace('\\', '/')
        
        for pattern, reason in patterns.items():
            # Convert pattern to handle both separators
            normalized_pattern = pattern.replace('[/\\\\]', '/')
            if re.match(normalized_pattern, normalized_path):
                return reason
        return "No specific reason"
    
    def _get_classification_reason(self, rel_path: str, file_type: FileType) -> str:
        """Get the reason for file classification."""
        
        pattern_groups = [
            (self.source_patterns, "Source code file"),
            (self.script_patterns, "Script file"),
            (self.test_patterns, "Test file"),
            (self.doc_patterns, "Documentation file"),
            (self.config_patterns, "Configuration file"),
            (self.model_patterns, "Model checkpoint"),
            (self.audio_patterns, "Audio sample"),
            (self.user_generated_patterns, "User-generated content"),
            (self.debug_patterns, "Debug file"),
            (self.temp_patterns, "Temporary file"),
            (self.venv_patterns, "Virtual environment"),
            (self.cache_patterns, "Cache file"),
            (self.git_patterns, "Git metadata"),
            (self.asset_patterns, "Project asset")
        ]
        
        for patterns, default_reason in pattern_groups:
            if self._matches_patterns(rel_path, patterns):
                return self._get_match_reason(rel_path, patterns)
        
        return f"Classified as {file_type.value}"
    
    def _should_skip_directory(self, dir_name: str) -> bool:
        """Determine if a directory should be skipped during scanning."""
        skip_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.venv', 'venv', 'env'
        }
        return dir_name in skip_dirs
    
    def get_files_by_type(self, file_infos: List[FileInfo]) -> Dict[FileType, List[FileInfo]]:
        """Group files by their type."""
        grouped = {}
        for file_info in file_infos:
            if file_info.file_type not in grouped:
                grouped[file_info.file_type] = []
            grouped[file_info.file_type].append(file_info)
        return grouped
    
    def get_files_by_action(self, file_infos: List[FileInfo]) -> Dict[FileAction, List[FileInfo]]:
        """Group files by their recommended action."""
        grouped = {}
        for file_info in file_infos:
            if file_info.action not in grouped:
                grouped[file_info.action] = []
            grouped[file_info.action].append(file_info)
        return grouped
    
    def generate_cleanup_report(self, file_infos: List[FileInfo]) -> str:
        """Generate a comprehensive cleanup report."""
        
        by_action = self.get_files_by_action(file_infos)
        by_type = self.get_files_by_type(file_infos)
        
        report = []
        report.append("# GitHub Preparation - File Classification Report")
        report.append("")
        
        # Summary statistics
        report.append("## Summary")
        report.append(f"Total files analyzed: {len(file_infos)}")
        report.append("")
        
        # Files by action
        report.append("## Recommended Actions")
        for action in FileAction:
            if action in by_action:
                files = by_action[action]
                report.append(f"### {action.value.replace('_', ' ').title()} ({len(files)} files)")
                for file_info in files[:10]:  # Show first 10
                    report.append(f"- {file_info.path} - {file_info.reason}")
                if len(files) > 10:
                    report.append(f"- ... and {len(files) - 10} more files")
                report.append("")
        
        # Files by type
        report.append("## File Types")
        for file_type in FileType:
            if file_type in by_type:
                files = by_type[file_type]
                report.append(f"### {file_type.value.replace('_', ' ').title()} ({len(files)} files)")
                report.append("")
        
        return "\n".join(report)