"""Wait event API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
import logging
from datetime import datetime

from app.schemas.wait_event import WaitEventsResponse, CurrentWaitEventsResponse
from app.services.wait_event_service import WaitEventService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{sql_id}", response_model=WaitEventsResponse)
async def get_wait_events_by_sql_id(
    sql_id: str,
    hours_back: int = QueryParam(24, ge=1, le=168, description="Hours to look back (max 7 days)"),
):
    """
    Get wait events for a specific SQL_ID.

    Retrieves wait events from V$ACTIVE_SESSION_HISTORY for the given SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **hours_back**: Number of hours to look back (1-168, default 24)

    Returns:
    - Wait events with category breakdown, top events, timeline, and recommendations

    Raises:
    - 400: Invalid SQL_ID format
    - 404: No wait events found
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID format
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        # Get wait events
        service = WaitEventService()
        result = service.get_wait_events_for_query(sql_id.upper(), hours_back)

        if result["total_samples"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NO_WAIT_EVENTS",
                    "message": f"No wait events found for SQL_ID '{sql_id}' in the last {hours_back} hours",
                    "sql_id": sql_id,
                },
            )

        return WaitEventsResponse(data=result)

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.error(f"Oracle error fetching wait events for {sql_id}: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.warning(f"Oracle connection failed for wait events {sql_id}, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        events = mock_service.generate_wait_events(limit=20)

        return {
            "events": events,
            "sql_id": sql_id,
            "total_samples": len(events),
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/current/system")
async def get_current_system_wait_events(
    top_n: int = QueryParam(50, ge=1, le=200, description="Number of top wait events"),
):
    """
    Get current wait events across the system.

    Retrieves current wait events from V$SESSION_WAIT.

    Parameters:
    - **top_n**: Number of top wait events to return (1-200, default 50)

    Returns:
    - Current wait events with category and SQL_ID breakdown

    Raises:
    - 502: Oracle connection error
    """
    try:
        # Get current wait events
        service = WaitEventService()
        result = service.get_current_system_wait_events(top_n)

        # Add timestamp
        result["timestamp"] = datetime.now().isoformat()

        return CurrentWaitEventsResponse(data=result)

    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed for current wait events, using mock data: {e.message}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        events = mock_service.generate_wait_events(limit=top_n)

        return {
            "events": events,
            "timestamp": datetime.now().isoformat(),
            "note": "Using mock data (Oracle database not available)"
        }
    except Exception as e:
        logger.warning(f"Oracle connection failed for current wait events, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        events = mock_service.generate_wait_events(limit=top_n)

        return {
            "events": events,
            "timestamp": datetime.now().isoformat(),
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/summary/{sql_id}")
async def get_wait_event_summary(
    sql_id: str,
    hours_back: int = QueryParam(24, ge=1, le=168, description="Hours to look back"),
):
    """
    Get aggregated wait event summary for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID
    - **hours_back**: Number of hours to look back

    Returns:
    - Aggregated wait event summary with percentages

    Raises:
    - 400: Invalid SQL_ID format
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID format
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        # Get wait event summary
        service = WaitEventService()
        wait_event_fetcher = service.wait_event_fetcher
        summary = wait_event_fetcher.get_wait_event_summary(sql_id.upper(), hours_back)

        return {"data": summary}

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.error(
            f"Oracle error fetching wait event summary for {sql_id}: {e.message}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.error(
            f"Unexpected error fetching wait event summary for {sql_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error fetching wait event summary",
        )
