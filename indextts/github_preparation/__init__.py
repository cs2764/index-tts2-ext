"""
GitHub preparation utilities for IndexTTS2 project.

This module provides tools for preparing the IndexTTS2 project for GitHub upload,
including file classification, cleanup, organization, and version management.
"""

from .file_classifier import FileClassifier, FileInfo, FileType, FileAction
from .safe_file_manager import SafeFileManager, FileOperation
from .version_manager import VersionManager
from .documentation_generator import DocumentationGenerator
from .gitignore_manager import GitIgnoreManager
from .metadata_manager import MetadataManager
from .github_preparation import GitHubPreparation, WorkflowStep, WorkflowState

__version__ = "1.0.0"
__all__ = [
    'FileClassifier', 'FileInfo', 'FileType', 'FileAction',
    'SafeFileManager', 'FileOperation',
    'VersionManager',
    'DocumentationGenerator',
    'GitIgnoreManager',
    'MetadataManager',
    'GitHubPreparation', 'WorkflowStep', 'WorkflowState'
]