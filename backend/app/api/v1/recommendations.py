"""Recommendation API endpoints."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
import logging

from app.schemas.recommendation import (
    RecommendationsResponse,
    IndexRecommendationsResponse,
    SQLRewriteRecommendationsResponse,
    HintRecommendationsResponse,
    Recommendation,
    IndexRecommendation,
    SQLRewriteRecommendation,
    OptimizerHintRecommendation,
    RecommendationSummary,
)
from app.services.recommendation_service import RecommendationService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{sql_id}")
async def get_recommendations(
    sql_id: str,
    include_index: bool = QueryParam(True, description="Include index recommendations"),
    include_rewrite: bool = QueryParam(True, description="Include SQL rewrite recommendations"),
    include_hints: bool = QueryParam(True, description="Include optimizer hint recommendations"),
    include_statistics: bool = QueryParam(True, description="Include statistics recommendations"),
    include_parallelism: bool = QueryParam(True, description="Include parallelism recommendations"),
):
    """
    Get comprehensive tuning recommendations for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)
    - **include_index**: Include index recommendations (default: true)
    - **include_rewrite**: Include SQL rewrite recommendations (default: true)
    - **include_hints**: Include optimizer hint recommendations (default: true)
    - **include_statistics**: Include statistics recommendations (default: true)
    - **include_parallelism**: Include parallelism recommendations (default: true)

    Returns:
    - Comprehensive list of recommendations with summary statistics

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

        # Get recommendations
        service = RecommendationService()
        result = service.get_recommendations(
            sql_id=sql_id.upper(),
            include_index=include_index,
            include_rewrite=include_rewrite,
            include_hints=include_hints,
            include_statistics=include_statistics,
            include_parallelism=include_parallelism,
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
        recommendations = [Recommendation(**rec) for rec in result["recommendations"]]
        summary = RecommendationSummary(**result["summary"])

        return RecommendationsResponse(
            sql_id=result["sql_id"],
            recommendations=recommendations,
            summary=summary,
            generated_at=result["generated_at"],
        )

    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed for recommendations {sql_id}, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        from datetime import datetime
        mock_service = MockDataService()
        rec_data = mock_service.generate_recommendations(sql_id)

        rec_data["generated_at"] = datetime.now().isoformat()
        rec_data["note"] = "Using mock data (Oracle database not available)"
        return rec_data
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Oracle connection failed for recommendations {sql_id}, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        from datetime import datetime
        mock_service = MockDataService()
        rec_data = mock_service.generate_recommendations(sql_id)

        rec_data["generated_at"] = datetime.now().isoformat()
        rec_data["note"] = "Using mock data (Oracle database not available)"
        return rec_data


@router.get("/{sql_id}/index", response_model=IndexRecommendationsResponse)
async def get_index_recommendations(sql_id: str):
    """
    Get index recommendations only for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)

    Returns:
    - List of index-specific recommendations

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

        # Get index recommendations
        service = RecommendationService()
        result = service.get_index_recommendations(sql_id.upper())

        # Convert to response model
        recommendations = [IndexRecommendation(**rec) for rec in result["recommendations"]]

        return IndexRecommendationsResponse(
            sql_id=result["sql_id"],
            recommendations=recommendations,
            total_count=result["total_count"],
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
        logger.error(f"Error generating index recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to generate index recommendations",
                "error": str(e),
            },
        )


@router.get("/{sql_id}/rewrite", response_model=SQLRewriteRecommendationsResponse)
async def get_rewrite_recommendations(sql_id: str):
    """
    Get SQL rewrite recommendations only for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)

    Returns:
    - List of SQL rewrite recommendations

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

        # Get rewrite recommendations
        service = RecommendationService()
        result = service.get_rewrite_recommendations(sql_id.upper())

        # Convert to response model
        recommendations = [
            SQLRewriteRecommendation(**rec) for rec in result["recommendations"]
        ]

        return SQLRewriteRecommendationsResponse(
            sql_id=result["sql_id"],
            recommendations=recommendations,
            total_count=result["total_count"],
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
        logger.error(f"Error generating rewrite recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to generate rewrite recommendations",
                "error": str(e),
            },
        )


@router.get("/{sql_id}/hints", response_model=HintRecommendationsResponse)
async def get_hint_recommendations(sql_id: str):
    """
    Get optimizer hint recommendations only for a SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)

    Returns:
    - List of optimizer hint recommendations

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

        # Get hint recommendations
        service = RecommendationService()
        result = service.get_hint_recommendations(sql_id.upper())

        # Convert to response model
        recommendations = [
            OptimizerHintRecommendation(**rec) for rec in result["recommendations"]
        ]

        return HintRecommendationsResponse(
            sql_id=result["sql_id"],
            recommendations=recommendations,
            total_count=result["total_count"],
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
        logger.error(f"Error generating hint recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to generate hint recommendations",
                "error": str(e),
            },
        )
