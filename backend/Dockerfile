# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1: Base Image
# ============================================================================
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ============================================================================
# Stage 2: Download Models
# ============================================================================
FROM base AS model-downloader

# Set cache directory for models
ENV TRANSFORMERS_CACHE=/models

# Install transformers and torch (needed for download)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install transformers

# Copy download script
COPY scripts/download_models.py /tmp/download_models.py

# Download all models during build
RUN python /tmp/download_models.py

# Verify models were downloaded
RUN ls -lah /models/

# ============================================================================
# Stage 3: Install Python Dependencies
# ============================================================================
FROM base AS dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python packages with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 4: Production Image
# ============================================================================
FROM python:3.11-slim AS production

# Set working directory
WORKDIR /app

# Set environment variables
ENV TRANSFORMERS_CACHE=/models \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy Python packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages \
    /usr/local/lib/python3.11/site-packages

# Copy pre-downloaded models from model-downloader stage
COPY --from=model-downloader /models /models

# Copy application code
COPY app/ /app/app/

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /models

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
