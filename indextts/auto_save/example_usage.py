"""
Example usage of the auto-save infrastructure.

This demonstrates how to integrate the auto-save functionality
with IndexTTS2 inference.
"""

import torch
from .save_manager import IncrementalSaveManager


def example_tts_with_autosave():
    """Example of how to use auto-save during TTS generation."""
    
    # Initialize auto-save manager
    save_manager = IncrementalSaveManager(
        save_interval=3,  # Save every 3 segments
        enabled=True
    )
    
    # Set up callbacks for progress reporting
    def progress_callback(message):
        print(f"Progress: {message}")
    
    def error_callback(error):
        print(f"Error: {error}")
    
    save_manager.set_callbacks(progress_callback, error_callback)
    
    # Initialize for generation
    output_path = "output/generated_audio.wav"
    save_manager.initialize_generation(output_path)
    
    try:
        # EXAMPLE: Simulate TTS generation with multiple segments
        # NOTE: This is demonstration code only. In real usage, replace with actual TTS calls.
        segments = [
            "Hello, this is the first segment.",
            "This is the second segment of our audio.",
            "Here comes the third segment.",
            "And finally, the fourth segment."
        ]
        
        for step, text in enumerate(segments, 1):
            # EXAMPLE: Simulate audio generation for this segment
            # REAL USAGE: Replace this with actual TTS engine call:
            # audio_tensor = tts_engine.infer(text, voice_prompt, **kwargs)
            simulated_audio = torch.randn(1, 22050)  # 1 second of FAKE audio for demo
            
            # Add segment to auto-save buffer (this part is real)
            segment_info = {
                'text': text,
                'generation_time': 0.5  # In real usage, measure actual generation time
            }
            
            save_triggered = save_manager.add_audio_segment(
                simulated_audio, step, segment_info
            )
            
            if save_triggered:
                print(f"Auto-save triggered at step {step}")
            
            # Get current save status
            status = save_manager.get_save_status()
            print(f"Step {step}: Next save at step {status['next_save_step']}")
        
        # Finalize the output
        final_path = save_manager.finalize_output()
        print(f"Generation complete! Final audio saved to: {final_path}")
        
        return final_path
        
    except Exception as e:
        print(f"Generation failed: {e}")
        return None
        
    finally:
        # Always clean up temporary files
        save_manager.cleanup_temp_files()


if __name__ == "__main__":
    example_tts_with_autosave()