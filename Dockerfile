FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    pkg-config \
    zlib1g-dev \
    libjpeg-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Upgrade packaging tools and install `uv` for dependency resolution
RUN pip install --no-cache-dir --upgrade pip setuptools wheel uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN set -ex && uv sync --no-dev --frozen

# Copy application code
COPY src/ src/
COPY streamlitui.py .
COPY knowledge/ knowledge/

# Expose Streamlit port
EXPOSE 8501

# Health check for ALB/ECS
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["uv", "run", "streamlit", "run", "streamlitui.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
