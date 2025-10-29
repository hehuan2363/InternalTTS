# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set environment variables for UV
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies with UV
COPY requirements.txt /app/
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Ensure data/audio directories exist and are writable by appuser
RUN mkdir -p data audio && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV TTS_APP_SECRET="change-me"
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "app.py"]
