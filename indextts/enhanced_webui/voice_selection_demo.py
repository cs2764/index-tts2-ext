"""
Demo script showing voice selection functionality integration with Gradio.
"""

import gradio as gr
import os
from typing import Tuple, Optional

from .enhanced_webui import EnhancedWebUI
from .webui_components import WebUIComponents


class VoiceSelectionDemo:
    """Demo class for voice selection functionality."""
    
    def __init__(self):
        """Initialize the demo."""
        self.enhanced_webui = EnhancedWebUI()
        self.components = WebUIComponents(self.enhanced_webui)
    
    def create_interface(self) -> gr.Interface:
        """Create Gradio interface for voice selection demo."""
        
        with gr.Blocks(title="Voice Selection Demo") as interface:
            gr.Markdown("# Voice Sample Selection Demo")
            gr.Markdown("This demo shows the voice sample selection and refresh functionality.")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Voice selection components
                    voice_dropdown, refresh_button, status_display = self.components.create_voice_selection_components()
                    
                    # Sample info display
                    sample_info = gr.JSON(
                        label="Selected Sample Info",
                        value={}
                    )
                    
                    # Validation status
                    validation_status = gr.HTML(
                        value="<p>Select a voice sample to see validation status</p>"
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Instructions")
                    gr.Markdown("""
                    1. **Add samples**: Place .wav or .mp3 files in the `samples` folder
                    2. **Refresh**: Click the refresh button to update the list
                    3. **Select**: Choose a voice sample from the dropdown
                    4. **Validate**: See validation status and sample information
                    """)
                    
                    # Sample folder info
                    folder_info = gr.HTML(
                        value=self._get_folder_info_html()
                    )
            
            # Event handlers
            refresh_button.click(
                fn=self._handle_refresh,
                outputs=[voice_dropdown, status_display, folder_info]
            )
            
            voice_dropdown.change(
                fn=self._handle_voice_selection,
                inputs=[voice_dropdown],
                outputs=[sample_info, validation_status]
            )
            
            # Initial load
            interface.load(
                fn=self._handle_initial_load,
                outputs=[voice_dropdown, status_display, folder_info]
            )
        
        return interface
    
    def _handle_refresh(self) -> Tuple[gr.Dropdown, gr.HTML, gr.HTML]:
        """Handle refresh button click."""
        try:
            # Refresh samples
            updated_dropdown, updated_status = self.components.refresh_voice_samples()
            
            # Update folder info
            folder_info = gr.HTML(value=self._get_folder_info_html())
            
            return updated_dropdown, updated_status, folder_info
            
        except Exception as e:
            error_status = gr.HTML(
                value=f'<div style="color: red;">Error: {str(e)}</div>'
            )
            return gr.Dropdown(choices=[], value=None), error_status, gr.HTML(value="")
    
    def _handle_voice_selection(self, voice_path: str) -> Tuple[gr.JSON, gr.HTML]:
        """Handle voice selection change."""
        if not voice_path:
            return gr.JSON(value={}), gr.HTML(value="<p>No sample selected</p>")
        
        # Get sample info
        sample_info = self.components.get_voice_sample_info(voice_path)
        
        # Validate selection
        is_valid, error_message = self.components.validate_voice_selection(voice_path)
        
        # Create validation status HTML
        if is_valid:
            validation_html = '''
            <div style="padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;">
                <strong>✅ Valid sample selected</strong>
            </div>
            '''
        else:
            validation_html = f'''
            <div style="padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;">
                <strong>❌ Invalid sample:</strong> {error_message}
            </div>
            '''
        
        return gr.JSON(value=sample_info or {}), gr.HTML(value=validation_html)
    
    def _handle_initial_load(self) -> Tuple[gr.Dropdown, gr.HTML, gr.HTML]:
        """Handle initial interface load."""
        return self._handle_refresh()
    
    def _get_folder_info_html(self) -> str:
        """Get HTML info about the samples folder."""
        samples_dir = self.enhanced_webui.get_voice_manager().get_samples_directory()
        
        if not os.path.exists(samples_dir):
            return f'''
            <div style="padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
                <strong>📁 Samples folder:</strong><br>
                <code>{samples_dir}</code><br>
                <em>Folder will be created automatically</em>
            </div>
            '''
        
        # Count files in directory
        try:
            all_files = os.listdir(samples_dir)
            audio_files = [f for f in all_files if f.lower().endswith(('.wav', '.mp3'))]
            
            return f'''
            <div style="padding: 10px; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px;">
                <strong>📁 Samples folder:</strong><br>
                <code>{samples_dir}</code><br>
                <strong>Files:</strong> {len(audio_files)} audio, {len(all_files) - len(audio_files)} other
            </div>
            '''
        except Exception as e:
            return f'''
            <div style="padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
                <strong>📁 Samples folder:</strong><br>
                <code>{samples_dir}</code><br>
                <em>Error reading folder: {str(e)}</em>
            </div>
            '''
    
    def launch(self, **kwargs):
        """Launch the demo interface."""
        interface = self.create_interface()
        return interface.launch(**kwargs)


def main():
    """Run the voice selection demo."""
    demo = VoiceSelectionDemo()
    demo.launch(share=False, debug=True)


if __name__ == "__main__":
    main()