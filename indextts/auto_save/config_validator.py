"""
Configuration validation and user input handling for auto-save functionality.
Implements requirements 1.3, 1.4, 1.6: validation, error handling, and user feedback.
"""

import os
import json
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from .config import AutoSaveConfig


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    
    is_valid: bool
    error_message: str = ""
    warning_message: str = ""
    corrected_value: Optional[Any] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class UserPreferences:
    """User preferences for auto-save configuration."""
    
    default_enabled: bool = True  # Enable incremental auto-save by default
    default_interval: int = 5
    remember_settings: bool = True
    show_performance_warnings: bool = True
    auto_adjust_for_performance: bool = True
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class AutoSaveConfigValidator:
    """
    Validates auto-save configuration and handles user input.
    Implements comprehensive validation with user feedback and persistence.
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        """
        Initialize configuration validator.
        
        Args:
            config_file_path: Optional path to configuration file for persistence
        """
        self.config_file_path = config_file_path or os.path.join(
            os.path.expanduser("~"), ".indextts", "auto_save_preferences.json"
        )
        
        # Load user preferences
        self.user_preferences = self._load_user_preferences()
        
        # Validation rules
        self.validation_rules = {
            'interval_range': (1, 10),
            'performance_warning_threshold': 2,
            'recommended_range': (3, 7),
            'max_file_size_mb': 1000,  # Maximum file size for auto-save
            'min_disk_space_mb': 100   # Minimum required disk space
        }
    
    def validate_auto_save_settings(self, enabled: bool, interval: int, 
                                  context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Comprehensive validation of auto-save settings.
        
        Args:
            enabled: Whether auto-save is enabled
            interval: Auto-save interval value
            context: Optional context information (file size, system info, etc.)
            
        Returns:
            ValidationResult with validation outcome and feedback
        """
        if not enabled:
            return ValidationResult(
                is_valid=True,
                warning_message="自动保存已禁用，只有在生成完全完成后才会保存最终音频文件"
            )
        
        # Validate interval type
        if not isinstance(interval, (int, float)):
            return ValidationResult(
                is_valid=False,
                error_message="自动保存间隔必须是数字",
                corrected_value=self.user_preferences.default_interval,
                suggestions=[
                    "请输入1-10之间的整数",
                    f"建议使用默认值: {self.user_preferences.default_interval}"
                ]
            )
        
        # Convert to integer
        interval = int(interval)
        
        # Validate interval range
        min_interval, max_interval = self.validation_rules['interval_range']
        if interval < min_interval or interval > max_interval:
            return ValidationResult(
                is_valid=False,
                error_message=f"自动保存间隔必须在{min_interval}-{max_interval}之间",
                corrected_value=max(min_interval, min(max_interval, interval)),
                suggestions=[
                    f"当前值 {interval} 超出有效范围",
                    f"推荐范围: {self.validation_rules['recommended_range'][0]}-{self.validation_rules['recommended_range'][1]}",
                    "较小值提供更好的保护但可能影响性能",
                    "较大值减少性能影响但保护程度较低"
                ]
            )
        
        # Performance warning for very frequent saves
        warning_msg = ""
        suggestions = []
        
        if interval <= self.validation_rules['performance_warning_threshold']:
            warning_msg = f"间隔设置为 {interval} 可能影响生成性能"
            suggestions.extend([
                "频繁保存会增加磁盘I/O操作",
                "建议在长文本生成时使用较小间隔",
                "短文本生成可以使用较大间隔以提高性能"
            ])
        
        # Context-based validation
        if context:
            context_warnings, context_suggestions = self._validate_context(interval, context)
            if context_warnings:
                warning_msg = f"{warning_msg}; {context_warnings}" if warning_msg else context_warnings
            suggestions.extend(context_suggestions)
        
        return ValidationResult(
            is_valid=True,
            warning_message=warning_msg,
            suggestions=suggestions
        )
    
    def _validate_context(self, interval: int, context: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Validate settings based on context information.
        
        Args:
            interval: Auto-save interval
            context: Context information
            
        Returns:
            Tuple of (warning_message, suggestions)
        """
        warnings = []
        suggestions = []
        
        # Check estimated file size
        estimated_size_mb = context.get('estimated_file_size_mb', 0)
        if estimated_size_mb > self.validation_rules['max_file_size_mb']:
            warnings.append("预计文件大小很大")
            suggestions.extend([
                "大文件建议使用较小的保存间隔",
                "考虑启用性能自适应调整"
            ])
        
        # Check available disk space
        available_space_mb = context.get('available_disk_space_mb', float('inf'))
        if available_space_mb < self.validation_rules['min_disk_space_mb']:
            warnings.append("磁盘空间不足")
            suggestions.extend([
                "建议清理磁盘空间",
                "考虑使用较大的保存间隔以减少临时文件"
            ])
        
        # Check text length
        text_length = context.get('text_length', 0)
        if text_length > 10000 and interval > 7:
            warnings.append("长文本使用较大间隔可能增加数据丢失风险")
            suggestions.append("长文本建议使用3-5的间隔值")
        elif text_length < 1000 and interval < 5:
            suggestions.append("短文本可以使用较大间隔以提高性能")
        
        # Check system performance
        system_load = context.get('system_load_percent', 0)
        if system_load > 80 and interval <= 3:
            warnings.append("系统负载较高")
            suggestions.extend([
                "高负载时建议使用较大间隔",
                "考虑启用性能自适应调整"
            ])
        
        return "; ".join(warnings), suggestions
    
    def get_recommended_settings(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get recommended auto-save settings based on context.
        
        Args:
            context: Optional context information
            
        Returns:
            Dictionary with recommended settings
        """
        # Start with user preferences
        recommended = {
            'enabled': self.user_preferences.default_enabled,
            'interval': self.user_preferences.default_interval,
            'reason': '基于用户偏好设置'
        }
        
        if not context:
            return recommended
        
        # Adjust based on context
        text_length = context.get('text_length', 0)
        system_load = context.get('system_load_percent', 0)
        available_space_mb = context.get('available_disk_space_mb', float('inf'))
        
        # Adjust interval based on text length
        if text_length > 20000:
            recommended['interval'] = 3
            recommended['reason'] = '长文本建议使用较小间隔以提供更好保护'
        elif text_length > 10000:
            recommended['interval'] = 4
            recommended['reason'] = '中等长度文本建议使用中等间隔'
        elif text_length < 1000:
            recommended['interval'] = 7
            recommended['reason'] = '短文本可以使用较大间隔以提高性能'
        
        # Adjust based on system performance
        if system_load > 80:
            recommended['interval'] = min(recommended['interval'] + 2, 8)
            recommended['reason'] += '；系统负载高，增加间隔以减少性能影响'
        
        # Adjust based on disk space
        if available_space_mb < 500:
            recommended['interval'] = min(recommended['interval'] + 1, 9)
            recommended['reason'] += '；磁盘空间有限，适当增加间隔'
        
        return recommended
    
    def handle_invalid_input(self, invalid_value: Any, validation_result: ValidationResult) -> Dict[str, Any]:
        """
        Handle invalid user input with corrective feedback.
        
        Args:
            invalid_value: The invalid input value
            validation_result: Validation result with error details
            
        Returns:
            Dictionary with corrective action information
        """
        return {
            'original_value': invalid_value,
            'corrected_value': validation_result.corrected_value,
            'error_message': validation_result.error_message,
            'user_action_required': True,
            'auto_correction_available': validation_result.corrected_value is not None,
            'suggestions': validation_result.suggestions,
            'help_text': self._get_help_text_for_error(validation_result.error_message)
        }
    
    def _get_help_text_for_error(self, error_message: str) -> str:
        """Get contextual help text for specific error messages."""
        help_texts = {
            '必须是数字': '自动保存间隔应该是1到10之间的整数。例如：5表示每生成5个段落后保存一次。',
            '必须在1-10之间': '有效的保存间隔范围是1-10。较小的值提供更频繁的保存，较大的值减少性能影响。',
            '影响生成性能': '频繁保存（间隔1-2）会增加磁盘操作，可能降低生成速度。建议根据文本长度选择合适的间隔。'
        }
        
        for key, help_text in help_texts.items():
            if key in error_message:
                return help_text
        
        return '请检查输入值是否符合要求。如需帮助，请参考用户手册。'
    
    def save_user_preferences(self, enabled: bool, interval: int) -> bool:
        """
        Save user preferences for future use.
        
        Args:
            enabled: Auto-save enabled setting
            interval: Auto-save interval setting
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.user_preferences.remember_settings:
            return True  # User doesn't want to save preferences
        
        try:
            # Update preferences
            self.user_preferences.default_enabled = enabled
            self.user_preferences.default_interval = interval
            self.user_preferences.last_updated = datetime.now()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            
            # Save to file
            preferences_dict = asdict(self.user_preferences)
            # Convert datetime to string for JSON serialization
            preferences_dict['last_updated'] = self.user_preferences.last_updated.isoformat()
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(preferences_dict, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Could not save auto-save preferences: {e}")
            return False
    
    def _load_user_preferences(self) -> UserPreferences:
        """Load user preferences from file."""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert datetime string back to datetime object
                if 'last_updated' in data and data['last_updated']:
                    data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                
                return UserPreferences(**data)
        except Exception as e:
            print(f"Warning: Could not load auto-save preferences: {e}")
        
        # Return default preferences if loading fails
        return UserPreferences()
    
    def get_default_values(self) -> Dict[str, Any]:
        """
        Get default values for auto-save configuration.
        
        Returns:
            Dictionary with default configuration values
        """
        return {
            'enabled': self.user_preferences.default_enabled,
            'interval': self.user_preferences.default_interval,
            'source': 'user_preferences' if os.path.exists(self.config_file_path) else 'system_defaults'
        }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset configuration to system defaults.
        
        Returns:
            Dictionary with reset default values
        """
        system_defaults = {
            'enabled': True,
            'interval': 5,
            'source': 'system_defaults'
        }
        
        # Update user preferences to system defaults
        self.user_preferences.default_enabled = system_defaults['enabled']
        self.user_preferences.default_interval = system_defaults['interval']
        self.user_preferences.last_updated = datetime.now()
        
        # Save updated preferences
        self.save_user_preferences(system_defaults['enabled'], system_defaults['interval'])
        
        return system_defaults
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation rules and current settings.
        
        Returns:
            Dictionary with validation summary
        """
        return {
            'validation_rules': self.validation_rules,
            'user_preferences': asdict(self.user_preferences),
            'config_file_path': self.config_file_path,
            'config_file_exists': os.path.exists(self.config_file_path),
            'supported_range': f"{self.validation_rules['interval_range'][0]}-{self.validation_rules['interval_range'][1]}",
            'recommended_range': f"{self.validation_rules['recommended_range'][0]}-{self.validation_rules['recommended_range'][1]}"
        }


def create_config_validator(config_file_path: Optional[str] = None) -> AutoSaveConfigValidator:
    """
    Create and initialize a configuration validator.
    
    Args:
        config_file_path: Optional path to configuration file
        
    Returns:
        Initialized AutoSaveConfigValidator instance
    """
    return AutoSaveConfigValidator(config_file_path)


def validate_and_correct_settings(enabled: bool, interval: int, 
                                context: Optional[Dict[str, Any]] = None) -> Tuple[bool, int, ValidationResult]:
    """
    Convenience function to validate and auto-correct settings.
    
    Args:
        enabled: Auto-save enabled setting
        interval: Auto-save interval setting
        context: Optional context information
        
    Returns:
        Tuple of (corrected_enabled, corrected_interval, validation_result)
    """
    validator = create_config_validator()
    result = validator.validate_auto_save_settings(enabled, interval, context)
    
    corrected_enabled = enabled
    corrected_interval = interval
    
    if not result.is_valid and result.corrected_value is not None:
        corrected_interval = result.corrected_value
    
    return corrected_enabled, corrected_interval, result