"""
Voice sample manager for handling voice reference files.
"""

import os
import librosa
import soundfile as sf
from typing import List, Optional
from .models import VoiceSample
from ..config.enhanced_config import VoiceSampleConfig


class VoiceSampleManager:
    """Manages voice sample files and directory operations."""
    
    def __init__(self, config: Optional[VoiceSampleConfig] = None):
        """Initialize voice sample manager with configuration."""
        self.config = config or VoiceSampleConfig.default()
        self._ensure_samples_directory()
    
    def get_available_samples(self) -> List[VoiceSample]:
        """
        Get list of available voice samples.
        
        Returns:
            List of VoiceSample objects
        """
        samples = []
        
        if not os.path.exists(self.config.samples_directory):
            return samples
        
        try:
            for filename in os.listdir(self.config.samples_directory):
                filepath = os.path.join(self.config.samples_directory, filename)
                
                if os.path.isfile(filepath):
                    sample = self._create_voice_sample(filename, filepath)
                    if sample and sample.is_valid:
                        samples.append(sample)
        except Exception as e:
            print(f"Error reading samples directory: {e}")
        
        # Sort by filename
        samples.sort(key=lambda s: s.filename.lower())
        return samples
    
    def refresh_samples(self) -> List[VoiceSample]:
        """
        Refresh sample list and return updated list.
        
        Returns:
            Updated list of VoiceSample objects
        """
        return self.get_available_samples()
    
    def validate_sample(self, file_path: str) -> bool:
        """
        Validate audio sample format and quality.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if sample is valid, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        if ext not in self.config.supported_formats:
            return False
        
        # Check file size (basic validation)
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False
        except Exception:
            return False
        
        # Advanced audio validation
        try:
            # Try to load the audio file to verify it's valid
            if ext == 'wav':
                # Use soundfile for WAV files
                data, sample_rate = sf.read(file_path)
                if len(data) == 0:
                    return False
            elif ext == 'mp3':
                # Use librosa for MP3 files
                data, sample_rate = librosa.load(file_path, sr=None)
                if len(data) == 0:
                    return False
            
            # Check minimum duration (at least 0.1 seconds)
            duration = len(data) / sample_rate
            if duration < 0.1:
                return False
                
            # Check sample rate is reasonable (8kHz to 48kHz)
            if sample_rate < 8000 or sample_rate > 48000:
                return False
                
        except Exception as e:
            print(f"Audio validation failed for {file_path}: {e}")
            return False
        
        return True
    
    def add_sample(self, source_path: str, target_filename: Optional[str] = None) -> Optional[VoiceSample]:
        """
        Add a new voice sample to the samples directory.
        
        Args:
            source_path: Path to source audio file
            target_filename: Optional target filename (uses source filename if not provided)
            
        Returns:
            VoiceSample object if successful, None otherwise
        """
        if not self.validate_sample(source_path):
            return None
        
        if target_filename is None:
            target_filename = os.path.basename(source_path)
        
        target_path = os.path.join(self.config.samples_directory, target_filename)
        
        try:
            # Copy file to samples directory
            import shutil
            shutil.copy2(source_path, target_path)
            
            return self._create_voice_sample(target_filename, target_path)
        except Exception as e:
            print(f"Error adding sample {source_path}: {e}")
            return None
    
    def remove_sample(self, filename: str) -> bool:
        """
        Remove a voice sample from the samples directory.
        
        Args:
            filename: Name of the file to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        filepath = os.path.join(self.config.samples_directory, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error removing sample {filename}: {e}")
        
        return False
    
    def get_samples_directory(self) -> str:
        """Get the samples directory path."""
        return self.config.samples_directory
    
    def _ensure_samples_directory(self):
        """Ensure samples directory exists and populate with default samples if empty."""
        if self.config.auto_create_directory and not os.path.exists(self.config.samples_directory):
            try:
                os.makedirs(self.config.samples_directory, exist_ok=True)
                print(f"Created samples directory: {self.config.samples_directory}")
                
                # Copy default samples from examples directory if available
                self._populate_default_samples()
                
            except Exception as e:
                print(f"Error creating samples directory: {e}")
    
    def _populate_default_samples(self):
        """Populate samples directory with default samples from examples."""
        examples_dir = "examples"
        if not os.path.exists(examples_dir):
            return
        
        try:
            import shutil
            
            # Copy voice samples from examples directory
            for filename in os.listdir(examples_dir):
                if filename.startswith("voice_") and filename.endswith((".wav", ".mp3")):
                    source_path = os.path.join(examples_dir, filename)
                    target_path = os.path.join(self.config.samples_directory, filename)
                    
                    if not os.path.exists(target_path):
                        shutil.copy2(source_path, target_path)
                        print(f"Copied default sample: {filename}")
                        
        except Exception as e:
            print(f"Warning: Could not populate default samples: {e}")
    
    def _create_voice_sample(self, filename: str, filepath: str) -> Optional[VoiceSample]:
        """Create a VoiceSample object from file information."""
        try:
            file_size = os.path.getsize(filepath)
            _, ext = os.path.splitext(filename)
            ext = ext.lower().lstrip('.')
            
            # Extract audio metadata
            duration = None
            sample_rate = None
            
            try:
                if ext == 'wav':
                    data, sample_rate = sf.read(filepath)
                    duration = len(data) / sample_rate
                elif ext == 'mp3':
                    data, sample_rate = librosa.load(filepath, sr=None)
                    duration = len(data) / sample_rate
            except Exception as e:
                print(f"Warning: Could not extract audio metadata for {filename}: {e}")
            
            # Validate the sample
            is_valid = self.validate_sample(filepath)
            
            return VoiceSample(
                filename=filename,
                filepath=filepath,
                format=ext,
                file_size=file_size,
                duration=duration,
                sample_rate=sample_rate,
                created_at=None,  # Will be set in __post_init__
                is_valid=is_valid
            )
        except Exception as e:
            print(f"Error creating voice sample for {filename}: {e}")
            return None