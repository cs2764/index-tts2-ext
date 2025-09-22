"""
Performance tests for dark theme compatibility and UI rendering.
"""

import time
import threading
from unittest import TestCase
from unittest.mock import Mock, patch

from indextts.enhanced_webui.ui_theme_manager import UIThemeManager, get_theme_manager
from indextts.enhanced_webui.enhanced_ui_components import EnhancedUIComponents


class TestDarkThemePerformance(TestCase):
    """Test performance of dark theme rendering and compatibility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.theme_manager = get_theme_manager()
        
        # Mock enhanced webui
        self.mock_enhanced_webui = Mock()
        self.mock_enhanced_webui.get_config.return_value = Mock()
        
        self.ui_components = EnhancedUIComponents(self.mock_enhanced_webui)
    
    def test_css_generation_performance(self):
        """Test CSS generation performance."""
        start_time = time.time()
        
        # Generate CSS multiple times
        for _ in range(100):
            css = self.theme_manager.get_custom_css()
        
        generation_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(generation_time, 1.0)  # Less than 1 second for 100 generations
        
        # CSS should be substantial but not excessive
        self.assertGreater(len(css), 1000)  # At least 1KB
        self.assertLess(len(css), 100000)   # Less than 100KB
    
    def test_theme_switching_performance(self):
        """Test performance of theme switching."""
        start_time = time.time()
        
        # Switch themes multiple times
        for i in range(50):
            theme = "dark" if i % 2 == 0 else "light"
            self.theme_manager.set_theme(theme)
            css = self.theme_manager.get_custom_css()
        
        switching_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(switching_time, 2.0)  # Less than 2 seconds for 50 switches
    
    def test_component_styling_performance(self):
        """Test performance of component styling application."""
        import gradio as gr
        
        # Create mock components
        components = []
        for i in range(100):
            mock_component = Mock()
            mock_component.elem_classes = []
            components.append(mock_component)
        
        start_time = time.time()
        
        # Apply styling to all components
        for component in components:
            styled = self.theme_manager.apply_theme_to_component(component, "file_upload")
        
        styling_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(styling_time, 1.0)  # Less than 1 second for 100 components
    
    def test_html_generation_performance(self):
        """Test performance of themed HTML generation."""
        start_time = time.time()
        
        # Generate various HTML elements
        for i in range(100):
            # Status messages
            self.theme_manager.create_status_message(f"Message {i}", "success")
            self.theme_manager.create_status_message(f"Error {i}", "error")
            
            # Progress bars
            self.theme_manager.create_progress_bar(i / 100.0, f"Progress {i}%")
            
            # Loading indicators
            self.theme_manager.create_loading_indicator(f"Loading {i}...")
        
        html_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(html_time, 2.0)  # Less than 2 seconds for 400 HTML generations
    
    def test_concurrent_theme_operations(self):
        """Test concurrent theme operations performance."""
        results = []
        errors = []
        
        def theme_worker():
            try:
                for i in range(20):
                    # Generate CSS
                    css = self.theme_manager.get_custom_css()
                    
                    # Create status message
                    status = self.theme_manager.create_status_message(f"Test {i}", "info")
                    
                    # Create progress bar
                    progress = self.theme_manager.create_progress_bar(0.5, "50%")
                    
                    results.append((css, status, progress))
            except Exception as e:
                errors.append(e)
        
        # Run multiple concurrent operations
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=theme_worker)
            threads.append(thread)
            thread.start()
        
        start_time = time.time()
        
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        # Should complete without errors
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 100)  # 5 threads * 20 operations each
        
        # Should complete within reasonable time
        self.assertLess(concurrent_time, 5.0)  # Less than 5 seconds
    
    def test_memory_usage_during_theme_operations(self):
        """Test memory usage during intensive theme operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform intensive theme operations
        for i in range(1000):
            css = self.theme_manager.get_custom_css()
            status = self.theme_manager.create_status_message(f"Test {i}", "success")
            progress = self.theme_manager.create_progress_bar(i / 1000.0, f"{i/10:.1f}%")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        self.assertLess(memory_increase, 50 * 1024 * 1024)
    
    def test_large_content_rendering_performance(self):
        """Test performance with large content rendering."""
        # Create large content
        large_text = "\n".join([f"Line {i}: This is a very long line with lots of content to test rendering performance." for i in range(1000)])
        
        start_time = time.time()
        
        # Render large content with theming
        preview_html = self.theme_manager.create_file_preview_html(
            large_text,
            "large_file.txt",
            "utf-8",
            "500 KB",
            1000,
            True
        )
        
        rendering_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(rendering_time, 2.0)  # Less than 2 seconds
        
        # Should contain the content
        self.assertIn("large_file.txt", preview_html)
        self.assertIn("Line 1:", preview_html)
    
    def test_chapter_preview_performance_with_many_chapters(self):
        """Test chapter preview performance with many chapters."""
        # Create many chapters
        chapters = [f"第{i+1}章 章节标题{i+1}" for i in range(500)]
        
        start_time = time.time()
        
        # Render chapter preview
        chapter_html = self.theme_manager.create_chapter_preview_html(chapters, len(chapters))
        
        rendering_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(rendering_time, 1.0)  # Less than 1 second
        
        # Should contain chapter information
        self.assertIn("共识别到 500 个章节", chapter_html)
        self.assertIn("第1章", chapter_html)
        
        # Should handle truncation for display
        self.assertIn("还有", chapter_html)  # Should show "还有 X 个章节"
    
    def test_responsive_design_performance(self):
        """Test responsive design CSS performance."""
        css = self.theme_manager.get_custom_css()
        
        # Should contain responsive design rules
        self.assertIn("@media", css)
        self.assertIn("max-width", css)
        
        # Count media queries (should be reasonable number)
        media_query_count = css.count("@media")
        self.assertGreater(media_query_count, 0)
        self.assertLess(media_query_count, 20)  # Not excessive
    
    def test_css_minification_effectiveness(self):
        """Test CSS size and minification effectiveness."""
        css = self.theme_manager.get_custom_css()
        
        # CSS should be reasonably sized
        css_size = len(css)
        self.assertGreater(css_size, 1000)   # At least 1KB (substantial)
        self.assertLess(css_size, 200000)    # Less than 200KB (not excessive)
        
        # Should not have excessive whitespace
        lines = css.split('\n')
        empty_lines = sum(1 for line in lines if not line.strip())
        total_lines = len(lines)
        
        # Empty lines should be less than 20% of total
        if total_lines > 0:
            empty_ratio = empty_lines / total_lines
            self.assertLess(empty_ratio, 0.2)
    
    def test_color_calculation_performance(self):
        """Test color calculation and manipulation performance."""
        start_time = time.time()
        
        # Test color operations
        for i in range(1000):
            # Test various color operations that might be used
            base_color = f"#{i:06x}"  # Generate hex colors
            
            # Simulate color manipulations
            rgb_values = [int(base_color[j:j+2], 16) for j in (1, 3, 5)]
            darker = [max(0, val - 20) for val in rgb_values]
            lighter = [min(255, val + 20) for val in rgb_values]
        
        color_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(color_time, 0.5)  # Less than 0.5 seconds for 1000 operations
    
    def test_tooltip_rendering_performance(self):
        """Test tooltip rendering performance."""
        start_time = time.time()
        
        # Create many tooltips
        for i in range(200):
            tooltip_html = self.theme_manager.create_tooltip(
                f"Element {i}",
                f"This is tooltip text for element {i} with detailed information."
            )
        
        tooltip_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(tooltip_time, 1.0)  # Less than 1 second for 200 tooltips
    
    def test_status_icon_rendering_performance(self):
        """Test status icon rendering performance."""
        status_types = ["success", "error", "warning", "info"]
        
        start_time = time.time()
        
        # Create many status messages with icons
        for i in range(100):
            for status_type in status_types:
                status_html = self.theme_manager.create_status_message(
                    f"Status message {i}",
                    status_type
                )
        
        icon_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(icon_time, 2.0)  # Less than 2 seconds for 400 status messages


class TestUIComponentPerformance(TestCase):
    """Test performance of UI component operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock enhanced webui
        self.mock_enhanced_webui = Mock()
        self.mock_enhanced_webui.get_config.return_value = Mock()
        
        self.ui_components = EnhancedUIComponents(self.mock_enhanced_webui)
    
    def test_component_creation_performance(self):
        """Test performance of component creation."""
        start_time = time.time()
        
        # Create components multiple times
        for _ in range(10):
            file_components = self.ui_components.create_enhanced_file_upload_components()
            format_components = self.ui_components.create_enhanced_format_selection_components()
            voice_components = self.ui_components.create_enhanced_voice_selection_components()
            auto_save_components = self.ui_components.create_enhanced_auto_save_components()
            generation_components = self.ui_components.create_enhanced_generation_components()
        
        creation_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(creation_time, 5.0)  # Less than 5 seconds for 50 component sets
    
    def test_update_operations_performance(self):
        """Test performance of component update operations."""
        import tempfile
        import os
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Test content for performance testing")
            temp_file = f.name
        
        try:
            start_time = time.time()
            
            # Perform multiple update operations
            for i in range(20):
                preview_html, chapter_html, show_native = self.ui_components.update_file_preview(
                    temp_file,
                    file_cleaning_enabled=True,
                    chapter_recognition_enabled=True
                )
                
                format_info = self.ui_components.update_format_info("MP3", 128)
                
                filename_preview = self.ui_components.update_filename_preview(
                    temp_file,
                    "/path/to/voice.wav",
                    "MP3"
                )
            
            update_time = time.time() - start_time
            
            # Should complete within reasonable time
            self.assertLess(update_time, 10.0)  # Less than 10 seconds for 60 operations
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_concurrent_component_operations(self):
        """Test concurrent component operations."""
        results = []
        errors = []
        
        def component_worker():
            try:
                for i in range(10):
                    # Create components
                    components = self.ui_components.create_enhanced_file_upload_components()
                    
                    # Update format info
                    format_info = self.ui_components.update_format_info("MP3", 64)
                    
                    results.append((components, format_info))
            except Exception as e:
                errors.append(e)
        
        # Run concurrent operations
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=component_worker)
            threads.append(thread)
            thread.start()
        
        start_time = time.time()
        
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        
        # Should complete without errors
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 30)  # 3 threads * 10 operations each
        
        # Should complete within reasonable time
        self.assertLess(concurrent_time, 5.0)  # Less than 5 seconds


if __name__ == '__main__':
    import unittest
    unittest.main()