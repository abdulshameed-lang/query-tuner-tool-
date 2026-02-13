/**
 * AWR and ASH types matching backend Pydantic schemas
 */

/**
 * AWR Snapshot
 */
export interface AWRSnapshot {
  snap_id: number;
  dbid: number;
  instance_number: number;
  begin_interval_time: string;
  end_interval_time: string;
  startup_time?: string;
  snap_level?: number;
}

export interface SnapshotListResponse {
  snapshots: AWRSnapshot[];
  total_count: number;
}

/**
 * Historical SQL Statistics
 */
export interface HistoricalSQLStat {
  snap_id: number;
  instance_number: number;
  begin_interval_time: string;
  end_interval_time: string;
  plan_hash_value: number;
  executions_delta?: number;
  elapsed_time_sec?: number;
  cpu_time_sec?: number;
  buffer_gets_delta?: number;
  disk_reads_delta?: number;
  rows_processed_delta?: number;
  parse_calls_delta?: number;
  version_count?: number;
}

export interface HistoricalSQLResponse {
  sql_id: string;
  statistics: HistoricalSQLStat[];
  sample_count: number;
  time_range: {
    begin?: string;
    end?: string;
  };
}

/**
 * ASH Sample
 */
export interface ASHSample {
  sample_id?: number;
  sample_time: string;
  session_id?: number;
  session_serial?: number;
  sql_id?: string;
  sql_plan_hash_value?: number;
  event?: string;
  wait_class?: string;
  wait_time?: number;
  time_waited?: number;
  session_state?: string;
  session_type?: string;
  blocking_session?: number;
  current_obj?: number;
  program?: string;
  module?: string;
}

export interface ASHActivityResponse {
  samples: ASHSample[];
  sample_count: number;
  time_range: {
    begin?: string;
    end?: string;
  };
}

/**
 * Time Series
 */
export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface TimeSeriesMetric {
  metric_name: string;
  unit: string;
  data_points: TimeSeriesDataPoint[];
}

/**
 * AWR Report Components
 */
export interface LoadProfile {
  user_commits?: Record<string, number>;
  user_rollbacks?: Record<string, number>;
  user_calls?: Record<string, number>;
  execute_count?: Record<string, number>;
  parse_count_total?: Record<string, number>;
  parse_count_hard?: Record<string, number>;
  physical_reads?: Record<string, number>;
  physical_writes?: Record<string, number>;
  redo_size?: Record<string, number>;
}

export interface TopSQL {
  sql_id: string;
  plan_hash_value: number;
  executions: number;
  elapsed_time_sec: number;
  cpu_time_sec: number;
  buffer_gets: number;
  disk_reads: number;
  rows_processed: number;
  parse_calls: number;
  avg_elapsed_sec: number;
}

export interface WaitEvent {
  event_name: string;
  wait_class: string;
  total_waits_delta: number;
  total_timeouts_delta?: number;
  time_waited_sec: number;
  avg_wait_ms: number;
}

export interface WaitEventSummary {
  by_wait_class: Record<string, any>;
  total_wait_time_sec: number;
  top_wait_class?: string;
}

export interface InstanceEfficiency {
  buffer_cache_hit_ratio?: number;
  soft_parse_ratio?: number;
  execute_to_parse_ratio?: number;
}

export interface ReportInfo {
  begin_snap_id: number;
  end_snap_id: number;
  begin_time: string;
  end_time: string;
  elapsed_time_minutes: number;
  generated_at: string;
}

export interface AWRReport {
  report_info: ReportInfo;
  database_info: Record<string, any>;
  load_profile?: LoadProfile;
  top_sql_by_elapsed_time: TopSQL[];
  top_sql_by_cpu: TopSQL[];
  top_sql_by_gets: TopSQL[];
  top_sql_by_reads: TopSQL[];
  top_sql_by_executions: TopSQL[];
  wait_events: WaitEvent[];
  wait_events_summary: WaitEventSummary;
  time_model_statistics: Record<string, any>;
  instance_efficiency: InstanceEfficiency;
  recommendations: string[];
}

/**
 * Historical Comparison
 */
export interface MetricStatistics {
  mean: number;
  median: number;
  stdev: number;
  p95: number;
}

export interface HistoricalBaseline {
  sample_count: number;
  elapsed_time_sec: MetricStatistics;
  cpu_time_sec: MetricStatistics;
  buffer_gets_per_exec: MetricStatistics;
  disk_reads_per_exec: MetricStatistics;
}

export interface MetricComparison {
  current: number;
  baseline_mean: number;
  baseline_median: number;
  baseline_p95: number;
  change: number;
  change_percent: number;
  regression: boolean;
  improvement: boolean;
}

export interface CurrentMetrics {
  executions: number;
  elapsed_time_sec: number;
  cpu_time_sec: number;
  buffer_gets_per_exec: number;
  disk_reads_per_exec: number;
  rows_processed_per_exec: number;
}

export interface HistoricalComparisonResult {
  sql_id: string;
  current: CurrentMetrics;
  historical?: HistoricalBaseline;
  comparison?: Record<string, MetricComparison>;
  trend: string;
  threshold_percent: number;
  recommendations: string[];
  analysis_timestamp: string;
}

/**
 * Performance Trends
 */
export interface TrendDirection {
  direction: string;
  slope: number;
  values: number[];
}

export interface PerformanceAnomaly {
  timestamp: string;
  snap_id?: number;
  metric: string;
  value: number;
  mean: number;
  z_score: number;
  severity: string;
}

export interface PerformanceTrendResult {
  sql_id: string;
  time_series: Record<string, any>[];
  metrics_trends: Record<string, TrendDirection>;
  overall_trend: string;
  anomalies: PerformanceAnomaly[];
  sample_count: number;
  time_range: {
    begin?: string;
    end?: string;
  };
}

/**
 * Regression Detection
 */
export interface RegressionPeriod {
  days: number;
  sample_count: number;
  metrics: HistoricalBaseline;
}

export interface RegressionDetectionResult {
  sql_id: string;
  regression_detected: boolean;
  severity: string;
  baseline_period: RegressionPeriod;
  recent_period: RegressionPeriod;
  comparison: Record<string, MetricComparison>;
  threshold_percent: number;
}

/**
 * ASH Analysis
 */
export interface ASHActivityTimeline {
  timestamp: string;
  sample_count: number;
  cpu_samples: number;
  wait_samples: number;
  active_sessions: number;
}

export interface ASHWaitEventAnalysis {
  events: Record<string, any>[];
  unique_event_count: number;
  total_wait_time: number;
}

export interface ASHSQLAnalysis {
  sql_id: string;
  time_range: {
    begin: string;
    end: string;
  };
  sample_count: number;
  activity_timeline: ASHActivityTimeline[];
  wait_event_analysis: ASHWaitEventAnalysis;
  session_analysis: Record<string, any>;
  blocking_analysis: Record<string, any>;
  execution_activity: Record<string, any>;
}

export interface ASHHeatmapDataPoint {
  timestamp: string;
  wait_class: string;
  activity_count: number;
}

export interface ASHTimePeriodAnalysis {
  time_range: {
    begin: string;
    end: string;
  };
  sample_count: number;
  top_sql: Record<string, any>[];
  top_wait_events: Record<string, any>[];
  top_sessions: Record<string, any>[];
  activity_by_wait_class: Record<string, number>;
  cpu_vs_wait_breakdown: Record<string, any>;
  activity_heatmap_data: ASHHeatmapDataPoint[];
}

export interface Bottleneck {
  type: string;
  severity: string;
  description: string;
  recommendation: string;
}

export interface BottleneckAnalysisResult {
  time_range: {
    begin: string;
    end: string;
  };
  bottlenecks: Bottleneck[];
  top_sql: Record<string, any>[];
  top_wait_events: Record<string, any>[];
  cpu_vs_wait: Record<string, any>;
}

/**
 * Request Parameters
 */
export interface AWRReportParams {
  begin_snap_id: number;
  end_snap_id: number;
  top_n?: number;
  format?: string;
}

export interface ASHActivityParams {
  sql_id?: string;
  begin_time?: string;
  end_time?: string;
  minutes_back?: number;
  limit?: number;
}

export interface HistoricalComparisonParams {
  sql_id: string;
  days_back?: number;
  threshold_percent?: number;
}

export interface PerformanceTrendParams {
  sql_id: string;
  days_back?: number;
}

export interface RegressionDetectionParams {
  sql_id: string;
  baseline_days?: number;
  recent_days?: number;
  threshold_percent?: number;
}

/**
 * Enums
 */
export enum PerformanceTrend {
  IMPROVING = "improving",
  DEGRADING = "degrading",
  STABLE = "stable",
  ANOMALY = "anomaly",
  INSUFFICIENT_DATA = "insufficient_data",
}

export enum RegressionSeverity {
  NONE = "none",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum BottleneckType {
  CPU = "CPU",
  IO = "I/O",
  CONCURRENCY = "Concurrency",
  MEMORY = "Memory",
  NETWORK = "Network",
}

/**
 * Chart Data Types
 */
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
}

export interface LineChartData {
  name: string;
  data: ChartDataPoint[];
  color?: string;
}

export interface HeatmapData {
  x: string;
  y: string;
  value: number;
}
