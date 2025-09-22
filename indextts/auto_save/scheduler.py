"""
Save scheduling and step tracking for incremental auto-save functionality.
"""

import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta

from .config import AutoSaveConfig
from .performance_monitor import PerformanceMonitor


class SaveScheduler:
    """
    Manages save scheduling with configurable interval management and adaptive adjustment.
    """
    
    def __init__(self, config: AutoSaveConfig, performance_monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize the save scheduler.
        
        Args:
            config: Auto-save configuration
            performance_monitor: Optional performance monitor for adaptive scheduling
        """
        self.config = config
        self.performance_monitor = performance_monitor or PerformanceMonitor(
            history_size=50,
            monitoring_interval=2.0
        )
        
        # Current scheduling state
        self.base_interval = config.save_interval
        self.adaptive_interval = config.save_interval
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # Step tracking
        self.current_step = 0
        self.last_save_step = 0
        self.total_segments = 0
        
        # Performance tracking
        self.last_performance_check = datetime.now()
        self.performance_check_interval = 5.0  # seconds
        
        # Save timing statistics
        self.save_times = []
        self.max_save_time_history = 10
        
        # Callbacks
        self.interval_change_callback: Optional[Callable] = None
        self.performance_warning_callback: Optional[Callable] = None
    
    def update_step(self, step: int, total_segments: Optional[int] = None):
        """
        Update current step count.
        
        Args:
            step: Current generation step
            total_segments: Total number of segments (if known)
        """
        self.current_step = step
        if total_segments is not None:
            self.total_segments = total_segments
    
    def should_trigger_save(self, current_step: Optional[int] = None) -> bool:
        """
        Determine if save should be triggered based on current conditions.
        
        Args:
            current_step: Optional override for current step
            
        Returns:
            True if save should be triggered
        """
        if not self.config.enabled:
            return False
        
        step = current_step if current_step is not None else self.current_step
        
        # Don't save on step 0
        if step == 0:
            return False
        
        # Check if enough steps have passed since last save
        steps_since_last_save = step - self.last_save_step
        
        # Use adaptive interval if performance monitoring is enabled
        interval_to_use = self.adaptive_interval if self.config.performance_adaptive else self.base_interval
        
        should_save = steps_since_last_save >= interval_to_use
        
        # If we should save, check system performance
        if should_save and self.config.performance_adaptive:
            # Check if we should delay save due to high system load
            if self._should_delay_save_for_performance():
                return False
        
        return should_save
    
    def _should_delay_save_for_performance(self) -> bool:
        """
        Check if save should be delayed due to system performance.
        
        Returns:
            True if save should be delayed
        """
        now = datetime.now()
        
        # Only check performance periodically to avoid overhead
        if (now - self.last_performance_check).total_seconds() < self.performance_check_interval:
            return False
        
        self.last_performance_check = now
        
        # Check if system is under high load
        if self.performance_monitor.is_system_under_load():
            # Use adaptive interval calculation
            adaptive_interval = self.performance_monitor.get_adaptive_save_interval(self.base_interval)
            if adaptive_interval > self.adaptive_interval:
                self.adaptive_interval = adaptive_interval
                
                if self.performance_warning_callback:
                    self.performance_warning_callback(
                        f"High system load detected, adjusting save interval to {self.adaptive_interval}"
                    )
            
            return True
        
        return False
    
    def adjust_interval_for_performance(self, system_load: Optional[float] = None):
        """
        Dynamically adjust save interval based on system performance.
        
        Args:
            system_load: Optional system load metric (0.0-100.0)
        """
        if not self.config.performance_adaptive:
            return
        
        # Use the enhanced performance monitor's adaptive calculation
        new_adaptive_interval = self.performance_monitor.get_adaptive_save_interval(self.base_interval)
        
        if new_adaptive_interval != self.adaptive_interval:
            old_interval = self.adaptive_interval
            self.adaptive_interval = new_adaptive_interval
            
            if self.interval_change_callback:
                self.interval_change_callback(
                    f"Save interval adjusted from {old_interval} to {self.adaptive_interval} steps based on system performance"
                )
    
    def _adjust_interval_for_performance(self, increase: bool):
        """
        Adjust the adaptive interval based on performance conditions.
        
        Args:
            increase: True to increase interval (save less frequently), False to decrease
        """
        old_interval = self.adaptive_interval
        
        if increase:
            # Increase interval but don't exceed max
            self.adaptive_interval = min(self.config.max_interval, self.adaptive_interval + 1)
        else:
            # Decrease interval but don't go below base interval
            self.adaptive_interval = max(self.base_interval, self.adaptive_interval - 1)
        
        # Notify if interval changed
        if self.adaptive_interval != old_interval and self.interval_change_callback:
            self.interval_change_callback(
                f"Save interval adjusted from {old_interval} to {self.adaptive_interval} steps"
            )
    
    def handle_save_success(self, save_time: float):
        """
        Handle successful save operation.
        
        Args:
            save_time: Time taken for save operation in seconds
        """
        self.last_save_step = self.current_step
        self.consecutive_failures = 0
        
        # Track save timing
        self.save_times.append(save_time)
        if len(self.save_times) > self.max_save_time_history:
            self.save_times.pop(0)
        
        # If saves are consistently fast and system load is low, consider reducing interval
        if self.config.performance_adaptive and len(self.save_times) >= 3:
            avg_save_time = sum(self.save_times) / len(self.save_times)
            if avg_save_time < 1.0 and not self.performance_monitor.is_system_under_load():
                self._adjust_interval_for_performance(increase=False)
    
    def handle_save_failure(self, error_message: str):
        """
        Handle save failure and adjust strategy.
        
        Args:
            error_message: Error message from failed save
        """
        self.consecutive_failures += 1
        
        # If we have too many consecutive failures, increase interval to reduce save frequency
        if self.consecutive_failures >= self.max_consecutive_failures:
            self._adjust_interval_for_performance(increase=True)
            
            if self.performance_warning_callback:
                self.performance_warning_callback(
                    f"Multiple save failures detected, increasing save interval to {self.adaptive_interval}"
                )
    
    def reset_failure_count(self):
        """Reset failure count after successful save."""
        self.consecutive_failures = 0
    
    def get_next_save_step(self) -> int:
        """
        Get the step number when next save should occur.
        
        Returns:
            Step number for next save
        """
        interval_to_use = self.adaptive_interval if self.config.performance_adaptive else self.base_interval
        return self.last_save_step + interval_to_use
    
    def get_steps_until_next_save(self) -> int:
        """
        Get number of steps until next save.
        
        Returns:
            Number of steps until next save
        """
        return max(0, self.get_next_save_step() - self.current_step)
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status and statistics.
        
        Returns:
            Dictionary with scheduler status information
        """
        avg_save_time = sum(self.save_times) / len(self.save_times) if self.save_times else 0.0
        
        status = {
            'enabled': self.config.enabled,
            'base_interval': self.base_interval,
            'adaptive_interval': self.adaptive_interval,
            'performance_adaptive': self.config.performance_adaptive,
            'current_step': self.current_step,
            'last_save_step': self.last_save_step,
            'next_save_step': self.get_next_save_step(),
            'steps_until_next_save': self.get_steps_until_next_save(),
            'consecutive_failures': self.consecutive_failures,
            'total_segments': self.total_segments,
            'avg_save_time': avg_save_time,
            'save_count': len(self.save_times)
        }
        
        # Add performance metrics if available
        if self.performance_monitor:
            try:
                performance_summary = self.performance_monitor.get_performance_summary()
                status['performance'] = performance_summary
                status['performance']['under_load'] = self.performance_monitor.is_system_under_load()
            except Exception as e:
                status['performance'] = {'error': str(e)}
        
        return status
    
    def set_callbacks(self, interval_change_callback: Optional[Callable] = None,
                     performance_warning_callback: Optional[Callable] = None):
        """
        Set callback functions for scheduler events.
        
        Args:
            interval_change_callback: Function to call when interval changes
            performance_warning_callback: Function to call for performance warnings
        """
        self.interval_change_callback = interval_change_callback
        self.performance_warning_callback = performance_warning_callback
    
    def reset_scheduler(self):
        """Reset scheduler state for new generation."""
        self.current_step = 0
        self.last_save_step = 0
        self.total_segments = 0
        self.consecutive_failures = 0
        self.adaptive_interval = self.base_interval
        self.save_times.clear()
        
        # Start performance monitoring for new generation
        if hasattr(self.performance_monitor, 'start_monitoring'):
            self.performance_monitor.start_monitoring()