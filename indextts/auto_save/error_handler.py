"""
Error handling and recovery mechanisms for incremental auto-save functionality.
"""

import os
import time
import shutil
import tempfile
import torch
import torchaudio
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from pathlib import Path

from .config import AutoSaveConfig, SaveProgress, SaveOperation
from .file_manager import AutoSaveFileManager


class AutoSaveErrorHandler:
    """
    Manages save failures and recovery mechanisms for auto-save operations.
    Implements requirements 5.1, 5.2, 5.3, 5.4, 5.5.
    """
    
    def __init__(self, save_manager: 'IncrementalSaveManager'):
        """
        Initialize the error handler.
        
        Args:
            save_manager: Reference to the incremental save manager
        """
        self.save_manager = save_manager
        
        # Fallback save locations in order of preference
        self.fallback_locations = [
            os.path.expanduser("~/tmp/indextts_autosave"),
            tempfile.gettempdir(),
            "./temp_autosave"
        ]
        
        # Retry configuration
        self.max_retry_attempts = 3
        self.base_retry_delay = 1.0  # seconds
        self.max_retry_delay = 8.0  # seconds
        self.backoff_multiplier = 2.0
        
        # Error tracking
        self.error_history: List[Dict[str, Any]] = []
        self.max_error_history = 20
        self.consecutive_failures = 0
        self.last_error_time: Optional[datetime] = None
        
        # Recovery state
        self.recovery_mode = False
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        
        # Callbacks
        self.error_callback: Optional[Callable] = None
        self.recovery_callback: Optional[Callable] = None
        self.warning_callback: Optional[Callable] = None
    
    def handle_save_failure(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle save failure with appropriate recovery strategy.
        Implements requirement 5.1: log error but continue generation.
        
        Args:
            error: Exception that caused the save failure
            context: Context information about the failed save operation
            
        Returns:
            Dictionary with recovery action results
        """
        error_info = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context.copy(),
            'step': context.get('step', 0),
            'retry_attempted': False,
            'fallback_attempted': False,
            'recovery_successful': False
        }
        
        # Add to error history
        self._add_to_error_history(error_info)
        
        # Update failure tracking
        self.consecutive_failures += 1
        self.last_error_time = error_info['timestamp']
        
        # Determine recovery strategy based on error type and context
        recovery_result = self._determine_recovery_strategy(error, context)
        error_info.update(recovery_result)
        
        # Execute recovery strategy
        if recovery_result['strategy'] == 'retry':
            retry_result = self._attempt_retry_save(error, context)
            error_info['retry_attempted'] = True
            error_info['retry_result'] = retry_result
            error_info['recovery_successful'] = retry_result.get('success', False)
            
        elif recovery_result['strategy'] == 'fallback':
            fallback_result = self._attempt_fallback_save(error, context)
            error_info['fallback_attempted'] = True
            error_info['fallback_result'] = fallback_result
            error_info['recovery_successful'] = fallback_result.get('success', False)
            
        elif recovery_result['strategy'] == 'skip':
            # Skip this save and continue generation
            error_info['recovery_successful'] = True
            error_info['action'] = 'skipped_save_continuing_generation'
        
        # Initialize attempt flags if not set
        if 'retry_attempted' not in error_info:
            error_info['retry_attempted'] = False
        if 'fallback_attempted' not in error_info:
            error_info['fallback_attempted'] = False
        
        # Notify callbacks
        if self.error_callback:
            self.error_callback(error_info)
        
        # Check if we should enter recovery mode
        if self.consecutive_failures >= 3 and not self.recovery_mode:
            self._enter_recovery_mode()
        
        return error_info
    
    def _determine_recovery_strategy(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the best recovery strategy based on error type and context.
        
        Args:
            error: Exception that occurred
            context: Context information
            
        Returns:
            Dictionary with recovery strategy information
        """
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        strategy_info = {
            'strategy': 'skip',  # Default: skip and continue
            'reason': 'unknown_error',
            'priority': 'low'
        }
        
        # Disk space issues - try fallback location
        if 'no space left' in error_message or 'disk full' in error_message:
            strategy_info.update({
                'strategy': 'fallback',
                'reason': 'disk_space_full',
                'priority': 'high'
            })
        
        # Permission errors - try fallback location
        elif 'permission denied' in error_message or 'access denied' in error_message:
            strategy_info.update({
                'strategy': 'fallback',
                'reason': 'permission_denied',
                'priority': 'high'
            })
        
        # File system errors - retry with exponential backoff
        elif any(fs_error in error_message for fs_error in ['file exists', 'directory not found', 'path too long', 'filesystem error', 'temporary']):
            strategy_info.update({
                'strategy': 'retry',
                'reason': 'filesystem_error',
                'priority': 'medium'
            })
        
        # Network/remote storage issues - retry with backoff
        elif any(net_error in error_message for net_error in ['network', 'timeout', 'connection']):
            strategy_info.update({
                'strategy': 'retry',
                'reason': 'network_error',
                'priority': 'medium'
            })
        
        # Memory issues - skip this save to preserve resources
        elif 'memory' in error_message or 'out of memory' in error_message:
            strategy_info.update({
                'strategy': 'skip',
                'reason': 'memory_error',
                'priority': 'high'
            })
        
        # Audio processing errors - retry once
        elif any(audio_error in error_message for audio_error in ['audio', 'tensor', 'sample rate']):
            if self.consecutive_failures < 2:
                strategy_info.update({
                    'strategy': 'retry',
                    'reason': 'audio_processing_error',
                    'priority': 'medium'
                })
        
        return strategy_info
    
    def _attempt_retry_save(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to retry save operation with exponential backoff.
        Implements requirement 5.3: retry logic with exponential backoff.
        
        Args:
            error: Original error
            context: Save operation context
            
        Returns:
            Dictionary with retry results
        """
        retry_result = {
            'success': False,
            'attempts': 0,
            'total_delay': 0.0,
            'final_error': None,
            'errors': []
        }
        
        audio_data = context.get('audio_data')
        step = context.get('step', 0)
        
        if audio_data is None or (hasattr(audio_data, 'numel') and audio_data.numel() == 0):
            retry_result['final_error'] = "No audio data available for retry"
            return retry_result
        
        for attempt in range(self.max_retry_attempts):
            retry_result['attempts'] += 1
            
            # Calculate delay with exponential backoff
            delay = min(
                self.base_retry_delay * (self.backoff_multiplier ** attempt),
                self.max_retry_delay
            )
            
            if attempt > 0:
                time.sleep(delay)
                retry_result['total_delay'] += delay
            
            try:
                # Attempt the save operation again
                if hasattr(self.save_manager, 'file_manager') and self.save_manager.file_manager:
                    temp_path = self.save_manager.file_manager.save_audio_incremental(
                        audio_data, step, self.save_manager.audio_buffer.sampling_rate
                    )
                    
                    # Validate the saved file
                    validation = self.save_manager.file_manager.validate_audio_file(temp_path)
                    if validation['valid']:
                        retry_result['success'] = True
                        retry_result['file_path'] = temp_path
                        return retry_result
                    else:
                        raise RuntimeError(f"Validation failed: {validation['errors']}")
                else:
                    raise RuntimeError("File manager not available for retry")
                    
            except Exception as retry_error:
                retry_result['errors'].append({
                    'attempt': attempt + 1,
                    'error': str(retry_error),
                    'delay': delay
                })
                retry_result['final_error'] = str(retry_error)
        
        return retry_result
    
    def _attempt_fallback_save(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to save to fallback location when primary location fails.
        Implements requirement 5.2: fallback save locations.
        
        Args:
            error: Original error
            context: Save operation context
            
        Returns:
            Dictionary with fallback save results
        """
        fallback_result = {
            'success': False,
            'location_used': None,
            'attempts': 0,
            'errors': []
        }
        
        audio_data = context.get('audio_data')
        step = context.get('step', 0)
        
        if audio_data is None or (hasattr(audio_data, 'numel') and audio_data.numel() == 0):
            fallback_result['errors'].append("No audio data available for fallback save")
            return fallback_result
        
        # Try each fallback location
        for location in self.fallback_locations:
            fallback_result['attempts'] += 1
            
            try:
                # Ensure fallback directory exists and is writable
                if not self._ensure_fallback_directory(location):
                    fallback_result['errors'].append(f"Cannot access fallback location: {location}")
                    continue
                
                # Generate filename for fallback save
                base_name = Path(self.save_manager.output_path).stem if self.save_manager.output_path else "autosave"
                filename = f"{base_name}_fallback_step_{step:04d}.wav"
                fallback_path = os.path.join(location, filename)
                
                # Ensure audio is in correct format
                if audio_data.dim() == 1:
                    audio_data = audio_data.unsqueeze(0)
                audio_data = torch.clamp(audio_data, -1.0, 1.0)
                
                # Save to fallback location
                torchaudio.save(fallback_path, audio_data, self.save_manager.audio_buffer.sampling_rate)
                
                # Validate the saved file
                if os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 0:
                    # Quick validation - try to load the file
                    test_audio, test_sr = torchaudio.load(fallback_path)
                    if test_audio.numel() > 0 and test_sr > 0:
                        fallback_result['success'] = True
                        fallback_result['location_used'] = location
                        fallback_result['file_path'] = fallback_path
                        
                        # Update save manager's file manager to use fallback location
                        if hasattr(self.save_manager, 'file_manager') and self.save_manager.file_manager:
                            self.save_manager.file_manager.temp_dir = location
                            self.save_manager.file_manager.current_temp_file = fallback_path
                        
                        return fallback_result
                
                fallback_result['errors'].append(f"Validation failed for fallback save at {fallback_path}")
                
            except Exception as fallback_error:
                fallback_result['errors'].append(f"Fallback save failed at {location}: {str(fallback_error)}")
                continue
        
        return fallback_result
    
    def _ensure_fallback_directory(self, directory: str) -> bool:
        """
        Ensure fallback directory exists and is writable.
        
        Args:
            directory: Directory path to check/create
            
        Returns:
            True if directory is accessible and writable
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Test write access
            test_file = os.path.join(directory, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            return True
            
        except Exception:
            return False
    
    def recover_partial_generation(self) -> Dict[str, Any]:
        """
        Attempt to recover from partial generation failure.
        Implements requirement 5.4: recovery mechanisms for partial generation failures.
        
        Returns:
            Dictionary with recovery information and available partial audio
        """
        recovery_info = {
            'success': False,
            'partial_audio_available': False,
            'recovery_file_path': None,
            'recovered_duration': 0.0,
            'recovery_method': None,
            'errors': []
        }
        
        try:
            # Check if file manager has recoverable data
            if hasattr(self.save_manager, 'file_manager') and self.save_manager.file_manager:
                file_recovery = self.save_manager.file_manager.recover_from_backup()
                
                if file_recovery['success']:
                    recovery_info.update({
                        'success': True,
                        'partial_audio_available': True,
                        'recovery_file_path': file_recovery['backup_path'],
                        'recovery_method': 'file_backup',
                        'validation': file_recovery['validation']
                    })
                    
                    if file_recovery['validation']:
                        recovery_info['recovered_duration'] = file_recovery['validation'].get('duration_seconds', 0.0)
                    
                    return recovery_info
                else:
                    recovery_info['errors'].extend(file_recovery['errors'])
            
            # Try to recover from audio buffer
            if hasattr(self.save_manager, 'audio_buffer') and self.save_manager.audio_buffer:
                buffer_recovery = self._recover_from_audio_buffer()
                
                if buffer_recovery['success']:
                    recovery_info.update({
                        'success': True,
                        'partial_audio_available': True,
                        'recovery_file_path': buffer_recovery['file_path'],
                        'recovered_duration': buffer_recovery['duration'],
                        'recovery_method': 'audio_buffer'
                    })
                    
                    return recovery_info
                else:
                    recovery_info['errors'].extend(buffer_recovery['errors'])
            
            # Try to find any existing auto-save files
            fallback_recovery = self._recover_from_fallback_locations()
            if fallback_recovery['success']:
                recovery_info.update({
                    'success': True,
                    'partial_audio_available': True,
                    'recovery_file_path': fallback_recovery['file_path'],
                    'recovered_duration': fallback_recovery['duration'],
                    'recovery_method': 'fallback_search'
                })
                
                return recovery_info
            else:
                recovery_info['errors'].extend(fallback_recovery['errors'])
            
            recovery_info['errors'].append("No recoverable partial audio found")
            
        except Exception as e:
            recovery_info['errors'].append(f"Recovery attempt failed: {str(e)}")
        
        return recovery_info
    
    def _recover_from_audio_buffer(self) -> Dict[str, Any]:
        """
        Attempt to recover audio from the current audio buffer.
        
        Returns:
            Dictionary with buffer recovery results
        """
        buffer_recovery = {
            'success': False,
            'file_path': None,
            'duration': 0.0,
            'errors': []
        }
        
        try:
            if not self.save_manager.audio_buffer:
                buffer_recovery['errors'].append("No audio buffer available")
                return buffer_recovery
            
            # Get current audio from buffer
            current_audio = self.save_manager.audio_buffer.get_current_audio()
            
            if current_audio is None or current_audio.numel() == 0:
                buffer_recovery['errors'].append("Audio buffer is empty")
                return buffer_recovery
            
            # Create emergency save file
            emergency_dir = self.fallback_locations[0]  # Use first fallback location
            if not self._ensure_fallback_directory(emergency_dir):
                emergency_dir = tempfile.gettempdir()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_filename = f"emergency_recovery_{timestamp}.wav"
            emergency_path = os.path.join(emergency_dir, emergency_filename)
            
            # Ensure audio is in correct format
            if current_audio.dim() == 1:
                current_audio = current_audio.unsqueeze(0)
            current_audio = torch.clamp(current_audio, -1.0, 1.0)
            
            # Save emergency recovery file
            torchaudio.save(emergency_path, current_audio, self.save_manager.audio_buffer.sampling_rate)
            
            # Validate the saved file
            if os.path.exists(emergency_path) and os.path.getsize(emergency_path) > 0:
                duration = current_audio.shape[-1] / self.save_manager.audio_buffer.sampling_rate
                
                buffer_recovery.update({
                    'success': True,
                    'file_path': emergency_path,
                    'duration': duration
                })
            else:
                buffer_recovery['errors'].append("Emergency save file validation failed")
            
        except Exception as e:
            buffer_recovery['errors'].append(f"Buffer recovery failed: {str(e)}")
        
        return buffer_recovery
    
    def _recover_from_fallback_locations(self) -> Dict[str, Any]:
        """
        Search fallback locations for any existing auto-save files.
        
        Returns:
            Dictionary with fallback recovery results
        """
        fallback_recovery = {
            'success': False,
            'file_path': None,
            'duration': 0.0,
            'errors': []
        }
        
        # Search patterns for auto-save files
        search_patterns = [
            "*_incremental.wav",
            "*_step_*.wav",
            "*_fallback_*.wav",
            "emergency_recovery_*.wav"
        ]
        
        for location in self.fallback_locations:
            if not os.path.exists(location):
                continue
            
            try:
                # Find the most recent auto-save file
                latest_file = None
                latest_time = 0
                
                for pattern in search_patterns:
                    import glob
                    pattern_path = os.path.join(location, pattern)
                    files = glob.glob(pattern_path)
                    
                    for file_path in files:
                        try:
                            file_time = os.path.getmtime(file_path)
                            if file_time > latest_time:
                                # Validate the file before considering it
                                test_audio, test_sr = torchaudio.load(file_path)
                                if test_audio.numel() > 0 and test_sr > 0:
                                    latest_file = file_path
                                    latest_time = file_time
                        except Exception:
                            continue
                
                if latest_file:
                    # Calculate duration
                    audio, sr = torchaudio.load(latest_file)
                    duration = audio.shape[-1] / sr
                    
                    fallback_recovery.update({
                        'success': True,
                        'file_path': latest_file,
                        'duration': duration
                    })
                    
                    return fallback_recovery
                    
            except Exception as e:
                fallback_recovery['errors'].append(f"Search failed in {location}: {str(e)}")
                continue
        
        fallback_recovery['errors'].append("No recoverable files found in fallback locations")
        return fallback_recovery
    
    def _enter_recovery_mode(self):
        """Enter recovery mode after multiple consecutive failures."""
        self.recovery_mode = True
        self.recovery_attempts = 0
        
        if self.warning_callback:
            self.warning_callback(
                f"Entering recovery mode after {self.consecutive_failures} consecutive save failures"
            )
    
    def _exit_recovery_mode(self):
        """Exit recovery mode after successful operation."""
        self.recovery_mode = False
        self.recovery_attempts = 0
        self.consecutive_failures = 0
        
        if self.recovery_callback:
            self.recovery_callback("Exited recovery mode - auto-save operations restored")
    
    def _add_to_error_history(self, error_info: Dict[str, Any]):
        """Add error information to history."""
        self.error_history.append(error_info)
        
        # Limit history size
        if len(self.error_history) > self.max_error_history:
            self.error_history.pop(0)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics and recovery information.
        
        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'consecutive_failures': 0,
                'recovery_mode': self.recovery_mode,
                'error_types': {},
                'recovery_success_rate': 0.0
            }
        
        # Count error types
        error_types = {}
        successful_recoveries = 0
        
        for error in self.error_history:
            error_type = error.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            if error.get('recovery_successful', False):
                successful_recoveries += 1
        
        recovery_rate = successful_recoveries / len(self.error_history) if self.error_history else 0.0
        
        return {
            'total_errors': len(self.error_history),
            'consecutive_failures': self.consecutive_failures,
            'recovery_mode': self.recovery_mode,
            'recovery_attempts': self.recovery_attempts,
            'error_types': error_types,
            'recovery_success_rate': recovery_rate,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'fallback_locations': self.fallback_locations
        }
    
    def set_callbacks(self, error_callback: Optional[Callable] = None,
                     recovery_callback: Optional[Callable] = None,
                     warning_callback: Optional[Callable] = None):
        """
        Set callback functions for error handling events.
        
        Args:
            error_callback: Function to call when errors occur
            recovery_callback: Function to call for recovery events
            warning_callback: Function to call for warnings
        """
        self.error_callback = error_callback
        self.recovery_callback = recovery_callback
        self.warning_callback = warning_callback
    
    def reset_error_state(self):
        """Reset error tracking state."""
        self.consecutive_failures = 0
        self.last_error_time = None
        self.recovery_mode = False
        self.recovery_attempts = 0
        
        if self.recovery_callback:
            self.recovery_callback("Error state reset - auto-save monitoring restarted")
    
    def validate_recovery_options(self) -> Dict[str, Any]:
        """
        Validate available recovery options and their status.
        Implements requirement 5.5: validate integrity of auto-saved files.
        
        Returns:
            Dictionary with recovery options validation
        """
        validation_result = {
            'file_manager_backup': {'available': False, 'valid': False},
            'audio_buffer': {'available': False, 'valid': False},
            'fallback_files': {'available': False, 'valid': False, 'count': 0},
            'overall_recovery_possible': False
        }
        
        # Check file manager backup
        if hasattr(self.save_manager, 'file_manager') and self.save_manager.file_manager:
            recovery_status = self.save_manager.file_manager.get_recovery_status()
            validation_result['file_manager_backup'] = {
                'available': recovery_status['temp_file_exists'] or recovery_status['valid_backups'] > 0,
                'valid': recovery_status['temp_file_valid'] or recovery_status['valid_backups'] > 0,
                'details': recovery_status
            }
        
        # Check audio buffer
        if hasattr(self.save_manager, 'audio_buffer') and self.save_manager.audio_buffer:
            buffer_info = self.save_manager.audio_buffer.get_buffer_info()
            validation_result['audio_buffer'] = {
                'available': buffer_info['segment_count'] > 0,
                'valid': buffer_info['total_duration'] > 0,
                'details': buffer_info
            }
        
        # Check fallback locations
        fallback_check = self._recover_from_fallback_locations()
        validation_result['fallback_files'] = {
            'available': fallback_check['success'],
            'valid': fallback_check['success'],
            'count': 1 if fallback_check['success'] else 0,
            'details': fallback_check
        }
        
        # Determine if any recovery is possible
        validation_result['overall_recovery_possible'] = any([
            validation_result['file_manager_backup']['valid'],
            validation_result['audio_buffer']['valid'],
            validation_result['fallback_files']['valid']
        ])
        
        return validation_result
    
    def cleanup(self):
        """
        Clean up error handler resources.
        Implements requirement 6.6: proper resource cleanup.
        """
        try:
            # Clear error history
            self.error_history.clear()
            
            # Reset error state
            self.reset_error_state()
            
            # Clear callbacks
            self.error_callback = None
            self.recovery_callback = None
            self.warning_callback = None
            
            # Clear save manager reference
            self.save_manager = None
            
        except Exception as e:
            # Log cleanup error if possible
            print(f"Warning: Error during error handler cleanup: {e}")