"""
Data models for output file management.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import os


@dataclass
class OutputFile:
    """Represents a generated output audio file."""
    filename: str
    filepath: str
    format: str
    file_size: int
    duration: Optional[float]
    source_filename: Optional[str]
    voice_name: Optional[str]
    created_at: datetime
    is_segmented: bool
    segment_info: Optional[dict]
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.segment_info is None:
            self.segment_info = {}
    
    @property
    def display_name(self) -> str:
        """Get display name for the output file."""
        return os.path.splitext(self.filename)[0]
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)


@dataclass
class SegmentedOutput:
    """Represents a collection of segmented audio files."""
    base_filename: str
    output_directory: str
    segments: List[OutputFile]
    total_duration: Optional[float]
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def total_files(self) -> int:
        """Get total number of segment files."""
        return len(self.segments)
    
    @property
    def total_size_mb(self) -> float:
        """Get total size of all segments in megabytes."""
        return sum(segment.size_mb for segment in self.segments)