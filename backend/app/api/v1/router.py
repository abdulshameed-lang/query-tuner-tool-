"""Main API router aggregating all endpoint routers."""

from fastapi import APIRouter
import logging
import os

logger = logging.getLogger(__name__)

# Always import non-Oracle endpoints
from app.api.v1 import health, auth, user_connections

# Create main API router
api_router = APIRouter()

# Always include authentication and health endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(user_connections.router, prefix="/user-connections", tags=["user-connections"])

# Conditionally import Oracle-dependent endpoints (only if cx_Oracle is available)
ORACLE_ENDPOINTS_AVAILABLE = False
try:
    import cx_Oracle
    # If cx_Oracle is available, import Oracle-dependent modules
    from app.api.v1 import (
        connections,
        queries,
        execution_plans,
        wait_events,
        plan_comparison,
        recommendations,
        bugs,
        awr_ash,
        deadlocks
    )

    # Include Oracle-dependent endpoints
    api_router.include_router(connections.router, prefix="/connections", tags=["connections"])
    api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
    api_router.include_router(execution_plans.router, prefix="/execution-plans", tags=["execution-plans"])
    api_router.include_router(wait_events.router, prefix="/wait-events", tags=["wait-events"])
    api_router.include_router(plan_comparison.router, prefix="/plan-comparison", tags=["plan-comparison"])
    api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
    api_router.include_router(bugs.router, prefix="/bugs", tags=["bugs"])
    api_router.include_router(awr_ash.router, prefix="/awr-ash", tags=["awr-ash"])
    api_router.include_router(deadlocks.router, prefix="/deadlocks", tags=["deadlocks"])

    ORACLE_ENDPOINTS_AVAILABLE = True
    logger.info("Oracle endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Oracle endpoints not available (Railway mode): {e}")
    ORACLE_ENDPOINTS_AVAILABLE = False


@api_router.get("/")
async def api_root():
    """API v1 root endpoint."""
    base_endpoints = {
        "auth": "/api/v1/auth",
        "health": "/api/v1/health",
        "user-connections": "/api/v1/user-connections",
    }

    oracle_endpoints = {
        "connections": "/api/v1/connections",
        "queries": "/api/v1/queries",
        "execution-plans": "/api/v1/execution-plans",
        "wait-events": "/api/v1/wait-events",
        "plan-comparison": "/api/v1/plan-comparison",
        "recommendations": "/api/v1/recommendations",
        "bugs": "/api/v1/bugs",
        "awr-ash": "/api/v1/awr-ash",
        "deadlocks": "/api/v1/deadlocks",
    } if ORACLE_ENDPOINTS_AVAILABLE else {}

    return {
        "message": "Query Tuner API v1",
        "version": "1.0.0",
        "mode": "full" if ORACLE_ENDPOINTS_AVAILABLE else "railway (auth only)",
        "endpoints": {**base_endpoints, **oracle_endpoints},
    }
