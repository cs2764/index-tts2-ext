# Troubleshooting Guide

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
