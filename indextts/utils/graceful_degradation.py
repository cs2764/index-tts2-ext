"""
Graceful degradation utilities for enhanced WebUI features.
Ensures the system works even when optional components are unavailable.
"""

import logging
import functools
from typing import Any, Callable, Optional, Dict, Union


logger = logging.getLogger(__name__)


def graceful_import(module_name: str, fallback_value: Any = None, error_message: Optional[str] = None):
    """
    Decorator for graceful import handling.
    
    Args:
        module_name: Name of the module to import
        fallback_value: Value to return if import fails
        error_message: Custom error message to log
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ImportError as e:
                if error_message:
                    logger.warning(error_message)
                else:
                    logger.warning(f"Optional module '{module_name}' not available: {e}")
                return fallback_value
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return fallback_value
        return wrapper
    return decorator


def optional_feature(feature_name: str, fallback_value: Any = None):
    """
    Decorator for optional features that may not be available.
    
    Args:
        feature_name: Name of the feature for logging
        fallback_value: Value to return if feature is unavailable
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Optional feature '{feature_name}' unavailable: {e}")
                return fallback_value
        return wrapper
    return decorator


def safe_import(module_name: str, attribute: Optional[str] = None, fallback: Any = None):
    """
    Safely import a module or attribute with fallback.
    
    Args:
        module_name: Name of the module to import
        attribute: Specific attribute to import from the module
        fallback: Fallback value if import fails
    
    Returns:
        Imported module/attribute or fallback value
    """
    try:
        module = __import__(module_name, fromlist=[attribute] if attribute else [])
        if attribute:
            return getattr(module, attribute, fallback)
        return module
    except ImportError as e:
        logger.warning(f"Could not import {module_name}: {e}")
        return fallback
    except Exception as e:
        logger.error(f"Error importing {module_name}: {e}")
        return fallback


class FeatureAvailability:
    """Track availability of optional features."""
    
    def __init__(self):
        self._features = {}
        self._check_features()
    
    def _check_features(self):
        """Check availability of optional features."""
        # Enhanced UI components
        self._features['enhanced_ui'] = self._check_enhanced_ui()
        
        # File processing features
        self._features['file_preview'] = self._check_file_preview()
        self._features['epub_support'] = self._check_epub_support()
        self._features['encoding_detection'] = self._check_encoding_detection()
        
        # Chapter parsing features
        self._features['chapter_parsing'] = self._check_chapter_parsing()
        
        # Audio format features
        self._features['audio_formats'] = self._check_audio_formats()
        self._features['m4b_support'] = self._check_m4b_support()
        
        # Performance features
        self._features['performance_optimization'] = self._check_performance_optimization()
        self._features['memory_monitoring'] = self._check_memory_monitoring()
        
        # UI theme features
        self._features['ui_theming'] = self._check_ui_theming()
        
        # Task management features
        self._features['background_tasks'] = self._check_background_tasks()
    
    def _check_enhanced_ui(self) -> bool:
        """Check if enhanced UI components are available."""
        try:
            from indextts.enhanced_webui.enhanced_ui_components import EnhancedUIComponents
            return True
        except ImportError:
            return False
    
    def _check_file_preview(self) -> bool:
        """Check if file preview features are available."""
        try:
            from indextts.file_processing.file_preview import FilePreviewGenerator
            return True
        except ImportError:
            return False
    
    def _check_epub_support(self) -> bool:
        """Check if EPUB support is available."""
        try:
            import ebooklib
            return True
        except ImportError:
            return False
    
    def _check_encoding_detection(self) -> bool:
        """Check if encoding detection is available."""
        try:
            import chardet
            return True
        except ImportError:
            return False
    
    def _check_chapter_parsing(self) -> bool:
        """Check if chapter parsing is available."""
        try:
            from indextts.chapter_parsing.chapter_parser import SmartChapterParser
            return True
        except ImportError:
            return False
    
    def _check_audio_formats(self) -> bool:
        """Check if enhanced audio format support is available."""
        try:
            from indextts.audio_formats.audio_converter import AudioFormatConverter
            return True
        except ImportError:
            return False
    
    def _check_m4b_support(self) -> bool:
        """Check if M4B format support is available."""
        try:
            import ffmpeg
            return True
        except ImportError:
            return False
    
    def _check_performance_optimization(self) -> bool:
        """Check if performance optimization features are available."""
        try:
            from indextts.performance.preview_optimizer import PreviewOptimizer
            return True
        except ImportError:
            return False
    
    def _check_memory_monitoring(self) -> bool:
        """Check if memory monitoring is available."""
        try:
            import psutil
            return True
        except ImportError:
            return False
    
    def _check_ui_theming(self) -> bool:
        """Check if UI theming is available."""
        try:
            from indextts.enhanced_webui.ui_theme_manager import UIThemeManager
            return True
        except ImportError:
            return False
    
    def _check_background_tasks(self) -> bool:
        """Check if background task management is available."""
        try:
            from indextts.task_management.task_manager import TaskManager
            return True
        except ImportError:
            return False
    
    def is_available(self, feature_name: str) -> bool:
        """Check if a feature is available."""
        return self._features.get(feature_name, False)
    
    def get_available_features(self) -> Dict[str, bool]:
        """Get all available features."""
        return self._features.copy()
    
    def get_unavailable_features(self) -> list:
        """Get list of unavailable features."""
        return [name for name, available in self._features.items() if not available]
    
    def log_feature_status(self):
        """Log the status of all features."""
        logger.info("Enhanced WebUI Feature Availability:")
        for feature_name, available in self._features.items():
            status = "✅ Available" if available else "❌ Unavailable"
            logger.info(f"  {feature_name}: {status}")
        
        unavailable = self.get_unavailable_features()
        if unavailable:
            logger.warning(f"Unavailable features: {', '.join(unavailable)}")
            logger.info("The WebUI will work with reduced functionality. Install missing dependencies to enable all features.")


# Global feature availability instance
_feature_availability = None


def get_feature_availability() -> FeatureAvailability:
    """Get the global feature availability instance."""
    global _feature_availability
    if _feature_availability is None:
        _feature_availability = FeatureAvailability()
    return _feature_availability


class GracefulWebUIComponents:
    """WebUI components with graceful degradation."""
    
    def __init__(self):
        self.feature_availability = get_feature_availability()
        self.logger = logging.getLogger(__name__)
    
    @optional_feature("enhanced_ui_components", fallback_value=None)
    def create_enhanced_components(self, enhanced_webui):
        """Create enhanced UI components if available."""
        from indextts.enhanced_webui.enhanced_ui_components import EnhancedUIComponents
        return EnhancedUIComponents(enhanced_webui)
    
    @optional_feature("file_preview", fallback_value="")
    def generate_file_preview(self, file_path: str) -> str:
        """Generate file preview if available."""
        from indextts.file_processing.file_preview import FilePreviewGenerator
        
        generator = FilePreviewGenerator()
        preview = generator.generate_preview(file_path)
        return generator.format_preview_display(preview)
    
    @optional_feature("chapter_parsing", fallback_value=[])
    def parse_chapters(self, text: str) -> list:
        """Parse chapters if available."""
        from indextts.chapter_parsing.chapter_parser import SmartChapterParser
        
        parser = SmartChapterParser()
        return parser.parse(text)
    
    @optional_feature("ui_theming", fallback_value="")
    def get_theme_css(self) -> str:
        """Get theme CSS if available."""
        from indextts.enhanced_webui.ui_theme_manager import get_theme_manager
        
        theme_manager = get_theme_manager()
        return theme_manager.get_custom_css()
    
    @optional_feature("audio_conversion", fallback_value=None)
    def convert_audio_format(self, input_path: str, output_format: str) -> Optional[str]:
        """Convert audio format if available."""
        from indextts.audio_formats.audio_converter import AudioFormatConverter
        
        converter = AudioFormatConverter()
        return converter.convert_to_format(input_path, output_format)
    
    def create_fallback_components(self):
        """Create fallback components when enhanced features are unavailable."""
        import gradio as gr
        
        self.logger.info("Creating fallback UI components")
        
        # Basic file upload
        file_upload = gr.File(
            label="Upload File",
            file_types=[".txt"],
            type="filepath"
        )
        
        # Basic text input
        text_input = gr.Textbox(
            label="Text Input",
            lines=5,
            placeholder="Enter text for TTS generation..."
        )
        
        # Basic format selection
        format_dropdown = gr.Dropdown(
            choices=["WAV", "MP3"],
            value="WAV",
            label="Output Format"
        )
        
        # Basic generate button
        generate_button = gr.Button("Generate Audio", variant="primary")
        
        # Basic output
        audio_output = gr.Audio(label="Generated Audio")
        
        return {
            'file_upload': file_upload,
            'text_input': text_input,
            'format_dropdown': format_dropdown,
            'generate_button': generate_button,
            'audio_output': audio_output
        }
    
    def get_component_with_fallback(self, component_type: str, **kwargs):
        """Get a component with fallback to basic version."""
        if self.feature_availability.is_available('enhanced_ui'):
            try:
                # Try to create enhanced component
                return self._create_enhanced_component(component_type, **kwargs)
            except Exception as e:
                self.logger.warning(f"Failed to create enhanced {component_type}: {e}")
        
        # Fallback to basic component
        return self._create_basic_component(component_type, **kwargs)
    
    def _create_enhanced_component(self, component_type: str, **kwargs):
        """Create enhanced component."""
        # This would be implemented based on component type
        pass
    
    def _create_basic_component(self, component_type: str, **kwargs):
        """Create basic component."""
        import gradio as gr
        
        component_map = {
            'file_upload': gr.File,
            'textbox': gr.Textbox,
            'dropdown': gr.Dropdown,
            'button': gr.Button,
            'audio': gr.Audio,
            'html': gr.HTML
        }
        
        component_class = component_map.get(component_type, gr.HTML)
        return component_class(**kwargs)


def ensure_graceful_startup():
    """Ensure graceful startup with feature availability logging."""
    feature_availability = get_feature_availability()
    feature_availability.log_feature_status()
    
    # Log recommendations for missing features
    unavailable = feature_availability.get_unavailable_features()
    
    if 'epub_support' in unavailable:
        logger.info("Install 'ebooklib' for EPUB file support: pip install ebooklib")
    
    if 'encoding_detection' in unavailable:
        logger.info("Install 'chardet' for automatic encoding detection: pip install chardet")
    
    if 'memory_monitoring' in unavailable:
        logger.info("Install 'psutil' for memory monitoring: pip install psutil")
    
    if 'm4b_support' in unavailable:
        logger.info("Install 'ffmpeg-python' for M4B audiobook support: pip install ffmpeg-python")
    
    return feature_availability


# Graceful import decorators for specific modules
@graceful_import('ebooklib', fallback_value=None, error_message="EPUB support not available. Install ebooklib for EPUB file processing.")
def import_ebooklib():
    import ebooklib
    return ebooklib


@graceful_import('chardet', fallback_value=None, error_message="Encoding detection not available. Install chardet for automatic encoding detection.")
def import_chardet():
    import chardet
    return chardet


@graceful_import('psutil', fallback_value=None, error_message="Memory monitoring not available. Install psutil for performance monitoring.")
def import_psutil():
    import psutil
    return psutil


@graceful_import('ffmpeg', fallback_value=None, error_message="FFmpeg not available. Install ffmpeg-python for advanced audio format support.")
def import_ffmpeg():
    import ffmpeg
    return ffmpeg