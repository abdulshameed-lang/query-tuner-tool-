/**
 * TypeScript type definitions for plan comparison.
 * These types mirror the backend Pydantic schemas.
 */

import { PlanMetrics } from './executionPlan';

/**
 * Severity levels for findings and changes.
 */
export type Severity = 'none' | 'low' | 'medium' | 'high' | 'critical';

/**
 * Priority levels for recommendations.
 */
export type Priority = 'none' | 'low' | 'medium' | 'high';

/**
 * Individual regression finding.
 */
export interface RegressionFinding {
  type: string;
  severity: Severity;
  current_value?: number;
  historical_value?: number;
  ratio?: number;
  change_percent?: number;
  message: string;
}

/**
 * Individual improvement finding.
 */
export interface ImprovementFinding {
  type: string;
  current_value?: number;
  historical_value?: number;
  ratio?: number;
  change_percent?: number;
  message: string;
}

/**
 * Analysis of performance regressions.
 */
export interface RegressionAnalysis {
  has_regression: boolean;
  regression_count: number;
  improvement_count: number;
  severity: Severity;
  regressions: RegressionFinding[];
  improvements: ImprovementFinding[];
}

/**
 * Change in plan operation.
 */
export interface OperationChange {
  signature?: string;
  current?: Record<string, any>;
  historical?: Record<string, any>;
  changes?: string[];
}

/**
 * Detailed differences between two plans.
 */
export interface PlanDiff {
  operations_added: number;
  operations_removed: number;
  operations_modified: number;
  total_changes: number;
  added_details: Record<string, any>[];
  removed_details: Record<string, any>[];
  modified_details: OperationChange[];
}

/**
 * Significant operation change between plans.
 */
export interface SignificantChange {
  type: string;
  object_name?: string;
  historical_method?: string;
  current_method?: string;
  historical_sequence?: string[];
  current_sequence?: string[];
  access_method?: string;
  severity: Severity;
  message: string;
}

/**
 * Metrics for plan comparison.
 */
export interface PlanComparisonMetrics {
  current_metrics: PlanMetrics;
  historical_metrics: PlanMetrics;
}

/**
 * Recommendation from plan comparison.
 */
export interface ComparisonRecommendation {
  type: string;
  priority: Priority;
  message: string;
  actions?: string[];
  details?: string[];
}

/**
 * SQL Plan Baseline recommendation.
 */
export interface BaselineRecommendation {
  recommend_baseline: boolean;
  priority: Priority;
  reasons: string[];
  sql_id?: string;
  preferred_plan_hash?: number;
  baseline_creation_sql?: string;
  instructions?: string[];
}

/**
 * Metadata about plans being compared.
 */
export interface PlanComparisonMetadata {
  sql_id?: string;
  plan_hash_value?: number;
  first_snap_id?: number;
  last_snap_id?: number;
  first_seen?: string;
  last_seen?: string;
  snap_count?: number;
  timestamp?: string;
  child_number?: number;
}

/**
 * Complete plan comparison result.
 */
export interface PlanComparison {
  comparison_possible: boolean;
  reason?: string;
  plans_identical?: boolean;
  current_plan_hash?: number;
  historical_plan_hash?: number;
  current_metadata?: PlanComparisonMetadata;
  historical_metadata?: PlanComparisonMetadata;
  current_metrics?: Record<string, any>;
  historical_metrics?: Record<string, any>;
  regression_detected?: boolean;
  regression_analysis?: RegressionAnalysis;
  plan_diff?: PlanDiff;
  operation_changes?: SignificantChange[];
  recommendations?: ComparisonRecommendation[];
  comparison_timestamp?: string;
}

/**
 * API response for plan comparison.
 */
export interface PlanComparisonResponse {
  data: PlanComparison;
}

/**
 * Information about a plan version.
 */
export interface PlanVersionInfo {
  sql_id: string;
  plan_hash_value: number;
  first_snap_id?: number;
  last_snap_id?: number;
  first_seen?: string;
  last_seen?: string;
  snap_count?: number;
  timestamp?: string;
  child_number?: number;
  source?: 'current' | 'historical';
}

/**
 * API response for plan versions.
 */
export interface PlanVersionsResponse {
  data: PlanVersionInfo[];
  total_count: number;
}

/**
 * Request to compare plans.
 */
export interface CompareRequest {
  sql_id: string;
  current_plan_hash?: number;
  historical_plan_hash?: number;
  include_recommendations?: boolean;
}

/**
 * Request to get baseline recommendation.
 */
export interface BaselineRequest {
  sql_id: string;
  current_plan_hash: number;
  preferred_plan_hash: number;
}

/**
 * Data source for plan versions.
 */
export type PlanVersionSource = 'current' | 'historical' | 'both';

/**
 * Comparison status for UI display.
 */
export interface ComparisonStatus {
  loading: boolean;
  error?: string;
  comparison?: PlanComparison;
  versions?: PlanVersionInfo[];
}

/**
 * Chart data for regression visualization.
 */
export interface RegressionChartData {
  metric: string;
  current: number;
  historical: number;
  change_percent: number;
  is_regression: boolean;
}

/**
 * Comparison summary for dashboard.
 */
export interface ComparisonSummary {
  sql_id: string;
  has_regression: boolean;
  severity: Severity;
  regression_count: number;
  improvement_count: number;
  total_changes: number;
  recommend_baseline: boolean;
  comparison_timestamp: string;
}

/**
 * Filter options for plan versions list.
 */
export interface PlanVersionFilter {
  source?: PlanVersionSource;
  date_from?: string;
  date_to?: string;
  min_snap_count?: number;
}

/**
 * Sort options for plan versions list.
 */
export type PlanVersionSortField = 'plan_hash_value' | 'first_seen' | 'last_seen' | 'snap_count';

export interface PlanVersionSort {
  field: PlanVersionSortField;
  order: 'asc' | 'desc';
}
