/**
 * TypeScript type definitions for execution plans.
 * These types mirror the backend Pydantic schemas.
 */

/**
 * Single operation in an execution plan.
 */
export interface PlanOperation {
  id: number;
  parent_id?: number;
  operation: string;
  options?: string;
  object_owner?: string;
  object_name?: string;
  object_alias?: string;
  object_type?: string;
  optimizer?: string;
  cost?: number;
  cardinality?: number;
  bytes?: number;
  cpu_cost?: number;
  io_cost?: number;
  temp_space?: number;
  access_predicates?: string;
  filter_predicates?: string;
  projection?: string;
  time?: number;
  qblock_name?: string;
  remarks?: string;
  depth?: number;
  position?: number;
  search_columns?: number;
  partition_start?: string;
  partition_stop?: string;
  partition_id?: number;
  distribution?: string;
  cumulative_cost?: number;
  cumulative_cardinality?: number;
}

/**
 * Plan operation with children (tree structure).
 */
export interface PlanNode extends PlanOperation {
  children: PlanNode[];
}

/**
 * Issue detected in execution plan.
 */
export interface PlanIssue {
  type: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  operations?: Record<string, any>[];
}

/**
 * Recommendation for plan optimization.
 */
export interface PlanRecommendation {
  type: string;
  priority: 'low' | 'medium' | 'high';
  message: string;
  table?: string;
  predicates?: string;
  operation_id?: number;
  affected_tables?: string[];
}

/**
 * Execution plan metrics.
 */
export interface PlanMetrics {
  total_cost: number;
  total_cardinality: number;
  total_bytes: number;
  operation_count: number;
  operation_types: Record<string, number>;
  complexity: number;
  max_depth: number;
  parallel_operations: number;
}

/**
 * Execution plan analysis results.
 */
export interface PlanAnalysis {
  issues: PlanIssue[];
  recommendations: PlanRecommendation[];
  costly_operations: PlanOperation[];
  metrics: PlanMetrics;
}

/**
 * Statistics for an execution plan.
 */
export interface PlanStatistics {
  execution_count?: number;
  first_seen?: string;
  last_seen?: string;
}

/**
 * Complete execution plan with analysis.
 */
export interface ExecutionPlan {
  sql_id: string;
  plan_hash_value?: number;
  plan_tree: PlanNode;
  plan_operations: PlanOperation[];
  analysis: PlanAnalysis;
  statistics?: PlanStatistics;
}

/**
 * API response for execution plan.
 */
export interface ExecutionPlanResponse {
  data: ExecutionPlan;
}

/**
 * Execution plan history item.
 */
export interface PlanHistoryItem {
  sql_id: string;
  plan_hash_value: number;
  timestamp?: string;
  child_number?: number;
}

/**
 * API response for plan history.
 */
export interface PlanHistoryResponse {
  data: PlanHistoryItem[];
  total_count: number;
}

/**
 * Plan export format options.
 */
export type PlanExportFormat = 'text' | 'json' | 'xml';

/**
 * API response for plan export.
 */
export interface PlanExportResponse {
  sql_id: string;
  plan_hash_value?: number;
  format: PlanExportFormat;
  content: string;
}

/**
 * Tree data structure for Ant Design Tree component.
 */
export interface PlanTreeNode {
  key: string;
  title: React.ReactNode;
  children?: PlanTreeNode[];
  operation: PlanOperation;
  isLeaf?: boolean;
}
