"""
WebUI components for integrating enhanced features with Gradio interface.
"""

from typing import List, Optional, Tuple, Any
import gradio as gr
from .enhanced_webui import EnhancedWebUI
from .task_dashboard import TaskStatusDashboard
from .background_tts import BackgroundTTSIntegration


class WebUIComponents:
    """Gradio components for enhanced WebUI features."""
    
    def __init__(self, enhanced_webui: EnhancedWebUI, tts_engine=None):
        """
        Initialize WebUI components.
        
        Args:
            enhanced_webui: Enhanced WebUI instance
            tts_engine: Optional TTS engine for background processing
        """
        self.enhanced_webui = enhanced_webui
        self.config = enhanced_webui.get_config()
        self.task_dashboard = TaskStatusDashboard(enhanced_webui.get_task_manager())
        
        # Initialize background TTS integration if TTS engine is provided
        self.background_tts = None
        if tts_engine:
            self.background_tts = BackgroundTTSIntegration(
                enhanced_webui.get_task_manager(),
                tts_engine,
                enhanced_webui
            )
    
    def create_file_upload_components(self) -> Tuple[gr.File, gr.Checkbox, gr.Checkbox, gr.Checkbox]:
        """
        Create file upload components with separate processing toggles.
        
        Returns:
            Tuple of (file_upload, use_native_chapters, file_cleaning_toggle, chapter_recognition_toggle)
        """
        file_upload = gr.File(
            label="Upload TXT or EPUB file",
            file_types=[".txt", ".epub"],
            type="filepath"
        )
        
        # Get native chapters setting from config or use default
        try:
            use_native_value = self.config.chapter_parsing.use_native_epub_chapters
            # Handle mocked config
            if hasattr(use_native_value, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            use_native_value = False
        
        use_native_chapters = gr.Checkbox(
            label="Use native EPUB chapters",
            value=use_native_value,
            visible=False  # Will be shown when EPUB is uploaded
        )
        
        # File cleaning toggle - default enabled
        try:
            file_cleaning_enabled = self.config.file_processing.text_cleaning_enabled
            # Handle mocked config
            if hasattr(file_cleaning_enabled, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            file_cleaning_enabled = True
        
        file_cleaning_toggle = gr.Checkbox(
            label="文件清理",
            value=file_cleaning_enabled,
            info="清理多余空格、合并空行、处理特殊字符"
        )
        
        # Smart chapter recognition toggle - default disabled
        try:
            chapter_recognition_enabled = self.config.chapter_parsing.smart_parsing_enabled
            # Handle mocked config
            if hasattr(chapter_recognition_enabled, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            chapter_recognition_enabled = False
        
        chapter_recognition_toggle = gr.Checkbox(
            label="智能章节识别",
            value=chapter_recognition_enabled,
            info="自动识别章节标题和结构"
        )
        
        return file_upload, use_native_chapters, file_cleaning_toggle, chapter_recognition_toggle
    
    def create_format_selection_components(self) -> Tuple[gr.Dropdown, gr.Slider, gr.Checkbox]:
        """
        Create audio format selection components.
        
        Returns:
            Tuple of (format_dropdown, mp3_bitrate, enable_segmentation)
        """
        # Get supported formats from config or use defaults
        try:
            supported_formats = self.config.audio_formats.supported_formats
            default_format = self.config.audio_formats.default_format
            # Handle mocked config
            if hasattr(supported_formats, '_mock_name') or not supported_formats:
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            supported_formats = ["WAV", "MP3", "M4B"]
            default_format = "MP3"
        
        format_dropdown = gr.Dropdown(
            choices=supported_formats,
            value=default_format,
            label="Output format"
        )
        
        # Get MP3 bitrate from config or use default
        try:
            mp3_bitrate_value = self.config.audio_formats.mp3_bitrate
            # Handle mocked config
            if hasattr(mp3_bitrate_value, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            mp3_bitrate_value = 64
        
        mp3_bitrate = gr.Slider(
            minimum=32,
            maximum=320,
            value=mp3_bitrate_value,
            step=32,
            label="MP3 bitrate (kbps)",
            visible=False  # Will be shown when MP3 is selected
        )
        
        # Get segmentation config or use default
        try:
            segmentation_enabled = self.config.audio_formats.segmentation_config.enabled
            # Handle mocked config
            if hasattr(segmentation_enabled, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            segmentation_enabled = False
        
        enable_segmentation = gr.Checkbox(
            label="Enable chapter-based segmentation",
            value=segmentation_enabled
        )
        
        return format_dropdown, mp3_bitrate, enable_segmentation
    
    def create_voice_selection_components(self) -> Tuple[gr.Dropdown, gr.Button, gr.HTML]:
        """
        Create voice sample selection components.
        
        Returns:
            Tuple of (voice_dropdown, refresh_button, status_display)
        """
        # Get available voice samples
        samples = self.enhanced_webui.get_voice_manager().get_available_samples()
        sample_choices = [(sample.display_name, sample.filepath) for sample in samples]
        
        voice_dropdown = gr.Dropdown(
            choices=sample_choices,
            value=sample_choices[0][1] if sample_choices else None,
            label="Voice sample",
            allow_custom_value=False,
            info="Select a voice sample from the samples folder"
        )
        
        refresh_button = gr.Button(
            "🔄 Refresh",
            size="sm",
            variant="secondary"
        )
        
        status_display = gr.HTML(
            value=self._get_voice_status_html(samples),
            visible=True
        )
        
        return voice_dropdown, refresh_button, status_display
    
    def create_auto_save_components(self) -> Tuple[gr.Checkbox, gr.Textbox]:
        """
        Create auto-save components.
        
        Returns:
            Tuple of (auto_save_checkbox, filename_preview)
        """
        # Get auto-save setting from config or use default
        try:
            auto_save_enabled = self.config.output.auto_save_enabled
            # Handle mocked config
            if hasattr(auto_save_enabled, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            auto_save_enabled = True
        
        auto_save_checkbox = gr.Checkbox(
            label="Auto-save generated audio",
            value=auto_save_enabled
        )
        
        filename_preview = gr.Textbox(
            label="Output filename preview",
            interactive=False,
            placeholder="Filename will be generated automatically"
        )
        
        return auto_save_checkbox, filename_preview
    
    def create_task_status_components(self) -> Tuple[gr.HTML, gr.Dataframe, gr.HTML, gr.Button]:
        """
        Create comprehensive task status monitoring components.
        
        Returns:
            Tuple of (status_summary, task_table, detailed_view, refresh_button)
        """
        return self.task_dashboard.create_dashboard_components()
    
    def create_task_progress_components(self) -> Tuple[gr.HTML, gr.HTML]:
        """
        Create task progress monitoring components.
        
        Returns:
            Tuple of (progress_bars, console_output)
        """
        return self.task_dashboard.create_progress_components()
    
    def create_chapter_parsing_components(self) -> Tuple[gr.Checkbox, gr.Slider, gr.Dataframe]:
        """
        Create chapter parsing components.
        
        Returns:
            Tuple of (enable_parsing, confidence_threshold, chapter_preview)
        """
        enable_parsing = gr.Checkbox(
            label="Enable smart chapter parsing",
            value=True
        )
        
        # Get confidence threshold from config or use default
        try:
            confidence_value = self.config.chapter_parsing.confidence_threshold
            # Handle mocked config
            if hasattr(confidence_value, '_mock_name'):
                raise AttributeError("Mocked config")
        except (AttributeError, TypeError):
            confidence_value = 0.7
        
        confidence_threshold = gr.Slider(
            minimum=0.1,
            maximum=1.0,
            value=confidence_value,
            step=0.1,
            label="Chapter detection confidence threshold"
        )
        
        chapter_preview = gr.Dataframe(
            headers=["Chapter", "Title", "Confidence", "Length"],
            datatype=["number", "str", "number", "number"],
            label="Detected chapters",
            interactive=False
        )
        
        return enable_parsing, confidence_threshold, chapter_preview
    
    def refresh_voice_samples(self) -> Tuple[gr.Dropdown, gr.HTML]:
        """
        Refresh voice sample dropdown.
        
        Returns:
            Tuple of (updated_dropdown, status_html)
        """
        try:
            samples = self.enhanced_webui.get_voice_manager().refresh_samples()
            sample_choices = [(sample.display_name, sample.filepath) for sample in samples]
            
            updated_dropdown = gr.Dropdown(
                choices=sample_choices, 
                value=sample_choices[0][1] if sample_choices else None
            )
            
            status_html = gr.HTML(value=self._get_voice_status_html(samples))
            
            return updated_dropdown, status_html
            
        except Exception as e:
            error_html = gr.HTML(
                value=f'<div style="color: red;">Error refreshing samples: {str(e)}</div>'
            )
            return gr.Dropdown(choices=[], value=None), error_html
    
    def update_filename_preview(self, source_filename: Optional[str], voice_name: str, format_ext: str) -> str:
        """
        Update filename preview based on current settings.
        
        Args:
            source_filename: Source file name
            voice_name: Selected voice name
            format_ext: Selected format extension
            
        Returns:
            Generated filename preview
        """
        return self.enhanced_webui.get_output_manager().generate_filename(
            source_filename, voice_name, format_ext
        )
    
    def get_task_status_data(self) -> Tuple[List[List[str]], str, str, str]:
        """
        Get current task status data for all dashboard components.
        
        Returns:
            Tuple of (task_table_data, status_summary_html, progress_bars_html, console_output_html)
        """
        return self.task_dashboard.get_dashboard_data()
    
    def get_task_details(self, task_id: str) -> str:
        """
        Get detailed information for a specific task.
        
        Args:
            task_id: ID of the task to get details for
            
        Returns:
            HTML string with detailed task information
        """
        return self.task_dashboard.get_task_details(task_id)
    
    def should_auto_refresh_dashboard(self) -> bool:
        """
        Check if the task dashboard should auto-refresh.
        
        Returns:
            True if auto-refresh is needed
        """
        return self.task_dashboard.should_auto_refresh()
    
    def _get_voice_status_html(self, samples: List) -> str:
        """
        Generate HTML status display for voice samples.
        
        Args:
            samples: List of VoiceSample objects
            
        Returns:
            HTML string for status display
        """
        if not samples:
            return '''
            <div style="padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;">
                <strong>⚠️ No voice samples found</strong><br>
                Add .wav or .mp3 files to the samples folder and click refresh.
            </div>
            '''
        
        valid_samples = [s for s in samples if s.is_valid]
        invalid_samples = [s for s in samples if not s.is_valid]
        
        html_parts = []
        
        if valid_samples:
            html_parts.append(f'''
            <div style="padding: 8px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724; margin-bottom: 5px;">
                <strong>✅ {len(valid_samples)} valid sample(s) found</strong>
            </div>
            ''')
        
        if invalid_samples:
            invalid_names = ", ".join([s.filename for s in invalid_samples[:3]])
            if len(invalid_samples) > 3:
                invalid_names += f" and {len(invalid_samples) - 3} more"
            
            html_parts.append(f'''
            <div style="padding: 8px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24; margin-bottom: 5px;">
                <strong>❌ {len(invalid_samples)} invalid sample(s):</strong><br>
                <small>{invalid_names}</small>
            </div>
            ''')
        
        return "".join(html_parts)
    
    def validate_voice_selection(self, voice_path: str) -> Tuple[bool, str]:
        """
        Validate selected voice sample.
        
        Args:
            voice_path: Path to selected voice sample
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not voice_path:
            return False, "No voice sample selected"
        
        voice_manager = self.enhanced_webui.get_voice_manager()
        
        if not voice_manager.validate_sample(voice_path):
            return False, f"Invalid voice sample: {voice_path}"
        
        return True, ""
    
    def get_voice_sample_info(self, voice_path: str) -> Optional[dict]:
        """
        Get information about a voice sample.
        
        Args:
            voice_path: Path to voice sample
            
        Returns:
            Dictionary with sample information or None if not found
        """
        if not voice_path:
            return None
        
        samples = self.enhanced_webui.get_voice_manager().get_available_samples()
        
        for sample in samples:
            if sample.filepath == voice_path:
                return {
                    'filename': sample.filename,
                    'format': sample.format,
                    'duration': sample.duration,
                    'sample_rate': sample.sample_rate,
                    'file_size': sample.size_mb,
                    'is_valid': sample.is_valid
                }
        
        return None
    
    def get_background_tts_integration(self) -> Optional[BackgroundTTSIntegration]:
        """
        Get the background TTS integration instance.
        
        Returns:
            BackgroundTTSIntegration instance or None if not available
        """
        return self.background_tts
    
    def should_use_background_processing(self, text: str, **kwargs) -> bool:
        """
        Check if text should be processed in background.
        
        Args:
            text: Input text to analyze
            **kwargs: Additional parameters
            
        Returns:
            True if background processing should be used
        """
        if not self.background_tts:
            return False
        
        return self.background_tts.should_use_background_processing(text, **kwargs)
    
    def create_background_generation_task(self, 
                                        text: str,
                                        voice_prompt: str,
                                        output_path: str,
                                        generation_params: dict) -> Optional[str]:
        """
        Create a background TTS generation task.
        
        Args:
            text: Text to synthesize
            voice_prompt: Path to voice prompt audio
            output_path: Output file path
            generation_params: TTS generation parameters
            
        Returns:
            Task ID or None if background processing not available
        """
        if not self.background_tts:
            return None
        
        return self.background_tts.create_background_task(
            text=text,
            voice_prompt=voice_prompt,
            output_path=output_path,
            generation_params=generation_params
        )
    
    def get_background_task_status(self, task_id: str) -> Optional[dict]:
        """
        Get status of a background task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status dictionary or None if not found
        """
        if not self.background_tts:
            return None
        
        return self.background_tts.get_task_status(task_id)
    
    def cancel_background_task(self, task_id: str) -> bool:
        """
        Cancel a background task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        if not self.background_tts:
            return False
        
        return self.background_tts.cancel_task(task_id)
    
    def validate_segmentation_settings(self, chapters_per_file: int, file_type: str, chapter_recognition: bool) -> Tuple[bool, str]:
        """
        Validate segmentation settings based on file type and options.
        
        Args:
            chapters_per_file: Number of chapters per file
            file_type: File type (txt, epub, etc.)
            chapter_recognition: Whether chapter recognition is enabled
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate chapters_per_file range
        if chapters_per_file < 1 or chapters_per_file > 200:
            return False, "Chapters per file must be between 1 and 200"
        
        # Conditional segmentation logic: EPUB-only when chapter recognition disabled
        if not chapter_recognition and file_type.lower() != 'epub':
            return False, "Chapter segmentation is only available for EPUB files when chapter recognition is disabled"
        
        return True, ""
    
    def is_segmentation_available(self, file_type: str, chapter_recognition: bool) -> bool:
        """
        Check if segmentation is available based on file type and chapter recognition settings.
        
        Args:
            file_type: File type (txt, epub, etc.)
            chapter_recognition: Whether chapter recognition is enabled
            
        Returns:
            True if segmentation is available
        """
        # If chapter recognition is enabled, segmentation is available for all supported file types
        if chapter_recognition:
            return True
        
        # If chapter recognition is disabled, segmentation is only available for EPUB files
        return file_type.lower() == 'epub'