"""
Error handling and retry strategies for background tasks.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum


class ErrorType(Enum):
    """Types of errors that can occur during task processing."""
    TTS_GENERATION = "tts_generation"
    FILE_PROCESSING = "file_processing"
    FORMAT_CONVERSION = "format_conversion"
    NETWORK_ERROR = "network_error"
    RESOURCE_ERROR = "resource_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorInfo:
    """Information about an error that occurred."""
    error_type: ErrorType
    exception: Exception
    context: Dict[str, Any]
    timestamp: float
    retry_count: int = 0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class RetryStrategy(ABC):
    """Abstract base class for retry strategies."""
    
    @abstractmethod
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if the error should be retried."""
        pass
    
    @abstractmethod
    def get_delay(self, retry_count: int) -> float:
        """Get delay before next retry attempt."""
        pass
    
    @abstractmethod
    def get_max_attempts(self) -> int:
        """Get maximum number of retry attempts."""
        pass


class ExponentialBackoffRetry(RetryStrategy):
    """Exponential backoff retry strategy."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        """
        Initialize exponential backoff retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Exponential backoff factor
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Check if error should be retried."""
        return error_info.retry_count < self.max_attempts
    
    def get_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)
    
    def get_max_attempts(self) -> int:
        """Get maximum retry attempts."""
        return self.max_attempts


class ImmediateRetry(RetryStrategy):
    """Immediate retry strategy with no delay."""
    
    def __init__(self, max_attempts: int = 2):
        """
        Initialize immediate retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
        """
        self.max_attempts = max_attempts
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Check if error should be retried."""
        return error_info.retry_count < self.max_attempts
    
    def get_delay(self, retry_count: int) -> float:
        """No delay for immediate retry."""
        return 0.0
    
    def get_max_attempts(self) -> int:
        """Get maximum retry attempts."""
        return self.max_attempts


class FallbackStrategy:
    """Fallback strategy for when primary approach fails."""
    
    def __init__(self, fallback_options: List[Any]):
        """
        Initialize fallback strategy.
        
        Args:
            fallback_options: List of fallback options to try
        """
        self.fallback_options = fallback_options
        self.current_index = 0
    
    def get_next_option(self) -> Optional[Any]:
        """Get next fallback option."""
        if self.current_index < len(self.fallback_options):
            option = self.fallback_options[self.current_index]
            self.current_index += 1
            return option
        return None
    
    def has_more_options(self) -> bool:
        """Check if more fallback options are available."""
        return self.current_index < len(self.fallback_options)
    
    def reset(self):
        """Reset to first fallback option."""
        self.current_index = 0


class ErrorHandler:
    """Centralized error handling with recovery strategies."""
    
    def __init__(self):
        """Initialize error handler."""
        self.retry_strategies: Dict[ErrorType, RetryStrategy] = {
            ErrorType.TTS_GENERATION: ExponentialBackoffRetry(max_attempts=3, base_delay=2.0),
            ErrorType.FILE_PROCESSING: ImmediateRetry(max_attempts=2),
            ErrorType.FORMAT_CONVERSION: ExponentialBackoffRetry(max_attempts=2, base_delay=1.0),
            ErrorType.NETWORK_ERROR: ExponentialBackoffRetry(max_attempts=5, base_delay=1.0),
            ErrorType.RESOURCE_ERROR: ExponentialBackoffRetry(max_attempts=3, base_delay=5.0),
            ErrorType.VALIDATION_ERROR: ImmediateRetry(max_attempts=0),  # Don't retry validation errors
            ErrorType.UNKNOWN_ERROR: ExponentialBackoffRetry(max_attempts=2, base_delay=1.0)
        }
        
        self.fallback_strategies: Dict[ErrorType, FallbackStrategy] = {
            ErrorType.FORMAT_CONVERSION: FallbackStrategy(['wav', 'mp3']),
            ErrorType.TTS_GENERATION: FallbackStrategy(['cpu', 'fallback_model'])
        }
        
        self.error_callbacks: List[Callable] = []
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error_type: ErrorType, exception: Exception, 
                    context: Dict[str, Any]) -> 'ErrorResponse':
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            error_type: Type of error that occurred
            exception: The exception that was raised
            context: Additional context about the error
            
        Returns:
            ErrorResponse with recovery instructions
        """
        error_info = ErrorInfo(
            error_type=error_type,
            exception=exception,
            context=context,
            timestamp=time.time()
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Notify error callbacks
        self._notify_error_callbacks(error_info)
        
        # Determine recovery strategy
        retry_strategy = self.retry_strategies.get(error_type)
        fallback_strategy = self.fallback_strategies.get(error_type)
        
        response = ErrorResponse(
            error_info=error_info,
            should_retry=retry_strategy.should_retry(error_info) if retry_strategy else False,
            retry_delay=retry_strategy.get_delay(error_info.retry_count) if retry_strategy else 0.0,
            fallback_option=fallback_strategy.get_next_option() if fallback_strategy else None,
            recovery_suggestions=self._get_recovery_suggestions(error_type, exception)
        )
        
        return response
    
    def classify_error(self, exception: Exception, context: Dict[str, Any]) -> ErrorType:
        """
        Classify an exception into an error type.
        
        Args:
            exception: The exception to classify
            context: Additional context
            
        Returns:
            Classified error type
        """
        exception_name = type(exception).__name__
        error_message = str(exception).lower()
        
        # File processing errors
        if any(keyword in error_message for keyword in ['encoding', 'decode', 'file not found', 'permission']):
            return ErrorType.FILE_PROCESSING
        
        # Network errors
        if any(keyword in error_message for keyword in ['connection', 'timeout', 'network', 'dns']):
            return ErrorType.NETWORK_ERROR
        
        # Resource errors
        if any(keyword in error_message for keyword in ['memory', 'disk', 'cuda', 'out of memory']):
            return ErrorType.RESOURCE_ERROR
        
        # Validation errors
        if any(keyword in error_message for keyword in ['invalid', 'validation', 'format']):
            return ErrorType.VALIDATION_ERROR
        
        # TTS generation errors (based on context)
        if context.get('stage') in ['tts_generation', 'inference', 'model_loading']:
            return ErrorType.TTS_GENERATION
        
        # Format conversion errors
        if context.get('stage') in ['format_conversion', 'audio_processing']:
            return ErrorType.FORMAT_CONVERSION
        
        return ErrorType.UNKNOWN_ERROR
    
    def add_error_callback(self, callback: Callable):
        """
        Add callback for error notifications.
        
        Args:
            callback: Function to call when errors occur
        """
        self.error_callbacks.append(callback)
    
    def update_retry_strategy(self, error_type: ErrorType, strategy: RetryStrategy):
        """
        Update retry strategy for an error type.
        
        Args:
            error_type: Type of error
            strategy: New retry strategy
        """
        self.retry_strategies[error_type] = strategy
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error information."""
        self.logger.error(
            f"Error occurred: {error_info.error_type.value} - {error_info.exception} "
            f"(retry count: {error_info.retry_count})"
        )
        
        if error_info.context:
            self.logger.debug(f"Error context: {error_info.context}")
    
    def _notify_error_callbacks(self, error_info: ErrorInfo):
        """Notify registered error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.warning(f"Error in error callback: {e}")
    
    def _get_recovery_suggestions(self, error_type: ErrorType, exception: Exception) -> List[str]:
        """
        Get recovery suggestions for an error type.
        
        Args:
            error_type: Type of error
            exception: The exception that occurred
            
        Returns:
            List of recovery suggestions
        """
        suggestions = []
        
        if error_type == ErrorType.TTS_GENERATION:
            suggestions.extend([
                "Check if model files are properly loaded",
                "Verify input text format and length",
                "Try reducing batch size or text length"
            ])
        
        elif error_type == ErrorType.FILE_PROCESSING:
            suggestions.extend([
                "Check file permissions and accessibility",
                "Verify file format and encoding",
                "Ensure sufficient disk space"
            ])
        
        elif error_type == ErrorType.FORMAT_CONVERSION:
            suggestions.extend([
                "Try alternative output format",
                "Check audio codec availability",
                "Verify output directory permissions"
            ])
        
        elif error_type == ErrorType.RESOURCE_ERROR:
            suggestions.extend([
                "Free up system memory",
                "Check GPU memory availability",
                "Reduce processing batch size"
            ])
        
        elif error_type == ErrorType.NETWORK_ERROR:
            suggestions.extend([
                "Check internet connection",
                "Verify server availability",
                "Try again after a short delay"
            ])
        
        return suggestions


@dataclass
class ErrorResponse:
    """Response from error handler with recovery instructions."""
    error_info: ErrorInfo
    should_retry: bool
    retry_delay: float
    fallback_option: Optional[Any]
    recovery_suggestions: List[str]
    
    def __post_init__(self):
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []


class TaskRecoveryManager:
    """Manages task recovery and state restoration."""
    
    def __init__(self, error_handler: ErrorHandler):
        """
        Initialize task recovery manager.
        
        Args:
            error_handler: Error handler instance
        """
        self.error_handler = error_handler
        self.recovery_attempts: Dict[str, int] = {}
        self.failed_tasks: Dict[str, ErrorInfo] = {}
    
    def attempt_recovery(self, task_id: str, error_type: ErrorType, 
                        exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from a task error.
        
        Args:
            task_id: ID of the failed task
            error_type: Type of error that occurred
            exception: The exception that was raised
            context: Additional context about the error
            
        Returns:
            True if recovery should be attempted, False otherwise
        """
        # Track recovery attempts
        if task_id not in self.recovery_attempts:
            self.recovery_attempts[task_id] = 0
        
        self.recovery_attempts[task_id] += 1
        
        # Handle the error
        error_response = self.error_handler.handle_error(error_type, exception, context)
        
        # Store error info for failed tasks
        if not error_response.should_retry:
            self.failed_tasks[task_id] = error_response.error_info
            return False
        
        return True
    
    def get_recovery_delay(self, task_id: str, error_type: ErrorType) -> float:
        """
        Get delay before retry attempt.
        
        Args:
            task_id: ID of the task
            error_type: Type of error
            
        Returns:
            Delay in seconds before retry
        """
        retry_count = self.recovery_attempts.get(task_id, 0)
        strategy = self.error_handler.retry_strategies.get(error_type)
        
        if strategy:
            return strategy.get_delay(retry_count)
        
        return 0.0
    
    def cleanup_task_recovery(self, task_id: str):
        """
        Clean up recovery tracking for a completed task.
        
        Args:
            task_id: ID of the task to clean up
        """
        if task_id in self.recovery_attempts:
            del self.recovery_attempts[task_id]
        
        if task_id in self.failed_tasks:
            del self.failed_tasks[task_id]
    
    def get_failed_tasks(self) -> Dict[str, ErrorInfo]:
        """Get information about failed tasks."""
        return self.failed_tasks.copy()
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        return {
            'active_recoveries': len(self.recovery_attempts),
            'failed_tasks': len(self.failed_tasks),
            'total_recovery_attempts': sum(self.recovery_attempts.values())
        }