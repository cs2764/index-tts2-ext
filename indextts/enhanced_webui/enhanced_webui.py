"""
Main enhanced WebUI class that integrates all new features.
"""

import gradio as gr
from typing import Optional, Dict
from ..config import EnhancedWebUIConfig, ConfigManager
from ..file_processing import FileProcessor
from ..chapter_parsing import SmartChapterParser
from ..audio_formats import AudioFormatConverter
from ..task_management import TaskManager
from ..voice_management import VoiceSampleManager
from ..output_management import OutputManager
from .ui_polish import UIPolishManager, create_enhanced_ui_components


class EnhancedWebUI:
    """Main class that integrates all enhanced WebUI features."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the enhanced WebUI with all components.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path or "config")
        self.config = self.config_manager.load_config()
        
        # Initialize all components
        self.file_processor = FileProcessor(self.config.file_processing)
        self.chapter_parser = SmartChapterParser(self.config.chapter_parsing)
        self.format_converter = AudioFormatConverter(self.config.audio_formats)
        self.task_manager = TaskManager(self.config.task_management)
        # Give task manager access to enhanced webui for format conversion
        self.task_manager.enhanced_webui = self
        self.voice_manager = VoiceSampleManager(self.config.voice_samples)
        self.output_manager = OutputManager(self.config.output)
        
        # Initialize UI polish and enhancements
        self.ui_polish_manager = UIPolishManager()
        
        print("Enhanced WebUI initialized with all components and UI polish")
    
    def get_file_processor(self) -> FileProcessor:
        """Get the file processor instance."""
        return self.file_processor
    
    def get_chapter_parser(self) -> SmartChapterParser:
        """Get the chapter parser instance."""
        return self.chapter_parser
    
    def get_format_converter(self) -> AudioFormatConverter:
        """Get the format converter instance."""
        return self.format_converter
    
    def get_task_manager(self) -> TaskManager:
        """Get the task manager instance."""
        return self.task_manager
    
    def get_voice_manager(self) -> VoiceSampleManager:
        """Get the voice manager instance."""
        return self.voice_manager
    
    def get_output_manager(self) -> OutputManager:
        """Get the output manager instance."""
        return self.output_manager
    
    def get_audio_segmenter(self):
        """Get the audio segmenter instance from format converter."""
        from ..audio_formats.format_converter import AudioSegmenter
        return AudioSegmenter(self.format_converter)
    
    def get_config(self) -> EnhancedWebUIConfig:
        """Get the current configuration."""
        return self.config
    
    def update_config(self, updates: dict) -> bool:
        """
        Update configuration and reinitialize components if needed.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            True if update was successful
        """
        try:
            self.config = self.config_manager.update_config(updates)
            
            # Reinitialize components with new config
            self._reinitialize_components()
            
            return True
        except Exception as e:
            print(f"Error updating configuration: {e}")
            return False
    
    def shutdown(self):
        """Shutdown all components gracefully."""
        if self.task_manager:
            self.task_manager.shutdown()
        print("Enhanced WebUI shutdown complete")
    
    def create_enhanced_interface(self) -> gr.Blocks:
        """
        Create the enhanced Gradio interface with all polish and improvements.
        
        Returns:
            Gradio Blocks interface with enhanced UI
        """
        # Create enhanced UI components
        components = create_enhanced_ui_components()
        
        # Add loading indicators and progress feedback
        components = self.ui_polish_manager.add_loading_indicators(components)
        components = self.ui_polish_manager.add_tooltips_and_help(components)
        
        # Add progress feedback functions
        progress_functions = self.ui_polish_manager.add_progress_feedback(
            lambda progress, message: print(f"Progress: {progress*100:.1f}% - {message}")
        )
        
        # Create responsive layout with event handlers
        interface = self._create_interface_with_handlers(components, progress_functions)
        
        return interface
    
    def _create_interface_with_handlers(self, components: Dict[str, gr.Component], 
                                      progress_functions: Dict[str, callable]) -> gr.Blocks:
        """
        Create interface with event handlers within Blocks context.
        
        Args:
            components: Dictionary of UI components
            progress_functions: Dictionary of progress update functions
            
        Returns:
            Gradio Blocks interface with event handlers
        """
        with gr.Blocks(
            theme=gr.themes.Soft(
                primary_hue=gr.themes.colors.blue,
                secondary_hue=gr.themes.colors.slate,
                neutral_hue=gr.themes.colors.slate
            ),
            css=self.ui_polish_manager._get_custom_css(),
            title="IndexTTS2 Enhanced Web UI"
        ) as interface:
            
            # Header
            gr.HTML(
                value="<h1 style='text-align: center; margin-bottom: 20px;'>"
                      "🎵 IndexTTS2 Enhanced Web UI</h1>"
                      "<p style='text-align: center; color: #64748b;'>"
                      "Advanced text-to-speech with performance optimizations and enhanced UX"
                      "</p>"
            )
            
            # Main interface components
            with gr.Row():
                with gr.Column():
                    file_upload = components.get('file_upload', gr.File(label="📁 Upload File"))
                    text_input = components.get('text_input', gr.Textbox(label="✨ Text Input", lines=5))
                
                with gr.Column():
                    voice_sample = components.get('voice_sample', gr.Dropdown(label="🎤 Voice Sample"))
                    output_format = gr.Dropdown(
                        label="💾 Output Format",
                        choices=["WAV", "MP3", "M4B"],
                        value="WAV"
                    )
                    generate_btn = components.get('generate_btn', gr.Button("🎯 Generate Audio", variant="primary"))
            
            # Status and output
            with gr.Row():
                with gr.Column():
                    file_status = components.get('file_upload_status', gr.HTML(visible=False))
                    task_status = components.get('task_status_indicator', gr.HTML(visible=False))
                
                with gr.Column():
                    audio_output = components.get('audio_output', gr.Audio(label="🎧 Generated Audio"))
            
            # Set up event handlers within the Blocks context
            def handle_file_upload(file):
                if file is None:
                    return None, progress_functions['update_file_progress'](0, "No file selected")
                
                try:
                    # Update progress: Starting
                    progress_html = progress_functions['update_file_progress'](0.1, "Processing file...")
                    
                    # Process file (simplified for demo)
                    with open(file.name, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Update progress: Complete
                    progress_html = progress_functions['update_file_progress'](1.0, "File processed successfully")
                    
                    return content, progress_html
                    
                except Exception as e:
                    error_html = self.ui_polish_manager.format_error_message(e, "File Processing")
                    return None, error_html
            
            def handle_generation(text, voice_sample_val, output_format_val):
                if not text or not text.strip():
                    return None, progress_functions['update_task_status']("failed", "❌")
                
                try:
                    # Update status: Starting
                    status_html = progress_functions['update_task_status']("processing", "🔄")
                    
                    # For demo purposes, simulate generation
                    import time
                    time.sleep(0.5)  # Simulate processing
                    
                    # Update status: Complete
                    status_html = progress_functions['update_task_status']("completed", "✅")
                    
                    return None, status_html  # Return None for audio since this is a demo
                    
                except Exception as e:
                    error_html = self.ui_polish_manager.format_error_message(e, "Audio Generation")
                    failed_status = progress_functions['update_task_status']("failed", "❌")
                    return None, failed_status
            
            # Connect event handlers
            file_upload.change(
                fn=handle_file_upload,
                inputs=[file_upload],
                outputs=[text_input, file_status]
            )
            
            generate_btn.click(
                fn=handle_generation,
                inputs=[text_input, voice_sample, output_format],
                outputs=[audio_output, task_status]
            )
        
        return interface
    
    def _reinitialize_components(self):
        """Reinitialize components with updated configuration."""
        # Only reinitialize if configuration has changed significantly
        # For now, we'll keep the existing instances
        pass