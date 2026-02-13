"""Connection endpoints for database connectivity."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import logging

from app.core.oracle.connection import (
    get_connection_manager,
    OracleConnectionError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionTestResponse(BaseModel):
    """Response model for connection test."""

    status: str
    version: str
    database: str
    user: str
    dsn: str


class PoolStatsResponse(BaseModel):
    """Response model for pool statistics."""

    status: str
    min_size: int = Field(default=0)
    max_size: int = Field(default=0)
    busy_count: int = Field(default=0)
    open_count: int = Field(default=0)
    timeout: int = Field(default=0)


@router.get("/test", response_model=ConnectionTestResponse)
async def test_connection():
    """
    Test Oracle database connection.

    Returns:
        Connection test results including database version and name

    Raises:
        HTTPException: If connection test fails
    """
    try:
        manager = get_connection_manager()
        result = manager.test_connection()
        return result
    except OracleConnectionError as e:
        logger.error(f"Connection test failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error during connection test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during connection test",
        )


@router.get("/pool/stats", response_model=PoolStatsResponse)
async def get_pool_stats():
    """
    Get connection pool statistics.

    Returns:
        Connection pool statistics

    Raises:
        HTTPException: If unable to get pool stats
    """
    try:
        manager = get_connection_manager()
        stats = manager.get_pool_stats()
        return stats
    except OracleConnectionError as e:
        logger.error(f"Failed to get pool stats: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error getting pool stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting pool statistics",
        )
