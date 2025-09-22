"""
Optimized chapter parsing algorithms for improved speed and accuracy.
"""

import re
import time
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..chapter_parsing.models import Chapter, PotentialChapter, ChapterPattern


@dataclass
class OptimizationMetrics:
    """Metrics for chapter parsing optimization."""
    total_time: float
    pattern_matching_time: float
    filtering_time: float
    content_extraction_time: float
    candidates_found: int
    chapters_extracted: int
    optimization_level: str


class ChapterParsingOptimizer:
    """Optimized chapter parsing with improved algorithms."""
    
    def __init__(self, enable_parallel_processing: bool = True, max_workers: int = 4):
        """
        Initialize chapter parsing optimizer.
        
        Args:
            enable_parallel_processing: Whether to use parallel processing
            max_workers: Maximum number of worker threads
        """
        self.enable_parallel_processing = enable_parallel_processing
        self.max_workers = max_workers
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._pattern_cache: Dict[str, List[PotentialChapter]] = {}
        self.metrics = OptimizationMetrics(0, 0, 0, 0, 0, 0, "none")
    
    def optimize_chapter_parsing(self, text: str, patterns: List[ChapterPattern], 
                               optimization_settings: Dict[str, any]) -> Tuple[List[Chapter], OptimizationMetrics]:
        """
        Perform optimized chapter parsing with configurable optimization level.
        
        Args:
            text: Text to parse for chapters
            patterns: List of chapter patterns to use
            optimization_settings: Optimization configuration
            
        Returns:
            Tuple of (chapters, metrics)
        """
        start_time = time.time()
        
        # Determine optimization level
        use_fast_scan = optimization_settings.get('use_fast_scan', True)
        cache_patterns = optimization_settings.get('cache_patterns', True)
        max_candidates = optimization_settings.get('max_candidates', 100)
        batch_size = optimization_settings.get('batch_size', 500)
        
        optimization_level = self._determine_optimization_level(optimization_settings)
        
        try:
            # Step 1: Optimized pattern matching
            pattern_start = time.time()
            candidates = self._optimized_pattern_matching(
                text, patterns, use_fast_scan, cache_patterns, max_candidates, batch_size
            )
            pattern_time = time.time() - pattern_start
            
            # Step 2: Optimized filtering
            filter_start = time.time()
            filtered_candidates = self._optimized_filtering(candidates, optimization_settings)
            filter_time = time.time() - filter_start
            
            # Step 3: Optimized content extraction
            extract_start = time.time()
            chapters = self._optimized_content_extraction(text, filtered_candidates, optimization_settings)
            extract_time = time.time() - extract_start
            
            total_time = time.time() - start_time
            
            # Create metrics
            self.metrics = OptimizationMetrics(
                total_time=total_time,
                pattern_matching_time=pattern_time,
                filtering_time=filter_time,
                content_extraction_time=extract_time,
                candidates_found=len(candidates),
                chapters_extracted=len(chapters),
                optimization_level=optimization_level
            )
            
            return chapters, self.metrics
            
        except Exception as e:
            # Fallback to basic parsing if optimization fails
            print(f"Optimization failed, falling back to basic parsing: {e}")
            return self._fallback_parsing(text, patterns), self.metrics
    
    def _optimized_pattern_matching(self, text: str, patterns: List[ChapterPattern],
                                  use_fast_scan: bool, cache_patterns: bool,
                                  max_candidates: int, batch_size: int) -> List[PotentialChapter]:
        """Optimized pattern matching with caching and parallel processing."""
        candidates = []
        
        # Use cached results if available
        text_hash = str(hash(text[:1000]))  # Hash first 1000 chars for cache key
        if cache_patterns and text_hash in self._pattern_cache:
            return self._pattern_cache[text_hash][:max_candidates]
        
        if use_fast_scan and self.enable_parallel_processing and len(patterns) > 2:
            # Parallel pattern matching for multiple patterns
            candidates = self._parallel_pattern_matching(text, patterns, batch_size)
        else:
            # Sequential pattern matching
            candidates = self._sequential_pattern_matching(text, patterns)
        
        # Limit candidates to prevent memory issues
        candidates = candidates[:max_candidates]
        
        # Cache results
        if cache_patterns:
            self._pattern_cache[text_hash] = candidates
            
            # Limit cache size
            if len(self._pattern_cache) > 10:
                oldest_key = next(iter(self._pattern_cache))
                del self._pattern_cache[oldest_key]
        
        return candidates
    
    def _parallel_pattern_matching(self, text: str, patterns: List[ChapterPattern], 
                                 batch_size: int) -> List[PotentialChapter]:
        """Parallel pattern matching using thread pool."""
        candidates = []
        
        # Split text into batches for parallel processing
        text_batches = self._split_text_into_batches(text, batch_size)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit pattern matching tasks
            futures = []
            for batch_start, batch_text in text_batches:
                future = executor.submit(
                    self._match_patterns_in_batch, 
                    batch_text, patterns, batch_start
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_candidates = future.result()
                    candidates.extend(batch_candidates)
                except Exception as e:
                    print(f"Error in parallel pattern matching: {e}")
        
        # Sort candidates by position
        candidates.sort(key=lambda x: x.start_index)
        return candidates
    
    def _sequential_pattern_matching(self, text: str, patterns: List[ChapterPattern]) -> List[PotentialChapter]:
        """Sequential pattern matching with optimized regex."""
        candidates = []
        
        for pattern in patterns:
            # Get or compile pattern
            compiled_pattern = self._get_compiled_pattern(pattern)
            
            # Find matches
            matches = compiled_pattern.finditer(text)
            
            for match in matches:
                title_text = match.group(0).strip()
                
                # Quick exclusion check
                if self._quick_exclusion_check(title_text):
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
    
    def _optimized_filtering(self, candidates: List[PotentialChapter], 
                           optimization_settings: Dict[str, any]) -> List[PotentialChapter]:
        """Optimized candidate filtering with improved algorithms."""
        if not candidates:
            return []
        
        # Step 1: Fast duplicate removal using set-based approach
        unique_candidates = self._fast_duplicate_removal(candidates)
        
        # Step 2: Optimized confidence filtering
        confidence_filtered = self._optimized_confidence_filtering(unique_candidates)
        
        # Step 3: Optimized distance filtering
        distance_filtered = self._optimized_distance_filtering(confidence_filtered)
        
        return distance_filtered
    
    def _fast_duplicate_removal(self, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Fast duplicate removal using hash-based approach."""
        seen_titles: Set[str] = set()
        seen_positions: Set[int] = set()
        unique_candidates = []
        
        # Sort by confidence (descending) and position (ascending)
        sorted_candidates = sorted(candidates, key=lambda x: (-x.confidence_score, x.start_index))
        
        for candidate in sorted_candidates:
            # Create unique key combining title and approximate position
            title_key = candidate.title_text.strip().lower()
            position_key = candidate.start_index // 50  # Group positions within 50 chars
            
            if title_key not in seen_titles and position_key not in seen_positions:
                seen_titles.add(title_key)
                seen_positions.add(position_key)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def _optimized_confidence_filtering(self, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Optimized confidence-based filtering."""
        if not candidates:
            return []
        
        # Calculate dynamic confidence threshold based on candidate distribution
        confidence_scores = [c.confidence_score for c in candidates]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Use adaptive threshold
        if avg_confidence > 70:
            threshold = 60  # High average - use higher threshold
        elif avg_confidence > 50:
            threshold = 40  # Medium average - use medium threshold
        else:
            threshold = 30  # Low average - use lower threshold
        
        return [c for c in candidates if c.confidence_score >= threshold]
    
    def _optimized_distance_filtering(self, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """Optimized distance-based filtering using spatial indexing."""
        if not candidates:
            return []
        
        # Sort by confidence (descending) for priority-based selection
        sorted_candidates = sorted(candidates, key=lambda x: -x.confidence_score)
        
        # Use spatial indexing for efficient distance checking
        selected_positions = []
        filtered_candidates = []
        
        for candidate in sorted_candidates:
            # Check if position conflicts with already selected candidates
            min_distance = self._calculate_min_distance(candidate)
            
            # Use binary search for efficient position checking
            conflict_found = False
            for pos in selected_positions:
                if abs(candidate.start_index - pos) < min_distance:
                    conflict_found = True
                    break
            
            if not conflict_found:
                selected_positions.append(candidate.start_index)
                filtered_candidates.append(candidate)
        
        # Sort final candidates by position
        filtered_candidates.sort(key=lambda x: x.start_index)
        return filtered_candidates
    
    def _optimized_content_extraction(self, text: str, candidates: List[PotentialChapter],
                                    optimization_settings: Dict[str, any]) -> List[Chapter]:
        """Optimized content extraction with boundary optimization."""
        if not candidates:
            return []
        
        chapters = []
        
        # Pre-calculate sentence boundaries for efficient boundary optimization
        sentence_boundaries = self._precompute_sentence_boundaries(text)
        
        # Handle preface
        if candidates[0].start_index > 10:
            preface_content = text[:candidates[0].start_index].strip()
            if len(preface_content) > 10:
                chapters.append(Chapter(title="前言", content=preface_content))
        
        # Extract chapters with optimized boundary detection
        for i, candidate in enumerate(candidates):
            content_start, content_end = self._optimized_boundary_detection(
                text, candidate, candidates, i, sentence_boundaries
            )
            
            content = text[content_start:content_end].strip()
            if content:
                chapters.append(Chapter(title=candidate.title_text, content=content))
        
        return chapters
    
    def _precompute_sentence_boundaries(self, text: str) -> List[int]:
        """Precompute sentence boundaries for efficient boundary optimization."""
        sentence_endings = r'[.!?。！？]'
        boundaries = []
        
        for match in re.finditer(sentence_endings, text):
            boundaries.append(match.end())
        
        return boundaries
    
    def _optimized_boundary_detection(self, text: str, current_candidate: PotentialChapter,
                                    all_candidates: List[PotentialChapter], current_index: int,
                                    sentence_boundaries: List[int]) -> Tuple[int, int]:
        """Optimized boundary detection using precomputed sentence boundaries."""
        # Find content start
        content_start = current_candidate.end_index
        next_newline = text.find('\n', content_start)
        if next_newline != -1:
            content_start = next_newline + 1
        
        # Find content end
        if current_index + 1 < len(all_candidates):
            next_candidate = all_candidates[current_index + 1]
            content_end = next_candidate.start_index
            
            # Use binary search to find optimal boundary
            content_end = self._binary_search_boundary(content_end, sentence_boundaries)
        else:
            content_end = len(text)
        
        return content_start, content_end
    
    def _binary_search_boundary(self, initial_boundary: int, sentence_boundaries: List[int]) -> int:
        """Use binary search to find optimal sentence boundary."""
        # Find the closest sentence boundary before the initial boundary
        left, right = 0, len(sentence_boundaries) - 1
        best_boundary = initial_boundary
        
        while left <= right:
            mid = (left + right) // 2
            boundary = sentence_boundaries[mid]
            
            if boundary <= initial_boundary:
                if initial_boundary - boundary <= 50:  # Within 50 characters
                    best_boundary = boundary
                left = mid + 1
            else:
                right = mid - 1
        
        return best_boundary
    
    def _split_text_into_batches(self, text: str, batch_size: int) -> List[Tuple[int, str]]:
        """Split text into batches for parallel processing."""
        batches = []
        text_length = len(text)
        
        for i in range(0, text_length, batch_size):
            batch_end = min(i + batch_size, text_length)
            batch_text = text[i:batch_end]
            batches.append((i, batch_text))
        
        return batches
    
    def _match_patterns_in_batch(self, batch_text: str, patterns: List[ChapterPattern], 
                               batch_start: int) -> List[PotentialChapter]:
        """Match patterns in a text batch."""
        candidates = []
        
        for pattern in patterns:
            compiled_pattern = self._get_compiled_pattern(pattern)
            matches = compiled_pattern.finditer(batch_text)
            
            for match in matches:
                title_text = match.group(0).strip()
                
                if self._quick_exclusion_check(title_text):
                    continue
                
                candidate = PotentialChapter(
                    title_text=title_text,
                    start_index=batch_start + match.start(),
                    end_index=batch_start + match.end(),
                    confidence_score=pattern.confidence_score,
                    pattern_type=pattern.name
                )
                candidates.append(candidate)
        
        return candidates
    
    def _get_compiled_pattern(self, pattern: ChapterPattern) -> re.Pattern:
        """Get or compile regex pattern with caching."""
        if pattern.name not in self._compiled_patterns:
            flags = re.MULTILINE | re.IGNORECASE if pattern.language == 'en' else re.MULTILINE
            self._compiled_patterns[pattern.name] = re.compile(pattern.pattern, flags)
        
        return self._compiled_patterns[pattern.name]
    
    def _quick_exclusion_check(self, title_text: str) -> bool:
        """Quick exclusion check for obviously invalid titles."""
        # Length check
        if len(title_text) < 2 or len(title_text) > 50:
            return True
        
        # Check for file extensions
        if '.' in title_text and title_text.split('.')[-1].lower() in ['html', 'htm', 'txt', 'doc', 'pdf']:
            return True
        
        # Check for URLs
        if 'http' in title_text.lower() or 'www.' in title_text.lower():
            return True
        
        return False
    
    def _calculate_min_distance(self, candidate: PotentialChapter) -> int:
        """Calculate minimum distance based on confidence score."""
        if candidate.confidence_score >= 80:
            return 15
        elif candidate.confidence_score >= 60:
            return 30
        else:
            return 50
    
    def _determine_optimization_level(self, settings: Dict[str, any]) -> str:
        """Determine optimization level based on settings."""
        if settings.get('use_fast_scan', False) and settings.get('cache_patterns', False):
            return "aggressive"
        elif settings.get('use_fast_scan', False) or settings.get('cache_patterns', False):
            return "moderate"
        else:
            return "conservative"
    
    def _fallback_parsing(self, text: str, patterns: List[ChapterPattern]) -> List[Chapter]:
        """Fallback to basic parsing if optimization fails."""
        # Simple fallback implementation
        candidates = []
        
        for pattern in patterns:
            matches = re.finditer(pattern.pattern, text, re.MULTILINE)
            for match in matches:
                candidate = PotentialChapter(
                    title_text=match.group(0).strip(),
                    start_index=match.start(),
                    end_index=match.end(),
                    confidence_score=pattern.confidence_score,
                    pattern_type=pattern.name
                )
                candidates.append(candidate)
        
        # Basic filtering
        candidates = [c for c in candidates if c.confidence_score >= 50]
        candidates.sort(key=lambda x: x.start_index)
        
        # Basic content extraction
        chapters = []
        for i, candidate in enumerate(candidates):
            if i + 1 < len(candidates):
                content = text[candidate.end_index:candidates[i + 1].start_index].strip()
            else:
                content = text[candidate.end_index:].strip()
            
            if content:
                chapters.append(Chapter(title=candidate.title_text, content=content))
        
        return chapters
    
    def get_optimization_report(self) -> Dict[str, any]:
        """Get optimization performance report."""
        if self.metrics.total_time == 0:
            return {"status": "No optimization performed yet"}
        
        return {
            "performance": {
                "total_time": f"{self.metrics.total_time:.3f}s",
                "pattern_matching_time": f"{self.metrics.pattern_matching_time:.3f}s",
                "filtering_time": f"{self.metrics.filtering_time:.3f}s",
                "content_extraction_time": f"{self.metrics.content_extraction_time:.3f}s"
            },
            "results": {
                "candidates_found": self.metrics.candidates_found,
                "chapters_extracted": self.metrics.chapters_extracted,
                "extraction_rate": f"{(self.metrics.chapters_extracted / max(1, self.metrics.candidates_found)) * 100:.1f}%"
            },
            "optimization": {
                "level": self.metrics.optimization_level,
                "parallel_processing": self.enable_parallel_processing,
                "max_workers": self.max_workers,
                "pattern_cache_size": len(self._pattern_cache)
            }
        }