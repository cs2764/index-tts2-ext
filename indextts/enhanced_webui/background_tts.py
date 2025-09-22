"""
Background TTS generation integration for the enhanced WebUI.
"""

import os
import time
from typing import Dict, Any, Optional, Callable
from ..task_management import TaskManager


class BackgroundTTSIntegration:
    """Handles integration of TTS generation with background task management."""
    
    def __init__(self, task_manager: TaskManager, tts_engine, enhanced_webui):
        """
        Initialize background TTS integration.
        
        Args:
            task_manager: TaskManager instance for handling background tasks
            tts_engine: IndexTTS2 engine instance
            enhanced_webui: EnhancedWebUI instance for accessing other components
        """
        self.task_manager = task_manager
        self.tts_engine = tts_engine
        self.enhanced_webui = enhanced_webui
        
        # Thresholds for automatic background processing
        self.text_length_threshold = 500  # characters
        self.token_count_threshold = 200  # tokens
        
        # Register TTS task processor
        self._register_tts_processor()
    
    def should_use_background_processing(self, text: str, **kwargs) -> bool:
        """
        Determine if text should be processed in background.
        
        Args:
            text: Input text to analyze
            **kwargs: Additional parameters that might affect processing time
            
        Returns:
            True if background processing should be used
        """
        # Check text length - only use background for very long texts
        if len(text) > self.text_length_threshold * 2:  # Increase threshold
            return True
        
        # Check token count if tokenizer is available
        if hasattr(self.tts_engine, 'tokenizer') and self.tts_engine.tokenizer:
            try:
                tokens = self.tts_engine.tokenizer.tokenize(text)
                if len(tokens) > self.token_count_threshold * 2:  # Increase threshold
                    return True
            except Exception:
                # If tokenization fails, fall back to character count
                pass
        
        # Only use background for complex segmentation tasks
        segmentation_enabled = kwargs.get('enable_segmentation', False)
        chapters_per_file = kwargs.get('chapters_per_file', 1)
        
        # Only use background if segmentation is enabled AND there are many chapters
        if segmentation_enabled and chapters_per_file > 5:
            return True
        
        # Format conversion alone doesn't require background processing
        # since it's relatively fast
        
        return False
    
    def create_background_task(self, 
                             text: str,
                             voice_prompt: str,
                             output_path: str,
                             generation_params: Dict[str, Any],
                             progress_callback: Optional[Callable] = None,
                             console_callback: Optional[Callable] = None) -> str:
        """
        Create a background TTS generation task.
        
        Args:
            text: Text to synthesize
            voice_prompt: Path to voice prompt audio
            output_path: Output file path
            generation_params: TTS generation parameters
            progress_callback: Optional callback for progress updates
            console_callback: Optional callback for console output
            
        Returns:
            Task ID for tracking the background task
        """
        task_params = {
            'task_type': 'tts_generation',
            'text': text,
            'voice_prompt': voice_prompt,
            'output_path': output_path,
            'generation_params': generation_params,
            'tts_engine': self.tts_engine,  # Include TTS engine reference
            'created_by': 'webui'
        }
        
        task_id = self.task_manager.create_task(
            task_type='tts_generation',
            params=task_params,
            callback=progress_callback,
            console_callback=console_callback
        )
        
        return task_id
    
    def generate_audio_sync_or_async(self,
                                   text: str,
                                   voice_prompt: str,
                                   output_path: str,
                                   generation_params: Dict[str, Any],
                                   force_background: bool = False,
                                   progress_callback: Optional[Callable] = None,
                                   console_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Generate audio either synchronously or asynchronously based on content size.
        
        Args:
            text: Text to synthesize
            voice_prompt: Path to voice prompt audio
            output_path: Output file path
            generation_params: TTS generation parameters
            force_background: Force background processing regardless of content size
            progress_callback: Optional callback for progress updates
            console_callback: Optional callback for console output
            
        Returns:
            Dictionary with generation result information
        """
        # Determine processing mode
        use_background = force_background or self.should_use_background_processing(text, **generation_params)
        
        if use_background:
            # Create background task
            task_id = self.create_background_task(
                text=text,
                voice_prompt=voice_prompt,
                output_path=output_path,
                generation_params=generation_params,
                progress_callback=progress_callback,
                console_callback=console_callback
            )
            
            return {
                'mode': 'background',
                'task_id': task_id,
                'status': 'queued',
                'message': f'Large content detected. Processing in background (Task ID: {task_id[:8]}...)'
            }
        else:
            # Process synchronously
            try:
                result_path = self._process_tts_sync(
                    text=text,
                    voice_prompt=voice_prompt,
                    output_path=output_path,
                    generation_params=generation_params,
                    progress_callback=progress_callback
                )
                
                return {
                    'mode': 'synchronous',
                    'result_path': result_path,
                    'status': 'completed',
                    'message': 'Audio generation completed successfully'
                }
            except Exception as e:
                return {
                    'mode': 'synchronous',
                    'status': 'failed',
                    'error': str(e),
                    'message': f'Audio generation failed: {str(e)}'
                }
    
    def _process_tts_sync(self,
                         text: str,
                         voice_prompt: str,
                         output_path: str,
                         generation_params: Dict[str, Any],
                         progress_callback: Optional[Callable] = None) -> str:
        """
        Process TTS generation synchronously.
        
        Args:
            text: Text to synthesize
            voice_prompt: Path to voice prompt audio
            output_path: Output file path
            generation_params: TTS generation parameters
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to generated audio file
        """
        # Extract TTS parameters
        emo_ref_path = generation_params.get('emo_ref_path')
        emo_weight = generation_params.get('emo_weight', 0.8)
        emo_vector = generation_params.get('emo_vector')
        use_emo_text = generation_params.get('use_emo_text', False)
        emo_text = generation_params.get('emo_text')
        use_random = generation_params.get('use_random', False)
        max_text_tokens_per_segment = generation_params.get('max_text_tokens_per_segment', 120)
        
        # Extract generation kwargs
        generation_kwargs = generation_params.get('generation_kwargs', {})
        
        # Set progress callback if provided
        if progress_callback and hasattr(self.tts_engine, 'gr_progress'):
            self.tts_engine.gr_progress = progress_callback
        
        # Generate audio (always as WAV first)
        output_format = generation_params.get('output_format', 'wav').lower()
        temp_output = output_path if output_format == "wav" else output_path.replace(f".{output_format}", ".wav")
        
        # Call TTS engine
        result_path = self.tts_engine.infer(
            spk_audio_prompt=voice_prompt,
            text=text,
            output_path=temp_output,
            emo_audio_prompt=emo_ref_path,
            emo_alpha=emo_weight,
            emo_vector=emo_vector,
            use_emo_text=use_emo_text,
            emo_text=emo_text,
            use_random=use_random,
            verbose=generation_params.get('verbose', False),
            max_text_tokens_per_segment=max_text_tokens_per_segment,
            **generation_kwargs
        )
        
        # Convert format if needed
        if output_format != "wav" and result_path:
            result_path = self._convert_audio_format(
                result_path, output_format, generation_params
            )
        
        return result_path
    
    def _convert_audio_format(self, 
                            input_path: str, 
                            target_format: str, 
                            generation_params: Dict[str, Any]) -> str:
        """
        Convert audio to target format.
        
        Args:
            input_path: Path to input WAV file
            target_format: Target format (mp3, m4b)
            generation_params: Generation parameters for format-specific options
            
        Returns:
            Path to converted audio file
        """
        try:
            format_converter = self.enhanced_webui.get_format_converter()
            
            if target_format == "mp3":
                bitrate = generation_params.get('mp3_bitrate', 64)
                final_output = format_converter.convert_to_format(input_path, "mp3", bitrate=bitrate)
            elif target_format == "m4b":
                # Get chapters if available
                chapters = generation_params.get('chapters', [])
                metadata = generation_params.get('metadata', {})
                final_output = format_converter.create_m4b_audiobook([input_path], chapters, metadata)
            else:
                # Unsupported format, keep as WAV
                final_output = input_path
            
            # Remove temp WAV file if conversion was successful
            if final_output != input_path and os.path.exists(input_path):
                os.remove(input_path)
            
            return final_output
            
        except Exception as e:
            print(f"Format conversion failed: {e}")
            # Return original WAV file
            return input_path
    
    def _register_tts_processor(self):
        """Register TTS task processor with the task manager."""
        # This would be called by the task manager when processing TTS tasks
        # The actual processing logic is handled by the task manager's worker threads
        pass
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a background TTS task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status information or None if not found
        """
        task_status = self.task_manager.get_task_status(task_id)
        
        if not task_status:
            return None
        
        return {
            'task_id': task_id,
            'status': task_status.status.value,
            'progress': task_status.progress,
            'current_stage': task_status.current_stage,
            'estimated_remaining': task_status.estimated_remaining,
            'result_path': task_status.result_path,
            'error_message': task_status.error_message,
            'created_at': task_status.created_at.isoformat(),
            'updated_at': task_status.updated_at.isoformat()
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a background TTS task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled successfully
        """
        return self.task_manager.cancel_task(task_id)
    
    def get_download_link(self, task_id: str) -> Optional[str]:
        """
        Get download link for completed task results.
        
        Args:
            task_id: ID of the completed task
            
        Returns:
            Download link or None if not available
        """
        return self.task_manager.get_download_link(task_id)
    
    def cleanup_old_tasks(self):
        """Clean up old completed tasks."""
        self.task_manager.cleanup_old_tasks()


def create_enhanced_generation_function(background_tts: BackgroundTTSIntegration):
    """
    Create an enhanced generation function that supports background processing.
    
    Args:
        background_tts: BackgroundTTSIntegration instance
        
    Returns:
        Enhanced generation function
    """
    def enhanced_gen_single(emo_control_method, voice_selection, prompt, text,
                          emo_ref_path, emo_weight,
                          vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8,
                          emo_text, emo_random,
                          output_format, mp3_bitrate, enable_segmentation, chapters_per_file,
                          auto_save, filename_preview,
                          max_text_tokens_per_segment=120,
                          force_background=False,
                          *args, progress=None):
        """
        Enhanced generation function with background processing support.
        """
        import gradio as gr
        
        # Determine voice prompt source
        voice_prompt = voice_selection if voice_selection else prompt
        
        # Validate voice selection
        if not voice_prompt:
            return gr.update(value=None, visible=True), gr.update(value="❌ No voice sample selected", visible=True)
        
        # Validate text input
        if not text or not text.strip():
            return gr.update(value=None, visible=True), gr.update(value="❌ No text provided", visible=True)
        
        # Determine output format and path
        format_ext = output_format.lower() if output_format else "wav"
        
        if auto_save and filename_preview:
            # Extract filename from HTML content if it contains HTML tags
            if filename_preview.strip().startswith('<'):
                # Parse HTML to extract the actual filename
                import re
                match = re.search(r'<code>([^<]+)</code>', filename_preview)
                if match:
                    actual_filename = match.group(1)
                else:
                    # Fallback: generate a new filename
                    actual_filename = f"spk_{int(time.time())}.{format_ext}"
            else:
                actual_filename = filename_preview
            
            output_path = os.path.join("outputs", actual_filename)
        else:
            output_path = os.path.join("outputs", f"spk_{int(time.time())}.{format_ext}")
        
        # Prepare generation parameters
        do_sample, top_p, top_k, temperature, length_penalty, num_beams, repetition_penalty, max_mel_tokens = args
        
        generation_kwargs = {
            "do_sample": bool(do_sample),
            "top_p": float(top_p),
            "top_k": int(top_k) if int(top_k) > 0 else None,
            "temperature": float(temperature),
            "length_penalty": float(length_penalty),
            "num_beams": num_beams,
            "repetition_penalty": float(repetition_penalty),
            "max_mel_tokens": int(max_mel_tokens),
        }
        
        # Process emotion control
        if type(emo_control_method) is not int:
            emo_control_method = emo_control_method.value
        
        # Initialize vec to None by default
        vec = None
        
        if emo_control_method == 0:  # emotion from speaker
            emo_ref_path = None
        elif emo_control_method == 1:  # emotion from reference audio
            emo_weight = emo_weight * 0.8  # normalize for better UX
        elif emo_control_method == 2:  # emotion from custom vectors
            vec = [vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8]
            # Normalize emotion vector
            k_vec = [0.75, 0.70, 0.80, 0.80, 0.75, 0.75, 0.55, 0.45]
            import numpy as np
            tmp = np.array(k_vec) * np.array(vec)
            if np.sum(tmp) > 0.8:
                tmp = tmp * 0.8 / np.sum(tmp)
            vec = tmp.tolist()
        
        if emo_text == "":
            emo_text = None
        
        # Prepare generation parameters
        generation_params = {
            'emo_ref_path': emo_ref_path,
            'emo_weight': emo_weight,
            'emo_vector': vec,
            'use_emo_text': (emo_control_method == 3),
            'emo_text': emo_text,
            'use_random': emo_random,
            'max_text_tokens_per_segment': int(max_text_tokens_per_segment),
            'generation_kwargs': generation_kwargs,
            'output_format': format_ext,
            'mp3_bitrate': int(mp3_bitrate) if mp3_bitrate else 64,
            'enable_segmentation': enable_segmentation,
            'chapters_per_file': int(chapters_per_file) if chapters_per_file else 10,
            'verbose': False  # Could be made configurable
        }
        
        # Create progress callback
        def progress_callback(task_status):
            if progress:
                progress(task_status.progress, desc=task_status.current_stage)
        
        # Create console callback for status updates
        status_messages = []
        def console_callback(message):
            status_messages.append(message)
        
        # Generate audio with background support
        result = background_tts.generate_audio_sync_or_async(
            text=text,
            voice_prompt=voice_prompt,
            output_path=output_path,
            generation_params=generation_params,
            force_background=force_background,
            progress_callback=progress_callback,
            console_callback=console_callback
        )
        
        # Handle result based on processing mode
        if result['mode'] == 'synchronous':
            if result['status'] == 'completed':
                return (
                    gr.update(value=result['result_path'], visible=True),
                    gr.update(value=f"✅ {result['message']}", visible=True)
                )
            else:
                return (
                    gr.update(value=None, visible=True),
                    gr.update(value=f"❌ {result['message']}", visible=True)
                )
        else:  # background mode
            return (
                gr.update(value=None, visible=True),
                gr.update(value=f"⏳ {result['message']}", visible=True)
            )
    
    return enhanced_gen_single