# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Project Overview

AI Token Wheel is an educational web application that visualizes how Large
Language Models (LLMs) probabilistically sample the next token from a
distribution. The backend uses FastAPI with HuggingFace Transformers (GPT-2)
for local model inference, with no API costs.

## Technology Stack

- **Backend**: FastAPI (Python 3.11)
- **ML Framework**: HuggingFace Transformers
- **Models**: GPT-2 (124M), GPT-2 Medium (355M)
- **Inference**: Local model inference using PyTorch (CPU-only)
- **Session Management**: In-memory storage with TTL-based cleanup
- **Container**: Docker with multi-stage builds for zero-startup-time deployment

## Common Commands

### Development

```bash
# Start development environment with Docker Compose
docker compose up backend

# The API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs

# First run downloads models (~3-5 minutes)
# Subsequent runs start instantly (~3-4 seconds) using persisted volume
```

### Production Build

```bash
# Build production Docker image (includes pre-downloaded models)
cd backend
docker build -t ai-token-wheel-backend:latest .

# Run production container
docker run -p 8000:8000 ai-token-wheel-backend:latest
```

### Testing API Endpoints

```bash
# List available models
curl http://localhost:8000/api/models

# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"model_name": "gpt2"}'
```

## Architecture

### Core Concepts

**Dynamic Threshold Filtering**: Instead of returning a fixed top-k tokens,
the API uses a dynamic threshold approach that returns all tokens with
probability ≥ threshold (default: 1%), with remaining tokens grouped into
an "Other" category. This guarantees visible wheel segments while
demonstrating the probability distribution's long tail.

**Session Isolation**: Each student session maintains a unique UUID,
conversation context, token generation history, and model selection. Sessions
are isolated for concurrent users and auto-expire after 1 hour of inactivity.

### Directory Structure

```text
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── models.py               # Pydantic request/response models
│   ├── routers/
│   │   └── sessions.py         # Session management endpoints
│   └── utils/
│       ├── model_loader.py     # HuggingFace model loading/caching
│       └── session_manager.py  # In-memory session storage
├── scripts/
│   └── download_models.py      # Pre-download models for Docker
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── Dockerfile                  # Production multi-stage build
└── Dockerfile.dev              # Development with hot-reload

docs/
├── API_DESIGN.md               # Complete API specification
└── DOCKER_PLAN.md              # Docker architecture and deployment
```

### Key Components

**Model Loader** (`app/utils/model_loader.py`):

- Loads models from cache directory (`TRANSFORMERS_CACHE=/models`)
- Uses `local_files_only=True` in production (no network access)
- Caches loaded models in memory for reuse across requests
- Maps friendly names ("gpt2") to HuggingFace IDs
  ("openai-community/gpt2")

**Session Manager** (`app/utils/session_manager.py`):

- In-memory session storage with dictionary-based lookup
- `Session` class tracks prompt, token history, timestamps
- `TokenInfo` class stores selected token metadata
- Background task cleans up expired sessions every 5 minutes

**API Router** (`app/routers/sessions.py`):

- Implements 7 core endpoints (create, get, set-prompt, next-token-probs,
  append-token, undo, delete)
- Uses PyTorch to compute token probabilities with softmax
- Handles "Other" category sampling by renormalizing below-threshold
  probabilities

### Model Inference Flow

1. User sets prompt via `POST /api/sessions/{id}/set-prompt`
2. Frontend requests probabilities via
   `GET /api/sessions/{id}/next-token-probs?threshold=0.01`
3. Backend tokenizes current text, runs forward pass, applies softmax to get
   probabilities
4. Returns tokens above threshold + "Other" category with sample tokens
5. User selects token (or "Other"), frontend calls
   `POST /api/sessions/{id}/append-token`
6. If "Other" selected, backend samples from below-threshold distribution
7. Token appended to session history, current_text updated

## Docker Architecture

### Development vs Production

**Development** (`Dockerfile.dev`):

- Does NOT download models during build (would be hidden by volume overlay)
- Downloads models at container startup via `download_models.py`
- Models persisted in named volume `model-cache`
- Hot-reload enabled via volume mount of `backend/app/`

**Production** (`Dockerfile`):

- Multi-stage build: base → model-downloader → dependencies → production
- Downloads models during build stage, copied into final image
- Models embedded in image for zero startup time
- Runs as non-root user (`appuser`)

### Important Docker Notes

- `TRANSFORMERS_CACHE=/models` must be set for HuggingFace cache location
- Production uses `local_files_only=True` to prevent network downloads
- BuildKit cache mounts optimize pip package installation
- Expected image size: ~1.35 GB (mostly model weights)

## API Endpoints

All endpoints are prefixed with `/api` except health/ready checks:

- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session state
- `POST /api/sessions/{id}/set-prompt` - Set/reset prompt
- `GET /api/sessions/{id}/next-token-probs` - Get token probabilities for
  wheel
- `POST /api/sessions/{id}/append-token` - Append selected token
- `POST /api/sessions/{id}/undo` - Undo last token
- `DELETE /api/sessions/{id}` - Delete session
- `GET /api/models` - List available models
- `GET /health` - Health check (for container orchestration)
- `GET /ready` - Readiness check (ensures models loaded)

Full API specification is documented in `docs/API_DESIGN.md`.

## Development Practices

### Adding a New Model

1. Add model ID to `MODEL_IDS` dict in `backend/app/utils/model_loader.py`
2. Add model to `MODELS` dict in `backend/scripts/download_models.py`
3. Add model info to `get_available_models()` function
4. Rebuild Docker image to download new model

### Session Cleanup

Sessions automatically expire after 1 hour of inactivity. Background task
runs every 5 minutes to cleanup expired sessions. Adjust TTL in `app/main.py`
if needed.

### CORS Configuration

Currently allows all origins (`allow_origins=["*"]`). Configure appropriately
for production deployment in `app/main.py`.

## Environment Variables

- `TRANSFORMERS_CACHE` - HuggingFace model cache directory
  (default: `/models`)
- `PYTHONUNBUFFERED=1` - Ensure Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1` - Prevent .pyc file creation

## Performance Characteristics

- **Startup Time**: 3-4 seconds (models pre-loaded in image)
- **Token Generation**: 50-100ms per token on modern CPU
- **Memory Usage**: ~600 MB for GPT-2, ~50 MB per active session
- **Recommended Resources**: 2 GB RAM, 2+ CPU cores

## Key Design Decisions

**Why Dynamic Threshold?** Guarantees visible wheel segments (minimum 1% by
default) while showing the long tail of the probability distribution.
Educational value: demonstrates that 50,000+ tokens exist below threshold.

**Why Backend Sampling for "Other"?** Simplifies frontend (doesn't need to
handle 50,000+ tokens), reduces payload size, ensures proper
probability-weighted sampling, and keeps token sampling logic secure on
backend.

**Why In-Memory Sessions?** Fast access, simple implementation, stateful
sessions with full context. Suitable for educational use case with moderate
concurrent users. Sessions auto-expire to prevent memory leaks.

**Why CPU-Only Inference?** GPT-2 inference is fast enough on CPU for
real-time token generation. No GPU reduces infrastructure costs and deployment
complexity.
