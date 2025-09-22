# Security Policy / 安全政策

[English](#english) | [中文](#中文)

---

## English

## Supported Versions

We actively support the following versions of IndexTTS2 with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in IndexTTS2, please report it responsibly.

### How to Report

1. **Email**: Send details to [security@indexteam.ai](mailto:security@indexteam.ai)
2. **GitHub**: Create a private security advisory on GitHub
3. **Encrypted Communication**: Use our PGP key for sensitive information

### What to Include

Please include the following information in your report:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and severity assessment
- **Reproduction**: Step-by-step instructions to reproduce
- **Environment**: System details where vulnerability was found
- **Proof of Concept**: Code or screenshots demonstrating the issue
- **Suggested Fix**: If you have ideas for remediation

### Response Timeline

- **Initial Response**: Within 24 hours
- **Assessment**: Within 72 hours
- **Fix Development**: 1-2 weeks for critical issues
- **Public Disclosure**: After fix is released and users have time to update

### Security Best Practices

When using IndexTTS2, please follow these security guidelines:

#### Input Validation
- Validate all text inputs for malicious content
- Sanitize file uploads and paths
- Limit file sizes and types for uploads

#### Network Security
- Use HTTPS in production environments
- Implement proper authentication for web interfaces
- Configure firewalls to restrict access

#### Data Protection
- Encrypt sensitive voice data at rest
- Use secure channels for data transmission
- Implement proper access controls

#### System Security
- Keep dependencies updated
- Use virtual environments
- Monitor system resources and logs

### Known Security Considerations

#### Audio File Processing
- Audio files are processed using external libraries
- Malformed audio files could potentially cause issues
- Always validate audio file formats and sources

#### Model Files
- Model checkpoints should be downloaded from trusted sources
- Verify checksums when available
- Be cautious with custom or third-party models

#### Web Interface
- The web interface should not be exposed to untrusted networks
- Implement rate limiting for API endpoints
- Validate all user inputs

### Vulnerability Disclosure Policy

We follow responsible disclosure practices:

1. **Private Reporting**: Report vulnerabilities privately first
2. **Coordinated Disclosure**: Work with us to develop fixes
3. **Public Disclosure**: Announce fixes after users can update
4. **Credit**: Security researchers will be credited (if desired)

### Security Updates

Security updates are distributed through:

- **GitHub Releases**: Tagged security releases
- **Package Managers**: Updated packages on PyPI
- **Security Advisories**: GitHub security advisories
- **Documentation**: Updated security guidelines

---

## 中文

## 支持的版本

我们积极支持以下IndexTTS2版本的安全更新：

| 版本    | 支持状态           |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## 报告漏洞

我们认真对待安全漏洞。如果您在IndexTTS2中发现安全漏洞，请负责任地报告。

### 如何报告

1. **邮件**: 发送详情至 [security@indexteam.ai](mailto:security@indexteam.ai)
2. **GitHub**: 在GitHub上创建私有安全建议
3. **加密通信**: 对敏感信息使用我们的PGP密钥

### 包含的信息

请在报告中包含以下信息：

- **描述**: 漏洞的清晰描述
- **影响**: 潜在影响和严重性评估
- **重现**: 重现的分步说明
- **环境**: 发现漏洞的系统详情
- **概念验证**: 演示问题的代码或截图
- **建议修复**: 如果您有修复想法

### 响应时间表

- **初始响应**: 24小时内
- **评估**: 72小时内
- **修复开发**: 关键问题1-2周
- **公开披露**: 修复发布后，用户有时间更新

### 安全最佳实践

使用IndexTTS2时，请遵循这些安全指南：

#### 输入验证
- 验证所有文本输入是否包含恶意内容
- 清理文件上传和路径
- 限制上传的文件大小和类型

#### 网络安全
- 在生产环境中使用HTTPS
- 为Web界面实施适当的身份验证
- 配置防火墙限制访问

#### 数据保护
- 静态加密敏感语音数据
- 使用安全通道进行数据传输
- 实施适当的访问控制

#### 系统安全
- 保持依赖项更新
- 使用虚拟环境
- 监控系统资源和日志

### 已知安全考虑

#### 音频文件处理
- 音频文件使用外部库处理
- 格式错误的音频文件可能导致问题
- 始终验证音频文件格式和来源

#### 模型文件
- 模型检查点应从可信来源下载
- 在可用时验证校验和
- 谨慎使用自定义或第三方模型

#### Web界面
- Web界面不应暴露给不可信网络
- 为API端点实施速率限制
- 验证所有用户输入

### 漏洞披露政策

我们遵循负责任的披露实践：

1. **私人报告**: 首先私下报告漏洞
2. **协调披露**: 与我们合作开发修复
3. **公开披露**: 用户可以更新后宣布修复
4. **致谢**: 安全研究人员将获得致谢（如需要）

### 安全更新

安全更新通过以下方式分发：

- **GitHub发布**: 标记的安全发布
- **包管理器**: PyPI上的更新包
- **安全建议**: GitHub安全建议
- **文档**: 更新的安全指南