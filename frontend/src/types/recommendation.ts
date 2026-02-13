/**
 * TypeScript type definitions for query tuning recommendations.
 * These types mirror the backend Pydantic schemas.
 */

/**
 * Recommendation types.
 */
export type RecommendationType =
  | 'index'
  | 'sql_rewrite'
  | 'optimizer_hint'
  | 'statistics'
  | 'partition'
  | 'parallel';

/**
 * Recommendation subtypes.
 */
export type RecommendationSubtype =
  | 'missing_index'
  | 'inefficient_index'
  | 'or_to_union'
  | 'not_in_to_not_exists'
  | 'eliminate_distinct'
  | 'scalar_subquery_to_join'
  | 'select_star'
  | 'join_method'
  | 'index_hint'
  | 'parallel_hint'
  | 'stale_statistics'
  | 'missing_statistics'
  | 'parallel_scan';

/**
 * Priority levels.
 */
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low';

/**
 * Impact levels.
 */
export type RecommendationImpact = 'high' | 'medium' | 'low' | 'minimal';

/**
 * Base recommendation model.
 */
export interface Recommendation {
  type: RecommendationType;
  subtype: RecommendationSubtype;
  priority: RecommendationPriority;
  estimated_impact: RecommendationImpact;
  title: string;
  description: string;
  rationale?: string[];
  implementation_notes?: string[];
}

/**
 * Index-related recommendation.
 */
export interface IndexRecommendation extends Recommendation {
  table?: string;
  columns?: string[];
  index_name?: string;
  current_operation?: string;
  cost?: number;
  cardinality?: number;
  sql?: string;
}

/**
 * SQL rewrite recommendation.
 */
export interface SQLRewriteRecommendation extends Recommendation {
  original_pattern?: string;
  suggested_pattern?: string;
  example_before?: string;
  example_after?: string;
}

/**
 * Optimizer hint recommendation.
 */
export interface OptimizerHintRecommendation extends Recommendation {
  hint: string;
  affected_operation?: string;
  table?: string;
  cardinality?: number;
  cost?: number;
  total_cost?: number;
}

/**
 * Statistics gathering recommendation.
 */
export interface StatisticsRecommendation extends Recommendation {
  table: string;
  sql: string;
  statistics_age_days?: number;
  last_analyzed?: string;
}

/**
 * Parallelism recommendation.
 */
export interface ParallelismRecommendation extends Recommendation {
  table?: string;
  cardinality?: number;
  cost?: number;
  hint?: string;
  sql?: string;
}

/**
 * Summary of recommendations.
 */
export interface RecommendationSummary {
  total_count: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  by_impact: Record<string, number>;
  critical_count: number;
  high_impact_count: number;
}

/**
 * API response for recommendations.
 */
export interface RecommendationsResponse {
  sql_id: string;
  recommendations: Recommendation[];
  summary: RecommendationSummary;
  generated_at: string;
}

/**
 * API response for index recommendations only.
 */
export interface IndexRecommendationsResponse {
  sql_id: string;
  recommendations: IndexRecommendation[];
  total_count: number;
}

/**
 * API response for SQL rewrite recommendations only.
 */
export interface SQLRewriteRecommendationsResponse {
  sql_id: string;
  recommendations: SQLRewriteRecommendation[];
  total_count: number;
}

/**
 * API response for optimizer hint recommendations only.
 */
export interface HintRecommendationsResponse {
  sql_id: string;
  recommendations: OptimizerHintRecommendation[];
  total_count: number;
}

/**
 * Filters for recommendation queries.
 */
export interface RecommendationFilters {
  types?: RecommendationType[];
  priorities?: RecommendationPriority[];
  min_impact?: RecommendationImpact;
}

/**
 * Request for generating recommendations.
 */
export interface RecommendationRequest {
  sql_id: string;
  include_index?: boolean;
  include_rewrite?: boolean;
  include_hints?: boolean;
  include_statistics?: boolean;
  include_parallelism?: boolean;
}

/**
 * Sort options for recommendations list.
 */
export type RecommendationSortField = 'priority' | 'impact' | 'type';

export interface RecommendationSort {
  field: RecommendationSortField;
  order: 'asc' | 'desc';
}

/**
 * Grouped recommendations by type.
 */
export interface GroupedRecommendations {
  index: IndexRecommendation[];
  sql_rewrite: SQLRewriteRecommendation[];
  optimizer_hint: OptimizerHintRecommendation[];
  statistics: StatisticsRecommendation[];
  parallelism: ParallelismRecommendation[];
}
