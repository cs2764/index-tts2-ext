"""
Environment configuration manager for enhanced WebUI features.
Supports environment variables and graceful degradation.
"""

import os
import yaml
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Environment-aware configuration manager."""
    
    def __init__(self, config_file: str = None):
        """Initialize environment configuration."""
        self.config_file = config_file or "config/enhanced_webui_config.yaml"
        self.config = {}
        self.env_prefix = "INDEXTTS_"
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Load base configuration from file
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                self.config = {}
        else:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self.config = self._get_default_config()
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config file is not available."""
        return {
            'file_processing': {
                'max_file_size_mb': 100,
                'supported_formats': ['txt', 'epub'],
                'encoding': {
                    'default_encoding': 'utf-8',
                    'fallback_encodings': ['gbk', 'gb2312', 'utf-16']
                }
            },
            'audio_formats': {
                'default_format': 'mp3',
                'supported_formats': ['wav', 'mp3', 'm4b'],
                'mp3': {'default_bitrate': 64}
            },
            'voice_samples': {
                'samples_dir': 'samples',
                'supported_formats': ['wav', 'mp3']
            },
            'output_management': {
                'output_dir': 'outputs',
                'auto_save': {'enabled': True}
            },
            'task_management': {
                'enabled': True,
                'queue': {
                    'max_queue_size': 50,
                    'worker_threads': 2
                }
            },
            'performance': {
                'memory': {
                    'enabled': True,
                    'warning_threshold': 80,
                    'critical_threshold': 90
                }
            },
            'logging': {
                'level': 'INFO',
                'file_path': 'logs/enhanced_webui.log'
            }
        }
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            # File processing
            f'{self.env_prefix}MAX_FILE_SIZE': ('file_processing', 'max_file_size_mb', int),
            f'{self.env_prefix}SUPPORTED_FORMATS': ('file_processing', 'supported_formats', self._parse_list),
            f'{self.env_prefix}DEFAULT_ENCODING': ('file_processing', 'encoding', 'default_encoding', str),
            
            # Audio formats
            f'{self.env_prefix}DEFAULT_AUDIO_FORMAT': ('audio_formats', 'default_format', str),
            f'{self.env_prefix}MP3_BITRATE': ('audio_formats', 'mp3', 'default_bitrate', int),
            
            # Directories
            f'{self.env_prefix}SAMPLES_DIR': ('voice_samples', 'samples_dir', str),
            f'{self.env_prefix}OUTPUT_DIR': ('output_management', 'output_dir', str),
            
            # Task management
            f'{self.env_prefix}ENABLE_BACKGROUND_TASKS': ('task_management', 'enabled', self._parse_bool),
            f'{self.env_prefix}MAX_QUEUE_SIZE': ('task_management', 'queue', 'max_queue_size', int),
            f'{self.env_prefix}WORKER_THREADS': ('task_management', 'queue', 'worker_threads', int),
            
            # Performance
            f'{self.env_prefix}MEMORY_WARNING_THRESHOLD': ('performance', 'memory', 'warning_threshold', int),
            f'{self.env_prefix}MEMORY_CRITICAL_THRESHOLD': ('performance', 'memory', 'critical_threshold', int),
            f'{self.env_prefix}ENABLE_PARALLEL': ('performance', 'processing', 'enable_parallel', self._parse_bool),
            
            # Logging
            f'{self.env_prefix}LOG_LEVEL': ('logging', 'level', str),
            f'{self.env_prefix}LOG_FILE': ('logging', 'file_path', str),
            
            # Development
            f'{self.env_prefix}DEBUG': ('development', 'debug', self._parse_bool),
            f'{self.env_prefix}MOCK_DEPENDENCIES': ('development', 'mock_dependencies', self._parse_bool),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    self._set_nested_config(config_path, env_value)
                    logger.debug(f"Set config from {env_var}: {config_path}")
                except Exception as e:
                    logger.warning(f"Failed to set config from {env_var}: {e}")
    
    def _set_nested_config(self, path_tuple: tuple, value: str):
        """Set nested configuration value from environment variable."""
        *path, converter = path_tuple
        
        # Convert value using the specified converter
        if callable(converter):
            converted_value = converter(value)
        else:
            # converter is actually part of the path
            path.append(converter)
            converted_value = value
        
        # Navigate to the nested location
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[path[-1]] = converted_value
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse list value from string."""
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set final value
        current[keys[-1]] = value
    
    def get_file_processing_config(self) -> Dict[str, Any]:
        """Get file processing configuration."""
        return self.get('file_processing', {})
    
    def get_audio_formats_config(self) -> Dict[str, Any]:
        """Get audio formats configuration."""
        return self.get('audio_formats', {})
    
    def get_voice_samples_config(self) -> Dict[str, Any]:
        """Get voice samples configuration."""
        return self.get('voice_samples', {})
    
    def get_output_management_config(self) -> Dict[str, Any]:
        """Get output management configuration."""
        return self.get('output_management', {})
    
    def get_task_management_config(self) -> Dict[str, Any]:
        """Get task management configuration."""
        return self.get('task_management', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get('performance', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature_mappings = {
            'background_tasks': 'task_management.enabled',
            'chapter_parsing': 'chapter_parsing.enabled',
            'memory_optimization': 'performance.memory.enabled',
            'auto_save': 'output_management.auto_save.enabled',
            'parallel_processing': 'performance.processing.enable_parallel',
            'caching': 'performance.processing.enable_caching',
            'responsive_ui': 'webui.interface.responsive',
            'accessibility': 'webui.interface.accessibility'
        }
        
        config_path = feature_mappings.get(feature)
        if config_path:
            return self.get(config_path, True)  # Default to enabled
        
        return False
    
    def get_directory_path(self, dir_type: str) -> str:
        """Get directory path with environment variable support."""
        dir_mappings = {
            'samples': 'voice_samples.samples_dir',
            'output': 'output_management.output_dir',
            'logs': 'logging.file_path',
            'test_data': 'development.test_data_dir'
        }
        
        config_path = dir_mappings.get(dir_type)
        if config_path:
            path = self.get(config_path, f'{dir_type}s')  # Default to plural
            
            # Handle log file path specially
            if dir_type == 'logs' and '/' in path:
                return os.path.dirname(path)
            
            return path
        
        return f'{dir_type}s'  # Default fallback
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.get_directory_path('samples'),
            self.get_directory_path('output'),
            self.get_directory_path('logs')
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    logger.info(f"Created directory: {directory}")
                except Exception as e:
                    logger.warning(f"Failed to create directory {directory}: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required sections
        required_sections = ['file_processing', 'audio_formats', 'task_management']
        for section in required_sections:
            if section not in self.config:
                issues.append(f"Missing required configuration section: {section}")
        
        # Validate numeric ranges
        numeric_validations = [
            ('file_processing.max_file_size_mb', 0, 1000),
            ('performance.memory.warning_threshold', 0, 100),
            ('performance.memory.critical_threshold', 0, 100),
            ('task_management.queue.max_queue_size', 1, 1000),
            ('task_management.queue.worker_threads', 1, 16)
        ]
        
        for config_path, min_val, max_val in numeric_validations:
            value = self.get(config_path)
            if value is not None and not (min_val <= value <= max_val):
                issues.append(f"Config {config_path} value {value} not in range [{min_val}, {max_val}]")
        
        # Validate directory paths
        critical_dirs = ['samples', 'output']
        for dir_type in critical_dirs:
            dir_path = self.get_directory_path(dir_type)
            if not dir_path:
                issues.append(f"Missing {dir_type} directory configuration")
        
        return issues
    
    def get_graceful_degradation_config(self) -> Dict[str, Any]:
        """Get configuration for graceful degradation when dependencies are missing."""
        return {
            'fallback_audio_format': 'wav',  # If MP3/M4B encoding fails
            'disable_chapter_parsing': not self.is_feature_enabled('chapter_parsing'),
            'disable_background_tasks': not self.is_feature_enabled('background_tasks'),
            'simple_ui_mode': not self.is_feature_enabled('responsive_ui'),
            'disable_performance_optimization': not self.is_feature_enabled('memory_optimization'),
            'mock_missing_dependencies': self.get('development.mock_dependencies', False)
        }
    
    def reload(self):
        """Reload configuration from file and environment."""
        self._load_config()
        logger.info("Configuration reloaded")


# Global configuration instance
_config_instance = None


def get_config() -> EnvironmentConfig:
    """Get global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance


def reload_config():
    """Reload global configuration."""
    global _config_instance
    if _config_instance:
        _config_instance.reload()
    else:
        _config_instance = EnvironmentConfig()


# Convenience functions
def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled."""
    return get_config().is_feature_enabled(feature)


def get_directory_path(dir_type: str) -> str:
    """Get directory path."""
    return get_config().get_directory_path(dir_type)


def ensure_directories():
    """Ensure required directories exist."""
    get_config().ensure_directories()