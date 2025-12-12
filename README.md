# AI Token Wheel

An educational web application that visualizes how Large Language Models (LLMs)
probabilistically sample the next token from a distribution. This interactive
tool demonstrates the fundamental mechanics of LLM text generation using GPT-2
for local inference.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.x-blue.svg)

## Features

- **Interactive Token Wheel**: Visualize probability distributions as a
  spinning wheel
- **Real-time Generation**: Watch token-by-token text generation with
  probability weights
- **Educational Focus**: Demonstrates dynamic threshold filtering and the long
  tail of token distributions
- **Local Inference**: No API costs - runs GPT-2 locally on CPU
- **Multiple Models**: Support for GPT-2 (124M) and GPT-2 Medium (355M)
  parameters

## Technology Stack

### Backend

- **Framework**: FastAPI (Python 3.11)
- **ML Framework**: HuggingFace Transformers
- **Models**: GPT-2 family (local inference, CPU-only)
- **Session Management**: In-memory storage with TTL-based cleanup
- **Container**: Docker with multi-stage builds

### Frontend

- **Framework**: SvelteKit 2 with Svelte 5 (runes mode)
- **Styling**: Tailwind CSS 4
- **State Management**: Svelte 5 `$state` and `$derived` runes
- **Testing**: Vitest (unit), Playwright (E2E)
- **Build Tool**: Vite

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ai-fun-token-wheel-v2

# Start both backend and frontend
docker compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

**Note**: First run downloads models (~3-5 minutes). Subsequent runs start
instantly (~3-4 seconds).

### Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download models (first time only)
python scripts/download_models.py

# Start development server
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Development Workflow

### Backend Development

#### Backend Formatting, Linting, and Type Checking

The backend uses **black**, **ruff**, and **mypy** configured via
`backend/pyproject.toml`.

```bash
cd backend
source .venv/bin/activate

# Format code with black
black app/

# Lint with ruff
ruff check app/

# Auto-fix linting issues
ruff check app/ --fix

# Type check with mypy
mypy app/ --pretty

# Run all checks
black app/ && ruff check app/ && mypy app/
```

#### Running Tests

```bash
cd backend
source .venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Development

#### Frontend Formatting, Linting, and Type Checking

The frontend uses **Prettier**, **ESLint**, and **TypeScript**.

```bash
cd frontend

# Check formatting with Prettier
npm run format

# Lint with ESLint
npm run lint

# Type check with TypeScript
npm run check

# Run all checks
npm run lint && npm run check

# Run tests
npm run test        # All tests
npm run test:unit   # Unit tests only
npm run test:e2e    # E2E tests only
```

#### Building for Production

```bash
cd frontend

# Build production bundle
npm run build

# Preview production build
npm run preview
```

## VSCode Setup (Recommended)

This project includes pre-configured VSCode settings for automatic formatting,
linting, and type checking. The setup provides a seamless development experience
with instant feedback and automatic code fixes.

### Quick Setup

1. **Open the project in VSCode**

   ```bash
   code .
   ```

2. **Install Recommended Extensions**

   VSCode will prompt you to install recommended extensions. Click "Install All"
   or manually install from the Extensions panel:

   - View → Extensions → Filter by "@recommended"
   - Click "Install Workspace Recommended Extensions"

3. **Reload VSCode** (if needed)

   After installing extensions, reload VSCode to activate them:

   - CMD+SHIFT+P (Mac) or CTRL+SHIFT+P (Windows/Linux)
   - Type "Developer: Reload Window"
   - Press Enter

4. **Verify Setup**

   - Open any Python file → should auto-format on save with Black
   - Open any Svelte/TypeScript file → should auto-format with Prettier
   - Linting errors should appear inline with squiggly underlines
   - All settings are pre-configured in `.vscode/settings.json`

### Recommended Extensions

The project includes `.vscode/extensions.json` with the following recommended
extensions:

#### Backend (Python)

| Extension | ID | Purpose |
| --------- | --- | ------- |
| [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | `ms-python.python` | Python language support |
| [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) | `ms-python.black-formatter` | Auto-format with Black |
| [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) | `charliermarsh.ruff` | Fast Python linting |
| [Mypy Type Checker](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker) | `ms-python.mypy-type-checker` | Static type checking |

#### Frontend (TypeScript/Svelte)

| Extension | ID | Purpose |
| --------- | --- | ------- |
| [Svelte for VS Code](https://marketplace.visualstudio.com/items?itemName=svelte.svelte-vscode) | `svelte.svelte-vscode` | Svelte language support |
| [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) | `dbaeumer.vscode-eslint` | JavaScript/TypeScript linting |
| [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) | `esbenp.prettier-vscode` | Code formatting |
| [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss) | `bradlc.vscode-tailwindcss` | Tailwind autocomplete |

### Features Enabled

Once extensions are installed and settings are activated:

#### Automatic Formatting

- **Format on Save**: Code automatically formats when you save files
- **Format on Paste**: Pasted code is formatted automatically
- **Organize Imports**: Import statements are automatically sorted

#### Inline Linting

- **Real-time Errors**: See linting errors as you type
- **Quick Fixes**: Click lightbulb icons for automatic fixes
- **Error Descriptions**: Hover over errors for detailed explanations

#### Type Checking

- **Type Hints**: IntelliSense shows type information
- **Type Errors**: Mypy errors appear inline in Python files
- **Auto-completion**: Smart suggestions based on types

#### Code Actions

- **Auto-fix on Save**: Automatically fix linting issues when saving
- **Organize Imports**: Import statements automatically sorted
- **Remove Unused Imports**: Dead code automatically removed

### VSCode Configuration Files

The VSCode setup uses these configuration files:

- **`.vscode/settings.json`** - Editor settings and tool configurations
- **`.vscode/extensions.json`** - Recommended extensions list
- **`backend/pyproject.toml`** - Black, Ruff, and Mypy configuration
- **`frontend/eslint.config.js`** - ESLint rules and settings
- **`frontend/tsconfig.json`** - TypeScript compiler options

### Troubleshooting

#### Extensions Not Working

1. **Check Extension Status**: View → Extensions → ensure all are enabled
2. **Reload VSCode**: CMD+SHIFT+P → "Developer: Reload Window"
3. **Check Output Panel**: View → Output → select extension from dropdown

#### Python Tools Not Found

1. **Activate Virtual Environment**:

   ```bash
   cd backend
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

2. **Verify Python Interpreter**: CMD+SHIFT+P → "Python: Select Interpreter"
   → Choose `.venv` interpreter

3. **Reinstall Dev Dependencies**:

   ```bash
   pip install -r requirements-dev.txt
   ```

#### Formatting Not Working

1. **Check Default Formatter**: Right-click in file → "Format Document With..."
   → Choose correct formatter
2. **Enable Format on Save**: Check `.vscode/settings.json` →
   `"editor.formatOnSave": true`
3. **Check for Syntax Errors**: Fix any syntax errors preventing formatting

### Manual Tool Usage (Without VSCode)

If you prefer not to use VSCode, all tools can be run from the command line:

```bash
# Backend
cd backend
source .venv/bin/activate
black app/                    # Format
ruff check app/ --fix         # Lint and auto-fix
mypy app/                     # Type check

# Frontend
cd frontend
npm run format                # Format
npm run lint                  # Lint
npm run check                 # Type check
```

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic models
│   │   ├── routers/
│   │   │   └── sessions.py      # Session endpoints
│   │   └── utils/
│   │       ├── model_loader.py  # Model management
│   │       └── session_manager.py
│   ├── scripts/
│   │   └── download_models.py   # Model downloader
│   ├── pyproject.toml           # Black, Ruff, Mypy config
│   ├── requirements.txt         # Production dependencies
│   └── requirements-dev.txt     # Development dependencies
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── client.ts    # API client
│   │   │   │   └── types.ts     # TypeScript types
│   │   │   ├── components/      # Svelte components
│   │   │   ├── stores/          # State management
│   │   │   └── utils/           # Utility functions
│   │   └── routes/              # SvelteKit routes
│   ├── eslint.config.js         # ESLint configuration
│   ├── svelte.config.js         # SvelteKit config
│   ├── tailwind.config.ts       # Tailwind config
│   └── package.json             # NPM dependencies
├── docs/                        # Additional documentation
├── docker-compose.yml
└── README.md
```

## Tool Configuration Reference

### Backend Configuration (`backend/pyproject.toml`)

```toml
[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "B", "UP"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
```

### Frontend Configuration

- **ESLint**: `frontend/eslint.config.js`
- **Prettier**: Uses defaults (integrated with ESLint)
- **TypeScript**: `frontend/tsconfig.json`
- **Tailwind**: `frontend/tailwind.config.ts`

## API Endpoints

All endpoints are prefixed with `/api` except health checks:

- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session state
- `POST /api/sessions/{id}/set-prompt` - Set initial prompt
- `GET /api/sessions/{id}/next-token-probs` - Get token probabilities
- `POST /api/sessions/{id}/append-token` - Append selected token
- `POST /api/sessions/{id}/undo` - Undo last token
- `DELETE /api/sessions/{id}` - Delete session
- `GET /api/models` - List available models
- `GET /health` - Health check
- `GET /ready` - Readiness check

Full API documentation: <http://localhost:8000/docs>

## Environment Variables

### Backend Environment Variables

- `TRANSFORMERS_CACHE` - Model cache directory (default: `/models`)
- `PYTHONUNBUFFERED` - Unbuffered Python output (default: `1`)

### Frontend Environment Variables

- `VITE_API_URL` - Backend API base URL (default: `http://localhost:8000`)

## Performance

- **Startup Time**: 3-4 seconds (models pre-loaded)
- **Token Generation**: 50-100ms per token (CPU)
- **Memory Usage**: ~600 MB for GPT-2, ~50 MB per session
- **Recommended**: 2 GB RAM, 2+ CPU cores

## Development Tips

### Adding a New Model

1. Add model ID to `backend/app/utils/model_loader.py`
2. Add model to `backend/scripts/download_models.py`
3. Rebuild Docker image to download the model

### Code Quality Checks

Run these commands before committing:

```bash
# Backend
cd backend && source .venv/bin/activate
black app/ && ruff check app/ --fix && mypy app/

# Frontend
cd frontend
npm run lint && npm run check
```

### Debugging

- Backend logs: Check Docker logs or terminal output
- Frontend: Use browser DevTools and SvelteKit debug mode
- API testing: Use FastAPI docs at `/docs` or tools like curl/Postman

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run formatting and linting checks
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **HuggingFace Transformers** for the ML framework
- **FastAPI** for the backend framework
- **SvelteKit** and **Svelte 5** for the frontend framework
- **GPT-2** model by OpenAI
