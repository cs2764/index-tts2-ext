"""
Enhanced configuration manager for IndexTTS2 WebUI.
Handles configuration loading, environment variable support, and graceful degradation.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileProcessingConfig:
    """Configuration for file processing features."""
    max_file_size_mb: int = 100
    preview_max_lines: int = 40
    enable_caching: bool = True
    cache_max_entries: int = 100
    cache_max_age_hours: int = 24
    supported_formats: list = field(default_factory=lambda: ['txt', 'epub'])
    text_cleaning_enabled_by_default: bool = True
    supported_encodings: list = field(default_factory=lambda: ['utf-8', 'gbk', 'gb2312'])
    fallback_encoding: str = 'utf-8'


@dataclass
class ChapterRecognitionConfig:
    """Configuration for chapter recognition features."""
    enabled_by_default: bool = False
    confidence_threshold: float = 0.7
    max_chapters_to_display: int = 10
    patterns: Dict[str, list] = field(default_factory=dict)


@dataclass
class AudioFormatConfig:
    """Configuration for audio format features."""
    default_format: str = 'mp3'
    mp3_default_bitrate: int = 64
    mp3_supported_bitrates: list = field(default_factory=lambda: [32, 64, 96, 128, 192, 256, 320])
    m4b_enable_chapters: bool = True
    m4b_enable_cover_art: bool = True
    default_chapters_per_file: int = 20
    max_chapters_per_file: int = 200


@dataclass
class VoiceManagementConfig:
    """Configuration for voice management features."""
    samples_directory: str = 'samples'
    auto_create_directory: bool = True
    supported_formats: list = field(default_factory=lambda: ['wav', 'mp3'])
    min_duration_seconds: float = 1.0
    max_duration_seconds: float = 30.0


@dataclass
class OutputManagementConfig:
    """Configuration for output management features."""
    output_directory: str = 'outputs'
    auto_create_directory: bool = True
    auto_save_enabled_by_default: bool = True
    filename_format: str = '{source_name}_{date}_{voice_name}.{format}'
    date_format: str = '%Y%m%d_%H%M%S'


@dataclass
class TaskManagementConfig:
    """Configuration for task management features."""
    enabled: bool = True
    max_concurrent_tasks: int = 3
    task_timeout_minutes: int = 60
    auto_background_threshold_chars: int = 10000
    persistence_enabled: bool = True
    max_history_entries: int = 100


@dataclass
class UIThemeConfig:
    """Configuration for UI theme features."""
    default_theme: str = 'auto'  # auto, light, dark
    dark_theme_colors: Dict[str, str] = field(default_factory=dict)
    light_theme_colors: Dict[str, str] = field(default_factory=dict)
    component_styles: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    enable_memory_optimization: bool = True
    max_memory_usage_percent: int = 80
    enable_preview_cache: bool = True
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    debounce_delay_ms: int = 300


@dataclass
class EnhancedWebUIConfig:
    """Main configuration class for enhanced WebUI features."""
    enabled: bool = True
    file_processing: FileProcessingConfig = field(default_factory=FileProcessingConfig)
    chapter_recognition: ChapterRecognitionConfig = field(default_factory=ChapterRecognitionConfig)
    audio_formats: AudioFormatConfig = field(default_factory=AudioFormatConfig)
    voice_management: VoiceManagementConfig = field(default_factory=VoiceManagementConfig)
    output_management: OutputManagementConfig = field(default_factory=OutputManagementConfig)
    task_management: TaskManagementConfig = field(default_factory=TaskManagementConfig)
    ui_theme: UIThemeConfig = field(default_factory=UIThemeConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    feature_flags: Dict[str, Any] = field(default_factory=dict)


class EnhancedConfigManager:
    """Enhanced configuration manager with environment variable support and graceful degradation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager."""
        self.logger = logging.getLogger(__name__)
        
        # Default config paths
        self.default_config_paths = [
            'config/enhanced_webui_config.yaml',
            'enhanced_webui_config.yaml',
            os.path.expanduser('~/.indextts/enhanced_webui_config.yaml')
        ]
        
        # Use provided path or search for default
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = self._find_config_file()
        
        # Load configuration
        self.config = self._load_config()
        
        # Apply environment variable overrides
        self._apply_environment_overrides()
        
        # Validate configuration
        self._validate_config()
    
    def _find_config_file(self) -> Optional[str]:
        """Find the configuration file."""
        for path in self.default_config_paths:
            if os.path.exists(path):
                self.logger.info(f"Found configuration file: {path}")
                return path
        
        self.logger.warning("No configuration file found, using defaults")
        return None
    
    def _load_config(self) -> EnhancedWebUIConfig:
        """Load configuration from file or use defaults."""
        if not self.config_path or not os.path.exists(self.config_path):
            self.logger.info("Using default configuration")
            return EnhancedWebUIConfig()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Extract enhanced features configuration
            enhanced_config = config_data.get('enhanced_features', {})
            
            return self._parse_config_data(enhanced_config)
            
        except Exception as e:
            self.logger.error(f"Error loading configuration from {self.config_path}: {e}")
            self.logger.info("Falling back to default configuration")
            return EnhancedWebUIConfig()
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> EnhancedWebUIConfig:
        """Parse configuration data into structured config objects."""
        try:
            # File processing config
            file_proc_data = config_data.get('file_processing', {})
            file_processing = FileProcessingConfig(
                max_file_size_mb=file_proc_data.get('max_file_size_mb', 100),
                preview_max_lines=file_proc_data.get('preview', {}).get('max_lines', 40),
                enable_caching=file_proc_data.get('preview', {}).get('enable_caching', True),
                cache_max_entries=file_proc_data.get('preview', {}).get('cache_max_entries', 100),
                cache_max_age_hours=file_proc_data.get('preview', {}).get('cache_max_age_hours', 24),
                supported_formats=file_proc_data.get('supported_formats', ['txt', 'epub']),
                text_cleaning_enabled_by_default=file_proc_data.get('text_cleaning', {}).get('enabled_by_default', True),
                supported_encodings=file_proc_data.get('encoding', {}).get('supported_encodings', ['utf-8', 'gbk', 'gb2312']),
                fallback_encoding=file_proc_data.get('encoding', {}).get('fallback_encoding', 'utf-8')
            )
            
            # Chapter recognition config
            chapter_data = config_data.get('chapter_recognition', {})
            chapter_recognition = ChapterRecognitionConfig(
                enabled_by_default=chapter_data.get('enabled_by_default', False),
                confidence_threshold=chapter_data.get('confidence_threshold', 0.7),
                max_chapters_to_display=chapter_data.get('max_chapters_to_display', 10),
                patterns=chapter_data.get('patterns', {})
            )
            
            # Audio format config
            audio_data = config_data.get('audio_formats', {})
            audio_formats = AudioFormatConfig(
                default_format=audio_data.get('default_format', 'mp3'),
                mp3_default_bitrate=audio_data.get('mp3', {}).get('default_bitrate', 64),
                mp3_supported_bitrates=audio_data.get('mp3', {}).get('supported_bitrates', [32, 64, 96, 128, 192, 256, 320]),
                m4b_enable_chapters=audio_data.get('m4b', {}).get('enable_chapters', True),
                m4b_enable_cover_art=audio_data.get('m4b', {}).get('enable_cover_art', True),
                default_chapters_per_file=audio_data.get('segmentation', {}).get('default_chapters_per_file', 20),
                max_chapters_per_file=audio_data.get('segmentation', {}).get('max_chapters_per_file', 200)
            )
            
            # Voice management config
            voice_data = config_data.get('voice_management', {})
            voice_management = VoiceManagementConfig(
                samples_directory=voice_data.get('samples_directory', 'samples'),
                auto_create_directory=voice_data.get('auto_create_directory', True),
                supported_formats=voice_data.get('supported_formats', ['wav', 'mp3']),
                min_duration_seconds=voice_data.get('validation', {}).get('min_duration_seconds', 1.0),
                max_duration_seconds=voice_data.get('validation', {}).get('max_duration_seconds', 30.0)
            )
            
            # Output management config
            output_data = config_data.get('output_management', {})
            output_management = OutputManagementConfig(
                output_directory=output_data.get('output_directory', 'outputs'),
                auto_create_directory=output_data.get('auto_create_directory', True),
                auto_save_enabled_by_default=output_data.get('auto_save_enabled_by_default', True),
                filename_format=output_data.get('filename_format', '{source_name}_{date}_{voice_name}.{format}'),
                date_format=output_data.get('date_format', '%Y%m%d_%H%M%S')
            )
            
            # Task management config
            task_data = config_data.get('task_management', {})
            task_management = TaskManagementConfig(
                enabled=task_data.get('enabled', True),
                max_concurrent_tasks=task_data.get('max_concurrent_tasks', 3),
                task_timeout_minutes=task_data.get('task_timeout_minutes', 60),
                auto_background_threshold_chars=task_data.get('auto_background_threshold_chars', 10000),
                persistence_enabled=task_data.get('persistence', {}).get('enabled', True),
                max_history_entries=task_data.get('persistence', {}).get('max_history_entries', 100)
            )
            
            # UI theme config
            theme_data = config_data.get('ui_theme', {})
            ui_theme = UIThemeConfig(
                default_theme=theme_data.get('default_theme', 'auto'),
                dark_theme_colors=theme_data.get('dark_theme', {}),
                light_theme_colors=theme_data.get('light_theme', {}),
                component_styles=theme_data.get('components', {})
            )
            
            # Performance config
            perf_data = config_data.get('performance', {})
            performance = PerformanceConfig(
                enable_memory_optimization=perf_data.get('memory', {}).get('enable_optimization', True),
                max_memory_usage_percent=perf_data.get('memory', {}).get('max_memory_usage_percent', 80),
                enable_preview_cache=perf_data.get('caching', {}).get('enable_preview_cache', True),
                enable_parallel_processing=perf_data.get('processing', {}).get('enable_parallel_processing', True),
                max_worker_threads=perf_data.get('processing', {}).get('max_worker_threads', 4),
                debounce_delay_ms=perf_data.get('ui', {}).get('debounce_delay_ms', 300)
            )
            
            # Feature flags
            feature_flags = config_data.get('feature_flags', {})
            
            return EnhancedWebUIConfig(
                enabled=config_data.get('enabled', True),
                file_processing=file_processing,
                chapter_recognition=chapter_recognition,
                audio_formats=audio_formats,
                voice_management=voice_management,
                output_management=output_management,
                task_management=task_management,
                ui_theme=ui_theme,
                performance=performance,
                feature_flags=feature_flags
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing configuration data: {e}")
            return EnhancedWebUIConfig()
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        env_mappings = {
            'INDEXTTS_MAX_FILE_SIZE_MB': ('file_processing.max_file_size_mb', int),
            'INDEXTTS_PREVIEW_MAX_LINES': ('file_processing.preview_max_lines', int),
            'INDEXTTS_SAMPLES_DIRECTORY': ('voice_management.samples_directory', str),
            'INDEXTTS_OUTPUT_DIRECTORY': ('output_management.output_directory', str),
            'INDEXTTS_MAX_CONCURRENT_TASKS': ('task_management.max_concurrent_tasks', int),
            'INDEXTTS_DEFAULT_THEME': ('ui_theme.default_theme', str),
            'INDEXTTS_ENABLE_ENHANCED_FEATURES': ('enabled', bool)
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Convert value to appropriate type
                    if value_type == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        converted_value = int(env_value)
                    else:
                        converted_value = env_value
                    
                    # Set the configuration value
                    self._set_config_value(config_path, converted_value)
                    self.logger.info(f"Applied environment override: {env_var} = {converted_value}")
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Invalid environment variable value for {env_var}: {env_value} ({e})")
    
    def _set_config_value(self, config_path: str, value: Any):
        """Set a configuration value using dot notation path."""
        parts = config_path.split('.')
        obj = self.config
        
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        setattr(obj, parts[-1], value)
    
    def _validate_config(self):
        """Validate configuration values."""
        try:
            # Validate file processing
            if self.config.file_processing.max_file_size_mb <= 0:
                self.logger.warning("Invalid max_file_size_mb, using default")
                self.config.file_processing.max_file_size_mb = 100
            
            if self.config.file_processing.preview_max_lines <= 0:
                self.logger.warning("Invalid preview_max_lines, using default")
                self.config.file_processing.preview_max_lines = 40
            
            # Validate chapter recognition
            if not 0 <= self.config.chapter_recognition.confidence_threshold <= 1:
                self.logger.warning("Invalid confidence_threshold, using default")
                self.config.chapter_recognition.confidence_threshold = 0.7
            
            # Validate audio formats
            if self.config.audio_formats.default_chapters_per_file <= 0:
                self.logger.warning("Invalid default_chapters_per_file, using default")
                self.config.audio_formats.default_chapters_per_file = 20
            
            # Validate task management
            if self.config.task_management.max_concurrent_tasks <= 0:
                self.logger.warning("Invalid max_concurrent_tasks, using default")
                self.config.task_management.max_concurrent_tasks = 3
            
            # Validate performance settings
            if not 0 < self.config.performance.max_memory_usage_percent <= 100:
                self.logger.warning("Invalid max_memory_usage_percent, using default")
                self.config.performance.max_memory_usage_percent = 80
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
    
    def get_config(self) -> EnhancedWebUIConfig:
        """Get the current configuration."""
        return self.config
    
    def is_feature_enabled(self, feature_path: str) -> bool:
        """Check if a specific feature is enabled."""
        if not self.config.enabled:
            return False
        
        try:
            parts = feature_path.split('.')
            obj = self.config
            
            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return False
            
            return bool(obj) if not callable(obj) else True
            
        except Exception:
            return False
    
    def get_feature_config(self, feature_name: str) -> Any:
        """Get configuration for a specific feature."""
        try:
            return getattr(self.config, feature_name)
        except AttributeError:
            self.logger.warning(f"Feature configuration not found: {feature_name}")
            return None
    
    def create_directories(self):
        """Create necessary directories based on configuration."""
        directories_to_create = []
        
        # Samples directory
        if self.config.voice_management.auto_create_directory:
            directories_to_create.append(self.config.voice_management.samples_directory)
        
        # Output directory
        if self.config.output_management.auto_create_directory:
            directories_to_create.append(self.config.output_management.output_directory)
        
        # Create directories
        for directory in directories_to_create:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {directory}")
            except Exception as e:
                self.logger.error(f"Failed to create directory {directory}: {e}")
    
    def get_deployment_config(self, environment: str = 'production') -> Dict[str, Any]:
        """Get deployment-specific configuration."""
        if not self.config_path or not os.path.exists(self.config_path):
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            deployment_config = config_data.get('deployment', {})
            return deployment_config.get(environment, {})
            
        except Exception as e:
            self.logger.error(f"Error loading deployment configuration: {e}")
            return {}
    
    def reload_config(self):
        """Reload configuration from file."""
        self.logger.info("Reloading configuration...")
        self.config = self._load_config()
        self._apply_environment_overrides()
        self._validate_config()
        self.logger.info("Configuration reloaded successfully")


# Global configuration manager instance
_config_manager = None


def get_enhanced_config_manager(config_path: Optional[str] = None) -> EnhancedConfigManager:
    """Get the global enhanced configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = EnhancedConfigManager(config_path)
    
    return _config_manager


def get_enhanced_config() -> EnhancedWebUIConfig:
    """Get the enhanced WebUI configuration."""
    return get_enhanced_config_manager().get_config()