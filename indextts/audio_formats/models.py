"""
Data models for audio format management components.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class AudiobookChapter:
    """Chapter with timing information for audiobook creation."""
    title: str
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    content: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Get chapter duration in seconds."""
        return self.end_time - self.start_time


@dataclass
class EmotionSettings:
    """Settings for emotion control in TTS generation."""
    control_method: int  # 0-3 for different emotion control modes
    reference_audio: Optional[str]
    emotion_weight: float
    emotion_vector: Optional[List[float]]
    emotion_text: Optional[str]
    use_random: bool
    
    @classmethod
    def default(cls) -> 'EmotionSettings':
        """Create default emotion settings."""
        return cls(
            control_method=0,
            reference_audio=None,
            emotion_weight=0.8,
            emotion_vector=None,
            emotion_text=None,
            use_random=False
        )


@dataclass
class GenerationParams:
    """Parameters for TTS generation."""
    do_sample: bool
    top_p: float
    top_k: Optional[int]
    temperature: float
    length_penalty: float
    num_beams: int
    repetition_penalty: float
    max_mel_tokens: int
    
    @classmethod
    def default(cls) -> 'GenerationParams':
        """Create default generation parameters."""
        return cls(
            do_sample=True,
            top_p=0.8,
            top_k=30,
            temperature=0.8,
            length_penalty=0.0,
            num_beams=3,
            repetition_penalty=10.0,
            max_mel_tokens=1500
        )


@dataclass
class SegmentationConfig:
    """Configuration for audio segmentation."""
    enabled: bool
    chapters_per_file: int
    use_chapter_detection: bool
    max_file_duration: Optional[float]
    create_subfolders: bool
    
    @classmethod
    def default(cls) -> 'SegmentationConfig':
        """Create default segmentation configuration."""
        return cls(
            enabled=False,
            chapters_per_file=10,
            use_chapter_detection=True,
            max_file_duration=None,
            create_subfolders=False  # Don't create subfolders - save directly to outputs
        )


@dataclass
class AudioGenerationRequest:
    """Complete request for audio generation with all parameters."""
    text_content: str
    voice_sample_path: str
    output_format: str
    emotion_settings: EmotionSettings
    generation_params: GenerationParams
    segmentation_config: SegmentationConfig
    auto_save: bool
    source_filename: Optional[str]
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AudioFormatConfig:
    """Configuration for audio format conversion."""
    supported_formats: List[str]
    default_format: str
    mp3_bitrate: int
    m4b_cover_support: bool
    chapter_metadata_support: bool
    
    @classmethod
    def default(cls) -> 'AudioFormatConfig':
        """Create default audio format configuration."""
        return cls(
            supported_formats=['wav', 'mp3', 'm4b'],
            default_format='mp3',
            mp3_bitrate=64,
            m4b_cover_support=True,
            chapter_metadata_support=True
        )