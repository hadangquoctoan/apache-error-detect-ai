# FastAPI Application Entry Point
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.api.v1.endpoints import router as api_v1_router


# Configure Loguru
def configure_logging():
    """Configure application logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.app.log_level,
    )
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.app.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("Starting AI Log Analyzer...")
    logger.info(f"Environment: {settings.app.env}")
    logger.info(f"LLM Provider: {settings.llm.provider}")
    logger.info(f"Model: {settings.llm.gemini.model}")

    yield

    logger.info("Shutting down AI Log Analyzer...")


# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    configure_logging()

    app = FastAPI(
        title="AI Log Analyzer",
        description="AI-powered Apache log analysis for automated incident diagnosis",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_v1_router)

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.app.debug else "An error occurred",
                "path": str(request.url),
            }
        )

    return app


# Create app instance
app = create_app()


# Run directly
if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server at http://{settings.api.host}:{settings.api.port}")

    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )
