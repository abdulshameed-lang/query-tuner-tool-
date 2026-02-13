"""Pydantic schemas for execution plan comparison."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas.execution_plan import PlanOperation, PlanMetrics


class RegressionFinding(BaseModel):
    """Individual regression finding."""

    type: str = Field(..., description="Regression type")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    current_value: Optional[float] = Field(None, description="Current metric value")
    historical_value: Optional[float] = Field(None, description="Historical metric value")
    ratio: Optional[float] = Field(None, description="Ratio of current to historical")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    message: str = Field(..., description="Human-readable description")

    class Config:
        from_attributes = True


class ImprovementFinding(BaseModel):
    """Individual improvement finding."""

    type: str = Field(..., description="Improvement type")
    current_value: Optional[float] = Field(None, description="Current metric value")
    historical_value: Optional[float] = Field(None, description="Historical metric value")
    ratio: Optional[float] = Field(None, description="Ratio of current to historical")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    message: str = Field(..., description="Human-readable description")

    class Config:
        from_attributes = True


class RegressionAnalysis(BaseModel):
    """Analysis of performance regressions."""

    has_regression: bool = Field(..., description="Whether any regression was detected")
    regression_count: int = Field(..., description="Number of regressions found")
    improvement_count: int = Field(..., description="Number of improvements found")
    severity: str = Field(..., description="Overall severity (none, low, medium, high)")
    regressions: List[RegressionFinding] = Field(
        default_factory=list, description="List of regression findings"
    )
    improvements: List[ImprovementFinding] = Field(
        default_factory=list, description="List of improvements"
    )

    class Config:
        from_attributes = True


class OperationChange(BaseModel):
    """Change in plan operation."""

    signature: Optional[str] = Field(None, description="Operation signature")
    current: Optional[Dict[str, Any]] = Field(None, description="Current operation details")
    historical: Optional[Dict[str, Any]] = Field(
        None, description="Historical operation details"
    )
    changes: Optional[List[str]] = Field(None, description="List of specific changes")

    class Config:
        from_attributes = True


class PlanDiff(BaseModel):
    """Detailed differences between two plans."""

    operations_added: int = Field(..., description="Number of operations added")
    operations_removed: int = Field(..., description="Number of operations removed")
    operations_modified: int = Field(..., description="Number of operations modified")
    total_changes: int = Field(..., description="Total number of changes")
    added_details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Details of added operations"
    )
    removed_details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Details of removed operations"
    )
    modified_details: List[OperationChange] = Field(
        default_factory=list, description="Details of modified operations"
    )

    class Config:
        from_attributes = True


class SignificantChange(BaseModel):
    """Significant operation change between plans."""

    type: str = Field(..., description="Change type")
    object_name: Optional[str] = Field(None, description="Affected object name")
    historical_method: Optional[str] = Field(None, description="Historical access method")
    current_method: Optional[str] = Field(None, description="Current access method")
    historical_sequence: Optional[List[str]] = Field(
        None, description="Historical join sequence"
    )
    current_sequence: Optional[List[str]] = Field(None, description="Current join sequence")
    access_method: Optional[str] = Field(None, description="Access method for new objects")
    severity: str = Field(..., description="Change severity (low, medium, high)")
    message: str = Field(..., description="Human-readable description")

    class Config:
        from_attributes = True


class PlanComparisonMetrics(BaseModel):
    """Metrics for plan comparison."""

    current_metrics: PlanMetrics = Field(..., description="Current plan metrics")
    historical_metrics: PlanMetrics = Field(..., description="Historical plan metrics")

    class Config:
        from_attributes = True


class ComparisonRecommendation(BaseModel):
    """Recommendation from plan comparison."""

    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority (low, medium, high)")
    message: str = Field(..., description="Recommendation message")
    actions: Optional[List[str]] = Field(None, description="Suggested actions")
    details: Optional[List[str]] = Field(None, description="Additional details")

    class Config:
        from_attributes = True


class BaselineRecommendation(BaseModel):
    """SQL Plan Baseline recommendation."""

    recommend_baseline: bool = Field(
        ..., description="Whether to recommend creating a baseline"
    )
    priority: str = Field(..., description="Priority (none, low, medium, high)")
    reasons: List[str] = Field(..., description="Reasons for recommendation")
    sql_id: Optional[str] = Field(None, description="SQL ID")
    preferred_plan_hash: Optional[int] = Field(
        None, description="Preferred plan hash value"
    )
    baseline_creation_sql: Optional[str] = Field(
        None, description="SQL to create baseline"
    )
    instructions: Optional[List[str]] = Field(
        None, description="Implementation instructions"
    )

    class Config:
        from_attributes = True


class PlanComparisonMetadata(BaseModel):
    """Metadata about plans being compared."""

    sql_id: Optional[str] = Field(None, description="SQL ID")
    plan_hash_value: Optional[int] = Field(None, description="Plan hash value")
    first_snap_id: Optional[int] = Field(None, description="First AWR snapshot ID")
    last_snap_id: Optional[int] = Field(None, description="Last AWR snapshot ID")
    first_seen: Optional[str] = Field(None, description="First seen timestamp")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")
    snap_count: Optional[int] = Field(None, description="Number of snapshots")
    timestamp: Optional[str] = Field(None, description="Plan timestamp")
    child_number: Optional[int] = Field(None, description="Child cursor number")

    class Config:
        from_attributes = True


class PlanComparison(BaseModel):
    """Complete plan comparison result."""

    comparison_possible: bool = Field(
        ..., description="Whether comparison could be performed"
    )
    reason: Optional[str] = Field(None, description="Reason if comparison not possible")
    plans_identical: Optional[bool] = Field(None, description="Whether plans are identical")
    current_plan_hash: Optional[int] = Field(None, description="Current plan hash value")
    historical_plan_hash: Optional[int] = Field(
        None, description="Historical plan hash value"
    )
    current_metadata: Optional[PlanComparisonMetadata] = Field(
        None, description="Current plan metadata"
    )
    historical_metadata: Optional[PlanComparisonMetadata] = Field(
        None, description="Historical plan metadata"
    )
    current_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Current plan metrics"
    )
    historical_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Historical plan metrics"
    )
    regression_detected: Optional[bool] = Field(
        None, description="Whether regression was detected"
    )
    regression_analysis: Optional[RegressionAnalysis] = Field(
        None, description="Regression analysis results"
    )
    plan_diff: Optional[PlanDiff] = Field(None, description="Detailed plan differences")
    operation_changes: Optional[List[SignificantChange]] = Field(
        None, description="Significant operation changes"
    )
    recommendations: Optional[List[ComparisonRecommendation]] = Field(
        None, description="Comparison recommendations"
    )
    comparison_timestamp: Optional[str] = Field(
        None, description="When comparison was performed"
    )

    class Config:
        from_attributes = True


class PlanComparisonResponse(BaseModel):
    """API response for plan comparison."""

    data: PlanComparison = Field(..., description="Plan comparison data")


class PlanVersionInfo(BaseModel):
    """Information about a plan version."""

    sql_id: str = Field(..., description="SQL ID")
    plan_hash_value: int = Field(..., description="Plan hash value")
    first_snap_id: Optional[int] = Field(None, description="First AWR snapshot ID")
    last_snap_id: Optional[int] = Field(None, description="Last AWR snapshot ID")
    first_seen: Optional[str] = Field(None, description="First seen timestamp")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")
    snap_count: Optional[int] = Field(None, description="Number of snapshots")
    timestamp: Optional[str] = Field(None, description="Plan timestamp")
    child_number: Optional[int] = Field(None, description="Child cursor number")

    class Config:
        from_attributes = True


class PlanVersionsResponse(BaseModel):
    """API response for plan versions."""

    data: List[PlanVersionInfo] = Field(..., description="List of plan versions")
    total_count: int = Field(..., description="Total number of versions")


class CompareRequest(BaseModel):
    """Request to compare plans."""

    sql_id: str = Field(..., description="SQL ID to compare")
    current_plan_hash: Optional[int] = Field(None, description="Current plan hash value")
    historical_plan_hash: Optional[int] = Field(
        None, description="Historical plan hash value to compare against"
    )
    include_recommendations: bool = Field(
        True, description="Whether to include recommendations"
    )


class BaselineRequest(BaseModel):
    """Request to get baseline recommendation."""

    sql_id: str = Field(..., description="SQL ID")
    current_plan_hash: int = Field(..., description="Current plan hash value")
    preferred_plan_hash: int = Field(..., description="Preferred plan hash value")
