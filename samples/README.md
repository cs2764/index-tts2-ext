# Voice Samples | 语音样本

This directory contains reference voice samples for IndexTTS voice cloning functionality.

本目录包含用于 IndexTTS 语音克隆功能的参考语音样本。

## Purpose | 用途

These audio files serve as reference voices for:
- Zero-shot voice cloning
- TTS model testing and validation
- Demonstration of different voice characteristics
- Quality benchmarking

这些音频文件用作以下用途的参考语音：
- 零样本语音克隆
- TTS 模型测试和验证
- 展示不同的语音特征
- 质量基准测试

## Usage | 使用方法

### Command Line | 命令行
```bash
indextts "Your text here" --voice samples/sample_voice.wav --output output.wav
```

### Python API | Python API
```python
from indextts.infer import IndexTTS

tts = IndexTTS(model_dir="checkpoints")
tts.infer("samples/sample_voice.wav", "Your text here", "output.wav")
```

### Web Interface | Web 界面
1. Launch WebUI: `python webui.py`
2. Upload any sample from this directory as reference voice
3. Enter your text and generate speech

1. 启动 WebUI：`python webui.py`
2. 上传此目录中的任何样本作为参考语音
3. 输入文本并生成语音

## File Formats | 文件格式

Supported audio formats:
- WAV (recommended for best quality)
- MP3 (compressed format)

支持的音频格式：
- WAV（推荐，质量最佳）
- MP3（压缩格式）

## Quality Guidelines | 质量指南

For best voice cloning results, reference audio should:
- Be 3-10 seconds long
- Have clear speech without background noise
- Contain natural speaking patterns
- Be in the target language (Chinese/English)

为获得最佳语音克隆效果，参考音频应该：
- 长度为 3-10 秒
- 语音清晰，无背景噪音
- 包含自然的说话模式
- 使用目标语言（中文/英文）

## Important Note | 重要说明

**DO NOT DELETE** these sample files - they are essential for:
- TTS functionality testing
- Voice cloning demonstrations
- Model validation
- User reference and examples

**请勿删除**这些样本文件 - 它们对以下功能至关重要：
- TTS 功能测试
- 语音克隆演示
- 模型验证
- 用户参考和示例

---

**IndexTTS Version**: 0.2.3  
**Last Updated**: January 11, 2025