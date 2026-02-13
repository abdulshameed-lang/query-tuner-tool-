/**
 * TypeScript type definitions for query-related data structures.
 * These types mirror the backend Pydantic schemas.
 */

/**
 * Base query information.
 */
export interface QueryBase {
  sql_id: string;
  sql_text: string;
  parsing_schema_name: string;
  executions: number;
  elapsed_time: number;
  cpu_time: number;
  buffer_gets: number;
  disk_reads: number;
  rows_processed: number;
  fetches: number;
  first_load_time: string;
  last_active_time: string;
}

/**
 * Query with calculated metrics (list view).
 */
export interface Query extends QueryBase {
  avg_elapsed_time: number;
  avg_cpu_time: number;
  avg_buffer_gets: number;
  avg_disk_reads: number;
  impact_score: number;
  needs_tuning: boolean;
}

/**
 * Detailed query information (detail view).
 */
export interface QueryDetail extends Query {
  plan_hash_value?: number;
  optimizer_mode?: string;
  optimizer_cost?: number;
  sorts?: number;
  sharable_mem?: number;
  persistent_mem?: number;
  runtime_mem?: number;
  serializable_aborts?: number;
  parse_calls?: number;
  application_wait_time?: number;
  concurrency_wait_time?: number;
  cluster_wait_time?: number;
  user_io_wait_time?: number;
  plsql_exec_time?: number;
  java_exec_time?: number;
  physical_read_requests?: number;
  physical_read_bytes?: number;
  physical_write_requests?: number;
  physical_write_bytes?: number;
  io_cell_offload_eligible_bytes?: number;
  io_interconnect_bytes?: number;
}

/**
 * Query filters for list endpoint.
 */
export interface QueryFilters {
  min_elapsed_time?: number;
  min_executions?: number;
  schema?: string;
  exclude_system_schemas?: boolean;
  sql_text_contains?: string;
}

/**
 * Sort parameters.
 */
export interface QuerySort {
  sort_by: string;
  order: 'asc' | 'desc';
}

/**
 * Pagination parameters.
 */
export interface PaginationParams {
  page: number;
  page_size: number;
}

/**
 * Pagination metadata.
 */
export interface PaginationMetadata {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

/**
 * Query list response.
 */
export interface QueryListResponse {
  data: Query[];
  pagination: PaginationMetadata;
  filters: QueryFilters;
  sort: QuerySort;
}

/**
 * Query detail response.
 */
export interface QueryDetailResponse {
  data: QueryDetail;
  statistics?: {
    total_queries: number;
    total_executions: number;
    total_elapsed_time: number;
    avg_elapsed_time: number;
  };
}

/**
 * Query summary statistics.
 */
export interface QuerySummary {
  total_queries: number;
  total_executions: number;
  total_elapsed_time: number;
  avg_elapsed_time: number;
  queries_needing_tuning: number;
}

/**
 * Query summary response.
 */
export interface QuerySummaryResponse {
  data: QuerySummary;
}

/**
 * API error response.
 */
export interface ApiError {
  code: string;
  message: string;
  sql_id?: string;
}
