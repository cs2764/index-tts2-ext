"""
Data models for voice sample management.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import os


@dataclass
class VoiceSample:
    """Represents a voice sample file."""
    filename: str
    filepath: str
    format: str
    file_size: int
    duration: Optional[float]
    sample_rate: Optional[int]
    created_at: datetime
    is_valid: bool
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def display_name(self) -> str:
        """Get display name for the voice sample."""
        return os.path.splitext(self.filename)[0]
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)