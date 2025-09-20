"""
Health Check API Endpoints
Provides health monitoring and status endpoints for the HARVEST application.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import psutil
import time
from datetime import datetime

from app.core.database import get_db_health
from app.core.cache import get_cache_health
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns the current status of the application.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "HARVEST API",
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with system metrics and dependency status.
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check dependencies
        db_status = await get_db_health()
        cache_status = await get_cache_health()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "HARVEST API",
            "version": "1.0.0",
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "dependencies": {
                "database": db_status,
                "cache": cache_status
            }
        }
        
        # Determine overall health
        if not db_status["healthy"] or not cache_status["healthy"]:
            health_data["status"] = "degraded"
        
        if cpu_percent > 90 or memory.percent > 90:
            health_data["status"] = "degraded"
            
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes deployments.
    """
    try:
        # Check if all critical services are ready
        db_status = await get_db_health()
        cache_status = await get_cache_health()
        
        if db_status["healthy"] and cache_status["healthy"]:
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready"
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes deployments.
    """
    return {"status": "alive"}