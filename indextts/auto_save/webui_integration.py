"""
WebUI integration for comprehensive auto-save error notifications and user feedback.
Implements requirements 4.3, 4.4, 4.5, 5.6.
"""

import gradio as gr
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime

from .notification_system import AutoSaveNotificationSystem
from .save_manager import IncrementalSaveManager


class AutoSaveWebUIIntegration:
    """
    Integrates auto-save notifications and error feedback with the WebUI.
    Implements comprehensive error notifications and user feedback system.
    """
    
    def __init__(self, enhanced_ui_components):
        """
        Initialize WebUI integration.
        
        Args:
            enhanced_ui_components: Enhanced UI components instance
        """
        self.ui_components = enhanced_ui_components
        self.notification_system: Optional[AutoSaveNotificationSystem] = None
        self.save_manager: Optional[IncrementalSaveManager] = None
        
        # UI state
        self.current_notifications: List[Dict[str, Any]] = []
        self.console_messages: List[str] = []
        self.max_console_messages = 100
        
        # UI components for notifications
        self.notification_display: Optional[gr.HTML] = None
        self.console_display: Optional[gr.HTML] = None
        self.save_status_display: Optional[gr.HTML] = None
        self.recovery_panel: Optional[gr.HTML] = None
    
    def setup_notification_components(self) -> Tuple[gr.HTML, gr.HTML, gr.HTML, gr.HTML]:
        """
        Set up UI components for auto-save notifications.
        
        Returns:
            Tuple of (notification_display, console_display, save_status_display, recovery_panel)
        """
        # Main notification display
        self.notification_display = gr.HTML(
            value="",
            visible=False,
            label="Auto-save Notifications",
            elem_classes=["auto-save-notifications"]
        )
        
        # Console log display
        self.console_display = gr.HTML(
            value=self.ui_components.create_console_log_display([]),
            visible=True,
            label="Auto-save Console",
            elem_classes=["auto-save-console"]
        )
        
        # Save status summary
        self.save_status_display = gr.HTML(
            value="",
            visible=False,
            label="Save Status",
            elem_classes=["save-status-summary"]
        )
        
        # Recovery instructions panel
        self.recovery_panel = gr.HTML(
            value="",
            visible=False,
            label="Recovery Instructions",
            elem_classes=["recovery-panel"]
        )
        
        return (self.notification_display, self.console_display, 
                self.save_status_display, self.recovery_panel)
    
    def initialize_with_save_manager(self, save_manager: IncrementalSaveManager):
        """
        Initialize integration with save manager and set up callbacks.
        
        Args:
            save_manager: Incremental save manager instance
        """
        self.save_manager = save_manager
        self.notification_system = save_manager.notification_system
        
        if self.notification_system:
            # Set up notification system callbacks
            self.notification_system.set_callbacks(
                ui_notification_callback=self._handle_ui_notification,
                progress_update_callback=self._handle_progress_update,
                console_callback=self._handle_console_message
            )
        
        # Set up save manager callbacks
        save_manager.set_callbacks(
            progress_callback=self._handle_progress_callback,
            error_callback=self._handle_error_callback,
            console_callback=self._handle_console_message,
            ui_notification_callback=self._handle_ui_notification
        )
    
    def _handle_ui_notification(self, notification: Dict[str, Any]):
        """
        Handle UI notification from notification system.
        
        Args:
            notification: Notification data
        """
        # Add to current notifications
        self.current_notifications.append(notification)
        
        # Limit notification history
        if len(self.current_notifications) > 10:
            self.current_notifications.pop(0)
        
        # Update notification display
        self._update_notification_display()
        
        # Handle special notification types
        if notification.get('type') == 'recovery':
            self._update_recovery_panel(notification)
    
    def _handle_progress_update(self, progress_info: Dict[str, Any]):
        """
        Handle progress update from notification system.
        
        Args:
            progress_info: Progress information
        """
        # Update save status display if available
        if self.save_manager and self.save_status_display:
            save_status = self.save_manager.get_save_status()
            status_html = self.ui_components.create_save_status_summary(save_status)
            self.save_status_display.update(value=status_html, visible=True)
    
    def _handle_console_message(self, message: str):
        """
        Handle console message from notification system.
        
        Args:
            message: Console message
        """
        # Add timestamp to message
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to console messages
        self.console_messages.append(formatted_message)
        
        # Limit console message history
        if len(self.console_messages) > self.max_console_messages:
            self.console_messages.pop(0)
        
        # Update console display
        self._update_console_display()
    
    def _handle_progress_callback(self, message: str):
        """
        Handle progress callback from save manager.
        
        Args:
            message: Progress message
        """
        self._handle_console_message(message)
    
    def _handle_error_callback(self, error_message: str):
        """
        Handle error callback from save manager.
        
        Args:
            error_message: Error message
        """
        self._handle_console_message(f"❌ {error_message}")
    
    def _update_notification_display(self):
        """Update the notification display with current notifications."""
        if not self.notification_display:
            return
        
        if not self.current_notifications:
            if hasattr(self.notification_display, 'update'):
                self.notification_display.update(value="", visible=False)
            return
        
        # Build combined notification HTML
        notifications_html = ""
        
        for notification in self.current_notifications[-3:]:  # Show last 3 notifications
            if notification.get('type') == 'success':
                notifications_html += self.ui_components.create_save_status_notification(
                    'success',
                    notification.get('title', '成功'),
                    notification.get('message', ''),
                    notification.get('details'),
                    notification.get('show_details', False)
                )
            elif notification.get('type') == 'error':
                notifications_html += self.ui_components.create_comprehensive_error_notification(
                    notification, 
                    notification.get('details', {}).get('step', 0)
                )
            elif notification.get('type') == 'warning':
                notifications_html += self.ui_components.create_save_status_notification(
                    'warning',
                    notification.get('title', '警告'),
                    notification.get('message', ''),
                    notification.get('details'),
                    notification.get('show_details', False)
                )
        
        if hasattr(self.notification_display, 'update'):
            self.notification_display.update(value=notifications_html, visible=bool(notifications_html))
    
    def _update_console_display(self):
        """Update the console display with recent messages."""
        if not self.console_display:
            return
        
        console_html = self.ui_components.create_console_log_display(
            self.console_messages, max_lines=15
        )
        if hasattr(self.console_display, 'update'):
            self.console_display.update(value=console_html)
    
    def _update_recovery_panel(self, recovery_notification: Dict[str, Any]):
        """
        Update the recovery panel with recovery instructions.
        
        Args:
            recovery_notification: Recovery notification data
        """
        if not self.recovery_panel:
            return
        
        recovery_html = self.ui_components.create_recovery_instructions_panel(
            recovery_notification
        )
        if hasattr(self.recovery_panel, 'update'):
            self.recovery_panel.update(value=recovery_html, visible=True)
    
    def update_save_status_display(self):
        """Update the save status display with current information."""
        if not self.save_manager or not self.save_status_display:
            return
        
        save_status = self.save_manager.get_save_status()
        status_html = self.ui_components.create_save_status_summary(save_status)
        if hasattr(self.save_status_display, 'update'):
            self.save_status_display.update(value=status_html, visible=save_status.get('enabled', False))
    
    def handle_generation_start(self, auto_save_enabled: bool, auto_save_interval: int):
        """
        Handle generation start event.
        
        Args:
            auto_save_enabled: Whether auto-save is enabled
            auto_save_interval: Auto-save interval
        """
        # Clear previous notifications and console messages
        self.current_notifications.clear()
        self.console_messages.clear()
        
        # Update displays
        self._update_notification_display()
        self._update_console_display()
        
        # Hide recovery panel
        if self.recovery_panel and hasattr(self.recovery_panel, 'update'):
            self.recovery_panel.update(value="", visible=False)
        
        # Show/hide save status based on auto-save setting
        if self.save_status_display:
            if auto_save_enabled:
                self.update_save_status_display()
            else:
                if hasattr(self.save_status_display, 'update'):
                    self.save_status_display.update(value="", visible=False)
        
        # Log generation start
        if auto_save_enabled:
            self._handle_console_message(
                f"🎯 开始音频生成 - 自动保存已启用 (间隔: {auto_save_interval} 段落)"
            )
        else:
            self._handle_console_message("🎯 开始音频生成 - 自动保存已禁用")
    
    def handle_generation_complete(self, final_file_path: str, total_duration: float):
        """
        Handle generation complete event.
        
        Args:
            final_file_path: Path to final output file
            total_duration: Total audio duration
        """
        if not self.save_manager or not self.notification_system:
            return
        
        # Get save count from save manager
        save_count = len([n for n in self.current_notifications if n.get('type') == 'success'])
        
        # Send completion notification
        self.notification_system.notify_generation_complete(
            final_file_path, total_duration, save_count
        )
        
        # Update save status display to show completion
        self.update_save_status_display()
    
    def handle_generation_error(self, error_message: str):
        """
        Handle generation error event.
        
        Args:
            error_message: Error message
        """
        self._handle_console_message(f"❌ 生成错误: {error_message}")
        
        # Try to recover partial generation if save manager is available
        if self.save_manager:
            recovery_info = self.save_manager.recover_partial_generation()
            
            if recovery_info.get('success'):
                self._handle_console_message("🔄 检测到可恢复的部分音频")
            else:
                self._handle_console_message("⚠️ 无法恢复部分音频")
    
    def get_notification_summary(self) -> Dict[str, Any]:
        """
        Get summary of current notifications and status.
        
        Returns:
            Dictionary with notification summary
        """
        return {
            'total_notifications': len(self.current_notifications),
            'success_count': len([n for n in self.current_notifications if n.get('type') == 'success']),
            'error_count': len([n for n in self.current_notifications if n.get('type') == 'error']),
            'warning_count': len([n for n in self.current_notifications if n.get('type') == 'warning']),
            'recovery_available': any(n.get('type') == 'recovery' for n in self.current_notifications),
            'console_message_count': len(self.console_messages),
            'save_manager_connected': self.save_manager is not None,
            'notification_system_connected': self.notification_system is not None
        }
    
    def clear_notifications(self):
        """Clear all notifications and console messages."""
        self.current_notifications.clear()
        self.console_messages.clear()
        
        # Update displays
        self._update_notification_display()
        self._update_console_display()
        
        # Hide recovery panel
        if self.recovery_panel and hasattr(self.recovery_panel, 'update'):
            self.recovery_panel.update(value="", visible=False)
        
        # Clear notification system history if available
        if self.notification_system:
            self.notification_system.clear_history()
    
    def export_console_log(self) -> str:
        """
        Export console log as text.
        
        Returns:
            Console log as formatted text
        """
        if not self.console_messages:
            return "No console messages available."
        
        log_text = "IndexTTS Auto-Save Console Log\n"
        log_text += "=" * 40 + "\n"
        log_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_text += f"Total Messages: {len(self.console_messages)}\n\n"
        
        for message in self.console_messages:
            log_text += f"{message}\n"
        
        return log_text
    
    def create_notification_controls(self) -> Tuple[gr.Button, gr.Button, gr.Button]:
        """
        Create control buttons for notification management.
        
        Returns:
            Tuple of (clear_button, export_button, refresh_button)
        """
        clear_button = gr.Button(
            "🗑️ 清除通知",
            size="sm",
            variant="secondary"
        )
        
        export_button = gr.Button(
            "📄 导出日志",
            size="sm",
            variant="secondary"
        )
        
        refresh_button = gr.Button(
            "🔄 刷新状态",
            size="sm",
            variant="secondary"
        )
        
        # Set up button callbacks
        clear_button.click(
            fn=lambda: self.clear_notifications(),
            outputs=[]
        )
        
        export_button.click(
            fn=lambda: self.export_console_log(),
            outputs=[]
        )
        
        refresh_button.click(
            fn=lambda: self.update_save_status_display(),
            outputs=[]
        )
        
        return clear_button, export_button, refresh_button


def create_auto_save_notification_interface(enhanced_ui_components) -> Tuple[AutoSaveWebUIIntegration, Dict[str, gr.Component]]:
    """
    Create complete auto-save notification interface.
    
    Args:
        enhanced_ui_components: Enhanced UI components instance
        
    Returns:
        Tuple of (integration_instance, ui_components_dict)
    """
    # Create integration instance
    integration = AutoSaveWebUIIntegration(enhanced_ui_components)
    
    # Set up notification components
    notification_display, console_display, save_status_display, recovery_panel = integration.setup_notification_components()
    
    # Create control buttons
    clear_button, export_button, refresh_button = integration.create_notification_controls()
    
    # Package UI components
    ui_components = {
        'notification_display': notification_display,
        'console_display': console_display,
        'save_status_display': save_status_display,
        'recovery_panel': recovery_panel,
        'clear_button': clear_button,
        'export_button': export_button,
        'refresh_button': refresh_button
    }
    
    return integration, ui_components