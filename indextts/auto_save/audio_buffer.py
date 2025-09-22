"""
Audio buffer management for incremental auto-save functionality.
"""

import torch
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from .config import AudioSegmentInfo


class AudioBufferManager:
    """Manages audio segments for efficient concatenation and memory management."""
    
    def __init__(self, sampling_rate: int = 22050):
        """
        Initialize the audio buffer manager.
        
        Args:
            sampling_rate: Audio sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
        self.audio_segments: List[AudioSegmentInfo] = []
        self.total_duration = 0.0
        self.segment_metadata: List[Dict[str, Any]] = []
        self._buffer_stats = {
            'total_segments': 0,
            'total_samples': 0,
            'memory_usage_mb': 0.0,
            'last_cleanup': datetime.now()
        }
    
    def add_segment(self, audio: torch.Tensor, segment_info: Dict[str, Any]) -> AudioSegmentInfo:
        """
        Add audio segment with metadata.
        
        Args:
            audio: Audio tensor data
            segment_info: Dictionary containing segment metadata
            
        Returns:
            AudioSegmentInfo object for the added segment
        """
        # Calculate duration
        duration = audio.shape[-1] / self.sampling_rate
        
        # Create segment info
        segment = AudioSegmentInfo(
            segment_index=len(self.audio_segments),
            audio_data=audio.clone(),  # Clone to avoid reference issues
            duration=duration,
            text_content=segment_info.get('text', ''),
            generation_time=segment_info.get('generation_time', 0.0),
            timestamp=datetime.now()
        )
        
        # Add to buffer
        self.audio_segments.append(segment)
        self.total_duration += duration
        
        # Update statistics
        self._update_buffer_stats()
        
        return segment
    
    def concatenate_segments(self, start_idx: int = 0, end_idx: Optional[int] = None) -> torch.Tensor:
        """
        Concatenate audio segments efficiently.
        
        Args:
            start_idx: Starting segment index (inclusive)
            end_idx: Ending segment index (exclusive), None for all remaining
            
        Returns:
            Concatenated audio tensor
        """
        if not self.audio_segments:
            return torch.empty(0)
        
        if end_idx is None:
            end_idx = len(self.audio_segments)
        
        # Validate indices
        start_idx = max(0, start_idx)
        end_idx = min(len(self.audio_segments), end_idx)
        
        if start_idx >= end_idx:
            return torch.empty(0)
        
        # Get segments to concatenate
        segments_to_concat = self.audio_segments[start_idx:end_idx]
        
        if not segments_to_concat:
            return torch.empty(0)
        
        # Handle single segment case
        if len(segments_to_concat) == 1:
            return segments_to_concat[0].audio_data.clone()
        
        # Concatenate multiple segments
        audio_tensors = [segment.audio_data for segment in segments_to_concat]
        
        # Ensure all tensors have the same number of dimensions
        max_dims = max(tensor.dim() for tensor in audio_tensors)
        normalized_tensors = []
        
        for tensor in audio_tensors:
            while tensor.dim() < max_dims:
                tensor = tensor.unsqueeze(0)
            normalized_tensors.append(tensor)
        
        # Concatenate along the last dimension (time axis)
        concatenated = torch.cat(normalized_tensors, dim=-1)
        
        return concatenated
    
    def get_current_audio(self) -> torch.Tensor:
        """
        Get concatenated audio from all current segments.
        
        Returns:
            Complete concatenated audio tensor
        """
        return self.concatenate_segments()
    
    def clear_buffer(self):
        """Clear audio buffer and reset state."""
        # Clear references to help with garbage collection
        for segment in self.audio_segments:
            if hasattr(segment.audio_data, 'data'):
                del segment.audio_data
        
        self.audio_segments.clear()
        self.total_duration = 0.0
        self.segment_metadata.clear()
        
        # Reset statistics
        self._buffer_stats = {
            'total_segments': 0,
            'total_samples': 0,
            'memory_usage_mb': 0.0,
            'last_cleanup': datetime.now()
        }
        
        # Force garbage collection
        import gc
        gc.collect()
    
    def get_buffer_info(self) -> Dict[str, Any]:
        """
        Get current buffer statistics.
        
        Returns:
            Dictionary with buffer information
        """
        return {
            'segment_count': len(self.audio_segments),
            'total_duration': self.total_duration,
            'sampling_rate': self.sampling_rate,
            'memory_stats': self._buffer_stats.copy(),
            'latest_segment_time': self.audio_segments[-1].timestamp if self.audio_segments else None
        }
    
    def cleanup_processed_segments(self, keep_last_n: int = 1):
        """
        Clean up old segments to manage memory usage.
        
        Args:
            keep_last_n: Number of recent segments to keep in memory
        """
        if len(self.audio_segments) <= keep_last_n:
            return
        
        # Keep only the last N segments
        segments_to_remove = len(self.audio_segments) - keep_last_n
        
        # Clear references to removed segments
        for i in range(segments_to_remove):
            segment = self.audio_segments[i]
            if hasattr(segment.audio_data, 'data'):
                del segment.audio_data
        
        # Keep only recent segments
        self.audio_segments = self.audio_segments[-keep_last_n:]
        
        # Recalculate total duration
        self.total_duration = sum(segment.duration for segment in self.audio_segments)
        
        # Update statistics
        self._update_buffer_stats()
        
        # Force garbage collection
        import gc
        gc.collect()
    
    def get_segment_range(self, start_time: float, end_time: float) -> List[AudioSegmentInfo]:
        """
        Get segments within a specific time range.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            List of segments within the time range
        """
        result = []
        current_time = 0.0
        
        for segment in self.audio_segments:
            segment_end_time = current_time + segment.duration
            
            # Check if segment overlaps with requested range
            if (current_time < end_time and segment_end_time > start_time):
                result.append(segment)
            
            current_time = segment_end_time
            
            # Stop if we've passed the end time
            if current_time >= end_time:
                break
        
        return result
    
    def _update_buffer_stats(self):
        """Update internal buffer statistics."""
        total_samples = 0
        memory_usage = 0.0
        
        for segment in self.audio_segments:
            if hasattr(segment.audio_data, 'numel'):
                samples = segment.audio_data.numel()
                total_samples += samples
                
                # Estimate memory usage (assuming float32)
                memory_usage += samples * 4  # 4 bytes per float32
        
        self._buffer_stats.update({
            'total_segments': len(self.audio_segments),
            'total_samples': total_samples,
            'memory_usage_mb': memory_usage / (1024 * 1024),
            'last_update': datetime.now()
        })
    
    def estimate_memory_usage(self) -> float:
        """
        Estimate current memory usage in MB.
        
        Returns:
            Estimated memory usage in megabytes
        """
        return self._buffer_stats['memory_usage_mb']
    
    def get_segment_by_index(self, index: int) -> Optional[AudioSegmentInfo]:
        """
        Get segment by index.
        
        Args:
            index: Segment index
            
        Returns:
            AudioSegmentInfo or None if index is invalid
        """
        if 0 <= index < len(self.audio_segments):
            return self.audio_segments[index]
        return None