"""
Audio format converter for handling WAV, MP3, and M4B format conversions.
"""

import os
import subprocess
import tempfile
import time
import logging
from typing import List, Dict, Optional, Union
import numpy as np
# Optional imports with safe fallbacks to allow tests to patch `ffmpeg`
try:
    import ffmpeg  # provided by ffmpeg-python
except Exception:  # noqa: BLE001
    class _FFmpegStub:
        pass
    ffmpeg = _FFmpegStub()  # type: ignore

try:
    import librosa
except Exception:  # noqa: BLE001
    librosa = None  # type: ignore

try:
    import soundfile as sf
except Exception:  # noqa: BLE001
    sf = None  # type: ignore
from .models import AudioFormatConfig, SegmentationConfig, AudiobookChapter
from .error_handling import (
    AudioErrorHandler, AudioErrorType, AudioGenerationContext,
    AudioGenerationRecoveryManager, AudioGenerationRetryWrapper
)
from ..chapter_parsing.models import Chapter

logger = logging.getLogger(__name__)


class AudioFormatConverter:
    """Handles audio format conversion and M4B audiobook creation."""
    
    def __init__(self, config: Optional[AudioFormatConfig] = None):
        """Initialize the audio format converter with configuration."""
        self.config = config or AudioFormatConfig.default()
        
        # Initialize error handling
        self.error_handler = AudioErrorHandler()
        self.recovery_manager = AudioGenerationRecoveryManager(self.error_handler)
        self.retry_wrapper = AudioGenerationRetryWrapper(self.recovery_manager)
        
        # Performance optimizations will be initialized lazily to avoid circular imports
        self._memory_optimizer = None
        self._audio_optimizer = None
    
    def convert_to_format(self, input_path: str, output_format: str, **kwargs) -> str:
        """
        Convert audio to specified format with options.
        
        Args:
            input_path: Path to input audio file
            output_format: Target format ('wav', 'mp3', 'm4b')
            **kwargs: Additional format-specific options
            
        Returns:
            Path to converted audio file
            
        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If input file doesn't exist
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if output_format not in self.config.supported_formats:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Generate output path
        if 'output_path' in kwargs:
            # Use provided output path directly
            output_path = kwargs['output_path']
        elif 'output_filename' in kwargs:
            # Use provided filename with output_dir
            output_dir = kwargs.get('output_dir', os.path.dirname(input_path))
            output_path = os.path.join(output_dir, kwargs['output_filename'])
        else:
            # Generate default output path
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = kwargs.get('output_dir', os.path.dirname(input_path))
            output_path = os.path.join(output_dir, f"{base_name}.{output_format}")
        
        # Remove output_path from kwargs to avoid conflicts
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['output_path', 'output_filename', 'output_dir']}
        
        if output_format == 'wav':
            return self._convert_to_wav(input_path, output_path, **filtered_kwargs)
        elif output_format == 'mp3':
            return self._convert_to_mp3(input_path, output_path, **filtered_kwargs)
        elif output_format == 'm4b':
            return self._convert_to_m4b(input_path, output_path, **filtered_kwargs)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def create_m4b_audiobook(self, audio_segments: List[str], 
                           chapters: Union[List[Chapter], List[AudiobookChapter]], 
                           metadata: Dict, output_path: str) -> str:
        """
        Create M4B audiobook with chapter bookmarks.
        
        Args:
            audio_segments: List of audio file paths to combine
            chapters: List of chapter objects for bookmarks
            metadata: Audiobook metadata (title, author, etc.)
            output_path: Path for output M4B file
            
        Returns:
            Path to created M4B audiobook
        """
        if not self.config.chapter_metadata_support:
            raise ValueError("Chapter metadata support is disabled")
        
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            # Check if we have audio segments
            if not audio_segments:
                raise ValueError("No audio segments provided for M4B creation")
            
            # If only one audio file, convert it directly
            if len(audio_segments) == 1:
                return self._convert_single_file_to_m4b(audio_segments[0], chapters, metadata, output_path)
            
            # Concatenate multiple audio files first
            temp_combined = self._concatenate_audio_files(audio_segments)
            
            try:
                result = self._convert_single_file_to_m4b(temp_combined, chapters, metadata, output_path)
                return result
            finally:
                # Clean up temporary file
                if os.path.exists(temp_combined):
                    os.remove(temp_combined)
                    
        except Exception as e:
            logger.error(f"Failed to create M4B audiobook: {str(e)}")
            raise RuntimeError(f"M4B audiobook creation failed: {str(e)}")
    
    def add_chapter_metadata(self, audio_path: str, 
                           chapters: Union[List[Chapter], List[AudiobookChapter]]) -> str:
        """
        Add chapter metadata to audio file.
        
        Args:
            audio_path: Path to audio file
            chapters: List of chapters with timing information
            
        Returns:
            Path to audio file with added metadata
        """
        if not self.config.chapter_metadata_support:
            raise ValueError("Chapter metadata support is disabled")
        
        try:
            # Create output path with metadata
            base_name = os.path.splitext(audio_path)[0]
            output_path = f"{base_name}_with_chapters.m4b"
            
            # Generate chapter metadata file
            chapter_file = self._create_chapter_metadata_file(chapters)
            
            try:
                # Use ffmpeg to add chapter metadata
                (
                    ffmpeg
                    .input(audio_path)
                    .output(output_path, 
                           acodec='aac',
                           f='mp4',
                           movflags='faststart')
                    .global_args('-i', chapter_file)
                    .global_args('-map_metadata', '1')
                    .overwrite_output()
                    .run(quiet=True, capture_stdout=True)
                )
                
                logger.info(f"Successfully added chapter metadata to {audio_path}: {output_path}")
                return output_path
                
            finally:
                # Clean up temporary chapter file
                if os.path.exists(chapter_file):
                    os.remove(chapter_file)
                    
        except Exception as e:
            logger.error(f"Failed to add chapter metadata to {audio_path}: {str(e)}")
            raise RuntimeError(f"Chapter metadata addition failed: {str(e)}")
    
    def validate_format(self, format_name: str) -> bool:
        """
        Validate if the given format is supported.
        
        Args:
            format_name: Format to validate (e.g., 'wav', 'mp3', 'm4b')
            
        Returns:
            True if format is supported, False otherwise
        """
        return format_name.lower() in self.config.supported_formats
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate if the audio file exists and is readable.
        
        Args:
            file_path: Path to audio file to validate
            
        Returns:
            True if file is valid, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            # Try to load the file to verify it's a valid audio file
            if librosa is None:
                # If librosa isn't available, fall back to extension check
                ext = os.path.splitext(file_path)[1].lower()
                return ext in {'.wav', '.mp3', '.m4b', '.flac', '.ogg'}
            librosa.load(file_path, sr=None, duration=0.1)  # Load just 0.1 seconds for validation
            return True
        except Exception as e:
            logger.warning(f"Audio file validation failed for {file_path}: {str(e)}")
            return False
    
    def get_audio_info(self, file_path: str) -> Dict[str, any]:
        """
        Get information about an audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio file information
        """
        if not self.validate_audio_file(file_path):
            raise ValueError(f"Invalid audio file: {file_path}")
        
        try:
            # Get basic audio information (use librosa if available)
            if librosa is None:
                raise RuntimeError("librosa not available")
            audio_data, sample_rate = librosa.load(file_path, sr=None)
            duration = len(audio_data) / sample_rate
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': 1 if len(audio_data.shape) == 1 else audio_data.shape[0],
                'samples': len(audio_data),
                'format': os.path.splitext(file_path)[1].lower().lstrip('.')
            }
        except Exception as e:
            logger.error(f"Failed to get audio info for {file_path}: {str(e)}")
            raise RuntimeError(f"Could not analyze audio file: {str(e)}")
    
    def _convert_to_wav(self, input_path: str, output_path: str, **kwargs) -> str:
        """Convert audio to WAV format."""
        try:
            # Use librosa to load and soundfile to save for consistent WAV output
            if librosa is None or sf is None:
                raise RuntimeError("librosa/soundfile not available")
            audio_data, sample_rate = librosa.load(input_path, sr=None)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            # Save as WAV with 16-bit PCM encoding
            sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
            
            logger.info(f"Successfully converted {input_path} to WAV: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert {input_path} to WAV: {str(e)}")
            raise RuntimeError(f"WAV conversion failed: {str(e)}")
    
    def _convert_to_mp3(self, input_path: str, output_path: str, **kwargs) -> str:
        """Convert audio to MP3 format with error handling and retry logic."""
        print(f"🔍 DEBUG: _convert_to_mp3 方法被调用 - format_converter.py")
        bitrate = kwargs.get('bitrate', self.config.mp3_bitrate)
        operation_id = f"mp3_conv_{int(time.time())}_{hash(input_path)}"
        
        # Enhanced console logging for MP3 conversion
        print(f"🎵 开始 MP3 转换...")
        print(f"   📁 输入文件: {input_path}")
        print(f"   📁 输出文件: {output_path}")
        print(f"   🎚️ 比特率: {bitrate} kbps")
        print(f"   🔧 操作ID: {operation_id}")
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"❌ 错误: 输入文件不存在: {input_path}")
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Get input file size for logging
        input_size = os.path.getsize(input_path)
        print(f"   📊 输入文件大小: {input_size / 1024 / 1024:.2f} MB")
        
        context = AudioGenerationContext(
            text_length=0,  # Not applicable for format conversion
            voice_sample_path=input_path,
            output_format='mp3',
            generation_stage='mp3_conversion'
        )
        
        def _convert():
            try:
                # Ensure output directory exists
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    print(f"   📂 创建输出目录: {output_dir}")
                    os.makedirs(output_dir, exist_ok=True)
                
                # Check system resources before conversion
                resource_status = self.error_handler.check_system_resources()
                print(f"   💾 系统内存使用率: {resource_status['memory_usage']:.1%}")
                if resource_status['memory_usage'] > 0.9:
                    print("⚠️  警告: 检测到高内存使用率")
                    logger.warning("High memory usage detected before MP3 conversion")
                
                print(f"   🔄 执行 FFmpeg 转换...")
                
                # Use ffmpeg for MP3 conversion with configurable bitrate
                (
                    ffmpeg
                    .input(input_path)
                    .output(output_path, acodec='mp3', audio_bitrate=f'{bitrate}k')
                    .overwrite_output()
                    .run(quiet=True, capture_stdout=True)
                )
                
                # Check if output file was created successfully
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    print(f"✅ MP3 转换成功!")
                    print(f"   📁 输出文件: {output_path}")
                    print(f"   📊 输出文件大小: {output_size / 1024 / 1024:.2f} MB")
                    print(f"   📉 压缩比: {(1 - output_size/input_size)*100:.1f}%")
                    logger.info(f"Successfully converted {input_path} to MP3 at {bitrate}kbps: {output_path}")
                    return output_path
                else:
                    print(f"❌ 错误: MP3 文件未生成")
                    raise RuntimeError("MP3 file was not created")
                
            except ffmpeg.Error as e:
                # Handle FFmpeg-specific errors
                error_msg = e.stderr.decode() if e.stderr else str(e)
                print(f"❌ FFmpeg 错误: {error_msg}")
                logger.error(f"FFmpeg error converting {input_path} to MP3: {error_msg}")
                
                # Check for specific error types
                if 'codec not found' in error_msg.lower():
                    print("❌ 错误: MP3 编解码器不可用")
                    raise RuntimeError(f"MP3 codec not available: {error_msg}")
                elif 'permission denied' in error_msg.lower():
                    print(f"❌ 错误: 没有写入权限到 {output_path}")
                    raise RuntimeError(f"Permission denied writing to {output_path}")
                else:
                    print(f"❌ 错误: MP3 转换失败")
                    raise RuntimeError(f"MP3 conversion failed: {error_msg}")
            
            except Exception as e:
                print(f"❌ 转换异常: {str(e)}")
                logger.error(f"Failed to convert {input_path} to MP3: {str(e)}")
                raise RuntimeError(f"MP3 conversion failed: {str(e)}")
        
        try:
            result = self.retry_wrapper.with_retry(_convert, operation_id, context)
            print(f"🎉 MP3 转换完成: {result}")
            return result
        except Exception as e:
            # If all retries failed, do NOT delete/convert original WAV; keep it
            print(f"⚠️  MP3 转换失败，保留原始 WAV 文件: {e}")
            logger.warning(f"MP3 conversion failed after retries; keeping original WAV: {e}")
            # Ensure we simply return the input_path (original WAV)
            return input_path
    
    def _convert_to_m4b(self, input_path: str, output_path: str, **kwargs) -> str:
        """Convert audio to M4B format."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            # Get metadata and chapters from kwargs
            metadata = kwargs.get('metadata', {})
            chapters = kwargs.get('chapters', [])
            cover_image = kwargs.get('cover_image', None)
            
            # Build ffmpeg command
            input_stream = ffmpeg.input(input_path)
            
            # Prepare output arguments
            output_args = {
                'acodec': 'aac',
                'f': 'mp4',
                'movflags': 'faststart'
            }
            
            # Add metadata if provided
            if metadata:
                for key, value in metadata.items():
                    if key in ['title', 'artist', 'album', 'date', 'genre', 'comment']:
                        output_args[f'metadata:{key}'] = str(value)
            
            # Create the output stream
            output_stream = input_stream.output(output_path, **output_args)
            
            # Add cover image if provided
            if cover_image and os.path.exists(cover_image):
                cover_input = ffmpeg.input(cover_image)
                output_stream = ffmpeg.output(
                    input_stream, cover_input, output_path,
                    **output_args,
                    **{'disposition:v:0': 'attached_pic'}
                )
            
            # Run the conversion
            output_stream.overwrite_output().run(quiet=True, capture_stdout=True)
            
            # Add chapters if provided
            if chapters and self.config.chapter_metadata_support:
                output_path = self.add_chapter_metadata(output_path, chapters)
            
            logger.info(f"Successfully converted {input_path} to M4B: {output_path}")
            return output_path
            
        except Exception as e:
            # Handle ffmpeg.Error and other exceptions
            if hasattr(e, 'stderr') and e.stderr:
                error_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            else:
                error_msg = str(e)
            logger.error(f"FFmpeg error converting {input_path} to M4B: {error_msg}")
            # Keep original WAV on failure
            return input_path
    
    def _concatenate_audio_files(self, audio_files: List[str]) -> str:
        """Concatenate multiple audio files into a single file."""
        if not audio_files:
            raise ValueError("No audio files provided for concatenation")
        
        if len(audio_files) == 1:
            return audio_files[0]
        
        try:
            # Create temporary output file
            temp_output = tempfile.mktemp(suffix='.wav')
            
            # Create input streams
            input_streams = [ffmpeg.input(f) for f in audio_files]
            
            # Concatenate using ffmpeg
            (
                ffmpeg
                .concat(*input_streams, v=0, a=1)
                .output(temp_output)
                .overwrite_output()
                .run(quiet=True, capture_stdout=True)
            )
            
            logger.info(f"Successfully concatenated {len(audio_files)} audio files")
            return temp_output
            
        except Exception as e:
            if hasattr(e, 'stderr') and e.stderr:
                error_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            else:
                error_msg = str(e)
            logger.error(f"Failed to concatenate audio files: {error_msg}")
            raise RuntimeError(f"Audio concatenation failed: {error_msg}")
    
    def _convert_single_file_to_m4b(self, audio_path: str, 
                                   chapters: Union[List[Chapter], List[AudiobookChapter]], 
                                   metadata: Dict, output_path: str) -> str:
        """Convert a single audio file to M4B with metadata and chapters."""
        return self._convert_to_m4b(audio_path, output_path, 
                                   metadata=metadata, chapters=chapters)
    
    def _create_chapter_metadata_file(self, chapters: Union[List[Chapter], List[AudiobookChapter]]) -> str:
        """Create a temporary metadata file for chapter information."""
        # Create temporary metadata file
        temp_file = tempfile.mktemp(suffix='.txt')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(";FFMETADATA1\n")
                
                for i, chapter in enumerate(chapters):
                    # Handle both Chapter and AudiobookChapter types
                    if isinstance(chapter, AudiobookChapter):
                        start_time = int(chapter.start_time * 1000)  # Convert to milliseconds
                        end_time = int(chapter.end_time * 1000)
                        title = chapter.title
                    else:
                        # For regular Chapter objects, create equal-duration chapters
                        chapter_duration = 300.0  # 5 minutes per chapter as default
                        start_time = int(i * chapter_duration * 1000)
                        end_time = int((i + 1) * chapter_duration * 1000)
                        title = chapter.title
                    
                    f.write(f"\n[CHAPTER]\n")
                    f.write(f"TIMEBASE=1/1000\n")
                    f.write(f"START={start_time}\n")
                    f.write(f"END={end_time}\n")
                    f.write(f"title={title}\n")
            
            return temp_file
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise RuntimeError(f"Failed to create chapter metadata file: {str(e)}")
    
    def create_audiobook_chapters_from_text_chapters(self, chapters: List[Chapter], 
                                                   total_duration: float) -> List[AudiobookChapter]:
        """
        Convert text chapters to audiobook chapters with timing information.
        
        Args:
            chapters: List of text chapters
            total_duration: Total duration of the audio in seconds
            
        Returns:
            List of AudiobookChapter objects with timing information
        """
        if not chapters:
            return []
        
        audiobook_chapters = []
        chapter_duration = total_duration / len(chapters)
        
        for i, chapter in enumerate(chapters):
            start_time = i * chapter_duration
            end_time = (i + 1) * chapter_duration
            
            audiobook_chapters.append(AudiobookChapter(
                title=chapter.title,
                start_time=start_time,
                end_time=end_time,
                content=chapter.content
            ))
        
        return audiobook_chapters


class AudioSegmenter:
    """Handles chapter-based audio segmentation."""
    
    def __init__(self, format_converter: Optional[AudioFormatConverter] = None):
        """Initialize the audio segmenter."""
        self.format_converter = format_converter or AudioFormatConverter()
    
    def segment_audio(self, audio_path: str, chapters: Union[List[Chapter], List[AudiobookChapter]], 
                     config: SegmentationConfig, output_dir: str) -> List[str]:
        """
        Segment audio based on chapters.
        
        Args:
            audio_path: Path to source audio file
            chapters: List of chapters for segmentation
            config: Segmentation configuration
            output_dir: Directory for output segments
            
        Returns:
            List of paths to segmented audio files
        """
        if not config.enabled:
            return [audio_path]
        
        try:
            # Validate input file
            if not self.format_converter.validate_audio_file(audio_path):
                raise ValueError(f"Invalid audio file: {audio_path}")
            
            # Convert chapters to audiobook chapters if needed
            if chapters and not isinstance(chapters[0], AudiobookChapter):
                audio_info = self.format_converter.get_audio_info(audio_path)
                audiobook_chapters = self.format_converter.create_audiobook_chapters_from_text_chapters(
                    chapters, audio_info['duration']
                )
            else:
                audiobook_chapters = chapters
            
            # Use optimized segmentation for large files or many chapters
            audio_duration = sum(c.end_time - c.start_time for c in audiobook_chapters) if audiobook_chapters else 0
            
            # Lazy import to avoid circular imports
            if self.format_converter._memory_optimizer is None:
                from ..performance.memory_manager import MemoryOptimizer
                self.format_converter._memory_optimizer = MemoryOptimizer()
            
            with self.format_converter._memory_optimizer.optimized_audio_processing(audio_duration) as opt_info:
                if opt_info['use_streaming'] or len(audiobook_chapters) > 20:
                    # Use optimized segmentation
                    if self.format_converter._audio_optimizer is None:
                        from ..performance.audio_optimizer import AudioSegmentationOptimizer
                        self.format_converter._audio_optimizer = AudioSegmentationOptimizer()
                    
                    segment_paths, metrics = self.format_converter._audio_optimizer.optimize_audio_segmentation(
                        audio_path, audiobook_chapters, config, output_dir, opt_info
                    )
                    logger.info(f"Optimized segmentation completed in {metrics.total_time:.2f}s")
                    return segment_paths
                else:
                    # Use standard segmentation
                    return self._standard_segmentation(audio_path, audiobook_chapters, config, output_dir)
            
        except Exception as e:
            logger.error(f"Failed to segment audio {audio_path}: {str(e)}")
            raise RuntimeError(f"Audio segmentation failed: {str(e)}")
    
    def _standard_segmentation(self, audio_path: str, chapters: List[AudiobookChapter],
                             config: SegmentationConfig, output_dir: str) -> List[str]:
        """Standard segmentation without optimization."""
        # Create output directory structure
        segment_dir = self._create_segment_directory(audio_path, output_dir, config)
        
        # Group chapters according to chapters_per_file setting
        chapter_groups = self._group_chapters(chapters, config.chapters_per_file)
        
        # Segment audio for each group
        segment_paths = []
        for i, chapter_group in enumerate(chapter_groups):
            segment_path = self._create_audio_segment(
                audio_path, chapter_group, i, segment_dir, config
            )
            segment_paths.append(segment_path)
        
        logger.info(f"Successfully segmented audio into {len(segment_paths)} files")
        return segment_paths
    
    def segment_by_chapters(self, audio_path: str, chapters: List, chapters_per_file: int) -> List[str]:
        """
        Segment audio by chapters without creating subfolders.
        
        Args:
            audio_path: Path to source audio file
            chapters: List of chapters
            chapters_per_file: Number of chapters per file
            
        Returns:
            List of paths to segmented audio files (directly in outputs folder)
        """
        try:
            # Create segmentation config that doesn't create subfolders
            from ..audio_formats.models import SegmentationConfig
            config = SegmentationConfig(
                enabled=True,
                chapters_per_file=chapters_per_file,
                use_chapter_detection=True,
                max_file_duration=None,
                create_subfolders=False  # Don't create subfolders
            )
            
            # Use outputs directory directly
            output_dir = "outputs"
            
            # Convert chapters to audiobook chapters if needed
            if chapters and hasattr(chapters[0], 'title'):
                # These are text chapters, convert to audiobook chapters
                audio_info = self.format_converter.get_audio_info(audio_path)
                audiobook_chapters = self.format_converter.create_audiobook_chapters_from_text_chapters(
                    chapters, audio_info['duration']
                )
            else:
                audiobook_chapters = chapters
            
            # Segment audio directly in outputs folder
            return self.segment_audio(audio_path, audiobook_chapters, config, output_dir)
            
        except Exception as e:
            print(f"章节分割失败: {e}")
            return [audio_path]  # Return original file if segmentation fails
    
    def _create_segment_directory(self, audio_path: str, output_dir: str, 
                                config: SegmentationConfig) -> str:
        """Create organized directory structure for segmented files."""
        # Always use output_dir directly - never create subfolders
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def _group_chapters(self, chapters: List[AudiobookChapter], 
                       chapters_per_file: int) -> List[List[AudiobookChapter]]:
        """Group chapters according to chapters_per_file setting."""
        if not chapters:
            return []
        
        # Validate chapters_per_file range (1-100)
        chapters_per_file = max(1, min(100, chapters_per_file))
        
        groups = []
        for i in range(0, len(chapters), chapters_per_file):
            group = chapters[i:i + chapters_per_file]
            groups.append(group)
        
        return groups
    
    def _create_audio_segment(self, audio_path: str, chapter_group: List[AudiobookChapter],
                            group_index: int, output_dir: str, 
                            config: SegmentationConfig) -> str:
        """Create a single audio segment from a group of chapters."""
        if not chapter_group:
            raise ValueError("Empty chapter group provided")
        
        # Calculate segment timing
        start_time = chapter_group[0].start_time
        end_time = chapter_group[-1].end_time
        
        # Generate output filename with chapter range
        first_chapter = group_index * config.chapters_per_file + 1
        last_chapter = first_chapter + len(chapter_group) - 1
        
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        segment_filename = f"{base_name}_{first_chapter}-{last_chapter}.wav"
        segment_path = os.path.join(output_dir, segment_filename)
        
        try:
            # Use ffmpeg to extract the audio segment
            (
                ffmpeg
                .input(audio_path, ss=start_time, t=(end_time - start_time))
                .output(segment_path, acodec='pcm_s16le')
                .overwrite_output()
                .run(quiet=True, capture_stdout=True)
            )
            
            logger.info(f"Created segment {segment_filename} ({start_time:.1f}s - {end_time:.1f}s)")
            return segment_path
            
        except Exception as e:
            if hasattr(e, 'stderr') and e.stderr:
                error_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            else:
                error_msg = str(e)
            logger.error(f"Failed to create audio segment: {error_msg}")
            raise RuntimeError(f"Audio segment creation failed: {error_msg}")
    
    def segment_audio_by_duration(self, audio_path: str, max_duration: float,
                                output_dir: str, config: SegmentationConfig) -> List[str]:
        """
        Segment audio by maximum duration instead of chapters.
        
        Args:
            audio_path: Path to source audio file
            max_duration: Maximum duration per segment in seconds
            output_dir: Directory for output segments
            config: Segmentation configuration
            
        Returns:
            List of paths to segmented audio files
        """
        try:
            # Get audio information
            audio_info = self.format_converter.get_audio_info(audio_path)
            total_duration = audio_info['duration']
            
            if total_duration <= max_duration:
                return [audio_path]  # No segmentation needed
            
            # Create output directory
            segment_dir = self._create_segment_directory(audio_path, output_dir, config)
            
            # Calculate number of segments
            num_segments = int(np.ceil(total_duration / max_duration))
            segment_paths = []
            
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            
            for i in range(num_segments):
                start_time = i * max_duration
                segment_duration = min(max_duration, total_duration - start_time)
                
                segment_filename = f"{base_name}_part_{i+1:03d}.wav"
                segment_path = os.path.join(segment_dir, segment_filename)
                
                # Extract segment using ffmpeg
                (
                    ffmpeg
                    .input(audio_path, ss=start_time, t=segment_duration)
                    .output(segment_path, acodec='pcm_s16le')
                    .overwrite_output()
                    .run(quiet=True, capture_stdout=True)
                )
                
                segment_paths.append(segment_path)
                logger.info(f"Created duration segment {segment_filename} ({start_time:.1f}s - {start_time + segment_duration:.1f}s)")
            
            return segment_paths
            
        except Exception as e:
            logger.error(f"Failed to segment audio by duration: {str(e)}")
            raise RuntimeError(f"Duration-based segmentation failed: {str(e)}")