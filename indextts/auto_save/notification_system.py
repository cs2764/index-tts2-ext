"""
Comprehensive notification system for auto-save operations and error feedback.
Implements requirements 4.3, 4.4, 4.5, 5.6.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum

from .config import SaveOperation


class NotificationType(Enum):
    """Types of notifications for auto-save operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    RECOVERY = "recovery"


class AutoSaveNotificationSystem:
    """
    Manages notifications and user feedback for auto-save operations.
    Implements requirements 4.3, 4.4, 4.5, 5.6.
    """
    
    def __init__(self, console_callback: Optional[Callable] = None):
        """
        Initialize the notification system.
        
        Args:
            console_callback: Optional callback for console output
        """
        self.console_callback = console_callback
        self.notification_history: List[Dict[str, Any]] = []
        self.max_history_size = 50
        
        # Set up logging for auto-save operations
        self.logger = self._setup_auto_save_logger()
        
        # UI notification callbacks
        self.ui_notification_callback: Optional[Callable] = None
        self.progress_update_callback: Optional[Callable] = None
        
        # Error message templates
        self.error_templates = self._initialize_error_templates()
        self.recovery_templates = self._initialize_recovery_templates()
        
        # Cleanup tracking
        self.active_notifications: Dict[str, Dict[str, Any]] = {}
        self.cleanup_performed = False
    
    def _setup_auto_save_logger(self) -> logging.Logger:
        """
        Set up dedicated logger for auto-save operations.
        Implements requirement 4.4: console logging for auto-save operations and errors.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('indextts.auto_save')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create file handler for auto-save logs
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'auto_save.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _initialize_error_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize user-friendly error message templates.
        Implements requirement 4.5: user-friendly error messages for common save failures.
        
        Returns:
            Dictionary of error templates
        """
        return {
            'disk_space_full': {
                'title': '磁盘空间不足',
                'message': '保存失败：磁盘空间不足。系统已尝试使用备用位置保存。',
                'suggestion': '请清理磁盘空间或选择其他保存位置。',
                'severity': 'error'
            },
            'permission_denied': {
                'title': '权限不足',
                'message': '保存失败：没有写入权限。系统已尝试使用临时目录保存。',
                'suggestion': '请检查文件夹权限或选择有写入权限的位置。',
                'severity': 'error'
            },
            'filesystem_error': {
                'title': '文件系统错误',
                'message': '保存失败：文件系统错误。系统正在重试保存操作。',
                'suggestion': '如果问题持续，请检查存储设备状态。',
                'severity': 'warning'
            },
            'network_error': {
                'title': '网络存储错误',
                'message': '保存失败：网络存储连接问题。系统正在重试。',
                'suggestion': '请检查网络连接或使用本地存储。',
                'severity': 'warning'
            },
            'memory_error': {
                'title': '内存不足',
                'message': '保存失败：系统内存不足。已跳过此次保存以保持生成继续。',
                'suggestion': '建议增加保存间隔或关闭其他程序释放内存。',
                'severity': 'warning'
            },
            'audio_processing_error': {
                'title': '音频处理错误',
                'message': '保存失败：音频数据处理错误。系统正在重试。',
                'suggestion': '如果问题持续，可能是音频数据损坏。',
                'severity': 'warning'
            },
            'validation_failed': {
                'title': '文件验证失败',
                'message': '保存失败：保存的音频文件验证失败。系统正在重试。',
                'suggestion': '可能是存储设备问题，建议检查磁盘健康状态。',
                'severity': 'error'
            },
            'unknown_error': {
                'title': '未知错误',
                'message': '保存失败：发生未知错误。系统正在尝试恢复。',
                'suggestion': '请查看详细日志或联系技术支持。',
                'severity': 'error'
            }
        }
    
    def _initialize_recovery_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize recovery instruction templates.
        Implements requirement 5.6: recovery instructions when partial audio is available.
        
        Returns:
            Dictionary of recovery templates
        """
        return {
            'partial_audio_available': {
                'title': '部分音频可恢复',
                'message': '生成中断，但已保存部分音频内容。',
                'instructions': [
                    '1. 检查输出文件夹中的部分音频文件',
                    '2. 可以从中断点继续生成剩余内容',
                    '3. 或者重新开始完整生成'
                ],
                'file_info': '部分音频文件位置：{file_path}',
                'duration_info': '已生成音频时长：{duration:.1f}秒'
            },
            'backup_recovery_available': {
                'title': '备份文件可用',
                'message': '发现可用的备份文件，可以恢复部分进度。',
                'instructions': [
                    '1. 系统已自动定位最新的备份文件',
                    '2. 备份文件包含生成失败前的音频内容',
                    '3. 可以选择恢复备份或重新开始生成'
                ],
                'file_info': '备份文件位置：{file_path}',
                'backup_time': '备份时间：{timestamp}'
            },
            'buffer_recovery_available': {
                'title': '内存缓存可恢复',
                'message': '音频缓存中有未保存的内容，可以尝试紧急恢复。',
                'instructions': [
                    '1. 系统将尝试从内存缓存恢复音频',
                    '2. 恢复的音频将保存到临时位置',
                    '3. 请及时备份恢复的文件'
                ],
                'warning': '内存恢复可能不完整，建议重新生成以确保质量'
            },
            'no_recovery_available': {
                'title': '无法恢复',
                'message': '很抱歉，没有找到可恢复的音频内容。',
                'instructions': [
                    '1. 建议重新开始音频生成',
                    '2. 可以启用更频繁的自动保存（间隔1-3）',
                    '3. 确保有足够的磁盘空间和权限'
                ],
                'suggestion': '为避免再次丢失进度，建议检查系统资源和权限设置'
            },
            'multiple_recovery_options': {
                'title': '多种恢复选项',
                'message': '发现多个可恢复的音频源，请选择最适合的恢复方式。',
                'instructions': [
                    '1. 文件备份：最可靠的恢复选项',
                    '2. 内存缓存：最新但可能不完整',
                    '3. 临时文件：中等可靠性'
                ],
                'recommendation': '建议优先使用文件备份进行恢复'
            }
        }
    
    def notify_save_success(self, operation: SaveOperation, step: int, 
                          duration: float, file_path: str) -> Dict[str, Any]:
        """
        Notify successful save operation.
        Implements requirement 4.1: display save success notifications.
        
        Args:
            operation: Save operation details
            step: Generation step
            duration: Audio duration saved
            file_path: Path to saved file
            
        Returns:
            Notification data for UI display
        """
        notification = {
            'type': NotificationType.SUCCESS.value,
            'title': '自动保存成功',
            'message': f'段落 {step} 已保存',
            'details': {
                'step': step,
                'duration': duration,
                'file_path': file_path,
                'operation_id': operation.operation_id,
                'timestamp': datetime.now()
            },
            'display_duration': 3000,  # 3 seconds
            'show_in_ui': True
        }
        
        # Log success
        self.logger.info(
            f"Auto-save success: step {step}, duration {duration:.1f}s, "
            f"file: {os.path.basename(file_path)}"
        )
        
        # Console output
        if self.console_callback:
            self.console_callback(f"✅ 自动保存成功 - 段落 {step} (时长: {duration:.1f}秒)")
        
        # Add to history
        self._add_to_history(notification)
        
        # Notify UI
        if self.ui_notification_callback:
            self.ui_notification_callback(notification)
        
        return notification
    
    def notify_save_failure(self, error_info: Dict[str, Any], step: int) -> Dict[str, Any]:
        """
        Notify save failure with user-friendly error message.
        Implements requirement 4.3: save failure notifications.
        
        Args:
            error_info: Error information from error handler
            step: Generation step where failure occurred
            
        Returns:
            Notification data for UI display
        """
        # Determine error type and get appropriate template
        error_type = self._classify_error(error_info.get('error_message', ''))
        template = self.error_templates.get(error_type, self.error_templates['unknown_error'])
        
        notification = {
            'type': NotificationType.ERROR.value,
            'title': template['title'],
            'message': template['message'],
            'suggestion': template['suggestion'],
            'details': {
                'step': step,
                'error_type': error_type,
                'original_error': error_info.get('error_message', ''),
                'recovery_attempted': error_info.get('retry_attempted', False) or error_info.get('fallback_attempted', False),
                'recovery_successful': error_info.get('recovery_successful', False),
                'timestamp': datetime.now()
            },
            'severity': template['severity'],
            'display_duration': 8000,  # 8 seconds for errors
            'show_in_ui': True,
            'show_details': True
        }
        
        # Enhanced logging with context
        self.logger.error(
            f"Auto-save failed: step {step}, error_type: {error_type}, "
            f"recovery_attempted: {notification['details']['recovery_attempted']}, "
            f"recovery_successful: {notification['details']['recovery_successful']}, "
            f"original_error: {error_info.get('error_message', 'Unknown')}"
        )
        
        # Console output with color coding
        if self.console_callback:
            recovery_status = ""
            if error_info.get('recovery_successful'):
                recovery_status = " (已恢复 ✓)"
            elif error_info.get('retry_attempted') or error_info.get('fallback_attempted'):
                recovery_status = " (恢复中...)"
            
            self.console_callback(
                f"❌ 自动保存失败 - 段落 {step}: {template['title']}{recovery_status}"
            )
            self.console_callback(f"   建议: {template['suggestion']}")
        
        # Add to history
        self._add_to_history(notification)
        
        # Notify UI
        if self.ui_notification_callback:
            self.ui_notification_callback(notification)
        
        return notification
    
    def notify_recovery_available(self, recovery_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify user about available recovery options.
        Implements requirement 5.6: recovery instructions when partial audio is available.
        
        Args:
            recovery_info: Recovery information from error handler
            
        Returns:
            Notification data for UI display
        """
        # Determine recovery type
        recovery_type = self._classify_recovery_type(recovery_info)
        template = self.recovery_templates.get(recovery_type, self.recovery_templates['no_recovery_available'])
        
        notification = {
            'type': NotificationType.RECOVERY.value,
            'title': template['title'],
            'message': template['message'],
            'instructions': template['instructions'],
            'details': {
                'recovery_type': recovery_type,
                'recovery_info': recovery_info,
                'timestamp': datetime.now()
            },
            'display_duration': 0,  # Persistent until dismissed
            'show_in_ui': True,
            'show_details': True,
            'actions': self._get_recovery_actions(recovery_info)
        }
        
        # Add file information if available
        if recovery_info.get('recovery_file_path'):
            file_path = recovery_info['recovery_file_path']
            duration = recovery_info.get('recovered_duration', 0.0)
            
            notification['file_info'] = template.get('file_info', '').format(file_path=file_path)
            if 'duration_info' in template:
                notification['duration_info'] = template['duration_info'].format(duration=duration)
        
        # Add backup time if available
        if recovery_info.get('backup_time'):
            notification['backup_time'] = template.get('backup_time', '').format(
                timestamp=recovery_info['backup_time']
            )
        
        # Log recovery notification
        self.logger.info(
            f"Recovery available: type {recovery_type}, "
            f"file: {recovery_info.get('recovery_file_path', 'N/A')}, "
            f"duration: {recovery_info.get('recovered_duration', 0.0):.1f}s"
        )
        
        # Console output
        if self.console_callback:
            self.console_callback(f"🔄 {template['title']}: {template['message']}")
            for i, instruction in enumerate(template['instructions'], 1):
                self.console_callback(f"   {instruction}")
        
        # Add to history
        self._add_to_history(notification)
        
        # Notify UI
        if self.ui_notification_callback:
            self.ui_notification_callback(notification)
        
        return notification
    
    def notify_progress_with_save_status(self, step: int, total_steps: int, 
                                       save_status: str, stage: str = "") -> Dict[str, Any]:
        """
        Notify progress update with integrated save status.
        Implements requirement 4.2: show current step count and next auto-save point.
        
        Args:
            step: Current step
            total_steps: Total steps
            save_status: Save status text
            stage: Current processing stage
            
        Returns:
            Progress notification data
        """
        progress_percent = (step / total_steps * 100) if total_steps > 0 else 0
        
        # Format progress message
        base_message = f"段落 {step}/{total_steps}"
        if stage:
            base_message += f" | {stage}"
        
        # Add save status
        full_message = f"{base_message} {save_status}"
        
        notification = {
            'type': NotificationType.INFO.value,
            'message': full_message,
            'progress_percent': progress_percent,
            'details': {
                'step': step,
                'total_steps': total_steps,
                'save_status': save_status,
                'stage': stage,
                'timestamp': datetime.now()
            },
            'show_in_ui': True,
            'is_progress': True
        }
        
        # Update progress callback
        if self.progress_update_callback:
            self.progress_update_callback(notification)
        
        return notification
    
    def notify_generation_complete(self, final_file_path: str, total_duration: float,
                                 save_count: int) -> Dict[str, Any]:
        """
        Notify generation completion with final file information.
        Implements requirement 4.5: confirm final file location and total duration.
        
        Args:
            final_file_path: Path to final output file
            total_duration: Total audio duration
            save_count: Number of auto-saves performed
            
        Returns:
            Completion notification data
        """
        notification = {
            'type': NotificationType.SUCCESS.value,
            'title': '音频生成完成',
            'message': f'总时长: {total_duration:.1f}秒',
            'details': {
                'final_file_path': final_file_path,
                'total_duration': total_duration,
                'save_count': save_count,
                'timestamp': datetime.now()
            },
            'file_info': f'文件位置: {final_file_path}',
            'save_info': f'执行了 {save_count} 次自动保存',
            'display_duration': 5000,  # 5 seconds
            'show_in_ui': True
        }
        
        # Log completion
        self.logger.info(
            f"Generation complete: duration {total_duration:.1f}s, "
            f"saves: {save_count}, file: {os.path.basename(final_file_path)}"
        )
        
        # Console output
        if self.console_callback:
            self.console_callback(f"✅ 音频生成完成 - 总时长: {total_duration:.1f}秒")
            self.console_callback(f"   文件位置: {final_file_path}")
            self.console_callback(f"   执行了 {save_count} 次自动保存")
        
        # Add to history
        self._add_to_history(notification)
        
        # Notify UI
        if self.ui_notification_callback:
            self.ui_notification_callback(notification)
        
        return notification
    
    def _classify_error(self, error_message: str) -> str:
        """
        Classify error type based on error message.
        
        Args:
            error_message: Error message to classify
            
        Returns:
            Error type key
        """
        error_msg_lower = error_message.lower()
        
        if any(keyword in error_msg_lower for keyword in ['no space left', 'disk full', 'space']):
            return 'disk_space_full'
        elif any(keyword in error_msg_lower for keyword in ['permission denied', 'access denied', 'permission']):
            return 'permission_denied'
        elif any(keyword in error_msg_lower for keyword in ['file exists', 'directory not found', 'filesystem']):
            return 'filesystem_error'
        elif any(keyword in error_msg_lower for keyword in ['network', 'timeout', 'connection']):
            return 'network_error'
        elif any(keyword in error_msg_lower for keyword in ['memory', 'out of memory']):
            return 'memory_error'
        elif any(keyword in error_msg_lower for keyword in ['audio', 'tensor', 'sample rate']):
            return 'audio_processing_error'
        elif any(keyword in error_msg_lower for keyword in ['validation', 'invalid', 'corrupt']):
            return 'validation_failed'
        else:
            return 'unknown_error'
    
    def _classify_recovery_type(self, recovery_info: Dict[str, Any]) -> str:
        """
        Classify recovery type based on available recovery information.
        
        Args:
            recovery_info: Recovery information
            
        Returns:
            Recovery type key
        """
        if not recovery_info.get('success', False):
            return 'no_recovery_available'
        
        recovery_method = recovery_info.get('recovery_method', '')
        
        if recovery_method == 'file_backup':
            return 'backup_recovery_available'
        elif recovery_method == 'audio_buffer':
            return 'buffer_recovery_available'
        elif recovery_info.get('partial_audio_available', False):
            return 'partial_audio_available'
        else:
            # Check if multiple recovery options are available
            available_options = 0
            if recovery_info.get('file_backup_available'):
                available_options += 1
            if recovery_info.get('buffer_available'):
                available_options += 1
            if recovery_info.get('fallback_files_available'):
                available_options += 1
            
            if available_options > 1:
                return 'multiple_recovery_options'
            elif available_options == 1:
                return 'partial_audio_available'
            else:
                return 'no_recovery_available'
    
    def _get_recovery_actions(self, recovery_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get available recovery actions based on recovery information.
        
        Args:
            recovery_info: Recovery information
            
        Returns:
            List of recovery actions
        """
        actions = []
        
        if recovery_info.get('recovery_file_path'):
            actions.append({
                'id': 'open_recovery_file',
                'label': '打开恢复文件',
                'description': '在文件管理器中打开恢复的音频文件'
            })
        
        if recovery_info.get('success'):
            actions.append({
                'id': 'continue_from_recovery',
                'label': '从恢复点继续',
                'description': '从恢复的进度继续生成剩余内容'
            })
        
        actions.extend([
            {
                'id': 'restart_generation',
                'label': '重新开始生成',
                'description': '忽略恢复内容，重新开始完整生成'
            },
            {
                'id': 'adjust_save_settings',
                'label': '调整保存设置',
                'description': '修改自动保存间隔以避免类似问题'
            }
        ])
        
        return actions
    
    def _add_to_history(self, notification: Dict[str, Any]):
        """Add notification to history with size limit."""
        self.notification_history.append(notification)
        
        # Limit history size
        if len(self.notification_history) > self.max_history_size:
            self.notification_history.pop(0)
    
    def get_notification_history(self, notification_type: Optional[str] = None,
                               limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get notification history.
        
        Args:
            notification_type: Filter by notification type
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        history = self.notification_history
        
        if notification_type:
            history = [n for n in history if n.get('type') == notification_type]
        
        return history[-limit:] if limit > 0 else history
    
    def set_callbacks(self, ui_notification_callback: Optional[Callable] = None,
                     progress_update_callback: Optional[Callable] = None,
                     console_callback: Optional[Callable] = None):
        """
        Set callback functions for different notification channels.
        
        Args:
            ui_notification_callback: Callback for UI notifications
            progress_update_callback: Callback for progress updates
            console_callback: Callback for console output
        """
        if ui_notification_callback:
            self.ui_notification_callback = ui_notification_callback
        if progress_update_callback:
            self.progress_update_callback = progress_update_callback
        if console_callback:
            self.console_callback = console_callback
    
    def clear_history(self):
        """Clear notification history."""
        self.notification_history.clear()
        self.logger.info("Notification history cleared")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current notification system status.
        
        Returns:
            Dictionary with system status information
        """
        return {
            'total_notifications': len(self.notification_history),
            'error_count': len([n for n in self.notification_history if n.get('type') == NotificationType.ERROR.value]),
            'success_count': len([n for n in self.notification_history if n.get('type') == NotificationType.SUCCESS.value]),
            'recovery_count': len([n for n in self.notification_history if n.get('type') == NotificationType.RECOVERY.value]),
            'callbacks_configured': {
                'ui_notification': self.ui_notification_callback is not None,
                'progress_update': self.progress_update_callback is not None,
                'console': self.console_callback is not None
            },
            'logger_configured': self.logger is not None
        }
    
    def notify_generation_cancelled(self, cancellation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify user about generation cancellation and cleanup results.
        Implements requirement 5.4: proper resource cleanup on generation cancellation.
        
        Args:
            cancellation_result: Results from cancellation handling
            
        Returns:
            Cancellation notification data
        """
        notification = {
            'type': NotificationType.WARNING.value,
            'title': '音频生成已取消',
            'message': '生成过程已中断，正在清理资源',
            'details': {
                'cancellation_result': cancellation_result,
                'timestamp': datetime.now()
            },
            'display_duration': 8000,  # 8 seconds
            'show_in_ui': True
        }
        
        # Add partial results information if available
        if cancellation_result.get('partial_results_preserved'):
            notification['partial_info'] = f"部分结果已保存: {cancellation_result.get('partial_file_path', 'N/A')}"
            notification['recovery_available'] = True
        
        # Add cleanup information
        if cancellation_result.get('cleanup_performed'):
            cleanup_details = cancellation_result.get('cleanup_details', {})
            freed_mb = cleanup_details.get('total_size_freed_mb', 0.0)
            notification['cleanup_info'] = f"已清理临时文件，释放 {freed_mb:.1f} MB 空间"
        
        # Log cancellation
        self.logger.warning(
            f"Generation cancelled - partial preserved: {cancellation_result.get('partial_results_preserved', False)}, "
            f"cleanup performed: {cancellation_result.get('cleanup_performed', False)}"
        )
        
        # Console output
        if self.console_callback:
            self.console_callback("⚠️ 音频生成已取消")
            if cancellation_result.get('partial_results_preserved'):
                self.console_callback(f"   部分结果已保存: {cancellation_result.get('partial_file_path', 'N/A')}")
            if cancellation_result.get('cleanup_performed'):
                self.console_callback("   临时文件已清理")
        
        # Add to history
        self._add_to_history(notification)
        
        # Notify UI
        if self.ui_notification_callback:
            self.ui_notification_callback(notification)
        
        return notification
    
    def notify_generation_completed(self, finalization_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify user about successful generation completion and cleanup.
        Implements requirement 2.7: automatic cleanup after successful generation.
        
        Args:
            finalization_result: Results from generation finalization
            
        Returns:
            Completion notification data
        """
        notification = {
            'type': NotificationType.SUCCESS.value,
            'title': '音频生成完成',
            'message': '生成成功，文件已保存',
            'details': {
                'finalization_result': finalization_result,
                'timestamp': datetime.now()
            },
            'display_duration': 5000,  # 5 seconds
            'show_in_ui': True
        }
        
        # Add final file information
        if finalization_result.get('final_path'):
            notification['file_info'] = f"文件位置: {finalization_result['final_path']}"
        
        # Add cleanup information
        if finalization_result.get('cleanup_performed'):
            cleanup_details = finalization_result.get('cleanup_details', {})
            freed_mb = cleanup_details.get('total_size_freed_mb', 0.0)
            notification['cleanup_info'] = f"已自动清理临时文件，释放 {freed_mb:.1f} MB 空间"
        
        # Log completion
        self.logger.info(
            f"Generation completed successfully - final file: {finalization_result.get('final_path', 'N/A')}, "
            f"cleanup performed: {finalization_result.get('cleanup_performed', False)}"
        )
        
        # Console output
        if self.console_callback:
            self.console_callback("✅ 音频生成完成")
            if finalization_result.get('final_path'):
                self.console_callback(f"   文件位置: {finalization_result['final_path']}")
            if finalization_result.get('cleanup_performed'):
                self.console_callback("   临时文件已自动清理")
        
        # Add to history
        self._add_to_history(notification)
        
        # Notify UI
        if self.ui_notification_callback:
            self.ui_notification_callback(notification)
        
        return notification
    
    def cleanup(self):
        """
        Clean up notification system resources.
        Implements requirement 6.6: proper resource cleanup.
        """
        if self.cleanup_performed:
            return
        
        try:
            # Clear active notifications
            self.active_notifications.clear()
            
            # Clear history
            self.notification_history.clear()
            
            # Reset callbacks
            self.ui_notification_callback = None
            self.progress_update_callback = None
            self.console_callback = None
            
            # Close logger handlers
            if self.logger:
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
            
            self.cleanup_performed = True
            
        except Exception as e:
            # Log cleanup error if logger is still available
            if self.logger and not self.cleanup_performed:
                self.logger.error(f"Error during notification system cleanup: {e}")
            
            # Fallback to print if logger is not available
            print(f"Warning: Error during notification system cleanup: {e}")