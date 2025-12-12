"""
AI Token Wheel - FastAPI Backend Application
Main application entry point.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import HealthResponse, ModelsResponse, ReadyResponse
from app.routers import sessions
from app.utils.model_loader import get_available_models, is_model_loaded, load_model
from app.utils.session_manager import session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def cleanup_sessions_task():
    """Background task to periodically clean up expired sessions."""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        try:
            expired_count = session_manager.cleanup_expired_sessions(ttl_hours=1)
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI Token Wheel Backend...")

    # Pre-load default model
    try:
        logger.info("Pre-loading default model (gpt2)...")
        load_model("gpt2")
        logger.info("Default model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load default model: {e}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_sessions_task())
    logger.info("Started background session cleanup task")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down AI Token Wheel Backend...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AI Token Wheel API",
    description=(
        "Educational backend for visualizing LLM token probability " "distributions"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Token Wheel API",
        "version": "1.0.0",
        "description": (
            "Educational backend for visualizing LLM token probability " "distributions"
        ),
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    return HealthResponse(
        status="healthy",
        model_loaded=is_model_loaded("gpt2"),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness check - models must be loaded."""
    from fastapi import HTTPException

    if not is_model_loaded("gpt2"):
        raise HTTPException(status_code=503, detail="Models not loaded")
    return ReadyResponse(status="ready")


@app.get("/api/models", response_model=ModelsResponse)
async def list_models():
    """Returns list of available models for session creation."""
    models = get_available_models()
    return ModelsResponse(models=models)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
