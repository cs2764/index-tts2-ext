"""
Progress tracking and console output for background tasks.
"""

import time
import threading
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ProgressStage:
    """Represents a processing stage with timing information."""
    name: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress: float = 0.0
    substages: List[str] = None
    
    def __post_init__(self):
        if self.substages is None:
            self.substages = []
    
    @property
    def duration(self) -> Optional[float]:
        """Get stage duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if stage is currently active."""
        return self.start_time is not None and self.end_time is None


class ProgressTracker:
    """Tracks progress and provides detailed console output for tasks."""
    
    def __init__(self, task_id: str, console_callback: Optional[Callable] = None):
        """
        Initialize progress tracker.
        
        Args:
            task_id: ID of the task being tracked
            console_callback: Optional callback for console output
        """
        self.task_id = task_id
        self.console_callback = console_callback or self._default_console_output
        self.start_time = time.time()
        self.stages: Dict[str, ProgressStage] = {}
        self.current_stage: Optional[str] = None
        self.overall_progress = 0.0
        self.estimated_total_time: Optional[float] = None
        self.batch_timings: List[Dict] = []
        self._last_substage: Optional[str] = None
        self._lock = threading.Lock()
    
    def start_stage(self, stage_name: str, substages: Optional[List[str]] = None):
        """
        Start a new processing stage.
        
        Args:
            stage_name: Name of the stage
            substages: Optional list of substage names
        """
        with self._lock:
            # End current stage if exists
            if self.current_stage and self.current_stage in self.stages:
                self.stages[self.current_stage].end_time = time.time()
            
            # Start new stage
            stage = ProgressStage(
                name=stage_name,
                start_time=time.time(),
                substages=substages or []
            )
            self.stages[stage_name] = stage
            self.current_stage = stage_name
            self._last_substage = None
            
            self._log_stage_start(stage_name, substages)
            # Emit an initial status line for the new stage at 0%
            self._log_status_line()
    
    def update_stage_progress(self, progress: float, substage: Optional[str] = None):
        """
        Update progress for current stage.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            substage: Optional substage description
        """
        with self._lock:
            if self.current_stage and self.current_stage in self.stages:
                stage = self.stages[self.current_stage]
                stage.progress = max(0.0, min(1.0, progress))
                
                if substage:
                    self._last_substage = substage
                    self._log_substage_progress(substage, progress)
                
                # Update overall progress based on stage weights
                self._update_overall_progress()
                # Emit compact single-line status
                self._log_status_line()
    
    def complete_stage(self, stage_name: Optional[str] = None):
        """
        Complete a processing stage.
        
        Args:
            stage_name: Name of stage to complete (current stage if None)
        """
        with self._lock:
            target_stage = stage_name or self.current_stage
            if target_stage and target_stage in self.stages:
                stage = self.stages[target_stage]
                stage.end_time = time.time()
                stage.progress = 1.0
                
                self._log_stage_completion(target_stage, stage.duration)
                
                if target_stage == self.current_stage:
                    self.current_stage = None
    
    def add_batch_timing(self, batch_info: Dict):
        """
        Add timing information for a batch operation.
        
        Args:
            batch_info: Dictionary with batch timing data
        """
        with self._lock:
            self.batch_timings.append({
                'timestamp': time.time(),
                'elapsed_total': time.time() - self.start_time,
                **batch_info
            })
            
            self._log_batch_timing(batch_info)
    
    def estimate_remaining_time(self) -> Optional[float]:
        """
        Estimate remaining processing time based on current progress.
        
        Returns:
            Estimated remaining time in seconds, or None if cannot estimate
        """
        if self.overall_progress <= 0:
            return None
        
        elapsed = time.time() - self.start_time
        if self.overall_progress >= 1.0:
            return 0.0
        
        # Simple linear estimation
        total_estimated = elapsed / self.overall_progress
        remaining = total_estimated - elapsed
        
        return max(0.0, remaining)
    
    def get_progress_summary(self) -> Dict:
        """
        Get comprehensive progress summary.
        
        Returns:
            Dictionary with progress information
        """
        with self._lock:
            elapsed = time.time() - self.start_time
            remaining = self.estimate_remaining_time()
            current_stage_name = self.current_stage
            stage_progress = 0.0
            if current_stage_name and current_stage_name in self.stages:
                stage_progress = self.stages[current_stage_name].progress
            
            return {
                'task_id': self.task_id,
                'overall_progress': self.overall_progress,
                'current_stage': {
                    'name': current_stage_name,
                    'progress': stage_progress,
                    'current_step': self._last_substage or ''
                },
                'status_line': self._build_status_line(),
                'elapsed_time': elapsed,
                'estimated_remaining': remaining,
                'stages': {
                    name: {
                        'progress': stage.progress,
                        'duration': stage.duration,
                        'is_active': stage.is_active
                    }
                    for name, stage in self.stages.items()
                },
                'batch_timings': self.batch_timings.copy(),
                'batch_count': len(self.batch_timings)
            }
    
    def _update_overall_progress(self):
        """Update overall progress based on stage progress."""
        if not self.stages:
            self.overall_progress = 0.0
            return
        
        # Define stage weights (can be customized)
        stage_weights = {
            'Text Processing': 0.1,
            'Model Loading': 0.1,
            'Audio Generation': 0.7,
            'Format Conversion': 0.05,
            'File Saving': 0.05
        }
        
        total_progress = 0.0
        total_weight = 0.0
        
        for stage_name, stage in self.stages.items():
            weight = stage_weights.get(stage_name, 1.0 / len(self.stages))
            total_progress += stage.progress * weight
            total_weight += weight
        
        if total_weight > 0:
            self.overall_progress = total_progress / total_weight
    
    def _log_stage_start(self, stage_name: str, substages: Optional[List[str]]):
        """Log stage start to console."""
        elapsed = time.time() - self.start_time
        message = f"[{self._format_time(elapsed)}] Starting stage: {stage_name}"
        
        if substages:
            message += f" (substages: {', '.join(substages)})"
        
        self.console_callback(message)
    
    def _log_substage_progress(self, substage: str, progress: float):
        """Log substage progress to console."""
        elapsed = time.time() - self.start_time
        percentage = progress * 100
        message = f"[{self._format_time(elapsed)}] {substage}: {percentage:.1f}%"
        
        remaining = self.estimate_remaining_time()
        if remaining:
            message += f" (ETA: {self._format_time(remaining)})"
        
        self.console_callback(message)
    
    def _log_stage_completion(self, stage_name: str, duration: Optional[float]):
        """Log stage completion to console."""
        elapsed = time.time() - self.start_time
        message = f"[{self._format_time(elapsed)}] Completed stage: {stage_name}"
        
        if duration:
            message += f" (took {self._format_time(duration)})"
        
        self.console_callback(message)
    
    def _log_batch_timing(self, batch_info: Dict):
        """Log batch timing information to console."""
        elapsed = time.time() - self.start_time
        
        # Extract relevant timing info
        batch_num = batch_info.get('batch_number', '?')
        batch_time = batch_info.get('batch_time', 0)
        total_batches = batch_info.get('total_batches', '?')
        
        message = f"[{self._format_time(elapsed)}] Batch {batch_num}/{total_batches} "
        message += f"completed in {self._format_time(batch_time)}"
        
        # Add throughput info if available
        if 'items_processed' in batch_info and batch_time > 0:
            throughput = batch_info['items_processed'] / batch_time
            message += f" ({throughput:.1f} items/sec)"
        
        self.console_callback(message)
        # Also emit a compact status line for consistency
        self._log_status_line()
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration for display."""
        if seconds is None:
            return "?"
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"
    
    def _build_status_line(self) -> str:
        """Build a compact single-line status summary for console and UI."""
        elapsed = time.time() - self.start_time
        remaining = self.estimate_remaining_time()
        stage = self.current_stage or "Initializing"
        # Determine stage progress
        stage_progress = 0.0
        if self.current_stage and self.current_stage in self.stages:
            stage_progress = self.stages[self.current_stage].progress
        percent = max(0.0, min(100.0, self.overall_progress * 100))
        parts = [
            f"{percent:.1f}%",
            f"Stage: {stage}",
            f"Elapsed: {self._format_time(elapsed)}"
        ]
        if remaining is not None:
            parts.append(f"ETA: {self._format_time(remaining)}")
        if self._last_substage:
            parts.append(f"Step: {self._last_substage}")
        return " | ".join(parts)
    
    def _log_status_line(self):
        """Emit the compact status line to the console callback."""
        self.console_callback(self._build_status_line())
    
    def _default_console_output(self, message: str):
        """Default console output function."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Task {self.task_id}: {message}")


class ConsoleOutputManager:
    """Manages console output for multiple tasks."""
    
    def __init__(self):
        """Initialize console output manager."""
        self.active_tasks: Dict[str, ProgressTracker] = {}
        self.output_callbacks: List[Callable] = []
        self.console_history: Dict[str, List[Dict]] = {}
        self._lock = threading.Lock()
    
    def register_task(self, task_id: str) -> ProgressTracker:
        """
        Register a new task for progress tracking.
        
        Args:
            task_id: ID of the task
            
        Returns:
            ProgressTracker instance for the task
        """
        with self._lock:
            # Initialize history buffer for this task
            self.console_history[task_id] = []
            
            # Wrap console output to capture per-task messages
            def task_console_output(message: str):
                self._console_output_for_task(task_id, message)
            
            tracker = ProgressTracker(
                task_id=task_id,
                console_callback=task_console_output
            )
            self.active_tasks[task_id] = tracker
            return tracker
    
    def unregister_task(self, task_id: str):
        """
        Unregister a completed task.
        
        Args:
            task_id: ID of the task to unregister
        """
        with self._lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def add_output_callback(self, callback: Callable):
        """
        Add callback for console output.
        
        Args:
            callback: Function to call with console messages
        """
        with self._lock:
            self.output_callbacks.append(callback)
    
    def get_task_progress(self, task_id: str) -> Optional[Dict]:
        """
        Get progress summary for a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Progress summary dictionary or None if task not found
        """
        with self._lock:
            tracker = self.active_tasks.get(task_id)
            if not tracker:
                return None
            summary = tracker.get_progress_summary()
            # Attach recent console messages
            summary['console_messages'] = self.console_history.get(task_id, [])
            return summary
    
    def get_all_progress(self) -> Dict[str, Dict]:
        """
        Get progress summaries for all active tasks.
        
        Returns:
            Dictionary mapping task IDs to progress summaries
        """
        with self._lock:
            data = {}
            for task_id, tracker in self.active_tasks.items():
                summary = tracker.get_progress_summary()
                summary['console_messages'] = self.console_history.get(task_id, [])
                data[task_id] = summary
            return data
    
    def _console_output_for_task(self, task_id: str, message: str, level: str = 'info'):
        """Handle console output and store per-task history."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {"timestamp": timestamp, "message": message, "level": level}
        # Keep last 100 messages per task
        history = self.console_history.setdefault(task_id, [])
        history.append(entry)
        if len(history) > 100:
            del history[0:len(history)-100]
        
        # Fan out to external callbacks
        for callback in self.output_callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"Error in console output callback: {e}")
