"""
Graceful degradation manager for handling missing optional dependencies.
Provides fallback functionality when optional features are not available.
"""

import logging
import importlib
from typing import Dict, Any, Optional, Callable, List
from functools import wraps

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages optional dependencies and provides graceful degradation."""
    
    def __init__(self):
        """Initialize dependency manager."""
        self.available_dependencies = {}
        self.missing_dependencies = {}
        self.fallback_handlers = {}
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check availability of optional dependencies."""
        # Core dependencies (should always be available)
        core_deps = {
            'yaml': 'PyYAML',
            'json': 'json (built-in)',
            'os': 'os (built-in)',
            'pathlib': 'pathlib (built-in)'
        }
        
        # Optional dependencies for enhanced features
        optional_deps = {
            'ebooklib': 'ebooklib (for EPUB processing)',
            'chardet': 'chardet (for encoding detection)',
            'librosa': 'librosa (for audio analysis)',
            'soundfile': 'soundfile (for audio I/O)',
            'pydub': 'pydub (for audio format conversion)',
            'mutagen': 'mutagen (for audio metadata)',
            'gradio': 'gradio (for web UI)',
            'psutil': 'psutil (for system monitoring)',
            'concurrent.futures': 'concurrent.futures (for parallel processing)',
            'threading': 'threading (built-in)',
            'queue': 'queue (built-in)'
        }
        
        # Check core dependencies
        for dep_name, description in core_deps.items():
            if self._check_import(dep_name):
                self.available_dependencies[dep_name] = description
            else:
                logger.error(f"Core dependency missing: {description}")
                self.missing_dependencies[dep_name] = description
        
        # Check optional dependencies
        for dep_name, description in optional_deps.items():
            if self._check_import(dep_name):
                self.available_dependencies[dep_name] = description
                logger.debug(f"Optional dependency available: {description}")
            else:
                logger.info(f"Optional dependency missing: {description}")
                self.missing_dependencies[dep_name] = description
    
    def _check_import(self, module_name: str) -> bool:
        """Check if a module can be imported."""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
    
    def is_available(self, dependency: str) -> bool:
        """Check if a dependency is available."""
        return dependency in self.available_dependencies
    
    def require_dependency(self, dependency: str, feature_name: str = None) -> bool:
        """Require a dependency for a feature, with graceful degradation."""
        if self.is_available(dependency):
            return True
        
        feature_desc = f" for {feature_name}" if feature_name else ""
        logger.warning(f"Dependency '{dependency}' not available{feature_desc}")
        
        # Check if there's a fallback handler
        if dependency in self.fallback_handlers:
            logger.info(f"Using fallback for {dependency}")
            return False  # Indicate fallback should be used
        
        return False
    
    def register_fallback(self, dependency: str, fallback_handler: Callable):
        """Register a fallback handler for a missing dependency."""
        self.fallback_handlers[dependency] = fallback_handler
        logger.debug(f"Registered fallback for {dependency}")
    
    def get_fallback(self, dependency: str) -> Optional[Callable]:
        """Get fallback handler for a dependency."""
        return self.fallback_handlers.get(dependency)
    
    def get_available_features(self) -> Dict[str, bool]:
        """Get list of available features based on dependencies."""
        features = {
            'epub_processing': self.is_available('ebooklib'),
            'encoding_detection': self.is_available('chardet'),
            'audio_analysis': self.is_available('librosa'),
            'audio_conversion': self.is_available('pydub') or self.is_available('soundfile'),
            'metadata_editing': self.is_available('mutagen'),
            'web_ui': self.is_available('gradio'),
            'system_monitoring': self.is_available('psutil'),
            'parallel_processing': self.is_available('concurrent.futures'),
            'background_tasks': self.is_available('threading') and self.is_available('queue')
        }
        
        return features
    
    def get_degradation_report(self) -> Dict[str, Any]:
        """Get report on missing dependencies and degraded features."""
        available_features = self.get_available_features()
        
        degraded_features = []
        for feature, available in available_features.items():
            if not available:
                degraded_features.append(feature)
        
        return {
            'available_dependencies': list(self.available_dependencies.keys()),
            'missing_dependencies': list(self.missing_dependencies.keys()),
            'available_features': [f for f, available in available_features.items() if available],
            'degraded_features': degraded_features,
            'fallback_handlers': list(self.fallback_handlers.keys())
        }


# Global dependency manager instance
_dependency_manager = None


def get_dependency_manager() -> DependencyManager:
    """Get global dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


def require_dependency(dependency: str, feature_name: str = None) -> bool:
    """Require a dependency with graceful degradation."""
    return get_dependency_manager().require_dependency(dependency, feature_name)


def is_dependency_available(dependency: str) -> bool:
    """Check if a dependency is available."""
    return get_dependency_manager().is_available(dependency)


def graceful_import(module_name: str, fallback_value=None):
    """Decorator for graceful imports with fallback values."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if require_dependency(module_name, func.__name__):
                return func(*args, **kwargs)
            else:
                logger.warning(f"Using fallback for {func.__name__} due to missing {module_name}")
                return fallback_value
        return wrapper
    return decorator


# Fallback implementations for common missing dependencies

class FallbackEbookProcessor:
    """Fallback EPUB processor when ebooklib is not available."""
    
    @staticmethod
    def read_epub(file_path: str) -> str:
        """Fallback EPUB reading - just return error message."""
        logger.error("EPUB processing not available - ebooklib not installed")
        raise ImportError("EPUB processing requires ebooklib package")


class FallbackEncodingDetector:
    """Fallback encoding detector when chardet is not available."""
    
    @staticmethod
    def detect(data: bytes) -> Dict[str, Any]:
        """Fallback encoding detection - assume UTF-8."""
        logger.warning("Using UTF-8 fallback - chardet not available for encoding detection")
        return {'encoding': 'utf-8', 'confidence': 0.5}


class FallbackAudioProcessor:
    """Fallback audio processor when librosa/soundfile not available."""
    
    @staticmethod
    def get_duration(file_path: str) -> float:
        """Fallback duration calculation."""
        logger.warning("Audio analysis not available - returning default duration")
        return 10.0  # Default 10 seconds
    
    @staticmethod
    def convert_format(input_path: str, output_path: str, format: str):
        """Fallback format conversion."""
        logger.error("Audio format conversion not available - missing audio libraries")
        raise ImportError("Audio conversion requires librosa or pydub")


class FallbackSystemMonitor:
    """Fallback system monitor when psutil is not available."""
    
    @staticmethod
    def get_memory_info():
        """Fallback memory info."""
        logger.warning("System monitoring not available - using defaults")
        return type('MemoryInfo', (), {
            'total': 8 * 1024 * 1024 * 1024,  # 8GB default
            'available': 4 * 1024 * 1024 * 1024,  # 4GB available
            'percent': 50.0
        })()


def register_fallbacks():
    """Register fallback handlers for common missing dependencies."""
    manager = get_dependency_manager()
    
    # Register fallback handlers
    manager.register_fallback('ebooklib', FallbackEbookProcessor)
    manager.register_fallback('chardet', FallbackEncodingDetector)
    manager.register_fallback('librosa', FallbackAudioProcessor)
    manager.register_fallback('soundfile', FallbackAudioProcessor)
    manager.register_fallback('psutil', FallbackSystemMonitor)


def get_feature_availability() -> Dict[str, bool]:
    """Get availability of enhanced features."""
    return get_dependency_manager().get_available_features()


def check_critical_dependencies() -> List[str]:
    """Check critical dependencies and return list of missing ones."""
    manager = get_dependency_manager()
    critical_deps = ['yaml', 'json', 'os', 'pathlib']
    
    missing_critical = []
    for dep in critical_deps:
        if not manager.is_available(dep):
            missing_critical.append(dep)
    
    return missing_critical


def initialize_graceful_degradation():
    """Initialize graceful degradation system."""
    # Register fallback handlers
    register_fallbacks()
    
    # Check critical dependencies
    missing_critical = check_critical_dependencies()
    if missing_critical:
        logger.error(f"Critical dependencies missing: {missing_critical}")
        raise ImportError(f"Critical dependencies missing: {missing_critical}")
    
    # Log degradation report
    manager = get_dependency_manager()
    report = manager.get_degradation_report()
    
    if report['degraded_features']:
        logger.info(f"Features with graceful degradation: {report['degraded_features']}")
    
    if report['missing_dependencies']:
        logger.info(f"Optional dependencies not available: {report['missing_dependencies']}")
    
    logger.info("Graceful degradation system initialized")


# Decorator for optional feature functions
def optional_feature(dependency: str, feature_name: str = None):
    """Decorator for functions that use optional features."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if require_dependency(dependency, feature_name or func.__name__):
                return func(*args, **kwargs)
            else:
                # Try to use fallback
                manager = get_dependency_manager()
                fallback = manager.get_fallback(dependency)
                if fallback:
                    logger.info(f"Using fallback for {func.__name__}")
                    return fallback(*args, **kwargs)
                else:
                    logger.warning(f"Feature {func.__name__} not available - no fallback")
                    return None
        return wrapper
    return decorator


# Initialize on import
try:
    initialize_graceful_degradation()
except Exception as e:
    logger.error(f"Failed to initialize graceful degradation: {e}")
    # Continue anyway - some functionality may still work