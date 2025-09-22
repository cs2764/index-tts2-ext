"""
Unit tests for voice selection demo.
"""

import os
import tempfile
import shutil
import pytest
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock

from indextts.enhanced_webui.voice_selection_demo import VoiceSelectionDemo


class TestVoiceSelectionDemo:
    """Test cases for voice selection demo."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the enhanced webui to use temp directory
        with patch('indextts.enhanced_webui.voice_selection_demo.EnhancedWebUI') as mock_webui_class:
            mock_webui = MagicMock()
            mock_voice_manager = MagicMock()
            mock_voice_manager.get_samples_directory.return_value = os.path.join(self.temp_dir, "samples")
            mock_webui.get_voice_manager.return_value = mock_voice_manager
            mock_webui_class.return_value = mock_webui
            
            self.demo = VoiceSelectionDemo()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_audio_file(self, filepath: str, duration: float = 1.0, 
                              sample_rate: int = 22050):
        """Create a test audio file."""
        # Generate test audio data (sine wave)
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write audio file
        sf.write(filepath, audio_data, sample_rate)
    
    def test_demo_initialization(self):
        """Test demo initialization."""
        assert self.demo is not None
        assert self.demo.enhanced_webui is not None
        assert self.demo.components is not None
    
    def test_create_interface(self):
        """Test interface creation."""
        interface = self.demo.create_interface()
        assert interface is not None
    
    def test_handle_refresh_empty(self):
        """Test refresh handling with no samples."""
        dropdown, status, folder_info = self.demo._handle_refresh()
        
        assert dropdown is not None
        assert status is not None
        assert folder_info is not None
    
    def test_handle_voice_selection_empty(self):
        """Test voice selection with no path."""
        sample_info, validation_status = self.demo._handle_voice_selection("")
        
        assert sample_info is not None
        assert validation_status is not None
    
    def test_handle_voice_selection_with_path(self):
        """Test voice selection with valid path."""
        # Create test file
        samples_dir = os.path.join(self.temp_dir, "samples")
        test_file = os.path.join(samples_dir, "test.wav")
        self.create_test_audio_file(test_file)
        
        # Mock the components to return valid info
        with patch.object(self.demo.components, 'get_voice_sample_info') as mock_info, \
             patch.object(self.demo.components, 'validate_voice_selection') as mock_validate:
            
            mock_info.return_value = {
                'filename': 'test.wav',
                'format': 'wav',
                'duration': 1.0,
                'sample_rate': 22050,
                'is_valid': True
            }
            mock_validate.return_value = (True, "")
            
            sample_info, validation_status = self.demo._handle_voice_selection(test_file)
            
            assert sample_info is not None
            assert validation_status is not None
    
    def test_get_folder_info_html_nonexistent(self):
        """Test folder info HTML for nonexistent folder."""
        html = self.demo._get_folder_info_html()
        
        assert "Samples folder" in html
        assert "will be created automatically" in html
    
    def test_get_folder_info_html_existing(self):
        """Test folder info HTML for existing folder."""
        # Create samples directory with test files
        samples_dir = os.path.join(self.temp_dir, "samples")
        os.makedirs(samples_dir, exist_ok=True)
        
        # Create test files
        self.create_test_audio_file(os.path.join(samples_dir, "test1.wav"))
        self.create_test_audio_file(os.path.join(samples_dir, "test2.wav"))
        
        # Create non-audio file
        with open(os.path.join(samples_dir, "readme.txt"), 'w') as f:
            f.write("test")
        
        html = self.demo._get_folder_info_html()
        
        assert "Samples folder" in html
        assert "2 audio" in html
        assert "1 other" in html
    
    def test_handle_initial_load(self):
        """Test initial load handling."""
        dropdown, status, folder_info = self.demo._handle_initial_load()
        
        assert dropdown is not None
        assert status is not None
        assert folder_info is not None
    
    def test_error_handling_in_refresh(self):
        """Test error handling in refresh."""
        # Mock components to raise exception
        with patch.object(self.demo.components, 'refresh_voice_samples', side_effect=Exception("Test error")):
            dropdown, status, folder_info = self.demo._handle_refresh()
            
            assert dropdown is not None
            assert status is not None
            assert folder_info is not None


if __name__ == "__main__":
    pytest.main([__file__])