# Enhanced WebUI Deployment Guide

This guide covers the deployment of the Enhanced IndexTTS2 WebUI with all new features including file preview, automatic processing, dark theme support, and performance optimizations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Environment Variables](#environment-variables)
4. [Deployment Methods](#deployment-methods)
5. [Feature Configuration](#feature-configuration)
6. [Performance Tuning](#performance-tuning)
7. [Troubleshooting](#troubleshooting)
8. [Monitoring](#monitoring)

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended for large files)
- **Storage**: At least 10GB free space for models and outputs
- **GPU**: CUDA-compatible GPU recommended for optimal performance

### Required Dependencies

The enhanced WebUI requires all standard IndexTTS2 dependencies plus additional packages for enhanced features:

```bash
# Core dependencies (handled by pyproject.toml)
- gradio >= 5.44
- torch >= 2.8
- pyyaml
- chardet (for encoding detection)
- ebooklib (for EPUB support)
- psutil (for performance monitoring)

# Optional dependencies for enhanced features
- pillow (for image processing)
- ffmpeg-python (for advanced audio processing)
```

### Installation

1. **Using UV (Recommended)**:
   ```bash
   # Install UV if not already installed
   pip install -U uv
   
   # Install all dependencies including enhanced features
   uv sync --all-extras
   ```

2. **Using Pip**:
   ```bash
   pip install -e .
   ```

## Configuration

### Configuration File

The enhanced WebUI uses `config/enhanced_webui_config.yaml` for configuration. This file contains all settings for enhanced features.

#### Key Configuration Sections

1. **Enhanced Features Control**:
   ```yaml
   enhanced_features:
     enabled: true  # Master switch for all enhanced features
   ```

2. **File Processing**:
   ```yaml
   file_processing:
     max_file_size_mb: 100
     preview:
       max_lines: 40
       enable_caching: true
   ```

3. **UI Theme**:
   ```yaml
   ui_theme:
     default_theme: auto  # auto, light, dark
   ```

4. **Performance**:
   ```yaml
   performance:
     enable_memory_optimization: true
     max_worker_threads: 4
   ```

### Configuration Management

The enhanced WebUI includes a sophisticated configuration management system:

```python
from indextts.config.enhanced_config_manager import get_enhanced_config

# Get configuration
config = get_enhanced_config()

# Check if a feature is enabled
if config.file_processing.enable_caching:
    # Use caching
    pass
```

## Environment Variables

You can override configuration settings using environment variables:

### Core Settings

```bash
# Enhanced features control
export INDEXTTS_ENABLE_ENHANCED_FEATURES=true

# File processing
export INDEXTTS_MAX_FILE_SIZE_MB=100
export INDEXTTS_PREVIEW_MAX_LINES=40

# Directories
export INDEXTTS_SAMPLES_DIRECTORY=samples
export INDEXTTS_OUTPUT_DIRECTORY=outputs

# Performance
export INDEXTTS_MAX_CONCURRENT_TASKS=3

# UI Theme
export INDEXTTS_DEFAULT_THEME=dark
```

### Production Settings

```bash
# Security
export INDEXTTS_ENABLE_FILE_VALIDATION=true
export INDEXTTS_MAX_UPLOAD_SIZE_MB=50

# Performance
export INDEXTTS_ENABLE_COMPRESSION=true
export INDEXTTS_CACHE_STATIC_ASSETS=true

# Logging
export INDEXTTS_LOG_LEVEL=INFO
export INDEXTTS_LOG_FILE=logs/enhanced_webui.log
```

## Deployment Methods

### Method 1: Automated Deployment Script

The easiest way to deploy is using the provided deployment script:

```bash
# Production deployment
python scripts/deploy_enhanced_webui.py --environment production

# Development deployment
python scripts/deploy_enhanced_webui.py --environment development

# Validation only (no deployment)
python scripts/deploy_enhanced_webui.py --validate-only
```

The deployment script will:
- Validate the environment
- Install dependencies
- Set up configuration
- Create startup scripts
- Run tests (optional)

### Method 2: Manual Deployment

1. **Validate Environment**:
   ```bash
   python scripts/deploy_enhanced_webui.py --validate-only
   ```

2. **Install Dependencies**:
   ```bash
   uv sync --all-extras
   ```

3. **Configure Settings**:
   - Copy `config/enhanced_webui_config.yaml` to your desired location
   - Modify settings as needed
   - Set environment variables

4. **Create Directories**:
   ```bash
   mkdir -p samples outputs logs temp
   ```

5. **Start the WebUI**:
   ```bash
   python webui.py
   ```

### Method 3: Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --all-extras

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p samples outputs logs temp

# Set environment variables
ENV INDEXTTS_ENVIRONMENT=production
ENV INDEXTTS_SAMPLES_DIRECTORY=/app/samples
ENV INDEXTTS_OUTPUT_DIRECTORY=/app/outputs

# Expose port
EXPOSE 7860

# Start command
CMD ["python", "webui.py", "--server-name", "0.0.0.0"]
```

Build and run:

```bash
docker build -t indextts-enhanced .
docker run -p 7860:7860 -v $(pwd)/samples:/app/samples -v $(pwd)/outputs:/app/outputs indextts-enhanced
```

## Feature Configuration

### File Processing Features

#### File Upload and Preview

```yaml
file_processing:
  # Maximum file size for upload
  max_file_size_mb: 100
  
  # Preview settings
  preview:
    max_lines: 40           # Lines to show in preview
    enable_caching: true    # Cache previews for performance
    cache_max_entries: 100  # Maximum cached previews
    cache_max_age_hours: 24 # Cache expiration time
  
  # Supported file formats
  supported_formats:
    - txt
    - epub
  
  # Text cleaning (enabled by default)
  text_cleaning:
    enabled_by_default: true
    merge_empty_lines: true
    remove_excess_whitespace: true
    clean_special_characters: true
```

#### Chapter Recognition

```yaml
chapter_recognition:
  enabled_by_default: false    # Disabled by default
  confidence_threshold: 0.7    # Minimum confidence for chapter detection
  max_chapters_to_display: 10  # Maximum chapters to show in preview
  
  # Chapter patterns for different languages
  patterns:
    chinese:
      - "第[一二三四五六七八九十\\d]+章\\s+[^\\n]+"
      - "第[一二三四五六七八九十\\d]+回\\s+[^\\n]+"
    english:
      - "Chapter\\s+\\d+[:\\s]+[^\\n]+"
      - "Part\\s+\\d+[:\\s]+[^\\n]+"
```

### Audio Format Features

```yaml
audio_formats:
  default_format: mp3
  
  # MP3 settings
  mp3:
    default_bitrate: 64
    supported_bitrates: [32, 64, 96, 128, 192, 256, 320]
  
  # M4B audiobook settings
  m4b:
    enable_chapters: true
    enable_cover_art: true
  
  # Segmentation settings
  segmentation:
    default_chapters_per_file: 20
    max_chapters_per_file: 200
    epub_only_when_chapter_recognition_disabled: true
```

### UI Theme Features

```yaml
ui_theme:
  default_theme: auto  # auto, light, dark
  
  # Dark theme colors
  dark_theme:
    primary_bg: "#1f2937"
    secondary_bg: "#374151"
    primary_text: "#f9fafb"
    accent_color: "#3b82f6"
    success_color: "#10b981"
    error_color: "#ef4444"
  
  # Component styling
  components:
    file_upload:
      border_radius: "8px"
      padding: "16px"
    
    preview_area:
      max_height: "400px"
      font_family: "monospace"
```

### Performance Features

```yaml
performance:
  # Memory management
  memory:
    enable_optimization: true
    max_memory_usage_percent: 80
  
  # Caching
  caching:
    enable_preview_cache: true
    enable_chapter_cache: true
  
  # Processing optimization
  processing:
    enable_parallel_processing: true
    max_worker_threads: 4
  
  # UI optimization
  ui:
    debounce_delay_ms: 300
    lazy_loading: true
```

## Performance Tuning

### Memory Optimization

1. **Adjust Memory Limits**:
   ```yaml
   performance:
     memory:
       max_memory_usage_percent: 80  # Adjust based on available RAM
   ```

2. **Enable Caching**:
   ```yaml
   performance:
     caching:
       enable_preview_cache: true
       enable_chapter_cache: true
   ```

3. **Optimize Processing**:
   ```yaml
   performance:
     processing:
       max_worker_threads: 4  # Adjust based on CPU cores
       chunk_size_lines: 1000
   ```

### File Processing Optimization

1. **Limit File Sizes**:
   ```yaml
   file_processing:
     max_file_size_mb: 100  # Adjust based on available memory
   ```

2. **Optimize Preview Generation**:
   ```yaml
   file_processing:
     preview:
       max_lines: 40  # Reduce for faster preview generation
   ```

### UI Performance

1. **Reduce Debounce Delay**:
   ```yaml
   performance:
     ui:
       debounce_delay_ms: 300  # Lower for more responsive UI
   ```

2. **Enable Lazy Loading**:
   ```yaml
   performance:
     ui:
       lazy_loading: true
   ```

## Troubleshooting

### Common Issues

#### 1. Enhanced Features Not Loading

**Symptoms**: Enhanced features are not visible in the UI

**Solutions**:
- Check if enhanced features are enabled in configuration:
  ```yaml
  enhanced_features:
    enabled: true
  ```
- Verify all dependencies are installed:
  ```bash
  uv sync --all-extras
  ```
- Check for import errors in logs

#### 2. File Upload Issues

**Symptoms**: Files cannot be uploaded or processed

**Solutions**:
- Check file size limits:
  ```yaml
  file_processing:
    max_file_size_mb: 100
  ```
- Verify file format support:
  ```yaml
  file_processing:
    supported_formats: [txt, epub]
  ```
- Check directory permissions for temp files

#### 3. Performance Issues

**Symptoms**: Slow preview generation or UI responsiveness

**Solutions**:
- Enable caching:
  ```yaml
  performance:
    caching:
      enable_preview_cache: true
  ```
- Adjust worker threads:
  ```yaml
  performance:
    processing:
      max_worker_threads: 4
  ```
- Reduce preview size:
  ```yaml
  file_processing:
    preview:
      max_lines: 20
  ```

#### 4. Theme Issues

**Symptoms**: Dark theme not working or poor contrast

**Solutions**:
- Check theme configuration:
  ```yaml
  ui_theme:
    default_theme: dark
  ```
- Verify CSS is loading properly
- Check browser compatibility

### Debug Mode

Enable debug mode for detailed logging:

```bash
export INDEXTTS_LOG_LEVEL=DEBUG
python webui.py
```

### Log Analysis

Check logs for errors:

```bash
# View recent logs
tail -f logs/enhanced_webui.log

# Search for errors
grep -i error logs/enhanced_webui.log

# Check performance metrics
grep -i performance logs/enhanced_webui.log
```

## Monitoring

### Health Checks

The enhanced WebUI includes built-in health checks:

1. **Configuration Validation**:
   ```bash
   python scripts/deploy_enhanced_webui.py --validate-only
   ```

2. **Feature Status**:
   ```python
   from indextts.config.enhanced_config_manager import get_enhanced_config
   
   config = get_enhanced_config()
   print(f"Enhanced features enabled: {config.enabled}")
   ```

3. **Performance Monitoring**:
   ```python
   from indextts.performance.preview_optimizer import PreviewOptimizer
   
   optimizer = PreviewOptimizer()
   report = optimizer.get_performance_report()
   print(report)
   ```

### Metrics Collection

Monitor key metrics:

- **Memory Usage**: Track memory consumption during file processing
- **Cache Performance**: Monitor cache hit rates for previews
- **Processing Times**: Track file processing and preview generation times
- **Error Rates**: Monitor failed operations and error frequencies

### Alerting

Set up alerts for:

- High memory usage (>90%)
- Low cache hit rates (<50%)
- Slow processing times (>5 seconds for small files)
- Frequent errors (>5% error rate)

## Production Considerations

### Security

1. **File Validation**: Enable strict file validation in production
2. **Size Limits**: Set appropriate file size limits
3. **Access Control**: Implement proper access controls
4. **Input Sanitization**: Ensure all user inputs are sanitized

### Scalability

1. **Load Balancing**: Use multiple instances behind a load balancer
2. **Caching**: Implement Redis or similar for shared caching
3. **File Storage**: Use shared storage for samples and outputs
4. **Database**: Consider using a database for task persistence

### Backup and Recovery

1. **Configuration Backup**: Regularly backup configuration files
2. **Model Backup**: Backup model checkpoints
3. **User Data**: Backup samples and outputs
4. **Recovery Procedures**: Document recovery procedures

## Support

For issues and support:

1. Check the [troubleshooting section](#troubleshooting)
2. Review logs for error messages
3. Validate configuration using the deployment script
4. Check GitHub issues for known problems
5. Create a new issue with detailed information

## Version Compatibility

This deployment guide is for Enhanced WebUI version 2.0+. For compatibility with different versions:

- **IndexTTS2 Core**: Compatible with all versions
- **Gradio**: Requires version 5.44+
- **Python**: Requires 3.10+
- **PyTorch**: Requires 2.8+

## Migration Guide

### From Standard WebUI

1. **Backup Current Setup**: Backup your current configuration and data
2. **Install Enhanced Features**: Follow the installation guide
3. **Migrate Configuration**: Update configuration files
4. **Test Functionality**: Verify all features work correctly
5. **Update Scripts**: Update any custom scripts or integrations

### Configuration Migration

The enhanced WebUI is backward compatible with existing configurations. Enhanced features are disabled by default and can be enabled gradually.

## Changelog

### Version 2.0.0
- Added file preview and automatic processing
- Implemented dark theme support
- Added chapter recognition system
- Enhanced audio format support
- Improved performance optimization
- Added comprehensive configuration management