# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Project Overview

AI Token Wheel is an educational web application that visualizes how Large
Language Models (LLMs) probabilistically sample the next token from a
distribution. The backend uses FastAPI with HuggingFace Transformers (GPT-2)
for local model inference, with no API costs.

## Technology Stack

### Backend

- **Framework**: FastAPI (Python 3.11)
- **ML Framework**: HuggingFace Transformers
- **Models**: GPT-2 (124M), GPT-2 Medium (355M)
- **Inference**: Local model inference using PyTorch (CPU-only)
- **Session Management**: In-memory storage with TTL-based cleanup
- **Container**: Docker with multi-stage builds for zero-startup-time deployment

### Frontend

- **Framework**: SvelteKit 2 with Svelte 5 (runes mode)
- **Styling**: Tailwind CSS 4 with Vite plugin
- **State Management**: Svelte 5 `$state` and `$derived` runes (reactive primitives)
- **Testing**: Vitest (unit tests), Playwright (E2E tests)
- **Build Tool**: Vite with SvelteKit plugin
- **Container**: Docker development image with hot-reload

## Common Commands

### Development

```bash
# Start full-stack development environment
docker compose up

# Or start services individually
docker compose up backend   # Backend only at http://localhost:8000
docker compose up frontend  # Frontend only at http://localhost:5173

# Backend API documentation: http://localhost:8000/docs
# First backend run downloads models (~3-5 minutes)
# Subsequent runs start instantly (~3-4 seconds) using persisted volume

# Frontend development (without Docker)
cd frontend
npm install
npm run dev  # Starts dev server at http://localhost:5173

# Run frontend tests
npm run test:unit        # Vitest unit tests
npm run test:e2e         # Playwright E2E tests
npm run test             # Run all tests

# Linting and formatting
npm run lint             # ESLint + Prettier check
npm run format           # Format with Prettier
npm run check            # Svelte type checking
```

### Production Build

```bash
# Build backend production image (includes pre-downloaded models)
cd backend
docker build -t ai-token-wheel-backend:latest .
docker run -p 8000:8000 ai-token-wheel-backend:latest

# Build frontend production image
cd frontend
npm run build              # Build for production
npm run preview            # Preview production build
docker build -t ai-token-wheel-frontend:latest .
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

frontend/
├── src/
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts       # Backend API client
│   │   ├── components/
│   │   │   ├── TokenWheel.svelte       # Main spinning wheel visualization
│   │   │   ├── SpinButton.svelte       # Spin trigger button
│   │   │   ├── WheelLegend.svelte      # Token probability legend
│   │   │   ├── OtherCategoryList.svelte # "Other" category tokens
│   │   │   ├── GeneratedText.svelte    # Display generated output
│   │   │   ├── PromptInput.svelte      # Initial prompt input
│   │   │   ├── ModelSelector.svelte    # GPT-2 model selector
│   │   │   └── LoadingSpinner.svelte   # Loading indicator
│   │   ├── stores/
│   │   │   └── session.svelte.ts       # Global state (Svelte 5 runes)
│   │   └── utils/
│   │       ├── colors.ts       # Token color palette
│   │       ├── wheel.ts        # Wheel segment calculations
│   │       └── spinner.ts      # Wheel animation logic
│   ├── routes/
│   │   ├── +page.svelte        # Landing page
│   │   ├── +layout.svelte      # App layout
│   │   └── wheel/
│   │       └── +page.svelte    # Main token wheel interface
│   └── app.css                 # Global styles (Tailwind imports)
├── static/                     # Static assets
├── e2e/                        # Playwright E2E tests
├── vite.config.ts              # Vite + Vitest configuration
├── svelte.config.js            # SvelteKit configuration
├── playwright.config.ts        # Playwright test configuration
├── package.json                # NPM dependencies and scripts
├── Dockerfile                  # Production build
└── Dockerfile.dev              # Development with hot-reload

docs/
├── API_DESIGN.md               # Complete API specification
└── DOCKER_PLAN.md              # Docker architecture and deployment
```

### Key Components

#### Backend Components

**Model Loader** (`backend/app/utils/model_loader.py`):

- Loads models from cache directory (`TRANSFORMERS_CACHE=/models`)
- Uses `local_files_only=True` in production (no network access)
- Caches loaded models in memory for reuse across requests
- Maps friendly names ("gpt2") to HuggingFace IDs
  ("openai-community/gpt2")

**Session Manager** (`backend/app/utils/session_manager.py`):

- In-memory session storage with dictionary-based lookup
- `Session` class tracks prompt, token history, timestamps
- `TokenInfo` class stores selected token metadata
- Background task cleans up expired sessions every 5 minutes

**API Router** (`backend/app/routers/sessions.py`):

- Implements 7 core endpoints (create, get, set-prompt, next-token-probs,
  append-token, undo, delete)
- Uses PyTorch to compute token probabilities with softmax
- Handles "Other" category sampling by renormalizing below-threshold
  probabilities

#### Frontend Components

**Session Store** (`frontend/src/lib/stores/session.svelte.ts`):

- Global state management using Svelte 5 `$state` runes (not Svelte stores)
- `SessionStore` class encapsulates all application state
- Reactive primitives: `$state` for mutable state, `$derived` for computed
  values
- Singleton instance `sessionStore` exported for app-wide access
- Tracks session ID, model, prompt, current text, token history, wheel data

**API Client** (`frontend/src/lib/api/client.ts`):

- TypeScript wrapper for all backend API calls
- Handles request/response serialization and error handling
- Functions: `createSession()`, `setPrompt()`, `getNextTokenProbs()`,
  `appendToken()`, `undoToken()`, `deleteSession()`
- Configurable API base URL via `VITE_API_URL` environment variable

**TokenWheel Component** (`frontend/src/lib/components/TokenWheel.svelte`):

- SVG-based wheel visualization with animated spinning
- Renders wheel segments proportional to token probabilities
- Color-coded segments using predefined palette
- Handles wheel animation and segment selection
- Displays "Other" category as special segment

**Utility Modules**:

- `wheel.ts`: Calculates wheel segment angles and positions from probabilities
- `spinner.ts`: Manages wheel spin animation with easing and duration
- `colors.ts`: Defines color palette for token segments

### Application Flow

1. **Session Creation**: Frontend calls `createSession(modelName)`, backend
   creates session with UUID
2. **Set Prompt**: User enters prompt, frontend calls `setPrompt(sessionId,
   prompt)`
3. **Request Probabilities**: Frontend calls `getNextTokenProbs(sessionId,
   threshold)`, backend tokenizes text, runs forward pass, applies softmax
4. **Display Wheel**: Backend returns tokens above threshold + "Other"
   category. Frontend renders TokenWheel with segments proportional to
   probabilities
5. **Spin & Select**: User clicks spin button, wheel animates and randomly
   selects segment based on probabilities
6. **Append Token**: Frontend calls `appendToken(sessionId, selection)`. If
   "Other" selected, backend samples from below-threshold distribution
7. **Update State**: Backend returns updated text and history, frontend updates
   session store
8. **Repeat**: Steps 3-7 repeat for each token generation
9. **Undo**: User can undo last token via `undoToken(sessionId)`

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

### Backend Development

**Adding a New Model**:

1. Add model ID to `MODEL_IDS` dict in `backend/app/utils/model_loader.py`
2. Add model to `MODELS` dict in `backend/scripts/download_models.py`
3. Add model info to `get_available_models()` function
4. Rebuild Docker image to download new model

**Session Cleanup**:

Sessions automatically expire after 1 hour of inactivity. Background task
runs every 5 minutes to cleanup expired sessions. Adjust TTL in
`backend/app/main.py` if needed.

**CORS Configuration**:

Currently allows all origins (`allow_origins=["*"]`). Configure appropriately
for production deployment in `backend/app/main.py`.

### Frontend Development

**Svelte 5 Runes** (not Svelte 4 stores):

- Use `$state` for reactive state (replaces `writable` stores)
- Use `$derived` for computed values (replaces `derived` stores)
- Use `$effect` for side effects (replaces `$:` reactive statements in many
  cases)
- State is defined in class instances (see `SessionStore` class)
- Import store instance: `import { sessionStore } from '$lib/stores/session.svelte.ts'`
- Access state: `sessionStore.sessionId`, `sessionStore.isLoading`, etc.

**Component Development**:

- Use `.svelte` extension for Svelte components
- Use `.svelte.ts` extension for TypeScript files with Svelte runes
- Components use Svelte 5 syntax (no `export let`, use `let { prop } = $props()`)
- Prefer composition over large monolithic components

**Styling**:

- Tailwind CSS 4 with `@tailwindcss/vite` plugin (no `postcss` config needed)
- Use utility classes directly in component markup
- Global styles in `src/app.css`

**Testing**:

- Unit tests: Vitest with `@vitest/browser-playwright` for component tests
- E2E tests: Playwright in `e2e/` directory
- Run `npm run test:unit` for unit tests, `npm run test:e2e` for E2E tests

## Environment Variables

### Backend Environment

- `TRANSFORMERS_CACHE` - HuggingFace model cache directory
  (default: `/models`)
- `PYTHONUNBUFFERED=1` - Ensure Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1` - Prevent .pyc file creation

### Frontend Environment

- `VITE_API_URL` - Backend API base URL (default: `http://localhost:8000`)
- Set in `frontend/.env` for local development
- Passed as environment variable in Docker Compose

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
