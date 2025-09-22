"""
Incremental save manager for IndexTTS2 auto-save functionality.
"""

import os
import time
import uuid
import torch
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

from .config import AutoSaveConfig, SaveProgress, AudioSegmentInfo, SaveOperation
from .audio_buffer import AudioBufferManager
from .file_manager import AutoSaveFileManager
from .scheduler import SaveScheduler
from .performance_monitor import PerformanceMonitor
from .error_handler import AutoSaveErrorHandler
from .notification_system import AutoSaveNotificationSystem


class IncrementalSaveManager:
    """Manages incremental saving of audio generation progress."""
    
    def __init__(self, save_interval: int = 5, enabled: bool = True, 
                 output_path: Optional[str] = None, voice_name: Optional[str] = None,
                 source_filename: Optional[str] = None):
        """
        Initialize the incremental save manager.
        
        Args:
            save_interval: Steps between saves (1-10)
            enabled: Whether auto-save is enabled
            output_path: Base output path for saved files
            voice_name: Name of the voice being used for generation
            source_filename: Original source filename if from uploaded file
        """
        self.config = AutoSaveConfig(
            enabled=enabled,
            save_interval=max(1, min(10, save_interval))
        )
        
        self.current_step = 0
        self.last_save_step = 0
        self.output_path = output_path
        self.temp_path: Optional[str] = None
        
        # Store naming information for consistent filename generation
        self.voice_name = voice_name
        self.source_filename = source_filename
        
        # Initialize components
        self.audio_buffer = AudioBufferManager()
        self.file_manager: Optional[AutoSaveFileManager] = None
        
        # Initialize enhanced performance monitoring
        self.performance_monitor = PerformanceMonitor(
            history_size=100,
            monitoring_interval=1.0
        )
        self.scheduler = SaveScheduler(self.config, self.performance_monitor)
        
        # Background save operations are now handled by the performance monitor
        # Keep this for backward compatibility
        self.save_thread_pool = self.performance_monitor.background_executor
        
        # Progress tracking
        self.save_progress: Optional[SaveProgress] = None
        self.last_save_info: Optional[Dict[str, Any]] = None
        
        # Error handling
        self.error_handler: Optional[AutoSaveErrorHandler] = None
        
        # Notification system
        self.notification_system: Optional[AutoSaveNotificationSystem] = None
        
        # Callbacks
        self.progress_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.console_callback: Optional[Callable] = None
    
    def initialize_generation(self, output_path: str, voice_name: Optional[str] = None,
                             source_filename: Optional[str] = None):
        """
        Initialize auto-save for a new generation.
        
        Args:
            output_path: Path where final output will be saved
            voice_name: Name of the voice being used for generation
            source_filename: Original source filename if from uploaded file
        """
        self.output_path = output_path
        self.voice_name = voice_name or self.voice_name
        self.source_filename = source_filename or self.source_filename
        self.file_manager = AutoSaveFileManager(output_path)
        
        # Set naming information in file manager
        self.file_manager.set_naming_info(self.voice_name, self.source_filename)
        
        # Initialize error handler
        self.error_handler = AutoSaveErrorHandler(self)
        
        # Initialize notification system
        self.notification_system = AutoSaveNotificationSystem(self.console_callback)
        
        # Reset state
        self.current_step = 0
        self.last_save_step = 0
        self.audio_buffer.clear_buffer()
        
        # Reset scheduler for new generation
        self.scheduler.reset_scheduler()
        
        # Set up performance monitoring callbacks
        self.performance_monitor.set_callbacks(
            performance_warning_callback=self.error_callback,
            metrics_update_callback=None  # Can be set later if needed
        )
        
        # Initialize progress tracking
        self.save_progress = SaveProgress(
            current_step=0,
            last_save_step=0,
            next_save_step=self.config.save_interval,
            total_segments=0,
            saved_duration=0.0,
            save_file_path=None,
            last_save_timestamp=datetime.now(),
            save_success=True,
            error_message=None
        )    

    def should_save(self) -> bool:
        """
        Check if current step requires auto-save.
        
        Returns:
            True if save should be triggered
        """
        # Delegate to scheduler for more sophisticated logic
        return self.scheduler.should_trigger_save(self.current_step)
    
    def add_audio_segment(self, audio_data: torch.Tensor, step: int, 
                         segment_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add new audio segment and trigger save if needed.
        
        Args:
            audio_data: Audio tensor for this segment
            step: Current generation step
            segment_info: Optional metadata about the segment
            
        Returns:
            True if save was triggered, False otherwise
        """
        if not self.config.enabled:
            return False
        
        self.current_step = step
        
        # Update scheduler with current step
        self.scheduler.update_step(step, len(self.audio_buffer.audio_segments) + 1)
        
        # Add segment to buffer
        if segment_info is None:
            segment_info = {}
        
        segment_info.update({
            'step': step,
            'generation_time': time.time()
        })
        
        self.audio_buffer.add_segment(audio_data, segment_info)
        
        # Update progress
        if self.save_progress:
            self.save_progress.current_step = step
            self.save_progress.total_segments = len(self.audio_buffer.audio_segments)
            self.save_progress.next_save_step = self.scheduler.get_next_save_step()
        
        # Check if save is needed
        if self.should_save():
            return self._trigger_save()
        
        return False
    
    def _trigger_save(self) -> bool:
        """
        Trigger incremental save operation with performance monitoring.
        
        Returns:
            True if save was initiated successfully
        """
        try:
            # Get current audio data
            current_audio = self.audio_buffer.get_current_audio()
            
            if current_audio.numel() == 0:
                return False
            
            # Track memory usage before save
            buffer_size_mb = self.audio_buffer.get_buffer_info().get('total_size_mb', 0.0)
            temp_files_size_mb = self._get_temp_files_size_mb()
            self.performance_monitor.track_memory_usage(buffer_size_mb, temp_files_size_mb)
            
            # Use performance monitor's background executor for save operation
            future = self.performance_monitor.execute_background_save(
                self._perform_save_operation,
                current_audio,
                self.current_step
            )
            
            # Update last save step immediately to prevent duplicate saves
            self.last_save_step = self.current_step
            
            if self.save_progress:
                self.save_progress.last_save_step = self.current_step
                self.save_progress.next_save_step = self.scheduler.get_next_save_step()
            
            return True
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"Failed to trigger save: {str(e)}")
            return False 
   
    def _perform_save_operation(self, audio: torch.Tensor, step: int) -> bool:
        """
        Perform the actual save operation in background thread with performance monitoring.
        
        Args:
            audio: Audio data to save
            step: Generation step
            
        Returns:
            True if save was successful
        """
        start_time = datetime.now()
        
        try:
            if not self.file_manager:
                raise RuntimeError("File manager not initialized")
            
            # Save audio to temporary file using incremental append with consistent naming
            temp_path = self.file_manager.save_audio_incremental_append(
                audio, self.audio_buffer.sampling_rate, self.voice_name, self.source_filename
            )
            
            # Validate saved file
            validation = self.file_manager.validate_audio_file(temp_path)
            if not validation['valid']:
                raise RuntimeError(f"Saved audio file validation failed: {temp_path} - {validation['errors']}")
            
            # Update progress and status
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Calculate saved duration and file size
            saved_duration = audio.shape[-1] / self.audio_buffer.sampling_rate
            file_size_mb = os.path.getsize(temp_path) / (1024**2) if os.path.exists(temp_path) else 0.0
            
            # Create save operation record
            operation_id = f"save_{step}_{int(time.time() * 1000)}"
            save_operation = SaveOperation(
                operation_id=operation_id,
                step=step,
                audio_segments=[],  # Will be populated if needed
                output_path=temp_path,
                start_time=start_time,
                end_time=end_time,
                success=True,
                file_size=file_size_mb * 1024 * 1024  # Convert back to bytes
            )
            
            # Update save info
            self.last_save_info = {
                'operation_id': operation_id,
                'step': step,
                'file_path': temp_path,
                'duration': saved_duration,
                'save_time': duration,
                'timestamp': end_time,
                'success': True
            }
            
            # Update progress tracking
            if self.save_progress:
                self.save_progress.save_file_path = temp_path
                self.save_progress.saved_duration = saved_duration
                self.save_progress.last_save_timestamp = end_time
                self.save_progress.save_success = True
                self.save_progress.error_message = None
            
            # Notify scheduler of successful save with performance metrics
            self.scheduler.handle_save_success(duration)
            
            # Send success notification
            if self.notification_system:
                self.notification_system.notify_save_success(
                    save_operation, step, saved_duration, temp_path
                )
            
            # Call progress callback if set
            if self.progress_callback:
                self.progress_callback(f"Auto-save completed at step {step}")
            
            return True
            
        except Exception as e:
            # Handle save failure using error handler
            error_msg = f"Save operation failed: {str(e)}"
            
            # Prepare context for error handler
            operation_id = f"save_{step}_{int(time.time() * 1000)}"
            error_context = {
                'operation_id': operation_id,
                'step': step,
                'audio_data': audio,
                'output_path': self.output_path,
                'save_type': 'incremental'
            }
            
            # Use error handler if available
            recovery_successful = False
            if self.error_handler:
                try:
                    error_result = self.error_handler.handle_save_failure(e, error_context)
                    recovery_successful = error_result.get('recovery_successful', False)
                    
                    if recovery_successful:
                        # Update save info with recovery success
                        self.last_save_info = {
                            'operation_id': operation_id,
                            'step': step,
                            'success': True,
                            'recovered': True,
                            'recovery_method': error_result.get('strategy', 'unknown'),
                            'timestamp': datetime.now()
                        }
                        
                        if self.save_progress:
                            self.save_progress.save_success = True
                            self.save_progress.error_message = None
                        
                        # Notify scheduler of successful recovery
                        self.scheduler.handle_save_success(0.1)  # Minimal time for recovery
                        
                        return True
                except Exception as handler_error:
                    error_msg += f" | Error handler failed: {str(handler_error)}"
            
            # If recovery failed or no error handler
            self.last_save_info = {
                'operation_id': operation_id,
                'step': step,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now()
            }
            
            if self.save_progress:
                self.save_progress.save_success = False
                self.save_progress.error_message = error_msg
            
            # Notify scheduler of save failure
            self.scheduler.handle_save_failure(error_msg)
            
            # Send failure notification
            if self.notification_system:
                self.notification_system.notify_save_failure(
                    {
                        'error_message': error_msg,
                        'error_type': type(e).__name__,
                        'recovery_attempted': recovery_successful,
                        'recovery_successful': recovery_successful,
                        'title': '保存失败',
                        'message': error_msg,
                        'suggestion': '请检查磁盘空间和权限设置'
                    },
                    step
                )
            
            if self.error_callback:
                self.error_callback(error_msg)
            
            return False
    
    def save_incremental_progress(self) -> bool:
        """
        Manually trigger incremental progress save.
        
        Returns:
            True if save was successful
        """
        if not self.config.enabled:
            return False
        
        current_audio = self.audio_buffer.get_current_audio()
        if current_audio.numel() == 0:
            return False
        
        return self._trigger_save() 
   
    def finalize_output(self) -> str:
        """
        Complete generation and finalize output file with consistent naming.
        Implements requirement 3.5: maintain same name established at first auto-save.
        
        Returns:
            Path to final output file
        """
        if not self.file_manager or not self.output_path:
            raise RuntimeError("Save manager not properly initialized")
        
        # Get final audio from buffer
        final_audio = self.audio_buffer.get_current_audio()
        
        if final_audio.numel() == 0:
            raise RuntimeError("No audio data to finalize")
        
        # Generate consistent filename using existing conventions
        try:
            # If we have a current temp file from incremental saves, finalize it
            if self.file_manager.current_temp_file and os.path.exists(self.file_manager.current_temp_file):
                # Use the file manager's finalize method with consistent naming
                final_path = self.file_manager.finalize_output(
                    temp_path=self.file_manager.current_temp_file,
                    final_path=self.output_path,
                    voice_name=self.voice_name,
                    source_filename=self.source_filename
                )
                return final_path
            else:
                # No incremental saves - save final audio directly with consistent naming
                # Generate consistent filename
                consistent_filename = self.file_manager.generate_consistent_filename(
                    voice_name=self.voice_name,
                    source_filename=self.source_filename
                )
                
                # Use the consistent filename instead of the original output path
                output_dir = os.path.dirname(self.output_path)
                
                # Handle case where output_path is just a filename (no directory)
                if not output_dir:
                    output_dir = os.getcwd()  # Use current working directory
                
                final_path = os.path.join(output_dir, consistent_filename)
                
                # Ensure audio is in correct format
                if final_audio.dim() == 1:
                    final_audio = final_audio.unsqueeze(0)
                
                # Clamp audio values
                final_audio = torch.clamp(final_audio, -1.0, 1.0)
                
                # Ensure output directory exists
                final_dir = os.path.dirname(final_path)
                if final_dir:  # Only create directory if there is one
                    os.makedirs(final_dir, exist_ok=True)
                
                # Save final file
                import torchaudio
                torchaudio.save(final_path, final_audio, self.audio_buffer.sampling_rate)
                
                # Validate final file
                validation = self.file_manager.validate_audio_file(final_path)
                if not validation['valid']:
                    raise RuntimeError(f"Final audio file validation failed: {validation['errors']}")
                
                return final_path
            
        except Exception as e:
            # Try to recover from most recent backup
            recovery_info = self.file_manager.recover_from_backup()
            if recovery_info['success'] and recovery_info['backup_path']:
                try:
                    final_path = self.file_manager.finalize_output(
                        temp_path=recovery_info['backup_path'],
                        final_path=self.output_path,
                        voice_name=self.voice_name,
                        source_filename=self.source_filename
                    )
                    return final_path
                except Exception:
                    pass
            
            raise RuntimeError(f"Failed to finalize output: {str(e)}")
    
    def cleanup_temp_files(self, preserve_for_recovery: bool = False):
        """
        Clean up temporary files after completion.
        Implements requirement 2.7, 6.6: automatic cleanup of temporary files.
        
        Args:
            preserve_for_recovery: If True, preserve files for potential recovery
        """
        cleanup_summary = {
            'file_manager_cleanup': None,
            'audio_buffer_cleared': False,
            'performance_monitor_stopped': False,
            'thread_pool_shutdown': False,
            'notification_system_cleanup': False,
            'error_handler_cleanup': False,
            'errors': []
        }
        
        try:
            # Clean up file manager resources
            if self.file_manager:
                cleanup_summary['file_manager_cleanup'] = self.file_manager.cleanup_temp_files(
                    preserve_current=preserve_for_recovery
                )
            
            # Clear audio buffer
            if self.audio_buffer:
                self.audio_buffer.clear_buffer()
                cleanup_summary['audio_buffer_cleared'] = True
            
            # Stop performance monitoring and cleanup
            if hasattr(self.performance_monitor, 'cleanup'):
                self.performance_monitor.cleanup()
                cleanup_summary['performance_monitor_stopped'] = True
            
            # Shutdown thread pool (now handled by performance monitor)
            # Keep for backward compatibility
            if hasattr(self.save_thread_pool, 'shutdown'):
                try:
                    self.save_thread_pool.shutdown(wait=True)
                    cleanup_summary['thread_pool_shutdown'] = True
                except Exception as e:
                    cleanup_summary['errors'].append(f"Thread pool shutdown error: {e}")
            
            # Clean up notification system
            if self.notification_system:
                try:
                    if hasattr(self.notification_system, 'cleanup'):
                        self.notification_system.cleanup()
                    cleanup_summary['notification_system_cleanup'] = True
                except Exception as e:
                    cleanup_summary['errors'].append(f"Notification system cleanup error: {e}")
            
            # Clean up error handler
            if self.error_handler:
                try:
                    if hasattr(self.error_handler, 'cleanup'):
                        self.error_handler.cleanup()
                    cleanup_summary['error_handler_cleanup'] = True
                except Exception as e:
                    cleanup_summary['errors'].append(f"Error handler cleanup error: {e}")
            
            # Reset state
            self.current_step = 0
            self.last_save_step = 0
            self.last_save_info = None
            self.save_progress = None
            
        except Exception as e:
            cleanup_summary['errors'].append(f"General cleanup error: {e}")
        
        return cleanup_summary
    
    def handle_generation_cancellation(self, preserve_partial_results: bool = True) -> Dict[str, Any]:
        """
        Handle proper resource cleanup when generation is cancelled or interrupted.
        Implements requirement 5.4: proper resource cleanup on generation cancellation.
        
        Args:
            preserve_partial_results: If True, preserve partial results for recovery
            
        Returns:
            Dictionary with cancellation handling results
        """
        cancellation_result = {
            'partial_results_preserved': False,
            'partial_file_path': None,
            'cleanup_performed': False,
            'recovery_info': None,
            'errors': []
        }
        
        try:
            # First, try to save current progress if requested
            if preserve_partial_results and self.audio_buffer:
                current_audio = self.audio_buffer.get_current_audio()
                if current_audio.numel() > 0:
                    try:
                        # Save current progress as emergency backup
                        if self.file_manager:
                            emergency_filename = f"emergency_save_{int(time.time())}.wav"
                            save_result = self.file_manager.save_audio_with_fallback(
                                current_audio, emergency_filename, self.audio_buffer.sampling_rate
                            )
                            
                            if save_result['success']:
                                cancellation_result['partial_results_preserved'] = True
                                cancellation_result['partial_file_path'] = save_result['file_path']
                                
                                # Create backup of the emergency save
                                backup_path = self.file_manager.create_backup(save_result['file_path'])
                                cancellation_result['backup_path'] = backup_path
                            else:
                                cancellation_result['errors'].extend(save_result['errors'])
                    
                    except Exception as e:
                        cancellation_result['errors'].append(f"Failed to preserve partial results: {e}")
            
            # Get recovery information before cleanup
            if self.file_manager:
                cancellation_result['recovery_info'] = self.file_manager.get_recovery_status()
            
            # Perform cleanup while preserving recovery files
            cleanup_summary = self.cleanup_temp_files(preserve_for_recovery=preserve_partial_results)
            cancellation_result['cleanup_performed'] = True
            cancellation_result['cleanup_details'] = cleanup_summary
            
            # Send cancellation notification
            if self.notification_system:
                try:
                    self.notification_system.notify_generation_cancelled(cancellation_result)
                except Exception as e:
                    cancellation_result['errors'].append(f"Notification error: {e}")
            
        except Exception as e:
            cancellation_result['errors'].append(f"Cancellation handling error: {e}")
        
        return cancellation_result
    
    def finalize_generation_success(self) -> Dict[str, Any]:
        """
        Finalize successful generation with proper cleanup.
        Implements requirement 2.7: automatic cleanup after successful generation.
        
        Returns:
            Dictionary with finalization results
        """
        finalization_result = {
            'final_path': None,
            'cleanup_performed': False,
            'backup_cleanup': False,
            'temp_cleanup': False,
            'success': False,
            'errors': []
        }
        
        try:
            # Finalize output file
            final_path = self.finalize_output()
            finalization_result['final_path'] = final_path
            
            # Perform full cleanup since generation was successful
            if self.config.cleanup_on_success:
                cleanup_summary = self.cleanup_temp_files(preserve_for_recovery=False)
                finalization_result['cleanup_performed'] = True
                finalization_result['cleanup_details'] = cleanup_summary
                
                # Check cleanup results
                if cleanup_summary.get('file_manager_cleanup'):
                    file_cleanup = cleanup_summary['file_manager_cleanup']
                    finalization_result['backup_cleanup'] = file_cleanup.get('backups_removed', 0) > 0
                    finalization_result['temp_cleanup'] = file_cleanup.get('temp_file_removed', False)
            
            # Send success notification
            if self.notification_system:
                try:
                    self.notification_system.notify_generation_completed(finalization_result)
                except Exception as e:
                    finalization_result['errors'].append(f"Notification error: {e}")
            
            finalization_result['success'] = True
            
        except Exception as e:
            finalization_result['errors'].append(f"Finalization error: {e}")
        
        return finalization_result
    
    def _get_temp_files_size_mb(self) -> float:
        """
        Calculate total size of temporary files in MB.
        
        Returns:
            Total size of temporary files in MB
        """
        total_size = 0.0
        
        if self.file_manager and hasattr(self.file_manager, 'temp_dir'):
            try:
                temp_dir = self.file_manager.temp_dir
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                total_size += os.path.getsize(file_path)
            except Exception:
                pass  # Return 0 if calculation fails
        
        return total_size / (1024**2)  # Convert to MB
    
    def get_save_status(self) -> Dict[str, Any]:
        """
        Get current save status and progress information with performance metrics.
        
        Returns:
            Dictionary with save status information
        """
        status = {
            'enabled': self.config.enabled,
            'current_step': self.current_step,
            'last_save_step': self.last_save_step,
            'next_save_step': self.scheduler.get_next_save_step(),
            'save_interval': self.config.save_interval,
            'buffer_info': self.audio_buffer.get_buffer_info(),
            'last_save_info': self.last_save_info,
            'scheduler_status': self.scheduler.get_scheduler_status()
        }
        
        # Add performance monitoring information
        if hasattr(self.performance_monitor, 'get_performance_summary'):
            status['performance'] = self.performance_monitor.get_performance_summary()
        
        # Add memory usage information
        buffer_size_mb = self.audio_buffer.get_buffer_info().get('total_size_mb', 0.0)
        temp_files_size_mb = self._get_temp_files_size_mb()
        memory_stats = self.performance_monitor.track_memory_usage(buffer_size_mb, temp_files_size_mb)
        status['memory_usage'] = {
            'audio_buffer_mb': memory_stats.audio_buffer_size_mb,
            'temp_files_mb': memory_stats.temp_files_size_mb,
            'system_memory_percent': memory_stats.system_memory_percent,
            'peak_memory_mb': memory_stats.peak_memory_mb,
            'memory_growth_rate': memory_stats.memory_growth_rate
        }
        
        if self.save_progress:
            status['progress'] = {
                'total_segments': self.save_progress.total_segments,
                'saved_duration': self.save_progress.saved_duration,
                'last_save_timestamp': self.save_progress.last_save_timestamp.isoformat(),
                'save_success': self.save_progress.save_success,
                'error_message': self.save_progress.error_message
            }
        
        return status
    
    def set_callbacks(self, progress_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None,
                     console_callback: Optional[Callable] = None,
                     ui_notification_callback: Optional[Callable] = None):
        """
        Set callback functions for progress and error reporting.
        
        Args:
            progress_callback: Function to call with progress updates
            error_callback: Function to call with error messages
            console_callback: Function to call for console output
            ui_notification_callback: Function to call for UI notifications
        """
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        self.console_callback = console_callback
        
        # Set scheduler callbacks
        self.scheduler.set_callbacks(
            interval_change_callback=progress_callback,
            performance_warning_callback=error_callback
        )
        
        # Set error handler callbacks
        if self.error_handler:
            self.error_handler.set_callbacks(
                error_callback=error_callback,
                recovery_callback=progress_callback,
                warning_callback=error_callback
            )
        
        # Set notification system callbacks
        if self.notification_system:
            self.notification_system.set_callbacks(
                ui_notification_callback=ui_notification_callback,
                progress_update_callback=progress_callback,
                console_callback=console_callback
            )
    
    def get_progress_status_text(self, current_step: int) -> str:
        """
        Get formatted auto-save status text for progress display.
        
        Args:
            current_step: Current generation step
            
        Returns:
            Formatted status text for display
        """
        if not self.config.enabled:
            return ""
        
        status = self.get_save_status()
        
        # Check if we just completed a save
        if (status['last_save_info'] and 
            status['last_save_info'].get('success') and 
            current_step == status['last_save_step']):
            return " | 已保存 ✓"
        
        # Check if save failed
        if (status['last_save_info'] and 
            not status['last_save_info'].get('success')):
            return " | 保存失败 ⚠️"
        
        # Show next save step
        next_save = status['next_save_step']
        if next_save > current_step:
            return f" | 下次保存: 段落 {next_save}"
        
        return ""
    
    def get_save_notification(self, current_step: int) -> Optional[Dict[str, str]]:
        """
        Get save notification for UI display.
        
        Args:
            current_step: Current generation step
            
        Returns:
            Dictionary with notification info or None
        """
        if not self.config.enabled or not self.last_save_info:
            return None
        
        # Only show notification for recent saves (within last step)
        if current_step != self.last_save_step:
            return None
        
        if self.last_save_info.get('success'):
            duration = self.last_save_info.get('duration', 0)
            return {
                'type': 'success',
                'title': '自动保存成功',
                'message': f'段落 {current_step} 已保存 (音频时长: {duration:.1f}秒)'
            }
        else:
            error = self.last_save_info.get('error', '未知错误')
            return {
                'type': 'error', 
                'title': '自动保存失败',
                'message': f'段落 {current_step}: {error}'
            }
    
    def format_progress_with_save_status(self, base_progress: str, current_step: int) -> str:
        """
        Format progress message with auto-save status.
        
        Args:
            base_progress: Base progress message
            current_step: Current generation step
            
        Returns:
            Enhanced progress message with save status
        """
        if not self.config.enabled:
            return base_progress
        
        save_status = self.get_progress_status_text(current_step)
        return f"{base_progress}{save_status}"
    
    def recover_partial_generation(self) -> Dict[str, Any]:
        """
        Attempt to recover partial generation after failure.
        Implements requirement 5.4: recovery mechanisms for partial generation failures.
        
        Returns:
            Dictionary with recovery information
        """
        if not self.error_handler:
            return {
                'success': False,
                'error': 'Error handler not initialized'
            }
        
        recovery_info = self.error_handler.recover_partial_generation()
        
        # Send recovery notification if notification system is available
        if self.notification_system and recovery_info.get('success'):
            self.notification_system.notify_recovery_available(recovery_info)
        
        return recovery_info
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """
        Get current recovery status and available options.
        
        Returns:
            Dictionary with recovery status information
        """
        recovery_status = {
            'error_handler_available': self.error_handler is not None,
            'file_manager_available': self.file_manager is not None,
            'audio_buffer_available': self.audio_buffer is not None
        }
        
        if self.error_handler:
            recovery_status['error_statistics'] = self.error_handler.get_error_statistics()
            recovery_status['recovery_options'] = self.error_handler.validate_recovery_options()
        
        if self.file_manager:
            recovery_status['file_recovery'] = self.file_manager.get_recovery_status()
        
        if self.audio_buffer:
            recovery_status['buffer_info'] = self.audio_buffer.get_buffer_info()
        
        return recovery_status
    
    def validate_auto_save_integrity(self) -> Dict[str, Any]:
        """
        Validate integrity of auto-saved files and recovery options.
        Implements requirement 5.5: validate integrity of auto-saved files.
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'overall_valid': False,
            'current_temp_file': {'exists': False, 'valid': False},
            'backup_files': {'count': 0, 'valid_count': 0},
            'audio_buffer': {'available': False, 'valid': False},
            'errors': []
        }
        
        try:
            # Validate current temp file
            if self.file_manager and self.file_manager.current_temp_file:
                temp_validation = self.file_manager.validate_audio_file(self.file_manager.current_temp_file)
                validation_result['current_temp_file'] = {
                    'exists': temp_validation['exists'],
                    'valid': temp_validation['valid'],
                    'details': temp_validation
                }
            
            # Validate backup files
            if self.file_manager:
                backup_count = len(self.file_manager.backup_files)
                valid_backups = 0
                
                for backup_path in self.file_manager.backup_files:
                    if os.path.exists(backup_path):
                        backup_validation = self.file_manager.validate_audio_file(backup_path)
                        if backup_validation['valid']:
                            valid_backups += 1
                
                validation_result['backup_files'] = {
                    'count': backup_count,
                    'valid_count': valid_backups
                }
            
            # Validate audio buffer
            if self.audio_buffer:
                buffer_info = self.audio_buffer.get_buffer_info()
                validation_result['audio_buffer'] = {
                    'available': buffer_info['segment_count'] > 0,
                    'valid': buffer_info['total_duration'] > 0,
                    'details': buffer_info
                }
            
            # Determine overall validity
            validation_result['overall_valid'] = any([
                validation_result['current_temp_file']['valid'],
                validation_result['backup_files']['valid_count'] > 0,
                validation_result['audio_buffer']['valid']
            ])
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def get_notification_history(self, notification_type: Optional[str] = None,
                               limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get notification history from the notification system.
        
        Args:
            notification_type: Filter by notification type
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        if not self.notification_system:
            return []
        
        return self.notification_system.get_notification_history(notification_type, limit)
    
    def get_console_logs(self, limit: int = 50) -> List[str]:
        """
        Get recent console log messages for auto-save operations.
        
        Args:
            limit: Maximum number of log messages to return
            
        Returns:
            List of log messages
        """
        if not self.notification_system:
            return []
        
        # Get notifications and format as console messages
        notifications = self.notification_system.get_notification_history(limit=limit)
        console_messages = []
        
        for notification in notifications:
            timestamp = notification.get('details', {}).get('timestamp', datetime.now())
            if isinstance(timestamp, datetime):
                time_str = timestamp.strftime('%H:%M:%S')
            else:
                time_str = str(timestamp)[:8]  # Fallback
            
            if notification.get('type') == 'success':
                step = notification.get('details', {}).get('step', 0)
                duration = notification.get('details', {}).get('duration', 0.0)
                console_messages.append(f"[{time_str}] ✅ 自动保存成功 - 段落 {step} (时长: {duration:.1f}秒)")
            elif notification.get('type') == 'error':
                step = notification.get('details', {}).get('step', 0)
                title = notification.get('title', '保存失败')
                console_messages.append(f"[{time_str}] ❌ {title} - 段落 {step}")
            elif notification.get('type') == 'recovery':
                title = notification.get('title', '恢复可用')
                console_messages.append(f"[{time_str}] 🔄 {title}")
        
        return console_messages