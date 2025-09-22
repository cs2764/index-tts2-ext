# Contributing to IndexTTS2 / 贡献指南

[English](#english) | [中文](#中文)

---

## English

Thank you for your interest in contributing to IndexTTS2! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- CUDA 12.8+ (for GPU acceleration)
- UV package manager
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/IndexTTS2.git
   cd IndexTTS2
   ```

2. **Install Dependencies**
   ```bash
   # Install UV package manager
   pip install -U uv
   
   # Install all dependencies including dev tools
   uv sync --all-extras --group dev
   ```

3. **Download Models**
   ```bash
   # Via HuggingFace
   uv tool install "huggingface_hub[cli]"
   hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
   ```

4. **Run Tests**
   ```bash
   # Run all tests
   uv run pytest tests/
   
   # Run specific test categories
   uv run pytest tests/test_inference.py
   ```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and modular

### Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting PR
- Include both unit tests and integration tests
- Test with different audio formats and languages

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update CHANGELOG.md with your changes
- Provide examples for new features

## 🔄 Contribution Process

### 1. Create an Issue

Before starting work, create an issue to discuss:
- Bug reports with reproduction steps
- Feature requests with use cases
- Performance improvements with benchmarks

### 2. Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, well-documented code
   - Add appropriate tests
   - Update documentation

3. **Test Your Changes**
   ```bash
   # Run tests
   uv run pytest tests/
   
   # Check code style
   uv run black --check .
   uv run flake8 .
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new emotion control feature"
   ```

### 3. Submit Pull Request

1. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Provide clear description of changes
   - Reference related issues
   - Include test results
   - Add screenshots for UI changes

## 🎯 Areas for Contribution

### High Priority
- **Performance Optimization**: Improve inference speed and memory usage
- **Audio Quality**: Enhance output quality and format support
- **Emotion Control**: Expand emotion categories and accuracy
- **Documentation**: Improve tutorials and examples

### Medium Priority
- **Language Support**: Add support for more languages
- **Model Compression**: Reduce model size while maintaining quality
- **Web UI**: Enhance user interface and experience
- **Testing**: Expand test coverage and automation

### Low Priority
- **Code Refactoring**: Improve code organization and maintainability
- **Utilities**: Add helpful tools and scripts
- **Examples**: Create more usage examples and demos

## 🐛 Bug Reports

When reporting bugs, please include:

- **Environment**: OS, Python version, CUDA version
- **Steps to Reproduce**: Clear, minimal reproduction steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Error Messages**: Full error logs and stack traces
- **Audio Files**: Sample inputs that cause the issue

## 💡 Feature Requests

For feature requests, please provide:

- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other ways to achieve the goal
- **Examples**: Similar features in other projects

## 📋 Code Review Process

All contributions go through code review:

1. **Automated Checks**: CI/CD runs tests and style checks
2. **Maintainer Review**: Core team reviews code quality and design
3. **Community Feedback**: Other contributors may provide input
4. **Approval**: Changes are merged after approval

## 🏆 Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- GitHub contributors page

---

## 中文

感谢您对IndexTTS2项目的贡献兴趣！本文档提供了项目贡献指南。

## 🚀 开始贡献

### 前置要求

- Python 3.10或更高版本
- CUDA 12.8+（用于GPU加速）
- UV包管理器
- Git

### 开发环境设置

1. **Fork并克隆**
   ```bash
   git clone https://github.com/your-username/IndexTTS2.git
   cd IndexTTS2
   ```

2. **安装依赖**
   ```bash
   # 安装UV包管理器
   pip install -U uv
   
   # 安装所有依赖包括开发工具
   uv sync --all-extras --group dev
   ```

3. **下载模型**
   ```bash
   # 通过HuggingFace
   uv tool install "huggingface_hub[cli]"
   hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
   ```

4. **运行测试**
   ```bash
   # 运行所有测试
   uv run pytest tests/
   
   # 运行特定测试类别
   uv run pytest tests/test_inference.py
   ```

## 📝 开发指南

### 代码风格

- 遵循PEP 8 Python风格指南
- 适当使用类型提示
- 为所有公共函数和类编写文档字符串
- 保持函数专注和模块化

### 测试

- 为新功能和错误修复编写测试
- 提交PR前确保所有测试通过
- 包括单元测试和集成测试
- 测试不同音频格式和语言

### 文档

- 为面向用户的更改更新README.md
- 为新函数和类添加文档字符串
- 在CHANGELOG.md中更新您的更改
- 为新功能提供示例

## 🔄 贡献流程

### 1. 创建Issue

开始工作前，创建issue讨论：
- 带有重现步骤的错误报告
- 带有用例的功能请求
- 带有基准测试的性能改进

### 2. 开发工作流

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行更改**
   - 编写清洁、文档完善的代码
   - 添加适当的测试
   - 更新文档

3. **测试更改**
   ```bash
   # 运行测试
   uv run pytest tests/
   
   # 检查代码风格
   uv run black --check .
   uv run flake8 .
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new emotion control feature"
   ```

### 3. 提交Pull Request

1. **推送到您的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **创建Pull Request**
   - 提供清晰的更改描述
   - 引用相关issues
   - 包含测试结果
   - 为UI更改添加截图

## 🎯 贡献领域

### 高优先级
- **性能优化**: 提高推理速度和内存使用
- **音频质量**: 增强输出质量和格式支持
- **情感控制**: 扩展情感类别和准确性
- **文档**: 改进教程和示例

### 中优先级
- **语言支持**: 添加更多语言支持
- **模型压缩**: 在保持质量的同时减少模型大小
- **Web界面**: 增强用户界面和体验
- **测试**: 扩展测试覆盖和自动化

### 低优先级
- **代码重构**: 改进代码组织和可维护性
- **实用工具**: 添加有用的工具和脚本
- **示例**: 创建更多使用示例和演示

## 🐛 错误报告

报告错误时，请包含：

- **环境**: 操作系统、Python版本、CUDA版本
- **重现步骤**: 清晰、最小的重现步骤
- **预期行为**: 应该发生什么
- **实际行为**: 实际发生了什么
- **错误消息**: 完整的错误日志和堆栈跟踪
- **音频文件**: 导致问题的示例输入

## 💡 功能请求

对于功能请求，请提供：

- **用例**: 为什么需要这个功能？
- **建议解决方案**: 它应该如何工作？
- **替代方案**: 实现目标的其他方式
- **示例**: 其他项目中的类似功能

## 📋 代码审查流程

所有贡献都经过代码审查：

1. **自动检查**: CI/CD运行测试和风格检查
2. **维护者审查**: 核心团队审查代码质量和设计
3. **社区反馈**: 其他贡献者可能提供意见
4. **批准**: 批准后合并更改

## 🏆 贡献认可

贡献者将在以下位置得到认可：
- CHANGELOG.md中的重要贡献
- README.md贡献者部分
- GitHub贡献者页面