## 🌐 Language / 语言

- [English Documentation](#english-documentation) 
- [中文文档](#中文文档)

---

# English Documentation

# IndexTTS2 - Advanced Text-to-Speech System

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/IndexTeam/IndexTTS2/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![PyTorch](https://img.shields.io/badge/pytorch-2.8+-red.svg)](https://pytorch.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Advanced Text-to-Speech with Emotion Control and Duration Precision

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

- **Python**: 3.10 or higher
- **CUDA**: 12.8+ (for GPU acceleration)
- **Memory**: 8GB+ VRAM recommended
- **Package Manager**: UV (required)
- **Storage**: 10GB+ free space for models

## 🛠️ Installation

### 1. Install UV Package Manager

```bash
# Install UV package manager first
pip install -U uv
```

### 2. Clone Repository

```bash
git clone https://github.com/IndexTeam/IndexTTS2.git
cd IndexTTS2
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
│   ├── infer_v2.py    # Core inference engine
│   ├── gpt/           # GPT model components
│   ├── s2mel/         # Semantic-to-mel conversion
│   ├── BigVGAN/       # Vocoder implementation
│   └── utils/         # Utility functions
├── checkpoints/        # Model weights and configuration
├── examples/           # Sample audio files and test cases
├── tests/              # Comprehensive test suite
├── tools/              # Utility scripts and helpers
├── docs/               # Documentation
├── webui.py           # Gradio web interface
└── pyproject.toml     # Package configuration
```

## 📚 Documentation

- **[API Reference](API_REFERENCE.md)**: Complete API documentation
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)**: Production deployment instructions
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project
- **[Changelog](CHANGELOG.md)**: Version history and updates

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Development setup and guidelines
- Code style and testing requirements
- Pull request process
- Areas where help is needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [GitHub](https://github.com/IndexTeam/IndexTTS2)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/IndexTeam/IndexTTS2/issues)
- **Releases**: [Version History](https://github.com/IndexTeam/IndexTTS2/releases)
- **Documentation**: [Full Documentation](docs/)

## 🙏 Acknowledgments

- Built on PyTorch and HuggingFace Transformers
- Uses BigVGAN for high-quality vocoding
- Emotion understanding powered by Qwen model
- Special thanks to the open-source community

---
# 中文文档

# IndexTTS2 - 先进的文本转语音系统

[![版本](https://img.shields.io/badge/版本-2.1.0-blue.svg)](https://github.com/IndexTeam/IndexTTS2/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![PyTorch](https://img.shields.io/badge/pytorch-2.8+-red.svg)](https://pytorch.org)
[![许可证](https://img.shields.io/badge/许可证-MIT-yellow.svg)](LICENSE)

具有情感控制和时长精确控制的先进文本转语音系统

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

- **Python**: 3.10或更高版本
- **CUDA**: 12.8+（用于GPU加速）
- **内存**: 推荐8GB+显存
- **包管理器**: UV（必需）
- **存储**: 10GB+可用空间用于模型

## 🛠️ 安装指南

### 1. 安装UV包管理器

```bash
# 首先安装UV包管理器
pip install -U uv
```

### 2. 克隆仓库

```bash
git clone https://github.com/IndexTeam/IndexTTS2.git
cd IndexTTS2
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
│   ├── infer_v2.py    # 核心推理引擎
│   ├── gpt/           # GPT模型组件
│   ├── s2mel/         # 语义到梅尔频谱转换
│   ├── BigVGAN/       # 声码器实现
│   └── utils/         # 实用函数
├── checkpoints/        # 模型权重和配置
├── examples/           # 示例音频文件和测试用例
├── tests/              # 全面的测试套件
├── tools/              # 实用脚本和助手
├── docs/               # 文档
├── webui.py           # Gradio网页界面
└── pyproject.toml     # 包配置
```

## 📚 文档

- **[API参考](API_REFERENCE.md)**: 完整的API文档
- **[部署指南](DEPLOYMENT_GUIDE.md)**: 生产环境部署说明
- **[贡献指南](CONTRIBUTING.md)**: 如何为项目做贡献
- **[更新日志](CHANGELOG.md)**: 版本历史和更新

## 🤝 贡献

我们欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详情：

- 开发设置和指南
- 代码风格和测试要求
- Pull Request流程
- 需要帮助的领域

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 🔗 链接

- **仓库**: [GitHub](https://github.com/IndexTeam/IndexTTS2)
- **问题**: [错误报告和功能请求](https://github.com/IndexTeam/IndexTTS2/issues)
- **发布**: [版本历史](https://github.com/IndexTeam/IndexTTS2/releases)
- **文档**: [完整文档](docs/)

## 🙏 致谢

- 基于PyTorch和HuggingFace Transformers构建
- 使用BigVGAN进行高质量声码化
- 情感理解由Qwen模型提供支持
- 特别感谢开源社区

---
