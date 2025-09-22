#!/usr/bin/env python3
"""
Enhanced WebUI startup script with graceful degradation and configuration validation.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


def setup_logging(log_level: str = 'INFO'):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_environment():
    """Validate the environment before starting."""
    logger = logging.getLogger(__name__)
    
    # Check Python version
    min_version = (3, 10)
    if sys.version_info[:2] < min_version:
        logger.error(f"Python {'.'.join(map(str, min_version))} or higher is required")
        return False
    
    # Check for required files
    required_files = ['webui.py', 'pyproject.toml']
    for file_name in required_files:
        if not (project_root / file_name).exists():
            logger.error(f"Required file not found: {file_name}")
            return False
    
    logger.info("Environment validation passed")
    return True


def setup_enhanced_features():
    """Set up enhanced features with graceful degradation."""
    logger = logging.getLogger(__name__)
    
    try:
        # Import graceful degradation utilities
        from indextts.utils.graceful_degradation import ensure_graceful_startup
        
        # Check feature availability and log status
        feature_availability = ensure_graceful_startup()
        
        # Load configuration
        try:
            from indextts.config.enhanced_config_manager import get_enhanced_config_manager
            
            config_manager = get_enhanced_config_manager()
            config = config_manager.get_config()
            
            if config.enabled:
                logger.info("Enhanced features are enabled")
                
                # Create necessary directories
                config_manager.create_directories()
                
                return True
            else:
                logger.info("Enhanced features are disabled in configuration")
                return False
                
        except Exception as e:
            logger.warning(f"Could not load enhanced configuration: {e}")
            logger.info("Falling back to basic WebUI functionality")
            return False
            
    except ImportError as e:
        logger.warning(f"Enhanced features not available: {e}")
        logger.info("Starting with basic WebUI functionality")
        return False


def start_webui(args):
    """Start the WebUI with appropriate configuration."""
    logger = logging.getLogger(__name__)
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed")
        sys.exit(1)
    
    # Set up enhanced features
    enhanced_available = setup_enhanced_features()
    
    # Prepare WebUI arguments
    webui_args = []
    
    # Add server configuration
    if args.server_name:
        webui_args.extend(['--server-name', args.server_name])
    
    if args.server_port:
        webui_args.extend(['--server-port', str(args.server_port)])
    
    if args.share:
        webui_args.append('--share')
    
    # Add enhanced features flag
    if enhanced_available:
        webui_args.append('--enhanced-features')
    
    # Set environment variables
    os.environ['PYTHONPATH'] = f"{os.environ.get('PYTHONPATH', '')}:{project_root}"
    
    if args.environment:
        os.environ['INDEXTTS_ENVIRONMENT'] = args.environment
    
    # Import and start WebUI
    try:
        # Change to project directory
        os.chdir(project_root)
        
        # Import webui module
        import webui
        
        # Start the WebUI
        logger.info("Starting IndexTTS2 Enhanced WebUI...")
        
        # If webui has a main function that accepts arguments
        if hasattr(webui, 'main') and callable(webui.main):
            webui.main(webui_args)
        else:
            # Fallback to running webui directly
            import subprocess
            cmd = [sys.executable, 'webui.py'] + webui_args
            subprocess.run(cmd)
            
    except Exception as e:
        logger.error(f"Failed to start WebUI: {e}")
        sys.exit(1)


def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description='Start Enhanced IndexTTS2 WebUI')
    
    # Server configuration
    parser.add_argument(
        '--server-name', 
        default='127.0.0.1',
        help='Server hostname (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--server-port', 
        type=int, 
        default=7860,
        help='Server port (default: 7860)'
    )
    parser.add_argument(
        '--share', 
        action='store_true',
        help='Create public Gradio link'
    )
    
    # Environment configuration
    parser.add_argument(
        '--environment', 
        choices=['development', 'production'],
        default='production',
        help='Runtime environment (default: production)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    # Enhanced features
    parser.add_argument(
        '--disable-enhanced-features',
        action='store_true',
        help='Disable enhanced features and use basic WebUI'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate environment, do not start WebUI'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Disable enhanced features if requested
    if args.disable_enhanced_features:
        os.environ['INDEXTTS_ENABLE_ENHANCED_FEATURES'] = 'false'
    
    # Validation only mode
    if args.validate_only:
        logger.info("Running validation only...")
        if validate_environment():
            setup_enhanced_features()
            logger.info("✅ Validation completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Validation failed")
            sys.exit(1)
    
    # Start the WebUI
    try:
        start_webui(args)
    except KeyboardInterrupt:
        logger.info("WebUI stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()