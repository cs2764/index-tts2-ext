"""
Unit tests for OutputManager class.
"""

import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest

from indextts.output_management.output_manager import OutputManager
from indextts.output_management.models import OutputFile, SegmentedOutput
from indextts.config.enhanced_config import OutputConfig


class TestOutputManager:
    """Test cases for OutputManager class."""
    
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
    
    def test_init_default_config(self):
        """Test OutputManager initialization with default config."""
        manager = OutputManager()
        assert manager.config is not None
        assert manager.auto_save_enabled == True  # Default should be True
        assert os.path.exists(manager.config.output_directory)
    
    def test_init_custom_config(self):
        """Test OutputManager initialization with custom config."""
        assert self.manager.config == self.config
        assert self.manager.auto_save_enabled == True
        assert os.path.exists(self.temp_dir)
    
    def test_auto_save_toggle(self):
        """Test auto-save toggle functionality."""
        # Initially enabled
        assert self.manager.auto_save_enabled == True
        assert self.manager.should_auto_save() == True
        
        # Disable auto-save
        self.manager.set_auto_save(False)
        assert self.manager.auto_save_enabled == False
        assert self.manager.should_auto_save() == False
        
        # Re-enable auto-save
        self.manager.set_auto_save(True)
        assert self.manager.auto_save_enabled == True
        assert self.manager.should_auto_save() == True
    
    def test_generate_filename_with_source_file(self):
        """Test filename generation with source file."""
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        filename = self.manager.generate_filename(
            source_file="test_book.txt",
            voice_name="alice",
            format_ext="mp3",
            timestamp=timestamp
        )
        expected = "test_book_20240115_143045_alice.mp3"
        assert filename == expected
    
    def test_generate_filename_without_source_file(self):
        """Test filename generation without source file (direct text input)."""
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        filename = self.manager.generate_filename(
            source_file=None,
            voice_name="bob",
            format_ext="wav",
            timestamp=timestamp
        )
        expected = "generation_20240115_143045_bob.wav"
        assert filename == expected
    
    def test_generate_filename_current_time(self):
        """Test filename generation with current time."""
        with patch('indextts.output_management.output_manager.datetime') as mock_datetime:
            mock_now = datetime(2024, 2, 20, 10, 15, 30)
            mock_datetime.now.return_value = mock_now
            
            filename = self.manager.generate_filename(
                source_file="novel.epub",
                voice_name="charlie",
                format_ext="m4b"
            )
            expected = "novel_20240220_101530_charlie.m4b"
            assert filename == expected
    
    def test_save_audio_file(self):
        """Test saving audio file."""
        audio_data = b"fake audio data"
        filename = "test_audio.mp3"
        
        output_file = self.manager.save_audio_file(
            audio_data=audio_data,
            filename=filename,
            source_filename="source.txt",
            voice_name="alice"
        )
        
        # Check file was created
        expected_path = os.path.join(self.temp_dir, filename)
        assert os.path.exists(expected_path)
        
        # Check file content
        with open(expected_path, 'rb') as f:
            assert f.read() == audio_data
        
        # Check OutputFile object
        assert output_file.filename == filename
        assert output_file.filepath == expected_path
        assert output_file.format == "mp3"
        assert output_file.file_size == len(audio_data)
        assert output_file.source_filename == "source.txt"
        assert output_file.voice_name == "alice"
        assert output_file.is_segmented == False
        assert isinstance(output_file.created_at, datetime)
    
    def test_save_audio_segments(self):
        """Test saving segmented audio files."""
        segments_data = [
            b"segment 1 data",
            b"segment 2 data",
            b"segment 3 data"
        ]
        base_filename = "test_book"
        format_ext = "m4b"
        chapters_per_file = 10
        
        segmented_output = self.manager.save_audio_segments(
            segments_data=segments_data,
            base_filename=base_filename,
            format_ext=format_ext,
            chapters_per_file=chapters_per_file,
            source_filename="book.txt",
            voice_name="narrator"
        )
        
        # Check SegmentedOutput object
        assert segmented_output.base_filename == base_filename
        assert segmented_output.total_files == 3
        assert len(segmented_output.segments) == 3
        assert isinstance(segmented_output.created_at, datetime)
        
        # Check individual segments
        for i, segment in enumerate(segmented_output.segments):
            start_chapter = (i * chapters_per_file) + 1
            end_chapter = (i + 1) * chapters_per_file
            expected_filename = f"{start_chapter}-{end_chapter}.{format_ext}"
            assert segment.filename == expected_filename
            assert segment.is_segmented == True
            assert segment.segment_info['start_chapter'] == start_chapter
            assert segment.segment_info['end_chapter'] == end_chapter
            assert segment.segment_info['segment_index'] == i
            assert segment.segment_info['total_segments'] == 3
            
            # Check file exists
            assert os.path.exists(segment.filepath)
            
            # Check file content
            with open(segment.filepath, 'rb') as f:
                assert f.read() == segments_data[i]
    
    def test_create_output_folder(self):
        """Test creating output folder."""
        timestamp = datetime(2024, 3, 10, 16, 45, 20)
        folder_path = self.manager.create_output_folder(
            base_filename="my_audiobook",
            timestamp=timestamp,
            voice_name="sarah"
        )
        
        expected_folder = os.path.join(self.temp_dir, "my_audiobook_20240310_164520_sarah")
        assert folder_path == expected_folder
        assert os.path.exists(folder_path)
        assert os.path.isdir(folder_path)
    
    def test_create_output_folder_without_voice_name(self):
        """Test creating output folder without voice name."""
        timestamp = datetime(2024, 3, 10, 16, 45, 20)
        folder_path = self.manager.create_output_folder(
            base_filename="my_audiobook",
            timestamp=timestamp
        )
        
        expected_folder = os.path.join(self.temp_dir, "my_audiobook_20240310_164520")
        assert folder_path == expected_folder
        assert os.path.exists(folder_path)
    
    def test_get_output_files_empty_directory(self):
        """Test getting output files from empty directory."""
        output_files = self.manager.get_output_files()
        assert output_files == []
    
    def test_get_output_files_with_files(self):
        """Test getting output files with existing files."""
        # Create some test files
        test_files = [
            ("audio1.mp3", b"audio data 1"),
            ("audio2.wav", b"audio data 2"),
            ("document.txt", b"not audio"),  # Should be ignored
            ("audio3.m4b", b"audio data 3")
        ]
        
        for filename, data in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(data)
        
        # Create a subfolder with segmented files
        subfolder = os.path.join(self.temp_dir, "segments")
        os.makedirs(subfolder)
        with open(os.path.join(subfolder, "1-10.mp3"), 'wb') as f:
            f.write(b"segment data")
        
        output_files = self.manager.get_output_files()
        
        # Should find 4 audio files (3 in root + 1 in subfolder)
        assert len(output_files) == 4
        
        # Check that non-audio files are excluded
        filenames = [f.filename for f in output_files]
        assert "document.txt" not in filenames
        assert "audio1.mp3" in filenames
        assert "audio2.wav" in filenames
        assert "audio3.m4b" in filenames
        assert "1-10.mp3" in filenames
        
        # Check segmented file detection
        segmented_files = [f for f in output_files if f.is_segmented]
        assert len(segmented_files) == 1
        assert segmented_files[0].filename == "1-10.mp3"
    
    def test_cleanup_old_files(self):
        """Test cleanup of old files."""
        # Create test files with different ages
        current_time = 1000000000  # Mock timestamp
        
        with patch('time.time', return_value=current_time):
            with patch('os.path.getctime') as mock_getctime:
                # Create files
                old_file = os.path.join(self.temp_dir, "old.mp3")
                new_file = os.path.join(self.temp_dir, "new.mp3")
                
                with open(old_file, 'w') as f:
                    f.write("old")
                with open(new_file, 'w') as f:
                    f.write("new")
                
                # Mock file creation times
                def mock_getctime_func(path):
                    if "old.mp3" in path:
                        return current_time - (31 * 24 * 3600)  # 31 days old
                    else:
                        return current_time - (1 * 24 * 3600)   # 1 day old
                
                mock_getctime.side_effect = mock_getctime_func
                
                # Run cleanup (max age 30 days)
                self.manager.cleanup_old_files(max_age_days=30)
                
                # Check results
                assert not os.path.exists(old_file)  # Should be removed
                assert os.path.exists(new_file)      # Should remain
    
    def test_ensure_output_directory_creation(self):
        """Test automatic output directory creation."""
        # Remove the directory
        shutil.rmtree(self.temp_dir)
        assert not os.path.exists(self.temp_dir)
        
        # Create new manager (should recreate directory)
        new_manager = OutputManager(self.config)
        assert os.path.exists(self.temp_dir)
    
    def test_filename_generation_edge_cases(self):
        """Test filename generation with edge cases."""
        # Test with file that has multiple extensions
        filename = self.manager.generate_filename(
            source_file="archive.tar.gz",
            voice_name="test",
            format_ext="mp3",
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        assert filename == "archive.tar_20240101_120000_test.mp3"
        
        # Test with file that has no extension
        filename = self.manager.generate_filename(
            source_file="README",
            voice_name="test",
            format_ext="wav",
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        assert filename == "README_20240101_120000_test.wav"
        
        # Test with path separators in source file
        filename = self.manager.generate_filename(
            source_file="/path/to/file.txt",
            voice_name="test",
            format_ext="m4b",
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        assert filename == "file_20240101_120000_test.m4b"


if __name__ == "__main__":
    pytest.main([__file__])