"""
Comprehensive performance monitoring and optimization for incremental auto-save functionality.
"""

import os
import time
import psutil
import threading
import torch
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque


@dataclass
class PerformanceMetrics:
    """Container for system performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_read_mb: float
    disk_write_mb: float
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    gpu_utilization: float = 0.0
    save_operation_time: float = 0.0
    generation_step_time: float = 0.0
    error: Optional[str] = None


@dataclass
class SaveOperationStats:
    """Statistics for save operations."""
    operation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    file_size_mb: float = 0.0
    segments_saved: int = 0
    success: bool = False
    error_message: Optional[str] = None
    system_metrics: Optional[PerformanceMetrics] = None


@dataclass
class MemoryUsageStats:
    """Memory usage statistics during generation."""
    timestamp: datetime
    audio_buffer_size_mb: float
    temp_files_size_mb: float
    torch_cache_size_mb: float
    system_memory_percent: float
    peak_memory_mb: float = 0.0
    memory_growth_rate: float = 0.0  # MB per minute


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for auto-save operations.
    Tracks system resources, save operation impact, and provides adaptive optimization.
    """
    
    def __init__(self, history_size: int = 100, monitoring_interval: float = 1.0):
        """
        Initialize performance monitor.
        
        Args:
            history_size: Number of metrics to keep in history
            monitoring_interval: Interval between automatic measurements (seconds)
        """
        self.history_size = history_size
        self.monitoring_interval = monitoring_interval
        
        # Performance history
        self.metrics_history: deque = deque(maxlen=history_size)
        self.save_stats_history: deque = deque(maxlen=history_size)
        self.memory_stats_history: deque = deque(maxlen=history_size)
        
        # Thresholds for performance warnings
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.gpu_memory_threshold = 90.0
        self.save_time_threshold = 5.0  # seconds
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Performance callbacks
        self.performance_warning_callback: Optional[Callable] = None
        self.metrics_update_callback: Optional[Callable] = None
        
        # Background save executor
        self.background_executor = ThreadPoolExecutor(
            max_workers=2, 
            thread_name_prefix="AutoSave-Background"
        )
        
        # Current operation tracking
        self.current_save_operations: Dict[str, SaveOperationStats] = {}
        self.generation_start_time: Optional[datetime] = None
        self.last_step_time: Optional[datetime] = None
        
        # Peak usage tracking
        self.peak_memory_usage = 0.0
        self.peak_gpu_memory_usage = 0.0
        
        # Adaptive optimization state
        self.optimization_enabled = True
        self.last_optimization_check = datetime.now()
        self.optimization_check_interval = 10.0  # seconds
    
    def start_monitoring(self):
        """Start background performance monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="PerformanceMonitor",
            daemon=True
        )
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background performance monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        self._stop_monitoring.set()
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2.0)
            self._monitoring_thread = None
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._stop_monitoring.wait(self.monitoring_interval):
            try:
                metrics = self.collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Check for performance issues
                self._check_performance_warnings(metrics)
                
                # Update callbacks
                if self.metrics_update_callback:
                    self.metrics_update_callback(metrics)
                    
            except Exception as e:
                # Log error but continue monitoring
                error_metrics = PerformanceMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    memory_used_gb=0.0,
                    memory_available_gb=0.0,
                    disk_read_mb=0.0,
                    disk_write_mb=0.0,
                    error=str(e)
                )
                self.metrics_history.append(error_metrics)
    
    def collect_system_metrics(self) -> PerformanceMetrics:
        """
        Collect comprehensive system performance metrics.
        
        Returns:
            PerformanceMetrics object with current system state
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Update peak memory tracking
            self.peak_memory_usage = max(self.peak_memory_usage, memory_used_gb)
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0.0
            disk_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0.0
            
            # GPU metrics (if available)
            gpu_memory_used_mb = 0.0
            gpu_memory_total_mb = 0.0
            gpu_utilization = 0.0
            
            if torch.cuda.is_available():
                try:
                    gpu_memory_used_mb = torch.cuda.memory_allocated() / (1024**2)
                    gpu_memory_total_mb = torch.cuda.get_device_properties(0).total_memory / (1024**2)
                    gpu_utilization = (gpu_memory_used_mb / gpu_memory_total_mb) * 100 if gpu_memory_total_mb > 0 else 0.0
                    
                    # Update peak GPU memory tracking
                    self.peak_gpu_memory_usage = max(self.peak_gpu_memory_usage, gpu_memory_used_mb)
                except Exception:
                    pass  # GPU metrics not critical
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_available_gb=memory_available_gb,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                gpu_memory_used_mb=gpu_memory_used_mb,
                gpu_memory_total_mb=gpu_memory_total_mb,
                gpu_utilization=gpu_utilization
            )
            
            # Add to history automatically
            self.metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            error_metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                memory_available_gb=0.0,
                disk_read_mb=0.0,
                disk_write_mb=0.0,
                error=str(e)
            )
            self.metrics_history.append(error_metrics)
            return error_metrics
    
    def track_memory_usage(self, audio_buffer_size_mb: float = 0.0, 
                          temp_files_size_mb: float = 0.0) -> MemoryUsageStats:
        """
        Track memory usage specific to auto-save operations.
        
        Args:
            audio_buffer_size_mb: Size of audio buffer in MB
            temp_files_size_mb: Size of temporary files in MB
            
        Returns:
            MemoryUsageStats object
        """
        # Get torch cache size
        torch_cache_size_mb = 0.0
        if torch.cuda.is_available():
            try:
                torch_cache_size_mb = torch.cuda.memory_reserved() / (1024**2)
            except Exception:
                pass
        
        # Get system memory
        memory = psutil.virtual_memory()
        system_memory_percent = memory.percent
        
        # Calculate memory growth rate
        memory_growth_rate = 0.0
        if len(self.memory_stats_history) > 0:
            last_stats = self.memory_stats_history[-1]
            time_diff = (datetime.now() - last_stats.timestamp).total_seconds() / 60.0  # minutes
            if time_diff > 0:
                memory_diff = memory.used / (1024**2) - (last_stats.system_memory_percent * memory.total / (100 * 1024**2))
                memory_growth_rate = memory_diff / time_diff
        
        stats = MemoryUsageStats(
            timestamp=datetime.now(),
            audio_buffer_size_mb=audio_buffer_size_mb,
            temp_files_size_mb=temp_files_size_mb,
            torch_cache_size_mb=torch_cache_size_mb,
            system_memory_percent=system_memory_percent,
            peak_memory_mb=self.peak_memory_usage * 1024,  # Convert GB to MB
            memory_growth_rate=memory_growth_rate
        )
        
        self.memory_stats_history.append(stats)
        return stats
    
    def start_save_operation(self, operation_id: Optional[str] = None) -> str:
        """
        Start tracking a save operation.
        
        Args:
            operation_id: Optional operation ID, will generate if not provided
            
        Returns:
            Operation ID for tracking
        """
        if operation_id is None:
            operation_id = f"save_{int(time.time() * 1000)}"
        
        # Collect current system metrics
        system_metrics = self.collect_system_metrics()
        
        save_stats = SaveOperationStats(
            operation_id=operation_id,
            start_time=datetime.now(),
            system_metrics=system_metrics
        )
        
        self.current_save_operations[operation_id] = save_stats
        return operation_id
    
    def end_save_operation(self, operation_id: str, success: bool = True, 
                          file_size_mb: float = 0.0, segments_saved: int = 0,
                          error_message: Optional[str] = None):
        """
        End tracking of a save operation.
        
        Args:
            operation_id: Operation ID from start_save_operation
            success: Whether the operation succeeded
            file_size_mb: Size of saved file in MB
            segments_saved: Number of audio segments saved
            error_message: Error message if operation failed
        """
        if operation_id not in self.current_save_operations:
            return
        
        save_stats = self.current_save_operations[operation_id]
        save_stats.end_time = datetime.now()
        save_stats.duration = max(0.001, (save_stats.end_time - save_stats.start_time).total_seconds())
        save_stats.success = success
        save_stats.file_size_mb = file_size_mb
        save_stats.segments_saved = segments_saved
        save_stats.error_message = error_message
        
        # Move to history
        self.save_stats_history.append(save_stats)
        del self.current_save_operations[operation_id]
        
        # Check if save took too long
        if save_stats.duration > self.save_time_threshold and self.performance_warning_callback:
            self.performance_warning_callback(
                f"Save operation took {save_stats.duration:.2f}s (threshold: {self.save_time_threshold}s)"
            )
    
    def execute_background_save(self, save_function: Callable, *args, **kwargs) -> Future:
        """
        Execute a save operation in the background.
        
        Args:
            save_function: Function to execute for saving
            *args: Arguments for save function
            **kwargs: Keyword arguments for save function
            
        Returns:
            Future object for the background operation
        """
        operation_id = self.start_save_operation()
        
        def wrapped_save():
            try:
                result = save_function(*args, **kwargs)
                self.end_save_operation(operation_id, success=True)
                return result
            except Exception as e:
                self.end_save_operation(operation_id, success=False, error_message=str(e))
                raise
        
        return self.background_executor.submit(wrapped_save)
    
    def _check_performance_warnings(self, metrics: PerformanceMetrics):
        """
        Check for performance issues and trigger warnings.
        
        Args:
            metrics: Current performance metrics
        """
        warnings = []
        
        if metrics.cpu_percent > self.cpu_threshold:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.memory_threshold:
            warnings.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.gpu_utilization > self.gpu_memory_threshold:
            warnings.append(f"High GPU memory usage: {metrics.gpu_utilization:.1f}%")
        
        # Check for long-running save operations
        for op_id, save_stats in self.current_save_operations.items():
            duration = (datetime.now() - save_stats.start_time).total_seconds()
            if duration > self.save_time_threshold:
                warnings.append(f"Save operation {op_id} running for {duration:.1f}s")
        
        # Trigger warnings if callback is set
        if warnings and self.performance_warning_callback:
            for warning in warnings:
                self.performance_warning_callback(warning)
    
    def is_system_under_load(self) -> bool:
        """
        Check if system is currently under high load.
        
        Returns:
            True if system is under high load
        """
        if not self.metrics_history:
            metrics = self.collect_system_metrics()
        else:
            metrics = self.metrics_history[-1]
        
        return (
            metrics.cpu_percent > self.cpu_threshold or
            metrics.memory_percent > self.memory_threshold or
            metrics.gpu_utilization > self.gpu_memory_threshold
        )
    
    def get_adaptive_save_interval(self, base_interval: int) -> int:
        """
        Calculate adaptive save interval based on system performance.
        
        Args:
            base_interval: Base save interval
            
        Returns:
            Adjusted save interval
        """
        if not self.optimization_enabled:
            return base_interval
        
        # Check if we should perform optimization check
        now = datetime.now()
        if (now - self.last_optimization_check).total_seconds() < self.optimization_check_interval:
            return base_interval
        
        self.last_optimization_check = now
        
        # Get recent performance metrics
        if len(self.metrics_history) < 3:
            return base_interval
        
        recent_metrics = list(self.metrics_history)[-3:]
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_gpu = sum(m.gpu_utilization for m in recent_metrics) / len(recent_metrics)
        
        # Calculate load factor (0.0 to 1.0+)
        load_factor = max(avg_cpu, avg_memory, avg_gpu) / 100.0
        
        # Adjust interval based on load
        if load_factor > 0.8:
            # High load - increase interval (save less frequently)
            return min(base_interval + 2, 10)
        elif load_factor < 0.4:
            # Low load - decrease interval (save more frequently)
            return max(base_interval - 1, 1)
        else:
            return base_interval
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance statistics
        """
        summary = {
            'monitoring_active': self._monitoring_active,
            'metrics_collected': len(self.metrics_history),
            'save_operations_tracked': len(self.save_stats_history),
            'memory_snapshots': len(self.memory_stats_history),
            'peak_memory_gb': self.peak_memory_usage,
            'peak_gpu_memory_mb': self.peak_gpu_memory_usage,
            'current_save_operations': len(self.current_save_operations)
        }
        
        # Current metrics
        if self.metrics_history:
            current = self.metrics_history[-1]
            summary['current_metrics'] = {
                'cpu_percent': current.cpu_percent,
                'memory_percent': current.memory_percent,
                'gpu_utilization': current.gpu_utilization,
                'timestamp': current.timestamp.isoformat()
            }
        
        # Save operation statistics
        if self.save_stats_history:
            successful_saves = [s for s in self.save_stats_history if s.success]
            failed_saves = [s for s in self.save_stats_history if not s.success]
            
            if successful_saves:
                avg_save_time = sum(s.duration for s in successful_saves) / len(successful_saves)
                total_data_saved = sum(s.file_size_mb for s in successful_saves)
                
                summary['save_statistics'] = {
                    'total_saves': len(self.save_stats_history),
                    'successful_saves': len(successful_saves),
                    'failed_saves': len(failed_saves),
                    'success_rate': len(successful_saves) / len(self.save_stats_history) * 100,
                    'avg_save_time': avg_save_time,
                    'total_data_saved_mb': total_data_saved
                }
        
        # Memory usage trends
        if self.memory_stats_history:
            recent_memory = list(self.memory_stats_history)[-10:]  # Last 10 measurements
            avg_growth_rate = sum(m.memory_growth_rate for m in recent_memory) / len(recent_memory)
            
            summary['memory_trends'] = {
                'avg_growth_rate_mb_per_min': avg_growth_rate,
                'current_buffer_size_mb': recent_memory[-1].audio_buffer_size_mb if recent_memory else 0,
                'current_temp_files_mb': recent_memory[-1].temp_files_size_mb if recent_memory else 0
            }
        
        return summary
    
    def set_callbacks(self, performance_warning_callback: Optional[Callable] = None,
                     metrics_update_callback: Optional[Callable] = None):
        """
        Set callback functions for performance events.
        
        Args:
            performance_warning_callback: Function to call for performance warnings
            metrics_update_callback: Function to call when metrics are updated
        """
        self.performance_warning_callback = performance_warning_callback
        self.metrics_update_callback = metrics_update_callback
    
    def cleanup(self):
        """Clean up resources and stop monitoring."""
        self.stop_monitoring()
        self.background_executor.shutdown(wait=True)
        self.current_save_operations.clear()
        self.metrics_history.clear()
        self.save_stats_history.clear()
        self.memory_stats_history.clear()
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()