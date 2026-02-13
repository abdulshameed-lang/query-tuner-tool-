"""Pydantic schemas for execution plans."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlanOperation(BaseModel):
    """Single operation in an execution plan."""

    id: int = Field(..., description="Operation ID")
    parent_id: Optional[int] = Field(None, description="Parent operation ID")
    operation: str = Field(..., description="Operation type")
    options: Optional[str] = Field(None, description="Operation options")
    object_owner: Optional[str] = Field(None, description="Object owner")
    object_name: Optional[str] = Field(None, description="Object name")
    object_alias: Optional[str] = Field(None, description="Object alias")
    object_type: Optional[str] = Field(None, description="Object type")
    optimizer: Optional[str] = Field(None, description="Optimizer mode")
    cost: Optional[int] = Field(None, description="Operation cost")
    cardinality: Optional[int] = Field(None, description="Estimated rows")
    bytes: Optional[int] = Field(None, description="Estimated bytes")
    cpu_cost: Optional[int] = Field(None, description="CPU cost")
    io_cost: Optional[int] = Field(None, description="I/O cost")
    temp_space: Optional[int] = Field(None, description="Temp space usage")
    access_predicates: Optional[str] = Field(None, description="Access predicates")
    filter_predicates: Optional[str] = Field(None, description="Filter predicates")
    projection: Optional[str] = Field(None, description="Projection")
    time: Optional[int] = Field(None, description="Elapsed time")
    qblock_name: Optional[str] = Field(None, description="Query block name")
    remarks: Optional[str] = Field(None, description="Remarks")
    depth: Optional[int] = Field(None, description="Depth in tree")
    position: Optional[int] = Field(None, description="Position")
    search_columns: Optional[int] = Field(None, description="Search columns")
    partition_start: Optional[str] = Field(None, description="Partition start")
    partition_stop: Optional[str] = Field(None, description="Partition stop")
    partition_id: Optional[int] = Field(None, description="Partition ID")
    distribution: Optional[str] = Field(None, description="Distribution method")
    cumulative_cost: Optional[int] = Field(None, description="Cumulative cost")
    cumulative_cardinality: Optional[int] = Field(
        None, description="Cumulative cardinality"
    )

    class Config:
        from_attributes = True


class PlanNode(PlanOperation):
    """Plan operation with children (tree structure)."""

    children: List["PlanNode"] = Field(
        default_factory=list, description="Child operations"
    )


# Enable forward references for recursive model
PlanNode.model_rebuild()


class PlanIssue(BaseModel):
    """Issue detected in execution plan."""

    type: str = Field(..., description="Issue type")
    severity: str = Field(..., description="Severity (low, medium, high)")
    message: str = Field(..., description="Issue description")
    operations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Affected operations"
    )


class PlanRecommendation(BaseModel):
    """Recommendation for plan optimization."""

    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority (low, medium, high)")
    message: str = Field(..., description="Recommendation description")
    table: Optional[str] = Field(None, description="Affected table")
    predicates: Optional[str] = Field(None, description="Related predicates")
    operation_id: Optional[int] = Field(None, description="Related operation ID")
    affected_tables: Optional[List[str]] = Field(
        None, description="List of affected tables"
    )


class PlanMetrics(BaseModel):
    """Execution plan metrics."""

    total_cost: int = Field(..., description="Total plan cost")
    total_cardinality: int = Field(..., description="Total estimated rows")
    total_bytes: int = Field(..., description="Total estimated bytes")
    operation_count: int = Field(..., description="Number of operations")
    operation_types: Dict[str, int] = Field(
        ..., description="Count of each operation type"
    )
    complexity: int = Field(..., description="Plan complexity score")
    max_depth: int = Field(..., description="Maximum depth of plan tree")
    parallel_operations: int = Field(..., description="Number of parallel operations")


class PlanAnalysis(BaseModel):
    """Execution plan analysis results."""

    issues: List[PlanIssue] = Field(..., description="Detected issues")
    recommendations: List[PlanRecommendation] = Field(
        ..., description="Optimization recommendations"
    )
    costly_operations: List[PlanOperation] = Field(
        ..., description="Most costly operations"
    )
    metrics: PlanMetrics = Field(..., description="Plan metrics")


class PlanStatistics(BaseModel):
    """Statistics for an execution plan."""

    execution_count: Optional[int] = Field(None, description="Number of executions")
    first_seen: Optional[str] = Field(None, description="First seen timestamp")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")


class ExecutionPlan(BaseModel):
    """Complete execution plan with analysis."""

    sql_id: str = Field(..., description="SQL ID")
    plan_hash_value: Optional[int] = Field(None, description="Plan hash value")
    plan_tree: PlanNode = Field(..., description="Hierarchical plan tree")
    plan_operations: List[PlanOperation] = Field(
        ..., description="Flat list of operations"
    )
    analysis: PlanAnalysis = Field(..., description="Plan analysis")
    statistics: Optional[PlanStatistics] = Field(None, description="Plan statistics")


class ExecutionPlanResponse(BaseModel):
    """API response for execution plan."""

    data: ExecutionPlan = Field(..., description="Execution plan data")


class PlanHistoryItem(BaseModel):
    """Execution plan history item."""

    sql_id: str = Field(..., description="SQL ID")
    plan_hash_value: int = Field(..., description="Plan hash value")
    timestamp: Optional[str] = Field(None, description="Plan timestamp")
    child_number: Optional[int] = Field(None, description="Child cursor number")


class PlanHistoryResponse(BaseModel):
    """API response for plan history."""

    data: List[PlanHistoryItem] = Field(..., description="List of plan versions")
    total_count: int = Field(..., description="Total number of plan versions")


class PlanExportFormat(BaseModel):
    """Export format options."""

    format: str = Field(
        "text", description="Export format (text, json, xml)", pattern="^(text|json|xml)$"
    )


class PlanExportResponse(BaseModel):
    """API response for plan export."""

    sql_id: str = Field(..., description="SQL ID")
    plan_hash_value: Optional[int] = Field(None, description="Plan hash value")
    format: str = Field(..., description="Export format")
    content: str = Field(..., description="Exported plan content")
