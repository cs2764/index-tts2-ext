"""
Optimized audio segmentation with minimal memory usage.
"""

import os
import time
import tempfile
import threading
from typing import List, Dict, Optional, Tuple, Iterator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import librosa
import soundfile as sf
from ..audio_formats.models import AudiobookChapter, SegmentationConfig


@dataclass
class AudioOptimizationMetrics:
    """Metrics for audio segmentation optimization."""
    total_time: float
    segmentation_time: float
    conversion_time: float
    io_time: float
    memory_peak_mb: float
    segments_created: int
    optimization_level: str


class AudioSegmentationOptimizer:
    """Optimized audio segmentation with memory efficiency."""
    
    def __init__(self, enable_streaming: bool = True, max_workers: int = 2):
        """
        Initialize audio segmentation optimizer.
        
        Args:
            enable_streaming: Whether to use streaming processing
            max_workers: Maximum number of worker threads
        """
        self.enable_streaming = enable_streaming
        self.max_workers = max_workers
        self.metrics = AudioOptimizationMetrics(0, 0, 0, 0, 0, 0, "none")
        self._temp_files: List[str] = []
        self._lock = threading.Lock()
    
    def optimize_audio_segmentation(self, audio_path: str, chapters: List[AudiobookChapter],
                                  config: SegmentationConfig, output_dir: str,
                                  optimization_settings: Dict[str, any]) -> Tuple[List[str], AudioOptimizationMetrics]:
        """
        Perform optimized audio segmentation.
        
        Args:
            audio_path: Path to source audio file
            chapters: List of chapters for segmentation
            config: Segmentation configuration
            output_dir: Output directory for segments
            optimization_settings: Optimization configuration
            
        Returns:
            Tuple of (segment_paths, metrics)
        """
        start_time = time.time()
        
        try:
            # Determine optimization strategy
            use_streaming = optimization_settings.get('use_streaming', True)
            segment_size = optimization_settings.get('segment_size', 30.0)
            estimated_memory = optimization_settings.get('estimated_memory', 0)
            
            optimization_level = self._determine_optimization_level(optimization_settings)
            
            # Get audio info efficiently
            io_start = time.time()
            audio_info = self._get_audio_info_fast(audio_path)
            io_time = time.time() - io_start
            
            # Choose segmentation strategy
            if use_streaming or estimated_memory > 100 * 1024 * 1024:  # 100MB threshold
                segment_paths = self._streaming_segmentation(
                    audio_path, chapters, config, output_dir, audio_info
                )
            else:
                segment_paths = self._memory_segmentation(
                    audio_path, chapters, config, output_dir, audio_info
                )
            
            total_time = time.time() - start_time
            
            # Create metrics
            self.metrics = AudioOptimizationMetrics(
                total_time=total_time,
                segmentation_time=total_time - io_time,
                conversion_time=0,  # Will be updated by specific methods
                io_time=io_time,
                memory_peak_mb=self._estimate_memory_usage(audio_info),
                segments_created=len(segment_paths),
                optimization_level=optimization_level
            )
            
            return segment_paths, self.metrics
            
        except Exception as e:
            print(f"Audio optimization failed, using fallback: {e}")
            return self._fallback_segmentation(audio_path, chapters, config, output_dir), self.metrics
    
    def _streaming_segmentation(self, audio_path: str, chapters: List[AudiobookChapter],
                              config: SegmentationConfig, output_dir: str,
                              audio_info: Dict) -> List[str]:
        """Streaming segmentation for large audio files."""
        segment_paths = []
        
        # Create output directory
        segment_dir = self._create_segment_directory(audio_path, output_dir, config)
        
        # Group chapters
        chapter_groups = self._group_chapters_optimized(chapters, config.chapters_per_file)
        
        # Process each group with streaming
        for i, chapter_group in enumerate(chapter_groups):
            segment_path = self._create_streaming_segment(
                audio_path, chapter_group, i, segment_dir, config, audio_info
            )
            segment_paths.append(segment_path)
        
        return segment_paths
    
    def _memory_segmentation(self, audio_path: str, chapters: List[AudiobookChapter],
                           config: SegmentationConfig, output_dir: str,
                           audio_info: Dict) -> List[str]:
        """In-memory segmentation for smaller audio files."""
        segment_paths = []
        
        # Load entire audio file into memory
        audio_data, sample_rate = librosa.load(audio_path, sr=None)
        
        # Create output directory
        segment_dir = self._create_segment_directory(audio_path, output_dir, config)
        
        # Group chapters
        chapter_groups = self._group_chapters_optimized(chapters, config.chapters_per_file)
        
        # Process each group in memory
        for i, chapter_group in enumerate(chapter_groups):
            segment_path = self._create_memory_segment(
                audio_data, sample_rate, chapter_group, i, segment_dir, config, audio_path
            )
            segment_paths.append(segment_path)
        
        return segment_paths
    
    def _create_streaming_segment(self, audio_path: str, chapter_group: List[AudiobookChapter],
                                group_index: int, output_dir: str, config: SegmentationConfig,
                                audio_info: Dict) -> str:
        """Create audio segment using streaming approach."""
        if not chapter_group:
            raise ValueError("Empty chapter group")
        
        # Calculate segment timing
        start_time = chapter_group[0].start_time
        end_time = chapter_group[-1].end_time
        duration = end_time - start_time
        
        # Generate output filename
        segment_filename = self._generate_segment_filename(
            audio_path, group_index, chapter_group, config
        )
        segment_path = os.path.join(output_dir, segment_filename)
        
        # Use streaming approach with temporary file
        temp_segment = self._create_temp_file('.wav')
        
        try:
            # Stream audio segment using librosa with offset and duration
            audio_segment, sample_rate = librosa.load(
                audio_path, 
                sr=None, 
                offset=start_time, 
                duration=duration
            )
            
            # Save to temporary file first
            sf.write(temp_segment, audio_segment, sample_rate, subtype='PCM_16')
            
            # Move to final location
            os.rename(temp_segment, segment_path)
            
            return segment_path
            
        except Exception as e:
            # Cleanup temporary file on error
            if os.path.exists(temp_segment):
                os.remove(temp_segment)
            raise RuntimeError(f"Streaming segment creation failed: {str(e)}")
    
    def _create_memory_segment(self, audio_data: np.ndarray, sample_rate: int,
                             chapter_group: List[AudiobookChapter], group_index: int,
                             output_dir: str, config: SegmentationConfig,
                             original_path: str) -> str:
        """Create audio segment using in-memory approach."""
        if not chapter_group:
            raise ValueError("Empty chapter group")
        
        # Calculate sample indices
        start_sample = int(chapter_group[0].start_time * sample_rate)
        end_sample = int(chapter_group[-1].end_time * sample_rate)
        
        # Extract segment
        segment_data = audio_data[start_sample:end_sample]
        
        # Generate output filename
        segment_filename = self._generate_segment_filename(
            original_path, group_index, chapter_group, config
        )
        segment_path = os.path.join(output_dir, segment_filename)
        
        # Save segment
        sf.write(segment_path, segment_data, sample_rate, subtype='PCM_16')
        
        return segment_path
    
    def _group_chapters_optimized(self, chapters: List[AudiobookChapter], 
                                chapters_per_file: int) -> List[List[AudiobookChapter]]:
        """Optimized chapter grouping with load balancing."""
        if not chapters:
            return []
        
        # Validate and clamp chapters_per_file
        chapters_per_file = max(1, min(100, chapters_per_file))
        
        # Simple grouping for now - can be enhanced with duration balancing
        groups = []
        for i in range(0, len(chapters), chapters_per_file):
            group = chapters[i:i + chapters_per_file]
            groups.append(group)
        
        return groups
    
    def _get_audio_info_fast(self, audio_path: str) -> Dict:
        """Get audio information efficiently without loading full file."""
        try:
            # Use librosa to get basic info without loading audio data
            duration = librosa.get_duration(path=audio_path)
            
            # Get sample rate from file header
            with sf.SoundFile(audio_path) as f:
                sample_rate = f.samplerate
                channels = f.channels
                frames = f.frames
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'frames': frames,
                'format': os.path.splitext(audio_path)[1].lower().lstrip('.')
            }
        except Exception as e:
            # Fallback to basic info
            return {
                'duration': 0.0,
                'sample_rate': 22050,
                'channels': 1,
                'frames': 0,
                'format': 'wav'
            }
    
    def _create_segment_directory(self, audio_path: str, output_dir: str, 
                                config: SegmentationConfig) -> str:
        """Create organized directory structure for segments."""
        # Always use output_dir directly - never create subfolders
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def _generate_segment_filename(self, audio_path: str, group_index: int,
                                 chapter_group: List[AudiobookChapter],
                                 config: SegmentationConfig) -> str:
        """Generate filename for audio segment."""
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Calculate chapter range
        first_chapter = group_index * config.chapters_per_file + 1
        last_chapter = first_chapter + len(chapter_group) - 1
        
        return f"{base_name}_{first_chapter:03d}-{last_chapter:03d}.wav"
    
    def _create_temp_file(self, suffix: str = '.wav') -> str:
        """Create temporary file and track it for cleanup."""
        temp_file = tempfile.mktemp(suffix=suffix)
        with self._lock:
            self._temp_files.append(temp_file)
        return temp_file
    
    def _estimate_memory_usage(self, audio_info: Dict) -> float:
        """Estimate peak memory usage in MB."""
        duration = audio_info.get('duration', 0)
        sample_rate = audio_info.get('sample_rate', 22050)
        channels = audio_info.get('channels', 1)
        
        # Estimate memory for float32 audio data
        samples = duration * sample_rate * channels
        memory_bytes = samples * 4  # 4 bytes per float32
        memory_mb = memory_bytes / (1024 * 1024)
        
        return memory_mb
    
    def _determine_optimization_level(self, settings: Dict[str, any]) -> str:
        """Determine optimization level based on settings."""
        use_streaming = settings.get('use_streaming', False)
        estimated_memory = settings.get('estimated_memory', 0)
        
        if use_streaming and estimated_memory > 200 * 1024 * 1024:  # 200MB
            return "aggressive_streaming"
        elif use_streaming:
            return "moderate_streaming"
        elif estimated_memory > 100 * 1024 * 1024:  # 100MB
            return "memory_conscious"
        else:
            return "standard_memory"
    
    def _fallback_segmentation(self, audio_path: str, chapters: List[AudiobookChapter],
                             config: SegmentationConfig, output_dir: str) -> List[str]:
        """Fallback segmentation using basic approach."""
        segment_paths = []
        
        try:
            # Simple fallback - create one segment per chapter
            segment_dir = self._create_segment_directory(audio_path, output_dir, config)
            
            for i, chapter in enumerate(chapters):
                # Load and save each chapter individually
                audio_segment, sample_rate = librosa.load(
                    audio_path,
                    sr=None,
                    offset=chapter.start_time,
                    duration=chapter.end_time - chapter.start_time
                )
                
                segment_filename = f"chapter_{i+1:03d}.wav"
                segment_path = os.path.join(segment_dir, segment_filename)
                
                sf.write(segment_path, audio_segment, sample_rate)
                segment_paths.append(segment_path)
                
        except Exception as e:
            print(f"Fallback segmentation failed: {e}")
        
        return segment_paths
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        with self._lock:
            for temp_file in self._temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error cleaning up temp file {temp_file}: {e}")
            self._temp_files.clear()
    
    def get_optimization_report(self) -> Dict[str, any]:
        """Get audio optimization performance report."""
        if self.metrics.total_time == 0:
            return {"status": "No optimization performed yet"}
        
        return {
            "performance": {
                "total_time": f"{self.metrics.total_time:.3f}s",
                "segmentation_time": f"{self.metrics.segmentation_time:.3f}s",
                "io_time": f"{self.metrics.io_time:.3f}s",
                "memory_peak_mb": f"{self.metrics.memory_peak_mb:.1f}MB"
            },
            "results": {
                "segments_created": self.metrics.segments_created,
                "avg_time_per_segment": f"{self.metrics.segmentation_time / max(1, self.metrics.segments_created):.3f}s"
            },
            "optimization": {
                "level": self.metrics.optimization_level,
                "streaming_enabled": self.enable_streaming,
                "max_workers": self.max_workers,
                "temp_files_created": len(self._temp_files)
            }
        }


class ParallelAudioProcessor:
    """Parallel audio processing for multiple segments."""
    
    def __init__(self, max_workers: int = 2):
        """Initialize parallel processor."""
        self.max_workers = max_workers
    
    def process_segments_parallel(self, segment_tasks: List[Dict], 
                                processor_func: callable) -> List[str]:
        """
        Process multiple audio segments in parallel.
        
        Args:
            segment_tasks: List of segment processing tasks
            processor_func: Function to process each segment
            
        Returns:
            List of processed segment paths
        """
        if not segment_tasks:
            return []
        
        processed_segments = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(processor_func, task): i 
                for i, task in enumerate(segment_tasks)
            }
            
            # Collect results in order
            results = [None] * len(segment_tasks)
            
            for future in as_completed(futures):
                task_index = futures[future]
                try:
                    result = future.result()
                    results[task_index] = result
                except Exception as e:
                    print(f"Error processing segment {task_index}: {e}")
                    results[task_index] = None
            
            # Filter out failed results
            processed_segments = [r for r in results if r is not None]
        
        return processed_segments


class StreamingAudioReader:
    """Streaming audio reader for memory-efficient processing."""
    
    def __init__(self, audio_path: str, chunk_duration: float = 30.0):
        """
        Initialize streaming reader.
        
        Args:
            audio_path: Path to audio file
            chunk_duration: Duration of each chunk in seconds
        """
        self.audio_path = audio_path
        self.chunk_duration = chunk_duration
        self.audio_info = self._get_audio_info()
        self.current_position = 0.0
    
    def _get_audio_info(self) -> Dict:
        """Get audio file information."""
        try:
            duration = librosa.get_duration(path=self.audio_path)
            with sf.SoundFile(self.audio_path) as f:
                sample_rate = f.samplerate
                channels = f.channels
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels
            }
        except Exception:
            return {
                'duration': 0.0,
                'sample_rate': 22050,
                'channels': 1
            }
    
    def read_chunks(self) -> Iterator[Tuple[np.ndarray, float, float]]:
        """
        Read audio in chunks.
        
        Yields:
            Tuple of (audio_data, start_time, end_time)
        """
        total_duration = self.audio_info['duration']
        
        while self.current_position < total_duration:
            # Calculate chunk boundaries
            start_time = self.current_position
            end_time = min(start_time + self.chunk_duration, total_duration)
            chunk_duration = end_time - start_time
            
            try:
                # Load chunk
                audio_chunk, _ = librosa.load(
                    self.audio_path,
                    sr=self.audio_info['sample_rate'],
                    offset=start_time,
                    duration=chunk_duration
                )
                
                yield audio_chunk, start_time, end_time
                
            except Exception as e:
                print(f"Error reading chunk at {start_time}s: {e}")
                break
            
            self.current_position = end_time
    
    def read_segment(self, start_time: float, end_time: float) -> np.ndarray:
        """
        Read specific audio segment.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Audio data as numpy array
        """
        duration = end_time - start_time
        
        try:
            audio_data, _ = librosa.load(
                self.audio_path,
                sr=self.audio_info['sample_rate'],
                offset=start_time,
                duration=duration
            )
            return audio_data
        except Exception as e:
            print(f"Error reading segment {start_time}-{end_time}s: {e}")
            return np.array([])