"""Query endpoints for retrieving and analyzing SQL queries."""

from fastapi import APIRouter, HTTPException, status, Query as QueryParam
from typing import Optional
import logging

from app.schemas.query import (
    QueryListResponse,
    QueryDetailResponse,
    QueryFilters,
    QuerySort,
    PaginationParams,
    PaginationMetadata,
    Query as QueryModel,
    QueryDetail,
)
from app.services.query_service import QueryService
from app.core.oracle.connection import OracleConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_queries(
    # Pagination
    page: int = QueryParam(1, ge=1, description="Page number"),
    page_size: int = QueryParam(20, ge=1, le=100, description="Items per page"),
    # Filters
    min_elapsed_time: Optional[float] = QueryParam(None, ge=0, description="Minimum elapsed time (microseconds)"),
    min_executions: Optional[int] = QueryParam(None, ge=0, description="Minimum executions"),
    schema: Optional[str] = QueryParam(None, max_length=128, description="Filter by schema"),
    exclude_system_schemas: bool = QueryParam(True, description="Exclude system schemas"),
    sql_text_contains: Optional[str] = QueryParam(None, max_length=500, description="SQL text search"),
    # Sorting
    sort_by: str = QueryParam("elapsed_time", description="Sort field"),
    order: str = QueryParam("desc", description="Sort order (asc/desc)"),
):
    """
    Get list of queries with filtering, sorting, and pagination.

    Retrieves queries from V$SQL with performance metrics.

    Parameters:
    - **page**: Page number (1-based)
    - **page_size**: Number of items per page (max 100)
    - **min_elapsed_time**: Filter queries with elapsed time >= this value
    - **min_executions**: Filter queries with executions >= this value
    - **schema**: Filter by specific schema name
    - **exclude_system_schemas**: Exclude SYS, SYSTEM, etc.
    - **sql_text_contains**: Search in SQL text
    - **sort_by**: Field to sort by
    - **order**: Sort order (asc or desc)

    Returns:
    - List of queries with pagination metadata
    """
    try:
        # Build filters
        filters = QueryFilters(
            min_elapsed_time=min_elapsed_time,
            min_executions=min_executions,
            schema=schema,
            exclude_system_schemas=exclude_system_schemas,
            sql_text_contains=sql_text_contains,
        )

        # Build sort
        sort = QuerySort(sort_by=sort_by, order=order)

        # Build pagination
        pagination = PaginationParams(page=page, page_size=page_size)

        # Get queries
        service = QueryService()
        queries, total_count = service.get_queries(filters, sort, pagination)

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        pagination_meta = PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

        # Convert to response models
        query_models = [QueryModel(**q) for q in queries]

        return QueryListResponse(
            data=query_models,
            pagination=pagination_meta,
            filters=filters,
            sort=sort,
        )

    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed, using mock data: {e.message}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        queries = mock_service.generate_queries(limit=min(page_size, 50))

        # Return simple format for frontend compatibility
        return {
            "queries": queries,
            "note": "Using mock data (Oracle database not available)"
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": str(e)},
        )
    except Exception as e:
        logger.warning(f"Oracle connection failed, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        queries = mock_service.generate_queries(limit=min(page_size, 50))

        # Return simple format for frontend compatibility
        return {
            "queries": queries,
            "note": "Using mock data (Oracle database not available)"
        }


@router.get("/{sql_id}")
async def get_query_by_id(sql_id: str):
    """
    Get detailed information for a specific query by SQL_ID.

    Parameters:
    - **sql_id**: Oracle SQL_ID (13 character alphanumeric identifier)

    Returns:
    - Detailed query information with statistics

    Raises:
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

        # Get query
        service = QueryService()
        result = service.get_query_by_id(sql_id.upper())

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "QUERY_NOT_FOUND",
                    "message": f"Query with SQL_ID '{sql_id}' not found",
                    "sql_id": sql_id,
                },
            )

        # Convert to response model
        query_detail = QueryDetail(**result["query"])

        return QueryDetailResponse(
            data=query_detail,
            statistics=result.get("statistics"),
        )

    except HTTPException:
        raise
    except OracleConnectionError as e:
        logger.warning(f"Oracle connection failed for query {sql_id}, using mock data: {e.message}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        queries = mock_service.generate_queries(limit=1)

        if queries:
            query = queries[0]
            query['sql_id'] = sql_id  # Use the requested SQL_ID
            return {
                "query": query,
                "note": "Using mock data (Oracle database not available)"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "QUERY_NOT_FOUND",
                    "message": f"Query with SQL_ID '{sql_id}' not found",
                    "sql_id": sql_id,
                },
            )
    except Exception as e:
        logger.warning(f"Oracle connection failed for query {sql_id}, using mock data: {e}")
        # Fallback to mock data for testing
        from app.services.mock_data_service import MockDataService
        mock_service = MockDataService()
        queries = mock_service.generate_queries(limit=1)

        if queries:
            query = queries[0]
            query['sql_id'] = sql_id  # Use the requested SQL_ID
            return {
                "query": query,
                "note": "Using mock data (Oracle database not available)"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "QUERY_NOT_FOUND",
                    "message": f"Query with SQL_ID '{sql_id}' not found",
                    "sql_id": sql_id,
                },
            )


@router.get("/summary/stats")
async def get_query_summary():
    """
    Get summary statistics for all queries.

    Returns:
    - Summary statistics including total queries, executions, and queries needing tuning
    """
    try:
        service = QueryService()
        summary = service.get_query_summary()
        return {"data": summary}

    except OracleConnectionError as e:
        logger.error(f"Oracle error fetching summary: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error fetching query summary",
        )
