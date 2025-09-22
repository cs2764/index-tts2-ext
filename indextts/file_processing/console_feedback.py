"""
Console feedback system for detailed text processing operations.
Provides detailed reporting of file cleaning and processing steps.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProcessingStats:
    """Statistics for text processing operations."""
    
    # Character and whitespace statistics
    excess_spaces_removed: int = 0
    empty_lines_merged: int = 0
    special_characters_removed: int = 0
    invisible_characters_removed: int = 0
    
    # Sentence and line processing
    sentences_broken: int = 0
    lines_processed: int = 0
    
    # File statistics
    original_size: int = 0
    processed_size: int = 0
    original_line_count: int = 0
    processed_line_count: int = 0
    
    # Timing information
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    processing_duration: Optional[float] = None
    
    # Processing stages
    stages_completed: List[str] = field(default_factory=list)
    stage_timings: Dict[str, float] = field(default_factory=dict)
    
    def finish_processing(self):
        """Mark processing as finished and calculate duration."""
        self.end_time = time.time()
        self.processing_duration = self.end_time - self.start_time
    
    def add_stage(self, stage_name: str, duration: float):
        """Add a completed processing stage with timing."""
        self.stages_completed.append(stage_name)
        self.stage_timings[stage_name] = duration


@dataclass
class ChapterDetectionStats:
    """Statistics for chapter detection operations."""
    
    chapters_detected: int = 0
    high_confidence_chapters: int = 0
    low_confidence_chapters_filtered: int = 0
    chapter_patterns_used: List[str] = field(default_factory=list)
    average_confidence_score: float = 0.0
    detection_duration: Optional[float] = None
    
    def calculate_average_confidence(self, confidence_scores: List[float]):
        """Calculate average confidence score from list of scores."""
        if confidence_scores:
            self.average_confidence_score = sum(confidence_scores) / len(confidence_scores)


class ProcessingFeedbackManager:
    """Manages detailed console feedback for text processing operations."""
    
    def __init__(self, console_callback: Optional[callable] = None):
        """
        Initialize the feedback manager.
        
        Args:
            console_callback: Optional callback function for console output
        """
        self.console_callback = console_callback or self._default_console_output
        self.current_stats = ProcessingStats()
        self.chapter_stats = ChapterDetectionStats()
        self.verbose = True
        
    def start_processing(self, filename: str, original_size: int, line_count: int):
        """
        Start processing feedback for a file.
        
        Args:
            filename: Name of the file being processed
            original_size: Original file size in bytes
            line_count: Original number of lines
        """
        self.current_stats = ProcessingStats()
        self.current_stats.original_size = original_size
        self.current_stats.original_line_count = line_count
        
        self._log_message(f"开始处理文件: {filename}")
        self._log_message(f"原始文件大小: {self._format_file_size(original_size)}")
        self._log_message(f"原始行数: {line_count:,} 行")
    
    def start_stage(self, stage_name: str):
        """
        Start a processing stage.
        
        Args:
            stage_name: Name of the processing stage
        """
        self._log_message(f"开始阶段: {stage_name}")
        return time.time()  # Return start time for duration calculation
    
    def finish_stage(self, stage_name: str, start_time: float, **kwargs):
        """
        Finish a processing stage and log results.
        
        Args:
            stage_name: Name of the processing stage
            start_time: Start time of the stage
            **kwargs: Additional statistics for the stage
        """
        duration = time.time() - start_time
        self.current_stats.add_stage(stage_name, duration)
        
        # Log stage completion with timing
        self._log_message(f"完成阶段: {stage_name} (耗时: {self._format_duration(duration)})")
        
        # Log specific statistics based on stage
        if stage_name == "文件清理" and kwargs:
            self._log_cleaning_results(**kwargs)
        elif stage_name == "章节识别" and kwargs:
            self._log_chapter_detection_results(**kwargs)
        elif stage_name == "句子分割" and kwargs:
            self._log_sentence_breaking_results(**kwargs)
    
    def log_cleaning_operation(self, operation: str, count: int, details: str = ""):
        """
        Log a specific cleaning operation.
        
        Args:
            operation: Type of cleaning operation
            count: Number of items processed
            details: Additional details about the operation
        """
        if count > 0:
            message = f"  {operation}: {count:,} 项"
            if details:
                message += f" ({details})"
            self._log_message(message)
            
            # Update statistics
            if "空格" in operation:
                self.current_stats.excess_spaces_removed += count
            elif "空行" in operation:
                self.current_stats.empty_lines_merged += count
            elif "特殊字符" in operation:
                self.current_stats.special_characters_removed += count
            elif "不可见字符" in operation:
                self.current_stats.invisible_characters_removed += count
    
    def log_chapter_detection(self, chapters_found: int, confidence_scores: List[float], 
                            patterns_used: List[str], filtered_count: int = 0):
        """
        Log chapter detection results.
        
        Args:
            chapters_found: Number of chapters detected
            confidence_scores: List of confidence scores for detected chapters
            patterns_used: List of chapter patterns that were used
            filtered_count: Number of low-confidence chapters filtered out
        """
        self.chapter_stats.chapters_detected = chapters_found
        self.chapter_stats.low_confidence_chapters_filtered = filtered_count
        self.chapter_stats.high_confidence_chapters = chapters_found - filtered_count
        self.chapter_stats.chapter_patterns_used = patterns_used
        self.chapter_stats.calculate_average_confidence(confidence_scores)
        
        self._log_message(f"章节识别完成:")
        self._log_message(f"  检测到章节: {chapters_found:,} 个")
        if filtered_count > 0:
            self._log_message(f"  过滤低置信度章节: {filtered_count:,} 个")
            self._log_message(f"  有效章节: {self.chapter_stats.high_confidence_chapters:,} 个")
        
        if confidence_scores:
            avg_confidence = self.chapter_stats.average_confidence_score
            self._log_message(f"  平均置信度: {avg_confidence:.2f}")
        
        if patterns_used:
            patterns_str = ", ".join(patterns_used)
            self._log_message(f"  使用的模式: {patterns_str}")
    
    def finish_processing(self, processed_size: int, processed_line_count: int):
        """
        Finish processing and log final summary.
        
        Args:
            processed_size: Final processed file size in bytes
            processed_line_count: Final number of lines after processing
        """
        self.current_stats.processed_size = processed_size
        self.current_stats.processed_line_count = processed_line_count
        self.current_stats.finish_processing()
        
        self._log_processing_summary()
    
    def _log_cleaning_results(self, **kwargs):
        """Log detailed cleaning operation results."""
        total_operations = 0
        
        if self.current_stats.excess_spaces_removed > 0:
            self._log_message(f"  处理了 {self.current_stats.excess_spaces_removed:,} 个多余空格")
            total_operations += 1
        
        if self.current_stats.empty_lines_merged > 0:
            self._log_message(f"  合并了 {self.current_stats.empty_lines_merged:,} 个空行")
            total_operations += 1
        
        if self.current_stats.special_characters_removed > 0:
            self._log_message(f"  清理了 {self.current_stats.special_characters_removed:,} 个特殊字符")
            total_operations += 1
        
        if self.current_stats.invisible_characters_removed > 0:
            self._log_message(f"  移除了 {self.current_stats.invisible_characters_removed:,} 个不可见字符")
            total_operations += 1
        
        if total_operations == 0:
            self._log_message("  文本已经很干净，无需清理")
    
    def _log_sentence_breaking_results(self, **kwargs):
        """Log sentence breaking operation results."""
        sentences_broken = kwargs.get('sentences_broken', self.current_stats.sentences_broken)
        if sentences_broken > 0:
            self._log_message(f"  分割了 {sentences_broken:,} 个长句")
        else:
            self._log_message("  句子长度合适，无需分割")
    
    def _log_chapter_detection_results(self, **kwargs):
        """Log chapter detection operation results."""
        # This is handled by log_chapter_detection method
        pass
    
    def _log_processing_summary(self):
        """Log final processing summary with statistics."""
        self._log_message("=" * 50)
        self._log_message("处理完成 - 统计摘要:")
        
        # File size changes
        size_change = self.current_stats.processed_size - self.current_stats.original_size
        size_change_pct = (size_change / self.current_stats.original_size * 100) if self.current_stats.original_size > 0 else 0
        
        self._log_message(f"文件大小: {self._format_file_size(self.current_stats.original_size)} → "
                         f"{self._format_file_size(self.current_stats.processed_size)} "
                         f"({size_change_pct:+.1f}%)")
        
        # Line count changes
        line_change = self.current_stats.processed_line_count - self.current_stats.original_line_count
        self._log_message(f"行数: {self.current_stats.original_line_count:,} → "
                         f"{self.current_stats.processed_line_count:,} "
                         f"({line_change:+,})")
        
        # Processing time
        if self.current_stats.processing_duration:
            self._log_message(f"总处理时间: {self._format_duration(self.current_stats.processing_duration)}")
        
        # Stage breakdown
        if self.current_stats.stage_timings:
            self._log_message("各阶段耗时:")
            for stage, duration in self.current_stats.stage_timings.items():
                percentage = (duration / self.current_stats.processing_duration * 100) if self.current_stats.processing_duration else 0
                self._log_message(f"  {stage}: {self._format_duration(duration)} ({percentage:.1f}%)")
        
        # Chapter detection summary
        if self.chapter_stats.chapters_detected > 0:
            self._log_message(f"章节检测: 共识别到 {self.chapter_stats.high_confidence_chapters} 章节")
        
        self._log_message("=" * 50)
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get processing summary as dictionary for programmatic access.
        
        Returns:
            Dictionary containing processing statistics and results
        """
        return {
            'file_stats': {
                'original_size': self.current_stats.original_size,
                'processed_size': self.current_stats.processed_size,
                'size_change': self.current_stats.processed_size - self.current_stats.original_size,
                'original_lines': self.current_stats.original_line_count,
                'processed_lines': self.current_stats.processed_line_count,
                'line_change': self.current_stats.processed_line_count - self.current_stats.original_line_count
            },
            'cleaning_stats': {
                'excess_spaces_removed': self.current_stats.excess_spaces_removed,
                'empty_lines_merged': self.current_stats.empty_lines_merged,
                'special_characters_removed': self.current_stats.special_characters_removed,
                'invisible_characters_removed': self.current_stats.invisible_characters_removed,
                'sentences_broken': self.current_stats.sentences_broken
            },
            'chapter_stats': {
                'chapters_detected': self.chapter_stats.chapters_detected,
                'high_confidence_chapters': self.chapter_stats.high_confidence_chapters,
                'filtered_chapters': self.chapter_stats.low_confidence_chapters_filtered,
                'average_confidence': self.chapter_stats.average_confidence_score,
                'patterns_used': self.chapter_stats.chapter_patterns_used
            },
            'timing': {
                'total_duration': self.current_stats.processing_duration,
                'stage_timings': self.current_stats.stage_timings.copy()
            }
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"
    
    def _log_message(self, message: str):
        """Log a message using the console callback."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if self.console_callback:
            self.console_callback(formatted_message)
        else:
            self._default_console_output(formatted_message)
    
    def _default_console_output(self, message: str):
        """Default console output function."""
        print(message)


class TextProcessingFeedback:
    """Specialized feedback for text processing operations."""
    
    def __init__(self, feedback_manager: ProcessingFeedbackManager):
        """
        Initialize text processing feedback.
        
        Args:
            feedback_manager: The main feedback manager instance
        """
        self.feedback_manager = feedback_manager
        self.operation_counts = {
            'excess_spaces': 0,
            'empty_lines': 0,
            'special_chars': 0,
            'invisible_chars': 0,
            'sentence_breaks': 0
        }
    
    def track_space_removal(self, original_text: str, cleaned_text: str) -> int:
        """
        Track excess space removal and return count.
        
        Args:
            original_text: Original text before cleaning
            cleaned_text: Text after space removal
            
        Returns:
            Number of excess spaces removed
        """
        import re
        
        # Count multiple consecutive spaces in original
        original_spaces = len(re.findall(r' {2,}', original_text))
        
        # Count multiple consecutive spaces in cleaned (should be 0)
        cleaned_spaces = len(re.findall(r' {2,}', cleaned_text))
        
        spaces_removed = original_spaces - cleaned_spaces
        self.operation_counts['excess_spaces'] += spaces_removed
        
        return spaces_removed
    
    def track_empty_line_merging(self, original_text: str, cleaned_text: str) -> int:
        """
        Track empty line merging and return count.
        
        Args:
            original_text: Original text before cleaning
            cleaned_text: Text after empty line merging
            
        Returns:
            Number of empty lines merged
        """
        import re
        
        # Count sequences of 3+ newlines in original
        original_empty_sequences = len(re.findall(r'\n\s*\n\s*\n+', original_text))
        
        # Count sequences of 3+ newlines in cleaned (should be fewer)
        cleaned_empty_sequences = len(re.findall(r'\n\s*\n\s*\n+', cleaned_text))
        
        lines_merged = original_empty_sequences - cleaned_empty_sequences
        self.operation_counts['empty_lines'] += lines_merged
        
        return lines_merged
    
    def track_special_character_removal(self, original_text: str, cleaned_text: str) -> int:
        """
        Track special character removal and return count.
        
        Args:
            original_text: Original text before cleaning
            cleaned_text: Text after special character removal
            
        Returns:
            Number of special characters removed
        """
        import unicodedata
        
        # Count control characters in original (excluding \n, \r, \t)
        original_control_chars = sum(1 for char in original_text 
                                   if unicodedata.category(char).startswith('C') 
                                   and char not in '\n\r\t')
        
        # Count control characters in cleaned
        cleaned_control_chars = sum(1 for char in cleaned_text 
                                  if unicodedata.category(char).startswith('C') 
                                  and char not in '\n\r\t')
        
        chars_removed = original_control_chars - cleaned_control_chars
        self.operation_counts['special_chars'] += chars_removed
        
        return chars_removed
    
    def track_invisible_character_removal(self, original_text: str, cleaned_text: str) -> int:
        """
        Track invisible character removal and return count.
        
        Args:
            original_text: Original text before cleaning
            cleaned_text: Text after invisible character removal
            
        Returns:
            Number of invisible characters removed
        """
        # Define invisible characters to track
        invisible_chars = [
            '\u200b',  # Zero Width Space
            '\u200c',  # Zero Width Non-Joiner
            '\u200d',  # Zero Width Joiner
            '\u2060',  # Word Joiner
            '\ufeff',  # Zero Width No-Break Space (BOM)
            '\u00a0',  # Non-breaking space
            '\u2000', '\u2001', '\u2002', '\u2003', '\u2004',  # Various spaces
            '\u2005', '\u2006', '\u2007', '\u2008', '\u2009',
            '\u200a', '\u202f', '\u205f', '\u3000'
        ]
        
        original_count = sum(original_text.count(char) for char in invisible_chars)
        cleaned_count = sum(cleaned_text.count(char) for char in invisible_chars)
        
        chars_removed = original_count - cleaned_count
        self.operation_counts['invisible_chars'] += chars_removed
        
        return chars_removed
    
    def track_sentence_breaking(self, original_text: str, processed_text: str) -> int:
        """
        Track sentence breaking operations and return count.
        
        Args:
            original_text: Original text before sentence breaking
            processed_text: Text after sentence breaking
            
        Returns:
            Number of sentences that were broken
        """
        # Count lines that were split (approximate)
        original_lines = len(original_text.split('\n'))
        processed_lines = len(processed_text.split('\n'))
        
        sentences_broken = max(0, processed_lines - original_lines)
        self.operation_counts['sentence_breaks'] += sentences_broken
        
        return sentences_broken
    
    def get_operation_summary(self) -> Dict[str, int]:
        """
        Get summary of all tracked operations.
        
        Returns:
            Dictionary with operation counts
        """
        return self.operation_counts.copy()