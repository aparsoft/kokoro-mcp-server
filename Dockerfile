# Multi-stage Dockerfile for Aparsoft TTS
# Optimized for production deployment with both CPU and optional GPU support

FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 ttsuser

WORKDIR /app

# Copy dependency files
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install hatchling && \
    pip install -e ".[mcp,cli]"

# Copy application code
COPY src/ /app/src/

# Change ownership
RUN chown -R ttsuser:ttsuser /app

# Switch to non-root user
USER ttsuser

# Create directories for outputs and logs
RUN mkdir -p /app/outputs /app/logs

# Expose port for HTTP transport (if using)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from aparsoft_tts.core.engine import TTSEngine; TTSEngine()" || exit 1

# Default command runs MCP server
CMD ["python", "-m", "aparsoft_tts.mcp_server"]


# GPU-enabled variant (optional)
FROM base as gpu

USER root

# Install CUDA dependencies if needed
# RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

USER ttsuser
