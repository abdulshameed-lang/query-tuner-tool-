"""Pydantic schemas for query tuning recommendations."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """Base recommendation model."""

    type: str = Field(..., description="Recommendation type")
    subtype: str = Field(..., description="Recommendation subtype")
    priority: str = Field(
        ..., description="Priority level (critical, high, medium, low)"
    )
    estimated_impact: str = Field(
        ..., description="Estimated impact (high, medium, low, minimal)"
    )
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    rationale: Optional[List[str]] = Field(
        None, description="List of reasons for this recommendation"
    )
    implementation_notes: Optional[List[str]] = Field(
        None, description="Implementation guidance"
    )

    class Config:
        from_attributes = True


class IndexRecommendation(Recommendation):
    """Index-related recommendation."""

    table: Optional[str] = Field(None, description="Table name")
    columns: Optional[List[str]] = Field(None, description="Columns for index")
    index_name: Optional[str] = Field(None, description="Index name")
    current_operation: Optional[str] = Field(None, description="Current plan operation")
    cost: Optional[int] = Field(None, description="Current operation cost")
    cardinality: Optional[int] = Field(None, description="Estimated rows")
    sql: Optional[str] = Field(None, description="CREATE INDEX SQL statement")


class SQLRewriteRecommendation(Recommendation):
    """SQL rewrite recommendation."""

    original_pattern: Optional[str] = Field(None, description="Current SQL pattern")
    suggested_pattern: Optional[str] = Field(None, description="Suggested SQL pattern")
    example_before: Optional[str] = Field(None, description="Example before rewrite")
    example_after: Optional[str] = Field(None, description="Example after rewrite")


class OptimizerHintRecommendation(Recommendation):
    """Optimizer hint recommendation."""

    hint: str = Field(..., description="Suggested optimizer hint")
    affected_operation: Optional[str] = Field(
        None, description="Affected plan operation"
    )
    table: Optional[str] = Field(None, description="Table name")
    cardinality: Optional[int] = Field(None, description="Operation cardinality")
    cost: Optional[int] = Field(None, description="Operation cost")
    total_cost: Optional[int] = Field(None, description="Total query cost")


class StatisticsRecommendation(Recommendation):
    """Statistics gathering recommendation."""

    table: str = Field(..., description="Table name")
    sql: str = Field(..., description="DBMS_STATS SQL statement")
    statistics_age_days: Optional[int] = Field(None, description="Age of statistics")
    last_analyzed: Optional[str] = Field(None, description="Last analysis timestamp")


class ParallelismRecommendation(Recommendation):
    """Parallelism recommendation."""

    table: Optional[str] = Field(None, description="Table name")
    cardinality: Optional[int] = Field(None, description="Operation cardinality")
    cost: Optional[int] = Field(None, description="Operation cost")
    hint: Optional[str] = Field(None, description="PARALLEL hint")
    sql: Optional[str] = Field(None, description="ALTER TABLE SQL for parallel")


class RecommendationSummary(BaseModel):
    """Summary of recommendations."""

    total_count: int = Field(..., description="Total number of recommendations")
    by_type: Dict[str, int] = Field(
        ..., description="Count of recommendations by type"
    )
    by_priority: Dict[str, int] = Field(
        ..., description="Count of recommendations by priority"
    )
    by_impact: Dict[str, int] = Field(
        ..., description="Count of recommendations by estimated impact"
    )
    critical_count: int = Field(..., description="Number of critical recommendations")
    high_impact_count: int = Field(
        ..., description="Number of high-impact recommendations"
    )


class RecommendationsResponse(BaseModel):
    """API response for recommendations."""

    sql_id: str = Field(..., description="SQL ID")
    recommendations: List[Recommendation] = Field(
        ..., description="List of recommendations"
    )
    summary: RecommendationSummary = Field(..., description="Recommendations summary")
    generated_at: str = Field(..., description="Timestamp when recommendations generated")


class IndexRecommendationsResponse(BaseModel):
    """API response for index recommendations only."""

    sql_id: str = Field(..., description="SQL ID")
    recommendations: List[IndexRecommendation] = Field(
        ..., description="Index recommendations"
    )
    total_count: int = Field(..., description="Total number of recommendations")


class SQLRewriteRecommendationsResponse(BaseModel):
    """API response for SQL rewrite recommendations only."""

    sql_id: str = Field(..., description="SQL ID")
    recommendations: List[SQLRewriteRecommendation] = Field(
        ..., description="SQL rewrite recommendations"
    )
    total_count: int = Field(..., description="Total number of recommendations")


class HintRecommendationsResponse(BaseModel):
    """API response for optimizer hint recommendations only."""

    sql_id: str = Field(..., description="SQL ID")
    recommendations: List[OptimizerHintRecommendation] = Field(
        ..., description="Optimizer hint recommendations"
    )
    total_count: int = Field(..., description="Total number of recommendations")


class RecommendationFilters(BaseModel):
    """Filters for recommendation queries."""

    types: Optional[List[str]] = Field(
        None, description="Filter by recommendation types"
    )
    priorities: Optional[List[str]] = Field(None, description="Filter by priorities")
    min_impact: Optional[str] = Field(
        None, description="Minimum impact level (high, medium, low)"
    )


class RecommendationRequest(BaseModel):
    """Request for generating recommendations."""

    sql_id: str = Field(..., description="SQL ID to analyze")
    include_index: bool = Field(True, description="Include index recommendations")
    include_rewrite: bool = Field(True, description="Include SQL rewrite recommendations")
    include_hints: bool = Field(True, description="Include optimizer hint recommendations")
    include_statistics: bool = Field(
        True, description="Include statistics recommendations"
    )
    include_parallelism: bool = Field(
        True, description="Include parallelism recommendations"
    )
