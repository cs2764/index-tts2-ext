"""
Documentation Generator for IndexTTS2 GitHub Preparation

This module provides bilingual documentation generation capabilities for the IndexTTS2 project,
creating comprehensive README files and system documentation with proper navigation and
installation instructions using UV package manager.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class DocumentationGenerator:
    """
    Generates bilingual documentation for IndexTTS2 project.
    
    Creates comprehensive README files and system documentation with:
    - English first, Chinese second structure
    - Navigation links to Chinese sections
    - Current IndexTTS2 capabilities and features
    - UV package manager installation instructions
    """
    
    def __init__(self, project_root: str = "."):
        """
        Initialize the documentation generator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "checkpoints" / "config.yaml"
        self.pyproject_path = self.project_root / "pyproject.toml"
        
    def get_project_metadata(self) -> Dict:
        """Extract project metadata from pyproject.toml and config files."""
        metadata = {
            "name": "IndexTTS2",
            "version": "2.0.0",
            "description": "Advanced Text-to-Speech with Emotion Control and Duration Precision",
            "author": "IndexTeam",
            "python_requires": ">=3.10",
            "main_dependencies": [
                "torch>=2.8.0",
                "torchaudio",
                "transformers",
                "gradio>=5.44.0",
                "librosa",
                "jieba",
                "g2p-en"
            ]
        }
        
        # Try to read from pyproject.toml if it exists
        if self.pyproject_path.exists():
            try:
                import tomllib
                with open(self.pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                    project_info = pyproject_data.get('project', {})
                    metadata.update({
                        "name": project_info.get('name', metadata['name']),
                        "version": project_info.get('version', metadata['version']),
                        "description": project_info.get('description', metadata['description']),
                        "python_requires": project_info.get('requires-python', metadata['python_requires'])
                    })
            except Exception:
                pass  # Use defaults if parsing fails
                
        return metadata
    
    def generate_navigation_links(self) -> str:
        """Generate navigation links to Chinese sections."""
        return """## 🌐 Language / 语言

- [English Documentation](#english-documentation) 
- [中文文档](#中文文档)

---
"""

    def generate_english_content(self, metadata: Dict) -> str:
        """Generate English documentation content."""
        return f"""# English Documentation

# {metadata['name']} - Advanced Text-to-Speech System

{metadata['description']}

## 🚀 Key Features

- **Zero-shot Voice Cloning**: Generate speech in any voice using just a short audio prompt
- **Emotional Expression Control**: Independent control over timbre and emotion through multiple modalities:
  - Audio-based emotion reference
  - Vector-based emotion control (8 emotions: happy, angry, sad, afraid, disgusted, melancholic, surprised, calm)
  - Text-based emotion descriptions via fine-tuned Qwen model
- **Duration Control**: First autoregressive TTS model with precise synthesis duration control
- **Multilingual Support**: Chinese and English text synthesis
- **High-Quality Output**: 22kHz audio generation with BigVGAN vocoder

## 🏗️ Architecture

- **GPT-based Autoregressive Model**: Core text-to-speech generation
- **Semantic Codec**: MaskGCT-based semantic representation
- **S2Mel Module**: Semantic-to-mel spectrogram conversion with diffusion
- **BigVGAN Vocoder**: High-quality mel-to-waveform conversion
- **Emotion Control System**: Qwen-based emotion understanding and vector mapping

## 📋 Requirements

- Python {metadata['python_requires']}
- CUDA 12.8+ (for GPU acceleration)
- 8GB+ VRAM recommended
- UV package manager (required)

## 🛠️ Installation

### 1. Install UV Package Manager

```bash
# Install UV package manager first
pip install -U uv
```

### 2. Clone Repository

```bash
git clone https://github.com/cs2764/index-tts2-ext.git
cd index-tts2-ext
```

### 3. Install Dependencies

```bash
# Install all dependencies (recommended)
uv sync --all-extras

# Or install specific features only
uv sync --extra webui --extra deepspeed
```

### 4. Download Models

#### Via HuggingFace (International)
```bash
uv tool install "huggingface_hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
```

#### Via ModelScope (China)
```bash
uv tool install "modelscope"
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
uv run webui.py
```

### Command Line Interface
```bash
# Basic usage
uv run indextts/cli.py "Hello world" -v examples/voice_01.wav

# With emotion control
uv run indextts/cli.py "I'm so happy!" -v examples/voice_01.wav --emotion happy
```

### Python API
```python
from indextts.infer_v2 import IndexTTS2

# Initialize model
tts = IndexTTS2()

# Generate speech
audio = tts.infer(
    text="Hello, this is IndexTTS2!",
    prompt_audio="examples/voice_01.wav",
    emotion="happy"
)
```

## 🎯 Use Cases

- **Voice Dubbing**: Precise timing control for video synchronization
- **Audiobook Narration**: Emotional storytelling with consistent voice
- **Multilingual Content**: Chinese and English content creation
- **Interactive Applications**: Expressive speech for chatbots and assistants

## ⚡ Performance Optimization

- **FP16 Inference**: Use `--fp16` flag for reduced VRAM usage
- **DeepSpeed**: Use `--deepspeed` for potential acceleration
- **CUDA Kernels**: Use `--cuda_kernel` for BigVGAN optimization
- **Device Auto-detection**: Supports CUDA, XPU, MPS, CPU

## 🧪 Testing

```bash
# Check GPU capability
uv run tools/gpu_check.py

# Run regression tests
uv run tests/regression_test.py
```

## 📁 Project Structure

```
├── indextts/           # Main package source code
├── checkpoints/        # Model weights and configuration
├── examples/           # Sample audio files and test cases
├── tests/              # Test scripts and sample data
├── tools/              # Utility scripts and helpers
├── webui.py           # Gradio web interface
└── pyproject.toml     # Package configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on PyTorch and HuggingFace Transformers
- Uses BigVGAN for high-quality vocoding
- Emotion understanding powered by Qwen model

---
"""

    def generate_chinese_content(self, metadata: Dict) -> str:
        """Generate Chinese documentation content."""
        return f"""# 中文文档

# {metadata['name']} - 先进的文本转语音系统

{metadata['description']}

## 🚀 核心特性

- **零样本语音克隆**: 仅使用短音频提示即可生成任意声音的语音
- **情感表达控制**: 通过多种模态独立控制音色和情感:
  - 基于音频的情感参考
  - 基于向量的情感控制（8种情感：开心、愤怒、悲伤、恐惧、厌恶、忧郁、惊讶、平静）
  - 通过微调Qwen模型进行基于文本的情感描述
- **时长控制**: 首个具有精确合成时长控制的自回归TTS模型
- **多语言支持**: 中文和英文文本合成
- **高质量输出**: 使用BigVGAN声码器生成22kHz音频

## 🏗️ 架构组件

- **基于GPT的自回归模型**: 核心文本转语音生成
- **语义编解码器**: 基于MaskGCT的语义表示
- **S2Mel模块**: 使用扩散的语义到梅尔频谱转换
- **BigVGAN声码器**: 高质量梅尔频谱到波形转换
- **情感控制系统**: 基于Qwen的情感理解和向量映射

## 📋 系统要求

- Python {metadata['python_requires']}
- CUDA 12.8+（用于GPU加速）
- 推荐8GB+显存
- UV包管理器（必需）

## 🛠️ 安装指南

### 1. 安装UV包管理器

```bash
# 首先安装UV包管理器
pip install -U uv
```

### 2. 克隆仓库

```bash
git clone https://github.com/cs2764/index-tts2-ext.git
cd index-tts2-ext
```

### 3. 安装依赖

```bash
# 安装所有依赖（推荐）
uv sync --all-extras

# 或仅安装特定功能
uv sync --extra webui --extra deepspeed
```

### 4. 下载模型

#### 通过HuggingFace（国际）
```bash
uv tool install "huggingface_hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
```

#### 通过ModelScope（中国）
```bash
uv tool install "modelscope"
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

## 🚀 快速开始

### Web界面（推荐）
```bash
uv run webui.py
```

### 命令行界面
```bash
# 基本用法
uv run indextts/cli.py "你好世界" -v examples/voice_01.wav

# 带情感控制
uv run indextts/cli.py "我很开心！" -v examples/voice_01.wav --emotion happy
```

### Python API
```python
from indextts.infer_v2 import IndexTTS2

# 初始化模型
tts = IndexTTS2()

# 生成语音
audio = tts.infer(
    text="你好，这是IndexTTS2！",
    prompt_audio="examples/voice_01.wav",
    emotion="happy"
)
```

## 🎯 应用场景

- **配音制作**: 精确时长控制用于视频同步
- **有声读物**: 情感丰富的叙述，声音一致
- **多语言内容**: 中英文内容创作
- **交互应用**: 为聊天机器人和助手提供富有表现力的语音

## ⚡ 性能优化

- **FP16推理**: 使用`--fp16`标志减少显存使用
- **DeepSpeed**: 使用`--deepspeed`进行潜在加速
- **CUDA内核**: 使用`--cuda_kernel`优化BigVGAN
- **设备自动检测**: 支持CUDA、XPU、MPS、CPU

## 🧪 测试

```bash
# 检查GPU能力
uv run tools/gpu_check.py

# 运行回归测试
uv run tests/regression_test.py
```

## 📁 项目结构

```
├── indextts/           # 主要包源代码
├── checkpoints/        # 模型权重和配置
├── examples/           # 示例音频文件和测试用例
├── tests/              # 测试脚本和示例数据
├── tools/              # 实用脚本和助手
├── webui.py           # Gradio网页界面
└── pyproject.toml     # 包配置
```

## 🤝 贡献

1. Fork本仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 🙏 致谢

- 基于PyTorch和HuggingFace Transformers构建
- 使用BigVGAN进行高质量声码化
- 情感理解由Qwen模型提供支持

---
"""

    def update_readme(self) -> None:
        """Generate and update the main README.md file."""
        metadata = self.get_project_metadata()
        
        # Generate complete README content
        readme_content = self.generate_navigation_links()
        readme_content += self.generate_english_content(metadata)
        readme_content += self.generate_chinese_content(metadata)
        
        # Write to README.md
        readme_path = self.project_root / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ Updated README.md with bilingual documentation")

    def create_system_docs(self) -> None:
        """Create comprehensive system documentation."""
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Create API documentation
        self._create_api_documentation(docs_dir)
        
        # Create deployment guide
        self._create_deployment_guide(docs_dir)
        
        # Create troubleshooting guide
        self._create_troubleshooting_guide(docs_dir)
        
        print(f"✅ Created system documentation in {docs_dir}")

    def _create_api_documentation(self, docs_dir: Path) -> None:
        """Create API documentation."""
        api_content = """# IndexTTS2 API Documentation

## Core Classes

### IndexTTS2

Main inference class for text-to-speech generation.

```python
from indextts.infer_v2 import IndexTTS2

tts = IndexTTS2(
    device="cuda",  # or "cpu", "mps"
    fp16=True,      # Use FP16 for memory efficiency
    deepspeed=False # Enable DeepSpeed acceleration
)
```

#### Methods

##### `infer(text, prompt_audio, emotion=None, **kwargs)`

Generate speech from text with optional emotion control.

**Parameters:**
- `text` (str): Input text to synthesize
- `prompt_audio` (str): Path to reference audio file
- `emotion` (str, optional): Emotion name or vector
- `language` (str): "zh" for Chinese, "en" for English
- `speed` (float): Speech speed multiplier (default: 1.0)

**Returns:**
- `numpy.ndarray`: Generated audio waveform

**Example:**
```python
audio = tts.infer(
    text="Hello world!",
    prompt_audio="examples/voice_01.wav",
    emotion="happy",
    language="en",
    speed=1.2
)
```

## Emotion Control

### Available Emotions

- `happy`: Joyful, upbeat expression
- `angry`: Aggressive, intense expression  
- `sad`: Melancholic, sorrowful expression
- `afraid`: Fearful, anxious expression
- `disgusted`: Repulsed, distasteful expression
- `melancholic`: Deep sadness, contemplative
- `surprised`: Shocked, amazed expression
- `calm`: Peaceful, relaxed expression

### Emotion Vectors

You can also use emotion vectors for fine-grained control:

```python
import numpy as np

# Custom emotion vector (8 dimensions)
emotion_vector = np.array([0.8, 0.2, 0.1, 0.0, 0.0, 0.3, 0.1, 0.5])

audio = tts.infer(
    text="Custom emotion example",
    prompt_audio="examples/voice_01.wav",
    emotion=emotion_vector
)
```

## Configuration

### Model Configuration

Edit `checkpoints/config.yaml` to modify model behavior:

```yaml
model:
  gpt_path: "checkpoints/gpt.pth"
  s2mel_path: "checkpoints/s2mel.pth"
  bigvgan_path: "checkpoints/bigvgan.pth"
  
inference:
  sample_rate: 22050
  hop_length: 256
  win_length: 1024
```

### Performance Tuning

```python
# Memory-efficient inference
tts = IndexTTS2(fp16=True, device="cuda")

# Maximum quality (requires more VRAM)
tts = IndexTTS2(fp16=False, cuda_kernel=True)

# CPU inference
tts = IndexTTS2(device="cpu")
```
"""
        
        with open(docs_dir / "API.md", 'w', encoding='utf-8') as f:
            f.write(api_content)

    def _create_deployment_guide(self, docs_dir: Path) -> None:
        """Create deployment guide."""
        deployment_content = """# Deployment Guide

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

# Install UV
RUN pip install -U uv

# Install dependencies
RUN uv sync --all-extras

# Download models
RUN uv tool install "huggingface_hub[cli]"
RUN hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints

EXPOSE 7860

CMD ["uv", "run", "webui.py", "--server-name", "0.0.0.0"]
```

### Cloud Deployment

#### AWS EC2
1. Launch GPU instance (g4dn.xlarge or larger)
2. Install CUDA drivers
3. Follow standard installation process
4. Configure security groups for port 7860

#### Google Cloud Platform
1. Create Compute Engine instance with GPU
2. Install NVIDIA drivers
3. Follow standard installation process

### Performance Considerations

- **Memory**: 8GB+ VRAM recommended for optimal performance
- **Storage**: 10GB+ for models and cache
- **CPU**: Multi-core recommended for preprocessing
- **Network**: High bandwidth for model downloads

### Scaling

For high-throughput applications:

```python
# Use multiple workers
import multiprocessing as mp

def worker_process():
    tts = IndexTTS2(device=f"cuda:{worker_id}")
    # Process requests...

# Start multiple workers
workers = []
for i in range(mp.cpu_count()):
    p = mp.Process(target=worker_process)
    workers.append(p)
    p.start()
```

### Monitoring

Monitor GPU usage and memory:

```bash
# GPU monitoring
nvidia-smi -l 1

# Memory usage
uv run tools/gpu_check.py
```
"""
        
        with open(docs_dir / "DEPLOYMENT.md", 'w', encoding='utf-8') as f:
            f.write(deployment_content)

    def _create_troubleshooting_guide(self, docs_dir: Path) -> None:
        """Create troubleshooting guide."""
        troubleshooting_content = """# Troubleshooting Guide

## Common Issues

### Installation Issues

#### UV Installation Failed
```bash
# Try alternative installation
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### CUDA Not Detected
```bash
# Check CUDA installation
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA
uv add torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Model Download Failed
```bash
# Use alternative download method
wget https://huggingface.co/IndexTeam/IndexTTS-2/resolve/main/gpt.pth -O checkpoints/gpt.pth
```

### Runtime Issues

#### Out of Memory (OOM)
- Enable FP16: `--fp16`
- Reduce batch size
- Use CPU inference: `--device cpu`
- Close other GPU applications

#### Slow Inference
- Enable CUDA kernels: `--cuda_kernel`
- Use FP16 precision: `--fp16`
- Check GPU utilization: `nvidia-smi`

#### Audio Quality Issues
- Check sample rate matches (22050 Hz)
- Verify prompt audio quality
- Try different emotion settings
- Ensure proper text preprocessing

### Web UI Issues

#### Port Already in Use
```bash
# Use different port
uv run webui.py --server-port 7861
```

#### Cannot Access Web UI
- Check firewall settings
- Use `--server-name 0.0.0.0` for external access
- Verify port forwarding

### Model Issues

#### Model Loading Failed
- Verify checkpoints directory structure
- Check file permissions
- Re-download corrupted models

#### Emotion Control Not Working
- Verify emotion name spelling
- Check emotion vector dimensions (must be 8)
- Ensure Qwen model is loaded

## Performance Optimization

### Memory Optimization
```python
# Optimize for low VRAM
tts = IndexTTS2(
    fp16=True,
    device="cuda",
    low_vram_mode=True
)
```

### Speed Optimization
```python
# Optimize for speed
tts = IndexTTS2(
    cuda_kernel=True,
    compile_model=True
)
```

## Getting Help

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Create new issue with:
   - System information
   - Error messages
   - Minimal reproduction code
   - Expected vs actual behavior

## Debug Information

Run diagnostic script:
```bash
uv run tools/gpu_check.py
```

This will output:
- System information
- GPU details
- Memory usage
- Model status
"""
        
        with open(docs_dir / "TROUBLESHOOTING.md", 'w', encoding='utf-8') as f:
            f.write(troubleshooting_content)

    def update_version_info(self) -> None:
        """Update version information in documentation."""
        # This method can be used to update version-specific information
        # in documentation files when versions change
        metadata = self.get_project_metadata()
        current_version = metadata['version']
        
        print(f"✅ Version information updated to {current_version}")

    def generate_all_documentation(self) -> None:
        """Generate all documentation files."""
        print("🚀 Generating bilingual documentation...")
        
        # Update main README
        self.update_readme()
        
        # Create system documentation
        self.create_system_docs()
        
        # Update version info
        self.update_version_info()
        
        print("✅ All documentation generated successfully!")


if __name__ == "__main__":
    # Example usage
    generator = DocumentationGenerator()
    generator.generate_all_documentation()