"""Deadlock detection API endpoints."""

from fastapi import APIRouter, HTTPException, status
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_deadlocks():
    """
    Get detected deadlocks from the database.

    Returns:
    - List of deadlocks with session and resource information

    Raises:
    - 502: Oracle connection error
    """
    try:
        # This would normally query Oracle for deadlock information
        # For now, return mock data
        logger.warning("Oracle connection not implemented, using mock data")
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        deadlocks = mock_service.generate_deadlocks()

        return {
            "deadlocks": deadlocks,
            "total_count": len(deadlocks),
            "note": "Using mock data (Oracle database not available)"
        }

    except Exception as e:
        logger.warning(f"Error fetching deadlocks, using mock data: {e}")
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        deadlocks = mock_service.generate_deadlocks()

        return {
            "deadlocks": deadlocks,
            "total_count": len(deadlocks),
            "note": "Using mock data (Oracle database not available)"
        }
