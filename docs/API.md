# IndexTTS2 API Documentation

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
