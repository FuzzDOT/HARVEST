"""
FastAPI Application Entry Point
Main application configuration and setup for HARVEST backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from app.config import settings
from app.api import predict, trends, alerts, marketplace, health
from app.core.database import init_db
from app.core.scheduler import start_scheduler
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting HARVEST backend application...")
    await init_db()
    start_scheduler()
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HARVEST backend application...")


# Create FastAPI application
app = FastAPI(
    title="HARVEST API",
    description="Agricultural Prediction and Marketplace Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(predict.router, prefix="/api/v1", tags=["predictions"])
app.include_router(trends.router, prefix="/api/v1", tags=["trends"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to HARVEST API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )