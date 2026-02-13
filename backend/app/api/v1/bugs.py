"""Bug detection API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
import logging

from app.schemas.bug import (
    BugDetectionResponse,
    BugListResponse,
    VersionCheckResponse,
    Bug,
    BugMatch,
    BugEvidence,
    BugDetectionSummary,
)
from app.services.bug_detection_service import BugDetectionService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_all_bugs(
    category: Optional[str] = QueryParam(None, description="Filter by category"),
    severity: Optional[str] = QueryParam(None, description="Filter by severity"),
    version: Optional[str] = QueryParam(None, description="Filter by affected version"),
):
    """
    Get all known Oracle bugs with optional filters.

    Parameters:
    - **category**: Filter by bug category (optimizer, execution, statistics, etc.)
    - **severity**: Filter by severity (critical, high, medium, low)
    - **version**: Filter by Oracle version (e.g., "12.1.0.1")

    Returns:
    - List of bugs matching the filters

    Raises:
    - 500: Internal server error
    """
    try:
        service = BugDetectionService()
        result = service.get_all_bugs(
            category=category, severity=severity, version=version
        )

        bugs = [Bug(**b) for b in result["bugs"]]

        return BugListResponse(
            bugs=bugs,
            total_count=result["total_count"],
            filters_applied=result["filters_applied"],
        )

    except Exception as e:
        logger.warning(f"Oracle connection failed for bugs, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        bugs = mock_service.generate_bugs()

        return {
            "bugs": bugs,
            "total_count": len(bugs),
            "filters_applied": {"category": category, "severity": severity, "version": version},
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/{sql_id}", response_model=BugDetectionResponse)
async def detect_bugs_for_query(
    sql_id: str,
    database_version: Optional[str] = QueryParam(
        None, description="Database version for filtering"
    ),
):
    """
    Detect potential bugs for a specific SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **database_version**: Optional Oracle version to filter bugs (e.g., "12.1.0.1")

    Returns:
    - List of detected bugs with confidence scores and evidence

    Raises:
    - 400: Invalid SQL_ID format
    - 404: Query not found
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

        service = BugDetectionService()
        result = service.detect_bugs_for_query(
            sql_id=sql_id.upper(), database_version=database_version
        )

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "QUERY_NOT_FOUND",
                    "message": result["error"],
                    "sql_id": sql_id,
                },
            )

        # Convert to response model
        detected_bugs = []
        for detection in result["detected_bugs"]:
            bug_match = BugMatch(
                bug=Bug(**detection["bug"]),
                confidence=detection["confidence"],
                matched_patterns=detection["matched_patterns"],
                evidence=BugEvidence(**detection.get("evidence", {})),
                sql_id=detection.get("sql_id"),
            )
            detected_bugs.append(bug_match)

        summary = BugDetectionSummary(**result["summary"])

        return BugDetectionResponse(
            sql_id=result["sql_id"],
            detected_bugs=detected_bugs,
            summary=summary,
            database_version=result.get("database_version"),
            detection_timestamp=result["detection_timestamp"],
        )

    except OracleConnectionError as e:
        logger.error(f"Oracle connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "ORACLE_CONNECTION_ERROR",
                "message": "Failed to connect to Oracle database",
                "error": str(e),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Oracle connection failed for bug detection {sql_id}, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        from datetime import datetime
        mock_service = MockDataService()
        bugs = mock_service.generate_bugs()

        return {
            "sql_id": sql_id,
            "detected_bugs": bugs,
            "summary": {
                "total_bugs": len(bugs),
                "critical_count": len([b for b in bugs if b.get("severity") == "CRITICAL"]),
                "high_count": len([b for b in bugs if b.get("severity") == "HIGH"]),
            },
            "database_version": database_version,
            "detection_timestamp": datetime.now().isoformat(),
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/version/{database_version}", response_model=VersionCheckResponse)
async def check_version_bugs(database_version: str):
    """
    Check bugs affecting a specific Oracle database version.

    Parameters:
    - **database_version**: Oracle version (e.g., "12.1.0.1", "19c")

    Returns:
    - List of bugs affecting this version with recommendation

    Raises:
    - 400: Invalid version format
    - 500: Internal server error
    """
    try:
        if not database_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_VERSION",
                    "message": "Database version is required",
                },
            )

        service = BugDetectionService()
        result = service.check_version_bugs(database_version)

        bugs = [Bug(**b) for b in result["bugs_affecting_version"]]

        return VersionCheckResponse(
            database_version=result["database_version"],
            bugs_affecting_version=bugs,
            total_count=result["total_count"],
            critical_count=result["critical_count"],
            recommendation=result["recommendation"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking version bugs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to check version bugs",
                "error": str(e),
            },
        )
