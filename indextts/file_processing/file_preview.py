"""
File preview generation for uploaded files.
"""

import os
import chardet
from dataclasses import dataclass
from typing import Optional


@dataclass
class FilePreview:
    """Data model for file preview information."""
    filename: str
    preview_text: str
    total_lines: int
    encoding: str
    file_size: str
    preview_truncated: bool
    cleaning_stats: Optional[dict] = None  # Add cleaning statistics


class FilePreviewGenerator:
    """Generates previews for uploaded files showing first 40 lines."""
    
    def __init__(self, preview_lines: int = 40):
        """Initialize with configurable preview line count."""
        self.preview_lines = preview_lines
    
    def generate_text_preview_with_cleaning(self, file_path: str, enable_cleaning: bool = False) -> FilePreview:
        """Generate preview with optional file cleaning and statistics."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        file_size = self._format_file_size(os.path.getsize(file_path))
        
        # Detect encoding for text files
        encoding = self._detect_encoding(file_path)
        
        # Read and optionally clean file content
        try:
            # Read the file content
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                original_content = f.read()
            
            # Apply cleaning if enabled
            if enable_cleaning:
                cleaned_content, cleaning_stats = self._clean_text_content(original_content)
                content_to_preview = cleaned_content
            else:
                content_to_preview = original_content
                cleaning_stats = None
            
            # Split into lines for preview
            lines = content_to_preview.split('\n')
            preview_lines = lines[:self.preview_lines]
            preview_text = '\n'.join(preview_lines)
            preview_truncated = len(lines) > self.preview_lines
            
            print(f"✅ 成功读取文件: {filename} ({encoding})")
            if cleaning_stats:
                print(f"🧹 文件清理完成: {cleaning_stats}")
            
            return FilePreview(
                filename=filename,
                preview_text=preview_text,
                total_lines=len(lines),
                encoding=encoding,
                file_size=file_size,
                preview_truncated=preview_truncated,
                cleaning_stats=cleaning_stats
            )
            
        except Exception as e:
            raise Exception(f"Error reading file {filename}: {str(e)}")
    
    def generate_text_preview(self, file_path: str) -> FilePreview:
        """Generate preview of first 40 lines from uploaded file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        file_size = self._format_file_size(os.path.getsize(file_path))
        
        # Detect encoding for text files
        encoding = self._detect_encoding(file_path)
        
        # Read file content with improved error handling
        try:
            # First try with detected encoding
            try:
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    lines = []
                    total_lines = 0
                    
                    for line_num, line in enumerate(f, 1):
                        total_lines = line_num
                        if line_num <= self.preview_lines:
                            # Clean up line endings and normalize whitespace
                            clean_line = line.rstrip('\n\r').replace('\t', '    ')
                            lines.append(clean_line)
                        elif line_num > self.preview_lines:
                            # Continue counting lines but don't store content
                            continue
                    
                    preview_text = '\n'.join(lines)
                    preview_truncated = total_lines > self.preview_lines
                    
                    print(f"✅ 成功读取文件: {filename} ({encoding})")
                    
                    return FilePreview(
                        filename=filename,
                        preview_text=preview_text,
                        total_lines=total_lines,
                        encoding=encoding,
                        file_size=file_size,
                        preview_truncated=preview_truncated
                    )
                    
            except UnicodeDecodeError as e:
                print(f"⚠️ 编码 {encoding} 读取失败，尝试其他编码: {str(e)}")
                
                # Try alternative encodings (including UTF-16 variants)
                for alt_encoding in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'gbk', 'gb18030', 'big5', 'latin-1']:
                    if alt_encoding == encoding:
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding=alt_encoding, errors='replace') as f:
                            lines = []
                            total_lines = 0
                            
                            for line_num, line in enumerate(f, 1):
                                total_lines = line_num
                                if line_num <= self.preview_lines:
                                    clean_line = line.rstrip('\n\r').replace('\t', '    ')
                                    # Remove replacement characters
                                    clean_line = clean_line.replace('�', '')
                                    lines.append(clean_line)
                                elif line_num > self.preview_lines:
                                    continue
                            
                            preview_text = '\n'.join(lines)
                            preview_truncated = total_lines > self.preview_lines
                            
                            print(f"✅ 使用备用编码成功读取: {alt_encoding}")
                            
                            return FilePreview(
                                filename=filename,
                                preview_text=preview_text,
                                total_lines=total_lines,
                                encoding=alt_encoding,
                                file_size=file_size,
                                preview_truncated=preview_truncated
                            )
                            
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                # If all encodings fail, use replace mode
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = []
                    total_lines = 0
                    
                    for line_num, line in enumerate(f, 1):
                        total_lines = line_num
                        if line_num <= self.preview_lines:
                            clean_line = line.rstrip('\n\r').replace('\t', '    ')
                            clean_line = clean_line.replace('�', '[?]')  # Mark replacement chars
                            lines.append(clean_line)
                        elif line_num > self.preview_lines:
                            continue
                    
                    preview_text = '\n'.join(lines)
                    preview_truncated = total_lines > self.preview_lines
                    
                    print(f"⚠️ 使用 UTF-8 替换模式读取文件")
                    
                    return FilePreview(
                        filename=filename,
                        preview_text=preview_text,
                        total_lines=total_lines,
                        encoding="UTF-8 (with replacements)",
                        file_size=file_size,
                        preview_truncated=preview_truncated
                    )
                
        except Exception as e:
            raise Exception(f"Error reading file {filename}: {str(e)}")
    
    def generate_epub_preview(self, file_path: str) -> FilePreview:
        """Generate preview for EPUB files by extracting text content."""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("ebooklib and beautifulsoup4 are required for EPUB processing")
        
        filename = os.path.basename(file_path)
        file_size = self._format_file_size(os.path.getsize(file_path))
        
        try:
            book = epub.read_epub(file_path)
            
            # Extract text from EPUB
            text_content = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    if text.strip():
                        text_content.append(text.strip())
            
            # Combine all text and split into lines
            full_text = '\n'.join(text_content)
            lines = full_text.split('\n')
            
            # Generate preview
            preview_lines = lines[:self.preview_lines]
            preview_text = '\n'.join(preview_lines)
            preview_truncated = len(lines) > self.preview_lines
            
            return FilePreview(
                filename=filename,
                preview_text=preview_text,
                total_lines=len(lines),
                encoding="UTF-8",  # EPUB is always UTF-8
                file_size=file_size,
                preview_truncated=preview_truncated
            )
            
        except Exception as e:
            raise Exception(f"Error processing EPUB file {filename}: {str(e)}")
    
    def format_preview_display(self, preview: FilePreview) -> str:
        """Format preview text for UI display with file information and cleaning results."""
        import html
        
        # Validate and clean the preview text for display
        clean_preview_text = self._validate_and_clean_text(preview.preview_text)
        
        # Use base64 encoding to ensure proper character display
        import base64
        
        # Convert text to base64 to avoid encoding issues in HTML
        text_bytes = clean_preview_text.encode('utf-8')
        text_b64 = base64.b64encode(text_bytes).decode('ascii')
        
        # Enhanced encoding detection and display
        encoding_display = preview.encoding
        if preview.encoding.lower() in ['gbk', 'gb2312', 'gb18030']:
            encoding_display = f"{preview.encoding} (简体中文)"
        elif preview.encoding.lower() in ['big5', 'big5-hkscs']:
            encoding_display = f"{preview.encoding} (繁体中文)"
        elif preview.encoding.lower().startswith('utf'):
            encoding_display = f"{preview.encoding} (Unicode)"
        
        # Create cleaning results section if available
        cleaning_section = ""
        if preview.cleaning_stats:
            stats = preview.cleaning_stats
            cleaning_items = []
            
            if stats.get('excess_spaces_removed', 0) > 0:
                cleaning_items.append(f"• 清理多余空格: {stats['excess_spaces_removed']} 处")
            if stats.get('empty_lines_merged', 0) > 0:
                cleaning_items.append(f"• 合并空行: {stats['empty_lines_merged']} 处")
            if stats.get('special_characters_removed', 0) > 0:
                cleaning_items.append(f"• 移除特殊字符: {stats['special_characters_removed']} 个")
            if stats.get('invisible_characters_removed', 0) > 0:
                cleaning_items.append(f"• 移除不可见字符: {stats['invisible_characters_removed']} 个")
            if stats.get('sentences_broken', 0) > 0:
                cleaning_items.append(f"• 分割长句: {stats['sentences_broken']} 处")
            
            if cleaning_items:
                cleaning_section = f"""
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; padding: 10px; margin-bottom: 15px; border-left: 4px solid #28a745;">
                    <h5 style="margin: 0 0 8px 0; color: #1f2328; font-size: 14px; font-weight: 600;">🧹 文件清理结果</h5>
                    <div style="font-size: 13px; color: #1f2328;">
                        {chr(10).join(cleaning_items)}<br>
                        <strong>行数变化:</strong> {stats.get('original_lines', 0)} → {stats.get('final_lines', 0)} ({stats.get('lines_change', 0):+d})<br>
                        <strong>字符变化:</strong> {stats.get('original_length', 0):,} → {stats.get('final_length', 0):,} ({stats.get('length_change', 0):+,})
                    </div>
                </div>
                """
            else:
                cleaning_section = f"""
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 6px; padding: 10px; margin-bottom: 15px; border-left: 4px solid #17a2b8;">
                    <h5 style="margin: 0 0 8px 0; color: #1f2328; font-size: 14px; font-weight: 600;">✨ 文件清理结果</h5>
                    <div style="font-size: 13px; color: #1f2328;">
                        文件内容已经很干净，无需清理
                    </div>
                </div>
                """
        
        # Create HTML directly embedding escaped text (no JS needed)
        escaped_text = html.escape(clean_preview_text)
        preview_html = f"""
        <div style=\"background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; font-family: 'Microsoft YaHei', 'SimHei', 'Segoe UI', Arial, sans-serif;\">
            <div style=\"background: #e9ecef; padding: 10px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #007bff;\">
                <h4 style=\"margin: 0 0 8px 0; color: #495057; font-size: 16px;\">📄 {html.escape(preview.filename)}</h4>
                <div style=\"font-size: 13px; color: #6c757d;\">
                    📊 大小: {preview.file_size} | 🔤 编码: {encoding_display} | 📝 总行数: {preview.total_lines:,}
                    {' | ⚠️ 预览已截断' if preview.preview_truncated else ''}
                </div>
            </div>
            {cleaning_section}
            <div style=\"background: white; border: 1px solid #e9ecef; border-radius: 6px; padding: 12px; max-height: 400px; overflow-y: auto;\">
                <pre style=\"margin: 0; font-family: 'Consolas', 'Monaco', 'Microsoft YaHei', 'SimHei', 'Courier New', monospace; font-size: 13px; line-height: 1.4; color: #212529; white-space: pre-wrap; word-wrap: break-word;\">{escaped_text}</pre>
            </div>
        </div>
        """
        
        return preview_html
    
    def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding using chardet with improved Chinese support."""
        try:
            with open(file_path, 'rb') as f:
                # Read more data for better detection
                raw_data = f.read(100000)  # Read first 100KB for better detection
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                print(f"🔍 编码检测结果: {encoding} (置信度: {confidence:.2f})")
                
                # Improved encoding detection for Chinese files
                if encoding:
                    encoding_lower = encoding.lower()
                    
                    # Handle UTF-16 variants first (important for correct detection)
                    if encoding_lower in ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-16le', 'utf-16be']:
                        # Verify UTF-16 encoding by trying to decode
                        try:
                            with open(file_path, 'r', encoding='utf-16') as test_f:
                                test_content = test_f.read(1000)
                                print(f"✅ 检测到 UTF-16 编码，成功验证")
                                return 'utf-16'
                        except (UnicodeDecodeError, UnicodeError):
                            # Try UTF-16 with different byte order
                            try:
                                with open(file_path, 'r', encoding='utf-16-le') as test_f:
                                    test_content = test_f.read(1000)
                                    print(f"✅ 检测到 UTF-16LE 编码，成功验证")
                                    return 'utf-16-le'
                            except (UnicodeDecodeError, UnicodeError):
                                try:
                                    with open(file_path, 'r', encoding='utf-16-be') as test_f:
                                        test_content = test_f.read(1000)
                                        print(f"✅ 检测到 UTF-16BE 编码，成功验证")
                                        return 'utf-16-be'
                                except (UnicodeDecodeError, UnicodeError):
                                    print(f"⚠️ UTF-16 编码验证失败，继续尝试其他编码")
                    
                    # Handle Chinese encodings with better mapping
                    elif encoding_lower in ['gb2312', 'gbk', 'gb18030', 'windows-1252']:
                        # Test if GBK works better
                        try:
                            with open(file_path, 'r', encoding='gbk') as test_f:
                                test_content = test_f.read(1000)
                                # Check if content looks like Chinese
                                chinese_chars = sum(1 for char in test_content if '\u4e00' <= char <= '\u9fff')
                                if chinese_chars > len(test_content) * 0.1:  # More than 10% Chinese chars
                                    print(f"✅ 检测到中文内容，使用 GBK 编码")
                                    return 'gbk'
                        except (UnicodeDecodeError, UnicodeError):
                            pass
                        
                        return 'gbk'
                    elif encoding_lower in ['big5', 'big5-hkscs']:
                        return 'big5'
                    elif encoding_lower.startswith('utf') and encoding_lower != 'utf-16':
                        return 'utf-8'
                    elif encoding_lower in ['ascii'] and confidence > 0.7:
                        return 'utf-8'  # ASCII is compatible with UTF-8
                    elif confidence > 0.8:
                        return encoding
                
                # Enhanced fallback: try common encodings with validation
                # Put UTF-16 variants earlier in the list for better detection
                test_encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'gbk', 'gb18030', 'big5', 'latin-1']
                
                for test_encoding in test_encodings:
                    try:
                        with open(file_path, 'r', encoding=test_encoding, errors='strict') as test_f:
                            test_content = test_f.read(2000)  # Read more for better validation
                            
                            # Check for common encoding issues
                            if '锘�' in test_content or '�' in test_content:
                                continue  # Skip if contains replacement characters
                            
                            # Special handling for UTF-16 variants
                            if test_encoding.startswith('utf-16'):
                                # Verify that content is readable and not garbled
                                if len(test_content) > 0 and not all(ord(char) > 0xFFFF for char in test_content[:100]):
                                    print(f"✅ 成功使用 {test_encoding} 编码读取文件")
                                    return test_encoding
                            
                            # Prefer UTF-8 for clean ASCII content
                            elif test_encoding == 'utf-8' and all(ord(char) < 128 for char in test_content[:500]):
                                print(f"✅ 检测到纯 ASCII 内容，使用 UTF-8 编码")
                                return 'utf-8'
                            
                            # Prefer GBK for Chinese content
                            elif test_encoding == 'gbk':
                                chinese_chars = sum(1 for char in test_content if '\u4e00' <= char <= '\u9fff')
                                if chinese_chars > 0:
                                    print(f"✅ 检测到中文内容，使用 GBK 编码")
                                    return 'gbk'
                            
                            else:
                                print(f"✅ 成功使用 {test_encoding} 编码读取文件")
                                return test_encoding
                            
                    except (UnicodeDecodeError, UnicodeError, LookupError):
                        continue
                        
        except Exception as e:
            print(f"⚠️ 编码检测异常: {str(e)}")
            
        print(f"⚠️ 使用默认 UTF-8 编码")
        return 'utf-8'  # Final fallback
    
    def _clean_text_content(self, text: str) -> tuple[str, dict]:
        """Clean text content and return statistics."""
        if not text:
            return "", {}
        
        original_lines = text.count('\n') + 1
        original_length = len(text)
        
        # Initialize statistics
        stats = {
            'original_lines': original_lines,
            'original_length': original_length,
            'excess_spaces_removed': 0,
            'empty_lines_merged': 0,
            'special_characters_removed': 0,
            'invisible_characters_removed': 0,
            'sentences_broken': 0
        }
        
        cleaned_text = text
        
        # 1. Remove invisible characters
        invisible_chars = ['\ufeff', '\u200b', '\u200c', '\u200d', '\u2060']
        for char in invisible_chars:
            count = cleaned_text.count(char)
            if count > 0:
                cleaned_text = cleaned_text.replace(char, '')
                stats['invisible_characters_removed'] += count
        
        # 2. Normalize line endings
        cleaned_text = cleaned_text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 3. Remove excess spaces (multiple spaces -> single space)
        import re
        original_spaces = len(re.findall(r' {2,}', cleaned_text))
        cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
        stats['excess_spaces_removed'] = original_spaces
        
        # 4. Merge consecutive empty lines (3+ empty lines -> 2 empty lines)
        original_empty_blocks = len(re.findall(r'\n\s*\n\s*\n', cleaned_text))
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        stats['empty_lines_merged'] = original_empty_blocks
        
        # 5. Remove special characters that might cause issues
        problematic_chars = ['锘�', '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08']
        for char in problematic_chars:
            count = cleaned_text.count(char)
            if count > 0:
                cleaned_text = cleaned_text.replace(char, '')
                stats['special_characters_removed'] += count
        
        # 6. Break very long sentences (optional, for better TTS)
        lines = cleaned_text.split('\n')
        broken_sentences = 0
        for i, line in enumerate(lines):
            if len(line) > 200:  # Very long line
                # Try to break at punctuation
                import re
                sentences = re.split(r'([。！？；])', line)
                if len(sentences) > 1:
                    # Rejoin with line breaks after punctuation
                    new_line = ''
                    for j in range(0, len(sentences)-1, 2):
                        if j+1 < len(sentences):
                            new_line += sentences[j] + sentences[j+1] + '\n'
                        else:
                            new_line += sentences[j]
                    lines[i] = new_line.rstrip('\n')
                    broken_sentences += 1
        
        stats['sentences_broken'] = broken_sentences
        cleaned_text = '\n'.join(lines)
        
        # Final statistics
        final_lines = cleaned_text.count('\n') + 1
        final_length = len(cleaned_text)
        
        stats['final_lines'] = final_lines
        stats['final_length'] = final_length
        stats['lines_change'] = final_lines - original_lines
        stats['length_change'] = final_length - original_length
        
        return cleaned_text, stats
    
    def _validate_and_clean_text(self, text: str) -> str:
        """Validate and clean text for proper display."""
        if not text:
            return ""
        
        # Remove or replace problematic characters
        cleaned_text = text
        
        # Replace common encoding artifacts
        replacements = {
            '锘�': '',  # UTF-8 BOM artifact
            '\ufeff': '',  # BOM character
            '\x00': '',  # Null character
            '\r\n': '\n',  # Normalize line endings
            '\r': '\n',  # Mac line endings
        }
        
        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)
        
        # Ensure text is valid Unicode
        try:
            # Try to encode and decode to validate
            cleaned_text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            # If there are encoding issues, clean them up
            cleaned_text = cleaned_text.encode('utf-8', errors='replace').decode('utf-8')
        
        return cleaned_text
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"