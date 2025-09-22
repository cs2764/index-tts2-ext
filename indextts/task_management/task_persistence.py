"""
Task persistence and state management for background tasks.
"""

import json
import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from .models import TaskStatus, TaskStatusEnum


@dataclass
class TaskSnapshot:
    """Snapshot of task state for persistence."""
    task_id: str
    status: str
    progress: float
    current_stage: str
    estimated_remaining: Optional[float]
    result_path: Optional[str]
    error_message: Optional[str]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    checkpoint_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_task_status(cls, task_status: TaskStatus) -> 'TaskSnapshot':
        """Create snapshot from TaskStatus object."""
        return cls(
            task_id=task_status.task_id,
            status=task_status.status.value,
            progress=task_status.progress,
            current_stage=task_status.current_stage,
            estimated_remaining=task_status.estimated_remaining,
            result_path=task_status.result_path,
            error_message=task_status.error_message,
            created_at=task_status.created_at.isoformat(),
            updated_at=task_status.updated_at.isoformat(),
            metadata=task_status.metadata
        )
    
    def to_task_status(self) -> TaskStatus:
        """Convert snapshot back to TaskStatus object."""
        return TaskStatus(
            task_id=self.task_id,
            status=TaskStatusEnum(self.status),
            progress=self.progress,
            current_stage=self.current_stage,
            estimated_remaining=self.estimated_remaining,
            result_path=self.result_path,
            error_message=self.error_message,
            created_at=datetime.fromisoformat(self.created_at),
            updated_at=datetime.fromisoformat(self.updated_at),
            metadata=self.metadata
        )


class TaskStateManager:
    """Manages task state persistence and recovery."""
    
    def __init__(self, enable_persistence: bool = True):
        """
        Initialize task state manager.
        
        Args:
            enable_persistence: Whether to enable state persistence
        """
        self.enable_persistence = enable_persistence
        self.task_snapshots: Dict[str, TaskSnapshot] = {}
        self.checkpoint_data: Dict[str, Dict[str, Any]] = {}
        self.state_history: Dict[str, List[TaskSnapshot]] = {}
        self._lock = threading.Lock()
        
        # Configuration
        self.max_history_per_task = 10
        self.auto_checkpoint_interval = 30.0  # seconds
        self.last_checkpoint_time = time.time()
    
    def save_task_state(self, task_status: TaskStatus):
        """
        Save current task state.
        
        Args:
            task_status: Current task status to save
        """
        if not self.enable_persistence:
            return
        
        with self._lock:
            snapshot = TaskSnapshot.from_task_status(task_status)
            
            # Add checkpoint data if available
            if task_status.task_id in self.checkpoint_data:
                snapshot.checkpoint_data = self.checkpoint_data[task_status.task_id].copy()
            
            # Save current snapshot
            self.task_snapshots[task_status.task_id] = snapshot
            
            # Add to history
            if task_status.task_id not in self.state_history:
                self.state_history[task_status.task_id] = []
            
            history = self.state_history[task_status.task_id]
            history.append(snapshot)
            
            # Limit history size
            if len(history) > self.max_history_per_task:
                history.pop(0)
    
    def restore_task_state(self, task_id: str) -> Optional[TaskStatus]:
        """
        Restore task state from persistence.
        
        Args:
            task_id: ID of task to restore
            
        Returns:
            Restored TaskStatus or None if not found
        """
        if not self.enable_persistence:
            return None
        
        with self._lock:
            snapshot = self.task_snapshots.get(task_id)
            if snapshot:
                return snapshot.to_task_status()
        
        return None
    
    def create_checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]):
        """
        Create a checkpoint for task recovery.
        
        Args:
            task_id: ID of the task
            checkpoint_data: Data to save for recovery
        """
        with self._lock:
            self.checkpoint_data[task_id] = {
                'timestamp': time.time(),
                'data': checkpoint_data.copy()
            }
            
            # Update snapshot if it exists
            if task_id in self.task_snapshots:
                self.task_snapshots[task_id].checkpoint_data = self.checkpoint_data[task_id].copy()
    
    def get_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint data for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Checkpoint data or None if not found
        """
        with self._lock:
            checkpoint = self.checkpoint_data.get(task_id)
            if checkpoint:
                return checkpoint['data'].copy()
        
        return None
    
    def get_task_history(self, task_id: str) -> List[TaskSnapshot]:
        """
        Get state history for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of task snapshots in chronological order
        """
        with self._lock:
            return self.state_history.get(task_id, []).copy()
    
    def cleanup_task_state(self, task_id: str):
        """
        Clean up state data for a completed task.
        
        Args:
            task_id: ID of the task to clean up
        """
        with self._lock:
            # Remove current snapshot
            if task_id in self.task_snapshots:
                del self.task_snapshots[task_id]
            
            # Remove checkpoint data
            if task_id in self.checkpoint_data:
                del self.checkpoint_data[task_id]
            
            # Keep history for completed tasks (for debugging/analysis)
            # History will be cleaned up by cleanup_old_history method
    
    def cleanup_old_history(self, max_age_hours: float = 24.0):
        """
        Clean up old task history.
        
        Args:
            max_age_hours: Maximum age of history to keep in hours
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self._lock:
            tasks_to_remove = []
            
            for task_id, history in self.state_history.items():
                # Filter out old snapshots
                filtered_history = []
                for snapshot in history:
                    snapshot_time = datetime.fromisoformat(snapshot.updated_at).timestamp()
                    if snapshot_time > cutoff_time:
                        filtered_history.append(snapshot)
                
                if filtered_history:
                    self.state_history[task_id] = filtered_history
                else:
                    tasks_to_remove.append(task_id)
            
            # Remove tasks with no recent history
            for task_id in tasks_to_remove:
                del self.state_history[task_id]
    
    def get_all_active_tasks(self) -> Dict[str, TaskStatus]:
        """
        Get all active tasks from persistence.
        
        Returns:
            Dictionary of active task statuses
        """
        active_tasks = {}
        
        with self._lock:
            for task_id, snapshot in self.task_snapshots.items():
                task_status = snapshot.to_task_status()
                if task_status.is_active:
                    active_tasks[task_id] = task_status
        
        return active_tasks
    
    def get_persistence_stats(self) -> Dict[str, Any]:
        """
        Get persistence statistics.
        
        Returns:
            Dictionary with persistence statistics
        """
        with self._lock:
            total_history_entries = sum(len(history) for history in self.state_history.values())
            
            return {
                'enabled': self.enable_persistence,
                'active_snapshots': len(self.task_snapshots),
                'checkpoint_count': len(self.checkpoint_data),
                'tasks_with_history': len(self.state_history),
                'total_history_entries': total_history_entries,
                'last_checkpoint_time': self.last_checkpoint_time
            }
    
    def export_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Export all data for a specific task.
        
        Args:
            task_id: ID of the task to export
            
        Returns:
            Dictionary with all task data or None if not found
        """
        with self._lock:
            export_data = {}
            
            # Current snapshot
            if task_id in self.task_snapshots:
                export_data['current_state'] = asdict(self.task_snapshots[task_id])
            
            # Checkpoint data
            if task_id in self.checkpoint_data:
                export_data['checkpoint'] = self.checkpoint_data[task_id].copy()
            
            # History
            if task_id in self.state_history:
                export_data['history'] = [asdict(snapshot) for snapshot in self.state_history[task_id]]
            
            return export_data if export_data else None
    
    def import_task_data(self, task_id: str, task_data: Dict[str, Any]):
        """
        Import task data from external source.
        
        Args:
            task_id: ID of the task
            task_data: Task data to import
        """
        with self._lock:
            # Import current state
            if 'current_state' in task_data:
                snapshot_data = task_data['current_state']
                self.task_snapshots[task_id] = TaskSnapshot(**snapshot_data)
            
            # Import checkpoint
            if 'checkpoint' in task_data:
                self.checkpoint_data[task_id] = task_data['checkpoint'].copy()
            
            # Import history
            if 'history' in task_data:
                history = [TaskSnapshot(**snapshot_data) for snapshot_data in task_data['history']]
                self.state_history[task_id] = history


class TaskResultManager:
    """Manages task results and download functionality."""
    
    def __init__(self):
        """Initialize task result manager."""
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.result_files: Dict[str, List[str]] = {}
        self.download_links: Dict[str, str] = {}
        self._lock = threading.Lock()
    
    def store_task_result(self, task_id: str, result_data: Dict[str, Any], 
                         output_files: List[str]):
        """
        Store task result and output files.
        
        Args:
            task_id: ID of the completed task
            result_data: Result metadata
            output_files: List of output file paths
        """
        with self._lock:
            self.task_results[task_id] = {
                'timestamp': time.time(),
                'result_data': result_data.copy(),
                'file_count': len(output_files)
            }
            
            self.result_files[task_id] = output_files.copy()
            
            # Generate download link based on actual file path
            if output_files:
                # Use the first output file as the primary download
                primary_file = output_files[0]
                if os.path.exists(primary_file):
                    # Generate a proper download link based on the file location
                    # This assumes the file is in the outputs directory and accessible via web server
                    relative_path = os.path.relpath(primary_file, start='.')
                    self.download_links[task_id] = f"/api/download/{task_id}?file={relative_path}"
                    print(f"📎 生成下载链接: {self.download_links[task_id]}")
                else:
                    print(f"⚠️  警告: 输出文件不存在，无法生成下载链接: {primary_file}")
                    self.download_links[task_id] = None
            else:
                print(f"⚠️  警告: 没有输出文件，无法生成下载链接")
                self.download_links[task_id] = None
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result data for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Result data or None if not found
        """
        with self._lock:
            return self.task_results.get(task_id, {}).get('result_data')
    
    def get_result_files(self, task_id: str) -> List[str]:
        """
        Get output files for a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of output file paths
        """
        with self._lock:
            return self.result_files.get(task_id, []).copy()
    
    def get_download_link(self, task_id: str) -> Optional[str]:
        """
        Get download link for task results.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Download link or None if not available
        """
        with self._lock:
            return self.download_links.get(task_id)
    
    def cleanup_task_results(self, task_id: str):
        """
        Clean up results for a task.
        
        Args:
            task_id: ID of the task to clean up
        """
        with self._lock:
            if task_id in self.task_results:
                del self.task_results[task_id]
            
            if task_id in self.result_files:
                del self.result_files[task_id]
            
            if task_id in self.download_links:
                del self.download_links[task_id]
    
    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available task results.
        
        Returns:
            Dictionary mapping task IDs to result summaries
        """
        with self._lock:
            results = {}
            for task_id, result_info in self.task_results.items():
                results[task_id] = {
                    'timestamp': result_info['timestamp'],
                    'file_count': result_info['file_count'],
                    'download_link': self.download_links.get(task_id),
                    'has_files': task_id in self.result_files
                }
            return results