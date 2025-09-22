# IndexTTS2 Windows 部署启动指南

本文档详细介绍如何在 Windows 系统下部署和启动 IndexTTS2 项目。

## 系统要求

- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.10 或更高版本
- **GPU**: NVIDIA GPU (推荐，支持 CUDA 12.9)
- **内存**: 至少 8GB RAM (推荐 16GB 或更多)
- **存储**: 至少 10GB 可用空间

## 前置条件

### 1. 安装 Git 和 Git LFS

1. 下载并安装 [Git for Windows](https://git-scm.com/downloads)
2. 下载并安装 [Git LFS](https://git-lfs.com/)
3. 在命令提示符中启用 Git LFS：

```cmd
git lfs install
```

### 2. 安装 CUDA Toolkit (可选但推荐)

如果您有 NVIDIA GPU，建议安装 CUDA Toolkit 12.9：

1. 访问 [NVIDIA CUDA Toolkit 下载页面](https://developer.nvidia.com/cuda-toolkit)
2. 下载并安装 CUDA Toolkit 12.9 或更新版本

## 项目部署步骤

### 步骤 1: 克隆项目

打开命令提示符或 PowerShell，执行以下命令：

```cmd
git clone https://github.com/index-tts/index-tts.git
cd index-tts
git lfs pull
```

### 步骤 2: 安装 UV 包管理器

UV 是现代化的 Python 包管理器，比 pip 快 115 倍：

```cmd
pip install -U uv
```

### 步骤 3: 创建虚拟环境

在项目目录中创建虚拟环境：

```cmd
uv venv
```

激活虚拟环境：

```cmd
.venv\Scripts\activate
```

### 步骤 4: 安装依赖

**重要提示 (Windows 用户)**: DeepSpeed 库在某些 Windows 系统上可能难以安装。建议使用以下命令安装：

```cmd
uv sync --extra webui
```

如果您想要完整功能（包括 DeepSpeed），可以尝试：

```cmd
uv sync --all-extras
```

如果安装过程中遇到网络问题，可以使用国内镜像：

```cmd
uv sync --extra webui --default-index "https://mirrors.aliyun.com/pypi/simple"
```

或者：

```cmd
uv sync --extra webui --default-index "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
```

### 步骤 5: 安装 PyTorch (CUDA 12.9 版本)

为了获得最佳性能，建议安装支持 CUDA 12.9 的 PyTorch：

```cmd
uv pip uninstall torch torchvision torchaudio
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu129
```

### 步骤 6: 下载模型

#### 方法 1: 使用 HuggingFace CLI

```cmd
uv tool install "huggingface_hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
```

#### 方法 2: 使用 ModelScope (推荐中国用户)

```cmd
uv tool install "modelscope"
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

### 步骤 7: 检查 GPU 加速

运行以下命令检查 GPU 是否正确配置：

```cmd
uv run tools/gpu_check.py
```

## 启动项目

### 启动 Web 界面 (推荐)

```cmd
uv run webui.py
```

启动后，在浏览器中访问 `http://127.0.0.1:7860` 即可使用 Web 界面。

### 启动参数选项

您可以使用以下参数优化性能：

```cmd
# 启用 FP16 推理 (降低显存使用)
uv run webui.py --fp16

# 启用 CUDA 内核优化
uv run webui.py --cuda_kernel

# 启用 DeepSpeed 加速 (如果已安装)
uv run webui.py --deepspeed

# 组合使用多个参数
uv run webui.py --fp16 --cuda_kernel
```

查看所有可用参数：

```cmd
uv run webui.py -h
```

### 命令行使用

如果您想通过命令行使用 IndexTTS2：

```cmd
uv run indextts/cli.py "Hello world" -v examples/voice_01.wav
```

## 常见问题解决

### 1. DeepSpeed 安装失败

如果 DeepSpeed 安装失败，请使用：

```cmd
uv sync --extra webui
```

这将跳过 DeepSpeed 但保留其他功能。

### 2. CUDA 相关错误

确保已安装 CUDA Toolkit 12.9 或更新版本，并重新安装 PyTorch：

```cmd
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu129
```

### 3. torchvision InterpolationMode 导入错误

如果遇到 `ImportError: cannot import name 'InterpolationMode' from 'torchvision.transforms'` 错误，说明 torchvision 版本过旧。解决方法：

```cmd
# 卸载旧版本
uv pip uninstall torch torchvision torchaudio

# 重新安装正确版本
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu129
```

验证安装：

```cmd
python -c "from torchvision.transforms import InterpolationMode; print('Success')"
```

### 4. 网络下载缓慢

对于中国用户，可以设置 HuggingFace 镜像：

```cmd
set HF_ENDPOINT=https://hf-mirror.com
```

### 5. 内存不足

如果遇到内存不足问题，建议：

- 使用 `--fp16` 参数启动
- 关闭其他占用内存的程序
- 考虑升级系统内存

## 性能优化建议

1. **使用 FP16**: 启用 `--fp16` 可以显著降低显存使用并提高速度
2. **CUDA 内核**: 使用 `--cuda_kernel` 可以加速 BigVGAN 处理
3. **DeepSpeed**: 在某些系统上可能提供额外加速，但效果因硬件而异
4. **批处理**: 对于大量音频生成，考虑批量处理以提高效率

## 验证安装

运行以下命令验证安装是否成功：

```cmd
uv run tests/regression_test.py
```

如果测试通过，说明安装配置正确。

## 技术支持

如果遇到问题，可以：

1. 查看项目的 [GitHub Issues](https://github.com/index-tts/index-tts/issues)
2. 加入 QQ 群：553460296 或 663272642
3. 加入 Discord：<https://discord.gg/uT32E7KDmy>
4. 发送邮件至：<indexspeech@bilibili.com>

---

**注意**: 本指南基于 IndexTTS2 项目的最新版本编写。如果您使用的是不同版本，某些步骤可能会有所不同。
