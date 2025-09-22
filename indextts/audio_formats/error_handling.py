"""
Enhanced error handling for audio generation and format conversion.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
from ..task_management.error_handler import (
    ErrorHandler, ErrorType, ErrorInfo, RetryStrategy, 
    ExponentialBackoffRetry, ImmediateRetry, FallbackStrategy
)

logger = logging.getLogger(__name__)


class AudioErrorType(Enum):
    """Specific error types for audio processing."""
    TTS_MODEL_LOADING_FAILED = "tts_model_loading_failed"
    TTS_INFERENCE_FAILED = "tts_inference_failed"
    AUDIO_FORMAT_CONVERSION_FAILED = "audio_format_conversion_failed"
    AUDIO_SEGMENTATION_FAILED = "audio_segmentation_failed"
    FFMPEG_ERROR = "ffmpeg_error"
    CODEC_NOT_AVAILABLE = "codec_not_available"
    INSUFFICIENT_MEMORY = "insufficient_memory"
    INVALID_AUDIO_INPUT = "invalid_audio_input"
    OUTPUT_PATH_ERROR = "output_path_error"
    VOICE_SAMPLE_ERROR = "voice_sample_error"


@dataclass
class AudioGenerationContext:
    """Context information for audio generation operations."""
    text_length: int
    voice_sample_path: str
    output_format: str
    generation_stage: str
    attempt_number: int = 1
    previous_errors: List[str] = None
    
    def __post_init__(self):
        if self.previous_errors is None:
            self.previous_errors = []


class AudioErrorHandler(ErrorHandler):
    """Enhanced error handler specifically for audio generation operations."""
    
    def __init__(self):
        """Initialize audio error handler with audio-specific strategies."""
        super().__init__()
        
        # Override with audio-specific retry strategies
        self.retry_strategies.update({
            ErrorType.TTS_GENERATION: ExponentialBackoffRetry(
                max_attempts=3, base_delay=2.0, max_delay=30.0
            ),
            ErrorType.FORMAT_CONVERSION: ExponentialBackoffRetry(
                max_attempts=2, base_delay=1.0, max_delay=10.0
            ),
            ErrorType.RESOURCE_ERROR: ExponentialBackoffRetry(
                max_attempts=2, base_delay=5.0, max_delay=60.0
            )
        })
        
        # Audio-specific fallback strategies
        self.fallback_strategies.update({
            ErrorType.FORMAT_CONVERSION: FallbackStrategy(['wav', 'mp3']),
            ErrorType.TTS_GENERATION: FallbackStrategy(['cpu_mode', 'reduced_batch_size', 'simplified_params'])
        })
        
        # Resource monitoring
        self.memory_threshold = 0.9  # 90% memory usage threshold
        self.gpu_memory_threshold = 0.85  # 85% GPU memory threshold
    
    def handle_audio_error(self, error_type: AudioErrorType, exception: Exception,
                          context: AudioGenerationContext) -> 'AudioErrorResponse':
        """
        Handle audio-specific errors with enhanced recovery strategies.
        
        Args:
            error_type: Specific audio error type
            exception: The exception that occurred
            context: Audio generation context
            
        Returns:
            AudioErrorResponse with recovery instructions
        """
        # Convert audio error type to general error type
        general_error_type = self._map_audio_error_type(error_type)
        
        # Create enhanced context
        enhanced_context = {
            'audio_error_type': error_type.value,
            'text_length': context.text_length,
            'voice_sample_path': context.voice_sample_path,
            'output_format': context.output_format,
            'generation_stage': context.generation_stage,
            'attempt_number': context.attempt_number,
            'previous_errors': context.previous_errors
        }
        
        # Handle the error using base handler
        base_response = self.handle_error(general_error_type, exception, enhanced_context)
        
        # Create audio-specific response
        audio_response = AudioErrorResponse(
            base_response=base_response,
            audio_error_type=error_type,
            context=context,
            recovery_actions=self._get_audio_recovery_actions(error_type, exception, context),
            fallback_options=self._get_audio_fallback_options(error_type, context)
        )
        
        return audio_response
    
    def _map_audio_error_type(self, audio_error_type: AudioErrorType) -> ErrorType:
        """Map audio-specific error types to general error types."""
        mapping = {
            AudioErrorType.TTS_MODEL_LOADING_FAILED: ErrorType.TTS_GENERATION,
            AudioErrorType.TTS_INFERENCE_FAILED: ErrorType.TTS_GENERATION,
            AudioErrorType.AUDIO_FORMAT_CONVERSION_FAILED: ErrorType.FORMAT_CONVERSION,
            AudioErrorType.AUDIO_SEGMENTATION_FAILED: ErrorType.FORMAT_CONVERSION,
            AudioErrorType.FFMPEG_ERROR: ErrorType.FORMAT_CONVERSION,
            AudioErrorType.CODEC_NOT_AVAILABLE: ErrorType.FORMAT_CONVERSION,
            AudioErrorType.INSUFFICIENT_MEMORY: ErrorType.RESOURCE_ERROR,
            AudioErrorType.INVALID_AUDIO_INPUT: ErrorType.VALIDATION_ERROR,
            AudioErrorType.OUTPUT_PATH_ERROR: ErrorType.FILE_PROCESSING,
            AudioErrorType.VOICE_SAMPLE_ERROR: ErrorType.VALIDATION_ERROR
        }
        return mapping.get(audio_error_type, ErrorType.UNKNOWN_ERROR)
    
    def _get_audio_recovery_actions(self, error_type: AudioErrorType, 
                                  exception: Exception, 
                                  context: AudioGenerationContext) -> List[str]:
        """Get specific recovery actions for audio errors."""
        actions = []
        
        if error_type == AudioErrorType.TTS_MODEL_LOADING_FAILED:
            actions.extend([
                "Verify model files are present and not corrupted",
                "Check available system memory",
                "Try restarting the application",
                "Ensure model files have correct permissions"
            ])
        
        elif error_type == AudioErrorType.TTS_INFERENCE_FAILED:
            actions.extend([
                "Reduce text length or split into smaller segments",
                "Check voice sample file validity",
                "Try different generation parameters",
                "Verify GPU/CPU resources are available"
            ])
        
        elif error_type == AudioErrorType.AUDIO_FORMAT_CONVERSION_FAILED:
            actions.extend([
                "Try converting to WAV format first",
                "Check if FFmpeg is properly installed",
                "Verify output directory permissions",
                "Use alternative audio codec"
            ])
        
        elif error_type == AudioErrorType.FFMPEG_ERROR:
            actions.extend([
                "Check FFmpeg installation and PATH",
                "Verify audio codec availability",
                "Try simpler conversion parameters",
                "Check input audio file integrity"
            ])
        
        elif error_type == AudioErrorType.INSUFFICIENT_MEMORY:
            actions.extend([
                "Reduce batch size or text length",
                "Close other applications to free memory",
                "Use CPU mode instead of GPU",
                "Process in smaller chunks"
            ])
        
        elif error_type == AudioErrorType.VOICE_SAMPLE_ERROR:
            actions.extend([
                "Verify voice sample file exists and is readable",
                "Check audio file format (WAV/MP3 supported)",
                "Ensure voice sample is not corrupted",
                "Try a different voice sample"
            ])
        
        return actions
    
    def _get_audio_fallback_options(self, error_type: AudioErrorType,
                                  context: AudioGenerationContext) -> Dict[str, Any]:
        """Get fallback options for audio errors."""
        fallbacks = {}
        
        if error_type == AudioErrorType.AUDIO_FORMAT_CONVERSION_FAILED:
            # Fallback to simpler formats
            if context.output_format == 'm4b':
                fallbacks['format'] = 'mp3'
            elif context.output_format == 'mp3':
                fallbacks['format'] = 'wav'
            
            fallbacks['bitrate'] = 64  # Lower bitrate for MP3
            fallbacks['codec'] = 'pcm_s16le'  # Simple codec for WAV
        
        elif error_type == AudioErrorType.TTS_INFERENCE_FAILED:
            # Fallback to simpler generation parameters
            fallbacks['batch_size'] = 1
            fallbacks['max_tokens'] = min(120, context.text_length // 4)
            fallbacks['use_cpu'] = True
            fallbacks['simplified_params'] = True
        
        elif error_type == AudioErrorType.INSUFFICIENT_MEMORY:
            # Memory-saving fallbacks
            fallbacks['use_cpu'] = True
            fallbacks['batch_size'] = 1
            fallbacks['chunk_size'] = min(100, context.text_length // 10)
        
        return fallbacks
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resources and return status."""
        import psutil
        
        try:
            # Check system memory
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100.0
            
            # Check disk space
            disk = psutil.disk_usage('/')
            disk_usage = (disk.total - disk.free) / disk.total
            
            # Check GPU memory if available
            gpu_memory_usage = 0.0
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.memory_stats()
                    allocated = gpu_memory.get('allocated_bytes.all.current', 0)
                    reserved = gpu_memory.get('reserved_bytes.all.current', 0)
                    max_memory = torch.cuda.get_device_properties(0).total_memory
                    gpu_memory_usage = max(allocated, reserved) / max_memory
            except ImportError:
                pass
            
            return {
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'gpu_memory_usage': gpu_memory_usage,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'resource_warnings': self._get_resource_warnings(memory_usage, disk_usage, gpu_memory_usage)
            }
            
        except Exception as e:
            logger.warning(f"Could not check system resources: {e}")
            return {
                'memory_usage': 0.0,
                'disk_usage': 0.0,
                'gpu_memory_usage': 0.0,
                'resource_warnings': ['Could not check system resources']
            }
    
    def _get_resource_warnings(self, memory_usage: float, disk_usage: float, 
                             gpu_memory_usage: float) -> List[str]:
        """Get resource usage warnings."""
        warnings = []
        
        if memory_usage > self.memory_threshold:
            warnings.append(f"High memory usage: {memory_usage:.1%}")
        
        if disk_usage > 0.9:
            warnings.append(f"Low disk space: {(1-disk_usage)*100:.1f}% free")
        
        if gpu_memory_usage > self.gpu_memory_threshold:
            warnings.append(f"High GPU memory usage: {gpu_memory_usage:.1%}")
        
        return warnings


@dataclass
class AudioErrorResponse:
    """Response from audio error handler with audio-specific recovery information."""
    base_response: 'ErrorResponse'
    audio_error_type: AudioErrorType
    context: AudioGenerationContext
    recovery_actions: List[str]
    fallback_options: Dict[str, Any]
    
    @property
    def should_retry(self) -> bool:
        """Check if the operation should be retried."""
        return self.base_response.should_retry
    
    @property
    def retry_delay(self) -> float:
        """Get delay before retry."""
        return self.base_response.retry_delay
    
    def get_user_friendly_message(self) -> str:
        """Get user-friendly error message."""
        error_messages = {
            AudioErrorType.TTS_MODEL_LOADING_FAILED: "Failed to load TTS model",
            AudioErrorType.TTS_INFERENCE_FAILED: "Audio generation failed",
            AudioErrorType.AUDIO_FORMAT_CONVERSION_FAILED: "Audio format conversion failed",
            AudioErrorType.FFMPEG_ERROR: "Audio processing error",
            AudioErrorType.INSUFFICIENT_MEMORY: "Insufficient system memory",
            AudioErrorType.VOICE_SAMPLE_ERROR: "Voice sample error"
        }
        
        base_message = error_messages.get(
            self.audio_error_type, 
            "Audio processing error"
        )
        
        if self.should_retry:
            return f"{base_message}. Retrying in {self.retry_delay:.1f} seconds..."
        else:
            return f"{base_message}. Please check the suggestions below."


class AudioGenerationRecoveryManager:
    """Manages recovery strategies for audio generation failures."""
    
    def __init__(self, error_handler: AudioErrorHandler):
        """Initialize recovery manager."""
        self.error_handler = error_handler
        self.recovery_history: Dict[str, List[AudioErrorResponse]] = {}
        self.successful_recoveries: Dict[str, Dict[str, Any]] = {}
    
    def attempt_recovery(self, operation_id: str, error_type: AudioErrorType,
                        exception: Exception, context: AudioGenerationContext) -> bool:
        """
        Attempt recovery from audio generation error.
        
        Args:
            operation_id: Unique identifier for the operation
            error_type: Type of audio error
            exception: The exception that occurred
            context: Audio generation context
            
        Returns:
            True if recovery should be attempted
        """
        # Track recovery history
        if operation_id not in self.recovery_history:
            self.recovery_history[operation_id] = []
        
        # Handle the error
        error_response = self.error_handler.handle_audio_error(error_type, exception, context)
        self.recovery_history[operation_id].append(error_response)
        
        # Check if we should attempt recovery
        if not error_response.should_retry:
            return False
        
        # Apply fallback options if available
        if error_response.fallback_options:
            self._apply_fallback_options(context, error_response.fallback_options)
        
        return True
    
    def _apply_fallback_options(self, context: AudioGenerationContext, 
                              fallback_options: Dict[str, Any]):
        """Apply fallback options to the context."""
        if 'format' in fallback_options:
            context.output_format = fallback_options['format']
        
        # Other fallback options would be applied to the actual generation parameters
        # This is a simplified example
    
    def get_recovery_suggestions(self, operation_id: str) -> List[str]:
        """Get recovery suggestions based on error history."""
        if operation_id not in self.recovery_history:
            return []
        
        suggestions = []
        error_history = self.recovery_history[operation_id]
        
        # Analyze error patterns
        error_types = [resp.audio_error_type for resp in error_history]
        
        if AudioErrorType.INSUFFICIENT_MEMORY in error_types:
            suggestions.extend([
                "Try processing smaller text segments",
                "Close other applications to free memory",
                "Use CPU mode instead of GPU"
            ])
        
        if AudioErrorType.AUDIO_FORMAT_CONVERSION_FAILED in error_types:
            suggestions.extend([
                "Try WAV format instead of MP3/M4B",
                "Check FFmpeg installation",
                "Verify output directory permissions"
            ])
        
        if len(error_history) > 2:
            suggestions.append("Consider restarting the application")
        
        return suggestions
    
    def record_successful_recovery(self, operation_id: str, 
                                 recovery_method: Dict[str, Any]):
        """Record a successful recovery for future reference."""
        self.successful_recoveries[operation_id] = recovery_method
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        total_operations = len(self.recovery_history)
        successful_recoveries = len(self.successful_recoveries)
        
        if total_operations == 0:
            return {'success_rate': 0.0, 'total_operations': 0}
        
        return {
            'success_rate': successful_recoveries / total_operations,
            'total_operations': total_operations,
            'successful_recoveries': successful_recoveries,
            'common_errors': self._get_common_error_types()
        }
    
    def _get_common_error_types(self) -> Dict[str, int]:
        """Get statistics on common error types."""
        error_counts = {}
        
        for error_list in self.recovery_history.values():
            for error_response in error_list:
                error_type = error_response.audio_error_type.value
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return error_counts


class AudioGenerationRetryWrapper:
    """Wrapper that adds retry logic to audio generation functions."""
    
    def __init__(self, recovery_manager: AudioGenerationRecoveryManager):
        """Initialize retry wrapper."""
        self.recovery_manager = recovery_manager
    
    def with_retry(self, func: Callable, operation_id: str, 
                  context: AudioGenerationContext, *args, **kwargs):
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            operation_id: Unique operation identifier
            context: Audio generation context
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result or raises final exception
        """
        last_exception = None
        
        for attempt in range(1, 4):  # Max 3 attempts
            try:
                context.attempt_number = attempt
                result = func(*args, **kwargs)
                
                # Record successful recovery if this wasn't the first attempt
                if attempt > 1:
                    self.recovery_manager.record_successful_recovery(
                        operation_id, {'attempt': attempt, 'context': context}
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Classify the error
                error_type = self._classify_audio_error(e)
                
                # Attempt recovery
                should_retry = self.recovery_manager.attempt_recovery(
                    operation_id, error_type, e, context
                )
                
                if not should_retry or attempt >= 3:
                    break
                
                # Wait before retry
                error_response = self.recovery_manager.recovery_history[operation_id][-1]
                if error_response.retry_delay > 0:
                    time.sleep(error_response.retry_delay)
        
        # All retries failed
        raise last_exception
    
    def _classify_audio_error(self, exception: Exception) -> AudioErrorType:
        """Classify exception into audio error type."""
        error_message = str(exception).lower()
        
        if 'memory' in error_message or 'out of memory' in error_message:
            return AudioErrorType.INSUFFICIENT_MEMORY
        elif 'ffmpeg' in error_message:
            return AudioErrorType.FFMPEG_ERROR
        elif 'codec' in error_message:
            return AudioErrorType.CODEC_NOT_AVAILABLE
        elif 'model' in error_message and 'load' in error_message:
            return AudioErrorType.TTS_MODEL_LOADING_FAILED
        elif 'inference' in error_message or 'generation' in error_message:
            return AudioErrorType.TTS_INFERENCE_FAILED
        elif 'format' in error_message or 'conversion' in error_message:
            return AudioErrorType.AUDIO_FORMAT_CONVERSION_FAILED
        elif 'voice' in error_message or 'sample' in error_message:
            return AudioErrorType.VOICE_SAMPLE_ERROR
        else:
            return AudioErrorType.TTS_INFERENCE_FAILED  # Default fallback


def create_resilient_audio_processor(tts_engine, format_converter):
    """
    Create a resilient audio processor with comprehensive error handling.
    
    Args:
        tts_engine: TTS engine instance
        format_converter: Audio format converter instance
        
    Returns:
        Resilient audio processor with error handling
    """
    error_handler = AudioErrorHandler()
    recovery_manager = AudioGenerationRecoveryManager(error_handler)
    retry_wrapper = AudioGenerationRetryWrapper(recovery_manager)
    
    class ResilientAudioProcessor:
        """Audio processor with comprehensive error handling and recovery."""
        
        def __init__(self):
            self.tts_engine = tts_engine
            self.format_converter = format_converter
            self.error_handler = error_handler
            self.recovery_manager = recovery_manager
            self.retry_wrapper = retry_wrapper
        
        def generate_audio_with_recovery(self, text: str, voice_prompt: str,
                                       output_path: str, **generation_params):
            """Generate audio with comprehensive error handling."""
            operation_id = f"gen_{int(time.time())}_{hash(text[:50])}"
            
            context = AudioGenerationContext(
                text_length=len(text),
                voice_sample_path=voice_prompt,
                output_format=generation_params.get('output_format', 'wav'),
                generation_stage='initialization'
            )
            
            def _generate():
                context.generation_stage = 'tts_generation'
                
                # Generate audio
                result_path = self.tts_engine.infer(
                    spk_audio_prompt=voice_prompt,
                    text=text,
                    output_path=output_path,
                    **generation_params
                )
                
                # Convert format if needed
                output_format = generation_params.get('output_format', 'wav')
                if output_format != 'wav' and result_path:
                    context.generation_stage = 'format_conversion'
                    result_path = self.format_converter.convert_to_format(
                        result_path, output_format, **generation_params
                    )
                
                return result_path
            
            return self.retry_wrapper.with_retry(_generate, operation_id, context)
        
        def get_system_status(self) -> Dict[str, Any]:
            """Get system status and resource information."""
            return self.error_handler.check_system_resources()
        
        def get_recovery_stats(self) -> Dict[str, Any]:
            """Get recovery statistics."""
            return self.recovery_manager.get_recovery_stats()
    
    return ResilientAudioProcessor()