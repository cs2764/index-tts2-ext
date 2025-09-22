"""
Performance optimizations for file preview generation and caching.
"""

import os
import time
import hashlib
import threading
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from ..file_processing.models import FilePreview


@dataclass
class PreviewCacheEntry:
    """Cache entry for file preview data."""
    preview: FilePreview
    file_path: str
    file_size: int
    file_mtime: float
    created_at: datetime
    access_count: int
    last_accessed: datetime


@dataclass
class PreviewMetrics:
    """Metrics for preview generation performance."""
    generation_time: float
    cache_hit: bool
    file_size: int
    lines_processed: int
    encoding_detection_time: float
    text_processing_time: float


class PreviewCache:
    """Thread-safe cache for file previews with automatic cleanup."""
    
    def __init__(self, max_entries: int = 50, max_age_hours: int = 24):
        """
        Initialize preview cache.
        
        Args:
            max_entries: Maximum number of cache entries
            max_age_hours: Maximum age of cache entries in hours
        """
        self.max_entries = max_entries
        self.max_age = timedelta(hours=max_age_hours)
        self._cache: Dict[str, PreviewCacheEntry] = {}
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_interval = 300  # 5 minutes
        self._running = True
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def get(self, file_path: str) -> Optional[FilePreview]:
        """
        Get cached preview for file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cached FilePreview if valid, None otherwise
        """
        cache_key = self._get_cache_key(file_path)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                return None
            
            # Check if file has been modified
            if not self._is_entry_valid(entry, file_path):
                del self._cache[cache_key]
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            return entry.preview
    
    def put(self, file_path: str, preview: FilePreview) -> None:
        """
        Cache preview for file.
        
        Args:
            file_path: Path to the file
            preview: FilePreview to cache
        """
        cache_key = self._get_cache_key(file_path)
        
        try:
            stat = os.stat(file_path)
            file_size = stat.st_size
            file_mtime = stat.st_mtime
        except OSError:
            return  # Can't cache if file doesn't exist
        
        entry = PreviewCacheEntry(
            preview=preview,
            file_path=file_path,
            file_size=file_size,
            file_mtime=file_mtime,
            created_at=datetime.now(),
            access_count=1,
            last_accessed=datetime.now()
        )
        
        with self._lock:
            self._cache[cache_key] = entry
            
            # Cleanup if cache is too large
            if len(self._cache) > self.max_entries:
                self._cleanup_old_entries()
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            total_access_count = sum(entry.access_count for entry in self._cache.values())
            
            if total_entries > 0:
                avg_access_count = total_access_count / total_entries
                oldest_entry = min(self._cache.values(), key=lambda x: x.created_at)
                newest_entry = max(self._cache.values(), key=lambda x: x.created_at)
            else:
                avg_access_count = 0
                oldest_entry = None
                newest_entry = None
            
            return {
                'total_entries': total_entries,
                'max_entries': self.max_entries,
                'total_access_count': total_access_count,
                'avg_access_count': avg_access_count,
                'oldest_entry_age': (datetime.now() - oldest_entry.created_at).total_seconds() / 3600 if oldest_entry else 0,
                'newest_entry_age': (datetime.now() - newest_entry.created_at).total_seconds() / 3600 if newest_entry else 0
            }
    
    def shutdown(self) -> None:
        """Shutdown cache and cleanup thread."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=1.0)
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key for file path."""
        # Use absolute path for consistent caching
        abs_path = os.path.abspath(file_path)
        return hashlib.md5(abs_path.encode('utf-8')).hexdigest()
    
    def _is_entry_valid(self, entry: PreviewCacheEntry, file_path: str) -> bool:
        """Check if cache entry is still valid."""
        # Check age
        if datetime.now() - entry.created_at > self.max_age:
            return False
        
        # Check if file still exists and hasn't been modified
        try:
            stat = os.stat(file_path)
            return (stat.st_size == entry.file_size and 
                   stat.st_mtime == entry.file_mtime)
        except OSError:
            return False  # File doesn't exist anymore
    
    def _cleanup_old_entries(self) -> None:
        """Remove old or least accessed entries."""
        if not self._cache:
            return
        
        # Remove expired entries first
        expired_keys = []
        for key, entry in self._cache.items():
            if datetime.now() - entry.created_at > self.max_age:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        # If still too many entries, remove least accessed
        if len(self._cache) > self.max_entries:
            # Sort by access count (ascending) and last accessed (ascending)
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: (x[1].access_count, x[1].last_accessed)
            )
            
            # Remove oldest entries
            entries_to_remove = len(self._cache) - self.max_entries
            for i in range(entries_to_remove):
                key = sorted_entries[i][0]
                del self._cache[key]
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        def cleanup_loop():
            while self._running:
                try:
                    time.sleep(self._cleanup_interval)
                    if self._running:
                        with self._lock:
                            self._cleanup_old_entries()
                except Exception as e:
                    print(f"Error in preview cache cleanup: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()


class PreviewOptimizer:
    """Optimizes file preview generation with caching and performance improvements."""
    
    def __init__(self, cache: Optional[PreviewCache] = None, 
                 memory_optimizer=None):
        """
        Initialize preview optimizer.
        
        Args:
            cache: Preview cache instance
            memory_optimizer: Memory optimizer instance
        """
        self.cache = cache or PreviewCache()
        self.memory_optimizer = memory_optimizer
        self._metrics_history: List[PreviewMetrics] = []
    
    def generate_optimized_preview(self, file_path: str, preview_lines: int = 40,
                                 force_regenerate: bool = False) -> Tuple[FilePreview, PreviewMetrics]:
        """
        Generate optimized file preview with caching.
        
        Args:
            file_path: Path to the file
            preview_lines: Number of lines to include in preview
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Tuple of (FilePreview, PreviewMetrics)
        """
        start_time = time.time()
        
        # Check cache first
        if not force_regenerate:
            cached_preview = self.cache.get(file_path)
            if cached_preview is not None:
                metrics = PreviewMetrics(
                    generation_time=time.time() - start_time,
                    cache_hit=True,
                    file_size=cached_preview.file_size,
                    lines_processed=cached_preview.total_lines,
                    encoding_detection_time=0.0,
                    text_processing_time=0.0
                )
                self._metrics_history.append(metrics)
                return cached_preview, metrics
        
        # Generate new preview
        preview, metrics = self._generate_preview_with_metrics(file_path, preview_lines)
        
        # Cache the result
        self.cache.put(file_path, preview)
        
        # Update metrics
        metrics.generation_time = time.time() - start_time
        metrics.cache_hit = False
        self._metrics_history.append(metrics)
        
        # Limit metrics history
        if len(self._metrics_history) > 100:
            self._metrics_history = self._metrics_history[-50:]
        
        return preview, metrics
    
    def _generate_preview_with_metrics(self, file_path: str, 
                                     preview_lines: int) -> Tuple[FilePreview, PreviewMetrics]:
        """Generate preview with detailed performance metrics."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        file_size = os.path.getsize(file_path)
        
        # Initialize metrics
        encoding_time = 0.0
        processing_time = 0.0
        lines_processed = 0
        
        # Use memory-optimized processing for large files
        if self.memory_optimizer and file_size > 5 * 1024 * 1024:  # 5MB threshold
            with self.memory_optimizer.optimized_file_processing(file_size) as opt_info:
                preview_text, encoding, total_lines, enc_time, proc_time = self._generate_large_file_preview(
                    file_path, file_ext, preview_lines, opt_info
                )
                encoding_time = enc_time
                processing_time = proc_time
                lines_processed = min(preview_lines, total_lines)
        else:
            # Standard preview generation
            preview_text, encoding, total_lines, enc_time, proc_time = self._generate_standard_preview(
                file_path, file_ext, preview_lines
            )
            encoding_time = enc_time
            processing_time = proc_time
            lines_processed = min(preview_lines, total_lines)
        
        # Determine if preview was truncated
        preview_truncated = total_lines > preview_lines
        
        # Format file size for display
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        preview = FilePreview(
            filename=filename,
            preview_text=preview_text,
            total_lines=total_lines,
            encoding=encoding,
            file_size=size_str,
            preview_truncated=preview_truncated
        )
        
        metrics = PreviewMetrics(
            generation_time=0.0,  # Will be set by caller
            cache_hit=False,
            file_size=file_size,
            lines_processed=lines_processed,
            encoding_detection_time=encoding_time,
            text_processing_time=processing_time
        )
        
        return preview, metrics
    
    def _generate_large_file_preview(self, file_path: str, file_ext: str, 
                                   preview_lines: int, opt_info: Dict[str, Any]) -> Tuple[str, str, int, float, float]:
        """Generate preview for large files using optimized processing."""
        encoding_start = time.time()
        
        if file_ext == 'txt':
            encoding = self._detect_encoding_optimized(file_path)
        else:
            encoding = 'utf-8'  # EPUB is always UTF-8
        
        encoding_time = time.time() - encoding_start
        
        processing_start = time.time()
        
        # Read only the first part of the file for preview
        preview_text = ""
        total_lines = 0
        lines_read = 0
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                # Read file line by line until we have enough for preview
                while lines_read < preview_lines * 2:  # Read extra to count total
                    line = f.readline()
                    if not line:
                        break
                    
                    if lines_read < preview_lines:
                        preview_text += line
                    
                    lines_read += 1
                
                # Count remaining lines efficiently
                remaining_lines = sum(1 for _ in f)
                total_lines = lines_read + remaining_lines
        
        except Exception as e:
            # Fallback to basic reading
            preview_text = f"Error reading file: {e}"
            total_lines = 0
        
        processing_time = time.time() - processing_start
        
        return preview_text, encoding, total_lines, encoding_time, processing_time
    
    def _generate_standard_preview(self, file_path: str, file_ext: str, 
                                 preview_lines: int) -> Tuple[str, str, int, float, float]:
        """Generate preview using standard processing."""
        encoding_start = time.time()
        
        if file_ext == 'txt':
            encoding = self._detect_encoding_optimized(file_path)
        else:
            encoding = 'utf-8'
        
        encoding_time = time.time() - encoding_start
        
        processing_start = time.time()
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                lines = []
                total_lines = 0
                
                for line in f:
                    if len(lines) < preview_lines:
                        lines.append(line)
                    total_lines += 1
                
                preview_text = ''.join(lines)
        
        except Exception as e:
            preview_text = f"Error reading file: {e}"
            total_lines = 0
        
        processing_time = time.time() - processing_start
        
        return preview_text, encoding, total_lines, encoding_time, processing_time
    
    def _detect_encoding_optimized(self, file_path: str) -> str:
        """Optimized encoding detection for preview generation."""
        try:
            import chardet
            
            # Read only first 8KB for encoding detection
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
            
            result = chardet.detect(sample)
            
            if result and result['confidence'] >= 0.7:
                detected_encoding = result['encoding'].lower()
                
                # Map common encoding variations
                encoding_map = {
                    'gb2312': 'gb2312',
                    'gbk': 'gbk',
                    'utf-8': 'utf-8',
                    'utf8': 'utf-8',
                    'ascii': 'utf-8',
                    'windows-1252': 'utf-8',
                }
                
                return encoding_map.get(detected_encoding, detected_encoding)
            else:
                return 'utf-8'
                
        except Exception:
            return 'utf-8'
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for preview generation."""
        if not self._metrics_history:
            return {"status": "No previews generated yet"}
        
        # Calculate statistics
        total_previews = len(self._metrics_history)
        cache_hits = sum(1 for m in self._metrics_history if m.cache_hit)
        cache_hit_rate = (cache_hits / total_previews) * 100
        
        generation_times = [m.generation_time for m in self._metrics_history if not m.cache_hit]
        if generation_times:
            avg_generation_time = sum(generation_times) / len(generation_times)
            max_generation_time = max(generation_times)
            min_generation_time = min(generation_times)
        else:
            avg_generation_time = max_generation_time = min_generation_time = 0
        
        total_files_processed = sum(m.file_size for m in self._metrics_history if not m.cache_hit)
        total_lines_processed = sum(m.lines_processed for m in self._metrics_history if not m.cache_hit)
        
        return {
            "cache_performance": {
                "total_previews": total_previews,
                "cache_hits": cache_hits,
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
                "cache_stats": self.cache.get_stats()
            },
            "generation_performance": {
                "avg_generation_time": f"{avg_generation_time:.3f}s",
                "max_generation_time": f"{max_generation_time:.3f}s",
                "min_generation_time": f"{min_generation_time:.3f}s",
                "total_files_processed": f"{total_files_processed / (1024*1024):.1f} MB",
                "total_lines_processed": total_lines_processed
            },
            "recent_metrics": [asdict(m) for m in self._metrics_history[-10:]]
        }
    
    def clear_cache(self) -> None:
        """Clear preview cache."""
        self.cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown optimizer and cleanup resources."""
        self.cache.shutdown()


# Global preview optimizer instance
_global_preview_optimizer: Optional[PreviewOptimizer] = None


def get_preview_optimizer() -> PreviewOptimizer:
    """Get global preview optimizer instance."""
    global _global_preview_optimizer
    if _global_preview_optimizer is None:
        _global_preview_optimizer = PreviewOptimizer()
    return _global_preview_optimizer


def shutdown_preview_optimizer() -> None:
    """Shutdown global preview optimizer."""
    global _global_preview_optimizer
    if _global_preview_optimizer is not None:
        _global_preview_optimizer.shutdown()
        _global_preview_optimizer = None