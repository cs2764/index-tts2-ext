#!/usr/bin/env python3
"""
Deployment script for Enhanced IndexTTS2 WebUI.
Handles setup, configuration validation, and deployment preparation.
"""

import os
import sys
import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to the path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


class EnhancedWebUIDeployer:
    """Deployment manager for Enhanced WebUI."""
    
    def __init__(self, environment: str = 'production'):
        """Initialize the deployer."""
        self.environment = environment
        self.project_root = project_root
        self.logger = self._setup_logging()
        
        # Deployment paths
        self.config_dir = self.project_root / 'config'
        self.scripts_dir = self.project_root / 'scripts'
        self.requirements_file = self.project_root / 'pyproject.toml'
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for deployment."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('deployment.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def validate_environment(self) -> bool:
        """Validate the deployment environment."""
        self.logger.info(f"Validating {self.environment} environment...")
        
        validation_checks = [
            self._check_python_version,
            self._check_required_files,
            self._check_dependencies,
            self._check_configuration,
            self._check_directories,
            self._check_permissions
        ]
        
        all_passed = True
        for check in validation_checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                self.logger.error(f"Validation check failed: {e}")
                all_passed = False
        
        if all_passed:
            self.logger.info("✅ Environment validation passed")
        else:
            self.logger.error("❌ Environment validation failed")
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version compatibility."""
        min_version = (3, 10)
        current_version = sys.version_info[:2]
        
        if current_version >= min_version:
            self.logger.info(f"✅ Python version: {'.'.join(map(str, current_version))}")
            return True
        else:
            self.logger.error(f"❌ Python version {'.'.join(map(str, current_version))} < {'.'.join(map(str, min_version))}")
            return False
    
    def _check_required_files(self) -> bool:
        """Check for required files."""
        required_files = [
            'webui.py',
            'pyproject.toml',
            'config/enhanced_webui_config.yaml',
            'indextts/__init__.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.logger.error(f"❌ Missing required files: {missing_files}")
            return False
        else:
            self.logger.info("✅ All required files present")
            return True
    
    def _check_dependencies(self) -> bool:
        """Check for required dependencies."""
        try:
            # Check if uv is available
            result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"✅ UV package manager: {result.stdout.strip()}")
            else:
                self.logger.warning("⚠️ UV package manager not found, falling back to pip")
            
            # Check critical dependencies
            critical_deps = ['gradio', 'torch', 'yaml']
            missing_deps = []
            
            for dep in critical_deps:
                try:
                    __import__(dep)
                    self.logger.info(f"✅ Dependency available: {dep}")
                except ImportError:
                    missing_deps.append(dep)
                    self.logger.error(f"❌ Missing dependency: {dep}")
            
            return len(missing_deps) == 0
            
        except Exception as e:
            self.logger.error(f"❌ Error checking dependencies: {e}")
            return False
    
    def _check_configuration(self) -> bool:
        """Check configuration validity."""
        try:
            from indextts.config.enhanced_config_manager import EnhancedConfigManager
            
            config_manager = EnhancedConfigManager()
            config = config_manager.get_config()
            
            if config.enabled:
                self.logger.info("✅ Enhanced features configuration loaded")
                
                # Check deployment-specific config
                deployment_config = config_manager.get_deployment_config(self.environment)
                if deployment_config:
                    self.logger.info(f"✅ {self.environment} deployment configuration loaded")
                else:
                    self.logger.warning(f"⚠️ No specific configuration for {self.environment} environment")
                
                return True
            else:
                self.logger.warning("⚠️ Enhanced features are disabled in configuration")
                return True  # Not an error, just disabled
                
        except Exception as e:
            self.logger.error(f"❌ Configuration validation failed: {e}")
            return False
    
    def _check_directories(self) -> bool:
        """Check and create necessary directories."""
        try:
            from indextts.config.enhanced_config_manager import get_enhanced_config
            
            config = get_enhanced_config()
            
            # Directories to check/create
            directories = [
                config.voice_management.samples_directory,
                config.output_management.output_directory,
                'logs',
                'temp'
            ]
            
            for directory in directories:
                dir_path = Path(directory)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"✅ Created directory: {directory}")
                else:
                    self.logger.info(f"✅ Directory exists: {directory}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Directory check failed: {e}")
            return False
    
    def _check_permissions(self) -> bool:
        """Check file and directory permissions."""
        try:
            # Check write permissions for key directories
            test_dirs = ['logs', 'temp']
            
            for test_dir in test_dirs:
                dir_path = Path(test_dir)
                if dir_path.exists():
                    # Try to create a test file
                    test_file = dir_path / 'permission_test.tmp'
                    try:
                        test_file.write_text('test')
                        test_file.unlink()
                        self.logger.info(f"✅ Write permission: {test_dir}")
                    except Exception:
                        self.logger.error(f"❌ No write permission: {test_dir}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Permission check failed: {e}")
            return False
    
    def install_dependencies(self, force: bool = False) -> bool:
        """Install required dependencies."""
        self.logger.info("Installing dependencies...")
        
        try:
            # Try UV first, fall back to pip
            commands_to_try = [
                ['uv', 'sync', '--all-extras'],
                ['pip', 'install', '-e', '.']
            ]
            
            for cmd in commands_to_try:
                try:
                    self.logger.info(f"Running: {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout
                    )
                    
                    if result.returncode == 0:
                        self.logger.info("✅ Dependencies installed successfully")
                        return True
                    else:
                        self.logger.warning(f"Command failed: {result.stderr}")
                        
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    self.logger.warning(f"Command not available or timed out: {e}")
                    continue
            
            self.logger.error("❌ Failed to install dependencies with any method")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error installing dependencies: {e}")
            return False
    
    def setup_configuration(self) -> bool:
        """Set up configuration for deployment."""
        self.logger.info(f"Setting up configuration for {self.environment}...")
        
        try:
            # Copy default config if it doesn't exist
            config_file = self.config_dir / 'enhanced_webui_config.yaml'
            if not config_file.exists():
                self.logger.error("❌ Configuration file not found")
                return False
            
            # Validate configuration
            from indextts.config.enhanced_config_manager import EnhancedConfigManager
            
            config_manager = EnhancedConfigManager(str(config_file))
            config = config_manager.get_config()
            
            # Create necessary directories
            config_manager.create_directories()
            
            # Apply environment-specific settings
            deployment_config = config_manager.get_deployment_config(self.environment)
            
            if deployment_config:
                self.logger.info(f"✅ Applied {self.environment} configuration")
                
                # Set up logging if specified
                logging_config = deployment_config.get('logging', {})
                if logging_config.get('log_file'):
                    log_dir = Path(logging_config['log_file']).parent
                    log_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"✅ Created log directory: {log_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Configuration setup failed: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run tests to validate deployment."""
        self.logger.info("Running deployment tests...")
        
        try:
            # Run enhanced features tests
            test_command = [
                sys.executable, '-m', 'pytest',
                'tests/test_enhanced_features_comprehensive.py',
                '--tb=short',
                '-v'
            ]
            
            self.logger.info(f"Running: {' '.join(test_command)}")
            result = subprocess.run(
                test_command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info("✅ All tests passed")
                return True
            else:
                self.logger.error(f"❌ Tests failed:\n{result.stdout}\n{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Tests timed out")
            return False
        except FileNotFoundError:
            self.logger.warning("⚠️ pytest not available, skipping tests")
            return True  # Don't fail deployment if pytest is not available
        except Exception as e:
            self.logger.error(f"❌ Error running tests: {e}")
            return False
    
    def create_startup_script(self) -> bool:
        """Create startup script for the deployment."""
        self.logger.info("Creating startup script...")
        
        try:
            startup_script_content = f"""#!/bin/bash
# Enhanced IndexTTS2 WebUI Startup Script
# Environment: {self.environment}

set -e

# Change to project directory
cd "{self.project_root}"

# Set environment variables
export INDEXTTS_ENVIRONMENT="{self.environment}"
export PYTHONPATH="$PYTHONPATH:{self.project_root}"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated virtual environment"
fi

# Start the WebUI
echo "Starting Enhanced IndexTTS2 WebUI..."
python webui.py "$@"
"""
            
            startup_script_path = self.project_root / 'start_enhanced_webui.sh'
            startup_script_path.write_text(startup_script_content)
            startup_script_path.chmod(0o755)
            
            # Create Windows batch file
            batch_script_content = f"""@echo off
REM Enhanced IndexTTS2 WebUI Startup Script
REM Environment: {self.environment}

cd /d "{self.project_root}"

REM Set environment variables
set INDEXTTS_ENVIRONMENT={self.environment}
set PYTHONPATH=%PYTHONPATH%;{self.project_root}

REM Activate virtual environment if it exists
if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
    echo Activated virtual environment
)

REM Start the WebUI
echo Starting Enhanced IndexTTS2 WebUI...
python webui.py %*
"""
            
            batch_script_path = self.project_root / 'start_enhanced_webui.bat'
            batch_script_path.write_text(batch_script_content)
            
            self.logger.info("✅ Startup scripts created")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create startup script: {e}")
            return False
    
    def deploy(self, skip_tests: bool = False, skip_deps: bool = False) -> bool:
        """Run complete deployment process."""
        self.logger.info(f"Starting deployment for {self.environment} environment...")
        
        deployment_steps = [
            ("Environment Validation", self.validate_environment),
            ("Configuration Setup", self.setup_configuration),
            ("Startup Script Creation", self.create_startup_script)
        ]
        
        if not skip_deps:
            deployment_steps.insert(1, ("Dependency Installation", self.install_dependencies))
        
        if not skip_tests:
            deployment_steps.append(("Test Execution", self.run_tests))
        
        for step_name, step_function in deployment_steps:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Step: {step_name}")
            self.logger.info(f"{'='*60}")
            
            if not step_function():
                self.logger.error(f"❌ Deployment failed at step: {step_name}")
                return False
        
        self.logger.info(f"\n🎉 Deployment completed successfully for {self.environment} environment!")
        self.logger.info(f"You can start the Enhanced WebUI using:")
        self.logger.info(f"  Linux/Mac: ./start_enhanced_webui.sh")
        self.logger.info(f"  Windows:   start_enhanced_webui.bat")
        
        return True


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description='Deploy Enhanced IndexTTS2 WebUI')
    parser.add_argument(
        '--environment', '-e',
        choices=['development', 'production'],
        default='production',
        help='Deployment environment'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip running tests during deployment'
    )
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip dependency installation'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate environment, do not deploy'
    )
    
    args = parser.parse_args()
    
    deployer = EnhancedWebUIDeployer(args.environment)
    
    if args.validate_only:
        success = deployer.validate_environment()
    else:
        success = deployer.deploy(
            skip_tests=args.skip_tests,
            skip_deps=args.skip_deps
        )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()