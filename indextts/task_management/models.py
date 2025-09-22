"""
Data models for task management components.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class TaskStatusEnum(Enum):
    """Enumeration of possible task statuses."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStatus:
    """Represents the status and progress of a background task."""
    task_id: str
    status: TaskStatusEnum
    progress: float  # 0.0 to 1.0
    current_stage: str
    estimated_remaining: Optional[float]  # seconds
    result_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_complete(self) -> bool:
        """Check if the task is in a completed state."""
        return self.status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED]
    
    @property
    def is_active(self) -> bool:
        """Check if the task is currently active."""
        return self.status in [TaskStatusEnum.QUEUED, TaskStatusEnum.PROCESSING]


@dataclass
class TaskResult:
    """Represents the result of a completed task."""
    task_id: str
    success: bool
    output_files: List[str]
    metadata: Dict[str, Any]
    processing_time: float
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskManagerConfig:
    """Configuration for task management system."""
    max_concurrent_tasks: int
    task_timeout: int  # seconds
    cleanup_completed_after: int  # seconds
    enable_persistence: bool
    max_queue_size: int
    progress_update_interval: float  # seconds
    
    @classmethod
    def default(cls) -> 'TaskManagerConfig':
        """Create default task manager configuration."""
        return cls(
            max_concurrent_tasks=2,
            task_timeout=3600,  # 1 hour
            cleanup_completed_after=86400,  # 24 hours
            enable_persistence=True,
            max_queue_size=50,
            progress_update_interval=1.0
        )