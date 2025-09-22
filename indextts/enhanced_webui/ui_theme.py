"""
UI Theme Manager for Enhanced WebUI

This module provides dark theme compatible styling and consistent UI theming
for the IndexTTS2 enhanced web interface.
"""

import gradio as gr
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class ThemeColors:
    """Color scheme definitions for different themes."""
    
    # Text colors
    primary_text: str
    secondary_text: str
    success_text: str
    error_text: str
    warning_text: str
    
    # Background colors
    primary_bg: str
    secondary_bg: str
    success_bg: str
    error_bg: str
    warning_bg: str
    
    # Border colors
    primary_border: str
    success_border: str
    error_border: str
    warning_border: str
    
    # Interactive colors
    hover_bg: str
    active_bg: str


class UIThemeManager:
    """
    Manages UI theming and provides dark theme compatible components.
    
    This class provides consistent styling across the enhanced WebUI,
    with proper contrast ratios for text readability on dark backgrounds.
    """
    
    def __init__(self):
        """Initialize the theme manager with default color schemes."""
        self.dark_theme_colors = ThemeColors(
            # Text colors - high contrast for dark backgrounds
            primary_text="#ffffff",
            secondary_text="#b3b3b3",
            success_text="#4ade80",
            error_text="#f87171",
            warning_text="#fbbf24",
            
            # Background colors - dark theme compatible
            primary_bg="rgba(31, 41, 55, 0.8)",  # Dark gray with transparency
            secondary_bg="rgba(17, 24, 39, 0.9)",  # Darker gray
            success_bg="rgba(34, 197, 94, 0.1)",  # Green with low opacity
            error_bg="rgba(239, 68, 68, 0.1)",  # Red with low opacity
            warning_bg="rgba(251, 191, 36, 0.1)",  # Yellow with low opacity
            
            # Border colors
            primary_border="#4b5563",
            success_border="#22c55e",
            error_border="#ef4444",
            warning_border="#f59e0b",
            
            # Interactive colors
            hover_bg="rgba(55, 65, 81, 0.8)",
            active_bg="rgba(75, 85, 99, 0.8)"
        )
        
        self.light_theme_colors = ThemeColors(
            # Text colors - standard for light backgrounds
            primary_text="#1f2937",
            secondary_text="#6b7280",
            success_text="#059669",
            error_text="#dc2626",
            warning_text="#d97706",
            
            # Background colors - light theme
            primary_bg="#ffffff",
            secondary_bg="#f9fafb",
            success_bg="#d1fae5",
            error_bg="#fee2e2",
            warning_bg="#fef3c7",
            
            # Border colors
            primary_border="#d1d5db",
            success_border="#10b981",
            error_border="#ef4444",
            warning_border="#f59e0b",
            
            # Interactive colors
            hover_bg="#f3f4f6",
            active_bg="#e5e7eb"
        )
        
        # Default to dark theme for better compatibility
        self.current_theme = "dark"
        self.colors = self.dark_theme_colors
    
    def set_theme(self, theme: str) -> None:
        """
        Set the current theme.
        
        Args:
            theme: Either 'dark' or 'light'
        """
        if theme == "dark":
            self.colors = self.dark_theme_colors
        elif theme == "light":
            self.colors = self.light_theme_colors
        else:
            raise ValueError(f"Unknown theme: {theme}")
        
        self.current_theme = theme
    
    def get_status_style(self, status_type: str) -> Dict[str, str]:
        """
        Get CSS styles for status messages.
        
        Args:
            status_type: One of 'success', 'error', 'warning', 'info'
            
        Returns:
            Dictionary of CSS properties
        """
        base_style = {
            "padding": "12px",
            "border-radius": "6px",
            "margin": "8px 0",
            "font-weight": "500",
            "border-width": "1px",
            "border-style": "solid"
        }
        
        if status_type == "success":
            base_style.update({
                "color": self.colors.success_text,
                "background-color": self.colors.success_bg,
                "border-color": self.colors.success_border
            })
        elif status_type == "error":
            base_style.update({
                "color": self.colors.error_text,
                "background-color": self.colors.error_bg,
                "border-color": self.colors.error_border
            })
        elif status_type == "warning":
            base_style.update({
                "color": self.colors.warning_text,
                "background-color": self.colors.warning_bg,
                "border-color": self.colors.warning_border
            })
        else:  # info/default
            base_style.update({
                "color": self.colors.primary_text,
                "background-color": self.colors.primary_bg,
                "border-color": self.colors.primary_border
            })
        
        return base_style
    
    def get_preview_style(self) -> Dict[str, str]:
        """Get CSS styles for file preview components."""
        return {
            "background-color": self.colors.secondary_bg,
            "color": self.colors.primary_text,
            "padding": "16px",
            "border-radius": "8px",
            "border": f"1px solid {self.colors.primary_border}",
            "font-family": "monospace",
            "font-size": "14px",
            "line-height": "1.5",
            "max-height": "400px",
            "overflow-y": "auto",
            "white-space": "pre-wrap"
        }
    
    def get_chapter_preview_style(self) -> Dict[str, str]:
        """Get CSS styles for chapter preview components."""
        return {
            "background-color": self.colors.primary_bg,
            "color": self.colors.primary_text,
            "padding": "16px",
            "border-radius": "8px",
            "border": f"1px solid {self.colors.primary_border}",
            "margin": "8px 0"
        }
    
    def get_chapter_item_style(self) -> Dict[str, str]:
        """Get CSS styles for individual chapter items."""
        return {
            "padding": "8px 12px",
            "margin": "4px 0",
            "background-color": self.colors.secondary_bg,
            "border-left": f"3px solid {self.colors.primary_border}",
            "border-radius": "4px",
            "color": self.colors.primary_text
        }
    
    def get_toggle_style(self) -> Dict[str, str]:
        """Get CSS styles for toggle components."""
        return {
            "color": self.colors.primary_text,
            "background-color": self.colors.primary_bg,
            "border": f"1px solid {self.colors.primary_border}",
            "border-radius": "6px",
            "padding": "8px"
        }
    
    def style_to_css_string(self, style_dict: Dict[str, str]) -> str:
        """
        Convert a style dictionary to a CSS string.
        
        Args:
            style_dict: Dictionary of CSS properties
            
        Returns:
            CSS string suitable for inline styles
        """
        return "; ".join([f"{key}: {value}" for key, value in style_dict.items()])
    
    def create_status_html(self, message: str, status_type: str = "info", 
                          icon: str = "") -> str:
        """
        Create themed HTML for status messages.
        
        Args:
            message: The status message text
            status_type: Type of status ('success', 'error', 'warning', 'info')
            icon: Optional icon to display
            
        Returns:
            HTML string with proper theming
        """
        style = self.get_status_style(status_type)
        css_string = self.style_to_css_string(style)
        
        icon_html = f"<strong>{icon}</strong> " if icon else ""
        
        return f'<div style="{css_string}">{icon_html}{message}</div>'
    
    def create_preview_html(self, content: str, title: str = "") -> str:
        """
        Create themed HTML for file preview.
        
        Args:
            content: The preview content
            title: Optional title for the preview
            
        Returns:
            HTML string with proper theming
        """
        style = self.get_preview_style()
        css_string = self.style_to_css_string(style)
        
        title_html = f"<h4 style='margin: 0 0 12px 0; color: {self.colors.primary_text};'>{title}</h4>" if title else ""
        
        return f'<div style="{css_string}">{title_html}{content}</div>'
    
    def create_chapter_preview_html(self, chapters: list, total_count: int) -> str:
        """
        Create themed HTML for chapter preview.
        
        Args:
            chapters: List of chapter objects or strings
            total_count: Total number of chapters
            
        Returns:
            HTML string with proper theming
        """
        container_style = self.get_chapter_preview_style()
        item_style = self.get_chapter_item_style()
        
        container_css = self.style_to_css_string(container_style)
        item_css = self.style_to_css_string(item_style)
        
        # Header
        header_html = f"""
        <div style="margin-bottom: 12px;">
            <strong style="color: {self.colors.success_text};">📚 共识别到 {total_count} 个章节</strong>
        </div>
        """
        
        # Chapter list
        chapter_items = []
        display_chapters = chapters[:10]  # Show first 10 chapters
        
        for i, chapter in enumerate(display_chapters, 1):
            if hasattr(chapter, 'title') and not callable(getattr(chapter, 'title')):
                title = chapter.title
                confidence = getattr(chapter, 'confidence_score', 0.8)
                confidence_html = f"<small style='color: {self.colors.secondary_text};'>(置信度: {confidence:.2f})</small>"
            else:
                title = str(chapter)
                confidence_html = ""
            
            chapter_items.append(
                f'<div style="{item_css}"><strong>{i}.</strong> {title} {confidence_html}</div>'
            )
        
        if len(chapters) > 10:
            remaining = len(chapters) - 10
            chapter_items.append(
                f'<div style="padding: 8px 12px; color: {self.colors.secondary_text}; font-style: italic;">... 还有 {remaining} 个章节</div>'
            )
        
        chapters_html = f'<div style="max-height: 200px; overflow-y: auto;">{"".join(chapter_items)}</div>'
        
        return f'<div style="{container_css}">{header_html}{chapters_html}</div>'
    
    def apply_dark_theme_compatibility(self, component: gr.Component) -> gr.Component:
        """
        Apply dark theme compatible styling to Gradio components.
        
        Args:
            component: Gradio component to style
            
        Returns:
            Styled component
        """
        # Note: Gradio components have limited styling options
        # This method can be extended as Gradio adds more theming support
        
        if hasattr(component, 'elem_classes'):
            # Add dark theme CSS class if supported
            current_classes = getattr(component, 'elem_classes', []) or []
            if 'dark-theme-compatible' not in current_classes:
                current_classes.append('dark-theme-compatible')
                component.elem_classes = current_classes
        
        return component
    
    def get_readable_text_style(self, background_type: str = "dark") -> Dict[str, str]:
        """
        Get appropriate text styling for background type.
        
        Args:
            background_type: Either 'dark' or 'light'
            
        Returns:
            Dictionary of CSS properties for readable text
        """
        if background_type == "dark":
            return {
                "color": self.colors.primary_text,
                "text-shadow": "0 1px 2px rgba(0, 0, 0, 0.5)",
                "font-weight": "400"
            }
        else:
            return {
                "color": self.colors.primary_text,
                "text-shadow": "none",
                "font-weight": "400"
            }
    
    def create_themed_components(self) -> Dict[str, Any]:
        """
        Create pre-styled components for consistent theming.
        
        Returns:
            Dictionary of themed Gradio components
        """
        components = {}
        
        # Themed HTML component for status messages
        components['status_html'] = gr.HTML(
            value="",
            visible=False,
            elem_classes=['dark-theme-compatible']
        )
        
        # Themed HTML component for previews
        components['preview_html'] = gr.HTML(
            value="",
            visible=False,
            elem_classes=['dark-theme-compatible', 'preview-container']
        )
        
        # Themed HTML component for chapter preview
        components['chapter_preview_html'] = gr.HTML(
            value="",
            visible=False,
            elem_classes=['dark-theme-compatible', 'chapter-preview']
        )
        
        return components
    
    def get_custom_css(self) -> str:
        """
        Get custom CSS for dark theme compatibility.
        
        Returns:
            CSS string for injection into Gradio interface
        """
        return f"""
        /* Dark theme compatible styles */
        .dark-theme-compatible {{
            color: {self.colors.primary_text} !important;
        }}
        
        .dark-theme-compatible .gr-form {{
            background-color: {self.colors.primary_bg} !important;
            border-color: {self.colors.primary_border} !important;
        }}
        
        .dark-theme-compatible .gr-input {{
            background-color: {self.colors.secondary_bg} !important;
            color: {self.colors.primary_text} !important;
            border-color: {self.colors.primary_border} !important;
        }}
        
        .dark-theme-compatible .gr-button {{
            background-color: {self.colors.primary_bg} !important;
            color: {self.colors.primary_text} !important;
            border-color: {self.colors.primary_border} !important;
        }}
        
        .dark-theme-compatible .gr-button:hover {{
            background-color: {self.colors.hover_bg} !important;
        }}
        
        .preview-container {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
            line-height: 1.6 !important;
        }}
        
        .chapter-preview {{
            border-radius: 8px !important;
        }}
        
        /* Ensure text readability on all backgrounds */
        .gradio-container {{
            --text-color-primary: {self.colors.primary_text};
            --text-color-secondary: {self.colors.secondary_text};
            --bg-color-primary: {self.colors.primary_bg};
            --bg-color-secondary: {self.colors.secondary_bg};
        }}
        """


# Global theme manager instance
theme_manager = UIThemeManager()


def get_theme_manager() -> UIThemeManager:
    """Get the global theme manager instance."""
    return theme_manager


def create_status_message(message: str, status_type: str = "info", 
                         icon: str = "") -> str:
    """
    Convenience function to create themed status messages.
    
    Args:
        message: The status message text
        status_type: Type of status ('success', 'error', 'warning', 'info')
        icon: Optional icon to display
        
    Returns:
        HTML string with proper theming
    """
    return theme_manager.create_status_html(message, status_type, icon)


def create_file_preview(content: str, title: str = "") -> str:
    """
    Convenience function to create themed file previews.
    
    Args:
        content: The preview content
        title: Optional title for the preview
        
    Returns:
        HTML string with proper theming
    """
    return theme_manager.create_preview_html(content, title)


def create_chapter_preview(chapters: list, total_count: int) -> str:
    """
    Convenience function to create themed chapter previews.
    
    Args:
        chapters: List of chapter objects or strings
        total_count: Total number of chapters
        
    Returns:
        HTML string with proper theming
    """
    return theme_manager.create_chapter_preview_html(chapters, total_count)