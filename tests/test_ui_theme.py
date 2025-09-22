"""
Unit tests for UI Theme Manager

Tests theme compatibility, readability, and component creation functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from indextts.enhanced_webui.ui_theme import (
    UIThemeManager, 
    ThemeColors,
    get_theme_manager,
    create_status_message,
    create_file_preview,
    create_chapter_preview
)


class TestThemeColors(unittest.TestCase):
    """Test ThemeColors dataclass."""
    
    def test_theme_colors_creation(self):
        """Test creating ThemeColors with all required fields."""
        colors = ThemeColors(
            primary_text="#ffffff",
            secondary_text="#b3b3b3",
            success_text="#4ade80",
            error_text="#f87171",
            warning_text="#fbbf24",
            primary_bg="rgba(31, 41, 55, 0.8)",
            secondary_bg="rgba(17, 24, 39, 0.9)",
            success_bg="rgba(34, 197, 94, 0.1)",
            error_bg="rgba(239, 68, 68, 0.1)",
            warning_bg="rgba(251, 191, 36, 0.1)",
            primary_border="#4b5563",
            success_border="#22c55e",
            error_border="#ef4444",
            warning_border="#f59e0b",
            hover_bg="rgba(55, 65, 81, 0.8)",
            active_bg="rgba(75, 85, 99, 0.8)"
        )
        
        self.assertEqual(colors.primary_text, "#ffffff")
        self.assertEqual(colors.success_text, "#4ade80")
        self.assertEqual(colors.primary_bg, "rgba(31, 41, 55, 0.8)")


class TestUIThemeManager(unittest.TestCase):
    """Test UIThemeManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.theme_manager = UIThemeManager()
    
    def test_initialization(self):
        """Test theme manager initialization."""
        self.assertEqual(self.theme_manager.current_theme, "dark")
        self.assertIsNotNone(self.theme_manager.colors)
        self.assertIsNotNone(self.theme_manager.dark_theme_colors)
        self.assertIsNotNone(self.theme_manager.light_theme_colors)
    
    def test_set_theme_dark(self):
        """Test setting dark theme."""
        self.theme_manager.set_theme("dark")
        self.assertEqual(self.theme_manager.current_theme, "dark")
        self.assertEqual(self.theme_manager.colors, self.theme_manager.dark_theme_colors)
    
    def test_set_theme_light(self):
        """Test setting light theme."""
        self.theme_manager.set_theme("light")
        self.assertEqual(self.theme_manager.current_theme, "light")
        self.assertEqual(self.theme_manager.colors, self.theme_manager.light_theme_colors)
    
    def test_set_theme_invalid(self):
        """Test setting invalid theme raises error."""
        with self.assertRaises(ValueError):
            self.theme_manager.set_theme("invalid")
    
    def test_get_status_style_success(self):
        """Test getting success status style."""
        style = self.theme_manager.get_status_style("success")
        
        self.assertIn("color", style)
        self.assertIn("background-color", style)
        self.assertIn("border-color", style)
        self.assertEqual(style["color"], self.theme_manager.colors.success_text)
        self.assertEqual(style["background-color"], self.theme_manager.colors.success_bg)
        self.assertEqual(style["border-color"], self.theme_manager.colors.success_border)
    
    def test_get_status_style_error(self):
        """Test getting error status style."""
        style = self.theme_manager.get_status_style("error")
        
        self.assertEqual(style["color"], self.theme_manager.colors.error_text)
        self.assertEqual(style["background-color"], self.theme_manager.colors.error_bg)
        self.assertEqual(style["border-color"], self.theme_manager.colors.error_border)
    
    def test_get_status_style_warning(self):
        """Test getting warning status style."""
        style = self.theme_manager.get_status_style("warning")
        
        self.assertEqual(style["color"], self.theme_manager.colors.warning_text)
        self.assertEqual(style["background-color"], self.theme_manager.colors.warning_bg)
        self.assertEqual(style["border-color"], self.theme_manager.colors.warning_border)
    
    def test_get_status_style_info(self):
        """Test getting info/default status style."""
        style = self.theme_manager.get_status_style("info")
        
        self.assertEqual(style["color"], self.theme_manager.colors.primary_text)
        self.assertEqual(style["background-color"], self.theme_manager.colors.primary_bg)
        self.assertEqual(style["border-color"], self.theme_manager.colors.primary_border)
    
    def test_get_preview_style(self):
        """Test getting preview component style."""
        style = self.theme_manager.get_preview_style()
        
        self.assertIn("background-color", style)
        self.assertIn("color", style)
        self.assertIn("font-family", style)
        self.assertEqual(style["font-family"], "monospace")
        self.assertEqual(style["color"], self.theme_manager.colors.primary_text)
    
    def test_get_chapter_preview_style(self):
        """Test getting chapter preview style."""
        style = self.theme_manager.get_chapter_preview_style()
        
        self.assertIn("background-color", style)
        self.assertIn("color", style)
        self.assertIn("padding", style)
        self.assertEqual(style["color"], self.theme_manager.colors.primary_text)
    
    def test_style_to_css_string(self):
        """Test converting style dictionary to CSS string."""
        style_dict = {
            "color": "#ffffff",
            "background-color": "#000000",
            "padding": "10px"
        }
        
        css_string = self.theme_manager.style_to_css_string(style_dict)
        
        self.assertIn("color: #ffffff", css_string)
        self.assertIn("background-color: #000000", css_string)
        self.assertIn("padding: 10px", css_string)
        self.assertEqual(css_string.count(";"), 2)  # Two semicolons for three properties
    
    def test_create_status_html(self):
        """Test creating themed status HTML."""
        html = self.theme_manager.create_status_html("Test message", "success", "✅")
        
        self.assertIn("Test message", html)
        self.assertIn("✅", html)
        self.assertIn("<div", html)
        self.assertIn("style=", html)
        self.assertIn(self.theme_manager.colors.success_text, html)
    
    def test_create_status_html_no_icon(self):
        """Test creating status HTML without icon."""
        html = self.theme_manager.create_status_html("Test message", "error")
        
        self.assertIn("Test message", html)
        self.assertNotIn("<strong>", html)  # No icon means no strong tag
        self.assertIn(self.theme_manager.colors.error_text, html)
    
    def test_create_preview_html(self):
        """Test creating themed preview HTML."""
        content = "Sample file content\nLine 2\nLine 3"
        html = self.theme_manager.create_preview_html(content, "File Preview")
        
        self.assertIn(content, html)
        self.assertIn("File Preview", html)
        self.assertIn("<h4", html)
        self.assertIn("monospace", html)
    
    def test_create_preview_html_no_title(self):
        """Test creating preview HTML without title."""
        content = "Sample content"
        html = self.theme_manager.create_preview_html(content)
        
        self.assertIn(content, html)
        self.assertNotIn("<h4", html)  # No title means no h4 tag
    
    def test_create_chapter_preview_html(self):
        """Test creating themed chapter preview HTML."""
        # Mock chapter objects
        class MockChapter:
            def __init__(self, title, confidence=0.8):
                self.title = title
                self.confidence_score = confidence
        
        chapters = [
            MockChapter("第一章 开始", 0.9),
            MockChapter("第二章 发展", 0.8),
            MockChapter("第三章 结束", 0.7)
        ]
        
        html = self.theme_manager.create_chapter_preview_html(chapters, 3)
        
        self.assertIn("共识别到 3 个章节", html)
        self.assertIn("第一章 开始", html)
        self.assertIn("第二章 发展", html)
        self.assertIn("第三章 结束", html)
        self.assertIn("置信度: 0.9", html)
        self.assertIn("📚", html)
    
    def test_create_chapter_preview_html_many_chapters(self):
        """Test chapter preview with more than 10 chapters."""
        chapters = [f"Chapter {i}" for i in range(1, 16)]  # 15 chapters
        
        html = self.theme_manager.create_chapter_preview_html(chapters, 15)
        
        self.assertIn("共识别到 15 个章节", html)
        self.assertIn("Chapter 1", html)
        self.assertIn("Chapter 10", html)
        self.assertNotIn("Chapter 11", html)  # Should be truncated
        self.assertIn("还有 5 个章节", html)  # Should show remaining count
    
    def test_get_readable_text_style_dark(self):
        """Test getting readable text style for dark background."""
        style = self.theme_manager.get_readable_text_style("dark")
        
        self.assertIn("color", style)
        self.assertIn("text-shadow", style)
        self.assertEqual(style["color"], self.theme_manager.colors.primary_text)
        self.assertIn("rgba(0, 0, 0, 0.5)", style["text-shadow"])
    
    def test_get_readable_text_style_light(self):
        """Test getting readable text style for light background."""
        style = self.theme_manager.get_readable_text_style("light")
        
        self.assertIn("color", style)
        self.assertIn("text-shadow", style)
        self.assertEqual(style["text-shadow"], "none")
    
    @patch('indextts.enhanced_webui.ui_theme.gr')
    def test_create_themed_components(self, mock_gr):
        """Test creating themed components."""
        # Mock Gradio HTML component
        mock_html = Mock()
        mock_gr.HTML.return_value = mock_html
        
        components = self.theme_manager.create_themed_components()
        
        self.assertIn('status_html', components)
        self.assertIn('preview_html', components)
        self.assertIn('chapter_preview_html', components)
        
        # Verify HTML components were created with proper classes
        self.assertEqual(mock_gr.HTML.call_count, 3)
    
    def test_get_custom_css(self):
        """Test getting custom CSS for dark theme compatibility."""
        css = self.theme_manager.get_custom_css()
        
        self.assertIn(".dark-theme-compatible", css)
        self.assertIn(".gr-form", css)
        self.assertIn(".gr-input", css)
        self.assertIn(".gr-button", css)
        self.assertIn(self.theme_manager.colors.primary_text, css)
        self.assertIn("--text-color-primary", css)
    
    def test_contrast_ratios_dark_theme(self):
        """Test that dark theme colors provide sufficient contrast."""
        # This is a basic test - in a real implementation, you'd calculate
        # actual contrast ratios using WCAG guidelines
        
        # Primary text should be light on dark background
        self.assertTrue(self.theme_manager.dark_theme_colors.primary_text.startswith("#f") or 
                       self.theme_manager.dark_theme_colors.primary_text.startswith("#e"))
        
        # Success text should be distinguishable
        self.assertNotEqual(self.theme_manager.dark_theme_colors.success_text,
                           self.theme_manager.dark_theme_colors.primary_text)
        
        # Error text should be distinguishable
        self.assertNotEqual(self.theme_manager.dark_theme_colors.error_text,
                           self.theme_manager.dark_theme_colors.primary_text)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_get_theme_manager(self):
        """Test getting global theme manager instance."""
        manager = get_theme_manager()
        self.assertIsInstance(manager, UIThemeManager)
    
    def test_create_status_message(self):
        """Test convenience function for status messages."""
        html = create_status_message("Test", "success", "✅")
        self.assertIn("Test", html)
        self.assertIn("✅", html)
    
    def test_create_file_preview(self):
        """Test convenience function for file previews."""
        html = create_file_preview("Content", "Title")
        self.assertIn("Content", html)
        self.assertIn("Title", html)
    
    def test_create_chapter_preview(self):
        """Test convenience function for chapter previews."""
        chapters = ["Chapter 1", "Chapter 2"]
        html = create_chapter_preview(chapters, 2)
        self.assertIn("Chapter 1", html)
        self.assertIn("共识别到 2 个章节", html)


class TestThemeCompatibility(unittest.TestCase):
    """Test theme compatibility and readability."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.theme_manager = UIThemeManager()
    
    def test_dark_theme_readability(self):
        """Test that dark theme provides readable text."""
        self.theme_manager.set_theme("dark")
        
        # Test status messages are readable
        for status_type in ["success", "error", "warning", "info"]:
            style = self.theme_manager.get_status_style(status_type)
            
            # Color should be defined and not empty
            self.assertIn("color", style)
            self.assertTrue(style["color"])
            self.assertNotEqual(style["color"], "")
            
            # Background should be defined
            self.assertIn("background-color", style)
            self.assertTrue(style["background-color"])
    
    def test_light_theme_readability(self):
        """Test that light theme provides readable text."""
        self.theme_manager.set_theme("light")
        
        # Test status messages are readable
        for status_type in ["success", "error", "warning", "info"]:
            style = self.theme_manager.get_status_style(status_type)
            
            # Color should be defined and not empty
            self.assertIn("color", style)
            self.assertTrue(style["color"])
            self.assertNotEqual(style["color"], "")
    
    def test_theme_switching(self):
        """Test switching between themes maintains readability."""
        # Start with dark theme
        self.theme_manager.set_theme("dark")
        dark_style = self.theme_manager.get_status_style("success")
        
        # Switch to light theme
        self.theme_manager.set_theme("light")
        light_style = self.theme_manager.get_status_style("success")
        
        # Styles should be different but both valid
        self.assertNotEqual(dark_style["color"], light_style["color"])
        self.assertTrue(dark_style["color"])
        self.assertTrue(light_style["color"])
    
    def test_component_styling_consistency(self):
        """Test that all component styles use consistent color scheme."""
        preview_style = self.theme_manager.get_preview_style()
        chapter_style = self.theme_manager.get_chapter_preview_style()
        toggle_style = self.theme_manager.get_toggle_style()
        
        # All should use colors from the current theme
        self.assertEqual(preview_style["color"], self.theme_manager.colors.primary_text)
        self.assertEqual(chapter_style["color"], self.theme_manager.colors.primary_text)
        self.assertEqual(toggle_style["color"], self.theme_manager.colors.primary_text)


if __name__ == '__main__':
    unittest.main()