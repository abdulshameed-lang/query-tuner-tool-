"""Plan comparison API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
import logging

from app.schemas.plan_comparison import (
    PlanComparisonResponse,
    PlanComparison,
    RegressionAnalysis,
    RegressionFinding,
    ImprovementFinding,
    PlanDiff,
    SignificantChange,
    ComparisonRecommendation,
    BaselineRecommendation,
    PlanVersionsResponse,
    PlanVersionInfo,
    CompareRequest,
    BaselineRequest,
    PlanComparisonMetadata,
)
from app.services.plan_comparison_service import PlanComparisonService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{sql_id}/versions", response_model=PlanVersionsResponse)
async def get_plan_versions(
    sql_id: str,
    source: str = QueryParam(
        "current", description="Data source (current, historical, both)"
    ),
):
    """
    Get all execution plan versions for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **source**: Data source - 'current' (V$SQL_PLAN), 'historical' (DBA_HIST_SQL_PLAN), or 'both'

    Returns:
    - List of plan versions with metadata (plan_hash_value, timestamps, etc.)

    Raises:
    - 400: Invalid SQL_ID format or source
    - 404: No plan versions found
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

        # Validate source
        if source not in ["current", "historical", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SOURCE",
                    "message": "Source must be 'current', 'historical', or 'both'",
                },
            )

        # Get plan versions
        service = PlanComparisonService()
        versions = service.get_plan_versions(sql_id.upper(), source)

        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NO_PLAN_VERSIONS",
                    "message": f"No plan versions found for SQL_ID '{sql_id}'",
                    "sql_id": sql_id,
                },
            )

        # Convert to response model
        version_list = [PlanVersionInfo(**v) for v in versions]

        return PlanVersionsResponse(data=version_list, total_count=len(version_list))

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
        logger.error(f"Error fetching plan versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to fetch plan versions",
                "error": str(e),
            },
        )


@router.get("/{sql_id}/compare", response_model=PlanComparisonResponse)
async def compare_plans(
    sql_id: str,
    current_plan_hash: Optional[int] = QueryParam(
        None, description="Current plan hash value"
    ),
    historical_plan_hash: Optional[int] = QueryParam(
        None, description="Historical plan hash value to compare against"
    ),
    include_recommendations: bool = QueryParam(
        True, description="Include recommendations in response"
    ),
):
    """
    Compare current and historical execution plans for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **current_plan_hash**: Optional current plan hash value (defaults to latest)
    - **historical_plan_hash**: Optional historical plan hash to compare against (defaults to most recent historical)
    - **include_recommendations**: Whether to include recommendations (default: true)

    Returns:
    - Detailed plan comparison including regression analysis, operation changes, and recommendations

    Raises:
    - 400: Invalid SQL_ID format
    - 404: Plans not found for comparison
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

        # Get plan comparison
        service = PlanComparisonService()
        result = service.compare_plans(
            sql_id.upper(),
            current_plan_hash=current_plan_hash,
            historical_plan_hash=historical_plan_hash,
            include_recommendations=include_recommendations,
        )

        if not result.get("comparison_possible"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "COMPARISON_NOT_POSSIBLE",
                    "message": result.get(
                        "reason", "Plan comparison could not be performed"
                    ),
                    "sql_id": sql_id,
                },
            )

        # Convert to response model
        comparison = PlanComparison(
            comparison_possible=result["comparison_possible"],
            reason=result.get("reason"),
            plans_identical=result.get("plans_identical"),
            current_plan_hash=result.get("current_plan_hash"),
            historical_plan_hash=result.get("historical_plan_hash"),
            current_metadata=PlanComparisonMetadata(**result.get("current_metadata", {}))
            if result.get("current_metadata")
            else None,
            historical_metadata=PlanComparisonMetadata(
                **result.get("historical_metadata", {})
            )
            if result.get("historical_metadata")
            else None,
            current_metrics=result.get("current_metrics"),
            historical_metrics=result.get("historical_metrics"),
            regression_detected=result.get("regression_detected"),
            regression_analysis=RegressionAnalysis(
                has_regression=result["regression_analysis"]["has_regression"],
                regression_count=result["regression_analysis"]["regression_count"],
                improvement_count=result["regression_analysis"]["improvement_count"],
                severity=result["regression_analysis"]["severity"],
                regressions=[
                    RegressionFinding(**r)
                    for r in result["regression_analysis"]["regressions"]
                ],
                improvements=[
                    ImprovementFinding(**i)
                    for i in result["regression_analysis"]["improvements"]
                ],
            )
            if result.get("regression_analysis")
            else None,
            plan_diff=PlanDiff(**result["plan_diff"]) if result.get("plan_diff") else None,
            operation_changes=[
                SignificantChange(**c) for c in result.get("operation_changes", [])
            ],
            recommendations=[
                ComparisonRecommendation(**r) for r in result.get("recommendations", [])
            ],
            comparison_timestamp=result.get("comparison_timestamp"),
        )

        return PlanComparisonResponse(data=comparison)

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
        logger.error(f"Error comparing plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to compare plans",
                "error": str(e),
            },
        )


@router.post("/{sql_id}/baseline-recommendation", response_model=BaselineRecommendation)
async def get_baseline_recommendation(
    sql_id: str,
    request: BaselineRequest,
):
    """
    Get SQL Plan Baseline recommendation based on plan comparison.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **request**: Baseline request with current and preferred plan hashes

    Returns:
    - Baseline recommendation with creation SQL and instructions

    Raises:
    - 400: Invalid SQL_ID format or request
    - 404: Plans not found
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

        # Validate request
        if request.sql_id.upper() != sql_id.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "SQL_ID_MISMATCH",
                    "message": "SQL_ID in path and request body must match",
                },
            )

        # Get baseline recommendation
        service = PlanComparisonService()
        result = service.get_baseline_recommendation(
            sql_id=sql_id.upper(),
            current_plan_hash=request.current_plan_hash,
            preferred_plan_hash=request.preferred_plan_hash,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "PLANS_NOT_FOUND",
                    "message": "Could not generate baseline recommendation - plans not found",
                    "sql_id": sql_id,
                },
            )

        # Convert to response model
        recommendation = BaselineRecommendation(**result)

        return recommendation

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
        logger.error(f"Error generating baseline recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to generate baseline recommendation",
                "error": str(e),
            },
        )


@router.get("/{sql_id}/compare/{plan_hash_value}", response_model=PlanComparisonResponse)
async def compare_specific_plan(
    sql_id: str,
    plan_hash_value: int,
    compare_to: Optional[int] = QueryParam(
        None, description="Plan hash value to compare against"
    ),
):
    """
    Compare a specific plan against another plan version.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **plan_hash_value**: Plan hash value to analyze (current plan)
    - **compare_to**: Plan hash value to compare against (defaults to most recent historical)

    Returns:
    - Detailed plan comparison

    Raises:
    - 400: Invalid SQL_ID format
    - 404: Plans not found
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

        # Get plan comparison
        service = PlanComparisonService()
        result = service.compare_plans(
            sql_id.upper(),
            current_plan_hash=plan_hash_value,
            historical_plan_hash=compare_to,
        )

        if not result.get("comparison_possible"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "COMPARISON_NOT_POSSIBLE",
                    "message": result.get(
                        "reason", "Plan comparison could not be performed"
                    ),
                    "sql_id": sql_id,
                    "plan_hash_value": plan_hash_value,
                },
            )

        # Convert to response model (same as compare_plans endpoint)
        comparison = PlanComparison(
            comparison_possible=result["comparison_possible"],
            reason=result.get("reason"),
            plans_identical=result.get("plans_identical"),
            current_plan_hash=result.get("current_plan_hash"),
            historical_plan_hash=result.get("historical_plan_hash"),
            current_metadata=PlanComparisonMetadata(**result.get("current_metadata", {}))
            if result.get("current_metadata")
            else None,
            historical_metadata=PlanComparisonMetadata(
                **result.get("historical_metadata", {})
            )
            if result.get("historical_metadata")
            else None,
            current_metrics=result.get("current_metrics"),
            historical_metrics=result.get("historical_metrics"),
            regression_detected=result.get("regression_detected"),
            regression_analysis=RegressionAnalysis(
                has_regression=result["regression_analysis"]["has_regression"],
                regression_count=result["regression_analysis"]["regression_count"],
                improvement_count=result["regression_analysis"]["improvement_count"],
                severity=result["regression_analysis"]["severity"],
                regressions=[
                    RegressionFinding(**r)
                    for r in result["regression_analysis"]["regressions"]
                ],
                improvements=[
                    ImprovementFinding(**i)
                    for i in result["regression_analysis"]["improvements"]
                ],
            )
            if result.get("regression_analysis")
            else None,
            plan_diff=PlanDiff(**result["plan_diff"]) if result.get("plan_diff") else None,
            operation_changes=[
                SignificantChange(**c) for c in result.get("operation_changes", [])
            ],
            recommendations=[
                ComparisonRecommendation(**r) for r in result.get("recommendations", [])
            ],
            comparison_timestamp=result.get("comparison_timestamp"),
        )

        return PlanComparisonResponse(data=comparison)

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
        logger.error(f"Error comparing specific plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to compare specific plan",
                "error": str(e),
            },
        )
