"""Main API router aggregating all endpoint routers."""

from fastapi import APIRouter

from app.api.v1 import health, auth, user_connections, connections, queries, execution_plans, wait_events, plan_comparison, recommendations, bugs, awr_ash, deadlocks

# Create main API router
api_router = APIRouter()

# Include authentication endpoints (no auth required)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include health check endpoints
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Include user connection management endpoints (auth required)
api_router.include_router(user_connections.router, prefix="/user-connections", tags=["user-connections"])

# Include connection endpoints
api_router.include_router(connections.router, prefix="/connections", tags=["connections"])

# Include query endpoints
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])

# Include execution plan endpoints
api_router.include_router(execution_plans.router, prefix="/execution-plans", tags=["execution-plans"])

# Include wait event endpoints
api_router.include_router(wait_events.router, prefix="/wait-events", tags=["wait-events"])

# Include plan comparison endpoints
api_router.include_router(plan_comparison.router, prefix="/plan-comparison", tags=["plan-comparison"])

# Include recommendation endpoints
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

# Include bug detection endpoints
api_router.include_router(bugs.router, prefix="/bugs", tags=["bugs"])

# Include AWR/ASH endpoints
api_router.include_router(awr_ash.router, prefix="/awr-ash", tags=["awr-ash"])

# Include deadlock endpoints
api_router.include_router(deadlocks.router, prefix="/deadlocks", tags=["deadlocks"])


@api_router.get("/")
async def api_root():
    """API v1 root endpoint."""
    return {
        "message": "Query Tuner API v1",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "health": "/api/v1/health",
            "user-connections": "/api/v1/user-connections",
            "connections": "/api/v1/connections",
            "queries": "/api/v1/queries",
            "execution-plans": "/api/v1/execution-plans",
            "wait-events": "/api/v1/wait-events",
            "plan-comparison": "/api/v1/plan-comparison",
            "recommendations": "/api/v1/recommendations",
            "bugs": "/api/v1/bugs",
            "awr-ash": "/api/v1/awr-ash",
            "deadlocks": "/api/v1/deadlocks",
            "statistics": "/api/v1/statistics (coming soon)",
        },
    }
