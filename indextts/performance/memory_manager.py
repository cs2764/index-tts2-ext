"""
Memory management and optimization for large file processing.
"""

import gc
import os
import psutil
import threading
import time
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_memory: int
    available_memory: int
    used_memory: int
    memory_percent: float
    process_memory: int
    process_percent: float


@dataclass
class MemoryThresholds:
    """Memory usage thresholds for optimization."""
    warning_threshold: float = 0.75  # 75% memory usage
    critical_threshold: float = 0.90  # 90% memory usage
    cleanup_threshold: float = 0.85   # 85% memory usage
    chunk_size_threshold: float = 0.70  # 70% memory usage for chunking


class MemoryManager:
    """Manages memory usage and provides optimization strategies."""
    
    def __init__(self, thresholds: Optional[MemoryThresholds] = None):
        """Initialize memory manager with thresholds."""
        self.thresholds = thresholds or MemoryThresholds()
        self.process = psutil.Process()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[MemoryStats], None]] = []
        self._lock = threading.Lock()
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics."""
        # System memory
        system_memory = psutil.virtual_memory()
        
        # Process memory
        process_memory = self.process.memory_info()
        
        return MemoryStats(
            total_memory=system_memory.total,
            available_memory=system_memory.available,
            used_memory=system_memory.used,
            memory_percent=system_memory.percent / 100.0,
            process_memory=process_memory.rss,
            process_percent=process_memory.rss / system_memory.total
        )
    
    def is_memory_critical(self) -> bool:
        """Check if memory usage is at critical level."""
        stats = self.get_memory_stats()
        return stats.memory_percent >= self.thresholds.critical_threshold
    
    def is_memory_warning(self) -> bool:
        """Check if memory usage is at warning level."""
        stats = self.get_memory_stats()
        return stats.memory_percent >= self.thresholds.warning_threshold
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup should be performed."""
        stats = self.get_memory_stats()
        return stats.memory_percent >= self.thresholds.cleanup_threshold
    
    def should_use_chunking(self) -> bool:
        """Check if file processing should use chunking."""
        stats = self.get_memory_stats()
        return stats.memory_percent >= self.thresholds.chunk_size_threshold
    
    def calculate_optimal_chunk_size(self, file_size: int, base_chunk_size: int = 1024 * 1024) -> int:
        """
        Calculate optimal chunk size based on available memory.
        
        Args:
            file_size: Size of file to process
            base_chunk_size: Base chunk size in bytes (default 1MB)
            
        Returns:
            Optimal chunk size in bytes
        """
        stats = self.get_memory_stats()
        available_mb = stats.available_memory / (1024 * 1024)
        
        # Use 10% of available memory for chunking, but not more than 100MB
        optimal_size = min(int(available_mb * 0.1 * 1024 * 1024), 100 * 1024 * 1024)
        
        # Ensure minimum chunk size
        optimal_size = max(optimal_size, base_chunk_size)
        
        # Don't make chunks larger than the file
        optimal_size = min(optimal_size, file_size)
        
        return optimal_size
    
    def force_cleanup(self):
        """Force garbage collection and memory cleanup."""
        # Force garbage collection
        gc.collect()
        
        # Additional cleanup for specific libraries if needed
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
    
    def start_monitoring(self, interval: float = 5.0):
        """
        Start memory monitoring in background thread.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def add_callback(self, callback: Callable[[MemoryStats], None]):
        """Add callback for memory status updates."""
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[MemoryStats], None]):
        """Remove callback for memory status updates."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _monitor_loop(self, interval: float):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                stats = self.get_memory_stats()
                
                # Check for automatic cleanup
                if self.should_cleanup():
                    self.force_cleanup()
                
                # Notify callbacks
                with self._lock:
                    for callback in self._callbacks:
                        try:
                            callback(stats)
                        except Exception as e:
                            print(f"Error in memory callback: {e}")
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in memory monitoring: {e}")
                time.sleep(interval)


class MemoryOptimizer:
    """Provides memory optimization strategies for different operations."""
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """Initialize with memory manager."""
        self.memory_manager = memory_manager or MemoryManager()
    
    @contextmanager
    def optimized_file_processing(self, file_size: int):
        """
        Context manager for optimized file processing.
        
        Args:
            file_size: Size of file being processed
        """
        # Pre-processing cleanup if needed
        if self.memory_manager.should_cleanup():
            self.memory_manager.force_cleanup()
        
        # Calculate optimal settings
        use_chunking = self.memory_manager.should_use_chunking()
        chunk_size = self.memory_manager.calculate_optimal_chunk_size(file_size)
        
        optimization_info = {
            'use_chunking': use_chunking,
            'chunk_size': chunk_size,
            'memory_stats': self.memory_manager.get_memory_stats()
        }
        
        try:
            yield optimization_info
        finally:
            # Post-processing cleanup
            self.memory_manager.force_cleanup()
    
    @contextmanager
    def optimized_text_processing(self, text_length: int):
        """
        Context manager for optimized text processing.
        
        Args:
            text_length: Length of text being processed
        """
        # Estimate memory usage (rough approximation)
        estimated_memory = text_length * 4  # 4 bytes per character (Unicode)
        
        # Pre-processing optimization
        if self.memory_manager.should_cleanup():
            self.memory_manager.force_cleanup()
        
        # Determine processing strategy
        use_streaming = estimated_memory > (50 * 1024 * 1024)  # 50MB threshold
        
        optimization_info = {
            'use_streaming': use_streaming,
            'estimated_memory': estimated_memory,
            'memory_stats': self.memory_manager.get_memory_stats()
        }
        
        try:
            yield optimization_info
        finally:
            # Cleanup after processing
            self.memory_manager.force_cleanup()
    
    @contextmanager
    def optimized_audio_processing(self, audio_duration: float, sample_rate: int = 22050):
        """
        Context manager for optimized audio processing.
        
        Args:
            audio_duration: Duration of audio in seconds
            sample_rate: Audio sample rate
        """
        # Estimate memory usage for audio
        estimated_samples = int(audio_duration * sample_rate)
        estimated_memory = estimated_samples * 4  # 4 bytes per float32 sample
        
        # Pre-processing optimization
        if self.memory_manager.should_cleanup():
            self.memory_manager.force_cleanup()
        
        # Determine processing strategy
        use_streaming = estimated_memory > (100 * 1024 * 1024)  # 100MB threshold
        segment_size = min(30.0, audio_duration / 4) if use_streaming else audio_duration
        
        optimization_info = {
            'use_streaming': use_streaming,
            'segment_size': segment_size,
            'estimated_memory': estimated_memory,
            'memory_stats': self.memory_manager.get_memory_stats()
        }
        
        try:
            yield optimization_info
        finally:
            # Cleanup after processing
            self.memory_manager.force_cleanup()
    
    def optimize_chapter_parsing(self, text_length: int) -> Dict[str, Any]:
        """
        Get optimization settings for chapter parsing.
        
        Args:
            text_length: Length of text to parse
            
        Returns:
            Dictionary with optimization settings
        """
        stats = self.memory_manager.get_memory_stats()
        
        # Adjust algorithm parameters based on memory
        if stats.memory_percent > 0.8:
            # High memory usage - use conservative settings
            return {
                'use_fast_scan': False,
                'cache_patterns': False,
                'max_candidates': 50,
                'batch_size': 100
            }
        elif stats.memory_percent > 0.6:
            # Medium memory usage - balanced settings
            return {
                'use_fast_scan': True,
                'cache_patterns': True,
                'max_candidates': 100,
                'batch_size': 500
            }
        else:
            # Low memory usage - aggressive optimization
            return {
                'use_fast_scan': True,
                'cache_patterns': True,
                'max_candidates': 200,
                'batch_size': 1000
            }
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory usage report."""
        stats = self.memory_manager.get_memory_stats()
        
        return {
            'memory_stats': {
                'total_gb': stats.total_memory / (1024**3),
                'available_gb': stats.available_memory / (1024**3),
                'used_percent': stats.memory_percent * 100,
                'process_mb': stats.process_memory / (1024**2),
                'process_percent': stats.process_percent * 100
            },
            'thresholds': {
                'warning': self.memory_manager.thresholds.warning_threshold * 100,
                'critical': self.memory_manager.thresholds.critical_threshold * 100,
                'cleanup': self.memory_manager.thresholds.cleanup_threshold * 100
            },
            'recommendations': self._get_memory_recommendations(stats)
        }
    
    def _get_memory_recommendations(self, stats: MemoryStats) -> List[str]:
        """Get memory optimization recommendations."""
        recommendations = []
        
        if stats.memory_percent >= self.memory_manager.thresholds.critical_threshold:
            recommendations.append("Critical memory usage - consider reducing file sizes or processing in smaller chunks")
        elif stats.memory_percent >= self.memory_manager.thresholds.warning_threshold:
            recommendations.append("High memory usage - enable chunked processing for large files")
        
        if stats.process_percent > 0.1:  # Process using more than 10% of system memory
            recommendations.append("High process memory usage - consider restarting the application periodically")
        
        if stats.available_memory < (1024**3):  # Less than 1GB available
            recommendations.append("Low available memory - close other applications or upgrade system memory")
        
        return recommendations


class ChunkedFileProcessor:
    """Processes large files in memory-efficient chunks."""
    
    def __init__(self, memory_optimizer: Optional[MemoryOptimizer] = None):
        """Initialize with memory optimizer."""
        self.memory_optimizer = memory_optimizer or MemoryOptimizer()
    
    def process_text_file_chunked(self, file_path: str, processor_func: Callable[[str], str]) -> str:
        """
        Process large text file in chunks to manage memory usage.
        
        Args:
            file_path: Path to text file
            processor_func: Function to process each chunk
            
        Returns:
            Processed text content
        """
        file_size = os.path.getsize(file_path)
        
        with self.memory_optimizer.optimized_file_processing(file_size) as opt_info:
            if not opt_info['use_chunking']:
                # Process entire file at once
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return processor_func(content)
            
            # Process in chunks
            chunk_size = opt_info['chunk_size']
            processed_chunks = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    processed_chunk = processor_func(chunk)
                    processed_chunks.append(processed_chunk)
                    
                    # Force cleanup between chunks if memory is high
                    if self.memory_optimizer.memory_manager.should_cleanup():
                        self.memory_optimizer.memory_manager.force_cleanup()
            
            return ''.join(processed_chunks)
    
    def process_audio_segments_chunked(self, segments: List[str], 
                                     processor_func: Callable[[List[str]], str]) -> List[str]:
        """
        Process audio segments in memory-efficient batches.
        
        Args:
            segments: List of audio segment paths
            processor_func: Function to process each batch
            
        Returns:
            List of processed segment paths
        """
        if not segments:
            return []
        
        # Estimate total processing memory
        total_duration = len(segments) * 30.0  # Assume 30 seconds per segment
        
        with self.memory_optimizer.optimized_audio_processing(total_duration) as opt_info:
            if not opt_info['use_streaming']:
                # Process all segments at once
                return [processor_func(segments)]
            
            # Process in batches
            batch_size = max(1, len(segments) // 4)  # Process in 4 batches
            processed_segments = []
            
            for i in range(0, len(segments), batch_size):
                batch = segments[i:i + batch_size]
                processed_batch = processor_func(batch)
                processed_segments.extend(processed_batch if isinstance(processed_batch, list) else [processed_batch])
                
                # Cleanup between batches
                if self.memory_optimizer.memory_manager.should_cleanup():
                    self.memory_optimizer.memory_manager.force_cleanup()
            
            return processed_segments