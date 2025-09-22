# IndexTTS2 Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install -U uv

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy project files
COPY --chown=app:app . .

# Install dependencies
RUN uv sync --all-extras

# Create necessary directories
RUN mkdir -p outputs prompts logs samples && \
    chown -R app:app outputs prompts logs samples

# Switch to app user
USER app

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Default command
CMD ["uv", "run", "webui.py", "--host", "0.0.0.0", "--port", "7860"]