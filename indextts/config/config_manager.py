"""
Configuration manager for loading and saving enhanced WebUI settings.
"""

import os
import json
import yaml
from typing import Optional, Dict, Any
from .enhanced_config import EnhancedWebUIConfig


class ConfigManager:
    """Manages loading and saving of enhanced WebUI configuration."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "enhanced_webui.yaml")
        self._ensure_config_dir()
    
    def load_config(self) -> EnhancedWebUIConfig:
        """
        Load configuration from file or create default if not exists.
        
        Returns:
            EnhancedWebUIConfig object
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
                return EnhancedWebUIConfig.from_dict(config_dict)
            except Exception as e:
                print(f"Error loading config file {self.config_file}: {e}")
                print("Using default configuration")
        
        # Return default configuration if file doesn't exist or loading failed
        return EnhancedWebUIConfig.default()
    
    def save_config(self, config: EnhancedWebUIConfig) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._ensure_config_dir()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config.to_dict(), f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config file {self.config_file}: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> EnhancedWebUIConfig:
        """
        Update specific configuration values.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            Updated configuration object
        """
        config = self.load_config()
        config_dict = config.to_dict()
        
        # Apply updates recursively
        self._update_dict_recursive(config_dict, updates)
        
        # Create new config from updated dictionary
        updated_config = EnhancedWebUIConfig.from_dict(config_dict)
        
        # Save updated configuration
        self.save_config(updated_config)
        
        return updated_config
    
    def reset_to_default(self) -> EnhancedWebUIConfig:
        """
        Reset configuration to default values.
        
        Returns:
            Default configuration object
        """
        default_config = EnhancedWebUIConfig.default()
        self.save_config(default_config)
        return default_config
    
    def get_config_path(self) -> str:
        """Get the path to the configuration file."""
        return self.config_file
    
    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return os.path.exists(self.config_file)
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
    
    def _update_dict_recursive(self, target: Dict[str, Any], updates: Dict[str, Any]):
        """Recursively update dictionary with new values."""
        for key, value in updates.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict_recursive(target[key], value)
            else:
                target[key] = value