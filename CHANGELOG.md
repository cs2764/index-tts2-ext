# Changelog / 更新日志

[English](#english) | [中文](#中文)

---

## English

All notable changes to IndexTTS2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [2.1.0] - 2025-09-21

#### Added
- **Enhanced Web UI**: Improved user interface with better layout and controls
- **Auto-Save System**: Automatic saving of generated audio during long synthesis processes
- **Advanced Audio Format Support**: Enhanced MP3 conversion and format handling
- **Performance Monitoring**: Real-time performance metrics and optimization suggestions
- **Comprehensive Testing Suite**: Extensive test coverage for all major components
- **GitHub Preparation Tools**: Automated tools for repository management and cleanup

#### Enhanced
- **Emotion Control**: Improved emotion understanding with fine-tuned Qwen model
- **Duration Control**: More precise timing control for autoregressive synthesis
- **Error Handling**: Better error recovery and user feedback systems
- **Documentation**: Comprehensive bilingual documentation (English/Chinese)
- **Code Organization**: Modular architecture with improved maintainability

#### Fixed
- **Audio Processing**: Resolved MP3 encoding issues and format conversion bugs
- **Memory Management**: Optimized VRAM usage and memory cleanup
- **UI Responsiveness**: Fixed interface freezing during long operations
- **File Management**: Improved temporary file cleanup and resource management

#### Technical Improvements
- **Dependencies**: Updated to PyTorch 2.8+ with CUDA 12.8+ support
- **Package Management**: Full migration to UV package manager
- **Testing Infrastructure**: Comprehensive validation and regression testing
- **Performance**: Optimized inference speed and resource utilization

### [2.0.2] - 2025-09-20

#### Fixed
- Initial bug fixes and stability improvements
- Basic audio format handling

### [2.0.0] - 2025-09-15

#### Added
- Initial release of IndexTTS2
- Zero-shot voice cloning capability
- Multi-modal emotion control system
- Autoregressive architecture with duration control
- Multilingual support (Chinese/English)
- BigVGAN vocoder integration

---

## 中文

IndexTTS2的所有重要更改都将记录在此文件中。

格式基于[Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循[语义化版本控制](https://semver.org/spec/v2.0.0.html)。

### [2.1.0] - 2025年9月21日

#### 新增功能
- **增强Web界面**: 改进的用户界面，更好的布局和控件
- **自动保存系统**: 在长时间合成过程中自动保存生成的音频
- **高级音频格式支持**: 增强的MP3转换和格式处理
- **性能监控**: 实时性能指标和优化建议
- **全面测试套件**: 所有主要组件的广泛测试覆盖
- **GitHub准备工具**: 用于仓库管理和清理的自动化工具

#### 功能增强
- **情感控制**: 通过微调Qwen模型改进情感理解
- **时长控制**: 自回归合成的更精确时序控制
- **错误处理**: 更好的错误恢复和用户反馈系统
- **文档**: 全面的双语文档（英文/中文）
- **代码组织**: 模块化架构，提高可维护性

#### 问题修复
- **音频处理**: 解决MP3编码问题和格式转换错误
- **内存管理**: 优化显存使用和内存清理
- **界面响应**: 修复长时间操作期间的界面冻结
- **文件管理**: 改进临时文件清理和资源管理

#### 技术改进
- **依赖项**: 更新至PyTorch 2.8+，支持CUDA 12.8+
- **包管理**: 完全迁移至UV包管理器
- **测试基础设施**: 全面的验证和回归测试
- **性能**: 优化推理速度和资源利用率

### [2.0.2] - 2025年9月20日

#### 问题修复
- 初始错误修复和稳定性改进
- 基本音频格式处理

### [2.0.0] - 2025年9月15日

#### 新增功能
- IndexTTS2初始发布
- 零样本语音克隆能力
- 多模态情感控制系统
- 具有时长控制的自回归架构
- 多语言支持（中文/英文）
- BigVGAN声码器集成