"""
Unit tests for segmented file organization functionality.
"""

import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch
import pytest

from indextts.output_management.output_manager import OutputManager
from indextts.output_management.models import SegmentedOutput
from indextts.config.enhanced_config import OutputConfig


class TestSegmentedFileOrganization:
    """Test cases for segmented file organization."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config = OutputConfig(
            output_directory=self.temp_dir,
            auto_save_enabled=True,
            filename_format="{filename}_{date}_{voice_name}",
            create_subfolders=True,
            max_output_files=1000
        )
        self.manager = OutputManager(self.config)
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_subfolder_structure(self):
        """Test creation of subfolder structure for segmented files."""
        segments_data = [
            b"chapter 1-5 audio data",
            b"chapter 6-10 audio data",
            b"chapter 11-15 audio data"
        ]
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="my_novel",
            format_ext="m4b",
            chapters_per_file=5,
            source_filename="novel.txt",
            voice_name="narrator_alice"
        )
        
        # Check that subfolder was created
        assert os.path.exists(segmented_output.output_directory)
        assert os.path.isdir(segmented_output.output_directory)
        
        # Check folder name format includes filename + date + voice_name
        folder_name = os.path.basename(segmented_output.output_directory)
        assert "my_novel" in folder_name
        assert "narrator_alice" in folder_name
        assert len(folder_name.split("_")) >= 3  # Should have at least filename, date, voice parts
    
    def test_chapter_range_naming_single_digit(self):
        """Test chapter range naming with single digit ranges."""
        segments_data = [
            b"chapters 1-5",
            b"chapters 6-10",
            b"chapters 11-15"
        ]
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="book",
            format_ext="m4b",
            chapters_per_file=5,
            voice_name="voice1"
        )
        
        actual_filenames = [segment.filename for segment in segmented_output.segments]
        
        # With chapters_per_file=5, we get: 1-5, 6-10, 11-15
        assert len(actual_filenames) == 3
        assert actual_filenames[0] == "1-5.m4b"
        assert actual_filenames[1] == "6-10.m4b" 
        assert actual_filenames[2] == "11-15.m4b"
    
    def test_chapter_range_naming_large_numbers(self):
        """Test chapter range naming with large chapter numbers."""
        # Create 25 segments to test larger ranges
        segments_data = [b"segment data"] * 25
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="long_book",
            format_ext="mp3",
            chapters_per_file=10,
            voice_name="narrator"
        )
        
        # Check first few segment names
        expected_names = [
            "1-10.mp3",
            "11-20.mp3", 
            "21-30.mp3"  # Fixed range based on chapters_per_file
        ]
        
        actual_names = [segment.filename for segment in segmented_output.segments[:3]]
        assert actual_names == expected_names
    
    def test_folder_naming_format(self):
        """Test folder naming with filename + date + voice_name format."""
        timestamp = datetime(2024, 5, 15, 14, 30, 45)
        
        with patch('indextts.output_management.output_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp
            
            folder_path = self.manager.create_output_folder(
                base_filename="audiobook_series",
                voice_name="professional_narrator"
            )
            
            expected_folder_name = "audiobook_series_20240515_143045_professional_narrator"
            expected_path = os.path.join(self.temp_dir, expected_folder_name)
            
            assert folder_path == expected_path
            assert os.path.exists(folder_path)
    
    def test_folder_naming_without_voice_name(self):
        """Test folder naming when voice name is not provided."""
        timestamp = datetime(2024, 6, 20, 9, 15, 30)
        
        with patch('indextts.output_management.output_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp
            
            folder_path = self.manager.create_output_folder(
                base_filename="simple_book"
            )
            
            expected_folder_name = "simple_book_20240620_091530"
            expected_path = os.path.join(self.temp_dir, expected_folder_name)
            
            assert folder_path == expected_path
            assert os.path.exists(folder_path)
    
    def test_segmented_file_organization_structure(self):
        """Test complete segmented file organization structure."""
        segments_data = [
            b"part 1 audio",
            b"part 2 audio", 
            b"part 3 audio",
            b"part 4 audio"
        ]
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="epic_fantasy",
            format_ext="m4b",
            chapters_per_file=2,
            source_filename="fantasy.epub",
            voice_name="epic_narrator"
        )
        
        # Verify SegmentedOutput structure
        assert segmented_output.base_filename == "epic_fantasy"
        assert segmented_output.total_files == 4
        assert len(segmented_output.segments) == 4
        
        # Verify each segment file exists and has correct properties
        for i, segment in enumerate(segmented_output.segments):
            # Check file exists
            assert os.path.exists(segment.filepath)
            
            # Check segment properties
            assert segment.is_segmented == True
            assert segment.source_filename == "fantasy.epub"
            assert segment.voice_name == "epic_narrator"
            assert segment.format == "m4b"
            
            # Check segment info
            expected_start = (i * 2) + 1
            expected_end = (i + 1) * 2  # Fixed range based on chapters_per_file
            assert segment.segment_info['start_chapter'] == expected_start
            assert segment.segment_info['end_chapter'] == expected_end
            assert segment.segment_info['segment_index'] == i
            assert segment.segment_info['total_segments'] == 4
            
            # Check filename format
            expected_filename = f"{expected_start}-{expected_end}.m4b"
            assert segment.filename == expected_filename
    
    def test_single_segment_file_naming(self):
        """Test file naming when there's only one segment."""
        segments_data = [b"single chapter audio"]
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="short_story",
            format_ext="wav",
            chapters_per_file=10,
            voice_name="storyteller"
        )
        
        # With only one segment, should use base filename
        assert len(segmented_output.segments) == 1
        segment = segmented_output.segments[0]
        assert segment.filename == "short_story.wav"
    
    def test_different_audio_formats(self):
        """Test segmented file organization with different audio formats."""
        segments_data = [b"audio1", b"audio2"]
        
        formats_to_test = ["wav", "mp3", "m4b"]
        
        for format_ext in formats_to_test:
            segmented_output = self.manager.save_audio_segments(
                segments_data=segments_data,
                base_filename=f"test_{format_ext}",
                format_ext=format_ext,
                chapters_per_file=1,
                voice_name="test_voice"
            )
            
            # Check that files have correct format
            for segment in segmented_output.segments:
                assert segment.format == format_ext
                assert segment.filename.endswith(f".{format_ext}")
                assert os.path.exists(segment.filepath)
    
    def test_large_number_of_segments(self):
        """Test organization with a large number of segments."""
        # Create 100 segments
        segments_data = [f"segment {i} data".encode() for i in range(100)]
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="massive_audiobook",
            format_ext="mp3",
            chapters_per_file=10,
            voice_name="marathon_narrator"
        )
        
        # Should create 100 segments
        assert segmented_output.total_files == 100
        assert len(segmented_output.segments) == 100
        
        # Check first and last segment naming
        first_segment = segmented_output.segments[0]
        last_segment = segmented_output.segments[-1]
        
        assert first_segment.filename == "1-10.mp3"
        assert last_segment.filename == "991-1000.mp3"
        
        # Verify all files exist
        for segment in segmented_output.segments:
            assert os.path.exists(segment.filepath)
    
    def test_chapters_per_file_edge_cases(self):
        """Test different chapters_per_file values."""
        segments_data = [b"data1", b"data2", b"data3", b"data4", b"data5"]
        
        # Test chapters_per_file = 1 (each segment is one chapter)
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="individual_chapters",
            format_ext="wav",
            chapters_per_file=1,
            voice_name="voice"
        )
        
        expected_filenames = ["1-1.wav", "2-2.wav", "3-3.wav", "4-4.wav", "5-5.wav"]
        actual_filenames = [s.filename for s in segmented_output.segments]
        assert actual_filenames == expected_filenames
        
        # Test chapters_per_file > number of segments
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename="few_chapters",
            format_ext="mp3", 
            chapters_per_file=10,
            voice_name="voice"
        )
        
        expected_filenames = ["1-10.mp3", "11-20.mp3", "21-30.mp3", "31-40.mp3", "41-50.mp3"]
        actual_filenames = [s.filename for s in segmented_output.segments]
        assert actual_filenames == expected_filenames
    
    def test_folder_organization_multiple_books(self):
        """Test that multiple books create separate organized folders."""
        # Create segments for first book
        segments1 = [b"book1 part1", b"book1 part2"]
        segmented_output1 = self.manager.save_audio_segments(
            segments_data=segments1,
            base_filename="book_one",
            format_ext="m4b",
            voice_name="narrator1"
        )
        
        # Create segments for second book
        segments2 = [b"book2 part1", b"book2 part2"]
        segmented_output2 = self.manager.save_audio_segments(
            segments_data=segments2,
            base_filename="book_two", 
            format_ext="m4b",
            voice_name="narrator2"
        )
        
        # Should have different output directories
        assert segmented_output1.output_directory != segmented_output2.output_directory
        
        # Both directories should exist
        assert os.path.exists(segmented_output1.output_directory)
        assert os.path.exists(segmented_output2.output_directory)
        
        # Check folder names contain correct book names and narrators
        folder1_name = os.path.basename(segmented_output1.output_directory)
        folder2_name = os.path.basename(segmented_output2.output_directory)
        
        assert "book_one" in folder1_name and "narrator1" in folder1_name
        assert "book_two" in folder2_name and "narrator2" in folder2_name


if __name__ == "__main__":
    pytest.main([__file__])