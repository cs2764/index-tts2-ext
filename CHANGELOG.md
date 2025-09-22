# Changelog / 更新日志

[English](#english) | [中文](#中文)

---

## English

All notable changes to IndexTTS2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### [2.1.0] - 2025-09-22

#### Added
- **Enhanced Web UI**: Completely redesigned user interface with improved layout, controls, and user experience
- **Auto-Save System**: Intelligent automatic saving of generated audio during long synthesis processes with progress tracking
- **Advanced Audio Format Support**: Enhanced MP3, M4A, M4B conversion and format handling with error recovery
- **Performance Monitoring**: Real-time performance metrics, memory usage tracking, and optimization suggestions
- **Comprehensive Testing Suite**: Extensive test coverage for all major components with regression testing
- **GitHub Preparation Tools**: Automated tools for repository management, cleanup, and professional project structure
- **Audio Input Optimization**: Automatic trimming of input audio to 15 seconds to prevent memory overflow
- **Parameter Normalization**: Automatic normalization of synthesis parameters to recommended ranges for better user experience
- **Docker Support**: Complete containerization with health checks and multi-platform support
- **CI/CD Pipeline**: Automated testing and deployment with multi-platform compatibility

#### Enhanced
- **Emotion Control**: Improved emotion understanding with fine-tuned Qwen model and vector-based emotion mapping
- **Duration Control**: More precise timing control for autoregressive synthesis with millisecond accuracy
- **Error Handling**: Robust error recovery system with user-friendly feedback and graceful degradation
- **Documentation**: Comprehensive bilingual documentation (English/Chinese) with API reference and deployment guides
- **Code Organization**: Modular architecture with improved maintainability and separation of concerns
- **Memory Management**: Intelligent VRAM usage optimization and automatic memory cleanup
- **Audio Processing Pipeline**: Enhanced audio processing with better quality control and format validation

#### Fixed
- **Audio Processing**: Resolved MP3 encoding issues, format conversion bugs, and audio length validation
- **Memory Management**: Fixed VRAM overflow issues with long audio inputs and optimized memory cleanup
- **UI Responsiveness**: Fixed interface freezing during long operations with proper progress indicators
- **File Management**: Improved temporary file cleanup and resource management with automatic cleanup
- **Sample Audio Issues**: Fixed errors with overly long sample audio by implementing automatic trimming
- **Parameter Validation**: Enhanced parameter validation and normalization for better synthesis quality

#### Technical Improvements
- **Dependencies**: Updated to PyTorch 2.8+ with CUDA 12.8+ support and optimized dependency management
- **Package Management**: Complete migration to UV package manager with locked dependencies
- **Testing Infrastructure**: Comprehensive validation and regression testing with automated CI/CD
- **Performance**: Significantly optimized inference speed and resource utilization
- **FP16 Support**: Enhanced FP16 inference support for faster processing and reduced VRAM usage
- **Multi-Platform Support**: Improved compatibility across Windows, Linux, and macOS
- **Security**: Added security policy and vulnerability reporting system

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

### [2.1.0] - 2025年9月22日

#### 新增功能
- **增强Web界面**: 完全重新设计的用户界面，改进的布局、控件和用户体验
- **自动保存系统**: 智能自动保存生成的音频，支持长时间合成过程的进度跟踪
- **高级音频格式支持**: 增强的MP3、M4A、M4B转换和格式处理，支持错误恢复
- **性能监控**: 实时性能指标、内存使用跟踪和优化建议
- **全面测试套件**: 所有主要组件的广泛测试覆盖，包含回归测试
- **GitHub准备工具**: 用于仓库管理、清理和专业项目结构的自动化工具
- **音频输入优化**: 自动将输入音频裁剪至15秒以防止内存溢出
- **参数归一化**: 自动将合成参数归一化到推荐范围，改善用户体验
- **Docker支持**: 完整的容器化支持，包含健康检查和多平台支持
- **CI/CD流水线**: 自动化测试和部署，支持多平台兼容性

#### 功能增强
- **情感控制**: 通过微调Qwen模型和基于向量的情感映射改进情感理解
- **时长控制**: 自回归合成的更精确时序控制，支持毫秒级精度
- **错误处理**: 强大的错误恢复系统，用户友好的反馈和优雅降级
- **文档**: 全面的双语文档（英文/中文），包含API参考和部署指南
- **代码组织**: 模块化架构，提高可维护性和关注点分离
- **内存管理**: 智能显存使用优化和自动内存清理
- **音频处理流水线**: 增强的音频处理，更好的质量控制和格式验证

#### 问题修复
- **音频处理**: 解决MP3编码问题、格式转换错误和音频长度验证
- **内存管理**: 修复长音频输入的显存溢出问题，优化内存清理
- **界面响应**: 修复长时间操作期间的界面冻结，添加适当的进度指示器
- **文件管理**: 改进临时文件清理和资源管理，支持自动清理
- **样本音频问题**: 通过实现自动裁剪修复过长样本音频的错误
- **参数验证**: 增强参数验证和归一化，提高合成质量

#### 技术改进
- **依赖项**: 更新至PyTorch 2.8+，支持CUDA 12.8+和优化的依赖管理
- **包管理**: 完全迁移至UV包管理器，支持锁定依赖
- **测试基础设施**: 全面的验证和回归测试，支持自动化CI/CD
- **性能**: 显著优化推理速度和资源利用率
- **FP16支持**: 增强的FP16推理支持，更快的处理和减少显存使用
- **多平台支持**: 改进Windows、Linux和macOS的兼容性
- **安全性**: 添加安全策略和漏洞报告系统

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