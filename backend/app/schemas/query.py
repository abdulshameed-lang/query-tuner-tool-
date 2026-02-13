"""Pydantic schemas for query-related API endpoints."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


class QueryBase(BaseModel):
    """Base query model with common fields."""

    sql_id: str = Field(..., description="Oracle SQL_ID (13 character identifier)")
    sql_text: str = Field(..., description="SQL statement text")
    parsing_schema_name: Optional[str] = Field(None, description="Schema that parsed the SQL")


class Query(QueryBase):
    """Complete query model with performance metrics."""

    elapsed_time: float = Field(..., description="Total elapsed time in microseconds")
    cpu_time: float = Field(..., description="Total CPU time in microseconds")
    executions: int = Field(..., description="Number of executions")
    buffer_gets: int = Field(..., description="Number of buffer gets")
    disk_reads: int = Field(..., description="Number of disk reads")
    rows_processed: int = Field(..., description="Number of rows processed")

    # Average metrics
    avg_elapsed_time: Optional[float] = Field(None, description="Average elapsed time per execution")
    avg_cpu_time: Optional[float] = Field(None, description="Average CPU time per execution")
    avg_buffer_gets: Optional[float] = Field(None, description="Average buffer gets per execution")

    # Additional fields
    fetches: Optional[int] = Field(None, description="Number of fetches")
    sorts: Optional[int] = Field(None, description="Number of sorts")
    parse_calls: Optional[int] = Field(None, description="Number of parse calls")
    optimizer_cost: Optional[int] = Field(None, description="Optimizer cost")
    optimizer_mode: Optional[str] = Field(None, description="Optimizer mode")
    last_active_time: Optional[str] = Field(None, description="Last active time (ISO format)")
    first_load_time: Optional[str] = Field(None, description="First load time (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {
                "sql_id": "abc123xyz4567",
                "sql_text": "SELECT * FROM users WHERE id = :1",
                "parsing_schema_name": "APP_SCHEMA",
                "elapsed_time": 1234567.89,
                "cpu_time": 987654.32,
                "executions": 100,
                "buffer_gets": 50000,
                "disk_reads": 1000,
                "rows_processed": 100,
                "avg_elapsed_time": 12345.67,
                "avg_cpu_time": 9876.54,
                "avg_buffer_gets": 500.0,
            }
        }


class QueryDetail(Query):
    """Detailed query model with additional fields."""

    sql_fulltext: Optional[str] = Field(None, description="Complete SQL text (for long queries)")
    module: Optional[str] = Field(None, description="Application module")
    action: Optional[str] = Field(None, description="Application action")
    direct_writes: Optional[int] = Field(None, description="Number of direct writes")
    loads: Optional[int] = Field(None, description="Number of loads")
    invalidations: Optional[int] = Field(None, description="Number of invalidations")
    sharable_mem: Optional[int] = Field(None, description="Sharable memory in bytes")
    persistent_mem: Optional[int] = Field(None, description="Persistent memory in bytes")
    runtime_mem: Optional[int] = Field(None, description="Runtime memory in bytes")
    plan_hash_value: Optional[int] = Field(None, description="Execution plan hash value")
    child_number: Optional[int] = Field(None, description="Child cursor number")
    command_type: Optional[int] = Field(None, description="SQL command type")
    last_load_time: Optional[str] = Field(None, description="Last load time")
    avg_disk_reads: Optional[float] = Field(None, description="Average disk reads per execution")


class QueryFilters(BaseModel):
    """Query filter parameters."""

    min_elapsed_time: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum elapsed time in microseconds"
    )
    min_executions: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum number of executions"
    )
    schema: Optional[str] = Field(
        None,
        max_length=128,
        description="Filter by schema name"
    )
    exclude_system_schemas: bool = Field(
        True,
        description="Exclude system schemas (SYS, SYSTEM, etc.)"
    )
    sql_text_contains: Optional[str] = Field(
        None,
        max_length=500,
        description="Filter by SQL text substring"
    )

    @validator('schema')
    def validate_schema(cls, v):
        """Validate schema name format."""
        if v and not re.match(r'^[A-Z0-9_]+$', v.upper()):
            raise ValueError('Schema name must be alphanumeric and underscores only')
        return v.upper() if v else v


class QuerySort(BaseModel):
    """Query sort parameters."""

    sort_by: str = Field(
        "elapsed_time",
        description="Field to sort by"
    )
    order: str = Field(
        "desc",
        description="Sort order (asc or desc)"
    )

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        valid_fields = [
            "elapsed_time",
            "cpu_time",
            "executions",
            "buffer_gets",
            "disk_reads",
            "rows_processed",
            "avg_elapsed_time",
        ]
        if v not in valid_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(valid_fields)}')
        return v

    @validator('order')
    def validate_order(cls, v):
        """Validate order field."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('order must be "asc" or "desc"')
        return v.lower()


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class PaginationMetadata(BaseModel):
    """Pagination metadata for responses."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class QueryListResponse(BaseModel):
    """Response model for query list endpoint."""

    data: List[Query] = Field(..., description="List of queries")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    filters: Optional[QueryFilters] = Field(None, description="Applied filters")
    sort: Optional[QuerySort] = Field(None, description="Applied sorting")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "sql_id": "abc123xyz4567",
                        "sql_text": "SELECT * FROM users",
                        "parsing_schema_name": "APP_SCHEMA",
                        "elapsed_time": 1234567.89,
                        "cpu_time": 987654.32,
                        "executions": 100,
                        "buffer_gets": 50000,
                        "disk_reads": 1000,
                        "rows_processed": 100,
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 95,
                    "total_pages": 5,
                    "has_next": True,
                    "has_previous": False,
                },
            }
        }


class QueryDetailResponse(BaseModel):
    """Response model for query detail endpoint."""

    data: QueryDetail = Field(..., description="Query details")
    statistics: Optional[dict] = Field(None, description="Additional statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "sql_id": "abc123xyz4567",
                    "sql_text": "SELECT * FROM users WHERE id = :1",
                    "sql_fulltext": "SELECT * FROM users WHERE id = :1",
                    "parsing_schema_name": "APP_SCHEMA",
                    "elapsed_time": 1234567.89,
                    "cpu_time": 987654.32,
                    "executions": 100,
                    "buffer_gets": 50000,
                    "disk_reads": 1000,
                    "rows_processed": 100,
                    "plan_hash_value": 1234567890,
                },
                "statistics": {
                    "child_cursors": 1,
                    "total_executions": 100,
                    "total_elapsed_time": 1234567.89,
                },
            }
        }


class SqlIdRequest(BaseModel):
    """Request model for SQL_ID validation."""

    sql_id: str = Field(..., min_length=13, max_length=13, description="Oracle SQL_ID")

    @validator('sql_id')
    def validate_sql_id(cls, v):
        """Validate SQL_ID format."""
        if not v.isalnum():
            raise ValueError('SQL_ID must be alphanumeric')
        return v.upper()
