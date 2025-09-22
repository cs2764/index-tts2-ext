"""
Output file manager for organizing generated audio files.
"""

import os
import time
from datetime import datetime
from typing import List, Optional
from .models import OutputFile, SegmentedOutput
from ..config.enhanced_config import OutputConfig


class OutputManager:
    """Manages output files and directory organization."""
    
    def __init__(self, config: Optional[OutputConfig] = None):
        """Initialize output manager with configuration."""
        self.config = config or OutputConfig.default()
        self._auto_save_enabled = self.config.auto_save_enabled
        self._ensure_output_directory()
    
    def generate_filename(self, source_file: Optional[str], voice_name: str, 
                         format_ext: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate standardized filename with date and voice name.
        
        Args:
            source_file: Original source filename (can be None for direct text input)
            voice_name: Name of the voice used
            format_ext: File extension (without dot)
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            Generated filename
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        if source_file:
            # Remove extension from source file
            base_name = os.path.splitext(os.path.basename(source_file))[0]
            filename = f"{base_name}_{date_str}_{voice_name}.{format_ext}"
        else:
            # Direct text input
            filename = f"generation_{date_str}_{voice_name}.{format_ext}"
        
        return filename
    
    def save_audio_file(self, audio_data: bytes, filename: str, 
                       source_filename: Optional[str] = None,
                       voice_name: Optional[str] = None) -> OutputFile:
        """
        Save audio data to file and create OutputFile record.
        
        Args:
            audio_data: Audio data to save
            filename: Target filename
            source_filename: Original source filename
            voice_name: Voice name used for generation
            
        Returns:
            OutputFile object
        """
        filepath = os.path.join(self.config.output_directory, filename)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write audio data
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        # Get file information
        file_size = os.path.getsize(filepath)
        _, ext = os.path.splitext(filename)
        ext = ext.lower().lstrip('.')
        
        return OutputFile(
            filename=filename,
            filepath=filepath,
            format=ext,
            file_size=file_size,
            duration=None,  # TODO: Extract actual duration
            source_filename=source_filename,
            voice_name=voice_name,
            created_at=None,  # Will be set in __post_init__
            is_segmented=False,
            segment_info=None
        )
    
    def save_audio_segments(self, segments_data: List[bytes], base_filename: str,
                          format_ext: str, chapters_per_file: int = 10,
                          source_filename: Optional[str] = None,
                          voice_name: Optional[str] = None) -> SegmentedOutput:
        """
        Save segmented audio files in organized folder structure.
        
        Args:
            segments_data: List of audio data for each segment
            base_filename: Base filename for the segments
            format_ext: File extension
            chapters_per_file: Number of chapters per file
            source_filename: Original source filename
            voice_name: Voice name used for generation
            
        Returns:
            SegmentedOutput object with information about all segments
        """
        # Save segments directly to outputs folder (no subfolders)
        folder_name = self.config.output_directory
        
        segments = []
        total_segments = len(segments_data)
        
        for i, audio_data in enumerate(segments_data):
            # Calculate chapter range for this segment
            start_chapter = (i * chapters_per_file) + 1
            end_chapter = (i + 1) * chapters_per_file
            
            # Generate segment filename
            if total_segments > 1:
                segment_filename = f"{start_chapter}-{end_chapter}.{format_ext}"
            else:
                segment_filename = f"{base_filename}.{format_ext}"
            
            segment_filepath = os.path.join(folder_name, segment_filename)
            
            # Save segment
            with open(segment_filepath, 'wb') as f:
                f.write(audio_data)
            
            # Create OutputFile record
            file_size = os.path.getsize(segment_filepath)
            segment = OutputFile(
                filename=segment_filename,
                filepath=segment_filepath,
                format=format_ext,
                file_size=file_size,
                duration=None,  # TODO: Extract actual duration
                source_filename=source_filename,
                voice_name=voice_name,
                created_at=None,  # Will be set in __post_init__
                is_segmented=True,
                segment_info={
                    'start_chapter': start_chapter,
                    'end_chapter': end_chapter,
                    'segment_index': i,
                    'total_segments': total_segments
                }
            )
            segments.append(segment)
        
        return SegmentedOutput(
            base_filename=base_filename,
            output_directory=folder_name,
            segments=segments,
            total_duration=None,  # TODO: Calculate total duration
            created_at=None  # Will be set in __post_init__
        )
    
    def create_output_folder(self, base_filename: str, 
                           timestamp: Optional[datetime] = None,
                           voice_name: Optional[str] = None) -> str:
        """
        Return output directory path (no subfolders created).
        
        Args:
            base_filename: Base filename for the folder (ignored)
            timestamp: Optional timestamp (ignored)
            voice_name: Optional voice name (ignored)
            
        Returns:
            Path to output directory (no subfolders)
        """
        # Always return the main output directory - don't create subfolders
        os.makedirs(self.config.output_directory, exist_ok=True)
        return self.config.output_directory
    
    def get_output_files(self) -> List[OutputFile]:
        """
        Get list of all output files.
        
        Returns:
            List of OutputFile objects
        """
        output_files = []
        
        if not os.path.exists(self.config.output_directory):
            return output_files
        
        try:
            for root, dirs, files in os.walk(self.config.output_directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    # Skip non-audio files
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower().lstrip('.')
                    if ext not in ['wav', 'mp3', 'm4b']:
                        continue
                    
                    # Create OutputFile object
                    file_size = os.path.getsize(filepath)
                    is_segmented = root != self.config.output_directory
                    
                    output_file = OutputFile(
                        filename=filename,
                        filepath=filepath,
                        format=ext,
                        file_size=file_size,
                        duration=None,  # TODO: Extract actual duration
                        source_filename=None,  # TODO: Extract from metadata
                        voice_name=None,  # TODO: Extract from metadata
                        created_at=datetime.fromtimestamp(os.path.getctime(filepath)),
                        is_segmented=is_segmented,
                        segment_info=None
                    )
                    output_files.append(output_file)
        except Exception as e:
            print(f"Error reading output files: {e}")
        
        # Sort by creation time (newest first)
        output_files.sort(key=lambda f: f.created_at, reverse=True)
        return output_files
    
    def cleanup_old_files(self, max_age_days: int = 30):
        """
        Clean up old output files.
        
        Args:
            max_age_days: Maximum age of files to keep in days
        """
        if not os.path.exists(self.config.output_directory):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        try:
            for root, dirs, files in os.walk(self.config.output_directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    # Check file age
                    file_age = current_time - os.path.getctime(filepath)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(filepath)
                            print(f"Removed old file: {filepath}")
                        except Exception as e:
                            print(f"Error removing file {filepath}: {e}")
                
                # Remove empty directories
                if root != self.config.output_directory:
                    try:
                        if not os.listdir(root):
                            os.rmdir(root)
                            print(f"Removed empty directory: {root}")
                    except Exception as e:
                        print(f"Error removing directory {root}: {e}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    @property
    def auto_save_enabled(self) -> bool:
        """Get current auto-save status."""
        return self._auto_save_enabled
    
    def set_auto_save(self, enabled: bool):
        """
        Set auto-save functionality on/off.
        
        Args:
            enabled: Whether to enable auto-save
        """
        self._auto_save_enabled = enabled
    
    def should_auto_save(self) -> bool:
        """
        Check if auto-save should be performed.
        
        Returns:
            True if auto-save is enabled, False otherwise
        """
        return self._auto_save_enabled
    
    def _ensure_output_directory(self):
        """Ensure output directory exists."""
        if not os.path.exists(self.config.output_directory):
            try:
                os.makedirs(self.config.output_directory, exist_ok=True)
                print(f"Created output directory: {self.config.output_directory}")
            except Exception as e:
                print(f"Error creating output directory: {e}")