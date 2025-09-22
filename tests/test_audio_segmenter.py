"""
Unit tests for AudioSegmenter class.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import soundfile as sf

from indextts.audio_formats.format_converter import AudioSegmenter, AudioFormatConverter
from indextts.audio_formats.models import SegmentationConfig, AudiobookChapter
from indextts.chapter_parsing.models import Chapter


class TestAudioSegmenter(unittest.TestCase):
    """Test cases for AudioSegmenter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.segmenter = AudioSegmenter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test audio file
        self.test_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        sample_rate = 22050
        duration = 10.0  # 10 seconds
        samples = int(sample_rate * duration)
        audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, duration, samples))  # 440Hz sine wave
        sf.write(self.test_audio_path, audio_data, sample_rate)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default(self):
        """Test initialization with default format converter."""
        segmenter = AudioSegmenter()
        self.assertIsInstance(segmenter.format_converter, AudioFormatConverter)
    
    def test_init_custom_converter(self):
        """Test initialization with custom format converter."""
        converter = AudioFormatConverter()
        segmenter = AudioSegmenter(converter)
        self.assertEqual(segmenter.format_converter, converter)
    
    def test_segment_audio_disabled(self):
        """Test segmentation when disabled returns original file."""
        config = SegmentationConfig(enabled=False, chapters_per_file=5, 
                                  use_chapter_detection=True, max_file_duration=None,
                                  create_subfolders=True)
        
        result = self.segmenter.segment_audio(self.test_audio_path, [], config, self.temp_dir)
        
        self.assertEqual(result, [self.test_audio_path])
    
    def test_segment_audio_invalid_file(self):
        """Test segmentation with invalid audio file."""
        config = SegmentationConfig.default()
        config.enabled = True
        
        with self.assertRaises(RuntimeError) as context:
            self.segmenter.segment_audio('/nonexistent/file.wav', [], config, self.temp_dir)
        
        self.assertIn("Audio segmentation failed", str(context.exception))
    
    def test_group_chapters(self):
        """Test grouping chapters by chapters_per_file."""
        chapters = [
            AudiobookChapter(title=f"Chapter {i}", start_time=i*60, end_time=(i+1)*60)
            for i in range(10)
        ]
        
        # Test grouping by 3
        groups = self.segmenter._group_chapters(chapters, 3)
        self.assertEqual(len(groups), 4)  # 10 chapters / 3 = 4 groups (3,3,3,1)
        self.assertEqual(len(groups[0]), 3)
        self.assertEqual(len(groups[1]), 3)
        self.assertEqual(len(groups[2]), 3)
        self.assertEqual(len(groups[3]), 1)
        
        # Test grouping by 5
        groups = self.segmenter._group_chapters(chapters, 5)
        self.assertEqual(len(groups), 2)  # 10 chapters / 5 = 2 groups (5,5)
        self.assertEqual(len(groups[0]), 5)
        self.assertEqual(len(groups[1]), 5)
    
    def test_group_chapters_empty(self):
        """Test grouping empty chapter list."""
        groups = self.segmenter._group_chapters([], 5)
        self.assertEqual(groups, [])
    
    def test_group_chapters_boundary_values(self):
        """Test grouping with boundary values for chapters_per_file."""
        chapters = [
            AudiobookChapter(title=f"Chapter {i}", start_time=i*60, end_time=(i+1)*60)
            for i in range(5)
        ]
        
        # Test with value below minimum (should be clamped to 1)
        groups = self.segmenter._group_chapters(chapters, 0)
        self.assertEqual(len(groups), 5)  # Each chapter in its own group
        
        # Test with value above maximum (should be clamped to 100)
        groups = self.segmenter._group_chapters(chapters, 150)
        self.assertEqual(len(groups), 1)  # All chapters in one group
    
    def test_create_segment_directory_no_subfolders(self):
        """Test directory creation when subfolders are disabled."""
        config = SegmentationConfig.default()
        config.create_subfolders = False
        
        result = self.segmenter._create_segment_directory(
            self.test_audio_path, self.temp_dir, config
        )
        
        self.assertEqual(result, self.temp_dir)
    
    def test_create_segment_directory_with_subfolders(self):
        """Test directory creation when subfolders are enabled."""
        config = SegmentationConfig.default()
        config.create_subfolders = True
        
        result = self.segmenter._create_segment_directory(
            self.test_audio_path, self.temp_dir, config
        )
        
        # Should create a subdirectory
        self.assertNotEqual(result, self.temp_dir)
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.startswith(self.temp_dir))
        
        # Check folder name format contains base filename
        folder_name = os.path.basename(result)
        self.assertIn("test_audio", folder_name)
        self.assertIn("voice_sample", folder_name)
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_create_audio_segment(self, mock_ffmpeg):
        """Test creating a single audio segment."""
        # Mock ffmpeg chain
        mock_input_obj = MagicMock()
        mock_output_obj = MagicMock()
        mock_overwrite_obj = MagicMock()
        
        mock_ffmpeg.input.return_value = mock_input_obj
        mock_input_obj.output.return_value = mock_output_obj
        mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
        mock_overwrite_obj.run.return_value = None
        
        chapters = [
            AudiobookChapter(title="Chapter 1", start_time=0.0, end_time=60.0),
            AudiobookChapter(title="Chapter 2", start_time=60.0, end_time=120.0)
        ]
        
        config = SegmentationConfig.default()
        config.chapters_per_file = 2
        
        result = self.segmenter._create_audio_segment(
            self.test_audio_path, chapters, 0, self.temp_dir, config
        )
        
        # Verify ffmpeg was called correctly
        mock_ffmpeg.input.assert_called_once_with(self.test_audio_path, ss=0.0, t=120.0)
        mock_overwrite_obj.run.assert_called_once()
        
        # Check output filename format
        expected_filename = "test_audio_1-2.wav"
        self.assertTrue(result.endswith(expected_filename))
    
    def test_create_audio_segment_empty_group(self):
        """Test creating segment with empty chapter group."""
        config = SegmentationConfig.default()
        
        with self.assertRaises(ValueError) as context:
            self.segmenter._create_audio_segment(
                self.test_audio_path, [], 0, self.temp_dir, config
            )
        
        self.assertIn("Empty chapter group", str(context.exception))
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_segment_audio_by_duration(self, mock_ffmpeg):
        """Test segmenting audio by duration."""
        # Mock audio info
        with patch.object(self.segmenter.format_converter, 'get_audio_info') as mock_info:
            mock_info.return_value = {'duration': 25.0, 'sample_rate': 22050}
            
            # Mock ffmpeg chain
            mock_input_obj = MagicMock()
            mock_output_obj = MagicMock()
            mock_overwrite_obj = MagicMock()
            
            mock_ffmpeg.input.return_value = mock_input_obj
            mock_input_obj.output.return_value = mock_output_obj
            mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
            mock_overwrite_obj.run.return_value = None
            
            config = SegmentationConfig.default()
            config.create_subfolders = False
            
            result = self.segmenter.segment_audio_by_duration(
                self.test_audio_path, 10.0, self.temp_dir, config
            )
            
            # Should create 3 segments (25s / 10s = 3 segments: 10s, 10s, 5s)
            self.assertEqual(len(result), 3)
            
            # Verify ffmpeg was called 3 times
            self.assertEqual(mock_ffmpeg.input.call_count, 3)
            
            # Check filenames
            for i, path in enumerate(result):
                expected_filename = f"test_audio_part_{i+1:03d}.wav"
                self.assertTrue(path.endswith(expected_filename))
    
    def test_segment_audio_by_duration_no_segmentation_needed(self):
        """Test duration segmentation when file is already short enough."""
        with patch.object(self.segmenter.format_converter, 'get_audio_info') as mock_info:
            mock_info.return_value = {'duration': 5.0, 'sample_rate': 22050}
            
            config = SegmentationConfig.default()
            
            result = self.segmenter.segment_audio_by_duration(
                self.test_audio_path, 10.0, self.temp_dir, config
            )
            
            # Should return original file
            self.assertEqual(result, [self.test_audio_path])
    
    @patch('indextts.audio_formats.format_converter.ffmpeg')
    def test_segment_audio_with_text_chapters(self, mock_ffmpeg):
        """Test segmenting audio with regular Chapter objects."""
        # Mock format converter methods
        with patch.object(self.segmenter.format_converter, 'validate_audio_file') as mock_validate:
            with patch.object(self.segmenter.format_converter, 'get_audio_info') as mock_info:
                with patch.object(self.segmenter.format_converter, 'create_audiobook_chapters_from_text_chapters') as mock_create:
                    
                    mock_validate.return_value = True
                    mock_info.return_value = {'duration': 300.0, 'sample_rate': 22050}
                    
                    # Mock audiobook chapters creation
                    audiobook_chapters = [
                        AudiobookChapter(title="Chapter 1", start_time=0.0, end_time=150.0),
                        AudiobookChapter(title="Chapter 2", start_time=150.0, end_time=300.0)
                    ]
                    mock_create.return_value = audiobook_chapters
                    
                    # Mock ffmpeg
                    mock_input_obj = MagicMock()
                    mock_output_obj = MagicMock()
                    mock_overwrite_obj = MagicMock()
                    
                    mock_ffmpeg.input.return_value = mock_input_obj
                    mock_input_obj.output.return_value = mock_output_obj
                    mock_output_obj.overwrite_output.return_value = mock_overwrite_obj
                    mock_overwrite_obj.run.return_value = None
                    
                    # Test with regular Chapter objects
                    text_chapters = [
                        Chapter(title="Chapter 1", content="Content 1"),
                        Chapter(title="Chapter 2", content="Content 2")
                    ]
                    
                    config = SegmentationConfig.default()
                    config.enabled = True
                    config.chapters_per_file = 1
                    config.create_subfolders = False
                    
                    result = self.segmenter.segment_audio(
                        self.test_audio_path, text_chapters, config, self.temp_dir
                    )
                    
                    # Should create 2 segments (1 chapter per file)
                    self.assertEqual(len(result), 2)
                    
                    # Verify conversion was called
                    mock_create.assert_called_once_with(text_chapters, 300.0)


if __name__ == '__main__':
    unittest.main()