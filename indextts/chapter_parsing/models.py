"""
Data models for chapter parsing components.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import re


@dataclass
class Chapter:
    """Represents a final chapter with title and content."""
    title: str
    content: str
    confidence_score: float = 0.8  # Default confidence score


@dataclass
class PotentialChapter:
    """Represents a candidate chapter during parsing."""
    title_text: str
    start_index: int
    end_index: int
    confidence_score: int  # 0-100
    pattern_type: str


@dataclass
class ChapterPattern:
    """Represents a chapter detection pattern."""
    name: str
    pattern: str
    language: str  # 'zh' for Chinese, 'en' for English
    confidence_score: int  # 0-100
    compiled_pattern: Optional[re.Pattern] = None
    
    def __post_init__(self):
        if self.compiled_pattern is None:
            self.compiled_pattern = re.compile(self.pattern, re.MULTILINE)


@dataclass
class ChapterParsingConfig:
    """Configuration for chapter parsing operations."""
    min_chapter_distance: int
    merge_title_distance: int
    min_chapter_length: int
    max_chapters: int
    use_native_epub_chapters: bool
    enable_chinese_patterns: bool
    enable_english_patterns: bool
    
    @classmethod
    def default(cls) -> 'ChapterParsingConfig':
        """Create default chapter parsing configuration."""
        return cls(
            min_chapter_distance=50,
            merge_title_distance=25,
            min_chapter_length=100,
            max_chapters=1000,
            use_native_epub_chapters=True,
            enable_chinese_patterns=True,
            enable_english_patterns=True
        )