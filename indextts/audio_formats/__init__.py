"""
Audio format management module for converting between WAV, MP3, and M4B formats.
"""

from .format_converter import AudioFormatConverter
from .models import AudioGenerationRequest, SegmentationConfig

__all__ = ['AudioFormatConverter', 'AudioGenerationRequest', 'SegmentationConfig']