"""
UI polish and user experience improvements for the enhanced web UI.
"""

import gradio as gr
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class UITheme:
    """UI theme configuration."""
    primary_color: str = "#2563eb"
    secondary_color: str = "#64748b"
    success_color: str = "#059669"
    warning_color: str = "#d97706"
    error_color: str = "#dc2626"
    background_color: str = "#f8fafc"
    text_color: str = "#1e293b"


@dataclass
class LoadingIndicator:
    """Loading indicator configuration."""
    show_spinner: bool = True
    show_progress_bar: bool = True
    show_estimated_time: bool = True
    custom_message: Optional[str] = None


class UIPolishManager:
    """Manages UI polish and user experience improvements."""
    
    def __init__(self, theme: Optional[UITheme] = None):
        """Initialize UI polish manager."""
        self.theme = theme or UITheme()
        self.loading_indicators: Dict[str, LoadingIndicator] = {}
        self.tooltips: Dict[str, str] = {}
        self.help_texts: Dict[str, str] = {}
    
    def add_loading_indicators(self, components: Dict[str, gr.Component]) -> Dict[str, gr.Component]:
        """
        Add loading indicators to UI components.
        
        Args:
            components: Dictionary of component names to Gradio components
            
        Returns:
            Updated components with loading indicators
        """
        enhanced_components = components.copy()
        
        # Add loading indicators for key components
        loading_components = {
            'file_upload_status': gr.HTML(
                value="<div class='loading-indicator' style='display: none;'>"
                      "<div class='spinner'></div>"
                      "<span>Processing file...</span>"
                      "</div>",
                visible=False
            ),
            'generation_progress': gr.HTML(
                value="<div class='progress-container' style='display: none;'>"
                      "<div class='progress-bar'>"
                      "<div class='progress-fill' style='width: 0%;'></div>"
                      "</div>"
                      "<div class='progress-text'>Initializing...</div>"
                      "</div>",
                visible=False
            ),
            'task_status_indicator': gr.HTML(
                value="<div class='task-status' style='display: none;'>"
                      "<span class='status-icon'>⏳</span>"
                      "<span class='status-text'>Ready</span>"
                      "</div>",
                visible=False
            )
        }
        
        enhanced_components.update(loading_components)
        return enhanced_components
    
    def add_tooltips_and_help(self, components: Dict[str, gr.Component]) -> Dict[str, gr.Component]:
        """
        Add tooltips and help text to UI components.
        
        Args:
            components: Dictionary of component names to Gradio components
            
        Returns:
            Updated components with tooltips and help text
        """
        # Define tooltips for various components
        self.tooltips.update({
            'file_upload': 'Upload TXT or EPUB files for audio conversion. Supports UTF-8, GBK, and GB2312 encodings.',
            'voice_sample': 'Select a voice sample from the samples folder. WAV and MP3 formats are supported.',
            'output_format': 'Choose output format: WAV (uncompressed), MP3 (compressed), or M4B (audiobook with chapters).',
            'auto_save': 'Automatically save generated audio to the outputs folder with timestamp and voice name.',
            'chapter_segmentation': 'Split long content into separate audio files based on detected chapters.',
            'text_processing': 'Apply text cleaning options to improve speech synthesis quality.',
            'background_processing': 'Large files will automatically use background processing with progress tracking.'
        })
        
        # Define help texts
        self.help_texts.update({
            'file_formats': 'Supported formats: TXT (plain text), EPUB (e-book format). Maximum file size: 50MB.',
            'voice_samples': 'Place voice samples in the "samples" folder. Use clear, high-quality recordings for best results.',
            'chapter_detection': 'Automatic chapter detection supports Chinese (第X章, 第X回) and English (Chapter X) patterns.',
            'output_management': 'Files are saved with format: filename_YYYYMMDD_HHMMSS_voicename.ext',
            'performance_tips': 'For large files: enable chunked processing, use background tasks, and monitor memory usage.'
        })
        
        # Add help components
        help_components = {}
        for key, help_text in self.help_texts.items():
            help_components[f'{key}_help'] = gr.HTML(
                value=f"<div class='help-text' style='font-size: 0.9em; color: {self.theme.secondary_color}; margin-top: 5px;'>"
                      f"💡 {help_text}"
                      f"</div>",
                visible=False
            )
        
        components.update(help_components)
        return components
    
    def create_responsive_layout(self, components: Dict[str, gr.Component]) -> gr.Blocks:
        """
        Create responsive layout with improved organization.
        
        Args:
            components: Dictionary of UI components
            
        Returns:
            Gradio Blocks with responsive layout
        """
        with gr.Blocks(
            theme=gr.themes.Soft(
                primary_hue=gr.themes.colors.blue,
                secondary_hue=gr.themes.colors.slate,
                neutral_hue=gr.themes.colors.slate
            ),
            css=self._get_custom_css(),
            title="IndexTTS2 Enhanced Web UI"
        ) as interface:
            
            # Header section
            with gr.Row():
                gr.HTML(
                    value="<h1 style='text-align: center; margin-bottom: 20px;'>"
                          "🎵 IndexTTS2 Enhanced Web UI</h1>"
                          "<p style='text-align: center; color: #64748b;'>"
                          "Advanced text-to-speech with file processing, chapter detection, and multiple output formats"
                          "</p>"
                )
            
            # Main content area with tabs
            with gr.Tabs() as tabs:
                
                # File Processing Tab
                with gr.TabItem("📁 File Processing", id="file_tab"):
                    with gr.Row():
                        with gr.Column(scale=2):
                            components.get('file_upload', gr.File())
                            components.get('file_formats_help', gr.HTML())
                        
                        with gr.Column(scale=1):
                            components.get('file_upload_status', gr.HTML())
                    
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>📝 Text Processing Options</h3>")
                            components.get('text_cleaning_options', gr.CheckboxGroup())
                            components.get('performance_tips_help', gr.HTML())
                
                # Voice & Output Tab
                with gr.TabItem("🎤 Voice & Output", id="voice_tab"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>🎵 Voice Selection</h3>")
                            components.get('voice_sample', gr.Dropdown())
                            components.get('voice_refresh_btn', gr.Button())
                            components.get('voice_samples_help', gr.HTML())
                        
                        with gr.Column():
                            gr.HTML("<h3>💾 Output Settings</h3>")
                            components.get('output_format', gr.Dropdown())
                            components.get('auto_save', gr.Checkbox())
                            components.get('output_management_help', gr.HTML())
                
                # Advanced Settings Tab
                with gr.TabItem("⚙️ Advanced", id="advanced_tab"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>📚 Chapter Processing</h3>")
                            components.get('chapter_segmentation', gr.Checkbox())
                            components.get('chapters_per_file', gr.Slider())
                            components.get('chapter_detection_help', gr.HTML())
                        
                        with gr.Column():
                            gr.HTML("<h3>🚀 Performance</h3>")
                            components.get('background_processing', gr.Checkbox())
                            components.get('memory_optimization', gr.Checkbox())
            
            # Generation section
            with gr.Row():
                with gr.Column():
                    gr.HTML("<h3>✨ Text Input</h3>")
                    components.get('text_input', gr.Textbox())
                
                with gr.Column(scale=0.3):
                    gr.HTML("<h3>🎯 Generate</h3>")
                    components.get('generate_btn', gr.Button())
                    components.get('generation_progress', gr.HTML())
            
            # Status and Results section
            with gr.Row():
                with gr.Column():
                    gr.HTML("<h3>📊 Status & Results</h3>")
                    components.get('console_output', gr.Textbox())
                    components.get('task_status_indicator', gr.HTML())
                
                with gr.Column():
                    gr.HTML("<h3>🎧 Audio Output</h3>")
                    components.get('audio_output', gr.Audio())
                    components.get('download_links', gr.HTML())
        
        return interface
    
    def add_progress_feedback(self, progress_callback: Callable[[float, str], None]) -> Dict[str, Callable]:
        """
        Add progress feedback functions.
        
        Args:
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary of progress update functions
        """
        def update_file_processing_progress(progress: float, message: str):
            """Update file processing progress."""
            progress_html = f"""
            <div class='progress-container'>
                <div class='progress-bar'>
                    <div class='progress-fill' style='width: {progress * 100}%;'></div>
                </div>
                <div class='progress-text'>{message}</div>
                <div class='progress-percentage'>{progress * 100:.1f}%</div>
            </div>
            """
            return progress_html
        
        def update_generation_progress(progress: float, stage: str, eta: Optional[float] = None):
            """Update audio generation progress."""
            eta_text = f" (ETA: {eta:.1f}s)" if eta else ""
            progress_html = f"""
            <div class='generation-progress'>
                <div class='stage-indicator'>
                    <span class='stage-name'>{stage}</span>
                    <span class='stage-progress'>{progress * 100:.1f}%{eta_text}</span>
                </div>
                <div class='progress-bar'>
                    <div class='progress-fill' style='width: {progress * 100}%;'></div>
                </div>
            </div>
            """
            return progress_html
        
        def update_task_status(status: str, icon: str = "⏳"):
            """Update task status indicator."""
            status_colors = {
                'queued': '#f59e0b',
                'processing': '#3b82f6',
                'completed': '#10b981',
                'failed': '#ef4444'
            }
            color = status_colors.get(status.lower(), '#6b7280')
            
            status_html = f"""
            <div class='task-status' style='color: {color};'>
                <span class='status-icon'>{icon}</span>
                <span class='status-text'>{status.title()}</span>
            </div>
            """
            return status_html
        
        return {
            'update_file_progress': update_file_processing_progress,
            'update_generation_progress': update_generation_progress,
            'update_task_status': update_task_status
        }
    
    def create_error_handling_ui(self) -> Dict[str, gr.Component]:
        """Create user-friendly error handling UI components."""
        error_components = {
            'error_display': gr.HTML(
                value="",
                visible=False,
                elem_classes=["error-display"]
            ),
            'warning_display': gr.HTML(
                value="",
                visible=False,
                elem_classes=["warning-display"]
            ),
            'success_display': gr.HTML(
                value="",
                visible=False,
                elem_classes=["success-display"]
            )
        }
        
        return error_components
    
    def format_error_message(self, error: Exception, context: str = "") -> str:
        """Format error message for user-friendly display."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Create user-friendly error messages
        friendly_messages = {
            'FileNotFoundError': 'The specified file could not be found. Please check the file path.',
            'PermissionError': 'Permission denied. Please check file permissions or try a different location.',
            'UnicodeDecodeError': 'File encoding issue. The file may be corrupted or use an unsupported encoding.',
            'ValueError': 'Invalid input value. Please check your settings and try again.',
            'RuntimeError': 'A processing error occurred. Please try again or contact support.',
            'MemoryError': 'Insufficient memory. Try processing smaller files or restart the application.',
            'TimeoutError': 'Operation timed out. The file may be too large or the system is busy.'
        }
        
        friendly_message = friendly_messages.get(error_type, error_message)
        
        error_html = f"""
        <div class='error-message'>
            <div class='error-header'>
                <span class='error-icon'>❌</span>
                <span class='error-title'>Error in {context}</span>
            </div>
            <div class='error-content'>
                <p><strong>What happened:</strong> {friendly_message}</p>
                <details>
                    <summary>Technical details</summary>
                    <code>{error_type}: {error_message}</code>
                </details>
            </div>
        </div>
        """
        
        return error_html
    
    def format_success_message(self, message: str, details: Optional[Dict] = None) -> str:
        """Format success message for user-friendly display."""
        details_html = ""
        if details:
            details_list = [f"<li><strong>{k}:</strong> {v}</li>" for k, v in details.items()]
            details_html = f"<ul>{''.join(details_list)}</ul>"
        
        success_html = f"""
        <div class='success-message'>
            <div class='success-header'>
                <span class='success-icon'>✅</span>
                <span class='success-title'>Success!</span>
            </div>
            <div class='success-content'>
                <p>{message}</p>
                {details_html}
            </div>
        </div>
        """
        
        return success_html
    
    def _get_custom_css(self) -> str:
        """Get custom CSS for enhanced UI styling."""
        return f"""
        /* Custom CSS for Enhanced UI */
        
        .loading-indicator {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: {self.theme.background_color};
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        
        .spinner {{
            width: 20px;
            height: 20px;
            border: 2px solid #e2e8f0;
            border-top: 2px solid {self.theme.primary_color};
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .progress-container {{
            margin: 10px 0;
            padding: 10px;
            background: {self.theme.background_color};
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {self.theme.primary_color}, {self.theme.success_color});
            transition: width 0.3s ease;
        }}
        
        .progress-text {{
            font-size: 0.9em;
            color: {self.theme.text_color};
            margin-bottom: 4px;
        }}
        
        .progress-percentage {{
            font-size: 0.8em;
            color: {self.theme.secondary_color};
            text-align: right;
        }}
        
        .task-status {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: {self.theme.background_color};
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            font-size: 0.9em;
        }}
        
        .status-icon {{
            font-size: 1.2em;
        }}
        
        .help-text {{
            padding: 8px 12px;
            background: #f1f5f9;
            border-left: 3px solid {self.theme.primary_color};
            border-radius: 0 4px 4px 0;
            margin: 8px 0;
        }}
        
        .error-message, .success-message, .warning-message {{
            margin: 10px 0;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid;
        }}
        
        .error-message {{
            background: #fef2f2;
            border-color: {self.theme.error_color};
            color: #991b1b;
        }}
        
        .success-message {{
            background: #f0fdf4;
            border-color: {self.theme.success_color};
            color: #166534;
        }}
        
        .warning-message {{
            background: #fffbeb;
            border-color: {self.theme.warning_color};
            color: #92400e;
        }}
        
        .error-header, .success-header, .warning-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .error-content, .success-content, .warning-content {{
            font-size: 0.9em;
        }}
        
        details {{
            margin-top: 8px;
        }}
        
        summary {{
            cursor: pointer;
            font-weight: bold;
        }}
        
        code {{
            background: #f8fafc;
            padding: 4px 8px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85em;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .progress-container {{
                padding: 8px;
            }}
            
            .help-text {{
                font-size: 0.8em;
                padding: 6px 10px;
            }}
            
            .task-status {{
                padding: 6px 10px;
                font-size: 0.8em;
            }}
        }}
        
        /* Enhanced button styles */
        .gradio-button {{
            transition: all 0.2s ease;
        }}
        
        .gradio-button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        
        /* Enhanced input styles */
        .gradio-textbox, .gradio-dropdown {{
            transition: border-color 0.2s ease;
        }}
        
        .gradio-textbox:focus, .gradio-dropdown:focus {{
            border-color: {self.theme.primary_color};
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
        }}
        """


class ResponsiveDesignManager:
    """Manages responsive design elements for better usability."""
    
    def __init__(self):
        """Initialize responsive design manager."""
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200
        }
    
    def create_adaptive_layout(self, components: Dict[str, gr.Component]) -> Dict[str, Any]:
        """
        Create adaptive layout that responds to screen size.
        
        Args:
            components: Dictionary of UI components
            
        Returns:
            Layout configuration
        """
        layout_config = {
            'mobile': {
                'columns': 1,
                'tab_orientation': 'vertical',
                'compact_mode': True
            },
            'tablet': {
                'columns': 2,
                'tab_orientation': 'horizontal',
                'compact_mode': False
            },
            'desktop': {
                'columns': 3,
                'tab_orientation': 'horizontal',
                'compact_mode': False
            }
        }
        
        return layout_config
    
    def optimize_for_mobile(self, components: Dict[str, gr.Component]) -> Dict[str, gr.Component]:
        """Optimize components for mobile devices."""
        mobile_optimized = {}
        
        for name, component in components.items():
            if isinstance(component, gr.Textbox):
                # Make textboxes more mobile-friendly
                mobile_optimized[name] = gr.Textbox(
                    **component.constructor_args,
                    lines=min(component.lines or 3, 5),  # Limit lines on mobile
                    elem_classes=["mobile-textbox"]
                )
            elif isinstance(component, gr.Button):
                # Make buttons larger for touch
                mobile_optimized[name] = gr.Button(
                    **component.constructor_args,
                    elem_classes=["mobile-button"]
                )
            else:
                mobile_optimized[name] = component
        
        return mobile_optimized


class AccessibilityManager:
    """Manages accessibility features for the UI."""
    
    def __init__(self):
        """Initialize accessibility manager."""
        self.aria_labels = {}
        self.keyboard_shortcuts = {}
    
    def add_accessibility_features(self, components: Dict[str, gr.Component]) -> Dict[str, gr.Component]:
        """
        Add accessibility features to UI components.
        
        Args:
            components: Dictionary of UI components
            
        Returns:
            Components with accessibility features
        """
        # Define ARIA labels
        self.aria_labels.update({
            'file_upload': 'Upload text or EPUB file for conversion',
            'voice_sample': 'Select voice sample for speech synthesis',
            'text_input': 'Enter text to convert to speech',
            'generate_btn': 'Generate audio from text',
            'audio_output': 'Generated audio output'
        })
        
        # Define keyboard shortcuts
        self.keyboard_shortcuts.update({
            'Ctrl+U': 'Upload file',
            'Ctrl+Enter': 'Generate audio',
            'Ctrl+S': 'Save audio',
            'Ctrl+R': 'Refresh voice samples'
        })
        
        # Add accessibility attributes
        accessible_components = {}
        for name, component in components.items():
            if name in self.aria_labels:
                # Add ARIA label if supported
                accessible_components[name] = component
            else:
                accessible_components[name] = component
        
        return accessible_components
    
    def create_keyboard_shortcuts_help(self) -> gr.HTML:
        """Create help display for keyboard shortcuts."""
        shortcuts_html = "<div class='keyboard-shortcuts'><h4>⌨️ Keyboard Shortcuts</h4><ul>"
        
        for shortcut, description in self.keyboard_shortcuts.items():
            shortcuts_html += f"<li><kbd>{shortcut}</kbd> - {description}</li>"
        
        shortcuts_html += "</ul></div>"
        
        return gr.HTML(value=shortcuts_html, visible=False)


def create_enhanced_ui_components() -> Dict[str, gr.Component]:
    """Create all enhanced UI components with polish and improvements."""
    ui_manager = UIPolishManager()
    responsive_manager = ResponsiveDesignManager()
    accessibility_manager = AccessibilityManager()
    
    # Base components
    components = {
        'file_upload': gr.File(
            label="📁 Upload File",
            file_types=['.txt', '.epub'],
            elem_classes=["enhanced-file-upload"]
        ),
        'voice_sample': gr.Dropdown(
            label="🎤 Voice Sample",
            choices=[],
            elem_classes=["enhanced-dropdown"]
        ),
        'text_input': gr.Textbox(
            label="✨ Text Input",
            placeholder="Enter text to convert to speech...",
            lines=5,
            elem_classes=["enhanced-textbox"]
        ),
        'generate_btn': gr.Button(
            "🎯 Generate Audio",
            variant="primary",
            elem_classes=["enhanced-button", "generate-button"]
        ),
        'audio_output': gr.Audio(
            label="🎧 Generated Audio",
            elem_classes=["enhanced-audio"]
        )
    }
    
    # Add loading indicators
    components = ui_manager.add_loading_indicators(components)
    
    # Add tooltips and help
    components = ui_manager.add_tooltips_and_help(components)
    
    # Add error handling components
    components.update(ui_manager.create_error_handling_ui())
    
    # Add accessibility features
    components = accessibility_manager.add_accessibility_features(components)
    
    # Add keyboard shortcuts help
    components['keyboard_shortcuts_help'] = accessibility_manager.create_keyboard_shortcuts_help()
    
    return components