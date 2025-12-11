# AI Token Wheel - Docker Containerization Plan

## Overview

This document outlines the Docker containerization strategy for the AI Token Wheel
application, focusing on pre-loading ML models for zero startup time and optimized
cloud deployment.

## Goals

1. **Zero Startup Time**: Pre-load GPT-2 models during Docker build
2. **Fast Builds**: Leverage Docker layer caching and BuildKit features
3. **Small Image Size**: Multi-stage builds to minimize production image
4. **Cloud Ready**: Optimized for deployment to AWS/GCP/Azure
5. **Development Experience**: Efficient local development workflow

## Key Insights from Research

### HuggingFace Model Caching

**How it Works:**

- `from_pretrained()` automatically downloads models to cache directory
- Default cache location: `~/.cache/huggingface/hub/`
- Can specify custom location with `cache_dir` parameter
- `local_files_only=True` prevents network downloads (offline mode)

**Cache Directory Structure:**

```text
~/.cache/huggingface/
├── hub/
│   └── models--openai-community--gpt2/
│       ├── refs/
│       ├── snapshots/
│       │   └── e7da7f221d5bf496a48136c0cd264e630fe9fcc8/
│       │       ├── config.json
│       │       ├── model.safetensors
│       │       ├── tokenizer.json
│       │       └── vocab.json
│       └── blobs/
└── modules/
```

**Key Parameters:**

- `cache_dir`: Custom cache directory path
- `local_files_only=True`: Only use local files, no downloads
- `force_download=False`: Don't re-download if cached
- `revision`: Specific model version (branch, tag, or commit)

### Docker Best Practices

**Multi-Stage Builds:**

- Separate build dependencies from runtime dependencies
- Download models in build stage, copy to runtime stage
- Reduces final image size by 50-70%

**Layer Caching:**

- Order instructions from least to most frequently changing
- Copy requirements files before source code
- Use cache mounts for package managers

**BuildKit Features:**

- `--mount=type=cache` for persistent package caches
- `--mount=type=bind` for temporary file access
- Parallel stage execution
- Improved caching algorithm

## Docker Architecture

### Multi-Stage Dockerfile Strategy

Our Dockerfile will use **4 stages**:

1. **base**: Base Python image with common dependencies
2. **model-downloader**: Downloads and caches ML models
3. **dependencies**: Installs Python packages
4. **production**: Final runtime image

```dockerfile
# Stage 1: Base image
FROM python:3.11-slim AS base

# Stage 2: Download models
FROM base AS model-downloader
RUN python download_models.py

# Stage 3: Install dependencies
FROM base AS dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 4: Production
FROM python:3.11-slim AS production
COPY --from=model-downloader /models /models
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ /app/
CMD ["uvicorn", "app.main:app"]
```

### Directory Structure

```text
ai-fun-token-wheel-v2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers/
│   │   │   └── sessions.py
│   │   └── utils/
│   │       ├── model_loader.py
│   │       └── session_manager.py
│   ├── scripts/
│   │   └── download_models.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── .dockerignore
├── frontend/
│   └── (Svelte app)
├── docker-compose.yml
└── docs/
    ├── API_DESIGN.md
    └── DOCKER_PLAN.md
```

## Detailed Implementation

### 1. Model Download Script

**File:** `backend/scripts/download_models.py`

```python
#!/usr/bin/env python3
"""
Pre-download HuggingFace models for Docker image.
This script runs during Docker build to cache models.
"""
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

# Model configurations
MODELS = {
    "gpt2": "openai-community/gpt2",
    "gpt2-medium": "openai-community/gpt2-medium",
    # Add more models as needed
}

# Cache directory (will be copied to Docker image)
CACHE_DIR = os.getenv("TRANSFORMERS_CACHE", "/models")

def download_model(model_id: str, model_name: str):
    """Download and cache a model."""
    print(f"Downloading {model_name} ({model_id})...")

    # Download model
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=False,  # Allow downloads during build
    )
    print(f"  Model downloaded: {model.config.model_type}")

    # Download tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=False,
    )
    print(f"  Tokenizer downloaded: {len(tokenizer)} tokens\n")

    # Clean up memory
    del model
    del tokenizer

if __name__ == "__main__":
    print("=" * 60)
    print("Pre-downloading HuggingFace models...")
    print("=" * 60)

    for name, model_id in MODELS.items():
        download_model(model_id, name)

    print("=" * 60)
    print("All models downloaded successfully!")
    print(f"Cache directory: {CACHE_DIR}")
    print("=" * 60)
```

### 2. Model Loader Utility

**File:** `backend/app/utils/model_loader.py`

```python
"""
Model loading utilities for production.
Uses pre-downloaded models from Docker image.
"""
import os
from typing import Dict
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Use pre-downloaded models (set during Docker build)
CACHE_DIR = os.getenv("TRANSFORMERS_CACHE", "/models")

# Global model cache (loaded once at startup)
_model_cache: Dict[str, tuple] = {}

def load_model(model_name: str = "gpt2"):
    """
    Load a pre-downloaded model from cache.
    Models are loaded once and cached in memory.
    """
    if model_name in _model_cache:
        return _model_cache[model_name]

    # Map friendly names to HuggingFace IDs
    model_ids = {
        "gpt2": "openai-community/gpt2",
        "gpt2-medium": "openai-community/gpt2-medium",
    }

    model_id = model_ids.get(model_name)
    if not model_id:
        raise ValueError(f"Unknown model: {model_name}")

    print(f"Loading {model_name} from cache...")

    # Load from pre-downloaded cache (no network access)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=True,  # Critical: no downloads in production
        torch_dtype=torch.float32,
    )
    model.eval()  # Set to evaluation mode

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=True,
    )

    # Cache for future requests
    _model_cache[model_name] = (model, tokenizer)

    print(f"  Model loaded successfully!")
    return model, tokenizer

def get_available_models() -> list:
    """Return list of available pre-loaded models."""
    return ["gpt2", "gpt2-medium"]
```

### 3. Production Dockerfile

**File:** `backend/Dockerfile`

```dockerfile
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
```

### 4. Development Dockerfile

**File:** `backend/Dockerfile.dev`

**Important Note:** Unlike the production Dockerfile, the development version does
NOT download models during the build. This is because `docker-compose.yml` mounts
a volume at `/models`, which would overlay (hide) any models downloaded during the
build. Instead, models are downloaded at container startup and persisted in the
volume, making them available across container restarts.

```dockerfile
# syntax=docker/dockerfile:1

# Development Dockerfile with hot-reload and debugging
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/models

# Install Python packages with cache mount
COPY requirements.txt requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy download script (will run at container startup, not build time)
# NOTE: We don't download models during build because docker-compose mounts
# a volume at /models, which would overlay and hide any models in the image.
# Instead, we download at runtime on first start, and the volume persists them.
COPY scripts/download_models.py /tmp/download_models.py

# Copy application code (will be overridden by volume mount)
COPY app/ /app/app/

EXPOSE 8000

# Download models at startup (only downloads if not cached), then start server
# This ensures models are in the persisted volume, not hidden by the overlay
CMD python /tmp/download_models.py && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    --reload --reload-dir /app/app
```

### 5. .dockerignore File

**File:** `backend/.dockerignore`

```text
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Git
.git/
.gitignore

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# Documentation
*.md
docs/

# Models (we download them in the image)
models/
*.bin
*.safetensors

# OS
.DS_Store
Thumbs.db
```

### 6. Docker Compose for Development

**File:** `docker-compose.yml`

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
      cache_from:
        - ai-token-wheel-backend:latest
    image: ai-token-wheel-backend:dev
    container_name: token-wheel-backend
    ports:
      - "8000:8000"
    volumes:
      # Mount source code for hot-reload
      - ./backend/app:/app/app:ro
      # Persist model cache across container restarts
      - model-cache:/models
    environment:
      - TRANSFORMERS_CACHE=/models
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Add frontend service later
  # frontend:
  #   build: ./frontend
  #   ports:
  #     - "5173:5173"

volumes:
  model-cache:
    driver: local
```

### 7. Requirements Files

**File:** `backend/requirements.txt`

```text
# FastAPI and server
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# ML frameworks
torch==2.1.0
transformers==4.35.2

# Utilities
python-multipart==0.0.6
```

**File:** `backend/requirements-dev.txt`

```text
# Development tools
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.1

# Code quality
black==23.11.0
ruff==0.1.6
mypy==1.7.1

# Debugging
ipython==8.17.2
```

## Build and Run Instructions

### Local Development

```bash
# Build development image
docker compose build backend

# Start development environment
docker compose up backend

# The API will be available at http://localhost:8000
# Changes to code will trigger auto-reload
```

**First Run Behavior:**

On the first run, you'll see the download script execute:

```text
Downloading gpt2 (openai-community/gpt2)...
  Model downloaded: gpt2
  Tokenizer downloaded: 50257 tokens
All models downloaded successfully!
Starting uvicorn...
```

This takes ~3-5 minutes. The models are saved to the `model-cache` Docker volume.

**Subsequent Runs:**

On subsequent runs, HuggingFace detects the cached models and skips downloading:

```text
All models already cached, skipping download.
Starting uvicorn...
```

This takes ~3-4 seconds - instant startup!

### Production Build

```bash
# Build production image
cd backend
docker build -t ai-token-wheel-backend:latest .

# Run production container
docker run -p 8000:8000 ai-token-wheel-backend:latest

# Test the API
curl http://localhost:8000/api/models
```

### Multi-Platform Build (for ARM/AMD)

```bash
# Create buildx builder
docker buildx create --name multiplatform --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-registry/ai-token-wheel-backend:latest \
  --push \
  .
```

## Optimization Strategies

### Image Size Reduction

**Current Strategy:**

1. **Multi-stage builds**: Build artifacts in one stage, copy to final
2. **Slim base image**: `python:3.11-slim` instead of full Python
3. **Layer ordering**: Dependencies before code for better caching
4. **No cache directories**: Remove pip cache after install
5. **.dockerignore**: Exclude unnecessary files from build context

**Expected Image Sizes:**

- Base Python slim: ~150 MB
- - PyTorch CPU: ~650 MB
- - Transformers: ~50 MB
- - GPT-2 model: ~500 MB
- - Application code: ~5 MB
- **Total: ~1.35 GB** (mostly model weights)

**Further Optimizations (Future):**

- Use distroless Python image: Save ~100 MB
- Model quantization (int8): Reduce model size by 4x
- Shared base layer for multiple models

### Build Time Optimization

**Techniques:**

1. **BuildKit cache mounts**: Reuse pip downloads across builds
2. **Layer caching**: Order layers from least to most frequently changing
3. **Parallel builds**: Multi-stage builds run in parallel
4. **Cache models separately**: Models in their own layer

**Expected Build Times:**

- **First build** (cold): ~5-10 minutes

  - Download Python base image: 1 min
  - Download PyTorch: 2 min
  - Download models: 3-5 min
  - Install dependencies: 1 min

- **Incremental build** (code change): ~10 seconds

  - Layer cache hits for dependencies
  - Only rebuild final stage

- **Dependency update**: ~2 minutes
  - Reuse base image and models
  - Reinstall Python packages

### Runtime Performance

**Startup Time:**

- Models already loaded in image: **No download time**
- Model load to memory: **~2-3 seconds** for GPT-2
- FastAPI initialization: **~1 second**
- **Total startup: ~3-4 seconds** (vs. ~30 seconds downloading)

**Memory Usage:**

- Base Python + FastAPI: ~100 MB
- GPT-2 model loaded: ~500 MB
- Session management overhead: ~50 MB per active session
- **Recommended minimum**: 1 GB RAM
- **Recommended for production**: 2-4 GB RAM (for multiple concurrent users)

**CPU Requirements:**

- GPT-2 inference is CPU-only (no GPU needed)
- Modern CPU sufficient for real-time inference
- Each token generation: ~50-100ms on modern CPU
- **Recommended**: 2+ CPU cores for handling concurrent requests

## Cloud Deployment

### AWS Deployment

**Service Options:**

1. **AWS ECS (Elastic Container Service)**

   - Best for: Production deployments
   - Container orchestration managed by AWS
   - Auto-scaling based on CPU/memory
   - Integration with Application Load Balancer

2. **AWS Fargate**

   - Serverless container execution
   - No EC2 instance management
   - Pay only for running containers
   - Good for variable workloads

3. **AWS App Runner**
   - Simplest option
   - Automatic deployments from GitHub
   - Built-in load balancing
   - Limited customization

**Deployment Steps (ECS):**

```bash
# 1. Push image to ECR
aws ecr create-repository --repository-name ai-token-wheel-backend
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag ai-token-wheel-backend:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/ai-token-wheel-backend:latest

docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-token-wheel-backend:latest

# 2. Create ECS task definition (JSON)
# 3. Create ECS service with load balancer
# 4. Configure auto-scaling policies
```

**ECS Task Definition:**

```json
{
  "family": "ai-token-wheel-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/ai-token-wheel-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-token-wheel",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

**Service Options:**

1. **Cloud Run**

   - Serverless container execution
   - Auto-scales to zero
   - Pay per request
   - Easiest deployment

2. **Google Kubernetes Engine (GKE)**
   - Full Kubernetes control
   - Best for complex deployments
   - Advanced networking and scaling

**Deployment (Cloud Run):**

```bash
# 1. Push to Artifact Registry
gcloud artifacts repositories create ai-token-wheel \
  --repository-format=docker \
  --location=us-central1

docker tag ai-token-wheel-backend:latest \
  us-central1-docker.pkg.dev/PROJECT_ID/ai-token-wheel/backend:latest

docker push us-central1-docker.pkg.dev/PROJECT_ID/ai-token-wheel/backend:latest

# 2. Deploy to Cloud Run
gcloud run deploy ai-token-wheel-backend \
  --image us-central1-docker.pkg.dev/PROJECT_ID/ai-token-wheel/backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --allow-unauthenticated \
  --port 8000
```

### Azure Deployment

**Service Options:**

1. **Azure Container Instances**

   - Quick deployments
   - No orchestration
   - Good for testing

2. **Azure Container Apps**

   - Serverless containers
   - Kubernetes-based
   - Auto-scaling

3. **Azure Kubernetes Service (AKS)**
   - Full Kubernetes
   - Enterprise deployments

**Deployment (Container Apps):**

```bash
# 1. Push to ACR
az acr create --resource-group myResourceGroup \
  --name aiTokenWheel --sku Basic

az acr login --name aiTokenWheel

docker tag ai-token-wheel-backend:latest \
  aitokenwheel.azurecr.io/backend:latest

docker push aitokenwheel.azurecr.io/backend:latest

# 2. Deploy to Container Apps
az containerapp create \
  --name ai-token-wheel-backend \
  --resource-group myResourceGroup \
  --environment myEnvironment \
  --image aitokenwheel.azurecr.io/backend:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 1.0 \
  --memory 2.0Gi
```

## Cost Estimation

### Development Costs

- **Local Development**: Free (uses local Docker)
- **Docker Hub Storage**: Free tier (1 private repository)
- **GitHub Actions CI/CD**: Free tier (2,000 minutes/month)

### Production Costs (Estimated Monthly)

**AWS ECS/Fargate:**

- Fargate vCPU (1 vCPU): ~$30/month
- Fargate Memory (2 GB): ~$7/month
- Application Load Balancer: ~$20/month
- Data transfer: ~$5/month
- **Total: ~$62/month**

**Google Cloud Run:**

- Request pricing: $0.40 per 1M requests
- CPU time: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GiB-second
- For 10,000 users/month: **~$20-40/month**

**Azure Container Apps:**

- 1 vCPU, 2 GB: ~$35/month
- HTTP requests: Included
- **Total: ~$35/month**

**Recommendation:**

- **Development/Testing**: Google Cloud Run (free tier covers most usage)
- **Production (low traffic)**: Cloud Run or Azure Container Apps
- **Production (high traffic)**: AWS ECS Fargate with auto-scaling

## Monitoring and Observability

### Health Checks

**Endpoint:** `GET /health`

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "model_loaded": "gpt2" in _model_cache,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Readiness Probe

**Endpoint:** `GET /ready`

```python
@app.get("/ready")
async def readiness_check():
    """Readiness check - models must be loaded."""
    if not _model_cache:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return {"status": "ready"}
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log model loading
logger.info(f"Loading model {model_name}...")
logger.info(f"Model {model_name} loaded successfully")
```

### Metrics (Future)

- Prometheus metrics endpoint: `/metrics`
- Track: requests/sec, response time, model inference time
- Grafana dashboards for visualization

## Security Considerations

### Container Security

1. **Non-root user**: Run as `appuser` (UID 1000)
2. **Read-only filesystem**: Mount code as read-only where possible
3. **Minimal base image**: Use slim Python image
4. **No secrets in image**: Use environment variables or secret management
5. **Regular updates**: Keep base images and dependencies updated

### Network Security

1. **HTTPS only**: Use TLS termination at load balancer
2. **CORS configuration**: Restrict origins in production
3. **Rate limiting**: Implement per-IP rate limits
4. **Input validation**: Validate all user inputs

### Secrets Management

```bash
# AWS Secrets Manager
aws secretsmanager create-secret --name token-wheel/api-key \
  --secret-string "your-secret-key"

# GCP Secret Manager
gcloud secrets create api-key --data-file=./secret.txt

# Azure Key Vault
az keyvault secret set --vault-name myKeyVault \
  --name api-key --value "your-secret-key"
```

## CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/docker-build.yml`

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: your-username/ai-token-wheel-backend

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=your-username/ai-token-wheel-backend:buildcache
          cache-to: type=registry,ref=your-username/ai-token-wheel-backend:buildcache,mode=max
```

## Troubleshooting

### Common Issues

#### 1. Models not found in production

```bash
# Check if models directory exists
docker exec <container-id> ls -la /models

# Verify environment variable
docker exec <container-id> env | grep TRANSFORMERS_CACHE
```

#### 2. Out of memory errors

```bash
# Increase container memory
docker run -m 4g ai-token-wheel-backend:latest

# Check memory usage
docker stats <container-id>
```

#### 3. Slow startup

```bash
# Check model loading logs
docker logs <container-id>

# Verify models are pre-downloaded
docker run --rm ai-token-wheel-backend:latest ls -lah /models
```

#### 4. Build cache not working

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Check cache mounts
docker buildx build --progress=plain .
```

## Future Enhancements

1. **Model Quantization**: Reduce model size with int8 quantization
2. **GPU Support**: Add CUDA support for larger models (optional)
3. **Model Versioning**: Support multiple model versions
4. **A/B Testing**: Deploy multiple model versions simultaneously
5. **Edge Deployment**: Deploy to edge locations for lower latency
6. **Model Warm-up**: Pre-load models into memory on startup
7. **Graceful Shutdown**: Handle in-flight requests during shutdown

## Summary

This Docker strategy provides:

- **Zero startup time**: Models pre-loaded during build
- **Optimized builds**: Multi-stage builds with cache mounts
- **Small images**: ~1.35 GB (mostly model weights)
- **Fast rebuilds**: ~10 seconds for code changes
- **Cloud ready**: Deployable to AWS/GCP/Azure
- **Development friendly**: Hot-reload with Docker Compose
- **Production ready**: Health checks, logging, non-root user

The architecture ensures students can access the website and immediately start
generating tokens without waiting for model downloads.
