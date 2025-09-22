"""
UI theme manager for dark theme compatibility and enhanced user experience.
"""

import gradio as gr
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ThemeColors:
    """Color scheme for UI theming."""
    primary: str = "#2563eb"
    secondary: str = "#64748b"
    success: str = "#059669"
    warning: str = "#d97706"
    error: str = "#dc2626"
    info: str = "#0891b2"
    
    # Dark theme compatible colors
    text_primary: str = "#f8fafc"
    text_secondary: str = "#cbd5e1"
    text_muted: str = "#94a3b8"
    
    background_primary: str = "#0f172a"
    background_secondary: str = "#1e293b"
    background_tertiary: str = "#334155"
    
    border_color: str = "#475569"
    hover_color: str = "#3b82f6"


class UIThemeManager:
    """Manages UI theming and dark mode compatibility."""
    
    def __init__(self, theme_colors: Optional[ThemeColors] = None):
        """
        Initialize UI theme manager.
        
        Args:
            theme_colors: Custom theme colors, uses default if None
        """
        self.colors = theme_colors or ThemeColors()
        self._custom_css = self._generate_custom_css()
    
    def _generate_custom_css(self) -> str:
        """Generate custom CSS for dark theme compatibility."""
        return f"""
        /* Dark theme compatible styles */
        .gradio-container {{
            color: {self.colors.text_primary} !important;
        }}
        
        /* File upload area */
        .file-upload-area {{
            border: 2px dashed {self.colors.border_color} !important;
            background: {self.colors.background_secondary} !important;
            color: {self.colors.text_primary} !important;
            border-radius: 8px !important;
            padding: 20px !important;
            text-align: center !important;
        }}
        
        .file-upload-area:hover {{
            border-color: {self.colors.hover_color} !important;
            background: {self.colors.background_tertiary} !important;
        }}
        
        /* Preview text area */
        .preview-text {{
            background: {self.colors.background_secondary} !important;
            color: {self.colors.text_primary} !important;
            border: 1px solid {self.colors.border_color} !important;
            border-radius: 6px !important;
            padding: 12px !important;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
            font-size: 13px !important;
            line-height: 1.4 !important;
            max-height: 300px !important;
            overflow-y: auto !important;
        }}
        
        /* Chapter preview */
        .chapter-preview {{
            background: {self.colors.background_secondary} !important;
            color: {self.colors.text_primary} !important;
            border: 1px solid {self.colors.border_color} !important;
            border-radius: 6px !important;
            padding: 10px !important;
            margin: 8px 0 !important;
        }}
        
        .chapter-count {{
            color: {self.colors.success} !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }}
        
        .chapter-list {{
            max-height: 200px !important;
            overflow-y: auto !important;
        }}
        
        .chapter-item {{
            padding: 4px 8px !important;
            margin: 2px 0 !important;
            background: {self.colors.background_tertiary} !important;
            border-radius: 4px !important;
            color: {self.colors.text_secondary} !important;
            font-size: 14px !important;
        }}
        
        /* Status indicators */
        .status-success {{
            color: {self.colors.success} !important;
            font-weight: 500 !important;
        }}
        
        .status-warning {{
            color: {self.colors.warning} !important;
            font-weight: 500 !important;
        }}
        
        .status-error {{
            color: {self.colors.error} !important;
            font-weight: 500 !important;
        }}
        
        .status-info {{
            color: {self.colors.info} !important;
            font-weight: 500 !important;
        }}
        
        /* Loading indicators */
        .loading-spinner {{
            display: inline-block !important;
            width: 16px !important;
            height: 16px !important;
            border: 2px solid {self.colors.border_color} !important;
            border-radius: 50% !important;
            border-top-color: {self.colors.primary} !important;
            animation: spin 1s ease-in-out infinite !important;
            margin-right: 8px !important;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .loading-text {{
            color: {self.colors.text_secondary} !important;
            font-style: italic !important;
        }}
        
        /* Progress bars */
        .progress-container {{
            background: {self.colors.background_secondary} !important;
            border-radius: 4px !important;
            overflow: hidden !important;
            height: 8px !important;
            margin: 8px 0 !important;
        }}
        
        .progress-bar {{
            background: linear-gradient(90deg, {self.colors.primary}, {self.colors.hover_color}) !important;
            height: 100% !important;
            transition: width 0.3s ease !important;
        }}
        
        /* Tooltips */
        .tooltip {{
            position: relative !important;
            display: inline-block !important;
        }}
        
        .tooltip .tooltiptext {{
            visibility: hidden !important;
            width: 200px !important;
            background-color: {self.colors.background_primary} !important;
            color: {self.colors.text_primary} !important;
            text-align: center !important;
            border-radius: 6px !important;
            padding: 8px !important;
            position: absolute !important;
            z-index: 1000 !important;
            bottom: 125% !important;
            left: 50% !important;
            margin-left: -100px !important;
            border: 1px solid {self.colors.border_color} !important;
            font-size: 12px !important;
            line-height: 1.3 !important;
        }}
        
        .tooltip:hover .tooltiptext {{
            visibility: visible !important;
        }}
        
        /* Button enhancements */
        .btn-primary {{
            background: {self.colors.primary} !important;
            border-color: {self.colors.primary} !important;
            color: white !important;
        }}
        
        .btn-primary:hover {{
            background: {self.colors.hover_color} !important;
            border-color: {self.colors.hover_color} !important;
        }}
        
        .btn-secondary {{
            background: {self.colors.secondary} !important;
            border-color: {self.colors.secondary} !important;
            color: white !important;
        }}
        
        /* Form controls */
        .form-control {{
            background: {self.colors.background_secondary} !important;
            border: 1px solid {self.colors.border_color} !important;
            color: {self.colors.text_primary} !important;
        }}
        
        .form-control:focus {{
            border-color: {self.colors.primary} !important;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
        }}
        
        /* Checkbox and radio buttons */
        .checkbox-label, .radio-label {{
            color: {self.colors.text_primary} !important;
        }}
        
        /* Accordion styles */
        .accordion-header {{
            background: {self.colors.background_secondary} !important;
            color: {self.colors.text_primary} !important;
            border: 1px solid {self.colors.border_color} !important;
        }}
        
        .accordion-body {{
            background: {self.colors.background_tertiary} !important;
            color: {self.colors.text_primary} !important;
            border: 1px solid {self.colors.border_color} !important;
            border-top: none !important;
        }}
        
        /* Task status indicators */
        .task-queued {{
            color: {self.colors.warning} !important;
        }}
        
        .task-processing {{
            color: {self.colors.info} !important;
        }}
        
        .task-completed {{
            color: {self.colors.success} !important;
        }}
        
        .task-failed {{
            color: {self.colors.error} !important;
        }}
        
        /* Enhanced file preview styles */
        .file-preview-large {{
            min-height: 300px !important;
            max-height: 500px !important;
            overflow-y: auto !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 8px !important;
            padding: 0 !important;
            background: #f8f9fa !important;
            font-family: 'Segoe UI', Arial, sans-serif !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            color: #212529 !important;
        }}
        
        .file-preview-large pre {{
            background: white !important;
            color: #212529 !important;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
            font-size: 13px !important;
            line-height: 1.4 !important;
            margin: 0 !important;
            padding: 12px !important;
            border-radius: 6px !important;
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }}
        
        .chapter-preview {{
            min-height: 200px !important;
            max-height: 500px !important;
            overflow-y: auto !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 8px !important;
            padding: 0 !important;
            background: #f8f9fa !important;
            color: #212529 !important;
        }}
        
        .chapter-preview .chapter-item {{
            background: white !important;
            color: #212529 !important;
            border: 1px solid #e9ecef !important;
            margin: 8px !important;
            padding: 12px !important;
            border-radius: 6px !important;
        }}
        
        .chapter-preview .chapter-item:hover {{
            background: #f1f3f4 !important;
        }}
        
        .file-upload-area {{
            border: 2px dashed {self.colors.primary} !important;
            border-radius: 8px !important;
            padding: 20px !important;
            text-align: center !important;
            background: {self.colors.background_secondary} !important;
            transition: all 0.3s ease !important;
        }}
        
        .file-upload-area:hover {{
            border-color: {self.colors.hover_color} !important;
            background: {self.colors.background_tertiary} !important;
        }}
        
        /* Compact processing options */
        .processing-options {{
            background: {self.colors.background_secondary} !important;
            border: 1px solid {self.colors.border_color} !important;
            border-radius: 6px !important;
            padding: 12px !important;
            margin: 5px 0 !important;
        }}
        
        .processing-options h4 {{
            margin: 0 0 10px 0 !important;
            color: {self.colors.text_primary} !important;
            font-size: 14px !important;
            font-weight: bold !important;
        }}
        
        /* Chapter info styling */
        .chapter-info-header {{
            background: linear-gradient(135deg, {self.colors.success}, #20c997) !important;
            color: white !important;
            padding: 12px 15px !important;
            border-radius: 8px 8px 0 0 !important;
            margin: 0 !important;
            font-weight: bold !important;
        }}
        
        .chapter-list-container {{
            max-height: 350px !important;
            overflow-y: auto !important;
            border: 1px solid {self.colors.border_color} !important;
            border-radius: 0 0 8px 8px !important;
            background: {self.colors.background_secondary} !important;
        }}
        
        .chapter-item {{
            padding: 10px 15px !important;
            border-bottom: 1px solid {self.colors.border_color} !important;
            background: white !important;
            margin: 5px !important;
            border-radius: 4px !important;
            transition: background-color 0.2s ease !important;
        }}
        
        .chapter-item:hover {{
            background: {self.colors.background_tertiary} !important;
        }}
        
        .chapter-item:last-child {{
            border-bottom: none !important;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .gradio-container {{
                padding: 10px !important;
            }}
            
            .file-preview-large {{
                font-size: 12px !important;
                max-height: 300px !important;
                padding: 10px !important;
            }}
            
            .chapter-preview {{
                padding: 8px !important;
                max-height: 300px !important;
            }}
            
            .tooltip .tooltiptext {{
                width: 150px !important;
                margin-left: -75px !important;
                font-size: 11px !important;
            }}
            
            .processing-options {{
                padding: 8px !important;
            }}
        }}
        
        /* Auto-save configuration styles */
        .auto-save-info {{
            background: {self.colors.background_secondary} !important;
            border: 1px solid {self.colors.border_color} !important;
            border-radius: 6px !important;
            padding: 12px !important;
            margin: 8px 0 !important;
        }}
        
        .auto-save-info.enabled {{
            border-color: {self.colors.success} !important;
            background: rgba(5, 150, 105, 0.1) !important;
        }}
        
        .auto-save-info.disabled {{
            border-color: {self.colors.warning} !important;
            background: rgba(217, 119, 6, 0.1) !important;
        }}
        
        .auto-save-info.error {{
            border-color: {self.colors.error} !important;
            background: rgba(220, 38, 38, 0.1) !important;
        }}
        
        .auto-save-info small {{
            color: {self.colors.text_secondary} !important;
            line-height: 1.4 !important;
        }}
        
        /* Auto-save slider styling */
        .auto-save-slider {{
            margin: 8px 0 !important;
        }}
        
        .auto-save-slider .gr-slider {{
            background: {self.colors.background_secondary} !important;
        }}
        
        .auto-save-slider .gr-slider-track {{
            background: {self.colors.border_color} !important;
        }}
        
        .auto-save-slider .gr-slider-thumb {{
            background: {self.colors.primary} !important;
            border: 2px solid {self.colors.background_primary} !important;
        }}
        
        .auto-save-slider .gr-slider-thumb:hover {{
            background: {self.colors.hover_color} !important;
        }}
        """
    
    def get_custom_css(self) -> str:
        """Get custom CSS for the theme."""
        return self._custom_css
    
    def create_loading_indicator(self, text: str = "Loading...") -> str:
        """
        Create HTML for loading indicator.
        
        Args:
            text: Loading text to display
            
        Returns:
            HTML string for loading indicator
        """
        return f"""
        <div class="loading-container">
            <span class="loading-spinner"></span>
            <span class="loading-text">{text}</span>
        </div>
        """
    
    def create_progress_bar(self, progress: float, text: str = "") -> str:
        """
        Create HTML for progress bar.
        
        Args:
            progress: Progress value (0.0 to 1.0)
            text: Optional progress text
            
        Returns:
            HTML string for progress bar
        """
        progress_percent = min(100, max(0, progress * 100))
        
        return f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress_percent}%"></div>
        </div>
        {f'<div class="progress-text">{text}</div>' if text else ''}
        """
    
    def create_status_message(self, message: str, status_type: str = "info") -> str:
        """
        Create HTML for status message.
        
        Args:
            message: Status message text
            status_type: Type of status (success, warning, error, info)
            
        Returns:
            HTML string for status message
        """
        return f'<div class="status-{status_type}">{message}</div>'
    
    def create_tooltip(self, content: str, tooltip_text: str) -> str:
        """
        Create HTML for tooltip.
        
        Args:
            content: Content to show tooltip on
            tooltip_text: Tooltip text
            
        Returns:
            HTML string with tooltip
        """
        return f"""
        <div class="tooltip">
            {content}
            <span class="tooltiptext">{tooltip_text}</span>
        </div>
        """
    
    def create_file_preview_html(self, preview_text: str, filename: str, 
                                encoding: str, file_size: str, total_lines: int,
                                preview_truncated: bool) -> str:
        """
        Create HTML for file preview display.
        
        Args:
            preview_text: Preview text content
            filename: Name of the file
            encoding: File encoding
            file_size: File size string
            total_lines: Total number of lines
            preview_truncated: Whether preview was truncated
            
        Returns:
            HTML string for file preview
        """
        truncation_note = ""
        if preview_truncated:
            truncation_note = f'<div class="status-info">显示前40行，共{total_lines}行</div>'
        
        return f"""
        <div class="file-info">
            <strong>文件信息:</strong> {filename} | 编码: {encoding} | 大小: {file_size} | 行数: {total_lines}
        </div>
        {truncation_note}
        <div class="preview-text">{preview_text}</div>
        """
    
    def create_chapter_preview_html(self, chapters: List[str], chapter_count: int) -> str:
        """
        Create HTML for chapter preview display.
        
        Args:
            chapters: List of chapter titles
            chapter_count: Total number of chapters
            
        Returns:
            HTML string for chapter preview
        """
        if not chapters:
            return '<div class="status-info">未检测到章节</div>'
        
        chapter_items = ""
        for i, chapter in enumerate(chapters[:10]):  # Show first 10 chapters
            chapter_items += f'<div class="chapter-item">{i+1}. {chapter}</div>'
        
        if len(chapters) > 10:
            chapter_items += f'<div class="chapter-item status-info">... 还有 {len(chapters) - 10} 个章节</div>'
        
        return f"""
        <div class="chapter-preview">
            <div class="chapter-count">共识别到 {chapter_count} 个章节</div>
            <div class="chapter-list">
                {chapter_items}
            </div>
        </div>
        """
    
    def create_task_status_html(self, task_id: str, status: str, progress: float = 0.0,
                              current_stage: str = "", estimated_remaining: Optional[float] = None) -> str:
        """
        Create HTML for task status display.
        
        Args:
            task_id: Task identifier
            status: Task status (queued, processing, completed, failed)
            progress: Progress value (0.0 to 1.0)
            current_stage: Current processing stage
            estimated_remaining: Estimated remaining time in seconds
            
        Returns:
            HTML string for task status
        """
        status_icons = {
            'queued': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'failed': '❌'
        }
        
        icon = status_icons.get(status, '❓')
        
        progress_html = ""
        if status == 'processing' and progress > 0:
            progress_html = self.create_progress_bar(progress)
        
        time_html = ""
        if estimated_remaining and estimated_remaining > 0:
            if estimated_remaining < 60:
                time_str = f"{estimated_remaining:.0f}秒"
            else:
                minutes = int(estimated_remaining // 60)
                seconds = int(estimated_remaining % 60)
                time_str = f"{minutes}分{seconds}秒"
            time_html = f'<div class="status-info">预计剩余: {time_str}</div>'
        
        stage_html = ""
        if current_stage:
            stage_html = f'<div class="status-info">当前阶段: {current_stage}</div>'
        
        return f"""
        <div class="task-status task-{status}">
            <div class="task-header">
                {icon} 任务 {task_id[:8]}... - {status.value.upper()}
            </div>
            {stage_html}
            {progress_html}
            {time_html}
        </div>
        """
    
    def apply_theme_to_component(self, component: gr.Component, 
                                component_type: str = "default") -> gr.Component:
        """
        Apply theme styling to a Gradio component.
        
        Args:
            component: Gradio component to style
            component_type: Type of component for specific styling
            
        Returns:
            Styled component
        """
        # Add CSS classes based on component type
        css_classes = []
        
        if component_type == "file_upload":
            css_classes.append("file-upload-area")
        elif component_type == "preview":
            css_classes.append("preview-text")
        elif component_type == "button_primary":
            css_classes.append("btn-primary")
        elif component_type == "button_secondary":
            css_classes.append("btn-secondary")
        elif component_type == "form_control":
            css_classes.append("form-control")
        
        # Apply CSS classes if component supports it
        if hasattr(component, 'elem_classes') and css_classes:
            if component.elem_classes:
                component.elem_classes.extend(css_classes)
            else:
                component.elem_classes = css_classes
        
        return component
    
    def get_help_text_for_component(self, component_name: str) -> str:
        """
        Get help text for UI components.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Help text string
        """
        help_texts = {
            "file_cleaning": "清理文件中的多余空格、合并连续空行、移除不可见字符，提高语音合成质量",
            "chapter_recognition": "自动识别文本中的章节标题，支持中文和英文章节格式",
            "format_selection": "选择音频输出格式：WAV (无损)、MP3 (压缩)、M4B (有声书格式)",
            "segmentation": "将长文本按章节分割成多个音频文件，便于管理和播放",
            "auto_save": "自动保存生成的音频文件到 outputs 文件夹，使用标准化文件名",
            "voice_selection": "选择参考音色样本，支持 WAV 和 MP3 格式",
            "background_processing": "长文本自动使用后台处理，可以继续使用界面进行其他操作",
            "incremental_auto_save": "在音频生成过程中定期保存进度，防止生成失败时丢失已完成的音频"
        }
        
        return help_texts.get(component_name, "")


# Global theme manager instance
_global_theme_manager: Optional[UIThemeManager] = None


def get_theme_manager() -> UIThemeManager:
    """Get global theme manager instance."""
    global _global_theme_manager
    if _global_theme_manager is None:
        _global_theme_manager = UIThemeManager()
    return _global_theme_manager


def apply_dark_theme_css() -> str:
    """Get CSS for dark theme compatibility."""
    return get_theme_manager().get_custom_css()