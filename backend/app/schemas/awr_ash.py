"""Pydantic schemas for AWR and ASH data."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AWRSnapshot(BaseModel):
    """AWR snapshot information."""

    snap_id: int = Field(..., description="Snapshot ID")
    dbid: int = Field(..., description="Database ID")
    instance_number: int = Field(..., description="Instance number")
    begin_interval_time: str = Field(..., description="Snapshot begin time")
    end_interval_time: str = Field(..., description="Snapshot end time")
    startup_time: Optional[str] = Field(None, description="Instance startup time")
    snap_level: Optional[int] = Field(None, description="Snapshot level")

    class Config:
        from_attributes = True


class SnapshotListResponse(BaseModel):
    """Response for snapshot list."""

    snapshots: List[AWRSnapshot] = Field(..., description="List of snapshots")
    total_count: int = Field(..., description="Total number of snapshots")

    class Config:
        from_attributes = True


class HistoricalSQLStat(BaseModel):
    """Historical SQL statistics from AWR."""

    snap_id: int = Field(..., description="Snapshot ID")
    instance_number: int = Field(..., description="Instance number")
    begin_interval_time: str = Field(..., description="Interval begin time")
    end_interval_time: str = Field(..., description="Interval end time")
    plan_hash_value: int = Field(..., description="Plan hash value")
    executions_delta: Optional[int] = Field(0, description="Executions in interval")
    elapsed_time_sec: Optional[float] = Field(0, description="Elapsed time in seconds")
    cpu_time_sec: Optional[float] = Field(0, description="CPU time in seconds")
    buffer_gets_delta: Optional[int] = Field(0, description="Buffer gets")
    disk_reads_delta: Optional[int] = Field(0, description="Disk reads")
    rows_processed_delta: Optional[int] = Field(0, description="Rows processed")
    parse_calls_delta: Optional[int] = Field(0, description="Parse calls")
    version_count: Optional[int] = Field(0, description="Version count")

    class Config:
        from_attributes = True


class HistoricalSQLResponse(BaseModel):
    """Response for historical SQL statistics."""

    sql_id: str = Field(..., description="SQL_ID")
    statistics: List[HistoricalSQLStat] = Field(..., description="Historical statistics")
    sample_count: int = Field(..., description="Number of samples")
    time_range: Dict[str, Optional[str]] = Field(..., description="Time range of data")

    class Config:
        from_attributes = True


class ASHSample(BaseModel):
    """Active Session History sample."""

    sample_id: Optional[int] = Field(None, description="Sample ID")
    sample_time: str = Field(..., description="Sample time")
    session_id: Optional[int] = Field(None, description="Session ID")
    session_serial: Optional[int] = Field(None, description="Session serial number", alias="session_serial#")
    sql_id: Optional[str] = Field(None, description="SQL_ID")
    sql_plan_hash_value: Optional[int] = Field(None, description="Plan hash value")
    event: Optional[str] = Field(None, description="Wait event")
    wait_class: Optional[str] = Field(None, description="Wait class")
    wait_time: Optional[int] = Field(None, description="Wait time")
    time_waited: Optional[int] = Field(None, description="Time waited")
    session_state: Optional[str] = Field(None, description="Session state")
    session_type: Optional[str] = Field(None, description="Session type")
    blocking_session: Optional[int] = Field(None, description="Blocking session ID")
    current_obj: Optional[int] = Field(None, description="Current object number", alias="current_obj#")
    program: Optional[str] = Field(None, description="Program name")
    module: Optional[str] = Field(None, description="Module name")

    class Config:
        from_attributes = True
        populate_by_name = True


class ASHActivityResponse(BaseModel):
    """Response for ASH activity data."""

    samples: List[ASHSample] = Field(..., description="ASH samples")
    sample_count: int = Field(..., description="Total sample count")
    time_range: Dict[str, Optional[str]] = Field(..., description="Time range")

    class Config:
        from_attributes = True


class TimeSeriesDataPoint(BaseModel):
    """Time-series data point."""

    timestamp: str = Field(..., description="Timestamp")
    value: float = Field(..., description="Metric value")
    label: Optional[str] = Field(None, description="Data point label")

    class Config:
        from_attributes = True


class TimeSeriesMetric(BaseModel):
    """Time-series metric with multiple data points."""

    metric_name: str = Field(..., description="Metric name")
    unit: str = Field(..., description="Unit of measurement")
    data_points: List[TimeSeriesDataPoint] = Field(..., description="Time-series data")

    class Config:
        from_attributes = True


class LoadProfile(BaseModel):
    """AWR load profile statistics."""

    user_commits: Optional[Dict[str, float]] = Field(None, description="User commits")
    user_rollbacks: Optional[Dict[str, float]] = Field(None, description="User rollbacks")
    user_calls: Optional[Dict[str, float]] = Field(None, description="User calls")
    execute_count: Optional[Dict[str, float]] = Field(None, description="Execute count")
    parse_count_total: Optional[Dict[str, float]] = Field(None, description="Total parse count", alias="parse count (total)")
    parse_count_hard: Optional[Dict[str, float]] = Field(None, description="Hard parse count", alias="parse count (hard)")
    physical_reads: Optional[Dict[str, float]] = Field(None, description="Physical reads")
    physical_writes: Optional[Dict[str, float]] = Field(None, description="Physical writes")
    redo_size: Optional[Dict[str, float]] = Field(None, description="Redo size")

    class Config:
        from_attributes = True
        populate_by_name = True


class TopSQL(BaseModel):
    """Top SQL entry from AWR."""

    sql_id: str = Field(..., description="SQL_ID")
    plan_hash_value: int = Field(..., description="Plan hash value")
    executions: int = Field(..., description="Total executions")
    elapsed_time_sec: float = Field(..., description="Elapsed time in seconds")
    cpu_time_sec: float = Field(..., description="CPU time in seconds")
    buffer_gets: int = Field(..., description="Buffer gets")
    disk_reads: int = Field(..., description="Disk reads")
    rows_processed: int = Field(..., description="Rows processed")
    parse_calls: int = Field(..., description="Parse calls")
    avg_elapsed_sec: float = Field(..., description="Average elapsed time per execution")

    class Config:
        from_attributes = True


class WaitEvent(BaseModel):
    """Wait event statistics."""

    event_name: str = Field(..., description="Event name")
    wait_class: str = Field(..., description="Wait class")
    total_waits_delta: int = Field(..., description="Total waits")
    total_timeouts_delta: Optional[int] = Field(0, description="Total timeouts")
    time_waited_sec: float = Field(..., description="Time waited in seconds")
    avg_wait_ms: float = Field(..., description="Average wait time in milliseconds")

    class Config:
        from_attributes = True


class WaitEventSummary(BaseModel):
    """Wait events summary by wait class."""

    by_wait_class: Dict[str, Dict[str, Any]] = Field(..., description="Grouped by wait class")
    total_wait_time_sec: float = Field(..., description="Total wait time in seconds")
    top_wait_class: Optional[str] = Field(None, description="Top wait class")

    class Config:
        from_attributes = True


class InstanceEfficiency(BaseModel):
    """Instance efficiency metrics."""

    buffer_cache_hit_ratio: Optional[float] = Field(None, description="Buffer cache hit ratio %")
    soft_parse_ratio: Optional[float] = Field(None, description="Soft parse ratio %")
    execute_to_parse_ratio: Optional[float] = Field(None, description="Execute to parse ratio")

    class Config:
        from_attributes = True


class ReportInfo(BaseModel):
    """AWR report information."""

    begin_snap_id: int = Field(..., description="Begin snapshot ID")
    end_snap_id: int = Field(..., description="End snapshot ID")
    begin_time: str = Field(..., description="Begin time")
    end_time: str = Field(..., description="End time")
    elapsed_time_minutes: float = Field(..., description="Elapsed time in minutes")
    generated_at: str = Field(..., description="Report generation timestamp")

    class Config:
        from_attributes = True


class AWRReport(BaseModel):
    """Complete AWR report."""

    report_info: ReportInfo = Field(..., description="Report information")
    database_info: Dict[str, Any] = Field(..., description="Database information")
    load_profile: Optional[LoadProfile] = Field(None, description="Load profile statistics")
    top_sql_by_elapsed_time: List[TopSQL] = Field(..., description="Top SQL by elapsed time")
    top_sql_by_cpu: List[TopSQL] = Field(..., description="Top SQL by CPU time")
    top_sql_by_gets: List[TopSQL] = Field(..., description="Top SQL by buffer gets")
    top_sql_by_reads: List[TopSQL] = Field(..., description="Top SQL by disk reads")
    top_sql_by_executions: List[TopSQL] = Field(..., description="Top SQL by executions")
    wait_events: List[WaitEvent] = Field(..., description="Wait events")
    wait_events_summary: WaitEventSummary = Field(..., description="Wait events summary")
    time_model_statistics: Dict[str, Any] = Field(..., description="Time model statistics")
    instance_efficiency: InstanceEfficiency = Field(..., description="Instance efficiency")
    recommendations: List[str] = Field(..., description="Performance recommendations")

    class Config:
        from_attributes = True


class MetricStatistics(BaseModel):
    """Statistical measures for a metric."""

    mean: float = Field(..., description="Mean value")
    median: float = Field(..., description="Median value")
    stdev: float = Field(..., description="Standard deviation")
    p95: float = Field(..., description="95th percentile")

    class Config:
        from_attributes = True


class HistoricalBaseline(BaseModel):
    """Historical baseline statistics."""

    sample_count: int = Field(..., description="Number of samples")
    elapsed_time_sec: MetricStatistics = Field(..., description="Elapsed time statistics")
    cpu_time_sec: MetricStatistics = Field(..., description="CPU time statistics")
    buffer_gets_per_exec: MetricStatistics = Field(..., description="Buffer gets statistics")
    disk_reads_per_exec: MetricStatistics = Field(..., description="Disk reads statistics")

    class Config:
        from_attributes = True


class MetricComparison(BaseModel):
    """Comparison of a metric between current and baseline."""

    current: float = Field(..., description="Current value")
    baseline_mean: float = Field(..., description="Baseline mean")
    baseline_median: float = Field(..., description="Baseline median")
    baseline_p95: float = Field(..., description="Baseline 95th percentile")
    change: float = Field(..., description="Absolute change")
    change_percent: float = Field(..., description="Percentage change")
    regression: bool = Field(..., description="Is this a regression")
    improvement: bool = Field(..., description="Is this an improvement")

    class Config:
        from_attributes = True


class CurrentMetrics(BaseModel):
    """Current query performance metrics."""

    executions: int = Field(..., description="Total executions")
    elapsed_time_sec: float = Field(..., description="Elapsed time per execution")
    cpu_time_sec: float = Field(..., description="CPU time per execution")
    buffer_gets_per_exec: float = Field(..., description="Buffer gets per execution")
    disk_reads_per_exec: float = Field(..., description="Disk reads per execution")
    rows_processed_per_exec: float = Field(..., description="Rows processed per execution")

    class Config:
        from_attributes = True


class HistoricalComparisonResult(BaseModel):
    """Result of current vs historical comparison."""

    sql_id: str = Field(..., description="SQL_ID")
    current: CurrentMetrics = Field(..., description="Current metrics")
    historical: Optional[HistoricalBaseline] = Field(None, description="Historical baseline")
    comparison: Optional[Dict[str, MetricComparison]] = Field(None, description="Metric comparisons")
    trend: str = Field(..., description="Performance trend")
    threshold_percent: float = Field(..., description="Threshold percentage")
    recommendations: List[str] = Field(..., description="Recommendations")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")

    class Config:
        from_attributes = True


class TrendDirection(BaseModel):
    """Trend direction for a metric."""

    direction: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    slope: float = Field(..., description="Trend slope")
    values: List[float] = Field(..., description="Metric values")

    class Config:
        from_attributes = True


class PerformanceAnomaly(BaseModel):
    """Performance anomaly detection."""

    timestamp: str = Field(..., description="Anomaly timestamp")
    snap_id: Optional[int] = Field(None, description="Snapshot ID")
    metric: str = Field(..., description="Metric name")
    value: float = Field(..., description="Anomaly value")
    mean: float = Field(..., description="Expected mean")
    z_score: float = Field(..., description="Z-score")
    severity: str = Field(..., description="Severity (high, medium)")

    class Config:
        from_attributes = True


class PerformanceTrendResult(BaseModel):
    """Performance trend analysis result."""

    sql_id: str = Field(..., description="SQL_ID")
    time_series: List[Dict[str, Any]] = Field(..., description="Time-series data")
    metrics_trends: Dict[str, TrendDirection] = Field(..., description="Trends by metric")
    overall_trend: str = Field(..., description="Overall trend assessment")
    anomalies: List[PerformanceAnomaly] = Field(..., description="Detected anomalies")
    sample_count: int = Field(..., description="Number of samples")
    time_range: Dict[str, Optional[str]] = Field(..., description="Time range")

    class Config:
        from_attributes = True


class RegressionPeriod(BaseModel):
    """Period data for regression detection."""

    days: int = Field(..., description="Number of days in period")
    sample_count: int = Field(..., description="Number of samples")
    metrics: HistoricalBaseline = Field(..., description="Period metrics")

    class Config:
        from_attributes = True


class RegressionDetectionResult(BaseModel):
    """Performance regression detection result."""

    sql_id: str = Field(..., description="SQL_ID")
    regression_detected: bool = Field(..., description="Was regression detected")
    severity: str = Field(..., description="Regression severity")
    baseline_period: RegressionPeriod = Field(..., description="Baseline period data")
    recent_period: RegressionPeriod = Field(..., description="Recent period data")
    comparison: Dict[str, MetricComparison] = Field(..., description="Metric comparisons")
    threshold_percent: float = Field(..., description="Threshold percentage")

    class Config:
        from_attributes = True


class ASHActivityTimeline(BaseModel):
    """ASH activity timeline data point."""

    timestamp: str = Field(..., description="Timestamp")
    sample_count: int = Field(..., description="Sample count")
    cpu_samples: int = Field(..., description="CPU samples")
    wait_samples: int = Field(..., description="Wait samples")
    active_sessions: int = Field(..., description="Active sessions")

    class Config:
        from_attributes = True


class ASHWaitEventAnalysis(BaseModel):
    """ASH wait event analysis."""

    events: List[Dict[str, Any]] = Field(..., description="Wait events")
    unique_event_count: int = Field(..., description="Unique event count")
    total_wait_time: float = Field(..., description="Total wait time")

    class Config:
        from_attributes = True


class ASHSQLAnalysis(BaseModel):
    """ASH analysis for specific SQL_ID."""

    sql_id: str = Field(..., description="SQL_ID")
    time_range: Dict[str, str] = Field(..., description="Time range")
    sample_count: int = Field(..., description="Sample count")
    activity_timeline: List[ASHActivityTimeline] = Field(..., description="Activity timeline")
    wait_event_analysis: ASHWaitEventAnalysis = Field(..., description="Wait event analysis")
    session_analysis: Dict[str, Any] = Field(..., description="Session analysis")
    blocking_analysis: Dict[str, Any] = Field(..., description="Blocking analysis")
    execution_activity: Dict[str, Any] = Field(..., description="Execution activity")

    class Config:
        from_attributes = True


class ASHHeatmapDataPoint(BaseModel):
    """ASH heatmap data point."""

    timestamp: str = Field(..., description="Timestamp")
    wait_class: str = Field(..., description="Wait class")
    activity_count: int = Field(..., description="Activity count")

    class Config:
        from_attributes = True


class ASHTimePeriodAnalysis(BaseModel):
    """ASH time period analysis."""

    time_range: Dict[str, str] = Field(..., description="Time range")
    sample_count: int = Field(..., description="Sample count")
    top_sql: List[Dict[str, Any]] = Field(..., description="Top SQL")
    top_wait_events: List[Dict[str, Any]] = Field(..., description="Top wait events")
    top_sessions: List[Dict[str, Any]] = Field(..., description="Top sessions")
    activity_by_wait_class: Dict[str, int] = Field(..., description="Activity by wait class")
    cpu_vs_wait_breakdown: Dict[str, Any] = Field(..., description="CPU vs wait breakdown")
    activity_heatmap_data: List[ASHHeatmapDataPoint] = Field(..., description="Heatmap data")

    class Config:
        from_attributes = True


class Bottleneck(BaseModel):
    """Performance bottleneck."""

    type: str = Field(..., description="Bottleneck type")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Description")
    recommendation: str = Field(..., description="Recommendation")

    class Config:
        from_attributes = True


class BottleneckAnalysisResult(BaseModel):
    """Bottleneck analysis result."""

    time_range: Dict[str, str] = Field(..., description="Time range")
    bottlenecks: List[Bottleneck] = Field(..., description="Detected bottlenecks")
    top_sql: List[Dict[str, Any]] = Field(..., description="Top SQL")
    top_wait_events: List[Dict[str, Any]] = Field(..., description="Top wait events")
    cpu_vs_wait: Dict[str, Any] = Field(..., description="CPU vs wait breakdown")

    class Config:
        from_attributes = True
