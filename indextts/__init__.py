"""
IndexTTS2: A Breakthrough in Emotionally Expressive and Duration-Controlled Auto-Regressive Zero-Shot Text-to-Speech

Enhanced WebUI Features:
- File upload and processing (TXT, EPUB)
- Smart chapter parsing
- Multiple audio formats (WAV, MP3, M4B)
- Background task management
- Voice sample management
- Output file organization
"""

# Enhanced WebUI components
from .enhanced_webui import EnhancedWebUI
from .file_processing import FileProcessor
from .chapter_parsing import SmartChapterParser
from .audio_formats import AudioFormatConverter
from .task_management import TaskManager
from .voice_management import VoiceSampleManager
from .output_management import OutputManager
from .config import EnhancedWebUIConfig, ConfigManager

__all__ = [
    'EnhancedWebUI',
    'FileProcessor',
    'SmartChapterParser', 
    'AudioFormatConverter',
    'TaskManager',
    'VoiceSampleManager',
    'OutputManager',
    'EnhancedWebUIConfig',
    'ConfigManager'
]