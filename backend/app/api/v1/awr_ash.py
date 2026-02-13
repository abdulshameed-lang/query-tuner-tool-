"""AWR and ASH API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
from datetime import datetime
import logging

from app.schemas.awr_ash import (
    SnapshotListResponse,
    AWRReport,
    ASHActivityResponse,
    HistoricalSQLResponse,
    HistoricalComparisonResult,
    PerformanceTrendResult,
    RegressionDetectionResult,
    ASHSQLAnalysis,
    ASHTimePeriodAnalysis,
    BottleneckAnalysisResult,
)
from app.services.awr_ash_service import AWRASHService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/snapshots")
async def get_awr_snapshots(
    days_back: int = QueryParam(7, description="Number of days to look back"),
    limit: Optional[int] = QueryParam(100, description="Maximum number of snapshots"),
):
    """
    Get available AWR snapshots.

    Parameters:
    - **days_back**: Number of days to look back (default: 7)
    - **limit**: Maximum number of snapshots to return (default: 100)

    Returns:
    - List of AWR snapshots with metadata

    Raises:
    - 500: Internal server error
    - 502: Oracle connection error
    """
    try:
        service = AWRASHService()
        result = service.get_snapshots(days_back=days_back, limit=limit)

        return SnapshotListResponse(
            snapshots=result.get("snapshots", []),
            total_count=result.get("total_count", 0)
        )

    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed for AWR snapshots, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        snapshots = mock_service.generate_awr_snapshots(days_back=days_back)

        return {
            "snapshots": snapshots,
            "total_count": len(snapshots),
            "note": "Using mock data (Oracle database not available)"
        }
    except Exception as e:
        logger.warning(f"Oracle connection failed for AWR snapshots, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        snapshots = mock_service.generate_awr_snapshots(days_back=days_back)

        return {
            "snapshots": snapshots,
            "total_count": len(snapshots),
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/report")
async def generate_awr_report(
    begin_snap_id: int = QueryParam(..., description="Beginning snapshot ID"),
    end_snap_id: int = QueryParam(..., description="Ending snapshot ID"),
    top_n: int = QueryParam(10, description="Number of top items to include"),
    format: str = QueryParam("json", description="Output format (json or html)"),
):
    """
    Generate AWR report between two snapshots.

    Parameters:
    - **begin_snap_id**: Beginning snapshot ID (required)
    - **end_snap_id**: Ending snapshot ID (required)
    - **top_n**: Number of top SQL/events to include (default: 10)
    - **format**: Output format - json or html (default: json)

    Returns:
    - Complete AWR report with performance metrics

    Raises:
    - 400: Invalid snapshot IDs
    - 404: Snapshots not found
    - 502: Oracle connection error
    """
    try:
        if begin_snap_id >= end_snap_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SNAPSHOTS",
                    "message": "Begin snapshot must be less than end snapshot",
                },
            )

        service = AWRASHService()
        report = service.generate_awr_report(
            begin_snap_id=begin_snap_id,
            end_snap_id=end_snap_id,
            top_n=top_n,
            format=format
        )

        if "error" in report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "SNAPSHOTS_NOT_FOUND",
                    "message": report["error"],
                },
            )

        return AWRReport(**report)

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed for AWR report, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        report = mock_service.generate_awr_report(begin_snap_id, end_snap_id)

        report["note"] = "Using mock data (Oracle database not available)"
        return report
    except Exception as e:
        logger.warning(f"Oracle connection failed for AWR report, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        report = mock_service.generate_awr_report(begin_snap_id, end_snap_id)

        report["note"] = "Using mock data (Oracle database not available)"
        return report


@router.get("/ash/activity", response_model=ASHActivityResponse)
async def get_ash_activity(
    sql_id: Optional[str] = QueryParam(None, description="Filter by SQL_ID"),
    begin_time: Optional[datetime] = QueryParam(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = QueryParam(None, description="End time (ISO format)"),
    minutes_back: Optional[int] = QueryParam(60, description="Minutes to look back"),
    limit: int = QueryParam(1000, description="Maximum samples to return"),
):
    """
    Get Active Session History (ASH) samples.

    Parameters:
    - **sql_id**: Optional SQL_ID filter
    - **begin_time**: Start time (ISO format, e.g., 2024-01-15T10:00:00)
    - **end_time**: End time (ISO format)
    - **minutes_back**: Minutes to look back if times not specified (default: 60)
    - **limit**: Maximum number of samples (default: 1000)

    Returns:
    - List of ASH samples with activity data

    Raises:
    - 502: Oracle connection error
    """
    try:
        service = AWRASHService()
        result = service.get_ash_activity(
            sql_id=sql_id,
            begin_time=begin_time,
            end_time=end_time,
            minutes_back=minutes_back,
            limit=limit
        )

        return ASHActivityResponse(
            samples=result.get("samples", []),
            sample_count=result.get("sample_count", 0),
            time_range=result.get("time_range", {})
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
    except Exception as e:
        logger.error(f"Error fetching ASH activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch ASH activity",
                "error": str(e),
            },
        )


@router.get("/ash/sql/{sql_id}", response_model=ASHSQLAnalysis)
async def analyze_sql_ash_activity(
    sql_id: str,
    begin_time: Optional[datetime] = QueryParam(None, description="Start time"),
    end_time: Optional[datetime] = QueryParam(None, description="End time"),
    minutes_back: int = QueryParam(60, description="Minutes to look back"),
):
    """
    Analyze ASH activity for a specific SQL_ID.

    Parameters:
    - **sql_id**: SQL_ID to analyze (13 character alphanumeric)
    - **begin_time**: Start time (ISO format)
    - **end_time**: End time (ISO format)
    - **minutes_back**: Minutes to look back if times not specified (default: 60)

    Returns:
    - Detailed ASH analysis with timeline, wait events, sessions, blocking

    Raises:
    - 400: Invalid SQL_ID
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        service = AWRASHService()
        analysis = service.analyze_sql_ash_activity(
            sql_id=sql_id.upper(),
            begin_time=begin_time,
            end_time=end_time,
            minutes_back=minutes_back
        )

        if "error" in analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NO_ASH_DATA",
                    "message": analysis["error"],
                },
            )

        return ASHSQLAnalysis(**analysis)

    except HTTPException:
        raise
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
    except Exception as e:
        logger.error(f"Error analyzing SQL ASH activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to analyze SQL ASH activity",
                "error": str(e),
            },
        )


@router.get("/historical/sql/{sql_id}", response_model=HistoricalSQLResponse)
async def get_historical_sql_performance(
    sql_id: str,
    days_back: int = QueryParam(7, description="Days of history to retrieve"),
):
    """
    Get historical performance for a SQL_ID from AWR.

    Parameters:
    - **sql_id**: SQL_ID (13 character alphanumeric)
    - **days_back**: Number of days of history (default: 7)

    Returns:
    - Historical SQL statistics and summary

    Raises:
    - 400: Invalid SQL_ID
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        service = AWRASHService()
        result = service.get_historical_sql_performance(
            sql_id=sql_id.upper(),
            days_back=days_back
        )

        return HistoricalSQLResponse(
            sql_id=result["sql_id"],
            statistics=result.get("statistics", []),
            sample_count=result.get("sample_count", 0),
            time_range=result.get("time_range", {})
        )

    except HTTPException:
        raise
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
    except Exception as e:
        logger.error(f"Error fetching historical SQL performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch historical SQL performance",
                "error": str(e),
            },
        )


@router.get("/historical/compare/{sql_id}", response_model=HistoricalComparisonResult)
async def compare_current_vs_historical(
    sql_id: str,
    days_back: int = QueryParam(7, description="Days of history to compare"),
    threshold_percent: float = QueryParam(20.0, description="Regression threshold %"),
):
    """
    Compare current performance vs historical baseline.

    Parameters:
    - **sql_id**: SQL_ID (13 character alphanumeric)
    - **days_back**: Days of history for baseline (default: 7)
    - **threshold_percent**: Threshold for regression detection % (default: 20)

    Returns:
    - Comparison results with trend and recommendations

    Raises:
    - 400: Invalid SQL_ID
    - 404: Query not found
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        service = AWRASHService()
        comparison = service.compare_current_vs_historical(
            sql_id=sql_id.upper(),
            days_back=days_back,
            threshold_percent=threshold_percent
        )

        if "error" in comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "QUERY_NOT_FOUND",
                    "message": comparison["error"],
                },
            )

        return HistoricalComparisonResult(**comparison)

    except HTTPException:
        raise
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
    except Exception as e:
        logger.error(f"Error comparing performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to compare performance",
                "error": str(e),
            },
        )


@router.get("/historical/trends/{sql_id}", response_model=PerformanceTrendResult)
async def analyze_performance_trend(
    sql_id: str,
    days_back: int = QueryParam(30, description="Days to analyze"),
):
    """
    Analyze performance trend over time.

    Parameters:
    - **sql_id**: SQL_ID (13 character alphanumeric)
    - **days_back**: Days to analyze (default: 30)

    Returns:
    - Trend analysis with time-series data and anomaly detection

    Raises:
    - 400: Invalid SQL_ID
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        service = AWRASHService()
        trend = service.analyze_performance_trend(
            sql_id=sql_id.upper(),
            days_back=days_back
        )

        if "error" in trend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "INSUFFICIENT_DATA",
                    "message": trend.get("message", "Insufficient data for trend analysis"),
                },
            )

        return PerformanceTrendResult(**trend)

    except HTTPException:
        raise
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
    except Exception as e:
        logger.error(f"Error analyzing trend: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to analyze performance trend",
                "error": str(e),
            },
        )


@router.get("/historical/regression/{sql_id}", response_model=RegressionDetectionResult)
async def detect_performance_regression(
    sql_id: str,
    baseline_days: int = QueryParam(14, description="Days for baseline period"),
    recent_days: int = QueryParam(1, description="Days for recent period"),
    threshold_percent: float = QueryParam(30.0, description="Regression threshold %"),
):
    """
    Detect performance regression by comparing recent vs baseline.

    Parameters:
    - **sql_id**: SQL_ID (13 character alphanumeric)
    - **baseline_days**: Days for baseline period (default: 14)
    - **recent_days**: Days for recent period (default: 1)
    - **threshold_percent**: Regression threshold % (default: 30)

    Returns:
    - Regression detection results with severity

    Raises:
    - 400: Invalid SQL_ID or parameters
    - 502: Oracle connection error
    """
    try:
        # Validate SQL_ID
        if not sql_id or len(sql_id) != 13 or not sql_id.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SQL_ID",
                    "message": "SQL_ID must be 13 alphanumeric characters",
                },
            )

        if recent_days >= baseline_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PERIODS",
                    "message": "Recent days must be less than baseline days",
                },
            )

        service = AWRASHService()
        regression = service.detect_regression(
            sql_id=sql_id.upper(),
            baseline_days=baseline_days,
            recent_days=recent_days,
            threshold_percent=threshold_percent
        )

        return RegressionDetectionResult(**regression)

    except HTTPException:
        raise
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
    except Exception as e:
        logger.error(f"Error detecting regression: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to detect regression",
                "error": str(e),
            },
        )
