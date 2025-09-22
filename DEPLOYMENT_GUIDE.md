# IndexTTS2 Deployment Guide / 部署指南

[English](#english) | [中文](#中文)

---

## English

This guide provides comprehensive instructions for deploying IndexTTS2 with all features and optimizations.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Environment Variables](#environment-variables)
5. [Deployment Options](#deployment-options)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **OS**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: 3.10 or higher
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space (more for models and outputs)
- **GPU**: CUDA-compatible GPU recommended (optional)

### Recommended Requirements

- **RAM**: 32GB for large file processing
- **Storage**: SSD with 50GB+ free space
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **CPU**: Multi-core processor (8+ cores recommended)

### Dependencies

#### Core Dependencies (Required)
```bash
# Installed automatically with uv sync
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.30.0
gradio>=4.0.0
PyYAML>=6.0
```

#### Optional Dependencies (Enhanced Features)
```bash
# For EPUB processing
ebooklib>=0.18

# For encoding detection
chardet>=5.0.0

# For audio processing
librosa>=0.10.0
soundfile>=0.12.0
pydub>=0.25.0

# For audio metadata
mutagen>=1.46.0

# For system monitoring
psutil>=5.9.0
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/IndexTeam/IndexTTS-2.git
cd IndexTTS-2
```

### 2. Install UV Package Manager

```bash
# Install UV (if not already installed)
pip install -U uv
```

### 3. Install Dependencies

```bash
# Install all dependencies including optional ones
uv sync --all-extras

# Or install specific feature sets
uv sync --extra webui --extra audio --extra performance
```

### 4. Download Models

```bash
# Via HuggingFace
uv tool install "huggingface_hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints

# Or via ModelScope (China)
uv tool install "modelscope"
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

### 5. Verify Installation

```bash
# Run system check
uv run tools/gpu_check.py

# Run smoke tests
uv run python -m pytest tests/test_runner.py --type smoke
```

## Configuration

### 1. Basic Configuration

Copy and customize the configuration file:

```bash
# Copy default configuration
cp config/enhanced_webui_config.yaml config/my_config.yaml

# Edit configuration
nano config/my_config.yaml
```

### 2. Key Configuration Sections

#### File Processing
```yaml
file_processing:
  max_file_size_mb: 100          # Maximum file size
  supported_formats: [txt, epub] # Supported formats
  encoding:
    default_encoding: utf-8      # Default text encoding
```

#### Audio Formats
```yaml
audio_formats:
  default_format: mp3            # Default output format
  mp3:
    default_bitrate: 64          # MP3 bitrate in kbps
  m4b:
    enable_bookmarks: true       # Enable chapter bookmarks
```

#### Performance
```yaml
performance:
  memory:
    warning_threshold: 80        # Memory warning at 80%
    critical_threshold: 90       # Critical at 90%
  processing:
    enable_parallel: true        # Enable parallel processing
    max_parallel_processes: 4    # Max parallel processes
```

### 3. Directory Structure

Ensure the following directories exist:

```
IndexTTS-2/
├── checkpoints/          # Model files
├── config/              # Configuration files
├── samples/             # Voice samples (created automatically)
├── outputs/             # Generated audio (created automatically)
├── logs/               # Log files (created automatically)
└── prompts/            # Uploaded prompts (created automatically)
```

## Environment Variables

Configure the system using environment variables for deployment flexibility:

### Core Settings
```bash
# File processing
export INDEXTTS_MAX_FILE_SIZE=100
export INDEXTTS_SUPPORTED_FORMATS="txt,epub"
export INDEXTTS_DEFAULT_ENCODING="utf-8"

# Directories
export INDEXTTS_SAMPLES_DIR="/path/to/samples"
export INDEXTTS_OUTPUT_DIR="/path/to/outputs"

# Audio settings
export INDEXTTS_DEFAULT_AUDIO_FORMAT="mp3"
export INDEXTTS_MP3_BITRATE=64
```

### Performance Settings
```bash
# Memory management
export INDEXTTS_MEMORY_WARNING_THRESHOLD=80
export INDEXTTS_MEMORY_CRITICAL_THRESHOLD=90

# Task management
export INDEXTTS_ENABLE_BACKGROUND_TASKS=true
export INDEXTTS_MAX_QUEUE_SIZE=50
export INDEXTTS_WORKER_THREADS=2
```

### Development Settings
```bash
# Debug mode
export INDEXTTS_DEBUG=false
export INDEXTTS_LOG_LEVEL="INFO"
export INDEXTTS_MOCK_DEPENDENCIES=false
```

## Deployment Options

### 1. Local Development

```bash
# Run with default settings
uv run webui.py

# Run with custom configuration
uv run webui.py --config config/my_config.yaml

# Run in debug mode
INDEXTTS_DEBUG=true uv run webui.py
```

### 2. Production Server

#### Using Systemd (Linux)

Create service file `/etc/systemd/system/indextts-webui.service`:

```ini
[Unit]
Description=IndexTTS2 Enhanced WebUI
After=network.target

[Service]
Type=simple
User=indextts
WorkingDirectory=/opt/IndexTTS-2
Environment=INDEXTTS_LOG_LEVEL=INFO
Environment=INDEXTTS_OUTPUT_DIR=/var/lib/indextts/outputs
Environment=INDEXTTS_SAMPLES_DIR=/var/lib/indextts/samples
ExecStart=/opt/IndexTTS-2/.venv/bin/python webui.py --host 0.0.0.0 --port 7860
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable indextts-webui
sudo systemctl start indextts-webui
sudo systemctl status indextts-webui
```

#### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install -U uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --all-extras

# Create directories
RUN mkdir -p samples outputs logs

# Expose port
EXPOSE 7860

# Set environment variables
ENV INDEXTTS_OUTPUT_DIR=/app/outputs
ENV INDEXTTS_SAMPLES_DIR=/app/samples
ENV INDEXTTS_LOG_LEVEL=INFO

# Run application
CMD ["uv", "run", "webui.py", "--host", "0.0.0.0", "--port", "7860"]
```

Build and run:
```bash
docker build -t indextts-webui .
docker run -p 7860:7860 -v ./outputs:/app/outputs -v ./samples:/app/samples indextts-webui
```

### 3. Cloud Deployment

#### AWS EC2

1. Launch EC2 instance (recommended: g4dn.xlarge or larger)
2. Install dependencies and clone repository
3. Configure security groups (port 7860)
4. Use systemd service for auto-restart
5. Consider using EFS for shared storage

#### Google Cloud Platform

1. Create Compute Engine instance with GPU
2. Install CUDA drivers if using GPU
3. Follow standard installation steps
4. Use Cloud Storage for model files

#### Azure

1. Create Virtual Machine with GPU support
2. Install dependencies
3. Configure network security groups
4. Use Azure Blob Storage for large files

## Performance Optimization

### 1. Memory Optimization

```yaml
# In config file
performance:
  memory:
    enabled: true
    warning_threshold: 75
    critical_threshold: 85
    auto_cleanup: true
```

### 2. GPU Optimization

```bash
# Enable CUDA kernels
export CUDA_VISIBLE_DEVICES=0
uv run webui.py --use_cuda_kernel --fp16
```

### 3. Parallel Processing

```yaml
performance:
  processing:
    enable_parallel: true
    max_parallel_processes: 4  # Adjust based on CPU cores
```

### 4. Caching

```yaml
performance:
  processing:
    enable_caching: true
```

### 5. Background Tasks

```yaml
task_management:
  enabled: true
  queue:
    max_queue_size: 100
    worker_threads: 4  # Adjust based on system
```

## Monitoring and Maintenance

### 1. Logging

Configure logging in `config/enhanced_webui_config.yaml`:

```yaml
logging:
  level: INFO
  file_path: logs/enhanced_webui.log
  rotation:
    enabled: true
    max_size_mb: 10
    backup_count: 5
```

### 2. Health Checks

Create health check script `scripts/health_check.py`:

```python
#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get('http://localhost:7860/health', timeout=10)
    if response.status_code == 200:
        print("Service healthy")
        sys.exit(0)
    else:
        print(f"Service unhealthy: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
```

### 3. Performance Monitoring

Monitor key metrics:
- Memory usage
- CPU usage
- GPU utilization (if applicable)
- Task queue length
- Response times

### 4. Log Rotation

Set up log rotation with logrotate:

```bash
# /etc/logrotate.d/indextts-webui
/var/log/indextts/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 indextts indextts
}
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: Missing optional dependencies
```
ImportError: No module named 'ebooklib'
```

**Solution**: Install optional dependencies or enable graceful degradation
```bash
# Install missing dependency
uv add ebooklib

# Or enable graceful degradation
export INDEXTTS_MOCK_DEPENDENCIES=true
```

#### 2. Memory Issues

**Problem**: Out of memory errors
```
RuntimeError: CUDA out of memory
```

**Solutions**:
- Reduce batch size
- Enable memory optimization
- Use CPU instead of GPU for large files
- Increase system RAM

#### 3. File Processing Errors

**Problem**: Encoding detection fails
```
UnicodeDecodeError: 'utf-8' codec can't decode
```

**Solution**: Configure fallback encodings
```yaml
file_processing:
  encoding:
    fallback_encodings: [gbk, gb2312, utf-16, latin1]
```

#### 4. Audio Format Issues

**Problem**: Audio conversion fails
```
Error: Could not convert to M4B format
```

**Solutions**:
- Install ffmpeg
- Check audio dependencies
- Use fallback format (WAV)

### Debug Mode

Enable debug mode for detailed logging:

```bash
export INDEXTTS_DEBUG=true
export INDEXTTS_LOG_LEVEL=DEBUG
uv run webui.py
```

### Performance Issues

If experiencing slow performance:

1. Check system resources
2. Enable parallel processing
3. Optimize memory settings
4. Use GPU acceleration
5. Reduce file sizes

### Getting Help

1. Check logs in `logs/enhanced_webui.log`
2. Run diagnostic tests: `uv run python -m pytest tests/test_runner.py --type regression`
3. Review configuration with: `uv run python -c "from indextts.config.env_config import get_config; print(get_config().validate_config())"`
4. Check dependency status: `uv run python -c "from indextts.config.graceful_degradation import get_dependency_manager; print(get_dependency_manager().get_degradation_report())"`

## Security Considerations

### 1. File Upload Security

- Limit file sizes
- Validate file types
- Scan uploaded files
- Use secure temporary directories

### 2. Network Security

- Use HTTPS in production
- Configure firewall rules
- Limit access to management interfaces
- Regular security updates

### 3. Data Privacy

- Secure voice samples
- Encrypt sensitive data
- Regular backups
- Access logging

## Backup and Recovery

### 1. Important Files to Backup

- Configuration files (`config/`)
- Voice samples (`samples/`)
- Generated outputs (`outputs/`)
- Model checkpoints (`checkpoints/`)
- Logs (`logs/`)

### 2. Backup Script

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/indextts/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r config/ "$BACKUP_DIR/"
cp -r samples/ "$BACKUP_DIR/"
cp -r outputs/ "$BACKUP_DIR/"
tar -czf "$BACKUP_DIR/logs.tar.gz" logs/

echo "Backup completed: $BACKUP_DIR"
```

### 3. Recovery Procedure

1. Stop the service
2. Restore configuration files
3. Restore voice samples
4. Restart the service
5. Verify functionality

This deployment guide provides comprehensive instructions for setting up and maintaining the Enhanced IndexTTS2 WebUI in various environments. Adjust the configurations based on your specific requirements and infrastructure.
---


## 中文

本指南提供了部署IndexTTS2及其所有功能和优化的全面说明。

## 目录

1. [系统要求](#系统要求)
2. [安装](#安装)
3. [配置](#配置)
4. [环境变量](#环境变量)
5. [部署选项](#部署选项)
6. [性能优化](#性能优化)
7. [监控和维护](#监控和维护)
8. [故障排除](#故障排除)

## 系统要求

### 最低要求

- **操作系统**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: 3.10或更高版本
- **内存**: 最低8GB，推荐16GB
- **存储**: 10GB可用空间（模型和输出需要更多）
- **GPU**: 推荐CUDA兼容GPU（可选）

### 推荐配置

- **内存**: 32GB用于大文件处理
- **存储**: SSD，50GB+可用空间
- **GPU**: NVIDIA GPU，8GB+显存
- **CPU**: 多核处理器（推荐8+核心）

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/IndexTeam/IndexTTS2.git
cd IndexTTS2
```

### 2. 安装UV包管理器

```bash
# 安装UV（如果尚未安装）
pip install -U uv
```

### 3. 安装依赖

```bash
# 安装所有依赖包括可选组件
uv sync --all-extras

# 或安装特定功能集
uv sync --extra webui --extra deepspeed
```

### 4. 下载模型

```bash
# 通过HuggingFace
uv tool install "huggingface_hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints

# 或通过ModelScope（中国）
uv tool install "modelscope"
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

### 5. 验证安装

```bash
# 运行系统检查
uv run tools/gpu_check.py

# 运行基础测试
uv run pytest tests/regression_test.py
```

## 配置

### 基本配置

IndexTTS2使用YAML配置文件进行设置。主要配置文件位于`checkpoints/config.yaml`。

### 关键配置选项

```yaml
# 模型配置
model:
  gpt_path: "checkpoints/gpt.pth"
  s2mel_path: "checkpoints/s2mel.pth"
  bigvgan_path: "checkpoints/bigvgan.pth"

# 音频设置
audio:
  sample_rate: 22050
  hop_length: 256
  win_length: 1024

# 推理设置
inference:
  fp16: true
  use_cuda_kernel: true
  batch_size: 1
```

## 部署选项

### 1. 本地开发

```bash
# 使用默认设置运行
uv run webui.py

# 使用自定义端口
uv run webui.py --port 8080

# 启用调试模式
uv run webui.py --debug
```

### 2. 生产服务器

#### 使用Systemd（Linux）

创建服务文件`/etc/systemd/system/indextts.service`：

```ini
[Unit]
Description=IndexTTS2 Web Interface
After=network.target

[Service]
Type=simple
User=indextts
WorkingDirectory=/opt/IndexTTS2
ExecStart=/opt/IndexTTS2/.venv/bin/python webui.py --host 0.0.0.0 --port 7860
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl enable indextts
sudo systemctl start indextts
sudo systemctl status indextts
```

### 3. Docker部署

创建`Dockerfile`：

```dockerfile
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装UV
RUN pip install -U uv

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --all-extras

# 创建目录
RUN mkdir -p outputs prompts

# 暴露端口
EXPOSE 7860

# 运行应用
CMD ["uv", "run", "webui.py", "--host", "0.0.0.0", "--port", "7860"]
```

构建并运行：
```bash
docker build -t indextts2 .
docker run -p 7860:7860 -v ./outputs:/app/outputs indextts2
```

## 性能优化

### 1. GPU优化

```bash
# 启用CUDA内核
export CUDA_VISIBLE_DEVICES=0
uv run webui.py --cuda_kernel --fp16
```

### 2. 内存优化

- 使用FP16推理减少显存使用
- 启用梯度检查点
- 调整批处理大小

### 3. CPU优化

- 使用多线程处理
- 启用MKLDNN优化
- 调整工作进程数量

## 监控和维护

### 1. 日志记录

日志文件位置：
- 应用日志：`logs/webui.log`
- 错误日志：`logs/error.log`
- 访问日志：`logs/access.log`

### 2. 健康检查

创建健康检查脚本：

```python
#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get('http://localhost:7860/health', timeout=10)
    if response.status_code == 200:
        print("服务正常")
        sys.exit(0)
    else:
        print(f"服务异常: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"健康检查失败: {e}")
    sys.exit(1)
```

### 3. 性能监控

监控关键指标：
- 内存使用率
- CPU使用率
- GPU利用率（如适用）
- 响应时间
- 错误率

## 故障排除

### 常见问题

#### 1. 导入错误

**问题**: 缺少依赖包
```
ImportError: No module named 'xxx'
```

**解决方案**: 重新安装依赖
```bash
uv sync --all-extras
```

#### 2. 内存不足

**问题**: CUDA内存不足
```
RuntimeError: CUDA out of memory
```

**解决方案**:
- 使用`--fp16`标志
- 减少批处理大小
- 使用CPU推理

#### 3. 模型加载失败

**问题**: 找不到模型文件
```
FileNotFoundError: checkpoints/gpt.pth
```

**解决方案**: 重新下载模型
```bash
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
```

### 调试模式

启用调试模式获取详细日志：

```bash
uv run webui.py --debug --log-level DEBUG
```

### 获取帮助

1. 检查日志文件
2. 运行诊断测试
3. 查看配置文件
4. 检查系统资源

## 安全考虑

### 1. 网络安全

- 在生产环境中使用HTTPS
- 配置防火墙规则
- 限制管理接口访问
- 定期安全更新

### 2. 数据隐私

- 保护语音样本
- 加密敏感数据
- 定期备份
- 访问日志记录

## 备份和恢复

### 1. 重要文件备份

- 配置文件（`checkpoints/config.yaml`）
- 语音样本（`examples/`）
- 生成输出（`outputs/`）
- 模型检查点（`checkpoints/`）

### 2. 备份脚本

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/indextts2/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r checkpoints/ "$BACKUP_DIR/"
cp -r examples/ "$BACKUP_DIR/"
cp -r outputs/ "$BACKUP_DIR/"

echo "备份完成: $BACKUP_DIR"
```

### 3. 恢复程序

1. 停止服务
2. 恢复配置文件
3. 恢复模型文件
4. 重启服务
5. 验证功能

本部署指南提供了在各种环境中设置和维护IndexTTS2的全面说明。请根据您的具体要求和基础设施调整配置。