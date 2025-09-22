"""
Tests for UV installation validation after GitHub preparation cleanup.

This module specifically tests that the project can be properly installed
and run using UV package manager after cleanup operations.
"""

import pytest
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.validation_system import InstallationValidator


class TestUVInstallationValidation:
    """Test UV installation validation functionality."""
    
    @pytest.fixture
    def minimal_project(self):
        """Create minimal project structure for UV testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create pyproject.toml with minimal dependencies
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "indextts-test"
version = "1.0.0"
description = "Test project for UV installation"
authors = [{name = "Test Team", email = "test@example.com"}]
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0.0"
]

[project.scripts]
indextts-cli = "indextts.cli:main"
"""
        (project_path / 'pyproject.toml').write_text(pyproject_content)
        
        # Create package structure
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        
        # Create __init__.py
        (indextts_dir / '__init__.py').write_text('''
"""IndexTTS test package."""
__version__ = "1.0.0"
''')
        
        # Create CLI module
        (indextts_dir / 'cli.py').write_text('''
"""CLI interface for IndexTTS."""
import sys
import click

@click.command()
@click.option('--help', is_flag=True, help='Show help message')
def main(help):
    """IndexTTS CLI interface."""
    if help:
        click.echo("IndexTTS CLI Help")
        click.echo("Usage: indextts-cli [OPTIONS]")
        return 0
    
    click.echo("IndexTTS CLI - Hello World!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
''')
        
        # Create basic module
        (indextts_dir / 'core.py').write_text('''
"""Core IndexTTS functionality."""

def hello_world():
    """Return hello world message."""
    return "Hello from IndexTTS!"

class IndexTTS:
    """Main IndexTTS class."""
    
    def __init__(self):
        self.version = "1.0.0"
    
    def generate(self, text):
        """Generate speech from text."""
        return f"Generated speech for: {text}"
''')
        
        # Create README
        readme_content = """
# IndexTTS Test Project

Test project for UV installation validation.

## Installation

```bash
uv sync
```

## Usage

```bash
uv run indextts-cli --help
```
"""
        (project_path / 'README.md').write_text(readme_content)
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def realistic_project(self):
        """Create realistic project structure similar to actual IndexTTS."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create comprehensive pyproject.toml
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "indextts"
version = "2.0.0"
description = "IndexTTS2: Breakthrough text-to-speech system with emotional expression control"
authors = [
    {name = "IndexTeam", email = "team@index.com"}
]
license = {text = "MIT"}
readme = "README.md"
homepage = "https://github.com/IndexTeam/IndexTTS-2"
repository = "https://github.com/IndexTeam/IndexTTS-2"
keywords = ["tts", "speech-synthesis", "ai", "voice-cloning"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Multimedia :: Sound/Audio :: Speech",
    "Topic :: Scientific/Engineering :: Artificial Intelligence"
]

dependencies = [
    "torch>=2.0.0",
    "torchaudio>=2.0.0", 
    "numpy>=1.21.0",
    "librosa>=0.9.0",
    "scipy>=1.7.0",
    "transformers>=4.20.0",
    "safetensors>=0.3.0",
    "click>=8.0.0",
    "tqdm>=4.60.0",
    "pyyaml>=6.0",
    "jieba>=0.42.0",
    "g2p-en>=2.1.0",
    "sentencepiece>=0.1.95"
]

[project.optional-dependencies]
webui = [
    "gradio>=4.0.0",
    "matplotlib>=3.5.0"
]
deepspeed = [
    "deepspeed>=0.9.0"
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=5.0.0"
]
all = [
    "indextts[webui,deepspeed,dev]"
]

[project.scripts]
indextts = "indextts.cli:main"

[project.urls]
"Bug Reports" = "https://github.com/IndexTeam/IndexTTS-2/issues"
"Source" = "https://github.com/IndexTeam/IndexTTS-2"
"Documentation" = "https://github.com/IndexTeam/IndexTTS-2/docs"

[tool.hatch.version]
path = "indextts/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["indextts"]
"""
        (project_path / 'pyproject.toml').write_text(pyproject_content)
        
        # Create comprehensive package structure
        indextts_dir = project_path / 'indextts'
        indextts_dir.mkdir()
        
        # Create __init__.py with version
        (indextts_dir / '__init__.py').write_text('''
"""
IndexTTS2: Breakthrough text-to-speech system with emotional expression control.

This package provides zero-shot voice cloning with precise duration control
and emotional expression capabilities.
"""

__version__ = "2.0.0"
__author__ = "IndexTeam"
__email__ = "team@index.com"

from .core import IndexTTS2
from .cli import main as cli_main

__all__ = ["IndexTTS2", "cli_main"]
''')
        
        # Create CLI module
        (indextts_dir / 'cli.py').write_text('''
"""Command-line interface for IndexTTS2."""

import sys
import click
from pathlib import Path
from .core import IndexTTS2

@click.command()
@click.argument('text', required=False)
@click.option('-v', '--voice', type=click.Path(exists=True), 
              help='Path to reference voice file')
@click.option('--emotion', default='neutral', 
              help='Emotion for synthesis (happy, sad, angry, etc.)')
@click.option('--output', '-o', type=click.Path(), 
              help='Output audio file path')
@click.option('--help', is_flag=True, help='Show this help message')
def main(text, voice, emotion, output, help):
    """
    IndexTTS2 Command Line Interface.
    
    Generate speech from text using voice cloning and emotion control.
    
    Examples:
        indextts "Hello world" -v voice.wav -o output.wav
        indextts "Happy speech" --emotion happy -v voice.wav
    """
    if help or not text:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return 0
    
    try:
        # Initialize IndexTTS2
        tts = IndexTTS2()
        
        # Generate speech
        click.echo(f"Generating speech for: {text}")
        click.echo(f"Voice: {voice or 'default'}")
        click.echo(f"Emotion: {emotion}")
        
        result = tts.generate(text, voice_path=voice, emotion=emotion)
        
        if output:
            click.echo(f"Saving to: {output}")
        else:
            click.echo("Output saved to: generated_speech.wav")
        
        click.echo("Speech generation completed successfully!")
        return 0
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
''')
        
        # Create core module
        (indextts_dir / 'core.py').write_text('''
"""Core IndexTTS2 functionality."""

import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

class IndexTTS2:
    """
    IndexTTS2: Breakthrough text-to-speech system.
    
    Features:
    - Zero-shot voice cloning
    - Emotional expression control  
    - Precise duration control
    - Multilingual support (Chinese/English)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize IndexTTS2 model."""
        self.model_path = model_path or "checkpoints/"
        self.version = "2.0.0"
        logger.info(f"IndexTTS2 v{self.version} initialized")
    
    def generate(self, 
                text: str, 
                voice_path: Optional[Union[str, Path]] = None,
                emotion: str = "neutral",
                output_path: Optional[Union[str, Path]] = None) -> str:
        """
        Generate speech from text.
        
        Args:
            text: Input text to synthesize
            voice_path: Path to reference voice file
            emotion: Emotion for synthesis
            output_path: Output audio file path
            
        Returns:
            Path to generated audio file
        """
        logger.info(f"Generating speech: {text[:50]}...")
        logger.info(f"Voice: {voice_path}, Emotion: {emotion}")
        
        # Simulate speech generation
        output_file = output_path or "generated_speech.wav"
        
        # In real implementation, this would generate actual audio
        logger.info(f"Speech generated successfully: {output_file}")
        
        return str(output_file)
    
    def list_emotions(self) -> list:
        """List available emotions."""
        return [
            "neutral", "happy", "sad", "angry", 
            "surprised", "disgusted", "afraid", "calm"
        ]
''')
        
        # Create subpackages
        subpackages = ['gpt', 's2mel', 'vqvae', 'BigVGAN', 'utils']
        for subpkg in subpackages:
            subdir = indextts_dir / subpkg
            subdir.mkdir()
            (subdir / '__init__.py').write_text(f'"""{subpkg} module for IndexTTS2."""')
        
        # Create utils with actual functionality
        utils_dir = indextts_dir / 'utils'
        (utils_dir / 'audio.py').write_text('''
"""Audio processing utilities."""

def load_audio(path):
    """Load audio file."""
    return f"Loaded audio from {path}"

def save_audio(audio, path):
    """Save audio to file."""
    return f"Saved audio to {path}"
''')
        
        # Create webui entry point
        (project_path / 'webui.py').write_text('''
"""Web UI for IndexTTS2."""

import sys
from pathlib import Path

def main():
    """Launch IndexTTS2 web interface."""
    try:
        import gradio as gr
        from indextts.core import IndexTTS2
        
        tts = IndexTTS2()
        
        def generate_speech(text, emotion):
            """Generate speech via web interface."""
            if not text:
                return "Please enter text to synthesize"
            
            result = tts.generate(text, emotion=emotion)
            return f"Generated: {result}"
        
        # Create Gradio interface
        interface = gr.Interface(
            fn=generate_speech,
            inputs=[
                gr.Textbox(label="Text to synthesize"),
                gr.Dropdown(choices=tts.list_emotions(), label="Emotion", value="neutral")
            ],
            outputs=gr.Textbox(label="Result"),
            title="IndexTTS2 Web Interface",
            description="Generate speech with emotion control"
        )
        
        print("Starting IndexTTS2 Web UI...")
        interface.launch()
        
    except ImportError:
        print("Error: Gradio not installed. Install with: uv sync --extra webui")
        return 1
    except Exception as e:
        print(f"Error starting web UI: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
''')
        
        # Create comprehensive README
        readme_content = """
# IndexTTS2

IndexTTS2 is a breakthrough text-to-speech system that combines emotionally expressive speech synthesis with precise duration control in an autoregressive zero-shot architecture.

## Features

- **Zero-shot voice cloning**: Generate speech in any voice using just a short audio prompt
- **Emotional expression control**: Independent control over timbre and emotion
- **Duration control**: First autoregressive TTS model with precise synthesis duration control  
- **Multilingual support**: Chinese and English text synthesis
- **High-quality output**: 22kHz audio generation

## Installation

### Using UV (Recommended)

```bash
# Install UV package manager
pip install -U uv

# Install IndexTTS2 with all features
uv sync --all-extras

# Install specific features only
uv sync --extra webui --extra deepspeed
```

### Using pip

```bash
pip install -e .
pip install -e .[webui,deepspeed]
```

## Usage

### Command Line Interface

```bash
# Basic usage
uv run indextts "Hello world" -v examples/voice_01.wav

# With emotion control
uv run indextts "I'm so happy!" --emotion happy -v examples/voice_01.wav -o happy_speech.wav

# Show help
uv run indextts --help
```

### Web Interface

```bash
# Start web UI
uv run webui.py

# Or using Python
uv run python webui.py
```

### Python API

```python
from indextts import IndexTTS2

# Initialize model
tts = IndexTTS2()

# Generate speech
output = tts.generate(
    text="Hello, this is IndexTTS2!",
    voice_path="examples/voice_01.wav", 
    emotion="happy"
)
```

## Requirements

- Python 3.10+
- PyTorch 2.0+
- CUDA 12.0+ (for GPU acceleration)

## Model Download

```bash
# Via HuggingFace
uv tool install "huggingface_hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints

# Via ModelScope (China)
uv tool install "modelscope"
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

## Development

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black indextts/
uv run isort indextts/
```

---

# 中文文档

IndexTTS2 是一个突破性的文本转语音系统，结合了情感表达语音合成和精确时长控制的自回归零样本架构。

## 特性

- **零样本语音克隆**：仅使用短音频提示即可生成任何声音的语音
- **情感表达控制**：独立控制音色和情感
- **时长控制**：首个具有精确合成时长控制的自回归TTS模型
- **多语言支持**：中文和英文文本合成
- **高质量输出**：22kHz音频生成

## 安装

### 使用 UV（推荐）

```bash
# 安装 UV 包管理器
pip install -U uv

# 安装 IndexTTS2 及所有功能
uv sync --all-extras

# 仅安装特定功能
uv sync --extra webui --extra deepspeed
```

## 使用方法

### 命令行界面

```bash
# 基本用法
uv run indextts "你好世界" -v examples/voice_01.wav

# 情感控制
uv run indextts "我很开心！" --emotion happy -v examples/voice_01.wav -o happy_speech.wav
```

### 网页界面

```bash
# 启动网页界面
uv run webui.py
```

## 系统要求

- Python 3.10+
- PyTorch 2.0+
- CUDA 12.0+（GPU加速）
"""
        (project_path / 'README.md').write_text(readme_content, encoding='utf-8')
        
        # Create other necessary files
        (project_path / '.gitignore').write_text("""
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
outputs/
logs/
*.log
checkpoints/*.pth
checkpoints/*.pt
checkpoints/*.bin
!checkpoints/config.yaml
!checkpoints/README.md

# Temporary files
*.tmp
*.temp
debug_*.wav
test_output*.wav
""")
        
        yield project_path
        
        shutil.rmtree(temp_dir)
    
    def test_uv_availability_check(self):
        """Test checking if UV is available on the system."""
        validator = InstallationValidator(".")
        
        # This will test actual UV availability
        result = validator.validate_dependency_resolution()
        
        # Should either pass (if UV is available) or fail gracefully
        assert result.name == "dependency_resolution"
        assert isinstance(result.passed, bool)
        assert isinstance(result.message, str)
        assert 'details' in result.__dict__
    
    @patch('subprocess.run')
    def test_dependency_resolution_mock_success(self, mock_run, minimal_project):
        """Test dependency resolution with mocked successful UV."""
        # Mock successful UV lock command
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Dependencies resolved successfully",
            stderr=""
        )
        
        # Create uv.lock file
        (minimal_project / 'uv.lock').write_text('# UV lock file')
        
        validator = InstallationValidator(str(minimal_project))
        result = validator.validate_dependency_resolution()
        
        assert result.passed is True
        assert result.name == "dependency_resolution"
        assert result.details['lock_file_exists'] is True
        assert result.details['resolution_success'] is True
        assert "Dependencies resolve successfully" in result.message
    
    @patch('subprocess.run')
    def test_dependency_resolution_mock_failure(self, mock_run, minimal_project):
        """Test dependency resolution with mocked failed UV."""
        # Mock failed UV lock command
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Could not resolve dependencies: conflict detected"
        )
        
        validator = InstallationValidator(str(minimal_project))
        result = validator.validate_dependency_resolution()
        
        assert result.passed is False
        assert result.details['resolution_success'] is False
        assert "conflict detected" in result.details['resolution_error']
    
    @patch('subprocess.run')
    def test_uv_installation_mock_success(self, mock_run, minimal_project):
        """Test UV installation with mocked successful commands."""
        call_count = 0
        
        def mock_subprocess(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                return Mock(returncode=0, stdout="Synced dependencies successfully", stderr="")
            elif 'cli.py' in ' '.join(cmd) and '--help' in cmd:
                return Mock(returncode=0, stdout="IndexTTS CLI Help\nUsage: indextts-cli [OPTIONS]", stderr="")
            else:
                return Mock(returncode=0, stdout="Command executed", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        validator = InstallationValidator(str(minimal_project))
        result = validator.validate_uv_installation()
        
        assert result.passed is True
        assert result.name == "uv_installation"
        assert result.details['uv_sync_success'] is True
        assert len(result.details['run_tests']) > 0
        assert all(test['success'] for test in result.details['run_tests'])
        assert "successfully installs and runs" in result.message
    
    @patch('subprocess.run')
    def test_uv_installation_sync_failure(self, mock_run, minimal_project):
        """Test UV installation with sync failure."""
        def mock_subprocess(cmd, **kwargs):
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                return Mock(returncode=1, stdout="", stderr="Failed to sync: missing dependency")
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        validator = InstallationValidator(str(minimal_project))
        result = validator.validate_uv_installation()
        
        assert result.passed is False
        assert result.details['uv_sync_success'] is False
        assert "UV sync failed" in result.message
        assert "missing dependency" in result.message
    
    @patch('subprocess.run')
    def test_uv_installation_runtime_failure(self, mock_run, minimal_project):
        """Test UV installation with runtime test failure."""
        def mock_subprocess(cmd, **kwargs):
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                return Mock(returncode=0, stdout="Synced successfully", stderr="")
            elif 'cli.py' in ' '.join(cmd):
                return Mock(returncode=1, stdout="", stderr="Module not found")
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        validator = InstallationValidator(str(minimal_project))
        result = validator.validate_uv_installation()
        
        assert result.passed is False
        assert result.details['uv_sync_success'] is True
        assert "runtime tests failed" in result.message
    
    def test_uv_not_available(self, minimal_project):
        """Test behavior when UV is not available."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("uv command not found")
            
            validator = InstallationValidator(str(minimal_project))
            result = validator.validate_uv_installation()
            
            assert result.passed is False
            assert "UV not available" in result.message
            assert "uv command not found" in result.details['error']
    
    @patch('subprocess.run')
    def test_realistic_project_validation(self, mock_run, realistic_project):
        """Test validation with realistic IndexTTS project structure."""
        def mock_subprocess(cmd, **kwargs):
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                return Mock(returncode=0, stdout="Resolved 25 packages", stderr="")
            elif cmd[0:2] == ['uv', 'lock']:
                return Mock(returncode=0, stdout="Locked dependencies", stderr="")
            elif 'indextts' in ' '.join(cmd) and '--help' in cmd:
                return Mock(returncode=0, stdout="IndexTTS2 CLI Help", stderr="")
            else:
                return Mock(returncode=0, stdout="Success", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        # Create uv.lock file
        (realistic_project / 'uv.lock').write_text('# UV lock file with dependencies')
        
        validator = InstallationValidator(str(realistic_project))
        
        # Test dependency resolution
        dep_result = validator.validate_dependency_resolution()
        assert dep_result.passed is True
        
        # Test UV installation
        install_result = validator.validate_uv_installation()
        assert install_result.passed is True
        
        # Verify that complex dependencies are handled
        assert "Resolved" in install_result.details['uv_sync_output']
    
    @patch('subprocess.run')
    def test_timeout_handling(self, mock_run, minimal_project):
        """Test handling of command timeouts."""
        def mock_subprocess(cmd, **kwargs):
            if cmd == ['uv', '--version']:
                return Mock(returncode=0, stdout="uv 0.1.0", stderr="")
            elif cmd[0:2] == ['uv', 'sync']:
                raise subprocess.TimeoutExpired(cmd, timeout=300)
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = mock_subprocess
        
        validator = InstallationValidator(str(minimal_project))
        result = validator.validate_uv_installation()
        
        assert result.passed is False
        assert "timeout" in result.message.lower() or "failed" in result.message.lower()


class TestRealUVInstallation:
    """Tests that actually use UV if available (integration tests)."""
    
    def test_real_uv_check(self):
        """Test actual UV availability check."""
        try:
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            uv_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            uv_available = False
        
        if not uv_available:
            pytest.skip("UV not available for real integration test")
        
        # If UV is available, test basic functionality
        validator = InstallationValidator(".")
        result = validator.validate_dependency_resolution()
        
        # Should at least not crash
        assert result.name == "dependency_resolution"
        assert isinstance(result.passed, bool)
    
    @pytest.mark.slow
    def test_real_project_installation(self, realistic_project):
        """Test actual installation of realistic project (slow test)."""
        try:
            # Check if UV is available
            subprocess.run(['uv', '--version'], 
                          capture_output=True, text=True, timeout=10, check=True)
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pytest.skip("UV not available for real installation test")
        
        validator = InstallationValidator(str(realistic_project))
        
        # Test dependency resolution (should be fast)
        dep_result = validator.validate_dependency_resolution()
        
        # Should at least attempt resolution
        assert dep_result.name == "dependency_resolution"
        
        # Note: We don't test actual installation here as it would be very slow
        # and require internet access. The mocked tests above cover the logic.


if __name__ == "__main__":
    # Run with markers to separate fast and slow tests
    pytest.main([__file__, "-v", "-m", "not slow"])