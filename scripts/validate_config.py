#!/usr/bin/env python3
"""
Configuration validation script for Enhanced IndexTTS2 WebUI.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Add the project root to the path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


def validate_config(config_path: str) -> bool:
    """Validate configuration file."""
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Basic validation
        if 'enhanced_features' not in config_data:
            logger.error("Missing 'enhanced_features' section in configuration")
            return False
        
        enhanced_config = config_data['enhanced_features']
        
        # Validate enabled flag
        if 'enabled' in enhanced_config and not isinstance(enhanced_config['enabled'], bool):
            logger.error("enhanced_features.enabled must be a boolean")
            return False
        
        logger.info("✅ Configuration validation passed")
        return True
        
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return False


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Enhanced WebUI Configuration')
    parser.add_argument(
        'config_file',
        nargs='?',
        default='config/enhanced_webui_config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Validate configuration
    is_valid = validate_config(args.config_file)
    
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()