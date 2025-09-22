"""
Smart chapter parser for intelligent chapter detection and parsing.
Based on the SmartChapterParser algorithm documentation.
"""

import re
import time
from typing import List, Optional, Callable
from .models import Chapter, PotentialChapter, ChapterPattern, ChapterParsingConfig


class SmartChapterParser:
    """Intelligent chapter detection and parsing system."""
    
    def __init__(self, min_chapter_distance: int = 50, merge_title_distance: int = 25,
                 console_callback: Optional[Callable] = None):
        """Initialize the chapter parser with configuration."""
        self.min_chapter_distance = min_chapter_distance
        self.merge_title_distance = merge_title_distance
        self.chapter_patterns = self._load_chapter_patterns()
        self.console_callback = console_callback
        
        # Performance optimizations will be initialized lazily to avoid circular imports
        self._memory_optimizer = None
        self._chapter_optimizer = None
    
    def parse(self, text: str) -> List[Chapter]:
        """
        Parse text and identify chapters using the smart algorithm.
        
        Args:
            text: Input text to parse for chapters
            
        Returns:
            List of detected chapters
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Use optimized parsing for large texts
        text_length = len(text)
        
        # Use optimized parsing if text is large
        if text_length > 50000:
            try:
                # Lazy import to avoid circular imports
                if self._memory_optimizer is None:
                    from ..performance.memory_manager import MemoryOptimizer
                    self._memory_optimizer = MemoryOptimizer()
                
                if self._chapter_optimizer is None:
                    from ..performance.chapter_optimizer import ChapterParsingOptimizer
                    self._chapter_optimizer = ChapterParsingOptimizer()
                
                # Get optimization settings based on memory usage
                optimization_settings = self._memory_optimizer.optimize_chapter_parsing(text_length)
                
                chapters, metrics = self._chapter_optimizer.optimize_chapter_parsing(
                    text, self.chapter_patterns, optimization_settings
                )
                return chapters
            except Exception as e:
                print(f"Optimized parsing failed, falling back to standard: {e}")
                # Fall through to standard parsing
        
        # Standard parsing algorithm
        # Step 1: Preprocess text
        processed_text = self._preprocess(text)
        
        # Step 2: Scan for candidate chapters
        candidates = self._scan_for_candidates(processed_text)
        
        # Step 3: Filter and merge candidates (with context-aware validation)
        filtered_candidates = self._filter_and_merge_candidates(processed_text, candidates)
        
        # Step 4: Extract content
        chapters = self._extract_content(processed_text, filtered_candidates)
        
        return chapters
    
    def parse_with_feedback(self, text: str, feedback_manager=None) -> List[Chapter]:
        """
        Parse text and identify chapters with detailed console feedback.
        
        Args:
            text: Input text to parse for chapters
            feedback_manager: Optional feedback manager for console output
            
        Returns:
            List of detected chapters
        """
        if not text or len(text.strip()) == 0:
            return []
        
        start_time = time.time()
        
        if feedback_manager:
            stage_start = feedback_manager.start_stage("章节识别")
        
        # Use optimized parsing for large texts or real-time preview
        text_length = len(text)
        
        # Use optimized parsing if text is large or for real-time preview
        if text_length > 50000 or (feedback_manager and hasattr(feedback_manager, 'is_real_time_preview')):
            try:
                # Lazy import to avoid circular imports
                if self._memory_optimizer is None:
                    from ..performance.memory_manager import MemoryOptimizer
                    self._memory_optimizer = MemoryOptimizer()
                
                if self._chapter_optimizer is None:
                    from ..performance.chapter_optimizer import ChapterParsingOptimizer
                    self._chapter_optimizer = ChapterParsingOptimizer()
                
                # Get optimization settings based on memory usage and context
                optimization_settings = self._memory_optimizer.optimize_chapter_parsing(text_length)
                
                # Adjust settings for real-time preview
                if feedback_manager and hasattr(feedback_manager, 'is_real_time_preview'):
                    optimization_settings.update({
                        'use_fast_scan': True,
                        'cache_patterns': True,
                        'max_candidates': 50,  # Limit for faster preview
                        'batch_size': 200      # Smaller batches for responsiveness
                    })
                
                chapters, metrics = self._chapter_optimizer.optimize_chapter_parsing(
                    text, self.chapter_patterns, optimization_settings
                )
                
                if feedback_manager:
                    patterns_used = getattr(metrics, 'patterns_used', [])
                    self._log_chapter_results(chapters, feedback_manager, patterns_used)
                    feedback_manager.finish_stage("章节识别", stage_start)
                
                return chapters
            except Exception as e:
                if self.console_callback:
                    self.console_callback(f"优化解析失败，回退到标准解析: {e}")
                # Fall through to standard parsing
        
        # Standard parsing algorithm with feedback
        # Step 1: Preprocess text
        processed_text = self._preprocess(text)
        
        # Step 2: Scan for candidate chapters
        candidates = self._scan_for_candidates(processed_text)
        
        # Step 3: Filter and merge candidates (with context-aware validation)
        filtered_candidates = self._filter_and_merge_candidates(processed_text, candidates)
        
        # Step 4: Extract content
        chapters = self._extract_content(processed_text, filtered_candidates)
        
        # Log results with feedback
        if feedback_manager:
            patterns_used = [pattern.name for pattern in self.chapter_patterns 
                           if any(candidate.pattern_type == pattern.name for candidate in filtered_candidates)]
            confidence_scores = [chapter.confidence_score for chapter in chapters]
            filtered_count = len(candidates) - len(filtered_candidates)
            
            self._log_chapter_results(chapters, feedback_manager, patterns_used, confidence_scores, filtered_count)
            feedback_manager.finish_stage("章节识别", stage_start)
        
        return chapters
    
    def parse_for_preview(self, text: str, max_chapters: int = 20) -> List[Chapter]:
        """
        Parse text for real-time chapter preview with optimized performance.
        
        Args:
            text: Input text to parse for chapters
            max_chapters: Maximum number of chapters to return for preview
            
        Returns:
            List of detected chapters (limited for preview)
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # For preview, restrict to high-confidence patterns only to avoid noise
        preview_patterns = [p for p in self.chapter_patterns if p.confidence_score >= 80]
        
        # Use optimized parsing with preview-specific settings
        try:
            # Lazy import to avoid circular imports
            if self._memory_optimizer is None:
                from ..performance.memory_manager import MemoryOptimizer
                self._memory_optimizer = MemoryOptimizer()
            
            if self._chapter_optimizer is None:
                from ..performance.chapter_optimizer import ChapterParsingOptimizer
                self._chapter_optimizer = ChapterParsingOptimizer()
            
            # Preview-optimized settings
            optimization_settings = {
                'use_fast_scan': True,
                'cache_patterns': True,
                'max_candidates': max_chapters * 2,  # Allow some filtering
                'batch_size': 500
            }
            
            chapters, metrics = self._chapter_optimizer.optimize_chapter_parsing(
                text, preview_patterns, optimization_settings
            )
            
            # Limit results for preview
            return chapters[:max_chapters]
            
        except Exception as e:
            if self.console_callback:
                self.console_callback(f"预览解析失败，使用快速解析: {e}")
            
            # Fallback to fast basic parsing
            return self._fast_preview_parsing(text, max_chapters)
    
    def _fast_preview_parsing(self, text: str, max_chapters: int) -> List[Chapter]:
        """
        Fast chapter parsing for preview purposes.
        
        Args:
            text: Input text to parse
            max_chapters: Maximum chapters to return
            
        Returns:
            List of chapters (limited)
        """
        chapters = []
        
        # Use only the most reliable patterns for preview
        high_confidence_patterns = [p for p in self.chapter_patterns if p.confidence_score >= 70]
        
        for pattern in high_confidence_patterns[:3]:  # Limit to top 3 patterns
            matches = pattern.compiled_pattern.finditer(text)
            
            for match in matches:
                if len(chapters) >= max_chapters:
                    break
                
                title_text = match.group(0).strip()
                
                # Quick validation
                if len(title_text) < 2 or len(title_text) > 50:
                    continue
                
                # Create chapter with minimal content extraction
                chapter = Chapter(
                    title=title_text,
                    content="",  # Don't extract content for preview
                    confidence_score=pattern.confidence_score
                )
                chapters.append(chapter)
            
            if len(chapters) >= max_chapters:
                break
        
        return chapters
    
    def _log_chapter_results(self, chapters: List[Chapter], feedback_manager, 
                           patterns_used: List[str], confidence_scores: List[float] = None, 
                           filtered_count: int = 0):
        """
        Log chapter detection results using the feedback manager.
        
        Args:
            chapters: List of detected chapters
            feedback_manager: Feedback manager instance
            patterns_used: List of pattern names that were used
            confidence_scores: List of confidence scores for chapters
            filtered_count: Number of low-confidence chapters filtered out
        """
        if confidence_scores is None:
            confidence_scores = [chapter.confidence_score for chapter in chapters]
        
        feedback_manager.log_chapter_detection(
            chapters_found=len(chapters) + filtered_count,
            confidence_scores=confidence_scores,
            patterns_used=patterns_used,
            filtered_count=filtered_count
        )
    
    def _preprocess(self, text: str) -> str:
        """Text preprocessing to normalize whitespace."""
        # Replace full-width spaces with half-width spaces
        text = text.replace('　', ' ')
        return text
    
    def _scan_for_candidates(self, text: str) -> List[PotentialChapter]:
        """Scan text for potential chapters using multiple patterns."""
        candidates = []
        
        for pattern in self.chapter_patterns:
            matches = pattern.compiled_pattern.finditer(text)
            
            for match in matches:
                title_text = match.group(0).strip()
                
                # Skip if excluded by exclusion patterns
                if self._should_exclude(title_text):
                    continue
                
                # Special handling for heuristic patterns
                if pattern.confidence_score == 30:  # Heuristic pattern
                    if not self._validate_heuristic_match(text, match):
                        continue
                
                candidate = PotentialChapter(
                    title_text=title_text,
                    start_index=match.start(),
                    end_index=match.end(),
                    confidence_score=pattern.confidence_score,
                    pattern_type=pattern.name
                )
                candidates.append(candidate)
        
        return candidates
    
    def _filter_and_merge_candidates(self, text: str, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Filter and merge candidates using intelligent algorithms (context-aware)."""
        if not candidates:
            return []
        
        # Step 1: Remove low-confidence false positives with context-aware checks
        filtered_candidates = self._filter_low_confidence(text, candidates)
        
        # Step 2: Merge duplicate or overlapping chapters
        merged_candidates = self._merge_duplicates(filtered_candidates)
        
        # Step 3: Apply distance-based filtering
        final_candidates = self._apply_distance_filtering(merged_candidates)
        
        # Sort final candidates by position
        final_candidates.sort(key=lambda x: x.start_index)
        return final_candidates
    
    def _filter_low_confidence(self, text: str, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Filter out false positives with confidence-aware and context-aware checks."""
        filtered = []
        
        for candidate in candidates:
            score = candidate.confidence_score
            # Keep high-confidence structural patterns as-is
            if score >= 80:
                filtered.append(candidate)
                continue
            
            # Medium confidence (e.g., number_pattern, parentheses_pattern): require context validation
            if 60 <= score < 80:
                if self._validate_medium_confidence_candidate(text, candidate):
                    filtered.append(candidate)
                continue
            
            # Low confidence: apply stricter validation
            if 30 <= score < 60:
                if self._validate_low_confidence_candidate_with_context(text, candidate):
                    filtered.append(candidate)
                continue
        
        return filtered
    
    def _validate_low_confidence_candidate(self, candidate: PotentialChapter) -> bool:
        """Original validation for low-confidence candidates (kept for compatibility)."""
        title = candidate.title_text
        
        # Check title length (not too short, not too long)
        if len(title) < 2 or len(title) > 10:
            return False
        
        # Check for common chapter indicators
        chapter_indicators = ['章', '回', '节', '部', '卷', 'Chapter', 'Part', 'Section']
        if any(indicator in title for indicator in chapter_indicators):
            return True
        
        # Check for numbered patterns with punctuation
        if re.search(r'[一二三四五六七八九十\d]+[、.]', title):
            return True
        
        # Check for single character keywords
        keywords = ['序', '前言', '后记', '番外', '尾声']
        if title in keywords:
            return True
        
        return False
    
    def _validate_low_confidence_candidate_with_context(self, text: str, candidate: PotentialChapter) -> bool:
        """Stricter validation for low-confidence candidates using context around the line."""
        if not self._validate_low_confidence_candidate(candidate):
            return False
        
        # Require heading-like context (blank line before or after)
        if not self._has_heading_context(text, candidate.start_index, candidate.end_index):
            return False
        
        # The same line should not contain sentence-ending punctuation after the title
        if self._line_tail_has_sentence_punct(text, candidate.end_index):
            return False
        
        return True
    
    def _validate_medium_confidence_candidate(self, text: str, candidate: PotentialChapter) -> bool:
        """Validation for medium-confidence patterns (e.g., numbered headings)."""
        title = candidate.title_text.strip()
        
        # Strong indicators always pass
        if any(ind in title for ind in ['章', '回', '节', '部', '卷']) or re.match(r'^\s*Chapter\s+\d+', title, re.IGNORECASE):
            return True
        
        # Context requirements: should be isolated like a heading
        if not self._has_heading_context(text, candidate.start_index, candidate.end_index):
            return False
        
        # For number_pattern, ensure tail isn't a long, punctuated sentence (likely a paragraph list item)
        if candidate.pattern_type == 'number_pattern':
            m = re.match(r'^\s*[一二三四五六七八九十百千万廿卅卌\d]+\s*[、.．]\s*(.*)$', title)
            if m:
                tail = m.group(1).strip()
                # If tail is too long or contains sentence punctuation, treat as paragraph, not heading
                if len(tail) >= 20 or re.search(r'[。！？.!?]', tail):
                    return False
        
        # Avoid lines where the remainder of the current line contains sentence-ending punctuation
        if self._line_tail_has_sentence_punct(text, candidate.end_index):
            return False
        
        return True
    
    def _has_heading_context(self, text: str, start_idx: int, end_idx: int) -> bool:
        """Check for heading-like context: blank line before or after the line containing the title."""
        # Locate current line boundaries
        prev_nl = text.rfind('\n', 0, start_idx)
        prev2_nl = text.rfind('\n', 0, prev_nl) if prev_nl != -1 else -1
        next_nl = text.find('\n', end_idx)
        next2_nl = text.find('\n', next_nl + 1) if next_nl != -1 else -1
        
        prev_line = text[prev2_nl + 1:prev_nl] if prev_nl != -1 else ''
        next_line = text[next_nl + 1:next2_nl] if next_nl != -1 and next2_nl != -1 else ''
        
        # Consider it heading-like if there is a blank line either before or after
        has_blank_before = prev_line.strip() == ''
        has_blank_after = next_line.strip() == ''
        
        return has_blank_before or has_blank_after
    
    def _line_tail_has_sentence_punct(self, text: str, end_idx: int) -> bool:
        """Check if the remainder of the line after the match contains sentence-ending punctuation."""
        line_end = text.find('\n', end_idx)
        if line_end == -1:
            line_end = len(text)
        tail = text[end_idx:line_end]
        return bool(re.search(r'[。！？.!?]', tail))
    
    def _merge_duplicates(self, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Merge duplicate or overlapping chapters."""
        if not candidates:
            return []
        
        # Sort by position
        sorted_candidates = sorted(candidates, key=lambda x: x.start_index)
        merged = []
        
        for candidate in sorted_candidates:
            should_merge = False
            
            for i, existing in enumerate(merged):
                # Check if titles are similar or positions are very close
                if self._should_merge_candidates(candidate, existing):
                    # Merge by keeping the better one
                    # Priority: 1) Longer title, 2) Higher confidence
                    if (len(candidate.title_text) > len(existing.title_text) or
                        (len(candidate.title_text) == len(existing.title_text) and 
                         candidate.confidence_score > existing.confidence_score)):
                        merged[i] = candidate
                    should_merge = True
                    break
            
            if not should_merge:
                merged.append(candidate)
        
        return merged
    
    def _should_merge_candidates(self, candidate1: PotentialChapter, candidate2: PotentialChapter) -> bool:
        """Check if two candidates should be merged."""
        title1 = candidate1.title_text.strip()
        title2 = candidate2.title_text.strip()
        
        # Check title similarity first
        if candidate1.title_text == candidate2.title_text:
            return True
        
        # Check if one title is a subset of another (e.g., "第一章" vs "第一章 标题")
        if title1 in title2 or title2 in title1:
            # Only merge if they are similar chapter types
            if self._are_similar_chapter_types(candidate1, candidate2):
                return True
        
        # Check distance only for very close positions (likely same title split across lines)
        distance = abs(candidate1.start_index - candidate2.start_index)
        if distance <= 10:  # Very close positions only
            return True
        
        return False
    
    def _are_similar_chapter_types(self, candidate1: PotentialChapter, candidate2: PotentialChapter) -> bool:
        """Check if two candidates are similar chapter types."""
        # Both have chapter indicators
        chapter_indicators = ['章', '回', '节', '部', '卷']
        title1_has_chapter = any(ind in candidate1.title_text for ind in chapter_indicators)
        title2_has_chapter = any(ind in candidate2.title_text for ind in chapter_indicators)
        
        if title1_has_chapter and title2_has_chapter:
            return True
        
        # Both are keywords
        keywords = ['序', '前言', '后记', '番外', '尾声']
        title1_is_keyword = candidate1.title_text in keywords
        title2_is_keyword = candidate2.title_text in keywords
        
        if title1_is_keyword and title2_is_keyword:
            return True
        
        # Both are numbered patterns
        if (re.search(r'[一二三四五六七八九十\d]+[、.]', candidate1.title_text) and
            re.search(r'[一二三四五六七八九十\d]+[、.]', candidate2.title_text)):
            return True
        
        return False
    
    def _apply_distance_filtering(self, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Apply distance-based filtering with dynamic thresholds."""
        if not candidates:
            return []
        
        # Sort by confidence score (descending) and position (ascending)
        sorted_candidates = sorted(candidates, key=lambda x: (-x.confidence_score, x.start_index))
        
        final_candidates = []
        
        for candidate in sorted_candidates:
            should_add = True
            
            for accepted in final_candidates:
                distance = abs(candidate.start_index - accepted.start_index)
                min_distance = self._calculate_dynamic_distance(candidate, accepted)
                
                if distance < min_distance:
                    should_add = False
                    break
            
            if should_add:
                final_candidates.append(candidate)
        
        return final_candidates
    
    def _extract_content(self, text: str, candidates: List[PotentialChapter]) -> List[Chapter]:
        """Extract chapter content based on final candidates with boundary optimization."""
        if not candidates:
            return []
        
        chapters = []
        
        # Handle preface if first chapter doesn't start at beginning
        if candidates[0].start_index > 10:  # Some content before first chapter
            preface_content = text[:candidates[0].start_index].strip()
            if len(preface_content) > 10:  # Lower threshold for testing
                chapters.append(Chapter(title="前言", content=preface_content))
        
        # Extract content for each chapter with boundary optimization
        for i, candidate in enumerate(candidates):
            # Optimize chapter boundaries
            content_start, content_end = self._optimize_chapter_boundaries(
                text, candidate, candidates, i
            )
            
            # Extract and clean content
            content = self._clean_chapter_content(text[content_start:content_end])
            
            if len(content) > 0:
                chapters.append(Chapter(
                    title=candidate.title_text,
                    content=content
                ))
        
        return chapters
    
    def _optimize_chapter_boundaries(self, text: str, current_candidate: PotentialChapter, 
                                   all_candidates: List[PotentialChapter], 
                                   current_index: int) -> tuple[int, int]:
        """Optimize chapter boundaries to preserve context and handle transitions."""
        
        # Find content start - skip the title line
        content_start = current_candidate.end_index
        
        # Skip to next line after title
        next_newline = text.find('\n', content_start)
        if next_newline != -1:
            content_start = next_newline + 1
        
        # Find content end
        if current_index + 1 < len(all_candidates):
            next_candidate = all_candidates[current_index + 1]
            content_end = next_candidate.start_index
            
            # Optimize boundary - don't cut in the middle of a sentence
            content_end = self._find_optimal_boundary(text, content_end)
        else:
            content_end = len(text)
        
        return content_start, content_end
    
    def _find_optimal_boundary(self, text: str, initial_boundary: int) -> int:
        """Find optimal boundary that doesn't cut sentences or paragraphs."""
        # For boundary optimization, we want to be conservative
        # Only adjust if we're clearly cutting in the middle of something
        
        # If we're already at a good boundary (whitespace), use it
        if initial_boundary < len(text) and text[initial_boundary] in ['\n', ' ', '\t']:
            return initial_boundary
        
        # Look backwards a short distance for a better break point
        search_start = max(0, initial_boundary - 20)  # Only look back 20 chars
        
        # Look for sentence endings followed by whitespace
        sentence_endings = ['。', '！', '？', '.', '!', '?']
        for i in range(initial_boundary - 1, search_start, -1):
            if text[i] in sentence_endings:
                # Make sure it's followed by whitespace or newline
                if i + 1 < len(text) and text[i + 1] in ['\n', ' ', '\t']:
                    return i + 1
        
        # Look for line breaks
        for i in range(initial_boundary - 1, search_start, -1):
            if text[i] == '\n':
                return i + 1
        
        # If no good boundary found within short range, use original
        # This prevents cutting too much content
        return initial_boundary
    
    def _clean_chapter_content(self, content: str) -> str:
        """Clean chapter content by removing excessive whitespace."""
        if not content:
            return ""
        
        # Remove leading and trailing whitespace
        content = content.strip()
        
        # Normalize multiple consecutive newlines to at most 2
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove excessive spaces (but preserve intentional formatting)
        content = re.sub(r'[ \t]{3,}', '  ', content)
        
        # Clean up lines: remove leading/trailing spaces from each line
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        
        # Rejoin lines, preserving paragraph structure
        content = '\n'.join(lines)
        
        # Clean up any remaining excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content
    
    def _load_chapter_patterns(self) -> List[ChapterPattern]:
        """Load chapter detection patterns based on the algorithm documentation."""
        patterns = []
        
        # Structured patterns (confidence: 100)
        patterns.extend([
            ChapterPattern("structured_chapter", r"^\s*(第|卷)\s*[一二三四五六七八九十百千万零\d]+\s*[章回节部卷].*$", "zh", 100),
        ])
        
        # Keyword patterns (confidence: 80)
        patterns.extend([
            ChapterPattern("keyword_pattern", r"^\s*(序|前言|引子|楔子|后记|番外|尾声|序章|序幕)\s*$", "zh", 80),
        ])
        
        # Parentheses patterns (confidence: 65)
        patterns.extend([
            ChapterPattern("parentheses_pattern", r"^\s*[（(]\s*[一二三四五六七八九十百千万零廿卅卌\d]+\s*[)）]\s*.*$", "zh", 65),
        ])
        
        # Number patterns (confidence: 60)
        patterns.extend([
            ChapterPattern("number_pattern", r"^\s*[一二三四五六七八九十百千万廿卅卌\d]+\s*[、.．].*$", "zh", 60),
        ])
        
        # Heuristic patterns (confidence: 30)
        patterns.extend([
            # 至少包含一个中文或英文/数字，且不包含句末标点，避免纯标点行被识别为章节
            ChapterPattern("heuristic_pattern", r"^(?=.*[\u4e00-\u9fffA-Za-z0-9])[^^\n。！？…]{1,15}$", "zh", 30),
        ])
        
        # English patterns
        patterns.extend([
            ChapterPattern("english_chapter", r"^\s*Chapter\s+\d+.*$", "en", 100),
            ChapterPattern("english_part", r"^\s*Part\s+\d+.*$", "en", 90),
            ChapterPattern("english_section", r"^\s*Section\s+\d+.*$", "en", 80),
        ])
        
        return patterns
    
    def _should_exclude(self, title_text: str) -> bool:
        """Check if title should be excluded based on exclusion patterns."""
        # First check if it's a valid parentheses chapter pattern
        if re.match(r"^\s*[（(]\s*[一二三四五六七八九十百千万零廿卅卌\d]+\s*[)）]", title_text):
            return False  # Don't exclude valid parentheses chapters
        
        # Exclude structured titles where the trailing part is only punctuation (e.g., "第3章：……")
        m_struct = re.match(r"^\s*(第|卷)\s*[一二三四五六七八九十百千万零\d]+\s*[章回节部卷][:：\s]*?(.*)$", title_text)
        if m_struct:
            tail = m_struct.group(2) or ""
            # If tail has no CJK or alphanumeric, exclude
            if not re.search(r"[\u4e00-\u9fffA-Za-z0-9]", tail):
                return True
        
        exclusion_patterns = [
            r".*\.(html?|htm|txt|doc|pdf|jpg|png|gif|css|js)$",  # File names
            r"^\s*\d+(\.\w+)?\s*$",  # Pure numbers or numbers with extensions
            r".*(http|www|\.com|\.cn|\.org).*",  # URLs
            r".*[<>{}[\]();=&%#].*",  # Code-like content (but not parentheses chapters)
            r"^\s*\d{4,}\s*$",  # Long number sequences
            r"<[^>]+>",  # HTML tags
            r"^\s*[*+\-=_~`]+\s*$",  # Lines with only special symbols (*, +, -, =, _ , ~, `)
            r"^\s*[\.。·]{3,}\s*$",  # Lines with only dots/ellipses
            r"^\s*[…]{2,}\s*$",      # Lines with only ellipsis char
            r"^\s*[—–\-]{3,}\s*$",   # Lines with multiple dashes/em-dashes
            r"^\s*[_=]{3,}\s*$",     # Lines with multiple underscores or equals
        ]
        
        for pattern in exclusion_patterns:
            if re.match(pattern, title_text, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_heuristic_match(self, text: str, match: re.Match) -> bool:
        """Validate heuristic pattern matches with additional checks."""
        title_text = match.group(0).strip()
        
        # Length check
        if len(title_text) < 2:
            return False
        
        # Must contain at least one CJK or alphanumeric character
        if not re.search(r"[\u4e00-\u9fffA-Za-z0-9]", title_text):
            return False
        
        # Pure number check
        if re.match(r"^\s*\d+\s*$", title_text):
            return False
        
        # Reject lines that are mostly punctuation (e.g., '———', '……', '......')
        if re.match(r"^\s*[\-—–_=+`~·。．.,，…!！?？:：;；*＊\[\]{}()<>\/\\|]+\s*$", title_text):
            return False
        
        return True
    
    def _calculate_dynamic_distance(self, candidate1: PotentialChapter, candidate2: PotentialChapter) -> int:
        """Calculate dynamic minimum distance based on confidence scores."""
        min_confidence = min(candidate1.confidence_score, candidate2.confidence_score)
        
        if min_confidence >= 80:
            return 15  # High confidence
        elif min_confidence >= 60:
            return 30  # Medium confidence
        else:
            return self.min_chapter_distance  # Low confidence