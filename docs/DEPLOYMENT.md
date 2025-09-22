# Deployment Guide

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
