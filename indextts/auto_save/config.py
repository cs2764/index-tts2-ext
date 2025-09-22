"""
Configuration classes for auto-save functionality.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AutoSaveConfig:
    """Configuration for incremental auto-save functionality."""
    
    enabled: bool = True
    save_interval: int = 5  # Steps between saves
    max_interval: int = 10
    min_interval: int = 1
    performance_adaptive: bool = True
    backup_enabled: bool = True
    cleanup_on_success: bool = True
    
    def __post_init__(self):
        """Validate configuration values."""
        if not (self.min_interval <= self.save_interval <= self.max_interval):
            raise ValueError(f"save_interval ({self.save_interval}) must be between {self.min_interval} and {self.max_interval}")
    
    @classmethod
    def default(cls) -> 'AutoSaveConfig':
        """Create default configuration."""
        return cls()


@dataclass
class SaveProgress:
    """Progress tracking for auto-save operations."""
    
    current_step: int
    last_save_step: int
    next_save_step: int
    total_segments: int
    saved_duration: float
    save_file_path: Optional[str]
    last_save_timestamp: datetime
    save_success: bool
    error_message: Optional[str]
    
    def __post_init__(self):
        """Set default timestamp if not provided."""
        if not hasattr(self, 'last_save_timestamp') or self.last_save_timestamp is None:
            self.last_save_timestamp = datetime.now()


@dataclass
class AudioSegmentInfo:
    """Information about an audio segment."""
    
    segment_index: int
    audio_data: 'torch.Tensor'  # Forward reference to avoid import
    duration: float
    text_content: str
    generation_time: float
    timestamp: datetime
    file_offset: Optional[int] = None
    
    def __post_init__(self):
        """Set default timestamp if not provided."""
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SaveOperation:
    """Information about a save operation."""
    
    operation_id: str
    step: int
    audio_segments: list  # List[AudioSegmentInfo]
    output_path: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    file_size: Optional[int] = None
    
    def __post_init__(self):
        """Set default start time if not provided."""
        if not hasattr(self, 'start_time') or self.start_time is None:
            self.start_time = datetime.now()