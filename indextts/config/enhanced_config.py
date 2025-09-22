"""
Configuration classes for enhanced WebUI features.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
from ..file_processing.models import FileProcessingConfig
from ..chapter_parsing.models import ChapterParsingConfig
from ..audio_formats.models import AudioFormatConfig
from ..task_management.models import TaskManagerConfig


@dataclass
class VoiceSampleConfig:
    """Configuration for voice sample management."""
    samples_directory: str
    supported_formats: list
    auto_create_directory: bool
    default_samples: list
    
    @classmethod
    def default(cls) -> 'VoiceSampleConfig':
        """Create default voice sample configuration."""
        return cls(
            samples_directory="samples",
            supported_formats=['wav', 'mp3'],
            auto_create_directory=True,
            default_samples=[]
        )


@dataclass
class OutputConfig:
    """Configuration for output file management."""
    output_directory: str
    auto_save_enabled: bool
    filename_format: str
    create_subfolders: bool
    max_output_files: int
    
    @classmethod
    def default(cls) -> 'OutputConfig':
        """Create default output configuration."""
        return cls(
            output_directory="outputs",
            auto_save_enabled=True,
            filename_format="{filename}_{date}_{voice_name}",
            create_subfolders=False,  # Don't create subfolders - save directly to outputs
            max_output_files=1000
        )


@dataclass
class UIConfig:
    """Configuration for UI behavior and features."""
    enable_file_upload: bool
    enable_background_tasks: bool
    enable_chapter_parsing: bool
    enable_audio_segmentation: bool
    show_advanced_options: bool
    max_file_size_mb: int
    
    @classmethod
    def default(cls) -> 'UIConfig':
        """Create default UI configuration."""
        return cls(
            enable_file_upload=True,
            enable_background_tasks=True,
            enable_chapter_parsing=True,
            enable_audio_segmentation=True,
            show_advanced_options=False,
            max_file_size_mb=50
        )


@dataclass
class EnhancedWebUIConfig:
    """Main configuration class for all enhanced WebUI features."""
    file_processing: FileProcessingConfig
    chapter_parsing: ChapterParsingConfig
    audio_formats: AudioFormatConfig
    task_management: TaskManagerConfig
    voice_samples: VoiceSampleConfig
    output: OutputConfig
    ui: UIConfig
    
    @classmethod
    def default(cls) -> 'EnhancedWebUIConfig':
        """Create default configuration for all components."""
        return cls(
            file_processing=FileProcessingConfig.default(),
            chapter_parsing=ChapterParsingConfig.default(),
            audio_formats=AudioFormatConfig.default(),
            task_management=TaskManagerConfig.default(),
            voice_samples=VoiceSampleConfig.default(),
            output=OutputConfig.default(),
            ui=UIConfig.default()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'file_processing': self.file_processing.__dict__,
            'chapter_parsing': self.chapter_parsing.__dict__,
            'audio_formats': self.audio_formats.__dict__,
            'task_management': self.task_management.__dict__,
            'voice_samples': self.voice_samples.__dict__,
            'output': self.output.__dict__,
            'ui': self.ui.__dict__
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EnhancedWebUIConfig':
        """Create configuration from dictionary."""
        return cls(
            file_processing=FileProcessingConfig(**config_dict.get('file_processing', {})),
            chapter_parsing=ChapterParsingConfig(**config_dict.get('chapter_parsing', {})),
            audio_formats=AudioFormatConfig(**config_dict.get('audio_formats', {})),
            task_management=TaskManagerConfig(**config_dict.get('task_management', {})),
            voice_samples=VoiceSampleConfig(**config_dict.get('voice_samples', {})),
            output=OutputConfig(**config_dict.get('output', {})),
            ui=UIConfig(**config_dict.get('ui', {}))
        )