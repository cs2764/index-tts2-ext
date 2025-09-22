"""
File processor for handling TXT and EPUB file uploads and processing.
"""

import os
import time
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from .models import ProcessedFile, FileProcessingConfig
from .validation import FileValidator, ValidationResult, format_validation_errors_for_ui
from .console_feedback import ProcessingFeedbackManager, TextProcessingFeedback

import chardet


class FileProcessor:
    """Handles file upload and processing for TXT and EPUB files."""
    
    def __init__(self, config: Optional[FileProcessingConfig] = None, 
                 console_callback: Optional[Callable] = None):
        """Initialize the file processor with configuration."""
        self.config = config or FileProcessingConfig.default()
        self.encoding_detector = chardet.UniversalDetector()
        self.validator = FileValidator(
            max_file_size=self.config.max_file_size,
            supported_formats=self.config.supported_formats
        )
        
        # Initialize console feedback system
        self.feedback_manager = ProcessingFeedbackManager(console_callback)
        self.text_feedback = TextProcessingFeedback(self.feedback_manager)
        
        # Performance optimizations will be initialized lazily to avoid circular imports
        self._memory_optimizer = None
        self._chunked_processor = None
        self._preview_optimizer = None
    
    def process_file(self, file_path: str, use_native_chapters: bool = True) -> ProcessedFile:
        """
        Process uploaded file and return structured content.
        
        Args:
            file_path: Path to the uploaded file
            use_native_chapters: Whether to use native EPUB chapters (for EPUB files)
            
        Returns:
            ProcessedFile object with extracted content and metadata
            
        Raises:
            ValueError: If file validation fails or format is not supported
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        # Comprehensive file validation
        validation_result = self.validator.validate_file(file_path)
        
        if not validation_result.is_valid:
            # Format validation errors for user-friendly display
            error_info = format_validation_errors_for_ui(validation_result)
            error_messages = error_info.get('errors', [])
            raise ValueError(f"File validation failed:\n" + "\n".join(error_messages))
        
        # Log warnings if any
        if validation_result.has_warnings():
            warning_info = format_validation_errors_for_ui(validation_result)
            warning_messages = warning_info.get('warnings', [])
            print(f"File validation warnings:\n" + "\n".join(warning_messages))
        
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        file_size = validation_result.file_info.get('file_size', os.path.getsize(file_path))
        
        # Count original lines for feedback
        original_line_count = self._count_file_lines(file_path, file_ext)
        
        # Start processing feedback
        self.feedback_manager.start_processing(filename, file_size, original_line_count)
        
        start_time = time.time()
        
        # Use memory-optimized processing for large files
        if file_size > 10 * 1024 * 1024:  # 10MB threshold
            # Lazy import to avoid circular imports
            if self._memory_optimizer is None:
                from ..performance.memory_manager import MemoryOptimizer, ChunkedFileProcessor
                self._memory_optimizer = MemoryOptimizer()
                self._chunked_processor = ChunkedFileProcessor(self._memory_optimizer)
            
            with self._memory_optimizer.optimized_file_processing(file_size) as opt_info:
                if file_ext == 'txt':
                    if opt_info['use_chunking']:
                        # Use chunked processing for large files
                        content = self._chunked_processor.process_text_file_chunked(
                            file_path, self._process_text_chunk
                        )
                        encoding = self.detect_encoding(file_path)
                    else:
                        content = self._process_txt_file(file_path)
                        encoding = self.detect_encoding(file_path)
                elif file_ext == 'epub':
                    content = self.extract_epub_content(file_path, use_native_chapters)
                    encoding = 'utf-8'  # EPUB is always UTF-8
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")
                
                # Apply text processing if enabled
                if self.config.text_cleaning_enabled:
                    stage_start = self.feedback_manager.start_stage("文件清理")
                    content = self._clean_text_with_feedback(content)
                    self.feedback_manager.finish_stage("文件清理", stage_start)
        else:
            # Standard processing for smaller files
            if file_ext == 'txt':
                content = self._process_txt_file(file_path)
                encoding = self.detect_encoding(file_path)
            elif file_ext == 'epub':
                content = self.extract_epub_content(file_path, use_native_chapters)
                encoding = 'utf-8'  # EPUB is always UTF-8
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Apply text processing if enabled
            if self.config.text_cleaning_enabled:
                stage_start = self.feedback_manager.start_stage("文件清理")
                content = self._clean_text_with_feedback(content)
                self.feedback_manager.finish_stage("文件清理", stage_start)
        
        processing_time = time.time() - start_time
        
        # Finish processing feedback
        processed_size = len(content.encode('utf-8'))
        processed_line_count = len(content.split('\n'))
        self.feedback_manager.finish_processing(processed_size, processed_line_count)
        
        return ProcessedFile(
            filename=filename,
            content=content,
            original_encoding=encoding,
            chapters=[],  # Will be populated by chapter parser
            metadata={
                'file_extension': file_ext,
                'original_size': file_size,
                'use_native_chapters': use_native_chapters,
                'processing_summary': self.feedback_manager.get_processing_summary()
            },
            processing_time=processing_time,
            file_size=file_size,
            created_at=None  # Will be set in __post_init__
        )
    
    def detect_encoding(self, file_path: str) -> str:
        """
        Auto-detect file encoding for TXT files.
        Supports UTF-8, GBK, GB2312 and other common encodings.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding string
        """
        self.encoding_detector.reset()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks for better detection
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.encoding_detector.feed(chunk)
                    if self.encoding_detector.done:
                        break
            
            self.encoding_detector.close()
            result = self.encoding_detector.result
            
            if result and result['confidence'] >= self.config.encoding_detection_confidence:
                detected_encoding = result['encoding'].lower()
                
                # Map common encoding variations
                encoding_map = {
                    'gb2312': 'gb2312',
                    'gbk': 'gbk',
                    'utf-8': 'utf-8',
                    'utf8': 'utf-8',
                    'ascii': 'utf-8',  # ASCII is a subset of UTF-8
                    'windows-1252': 'utf-8',  # Common fallback
                }
                
                return encoding_map.get(detected_encoding, detected_encoding)
            else:
                # Fallback to UTF-8 if detection confidence is low
                return 'utf-8'
                
        except Exception as e:
            # If detection fails, fallback to UTF-8
            print(f"Warning: Encoding detection failed for {file_path}: {e}")
            return 'utf-8'
    
    def extract_epub_content(self, file_path: str, use_native_chapters: bool) -> str:
        """
        Extract text content from EPUB files.
        
        Args:
            file_path: Path to the EPUB file
            use_native_chapters: Whether to preserve native chapter structure
            
        Returns:
            Extracted text content with optional chapter structure
        """
        try:
            import ebooklib
            from ebooklib import epub
        except ImportError:
            raise ImportError("ebooklib is required for EPUB processing. Install with: uv add ebooklib")
        
        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read EPUB file: {e}")
        
        content_parts = []
        
        if use_native_chapters:
            # Use native EPUB chapter structure
            content_parts = self._extract_epub_with_native_chapters(book)
        else:
            # Extract all text content without chapter structure
            content_parts = self._extract_epub_text_only(book)
        
        # Join all content and clean it
        full_content = '\n\n'.join(content_parts)
        return self._clean_epub_content(full_content)
    
    def _extract_epub_with_native_chapters(self, book) -> List[str]:
        """
        Extract EPUB content preserving native chapter structure.
        
        Args:
            book: EPUB book object from ebooklib
            
        Returns:
            List of chapter contents with titles
        """
        try:
            import ebooklib
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(f"Required dependencies missing: {e}")
        
        content_parts = []
        
        # Get the spine (reading order) of the book
        spine = book.spine
        
        for item_id, _ in spine:
            item = book.get_item_with_id(item_id)
            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    # Parse HTML content
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Extract text content
                    text_content = soup.get_text()
                    
                    if text_content.strip():
                        # Try to find chapter title
                        chapter_title = self._extract_chapter_title(soup)
                        
                        if chapter_title:
                            content_parts.append(f"# {chapter_title}\n\n{text_content.strip()}")
                        else:
                            content_parts.append(text_content.strip())
                            
                except Exception as e:
                    print(f"Warning: Failed to process EPUB item {item_id}: {e}")
                    continue
        
        return content_parts
    
    def _extract_epub_text_only(self, book) -> List[str]:
        """
        Extract EPUB content as plain text without chapter structure.
        
        Args:
            book: EPUB book object from ebooklib
            
        Returns:
            List of text content from all documents
        """
        try:
            import ebooklib
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(f"Required dependencies missing: {e}")
        
        content_parts = []
        
        # Get all document items
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    # Parse HTML content
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Extract text content
                    text_content = soup.get_text()
                    
                    if text_content.strip():
                        content_parts.append(text_content.strip())
                        
                except Exception as e:
                    print(f"Warning: Failed to process EPUB item: {e}")
                    continue
        
        return content_parts
    
    def _extract_chapter_title(self, soup) -> Optional[str]:
        """
        Extract chapter title from HTML content.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            
        Returns:
            Chapter title if found, None otherwise
        """
        # Look for common chapter title patterns
        title_selectors = [
            'h1', 'h2', 'h3',  # Standard headings
            '.chapter-title', '.title',  # Common CSS classes
            '[class*="title"]', '[class*="chapter"]'  # Partial class matches
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title_text = title_element.get_text().strip()
                if title_text and len(title_text) < 200:  # Reasonable title length
                    return title_text
        
        return None
    
    def _clean_epub_content(self, content: str) -> str:
        """
        Clean and normalize EPUB text content.
        
        Args:
            content: Raw extracted text content
            
        Returns:
            Cleaned and normalized text content
        """
        if not content:
            return content
        
        # Remove excessive whitespace
        import re
        
        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)
        
        # Replace multiple newlines with double newlines (paragraph breaks)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Remove leading/trailing whitespace from lines
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        content = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines at start and end
        content = content.strip()
        
        return content
    
    def _process_txt_file(self, file_path: str) -> str:
        """
        Process a TXT file with encoding detection and fallback handling.
        Supports UTF-8, GBK, GB2312 and other common encodings.
        """
        encoding = self.detect_encoding(file_path)
        
        # Try detected encoding first
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            pass
        
        # Fallback encodings in order of preference
        fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        
        for fallback_encoding in fallback_encodings:
            if fallback_encoding == encoding:
                continue  # Already tried
                
            try:
                with open(file_path, 'r', encoding=fallback_encoding) as f:
                    content = f.read()
                print(f"Warning: Used fallback encoding {fallback_encoding} for {file_path}")
                return content
            except UnicodeDecodeError:
                continue
        
        # Final fallback with error replacement
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            print(f"Warning: Used UTF-8 with error replacement for {file_path}")
            return content
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate file format, size, and readability using comprehensive validation.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        return self.validator.validate_file(file_path)
    
    def validate_file_simple(self, file_path: str) -> bool:
        """
        Simple file validation that returns True/False (legacy compatibility).
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid, False otherwise
            
        Raises:
            ValueError: If validation fails with specific error message
        """
        validation_result = self.validator.validate_file(file_path)
        
        if not validation_result.is_valid:
            # Format validation errors for user-friendly display
            error_info = format_validation_errors_for_ui(validation_result)
            error_messages = error_info.get('errors', [])
            raise ValueError(f"File validation failed:\n" + "\n".join(error_messages))
        
        return True
    
    def generate_file_preview(self, file_path: str, preview_lines: int = 40) -> 'FilePreview':
        """
        Generate optimized file preview with caching.
        
        Args:
            file_path: Path to the file
            preview_lines: Number of lines to include in preview
            
        Returns:
            FilePreview object with preview content and metadata
        """
        # Lazy import to avoid circular imports
        if self._preview_optimizer is None:
            from ..performance.preview_optimizer import get_preview_optimizer
            self._preview_optimizer = get_preview_optimizer()
        
        preview, metrics = self._preview_optimizer.generate_optimized_preview(
            file_path, preview_lines
        )
        
        # Log performance metrics if console callback is available
        if self.feedback_manager.console_callback:
            if metrics.cache_hit:
                self.feedback_manager.console_callback(f"文件预览已缓存 (用时 {metrics.generation_time:.3f}s)")
            else:
                self.feedback_manager.console_callback(
                    f"生成文件预览 (用时 {metrics.generation_time:.3f}s, "
                    f"编码检测 {metrics.encoding_detection_time:.3f}s, "
                    f"处理 {metrics.text_processing_time:.3f}s)"
                )
        
        return preview
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        info = {
            'filename': filename,
            'file_extension': file_ext,
            'file_size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime),
            'is_supported': file_ext in self.config.supported_formats
        }
        
        if file_ext == 'txt':
            info['detected_encoding'] = self.detect_encoding(file_path)
        
        return info
    
    def _clean_text(self, text: str) -> str:
        """
        Apply text cleaning operations based on configuration.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text content
        """
        if not text:
            return text
        
        # Only apply cleaning if enabled
        if not self.config.text_cleaning_enabled:
            return text
        
        # Remove invisible and control characters
        if self.config.clean_special_characters:
            text = self._remove_special_characters(text)
        
        # Merge consecutive empty lines
        if self.config.merge_empty_lines:
            text = self._merge_empty_lines(text)
        
        # Remove excess spaces
        if self.config.remove_excess_spaces:
            text = self._remove_excess_spaces(text)
        
        # Apply intelligent sentence breaking
        if self.config.intelligent_sentence_breaking:
            text = self._apply_sentence_breaking(text)
        
        return text
    
    def _remove_special_characters(self, text: str) -> str:
        """Remove invisible characters and control characters."""
        if not text:
            return text
        
        import re
        import unicodedata
        
        # Remove control characters (except newlines, tabs, and carriage returns)
        # Keep \n (10), \r (13), \t (9) but remove other control characters
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C') 
                      or char in '\n\r\t')
        
        # Remove zero-width characters
        zero_width_chars = [
            '\u200b',  # Zero Width Space
            '\u200c',  # Zero Width Non-Joiner
            '\u200d',  # Zero Width Joiner
            '\u2060',  # Word Joiner
            '\ufeff',  # Zero Width No-Break Space (BOM)
        ]
        for char in zero_width_chars:
            text = text.replace(char, '')
        
        # Remove other invisible characters
        invisible_chars = [
            '\u00a0',  # Non-breaking space
            '\u2000',  # En Quad
            '\u2001',  # Em Quad
            '\u2002',  # En Space
            '\u2003',  # Em Space
            '\u2004',  # Three-Per-Em Space
            '\u2005',  # Four-Per-Em Space
            '\u2006',  # Six-Per-Em Space
            '\u2007',  # Figure Space
            '\u2008',  # Punctuation Space
            '\u2009',  # Thin Space
            '\u200a',  # Hair Space
            '\u202f',  # Narrow No-Break Space
            '\u205f',  # Medium Mathematical Space
            '\u3000',  # Ideographic Space
        ]
        for char in invisible_chars:
            text = text.replace(char, ' ')
        
        return text
    
    def _merge_empty_lines(self, text: str) -> str:
        """Merge consecutive empty lines."""
        if not text:
            return text
        
        import re
        
        # Replace multiple consecutive empty lines with double newlines (paragraph breaks)
        # This preserves paragraph structure while removing excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Also handle cases with only spaces/tabs on lines
        text = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', text)
        
        return text
    
    def _remove_excess_spaces(self, text: str) -> str:
        """Remove excess spaces between Chinese and English text."""
        if not text:
            return text
        
        import re
        
        # Remove multiple consecutive spaces (replace with single space)
        text = re.sub(r' +', ' ', text)
        
        # Remove spaces between Chinese characters and punctuation
        # Chinese character ranges: \u4e00-\u9fff (CJK Unified Ideographs)
        # Also include: \u3400-\u4dbf (CJK Extension A), \uf900-\ufaff (CJK Compatibility)
        chinese_char = r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]'
        
        # Remove spaces between Chinese characters
        text = re.sub(f'({chinese_char})\\s+({chinese_char})', r'\1\2', text)
        
        # Remove spaces between Chinese characters and Chinese punctuation
        chinese_punct = r'[，。！？；：""''（）【】《》〈〉「」『』〔〕]'
        text = re.sub(f'({chinese_char})\\s+({chinese_punct})', r'\1\2', text)
        text = re.sub(f'({chinese_punct})\\s+({chinese_char})', r'\1\2', text)
        
        # Keep single spaces between Chinese and English/numbers for readability
        # This is intentional - we want to preserve spaces between different scripts
        
        # Remove trailing spaces at end of lines
        text = re.sub(r' +\n', '\n', text)
        
        # Remove leading spaces at beginning of lines
        text = re.sub(r'\n +', '\n', text)
        
        # Remove leading spaces at the very beginning
        text = text.lstrip(' ')
        
        return text
    
    def _apply_sentence_breaking(self, text: str) -> str:
        """Apply intelligent sentence breaking based on punctuation."""
        if not text:
            return text
        
        import re
        
        # Define sentence-ending punctuation for different languages
        # English: . ! ?
        # Chinese: 。！？
        sentence_endings = r'[.!?。！？]'
        
        # Split long sentences at appropriate punctuation marks
        # Look for sentences that are too long (over 100 characters without breaks)
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            if len(line) <= 100:
                processed_lines.append(line)
                continue
            
            # For long lines, try to break at sentence boundaries
            # Find sentence endings followed by space and capital letter or Chinese character
            sentence_breaks = list(re.finditer(
                f'({sentence_endings})\\s*([A-Z\\u4e00-\\u9fff])', 
                line
            ))
            
            # Also look for Chinese sentence endings not followed by space
            chinese_breaks = list(re.finditer(r'[。！？]([\u4e00-\u9fff])', line))
            sentence_breaks.extend(chinese_breaks)
            
            if not sentence_breaks:
                # No clear sentence breaks found, try other punctuation
                # Break at commas, semicolons, or colons if the line is very long
                if len(line) > 200:
                    other_breaks = list(re.finditer(r'[,;:，；：]\s*', line))
                    if other_breaks:
                        # Use the break closest to the middle of the line
                        mid_point = len(line) // 2
                        best_break = min(other_breaks, key=lambda x: abs(x.start() - mid_point))
                        break_pos = best_break.end()
                        processed_lines.append(line[:break_pos].rstrip())
                        processed_lines.append(line[break_pos:].lstrip())
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            else:
                # Sort breaks by position
                sentence_breaks.sort(key=lambda x: x.start())
                
                # Break at sentence boundaries
                current_pos = 0
                for match in sentence_breaks:
                    if match.start() - current_pos > 50:  # Only break if segment is reasonably long
                        break_pos = match.start() + 1  # Include the punctuation
                        processed_lines.append(line[current_pos:break_pos].rstrip())
                        current_pos = break_pos
                
                # Add the remaining part
                if current_pos < len(line):
                    processed_lines.append(line[current_pos:].lstrip())
        
        # Join the processed lines back together
        result = '\n'.join(processed_lines)
        
        # Clean up any double newlines that might have been created
        result = re.sub(r'\n\n+', '\n\n', result)
        
        return result
    
    def _process_text_chunk(self, chunk: str) -> str:
        """
        Process a text chunk with encoding handling.
        
        Args:
            chunk: Text chunk to process
            
        Returns:
            Processed text chunk
        """
        # Apply basic text cleaning to chunk
        if self.config.text_cleaning_enabled:
            return self._clean_text(chunk)
        return chunk
    
    def _count_file_lines(self, file_path: str, file_ext: str) -> int:
        """
        Count the number of lines in a file.
        
        Args:
            file_path: Path to the file
            file_ext: File extension
            
        Returns:
            Number of lines in the file
        """
        try:
            if file_ext == 'txt':
                encoding = self.detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as f:
                    return sum(1 for _ in f)
            elif file_ext == 'epub':
                # For EPUB, estimate based on extracted content
                content = self.extract_epub_content(file_path, True)
                return len(content.split('\n'))
            else:
                return 0
        except Exception:
            return 0
    
    def _clean_text_with_feedback(self, text: str) -> str:
        """
        Apply text cleaning operations with detailed feedback.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text content
        """
        if not text:
            return text
        
        # Only apply cleaning if enabled
        if not self.config.text_cleaning_enabled:
            return text
        
        original_text = text
        
        # Remove invisible and control characters
        if self.config.clean_special_characters:
            cleaned_text = self._remove_special_characters(text)
            invisible_removed = self.text_feedback.track_invisible_character_removal(text, cleaned_text)
            special_removed = self.text_feedback.track_special_character_removal(text, cleaned_text)
            
            if invisible_removed > 0:
                self.feedback_manager.log_cleaning_operation("移除不可见字符", invisible_removed)
            if special_removed > 0:
                self.feedback_manager.log_cleaning_operation("清理特殊字符", special_removed)
            
            text = cleaned_text
        
        # Merge consecutive empty lines
        if self.config.merge_empty_lines:
            cleaned_text = self._merge_empty_lines(text)
            lines_merged = self.text_feedback.track_empty_line_merging(text, cleaned_text)
            
            if lines_merged > 0:
                self.feedback_manager.log_cleaning_operation("合并空行", lines_merged)
            
            text = cleaned_text
        
        # Remove excess spaces
        if self.config.remove_excess_spaces:
            cleaned_text = self._remove_excess_spaces(text)
            spaces_removed = self.text_feedback.track_space_removal(text, cleaned_text)
            
            if spaces_removed > 0:
                self.feedback_manager.log_cleaning_operation("处理多余空格", spaces_removed)
            
            text = cleaned_text
        
        # Apply intelligent sentence breaking
        if self.config.intelligent_sentence_breaking:
            processed_text = self._apply_sentence_breaking(text)
            sentences_broken = self.text_feedback.track_sentence_breaking(text, processed_text)
            
            if sentences_broken > 0:
                self.feedback_manager.log_cleaning_operation("分割长句", sentences_broken)
            
            text = processed_text
        
        return text