"""
Data models for file processing components.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..chapter_parsing.models import Chapter


@dataclass
class FilePreview:
    """Represents a file preview with metadata."""
    filename: str
    preview_text: str
    total_lines: int
    encoding: str
    file_size: str  # Human-readable size (e.g., "1.2 MB")
    preview_truncated: bool


@dataclass
class ProcessedFile:
    """Represents a processed file with extracted content and metadata."""
    filename: str
    content: str
    original_encoding: str
    chapters: List['Chapter']  # Forward reference to avoid circular import
    metadata: Dict[str, Any]
    processing_time: float
    file_size: int
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class FileProcessingConfig:
    """Configuration for file processing operations."""
    supported_formats: List[str]
    max_file_size: int  # in bytes
    encoding_detection_confidence: float
    text_cleaning_enabled: bool
    merge_empty_lines: bool
    remove_excess_spaces: bool
    intelligent_sentence_breaking: bool
    clean_special_characters: bool
    
    @classmethod
    def default(cls) -> 'FileProcessingConfig':
        """Create default file processing configuration."""
        return cls(
            supported_formats=['txt', 'epub'],
            max_file_size=50 * 1024 * 1024,  # 50MB
            encoding_detection_confidence=0.8,
            text_cleaning_enabled=True,
            merge_empty_lines=True,
            remove_excess_spaces=True,
            intelligent_sentence_breaking=True,
            clean_special_characters=True
        )