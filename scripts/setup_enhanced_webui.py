#!/usr/bin/env python3
"""
Setup script for Enhanced IndexTTS2 WebUI.
Automates installation, configuration, and deployment.
"""

import os
import sys
import subprocess
import shutil
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional


class EnhancedWebUISetup:
    """Setup manager for Enhanced WebUI."""
    
    def __init__(self, verbose: bool = False):
        """Initialize setup manager."""
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with level."""
        if level == "ERROR":
            self.errors.append(message)
            print(f"❌ ERROR: {message}")
        elif level == "WARNING":
            self.warnings.append(message)
            print(f"⚠️  WARNING: {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        else:
            if self.verbose or level == "INFO":
                print(f"ℹ️  {message}")
    
    def run_command(self, command: List[str], description: str = None) -> bool:
        """Run shell command and return success status."""
        if description:
            self.log(f"Running: {description}")
        
        if self.verbose:
            self.log(f"Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=not self.verbose,
                text=True,
                check=True
            )
            
            if description:
                self.log(f"Completed: {description}", "SUCCESS")
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed: {description or ' '.join(command)}"
            if e.stderr:
                error_msg += f" - {e.stderr}"
            self.log(error_msg, "ERROR")
            return False
        except FileNotFoundError:
            self.log(f"Command not found: {command[0]}", "ERROR")
            return False
    
    def check_python_version(self) -> bool:
        """Check Python version requirements."""
        self.log("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            self.log(f"Python 3.10+ required, found {version.major}.{version.minor}", "ERROR")
            return False
        
        self.log(f"Python {version.major}.{version.minor}.{version.micro} OK", "SUCCESS")
        return True
    
    def check_uv_installation(self) -> bool:
        """Check if UV package manager is installed."""
        self.log("Checking UV package manager...")
        
        if shutil.which("uv"):
            self.log("UV package manager found", "SUCCESS")
            return True
        
        self.log("UV package manager not found", "WARNING")
        return False
    
    def install_uv(self) -> bool:
        """Install UV package manager."""
        self.log("Installing UV package manager...")
        
        return self.run_command(
            [sys.executable, "-m", "pip", "install", "-U", "uv"],
            "Installing UV package manager"
        )
    
    def install_dependencies(self, extras: List[str] = None) -> bool:
        """Install project dependencies."""
        self.log("Installing project dependencies...")
        
        if not extras:
            extras = ["webui", "audio", "performance"]
        
        # Check if uv.lock exists
        if not (self.project_root / "uv.lock").exists():
            self.log("uv.lock not found, running uv sync to create it")
        
        # Install with extras
        extra_args = []
        for extra in extras:
            extra_args.extend(["--extra", extra])
        
        return self.run_command(
            ["uv", "sync"] + extra_args,
            f"Installing dependencies with extras: {', '.join(extras)}"
        )
    
    def create_directories(self) -> bool:
        """Create required directories."""
        self.log("Creating required directories...")
        
        directories = [
            "samples",
            "outputs", 
            "logs",
            "prompts",
            "config"
        ]
        
        success = True
        for directory in directories:
            dir_path = self.project_root / directory
            try:
                dir_path.mkdir(exist_ok=True)
                self.log(f"Created directory: {directory}")
            except Exception as e:
                self.log(f"Failed to create directory {directory}: {e}", "ERROR")
                success = False
        
        return success
    
    def setup_configuration(self, config_template: str = None) -> bool:
        """Setup configuration files."""
        self.log("Setting up configuration...")
        
        config_dir = self.project_root / "config"
        
        # Copy default configuration if it doesn't exist
        default_config = config_dir / "enhanced_webui_config.yaml"
        user_config = config_dir / "user_config.yaml"
        
        if not user_config.exists() and default_config.exists():
            try:
                shutil.copy2(default_config, user_config)
                self.log("Created user configuration file", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to create user config: {e}", "ERROR")
                return False
        
        # Validate configuration
        if user_config.exists():
            try:
                with open(user_config, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                if config:
                    self.log("Configuration file validated", "SUCCESS")
                else:
                    self.log("Configuration file is empty", "WARNING")
                
            except Exception as e:
                self.log(f"Configuration validation failed: {e}", "ERROR")
                return False
        
        return True
    
    def download_models(self, method: str = "huggingface") -> bool:
        """Download model files."""
        self.log(f"Downloading models using {method}...")
        
        checkpoints_dir = self.project_root / "checkpoints"
        
        # Check if models already exist
        if (checkpoints_dir / "config.yaml").exists():
            self.log("Models already exist, skipping download")
            return True
        
        if method == "huggingface":
            # Install huggingface_hub if needed
            install_success = self.run_command(
                ["uv", "tool", "install", "huggingface_hub[cli]"],
                "Installing HuggingFace CLI"
            )
            
            if install_success:
                return self.run_command(
                    ["hf", "download", "IndexTeam/IndexTTS-2", "--local-dir", "checkpoints"],
                    "Downloading models from HuggingFace"
                )
        
        elif method == "modelscope":
            # Install modelscope if needed
            install_success = self.run_command(
                ["uv", "tool", "install", "modelscope"],
                "Installing ModelScope CLI"
            )
            
            if install_success:
                return self.run_command(
                    ["modelscope", "download", "--model", "IndexTeam/IndexTTS-2", "--local_dir", "checkpoints"],
                    "Downloading models from ModelScope"
                )
        
        self.log(f"Unknown download method: {method}", "ERROR")
        return False
    
    def run_tests(self, test_type: str = "smoke") -> bool:
        """Run tests to verify installation."""
        self.log(f"Running {test_type} tests...")
        
        test_script = self.project_root / "tests" / "test_runner.py"
        if not test_script.exists():
            self.log("Test runner not found, skipping tests", "WARNING")
            return True
        
        return self.run_command(
            ["uv", "run", "python", "-m", "pytest", str(test_script), "--type", test_type],
            f"Running {test_type} tests"
        )
    
    def check_gpu_support(self) -> bool:
        """Check GPU support."""
        self.log("Checking GPU support...")
        
        gpu_check_script = self.project_root / "tools" / "gpu_check.py"
        if gpu_check_script.exists():
            return self.run_command(
                ["uv", "run", "python", str(gpu_check_script)],
                "Checking GPU support"
            )
        else:
            self.log("GPU check script not found", "WARNING")
            return True
    
    def create_sample_files(self) -> bool:
        """Create sample voice files if they don't exist."""
        self.log("Setting up sample files...")
        
        samples_dir = self.project_root / "samples"
        examples_dir = self.project_root / "examples"
        
        # Copy example files to samples if available
        if examples_dir.exists():
            example_files = list(examples_dir.glob("voice_*.wav"))
            
            if example_files:
                for example_file in example_files[:3]:  # Copy first 3 examples
                    sample_file = samples_dir / example_file.name
                    if not sample_file.exists():
                        try:
                            shutil.copy2(example_file, sample_file)
                            self.log(f"Copied sample: {example_file.name}")
                        except Exception as e:
                            self.log(f"Failed to copy {example_file.name}: {e}", "WARNING")
                
                self.log("Sample files setup completed", "SUCCESS")
            else:
                self.log("No example voice files found", "WARNING")
        else:
            self.log("Examples directory not found", "WARNING")
        
        return True
    
    def setup_environment_file(self) -> bool:
        """Create environment file template."""
        self.log("Creating environment file template...")
        
        env_file = self.project_root / ".env.example"
        
        env_content = """# Enhanced IndexTTS2 WebUI Environment Configuration
# Copy this file to .env and customize as needed

# File Processing
INDEXTTS_MAX_FILE_SIZE=100
INDEXTTS_SUPPORTED_FORMATS=txt,epub
INDEXTTS_DEFAULT_ENCODING=utf-8

# Directories
INDEXTTS_SAMPLES_DIR=samples
INDEXTTS_OUTPUT_DIR=outputs

# Audio Settings
INDEXTTS_DEFAULT_AUDIO_FORMAT=mp3
INDEXTTS_MP3_BITRATE=64

# Performance
INDEXTTS_MEMORY_WARNING_THRESHOLD=80
INDEXTTS_MEMORY_CRITICAL_THRESHOLD=90
INDEXTTS_ENABLE_PARALLEL=true

# Task Management
INDEXTTS_ENABLE_BACKGROUND_TASKS=true
INDEXTTS_MAX_QUEUE_SIZE=50
INDEXTTS_WORKER_THREADS=2

# Logging
INDEXTTS_LOG_LEVEL=INFO
INDEXTTS_LOG_FILE=logs/enhanced_webui.log

# Development (set to true for development)
INDEXTTS_DEBUG=false
INDEXTTS_MOCK_DEPENDENCIES=false
"""
        
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            self.log("Environment file template created", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to create environment file: {e}", "ERROR")
            return False
    
    def generate_report(self) -> str:
        """Generate setup report."""
        report_lines = [
            "=" * 60,
            "ENHANCED INDEXTTS2 WEBUI SETUP REPORT",
            "=" * 60,
            ""
        ]
        
        if not self.errors and not self.warnings:
            report_lines.extend([
                "✅ Setup completed successfully!",
                "",
                "Next steps:",
                "1. Review configuration in config/user_config.yaml",
                "2. Add voice samples to the samples/ directory",
                "3. Run the WebUI: uv run webui.py",
                ""
            ])
        else:
            if self.errors:
                report_lines.extend([
                    "❌ Setup completed with errors:",
                    ""
                ])
                for error in self.errors:
                    report_lines.append(f"  • {error}")
                report_lines.append("")
            
            if self.warnings:
                report_lines.extend([
                    "⚠️  Warnings:",
                    ""
                ])
                for warning in self.warnings:
                    report_lines.append(f"  • {warning}")
                report_lines.append("")
        
        report_lines.extend([
            "Configuration:",
            f"  • Project root: {self.project_root}",
            f"  • Python version: {sys.version.split()[0]}",
            f"  • UV available: {'Yes' if shutil.which('uv') else 'No'}",
            "",
            "For help and documentation:",
            "  • Deployment Guide: DEPLOYMENT_GUIDE.md",
            "  • Configuration: config/enhanced_webui_config.yaml",
            "  • Logs: logs/enhanced_webui.log",
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def full_setup(self, 
                   install_deps: bool = True,
                   download_models: bool = True,
                   model_source: str = "huggingface",
                   run_tests: bool = True,
                   extras: List[str] = None) -> bool:
        """Run full setup process."""
        
        self.log("Starting Enhanced IndexTTS2 WebUI setup...", "INFO")
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Checking UV installation", self.check_uv_installation),
        ]
        
        # Install UV if needed
        if not shutil.which("uv"):
            steps.append(("Installing UV", self.install_uv))
        
        if install_deps:
            steps.append(("Installing dependencies", lambda: self.install_dependencies(extras)))
        
        steps.extend([
            ("Creating directories", self.create_directories),
            ("Setting up configuration", self.setup_configuration),
            ("Creating sample files", self.create_sample_files),
            ("Setting up environment file", self.setup_environment_file),
        ])
        
        if download_models:
            steps.append(("Downloading models", lambda: self.download_models(model_source)))
        
        steps.extend([
            ("Checking GPU support", self.check_gpu_support),
        ])
        
        if run_tests:
            steps.append(("Running tests", lambda: self.run_tests("smoke")))
        
        # Execute all steps
        success = True
        for step_name, step_func in steps:
            self.log(f"\n--- {step_name} ---")
            if not step_func():
                success = False
                if "Python version" in step_name or "Installing UV" in step_name:
                    # Critical failures
                    break
        
        # Generate and display report
        report = self.generate_report()
        print("\n" + report)
        
        return success and not self.errors


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Enhanced IndexTTS2 WebUI Setup")
    
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--no-models", action="store_true", help="Skip model download")
    parser.add_argument("--no-tests", action="store_true", help="Skip test execution")
    parser.add_argument("--model-source", choices=["huggingface", "modelscope"], 
                       default="huggingface", help="Model download source")
    parser.add_argument("--extras", nargs="*", default=["webui", "audio", "performance"],
                       help="Extra dependencies to install")
    
    args = parser.parse_args()
    
    setup = EnhancedWebUISetup(verbose=args.verbose)
    
    success = setup.full_setup(
        install_deps=not args.no_deps,
        download_models=not args.no_models,
        model_source=args.model_source,
        run_tests=not args.no_tests,
        extras=args.extras
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()