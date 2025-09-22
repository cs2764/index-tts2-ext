"""
Enhanced UI components with loading indicators, tooltips, and improved UX.
"""

import gradio as gr
from typing import Tuple, Optional, List, Dict, Any, Callable
from .ui_theme_manager import get_theme_manager, UIThemeManager
from .webui_components import WebUIComponents


class EnhancedUIComponents(WebUIComponents):
    """Enhanced WebUI components with improved UX and dark theme support."""
    
    def __init__(self, enhanced_webui, tts_engine=None):
        """
        Initialize enhanced UI components.
        
        Args:
            enhanced_webui: Enhanced WebUI instance
            tts_engine: Optional TTS engine for background processing
        """
        super().__init__(enhanced_webui, tts_engine)
        self.theme_manager = get_theme_manager()
    
    def create_enhanced_file_upload_components(self) -> Tuple[gr.File, gr.HTML, gr.HTML, 
                                                           gr.Checkbox, gr.Checkbox, gr.Checkbox]:
        """
        Create enhanced file upload components with preview and loading indicators.
        
        Returns:
            Tuple of (file_upload, file_preview, chapter_preview, use_native_chapters, 
                     file_cleaning_toggle, chapter_recognition_toggle)
        """
        # File upload with enhanced styling
        file_upload = gr.File(
            label="📁 Upload TXT or EPUB file",
            file_types=[".txt", ".epub"],
            type="filepath",
            elem_classes=["file-upload-area"]
        )
        
        # File preview display
        file_preview = gr.HTML(
            value="",
            visible=False,
            label="File Preview"
        )
        
        # Chapter preview display
        chapter_preview = gr.HTML(
            value="",
            visible=False,
            label="Chapter Preview"
        )
        
        # Native chapters checkbox with tooltip
        use_native_chapters = gr.Checkbox(
            label="Use native EPUB chapters",
            value=False,
            visible=False,
            info="Use the original chapter structure from EPUB file"
        )
        
        # File cleaning toggle with enhanced info
        file_cleaning_toggle = gr.Checkbox(
            label="🧹 文件清理",
            value=True,
            info=self.theme_manager.get_help_text_for_component("file_cleaning")
        )
        
        # Chapter recognition toggle with enhanced info
        chapter_recognition_toggle = gr.Checkbox(
            label="🔍 智能章节识别",
            value=False,
            info=self.theme_manager.get_help_text_for_component("chapter_recognition")
        )
        
        return (file_upload, file_preview, chapter_preview, use_native_chapters, 
                file_cleaning_toggle, chapter_recognition_toggle)
    
    def create_enhanced_format_selection_components(self) -> Tuple[gr.Dropdown, gr.Slider, 
                                                                gr.Checkbox, gr.Slider, gr.HTML]:
        """
        Create enhanced audio format selection components with tooltips.
        
        Returns:
            Tuple of (format_dropdown, mp3_bitrate, enable_segmentation, 
                     chapters_per_file, format_info)
        """
        # Format dropdown with enhanced options
        format_dropdown = gr.Dropdown(
            choices=["WAV", "MP3", "M4B"],
            value="MP3",
            label="🎵 Output Format",
            info=self.theme_manager.get_help_text_for_component("format_selection")
        )
        
        # MP3 bitrate slider
        mp3_bitrate = gr.Slider(
            minimum=32,
            maximum=320,
            value=64,
            step=32,
            label="MP3 Bitrate (kbps)",
            visible=True,
            info="Higher bitrate = better quality, larger file size"
        )
        
        # Segmentation checkbox
        enable_segmentation = gr.Checkbox(
            label="📚 Enable Chapter Segmentation",
            value=False,
            info=self.theme_manager.get_help_text_for_component("segmentation")
        )
        
        # Chapters per file slider (updated defaults)
        chapters_per_file = gr.Slider(
            minimum=1,
            maximum=200,
            value=20,
            step=1,
            label="Chapters per File",
            visible=False,
            info="Number of chapters to include in each audio file"
        )
        
        # Format information display
        format_info = gr.HTML(
            value=self._get_format_info_html("MP3"),
            visible=True
        )
        
        return format_dropdown, mp3_bitrate, enable_segmentation, chapters_per_file, format_info
    
    def create_enhanced_voice_selection_components(self) -> Tuple[gr.Dropdown, gr.Button, 
                                                               gr.HTML, gr.Audio]:
        """
        Create enhanced voice selection components with preview.
        
        Returns:
            Tuple of (voice_dropdown, refresh_button, status_display, voice_preview)
        """
        # Get available voice samples
        samples = self.enhanced_webui.get_voice_manager().get_available_samples()
        sample_choices = [(sample.display_name, sample.filepath) for sample in samples]
        
        # Voice dropdown with enhanced styling
        voice_dropdown = gr.Dropdown(
            choices=sample_choices,
            value=sample_choices[0][1] if sample_choices else None,
            label="🎤 Voice Sample",
            allow_custom_value=False,
            info=self.theme_manager.get_help_text_for_component("voice_selection")
        )
        
        # Refresh button with icon
        refresh_button = gr.Button(
            "🔄 Refresh Samples",
            size="sm",
            variant="secondary",
            elem_classes=["btn-secondary"]
        )
        
        # Status display with enhanced formatting
        status_display = gr.HTML(
            value=self._get_enhanced_voice_status_html(samples),
            visible=True
        )
        
        # Voice preview player (auto-filled with the selected sample)
        voice_preview = gr.Audio(
            label="Voice Preview",
            value=sample_choices[0][1] if sample_choices else None,
            visible=True if sample_choices else False,
            interactive=False
        )
        
        return voice_dropdown, refresh_button, status_display, voice_preview
    
    def create_enhanced_auto_save_components(self) -> Tuple[gr.Checkbox, gr.HTML, gr.HTML]:
        """
        Create enhanced auto-save components with filename preview.
        
        Returns:
            Tuple of (auto_save_checkbox, filename_preview, save_info)
        """
        # Auto-save checkbox with enhanced info
        auto_save_checkbox = gr.Checkbox(
            label="💾 Auto-save Generated Audio",
            value=True,
            info=self.theme_manager.get_help_text_for_component("auto_save")
        )
        
        # Filename preview
        filename_preview = gr.HTML(
            value="",
            visible=False,
            label="Filename Preview"
        )
        
        # Save information
        save_info = gr.HTML(
            value=self._get_save_info_html(),
            visible=True
        )
        
        return auto_save_checkbox, filename_preview, save_info
    
    def create_incremental_auto_save_components(self) -> Tuple[gr.Checkbox, gr.Slider, gr.HTML]:
        """
        Create enhanced incremental auto-save configuration components with validation.
        
        Returns:
            Tuple of (auto_save_enabled, auto_save_interval, auto_save_info)
        """
        # Import validator to get default values
        from ..auto_save.config_validator import create_config_validator
        validator = create_config_validator()
        defaults = validator.get_default_values()
        
        # Auto-save enable/disable checkbox with user preference default
        auto_save_enabled = gr.Checkbox(
            label="🔄 启用增量自动保存",
            value=defaults['enabled'],
            info="在生成过程中自动保存进度，防止错误导致的数据丢失"
        )
        
        # Auto-save interval slider with enhanced validation and user preference default
        auto_save_interval = gr.Slider(
            minimum=1,
            maximum=10,
            value=defaults['interval'],
            step=1,
            label="自动保存间隔",
            info="每生成多少个段落后自动保存一次（1-10段落）",
            visible=True,
            interactive=True
        )
        
        # Enhanced auto-save information display with validation feedback
        auto_save_info = gr.HTML(
            value=self.update_auto_save_info(defaults['enabled'], defaults['interval']),
            visible=True
        )
        
        return auto_save_enabled, auto_save_interval, auto_save_info
    
    def create_enhanced_generation_components(self) -> Tuple[gr.Button, gr.HTML, gr.HTML]:
        """
        Create enhanced generation components with progress tracking.
        
        Returns:
            Tuple of (generate_button, progress_display, status_display)
        """
        # Generate button with enhanced styling
        generate_button = gr.Button(
            "🎯 Generate Audio",
            variant="primary",
            size="lg",
            elem_classes=["btn-primary"]
        )
        
        # Progress display
        progress_display = gr.HTML(
            value="",
            visible=False,
            label="Generation Progress"
        )
        
        # Status display
        status_display = gr.HTML(
            value="Ready to generate audio",
            visible=True
        )
        
        return generate_button, progress_display, status_display
    
    def create_task_monitoring_components(self) -> Tuple[gr.HTML, gr.Button, gr.HTML]:
        """
        Create task monitoring components for background processing.
        
        Returns:
            Tuple of (task_list, refresh_tasks_button, task_info)
        """
        # Task list display
        task_list = gr.HTML(
            value="<div style='color:#6c757d;text-align:center'>No active background tasks</div>",
            visible=True,
            label="Background Tasks"
        )
        
        # Refresh tasks button
        refresh_tasks_button = gr.Button(
            "🔄 Refresh Tasks",
            size="sm",
            variant="secondary"
        )
        
        # Task information
        task_info = gr.HTML(
            value=self._get_task_info_html(),
            visible=True
        )
        
        return task_list, refresh_tasks_button, task_info
    
    def update_file_preview(self, file_path: Optional[str], 
                          file_cleaning_enabled: bool = True,
                          chapter_recognition_enabled: bool = False) -> Tuple[str, str, bool]:
        """
        Update file preview with loading indicator and enhanced display.
        
        Args:
            file_path: Path to uploaded file
            file_cleaning_enabled: Whether file cleaning is enabled
            chapter_recognition_enabled: Whether chapter recognition is enabled
            
        Returns:
            Tuple of (file_preview_html, chapter_preview_html, show_native_chapters)
        """
        if not file_path:
            return "", "", False
        
        try:
            # Show loading indicator
            loading_html = self.theme_manager.create_loading_indicator("Generating file preview...")
            
            # Generate file preview using optimized processor
            preview = self.enhanced_webui.get_file_processor().generate_file_preview(file_path)
            
            # Create enhanced file preview HTML
            file_preview_html = self.theme_manager.create_file_preview_html(
                preview.preview_text,
                preview.filename,
                preview.encoding,
                preview.file_size,
                preview.total_lines,
                preview.preview_truncated
            )
            
            # Generate chapter preview if enabled
            chapter_preview_html = ""
            show_native_chapters = False
            
            if chapter_recognition_enabled:
                # Show loading for chapter detection
                chapter_loading_html = self.theme_manager.create_loading_indicator("Detecting chapters...")
                
                # Get chapter parser and detect chapters
                chapter_parser = self.enhanced_webui.get_chapter_parser()
                
                # Use fast preview parsing
                chapters = chapter_parser.parse_for_preview(preview.preview_text)
                chapter_titles = [chapter.title for chapter in chapters]
                
                chapter_preview_html = self.theme_manager.create_chapter_preview_html(
                    chapter_titles, len(chapters)
                )
            
            # Check if EPUB file to show native chapters option
            if file_path.lower().endswith('.epub'):
                show_native_chapters = True
            
            return file_preview_html, chapter_preview_html, show_native_chapters
            
        except Exception as e:
            error_html = self.theme_manager.create_status_message(
                f"Error generating preview: {str(e)}", "error"
            )
            return error_html, "", False
    
    def update_format_info(self, selected_format: str, mp3_bitrate: int = 64) -> str:
        """
        Update format information display.
        
        Args:
            selected_format: Selected audio format
            mp3_bitrate: MP3 bitrate if MP3 is selected
            
        Returns:
            HTML string with format information
        """
        return self._get_format_info_html(selected_format, mp3_bitrate)
    
    def update_filename_preview(self, file_path: Optional[str], voice_path: Optional[str],
                              output_format: str = "MP3") -> str:
        """
        Update filename preview display.
        
        Args:
            file_path: Source file path
            voice_path: Voice sample path
            output_format: Output audio format
            
        Returns:
            HTML string with filename preview
        """
        if not file_path or not voice_path:
            return ""
        
        # Generate preview filename
        filename = self.enhanced_webui.get_output_manager().generate_filename(
            file_path, voice_path, output_format.lower()
        )
        
        return f"""
        <div class="filename-preview">
            <strong>Output filename:</strong> <code>{filename}</code>
        </div>
        """
    
    def get_filename_only(self, file_path: Optional[str], voice_path: Optional[str],
                         output_format: str = "MP3") -> str:
        """
        Get just the filename without HTML formatting.
        
        Args:
            file_path: Source file path
            voice_path: Voice sample path
            output_format: Output audio format
            
        Returns:
            Plain filename string
        """
        if not file_path or not voice_path:
            return ""
        
        # Generate preview filename
        return self.enhanced_webui.get_output_manager().generate_filename(
            file_path, voice_path, output_format.lower()
        )
    
    def update_generation_progress(self, progress: float, stage: str = "", 
                                 estimated_remaining: Optional[float] = None) -> str:
        """
        Update generation progress display.
        
        Args:
            progress: Progress value (0.0 to 1.0)
            stage: Current processing stage
            estimated_remaining: Estimated remaining time in seconds
            
        Returns:
            HTML string with progress display
        """
        progress_text = ""
        if stage:
            progress_text = f"Stage: {stage}"
        
        if estimated_remaining and estimated_remaining > 0:
            if estimated_remaining < 60:
                time_str = f"{estimated_remaining:.0f}s"
            else:
                minutes = int(estimated_remaining // 60)
                seconds = int(estimated_remaining % 60)
                time_str = f"{minutes}m {seconds}s"
            
            if progress_text:
                progress_text += f" | ETA: {time_str}"
            else:
                progress_text = f"ETA: {time_str}"
        
        return self.theme_manager.create_progress_bar(progress, progress_text)
    
    def update_task_list(self) -> str:
        """
        Update background task list display.
        
        Returns:
            HTML string with task list
        """
        task_manager = self.enhanced_webui.get_task_manager()
        # TaskManager has get_all_tasks(); filter to active tasks here
        tasks = task_manager.get_all_tasks()
        active_tasks = [t for t in tasks.values() if getattr(t, 'is_active', False)]
        
        if not active_tasks:
            return '<div class="status-info">No active background tasks</div>'
        
        task_html = ""
        for task in active_tasks:
            task_html += self.theme_manager.create_task_status_html(
                task.task_id,
                task.status,
                task.progress,
                task.current_stage,
                task.estimated_remaining
            )
        
        return f'<div class="task-list">{task_html}</div>'
    
    def _get_format_info_html(self, format_name: str, mp3_bitrate: int = 64) -> str:
        """Get format information HTML."""
        format_info = {
            "WAV": {
                "description": "Uncompressed audio format",
                "quality": "Highest quality",
                "size": "Large file size",
                "compatibility": "Universal compatibility"
            },
            "MP3": {
                "description": f"Compressed audio format ({mp3_bitrate} kbps)",
                "quality": "Good quality" if mp3_bitrate >= 128 else "Standard quality",
                "size": "Smaller file size",
                "compatibility": "Universal compatibility"
            },
            "M4B": {
                "description": "Audiobook format with chapters",
                "quality": "Good quality",
                "size": "Optimized for audiobooks",
                "compatibility": "Supports chapter navigation"
            }
        }
        
        info = format_info.get(format_name, {})
        if not info:
            return ""
        
        return f"""
        <div class="format-info">
            <strong>{format_name}:</strong> {info.get('description', '')}<br>
            <small>
                Quality: {info.get('quality', '')} | 
                Size: {info.get('size', '')} | 
                {info.get('compatibility', '')}
            </small>
        </div>
        """
    
    def _get_enhanced_voice_status_html(self, samples: List) -> str:
        """Get enhanced voice status HTML."""
        if not samples:
            return self.theme_manager.create_status_message(
                "No voice samples found. Please add samples to the 'samples' folder.", "warning"
            )
        
        return self.theme_manager.create_status_message(
            f"Found {len(samples)} voice samples", "success"
        )
    
    def _get_save_info_html(self) -> str:
        """Get save information HTML."""
        return """
        <div class="save-info">
            <small>
                Files will be saved to the <code>outputs</code> folder with format:<br>
                <code>filename_YYYYMMDD_HHMMSS_voicename.ext</code>
            </small>
        </div>
        """
    
    def _get_task_info_html(self) -> str:
        """Get task information HTML."""
        return """
        <div class="task-info">
            <small>
                Background tasks are automatically created for large files.<br>
                You can continue using the interface while tasks are processing.
            </small>
        </div>
        """
    
    def _get_incremental_auto_save_info_html(self) -> str:
        """Get incremental auto-save information HTML."""
        return """
        <div class="auto-save-info">
            <small>
                <strong>增量自动保存功能：</strong><br>
                • 在音频生成过程中定期保存进度<br>
                • 防止生成失败时丢失已完成的音频<br>
                • 较小的间隔值会更频繁保存，但可能影响性能<br>
                • 建议长文本使用较小间隔（3-5），短文本使用较大间隔（5-8）
            </small>
        </div>
        """
    
    def create_save_status_notification(self, notification_type: str, title: str, message: str, 
                                       details: Optional[Dict[str, Any]] = None,
                                       show_details: bool = False,
                                       actions: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Create enhanced save status notification HTML with details and actions.
        
        Args:
            notification_type: Type of notification ('success', 'error', 'warning', 'recovery')
            title: Notification title
            message: Notification message
            details: Optional detailed information
            show_details: Whether to show detailed information
            actions: Optional list of action buttons
            
        Returns:
            HTML string for notification display
        """
        if notification_type == 'success':
            icon = '✅'
            color = '#28a745'
            bg_color = '#d4edda'
            border_color = '#c3e6cb'
        elif notification_type == 'error':
            icon = '❌'
            color = '#dc3545'
            bg_color = '#f8d7da'
            border_color = '#f5c6cb'
        elif notification_type == 'warning':
            icon = '⚠️'
            color = '#ffc107'
            bg_color = '#fff3cd'
            border_color = '#ffeaa7'
        elif notification_type == 'recovery':
            icon = '🔄'
            color = '#17a2b8'
            bg_color = '#d1ecf1'
            border_color = '#bee5eb'
        else:
            icon = 'ℹ️'
            color = '#17a2b8'
            bg_color = '#d1ecf1'
            border_color = '#bee5eb'
        
        # Build notification HTML
        notification_html = f"""
        <div class="auto-save-notification" style="
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            color: {color};
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="font-weight: bold; margin-bottom: 8px; display: flex; align-items: center;">
                <span style="margin-right: 8px; font-size: 16px;">{icon}</span>
                <span>{title}</span>
            </div>
            <div style="font-size: 13px; margin-bottom: 8px;">
                {message}
            </div>
        """
        
        # Add detailed information if available
        if show_details and details:
            notification_html += '<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.1);">'
            
            # Add suggestion if available
            if details.get('suggestion'):
                notification_html += f'<div style="font-size: 12px; color: #6c757d; margin-bottom: 6px;"><strong>建议:</strong> {details["suggestion"]}</div>'
            
            # Add file information if available
            if details.get('file_info'):
                notification_html += f'<div style="font-size: 12px; color: #6c757d; margin-bottom: 4px;">{details["file_info"]}</div>'
            
            # Add duration information if available
            if details.get('duration_info'):
                notification_html += f'<div style="font-size: 12px; color: #6c757d; margin-bottom: 4px;">{details["duration_info"]}</div>'
            
            # Add recovery instructions if available
            if details.get('instructions'):
                notification_html += '<div style="font-size: 12px; color: #6c757d; margin-top: 8px;"><strong>恢复步骤:</strong></div>'
                for instruction in details['instructions']:
                    notification_html += f'<div style="font-size: 12px; color: #6c757d; margin-left: 8px;">{instruction}</div>'
            
            notification_html += '</div>'
        
        # Add action buttons if available
        if actions:
            notification_html += '<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.1);">'
            for action in actions:
                button_color = '#007bff' if action['id'] != 'restart_generation' else '#6c757d'
                notification_html += f"""
                <button onclick="handleNotificationAction('{action['id']}')" style="
                    background-color: {button_color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    margin-right: 8px;
                    margin-bottom: 4px;
                    font-size: 12px;
                    cursor: pointer;
                " title="{action.get('description', '')}">{action['label']}</button>
                """
            notification_html += '</div>'
        
        notification_html += '</div>'
        
        return notification_html
    
    def format_progress_with_save_indicators(self, base_progress: str, save_status: str) -> str:
        """
        Format progress message with save status indicators.
        
        Args:
            base_progress: Base progress message
            save_status: Save status text
            
        Returns:
            Enhanced progress message with save indicators
        """
        if not save_status:
            return base_progress
        
        # Add visual indicators for different save states
        if "已保存 ✓" in save_status:
            # Success indicator
            save_indicator = f'<span style="color: #28a745; font-weight: bold;">{save_status}</span>'
        elif "保存失败 ⚠️" in save_status:
            # Error indicator
            save_indicator = f'<span style="color: #dc3545; font-weight: bold;">{save_status}</span>'
        elif "下次保存:" in save_status:
            # Next save indicator
            save_indicator = f'<span style="color: #6c757d;">{save_status}</span>'
        else:
            save_indicator = save_status
        
        return f"{base_progress} {save_indicator}"
    
    def create_progress_html_with_save_status(self, progress_percent: float, status_text: str, 
                                            save_notification: Optional[Dict[str, str]] = None) -> str:
        """
        Create enhanced progress HTML with save status integration.
        
        Args:
            progress_percent: Progress percentage (0-100)
            status_text: Status text to display
            save_notification: Optional save notification to display
            
        Returns:
            HTML string with enhanced progress display
        """
        # Base progress bar
        progress_html = f"""
        <div style="margin-bottom: 10px;">
            <div style="background: #f0f0f0; border-radius: 10px; overflow: hidden; height: 20px; position: relative;">
                <div style="width: {progress_percent:.1f}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); transition: width 0.2s ease;"></div>
            </div>
            <div style="margin-top: 5px; font-size: 14px; color: #333;">
                {status_text}
            </div>
        </div>
        """
        
        # Add save notification if present
        if save_notification:
            notification_html = self.create_save_status_notification(
                save_notification['type'],
                save_notification['title'],
                save_notification['message']
            )
            progress_html += notification_html
        
        return progress_html
    
    def handle_auto_save_config_change(self, enabled: bool, interval: int, 
                                     context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Handle auto-save configuration changes with validation and user feedback.
        
        Args:
            enabled: Whether auto-save is enabled
            interval: Auto-save interval value
            context: Optional context information
            
        Returns:
            Tuple of (updated_info_html, feedback_data)
        """
        from ..auto_save.config_validator import create_config_validator
        
        validator = create_config_validator()
        
        # Validate settings
        is_valid, error_msg, validation_details = self.validate_auto_save_settings(enabled, interval, context)
        
        # Save user preferences if valid
        if is_valid and enabled:
            validator.save_user_preferences(enabled, interval)
        
        # Generate updated info HTML
        updated_info = self.update_auto_save_info(enabled, interval, context)
        
        # Prepare feedback data
        feedback_data = {
            'is_valid': is_valid,
            'error_message': error_msg,
            'warning_message': validation_details.get('warning_message', ''),
            'suggestions': validation_details.get('suggestions', []),
            'corrected_value': validation_details.get('corrected_value'),
            'recommended_settings': validation_details.get('recommended_settings'),
            'preferences_saved': is_valid and enabled
        }
        
        return updated_info, feedback_data
    
    def create_auto_save_validation_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """
        Create user-friendly validation feedback HTML.
        
        Args:
            feedback_data: Feedback data from validation
            
        Returns:
            HTML string with validation feedback
        """
        # Check if we have any feedback to show
        has_error = not feedback_data['is_valid']
        has_warning = bool(feedback_data.get('warning_message', ''))
        has_suggestions = bool(feedback_data.get('suggestions', []))
        has_recommendations = bool(feedback_data.get('recommended_settings'))
        
        if not (has_error or has_warning or has_suggestions or has_recommendations):
            return ""  # No feedback needed
        
        feedback_html = '<div class="auto-save-feedback" style="margin-top: 10px;">'
        
        # Error feedback
        if not feedback_data['is_valid']:
            feedback_html += f"""
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px; padding: 8px; margin-bottom: 8px;">
                <strong style="color: #721c24;">❌ 配置错误</strong><br>
                <span style="color: #721c24; font-size: 13px;">{feedback_data['error_message']}</span>
            """
            
            if feedback_data['corrected_value'] is not None:
                feedback_html += f"""
                <br><span style="color: #856404; font-size: 12px;">
                    💡 建议使用：{feedback_data['corrected_value']}
                </span>
                """
            
            feedback_html += "</div>"
        
        # Warning feedback
        if has_warning:
            feedback_html += f"""
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 8px; margin-bottom: 8px;">
                <strong style="color: #856404;">⚠️ 注意</strong><br>
                <span style="color: #856404; font-size: 13px;">{feedback_data.get('warning_message', '')}</span>
            </div>
            """
        
        # Suggestions
        suggestions = feedback_data.get('suggestions', [])
        if suggestions:
            feedback_html += '<div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 6px; padding: 8px; margin-bottom: 8px;">'
            feedback_html += '<strong style="color: #0c5460;">💡 建议</strong><br>'
            for suggestion in suggestions[:3]:  # Show up to 3 suggestions
                feedback_html += f'<span style="color: #0c5460; font-size: 12px;">• {suggestion}</span><br>'
            feedback_html += '</div>'
        
        # Recommended settings
        recommended = feedback_data.get('recommended_settings')
        if recommended and recommended.get('interval') != feedback_data.get('current_interval'):
            feedback_html += f"""
            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; padding: 8px;">
                <strong style="color: #155724;">🎯 推荐设置</strong><br>
                <span style="color: #155724; font-size: 12px;">
                    间隔：{recommended['interval']} - {recommended['reason']}
                </span>
            </div>
            """
        
        feedback_html += '</div>'
        return feedback_html
    
    def get_auto_save_context_info(self, text_content: str = "", file_path: str = "") -> Dict[str, Any]:
        """
        Generate context information for auto-save validation.
        
        Args:
            text_content: Text content to be processed
            file_path: Path to uploaded file (if any)
            
        Returns:
            Dictionary with context information
        """
        import os
        import shutil
        
        context = {}
        
        # Text length analysis
        if text_content:
            context['text_length'] = len(text_content)
            # Estimate segments (rough calculation)
            context['estimated_segments'] = max(1, len(text_content) // 100)
            # Rough estimate of output audio size (very approximate)
            context['estimated_file_size_mb'] = context['text_length'] * 0.001  # ~1KB per character
        
        # File size analysis
        if file_path and os.path.exists(file_path):
            file_size_bytes = os.path.getsize(file_path)
            context['file_size_mb'] = file_size_bytes / (1024 * 1024)
            # Update estimated file size based on actual file if available
            if 'estimated_file_size_mb' not in context:
                context['estimated_file_size_mb'] = context.get('text_length', 0) * 0.001  # ~1KB per character
        
        # System information
        try:
            # Get available disk space
            if hasattr(shutil, 'disk_usage'):
                usage = shutil.disk_usage('.')
                context['available_disk_space_mb'] = usage.free / (1024 * 1024)
            
            # Simple system load estimation (placeholder)
            context['system_load_percent'] = 50  # Default moderate load
        except:
            pass
        
        return context
    
    def validate_auto_save_settings(self, enabled: bool, interval: int, 
                                  context: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enhanced validation of auto-save configuration settings.
        
        Args:
            enabled: Whether auto-save is enabled
            interval: Auto-save interval value
            context: Optional context information for enhanced validation
            
        Returns:
            Tuple of (is_valid, error_message, validation_details)
        """
        # Import here to avoid circular imports
        from ..auto_save.config_validator import create_config_validator
        
        validator = create_config_validator()
        result = validator.validate_auto_save_settings(enabled, interval, context)
        
        validation_details = {
            'corrected_value': result.corrected_value,
            'warning_message': result.warning_message,
            'suggestions': result.suggestions,
            'recommended_settings': validator.get_recommended_settings(context) if context else None
        }
        
        return result.is_valid, result.error_message, validation_details
    
    def update_auto_save_info(self, enabled: bool, interval: int, 
                            context: Optional[Dict[str, Any]] = None) -> str:
        """
        Enhanced update of auto-save information display with comprehensive validation.
        
        Args:
            enabled: Whether auto-save is enabled
            interval: Auto-save interval value
            context: Optional context information for enhanced validation
            
        Returns:
            HTML string with updated auto-save information
        """
        if not enabled:
            return """
            <div class="auto-save-info disabled">
                <small>
                    <strong>⚠️ 增量自动保存已禁用</strong><br>
                    只有在生成完全完成后才会保存最终音频文件<br>
                    <span style="color: #6c757d;">提示：启用自动保存可以防止生成失败时的数据丢失</span>
                </small>
            </div>
            """
        
        # Enhanced validation with context
        is_valid, error_msg, validation_details = self.validate_auto_save_settings(enabled, interval, context)
        
        if not is_valid:
            corrected_value = validation_details.get('corrected_value')
            suggestions = validation_details.get('suggestions', [])
            
            error_html = f"""
            <div class="auto-save-info error">
                <small>
                    <strong>❌ 配置错误：</strong>{error_msg}
                </small>
            """
            
            if corrected_value is not None:
                error_html += f"""
                <br><small style="color: #6c757d;">
                    建议值：{corrected_value}
                </small>
                """
            
            if suggestions:
                error_html += "<br><small style='color: #6c757d;'>"
                for suggestion in suggestions[:2]:  # Show first 2 suggestions
                    error_html += f"• {suggestion}<br>"
                error_html += "</small>"
            
            error_html += "</div>"
            return error_html
        
        # Build success message with warnings and suggestions
        info_html = f"""
        <div class="auto-save-info enabled">
            <small>
                <strong>✅ 增量自动保存已启用</strong><br>
                每生成 {interval} 个段落后自动保存进度
        """
        
        # Add warning message if present
        warning_msg = validation_details.get('warning_message', '')
        if warning_msg:
            info_html += f"<br><strong>⚠️ 注意：</strong>{warning_msg}"
        
        # Add helpful suggestions
        suggestions = validation_details.get('suggestions', [])
        if suggestions:
            info_html += "<br><span style='color: #6c757d; font-size: 11px;'>"
            for suggestion in suggestions[:2]:  # Show first 2 suggestions
                info_html += f"💡 {suggestion}<br>"
            info_html += "</span>"
        
        # Add recommended settings if different from current
        recommended = validation_details.get('recommended_settings')
        if recommended and recommended['interval'] != interval:
            info_html += f"""
            <br><span style='color: #17a2b8; font-size: 11px;'>
                💡 推荐设置：间隔 {recommended['interval']} ({recommended['reason']})
            </span>
            """
        
        info_html += """
            </small>
        </div>
        """
        
        return info_html
    
    def create_comprehensive_error_notification(self, error_info: Dict[str, Any], 
                                              step: int) -> str:
        """
        Create comprehensive error notification with recovery guidance.
        Implements requirement 4.3: save failure notification system.
        
        Args:
            error_info: Error information from notification system
            step: Generation step where error occurred
            
        Returns:
            HTML string for comprehensive error display
        """
        # Get error classification and user-friendly message
        error_type = error_info.get('error_type', 'unknown_error')
        
        # Error type specific styling and icons
        error_configs = {
            'disk_space_full': {'icon': '💾', 'color': '#dc3545', 'urgency': 'high'},
            'permission_denied': {'icon': '🔒', 'color': '#dc3545', 'urgency': 'high'},
            'filesystem_error': {'icon': '📁', 'color': '#ffc107', 'urgency': 'medium'},
            'network_error': {'icon': '🌐', 'color': '#ffc107', 'urgency': 'medium'},
            'memory_error': {'icon': '🧠', 'color': '#ffc107', 'urgency': 'medium'},
            'audio_processing_error': {'icon': '🎵', 'color': '#ffc107', 'urgency': 'medium'},
            'validation_failed': {'icon': '⚠️', 'color': '#dc3545', 'urgency': 'high'},
            'unknown_error': {'icon': '❓', 'color': '#6c757d', 'urgency': 'low'}
        }
        
        config = error_configs.get(error_type, error_configs['unknown_error'])
        
        # Build comprehensive error notification
        notification_html = f"""
        <div class="comprehensive-error-notification" style="
            background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
            border: 2px solid {config['color']};
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 24px; margin-right: 12px;">{config['icon']}</span>
                <div>
                    <h4 style="margin: 0; color: {config['color']}; font-size: 18px;">
                        自动保存失败 - 段落 {step}
                    </h4>
                    <div style="font-size: 14px; color: #6c757d; margin-top: 4px;">
                        错误类型: {error_info.get('title', '未知错误')}
                    </div>
                </div>
            </div>
            
            <div style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="font-size: 14px; color: #333; margin-bottom: 12px;">
                    <strong>问题描述:</strong> {error_info.get('message', '发生未知错误')}
                </div>
                <div style="font-size: 14px; color: #28a745;">
                    <strong>建议解决方案:</strong> {error_info.get('suggestion', '请查看详细日志')}
                </div>
            </div>
        """
        
        # Add recovery status if available
        if error_info.get('recovery_attempted'):
            recovery_successful = error_info.get('recovery_successful', False)
            recovery_icon = '✅' if recovery_successful else '🔄'
            recovery_color = '#28a745' if recovery_successful else '#ffc107'
            recovery_text = '恢复成功' if recovery_successful else '正在尝试恢复'
            
            notification_html += f"""
            <div style="background: white; border-radius: 8px; padding: 12px; margin-bottom: 16px; border-left: 4px solid {recovery_color};">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 16px; margin-right: 8px;">{recovery_icon}</span>
                    <span style="font-size: 14px; color: {recovery_color}; font-weight: bold;">{recovery_text}</span>
                </div>
            </div>
            """
        
        # Add action buttons
        notification_html += """
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button onclick="dismissNotification(this)" style="
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                cursor: pointer;
            ">知道了</button>
            <button onclick="showErrorDetails(this)" style="
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                cursor: pointer;
            ">查看详情</button>
        </div>
        
        </div>
        """
        
        return notification_html
    
    def create_recovery_instructions_panel(self, recovery_info: Dict[str, Any]) -> str:
        """
        Create recovery instructions panel with step-by-step guidance.
        Implements requirement 5.6: recovery instructions when partial audio is available.
        
        Args:
            recovery_info: Recovery information from notification system
            
        Returns:
            HTML string for recovery instructions panel
        """
        recovery_type = recovery_info.get('recovery_type', 'no_recovery_available')
        
        # Recovery type specific configurations
        recovery_configs = {
            'partial_audio_available': {
                'icon': '🎵', 'color': '#28a745', 'title': '部分音频可恢复'
            },
            'backup_recovery_available': {
                'icon': '💾', 'color': '#17a2b8', 'title': '备份文件可用'
            },
            'buffer_recovery_available': {
                'icon': '🧠', 'color': '#ffc107', 'title': '内存缓存可恢复'
            },
            'multiple_recovery_options': {
                'icon': '🔄', 'color': '#6f42c1', 'title': '多种恢复选项'
            },
            'no_recovery_available': {
                'icon': '❌', 'color': '#dc3545', 'title': '无法恢复'
            }
        }
        
        config = recovery_configs.get(recovery_type, recovery_configs['no_recovery_available'])
        
        panel_html = f"""
        <div class="recovery-instructions-panel" style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid {config['color']};
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <span style="font-size: 32px; margin-right: 16px;">{config['icon']}</span>
                <div>
                    <h3 style="margin: 0; color: {config['color']}; font-size: 20px;">
                        {config['title']}
                    </h3>
                    <div style="font-size: 16px; color: #6c757d; margin-top: 4px;">
                        {recovery_info.get('message', '检测到可恢复的音频内容')}
                    </div>
                </div>
            </div>
        """
        
        # Add file information if available
        if recovery_info.get('file_info'):
            panel_html += f"""
            <div style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px; border-left: 4px solid {config['color']};">
                <div style="font-size: 14px; color: #333;">
                    <strong>📁 文件信息:</strong> {recovery_info['file_info']}
                </div>
            """
            
            if recovery_info.get('duration_info'):
                panel_html += f"""
                <div style="font-size: 14px; color: #333; margin-top: 8px;">
                    <strong>⏱️ 时长信息:</strong> {recovery_info['duration_info']}
                </div>
                """
            
            panel_html += '</div>'
        
        # Add step-by-step instructions
        if recovery_info.get('instructions'):
            panel_html += f"""
            <div style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: {config['color']}; font-size: 16px;">
                    📋 恢复步骤:
                </h4>
            """
            
            for i, instruction in enumerate(recovery_info['instructions'], 1):
                panel_html += f"""
                <div style="display: flex; align-items: flex-start; margin-bottom: 8px;">
                    <span style="
                        background-color: {config['color']};
                        color: white;
                        border-radius: 50%;
                        width: 24px;
                        height: 24px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        font-weight: bold;
                        margin-right: 12px;
                        flex-shrink: 0;
                    ">{i}</span>
                    <span style="font-size: 14px; color: #333; line-height: 1.5;">{instruction}</span>
                </div>
                """
            
            panel_html += '</div>'
        
        # Add warning if applicable
        if recovery_info.get('warning'):
            panel_html += f"""
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 16px; margin-right: 8px;">⚠️</span>
                    <span style="font-size: 14px; color: #856404;">
                        <strong>注意:</strong> {recovery_info['warning']}
                    </span>
                </div>
            </div>
            """
        
        # Add action buttons
        if recovery_info.get('actions'):
            panel_html += '<div style="display: flex; gap: 12px; flex-wrap: wrap;">'
            
            for action in recovery_info['actions']:
                button_style = self._get_action_button_style(action['id'])
                panel_html += f"""
                <button onclick="handleRecoveryAction('{action['id']}')" style="{button_style}" 
                        title="{action.get('description', '')}">
                    {action['label']}
                </button>
                """
            
            panel_html += '</div>'
        
        panel_html += '</div>'
        
        return panel_html
    
    def _get_action_button_style(self, action_id: str) -> str:
        """Get CSS style for action buttons based on action type."""
        button_styles = {
            'open_recovery_file': 'background-color: #28a745; color: white;',
            'continue_from_recovery': 'background-color: #007bff; color: white;',
            'restart_generation': 'background-color: #6c757d; color: white;',
            'adjust_save_settings': 'background-color: #17a2b8; color: white;'
        }
        
        base_style = """
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        """
        
        specific_style = button_styles.get(action_id, 'background-color: #6c757d; color: white;')
        
        return base_style + specific_style
    
    def create_console_log_display(self, log_messages: List[str], max_lines: int = 10) -> str:
        """
        Create console log display for auto-save operations.
        Implements requirement 4.4: console logging display in UI.
        
        Args:
            log_messages: List of log messages to display
            max_lines: Maximum number of lines to show
            
        Returns:
            HTML string for console log display
        """
        if not log_messages:
            return """
            <div class="console-log-display" style="
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border-radius: 8px;
                padding: 16px;
                margin: 12px 0;
                max-height: 200px;
                overflow-y: auto;
            ">
                <div style="color: #6c757d; text-align: center;">
                    暂无自动保存日志
                </div>
            </div>
            """
        
        # Limit messages to max_lines
        display_messages = log_messages[-max_lines:] if len(log_messages) > max_lines else log_messages
        
        console_html = """
        <div class="console-log-display" style="
            background: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #333;
        ">
        """
        
        for message in display_messages:
            # Color code messages based on content
            if '✅' in message or 'success' in message.lower():
                color = '#4ade80'  # Green for success
            elif '❌' in message or 'error' in message.lower() or 'failed' in message.lower():
                color = '#f87171'  # Red for errors
            elif '⚠️' in message or 'warning' in message.lower():
                color = '#fbbf24'  # Yellow for warnings
            elif '🔄' in message or 'recovery' in message.lower():
                color = '#60a5fa'  # Blue for recovery
            else:
                color = '#d4d4d4'  # Default gray
            
            console_html += f"""
            <div style="color: {color}; margin-bottom: 4px; line-height: 1.4;">
                {message}
            </div>
            """
        
        # Add scroll to bottom indicator if there are more messages
        if len(log_messages) > max_lines:
            console_html += f"""
            <div style="color: #6c757d; text-align: center; margin-top: 8px; font-style: italic;">
                ... 显示最近 {max_lines} 条日志 (共 {len(log_messages)} 条)
            </div>
            """
        
        console_html += '</div>'
        
        return console_html
    
    def create_save_status_summary(self, save_status: Dict[str, Any]) -> str:
        """
        Create save status summary display.
        
        Args:
            save_status: Save status information from save manager
            
        Returns:
            HTML string for save status summary
        """
        if not save_status.get('enabled', False):
            return """
            <div class="save-status-summary disabled" style="
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                margin: 8px 0;
                color: #6c757d;
                text-align: center;
            ">
                <span style="font-size: 14px;">⚠️ 增量自动保存已禁用</span>
            </div>
            """
        
        current_step = save_status.get('current_step', 0)
        last_save_step = save_status.get('last_save_step', 0)
        next_save_step = save_status.get('next_save_step', 0)
        save_interval = save_status.get('save_interval', 5)
        
        # Determine status color and icon
        if save_status.get('last_save_info', {}).get('success', True):
            status_color = '#28a745'
            status_icon = '✅'
            status_text = '正常'
        else:
            status_color = '#dc3545'
            status_icon = '❌'
            status_text = '异常'
        
        summary_html = f"""
        <div class="save-status-summary" style="
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h5 style="margin: 0; color: #333; font-size: 16px;">自动保存状态</h5>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 14px; margin-right: 6px;">{status_icon}</span>
                    <span style="color: {status_color}; font-weight: bold; font-size: 14px;">{status_text}</span>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px;">
                <div>
                    <div style="color: #6c757d; margin-bottom: 4px;">当前段落:</div>
                    <div style="font-weight: bold; color: #333;">{current_step}</div>
                </div>
                <div>
                    <div style="color: #6c757d; margin-bottom: 4px;">保存间隔:</div>
                    <div style="font-weight: bold; color: #333;">{save_interval} 段落</div>
                </div>
                <div>
                    <div style="color: #6c757d; margin-bottom: 4px;">上次保存:</div>
                    <div style="font-weight: bold; color: #333;">段落 {last_save_step}</div>
                </div>
                <div>
                    <div style="color: #6c757d; margin-bottom: 4px;">下次保存:</div>
                    <div style="font-weight: bold; color: #333;">段落 {next_save_step}</div>
                </div>
            </div>
        """
        
        # Add buffer information if available
        buffer_info = save_status.get('buffer_info', {})
        if buffer_info:
            segment_count = buffer_info.get('segment_count', 0)
            total_duration = buffer_info.get('total_duration', 0.0)
            
            summary_html += f"""
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #dee2e6;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px;">
                    <div>
                        <div style="color: #6c757d; margin-bottom: 4px;">缓存段落:</div>
                        <div style="font-weight: bold; color: #333;">{segment_count} 个</div>
                    </div>
                    <div>
                        <div style="color: #6c757d; margin-bottom: 4px;">缓存时长:</div>
                        <div style="font-weight: bold; color: #333;">{total_duration:.1f} 秒</div>
                    </div>
                </div>
            </div>
            """
        
        summary_html += '</div>'
        
        return summary_html
    
    def get_custom_css(self) -> str:
        """Get custom CSS for enhanced components."""
        base_css = self.theme_manager.get_custom_css()
        
        # Add CSS for notification system components
        notification_css = """
        /* Auto-save notification system styles */
        .auto-save-notification {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .comprehensive-error-notification {
            animation: shake 0.5s ease-in-out;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .recovery-instructions-panel {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .console-log-display {
            scrollbar-width: thin;
            scrollbar-color: #6c757d #1e1e1e;
        }
        
        .console-log-display::-webkit-scrollbar {
            width: 8px;
        }
        
        .console-log-display::-webkit-scrollbar-track {
            background: #1e1e1e;
        }
        
        .console-log-display::-webkit-scrollbar-thumb {
            background: #6c757d;
            border-radius: 4px;
        }
        
        .save-status-summary {
            transition: all 0.2s ease;
        }
        
        .save-status-summary:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Button hover effects */
        button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        
        /* Responsive design for notifications */
        @media (max-width: 768px) {
            .comprehensive-error-notification,
            .recovery-instructions-panel {
                padding: 16px;
                margin: 12px 0;
            }
            
            .save-status-summary {
                padding: 12px;
            }
        }
        """
        
        return base_css + notification_css


def create_enhanced_interface_with_theme() -> Tuple[gr.Interface, str]:
    """
    Create enhanced interface with dark theme support.
    
    Returns:
        Tuple of (interface, custom_css)
    """
    theme_manager = get_theme_manager()
    
    # This would be implemented in the main webui.py file
    # For now, just return the CSS
    return None, theme_manager.get_custom_css()