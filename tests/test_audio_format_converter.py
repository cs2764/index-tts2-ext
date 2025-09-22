"""
Unit tests for AudioFormatConverter class.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import soundfile as sf

from indextts.audio_formats.format_converter import AudioFormatConverter
from indextts.audio_formats.models import AudioFormatConfig


class TestAudioFormatConverter(unittest.TestCase):
    """Test cases for AudioFormatConverter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = AudioFormatConverter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test audio file
        self.test_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        sample_rate = 22050
        duration = 1.0  # 1 second
        samples = int(sample_rate * duration)
        audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, duration, samples))  # 440Hz sine wave
        sf.write(self.test_audio_path, audio_data, sample_rate)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        converter = AudioFormatConverter()
        self.assertIsInstance(converter.config, AudioFormatConfig)
        self.assertEqual(converter.config.default_format, 'mp3')
        self.assertEqual(converter.config.mp3_bitrate, 64)
    
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = AudioFormatConfig(
            supported_formats=['wav', 'mp3'],
            default_format='wav',
            mp3_bitrate=128,
            m4b_cover_support=False,
            chapter_metadata_support=False
        )
        converter = AudioFormatConverter(config)
        self.assertEqual(converter.config.default_format, 'wav')
        self.assertEqual(converter.config.mp3_bitrate, 128)
    
    def test_validate_format(self):
        """Test format validation."""
        self.assertTrue(self.converter.validate_format('wav'))
        self.assertTrue(self.converter.validate_format('mp3'))
        self.assertTrue(self.converter.validate_format('m4b'))
        self.assertTrue(self.converter.validate_format('WAV'))  # Case insensitive
        self.assertFalse(self.converter.validate_format('flac'))
        self.assertFalse(self.converter.validate_format('ogg'))
    
    def test_validate_audio_file(self):
        """Test audio file validation."""
        # Valid audio file
        self.assertTrue(self.converter.validate_audio_file(self.test_audio_path))
        
        # Non-existent file
        self.assertFalse(self.converter.validate_audio_file('/nonexistent/file.wav'))
        
        # Invalid file (create a text file with .wav extension)
        invalid_path = os.path.join(self.temp_dir, "invalid.wav")
        with open(invalid_path, 'w') as f:
            f.write("This is not an audio file")
        self.assertFalse(self.converter.validate_audio_file(invalid_path))
    
    def test_get_audio_info(self):
        """Test getting audio file information."""
        info = self.converter.get_audio_info(self.test_audio_path)
        
        self.assertIn('duration', info)
        self.assertIn('sample_rate', info)
        self.assertIn('channels', info)
        self.assertIn('samples', info)
        self.assertIn('format', info)
        
        self.assertAlmostEqual(info['duration'], 1.0, places=1)
        self.assertEqual(info['sample_rate'], 22050)
        self.assertEqual(info['format'], 'wav')
    
    def test_get_audio_info_invalid_file(self):
        """Test getting audio info for invalid file."""
        with self.assertRaises(ValueError):
            self.converter.get_audio_info('/nonexistent/file.wav')
    
    def test_convert_to_format_unsupported_format(self):
        """Test conversion to unsupported format."""
        with self.assertRaises(ValueError) as context:
            self.converter.convert_to_format(self.test_audio_path, 'flac')
        self.assertIn("Unsupported output format", str(context.exception))
    
    def test_convert_to_format_nonexistent_file(self):
        """Test conversion of non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.converter.convert_to_format('/nonexistent/file.wav', 'mp3')
    
    def test_convert_to_wav(self):
        """Test WAV conversion."""
        output_path = os.path.join(self.temp_dir, "output.wav")
        result_path = self.converter.convert_to_format(self.test_audio_path, 'wav', output_dir=self.temp_dir)
        
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(result_path.endswith('.wav'))
        
        # Verify the converted file is valid
        self.assertTrue(self.converter.validate_audio_file(result_path))
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_convert_to_mp3(self, mock_ffmpeg):
        """Test MP3 conversion."""
        # Mock ffmpeg chain
        mock_input_obj = MagicMock()
        mock_output_obj = MagicMock()
        mock_overwrite_obj = MagicMock()
        
        mock_ffmpeg.input.return_value = mock_input_obj
        mock_input_obj.output.return_value = mock_output_obj
        mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
        mock_overwrite_obj.run.return_value = None
        
        result_path = self.converter.convert_to_format(self.test_audio_path, 'mp3', output_dir=self.temp_dir)
        
        # Verify ffmpeg was called correctly
        mock_ffmpeg.input.assert_called_once_with(self.test_audio_path)
        mock_input_obj.output.assert_called_once()
        mock_overwrite_obj.run.assert_called_once()
        
        self.assertTrue(result_path.endswith('.mp3'))
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_convert_to_mp3_custom_bitrate(self, mock_ffmpeg):
        """Test MP3 conversion with custom bitrate."""
        mock_input_obj = MagicMock()
        mock_output_obj = MagicMock()
        mock_overwrite_obj = MagicMock()
        
        mock_ffmpeg.input.return_value = mock_input_obj
        mock_input_obj.output.return_value = mock_output_obj
        mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
        mock_overwrite_obj.run.return_value = None
        
        result_path = self.converter.convert_to_format(
            self.test_audio_path, 'mp3', 
            output_dir=self.temp_dir, 
            bitrate=128
        )
        
        # Verify ffmpeg was called with custom bitrate
        mock_input_obj.output.assert_called_once()
        call_args = mock_input_obj.output.call_args
        self.assertIn('audio_bitrate', call_args[1])
        self.assertEqual(call_args[1]['audio_bitrate'], '128k')
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_convert_to_mp3_ffmpeg_error(self, mock_ffmpeg):
        """Test MP3 conversion with FFmpeg error."""
        import ffmpeg
        
        mock_input_obj = MagicMock()
        mock_output_obj = MagicMock()
        mock_overwrite_obj = MagicMock()
        
        mock_ffmpeg.input.return_value = mock_input_obj
        mock_input_obj.output.return_value = mock_output_obj
        mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
        mock_overwrite_obj.run.side_effect = ffmpeg.Error('ffmpeg', '', b'Test error message')
        
        with self.assertRaises(RuntimeError) as context:
            self.converter.convert_to_format(self.test_audio_path, 'mp3', output_dir=self.temp_dir)
        
        self.assertIn("MP3 conversion failed", str(context.exception))
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_convert_to_m4b(self, mock_ffmpeg):
        """Test M4B conversion."""
        # Mock ffmpeg chain
        mock_input_obj = MagicMock()
        mock_output_obj = MagicMock()
        mock_overwrite_obj = MagicMock()
        
        mock_ffmpeg.input.return_value = mock_input_obj
        mock_input_obj.output.return_value = mock_output_obj
        mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
        mock_overwrite_obj.run.return_value = None
        
        result_path = self.converter.convert_to_format(self.test_audio_path, 'm4b', output_dir=self.temp_dir)
        
        # Verify ffmpeg was called correctly
        mock_ffmpeg.input.assert_called_once_with(self.test_audio_path)
        mock_input_obj.output.assert_called_once()
        mock_overwrite_obj.run.assert_called_once()
        
        self.assertTrue(result_path.endswith('.m4b'))
    
    def test_create_m4b_audiobook_empty_segments(self):
        """Test that M4B audiobook creation with empty segments raises error."""
        output_path = os.path.join(self.temp_dir, "output.m4b")
        # Empty segments should cause an error in concatenation
        with self.assertRaises(RuntimeError):
            self.converter.create_m4b_audiobook([], [], {}, output_path)
    
    def test_add_chapter_metadata_invalid_file(self):
        """Test that chapter metadata addition with invalid file raises error."""
        with self.assertRaises(RuntimeError):
            self.converter.add_chapter_metadata("nonexistent.wav", [])
    
    def test_add_chapter_metadata_disabled(self):
        """Test chapter metadata addition when disabled."""
        config = AudioFormatConfig.default()
        config.chapter_metadata_support = False
        converter = AudioFormatConverter(config)
        
        with self.assertRaises(ValueError) as context:
            converter.add_chapter_metadata("audio.wav", [])
        
        self.assertIn("Chapter metadata support is disabled", str(context.exception))
    
    def test_create_audiobook_chapters_from_text_chapters(self):
        """Test creating audiobook chapters from text chapters."""
        from indextts.chapter_parsing.models import Chapter
        
        text_chapters = [
            Chapter(title="Chapter 1", content="Content 1"),
            Chapter(title="Chapter 2", content="Content 2"),
            Chapter(title="Chapter 3", content="Content 3")
        ]
        
        total_duration = 900.0  # 15 minutes
        audiobook_chapters = self.converter.create_audiobook_chapters_from_text_chapters(
            text_chapters, total_duration
        )
        
        self.assertEqual(len(audiobook_chapters), 3)
        
        # Check first chapter
        self.assertEqual(audiobook_chapters[0].title, "Chapter 1")
        self.assertEqual(audiobook_chapters[0].start_time, 0.0)
        self.assertEqual(audiobook_chapters[0].end_time, 300.0)
        self.assertEqual(audiobook_chapters[0].duration, 300.0)
        
        # Check second chapter
        self.assertEqual(audiobook_chapters[1].start_time, 300.0)
        self.assertEqual(audiobook_chapters[1].end_time, 600.0)
        
        # Check third chapter
        self.assertEqual(audiobook_chapters[2].start_time, 600.0)
        self.assertEqual(audiobook_chapters[2].end_time, 900.0)
    
    def test_create_audiobook_chapters_empty_list(self):
        """Test creating audiobook chapters from empty list."""
        result = self.converter.create_audiobook_chapters_from_text_chapters([], 100.0)
        self.assertEqual(result, [])
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_concatenate_audio_files_single_file(self, mock_ffmpeg):
        """Test concatenating a single audio file."""
        result = self.converter._concatenate_audio_files([self.test_audio_path])
        self.assertEqual(result, self.test_audio_path)
        mock_ffmpeg.input.assert_not_called()
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    @patch('tempfile.mktemp')
    def test_concatenate_audio_files_multiple(self, mock_mktemp, mock_ffmpeg):
        """Test concatenating multiple audio files."""
        mock_mktemp.return_value = '/tmp/output.wav'
        
        # Mock ffmpeg chain
        mock_input1 = MagicMock()
        mock_input2 = MagicMock()
        mock_concat = MagicMock()
        mock_output = MagicMock()
        mock_overwrite = MagicMock()
        
        mock_ffmpeg.input.side_effect = [mock_input1, mock_input2]
        mock_ffmpeg.concat.return_value = mock_concat
        mock_concat.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite
        mock_overwrite.run.return_value = None
        
        files = [self.test_audio_path, self.test_audio_path]
        result = self.converter._concatenate_audio_files(files)
        
        self.assertEqual(result, '/tmp/output.wav')
        mock_ffmpeg.concat.assert_called_once()
        mock_overwrite.run.assert_called_once()
    
    def test_concatenate_audio_files_empty_list(self):
        """Test concatenating empty list raises error."""
        with self.assertRaises(ValueError) as context:
            self.converter._concatenate_audio_files([])
        
        self.assertIn("No audio files provided", str(context.exception))
    
    @patch('indextts.audio_formats.format_converter.tempfile.mktemp')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_create_chapter_metadata_file_audiobook_chapters(self, mock_open, mock_mktemp):
        """Test creating chapter metadata file with AudiobookChapter objects."""
        from indextts.audio_formats.models import AudiobookChapter
        
        mock_mktemp.return_value = '/tmp/metadata.txt'
        
        chapters = [
            AudiobookChapter(title="Chapter 1", start_time=0.0, end_time=300.0),
            AudiobookChapter(title="Chapter 2", start_time=300.0, end_time=600.0)
        ]
        
        result = self.converter._create_chapter_metadata_file(chapters)
        
        self.assertEqual(result, '/tmp/metadata.txt')
        mock_open.assert_called_once_with('/tmp/metadata.txt', 'w', encoding='utf-8')
        
        # Check that the file was written with correct content
        handle = mock_open()
        write_calls = handle.write.call_args_list
        
        # Verify FFMETADATA1 header
        self.assertIn(unittest.mock.call(";FFMETADATA1\n"), write_calls)
        
        # Verify chapter entries
        written_content = ''.join([call[0][0] for call in write_calls])
        self.assertIn("title=Chapter 1", written_content)
        self.assertIn("title=Chapter 2", written_content)
        self.assertIn("START=0", written_content)
        self.assertIn("START=300000", written_content)
    
    @patch('indextts.audio_formats.format_converter.tempfile.mktemp')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_create_chapter_metadata_file_text_chapters(self, mock_open, mock_mktemp):
        """Test creating chapter metadata file with regular Chapter objects."""
        from indextts.chapter_parsing.models import Chapter
        
        mock_mktemp.return_value = '/tmp/metadata.txt'
        
        chapters = [
            Chapter(title="Chapter 1", content="Content 1"),
            Chapter(title="Chapter 2", content="Content 2")
        ]
        
        result = self.converter._create_chapter_metadata_file(chapters)
        
        self.assertEqual(result, '/tmp/metadata.txt')
        
        # Check that the file was written
        handle = mock_open()
        write_calls = handle.write.call_args_list
        written_content = ''.join([call[0][0] for call in write_calls])
        
        # Should use default 5-minute chapters
        self.assertIn("START=0", written_content)
        self.assertIn("START=300000", written_content)  # 5 minutes in milliseconds
        self.assertIn("title=Chapter 1", written_content)
        self.assertIn("title=Chapter 2", written_content)


if __name__ == '__main__':
    unittest.main()