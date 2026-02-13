"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import logging

from app.config import settings
from app.core.oracle.connection import get_connection_manager, OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    timestamp: str
    environment: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Response model for detailed health check."""

    status: str
    timestamp: str
    environment: str
    version: str
    components: dict


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "0.1.0",
    }


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check including all components.

    Returns:
        Detailed health status of all components
    """
    components = {}

    # Check Oracle connection
    try:
        manager = get_connection_manager()
        pool_stats = manager.get_pool_stats()
        components["oracle"] = {
            "status": "healthy",
            "pool_status": pool_stats.get("status", "unknown"),
            "connections": {
                "busy": pool_stats.get("busy_count", 0),
                "open": pool_stats.get("open_count", 0),
                "max": pool_stats.get("max_size", 0),
            },
        }
    except OracleConnectionError as e:
        components["oracle"] = {
            "status": "unhealthy",
            "error": e.message,
        }
    except Exception as e:
        components["oracle"] = {
            "status": "unknown",
            "error": str(e),
        }

    # Check Redis (TODO: implement when Redis is integrated)
    components["redis"] = {
        "status": "not_implemented",
        "message": "Redis health check not yet implemented",
    }

    # Determine overall status
    oracle_healthy = components.get("oracle", {}).get("status") == "healthy"
    overall_status = "healthy" if oracle_healthy else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "0.1.0",
        "components": components,
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.

    Returns:
        200 if ready, 503 if not ready
    """
    try:
        manager = get_connection_manager()
        manager.test_connection()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e)}, 503


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.

    Returns:
        200 if alive
    """
    return {"status": "alive"}
