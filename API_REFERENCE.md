# IndexTTS2 API Reference / API参考文档

[English](#english) | [中文](#中文)

---

## English

This document provides comprehensive API reference for IndexTTS2, including Python API, CLI interface, and Web API endpoints.

## Table of Contents

1. [Python API](#python-api)
2. [Command Line Interface](#command-line-interface)
3. [Web API Endpoints](#web-api-endpoints)
4. [Configuration API](#configuration-api)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

## Python API

### Core Classes

#### IndexTTS2

The main inference class for text-to-speech generation.

```python
from indextts.infer_v2 import IndexTTS2

class IndexTTS2:
    def __init__(self, config_path: str = "checkpoints/config.yaml", **kwargs):
        """
        Initialize IndexTTS2 model.
        
        Args:
            config_path (str): Path to configuration file
            **kwargs: Additional configuration options
        """
```

##### Methods

###### `infer()`

Generate speech from text with emotion control.

```python
def infer(
    self,
    text: str,
    prompt_audio: str,
    emotion: Optional[str] = None,
    emotion_vector: Optional[List[float]] = None,
    duration_control: Optional[float] = None,
    **kwargs
) -> torch.Tensor:
    """
    Generate speech from text.
    
    Args:
        text (str): Input text to synthesize
        prompt_audio (str): Path to reference audio file
        emotion (str, optional): Emotion name (happy, sad, angry, etc.)
        emotion_vector (List[float], optional): Custom emotion vector
        duration_control (float, optional): Duration scaling factor
        
    Returns:
        torch.Tensor: Generated audio tensor
        
    Raises:
        ValueError: If text is empty or invalid
        FileNotFoundError: If prompt_audio file not found
        RuntimeError: If inference fails
    """
```

###### `save_audio()`

Save generated audio to file.

```python
def save_audio(
    self,
    audio: torch.Tensor,
    output_path: str,
    sample_rate: int = 22050,
    format: str = "wav"
) -> str:
    """
    Save audio tensor to file.
    
    Args:
        audio (torch.Tensor): Audio tensor to save
        output_path (str): Output file path
        sample_rate (int): Audio sample rate
        format (str): Output format (wav, mp3, m4a)
        
    Returns:
        str: Path to saved file
    """
```

### Emotion Control

#### Available Emotions

```python
SUPPORTED_EMOTIONS = [
    "happy",      # 开心
    "sad",        # 悲伤
    "angry",      # 愤怒
    "afraid",     # 恐惧
    "disgusted",  # 厌恶
    "melancholic", # 忧郁
    "surprised",  # 惊讶
    "calm"        # 平静
]
```

#### Emotion Vector Format

```python
# 8-dimensional emotion vector
emotion_vector = [
    0.8,  # happy
    0.1,  # sad
    0.0,  # angry
    0.0,  # afraid
    0.0,  # disgusted
    0.1,  # melancholic
    0.0,  # surprised
    0.0   # calm
]
```

### Audio Processing

#### AudioProcessor

```python
from indextts.utils.audio import AudioProcessor

class AudioProcessor:
    def __init__(self, sample_rate: int = 22050):
        """Initialize audio processor."""
        
    def load_audio(self, path: str) -> torch.Tensor:
        """Load audio file."""
        
    def save_audio(self, audio: torch.Tensor, path: str, format: str = "wav"):
        """Save audio to file."""
        
    def resample(self, audio: torch.Tensor, target_sr: int) -> torch.Tensor:
        """Resample audio to target sample rate."""
```

## Command Line Interface

### Basic Usage

```bash
# Basic synthesis
uv run indextts/cli.py "Hello world" -v examples/voice_01.wav

# With emotion control
uv run indextts/cli.py "I'm happy!" -v examples/voice_01.wav --emotion happy

# With output file
uv run indextts/cli.py "Hello" -v examples/voice_01.wav -o output.wav

# With duration control
uv run indextts/cli.py "Hello" -v examples/voice_01.wav --duration 1.5
```

### CLI Arguments

```bash
usage: cli.py [-h] [--voice VOICE] [--emotion EMOTION] 
              [--emotion-vector EMOTION_VECTOR] [--output OUTPUT]
              [--duration DURATION] [--fp16] [--cuda-kernel]
              [--config CONFIG] [--device DEVICE]
              text

positional arguments:
  text                  Text to synthesize

optional arguments:
  -h, --help           Show help message
  -v, --voice VOICE    Path to reference voice audio file
  -e, --emotion EMOTION
                       Emotion name (happy, sad, angry, etc.)
  --emotion-vector EMOTION_VECTOR
                       Custom emotion vector (8 floats)
  -o, --output OUTPUT  Output audio file path
  -d, --duration DURATION
                       Duration scaling factor
  --fp16               Use FP16 inference for memory efficiency
  --cuda-kernel        Use CUDA kernels for acceleration
  --config CONFIG      Path to configuration file
  --device DEVICE      Device to use (cuda, cpu, mps)
```

### Examples

```bash
# Chinese text synthesis
uv run indextts/cli.py "你好世界" -v examples/voice_01.wav -o hello_chinese.wav

# English with emotion
uv run indextts/cli.py "I'm so excited!" -v examples/voice_02.wav --emotion happy

# Custom emotion vector
uv run indextts/cli.py "Hello" -v examples/voice_01.wav --emotion-vector "0.8,0.1,0.0,0.0,0.0,0.1,0.0,0.0"

# Performance optimization
uv run indextts/cli.py "Hello" -v examples/voice_01.wav --fp16 --cuda-kernel
```

## Web API Endpoints

### Base URL

```
http://localhost:7860
```

### Authentication

Currently, no authentication is required for local deployment.

### Endpoints

#### POST /api/synthesize

Generate speech from text.

**Request Body:**
```json
{
  "text": "Hello, world!",
  "prompt_audio": "base64_encoded_audio_data",
  "emotion": "happy",
  "duration_control": 1.0,
  "output_format": "wav"
}
```

**Response:**
```json
{
  "success": true,
  "audio_data": "base64_encoded_audio_data",
  "duration": 2.5,
  "sample_rate": 22050,
  "message": "Synthesis completed successfully"
}
```

#### GET /api/emotions

Get list of supported emotions.

**Response:**
```json
{
  "emotions": [
    {"name": "happy", "description": "Happy emotion"},
    {"name": "sad", "description": "Sad emotion"},
    {"name": "angry", "description": "Angry emotion"}
  ]
}
```

#### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "gpu_available": true,
  "memory_usage": "45%"
}
```

#### POST /api/upload_voice

Upload reference voice sample.

**Request:** Multipart form data with audio file

**Response:**
```json
{
  "success": true,
  "file_id": "voice_sample_123",
  "duration": 3.2,
  "message": "Voice sample uploaded successfully"
}
```

## Configuration API

### Config Class

```python
from indextts.config import Config

class Config:
    def __init__(self, config_path: str = "checkpoints/config.yaml"):
        """Load configuration from file."""
        
    def get(self, key: str, default=None):
        """Get configuration value."""
        
    def set(self, key: str, value):
        """Set configuration value."""
        
    def save(self, path: str = None):
        """Save configuration to file."""
```

### Configuration Structure

```yaml
# Model paths
model:
  gpt_path: "checkpoints/gpt.pth"
  s2mel_path: "checkpoints/s2mel.pth"
  bigvgan_path: "checkpoints/bigvgan.pth"
  emotion_model_path: "checkpoints/qwen0.6bemo4-merge"

# Audio settings
audio:
  sample_rate: 22050
  hop_length: 256
  win_length: 1024
  n_fft: 1024

# Inference settings
inference:
  fp16: true
  use_cuda_kernel: false
  batch_size: 1
  max_length: 1024

# Emotion settings
emotion:
  default_emotion: "calm"
  emotion_strength: 1.0
  use_emotion_model: true
```

## Error Handling

### Exception Classes

```python
class IndexTTSError(Exception):
    """Base exception for IndexTTS errors."""
    pass

class ModelLoadError(IndexTTSError):
    """Raised when model loading fails."""
    pass

class InferenceError(IndexTTSError):
    """Raised when inference fails."""
    pass

class AudioProcessingError(IndexTTSError):
    """Raised when audio processing fails."""
    pass

class ConfigurationError(IndexTTSError):
    """Raised when configuration is invalid."""
    pass
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "type": "InferenceError",
    "message": "Failed to generate speech",
    "details": "CUDA out of memory",
    "code": "E001"
  }
}
```

### Common Error Codes

- `E001`: CUDA out of memory
- `E002`: Model file not found
- `E003`: Invalid audio format
- `E004`: Text too long
- `E005`: Invalid emotion parameter

## Examples

### Basic Python Usage

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

# Save audio
tts.save_audio(audio, "output.wav")
```

### Advanced Usage with Custom Emotion

```python
from indextts.infer_v2 import IndexTTS2

# Initialize model
tts = IndexTTS2()

# Custom emotion vector (happy + surprised)
emotion_vector = [0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.0]

# Generate speech with custom emotion
audio = tts.infer(
    text="What a surprise!",
    prompt_audio="examples/voice_01.wav",
    emotion_vector=emotion_vector,
    duration_control=1.2
)

# Save as MP3
tts.save_audio(audio, "surprise.mp3", format="mp3")
```

### Batch Processing

```python
from indextts.infer_v2 import IndexTTS2
import os

# Initialize model
tts = IndexTTS2()

# Batch process multiple texts
texts = [
    "Hello, world!",
    "How are you today?",
    "This is a test."
]

for i, text in enumerate(texts):
    audio = tts.infer(
        text=text,
        prompt_audio="examples/voice_01.wav",
        emotion="calm"
    )
    
    output_path = f"batch_output_{i:03d}.wav"
    tts.save_audio(audio, output_path)
    print(f"Generated: {output_path}")
```

### Web API Usage (Python)

```python
import requests
import base64

# Upload voice sample
with open("my_voice.wav", "rb") as f:
    voice_data = base64.b64encode(f.read()).decode()

# Synthesize speech
response = requests.post("http://localhost:7860/api/synthesize", json={
    "text": "Hello from API!",
    "prompt_audio": voice_data,
    "emotion": "happy",
    "output_format": "wav"
})

if response.json()["success"]:
    audio_data = base64.b64decode(response.json()["audio_data"])
    with open("api_output.wav", "wb") as f:
        f.write(audio_data)
```

---

## 中文

本文档提供IndexTTS2的全面API参考，包括Python API、命令行界面和Web API端点。

## 目录

1. [Python API](#python-api-1)
2. [命令行界面](#命令行界面)
3. [Web API端点](#web-api端点)
4. [配置API](#配置api)
5. [错误处理](#错误处理-1)
6. [示例](#示例-1)

## Python API

### 核心类

#### IndexTTS2

用于文本转语音生成的主要推理类。

```python
from indextts.infer_v2 import IndexTTS2

class IndexTTS2:
    def __init__(self, config_path: str = "checkpoints/config.yaml", **kwargs):
        """
        初始化IndexTTS2模型。
        
        参数:
            config_path (str): 配置文件路径
            **kwargs: 额外的配置选项
        """
```

##### 方法

###### `infer()`

从文本生成带有情感控制的语音。

```python
def infer(
    self,
    text: str,
    prompt_audio: str,
    emotion: Optional[str] = None,
    emotion_vector: Optional[List[float]] = None,
    duration_control: Optional[float] = None,
    **kwargs
) -> torch.Tensor:
    """
    从文本生成语音。
    
    参数:
        text (str): 要合成的输入文本
        prompt_audio (str): 参考音频文件路径
        emotion (str, optional): 情感名称（开心、悲伤、愤怒等）
        emotion_vector (List[float], optional): 自定义情感向量
        duration_control (float, optional): 时长缩放因子
        
    返回:
        torch.Tensor: 生成的音频张量
        
    异常:
        ValueError: 如果文本为空或无效
        FileNotFoundError: 如果找不到prompt_audio文件
        RuntimeError: 如果推理失败
    """
```

### 情感控制

#### 支持的情感

```python
SUPPORTED_EMOTIONS = [
    "happy",      # 开心
    "sad",        # 悲伤
    "angry",      # 愤怒
    "afraid",     # 恐惧
    "disgusted",  # 厌恶
    "melancholic", # 忧郁
    "surprised",  # 惊讶
    "calm"        # 平静
]
```

#### 情感向量格式

```python
# 8维情感向量
emotion_vector = [
    0.8,  # 开心
    0.1,  # 悲伤
    0.0,  # 愤怒
    0.0,  # 恐惧
    0.0,  # 厌恶
    0.1,  # 忧郁
    0.0,  # 惊讶
    0.0   # 平静
]
```

## 命令行界面

### 基本用法

```bash
# 基本合成
uv run indextts/cli.py "你好世界" -v examples/voice_01.wav

# 带情感控制
uv run indextts/cli.py "我很开心！" -v examples/voice_01.wav --emotion happy

# 指定输出文件
uv run indextts/cli.py "你好" -v examples/voice_01.wav -o output.wav

# 带时长控制
uv run indextts/cli.py "你好" -v examples/voice_01.wav --duration 1.5
```

### CLI参数

```bash
用法: cli.py [-h] [--voice VOICE] [--emotion EMOTION] 
              [--emotion-vector EMOTION_VECTOR] [--output OUTPUT]
              [--duration DURATION] [--fp16] [--cuda-kernel]
              [--config CONFIG] [--device DEVICE]
              text

位置参数:
  text                  要合成的文本

可选参数:
  -h, --help           显示帮助信息
  -v, --voice VOICE    参考语音音频文件路径
  -e, --emotion EMOTION
                       情感名称（开心、悲伤、愤怒等）
  --emotion-vector EMOTION_VECTOR
                       自定义情感向量（8个浮点数）
  -o, --output OUTPUT  输出音频文件路径
  -d, --duration DURATION
                       时长缩放因子
  --fp16               使用FP16推理提高内存效率
  --cuda-kernel        使用CUDA内核加速
  --config CONFIG      配置文件路径
  --device DEVICE      使用的设备（cuda、cpu、mps）
```

## Web API端点

### 基础URL

```
http://localhost:7860
```

### 端点

#### POST /api/synthesize

从文本生成语音。

**请求体:**
```json
{
  "text": "你好，世界！",
  "prompt_audio": "base64编码的音频数据",
  "emotion": "happy",
  "duration_control": 1.0,
  "output_format": "wav"
}
```

**响应:**
```json
{
  "success": true,
  "audio_data": "base64编码的音频数据",
  "duration": 2.5,
  "sample_rate": 22050,
  "message": "合成成功完成"
}
```

## 错误处理

### 异常类

```python
class IndexTTSError(Exception):
    """IndexTTS错误的基础异常。"""
    pass

class ModelLoadError(IndexTTSError):
    """模型加载失败时抛出。"""
    pass

class InferenceError(IndexTTSError):
    """推理失败时抛出。"""
    pass
```

## 示例

### 基本Python用法

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

# 保存音频
tts.save_audio(audio, "output.wav")
```

### 批量处理

```python
from indextts.infer_v2 import IndexTTS2

# 初始化模型
tts = IndexTTS2()

# 批量处理多个文本
texts = [
    "你好，世界！",
    "今天天气怎么样？",
    "这是一个测试。"
]

for i, text in enumerate(texts):
    audio = tts.infer(
        text=text,
        prompt_audio="examples/voice_01.wav",
        emotion="calm"
    )
    
    output_path = f"batch_output_{i:03d}.wav"
    tts.save_audio(audio, output_path)
    print(f"已生成: {output_path}")
```