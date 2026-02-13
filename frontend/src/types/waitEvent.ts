/**
 * TypeScript type definitions for wait events.
 * These types mirror the backend Pydantic schemas.
 */

/**
 * Individual wait event from ASH.
 */
export interface WaitEvent {
  sql_id?: string;
  sample_time?: string;
  session_id?: number;
  session_serial?: number;
  event?: string;
  wait_class?: string;
  wait_time?: number;
  time_waited?: number;
  p1text?: string;
  p1?: number;
  p2text?: string;
  p2?: number;
  p3text?: string;
  p3?: number;
  current_obj?: number;
  current_file?: number;
  current_block?: number;
  session_state?: string;
  blocking_session?: number;
  blocking_session_serial?: number;
  sql_plan_hash_value?: number;
  sql_plan_line_id?: number;
  category?: string;
}

/**
 * Current wait event from V$SESSION_WAIT.
 */
export interface CurrentWaitEvent {
  sid: number;
  serial: number;
  username?: string;
  program?: string;
  sql_id?: string;
  event: string;
  wait_class: string;
  state: string;
  wait_time?: number;
  seconds_in_wait?: number;
  p1text?: string;
  p1?: number;
  p2text?: string;
  p2?: number;
  p3text?: string;
  p3?: number;
  category?: string;
}

/**
 * Aggregated wait event summary.
 */
export interface WaitEventSummary {
  event: string;
  wait_class: string;
  category: string;
  wait_count: number;
  total_time_waited: number;
  avg_time_waited?: number;
  max_time_waited?: number;
  percentage: number;
}

/**
 * Wait event category aggregation.
 */
export interface WaitEventCategory {
  category: string;
  name: string;
  color: string;
  total_time_waited: number;
  wait_count?: number;
  event_types?: number;
  session_count?: number;
  total_wait_time?: number;
  percentage?: number;
}

/**
 * Time bucket for wait event timeline.
 */
export interface WaitEventTimelineBucket {
  sample_minute: string;
  wait_class: string;
  category: string;
  sample_count: number;
  total_time_waited: number;
}

/**
 * Blocking session information.
 */
export interface BlockingSession {
  blocking_session: number;
  blocking_session_serial: number;
  blocking_username?: string;
  blocking_program?: string;
  blocking_sql_id?: string;
  event: string;
  block_count: number;
}

/**
 * Wait event tuning recommendation.
 */
export interface WaitEventRecommendation {
  type: string;
  priority: 'low' | 'medium' | 'high';
  message: string;
  suggestions: string[];
  blocking_sessions?: BlockingSession[];
}

/**
 * Wait events data for a SQL_ID.
 */
export interface WaitEventsData {
  sql_id: string;
  hours_back: number;
  total_time_waited: number;
  total_samples: number;
  wait_events: WaitEvent[];
  category_breakdown: WaitEventCategory[];
  top_events: WaitEventSummary[];
  timeline: WaitEventTimelineBucket[];
  blocking_sessions: BlockingSession[];
  recommendations: WaitEventRecommendation[];
}

/**
 * API response for wait events by SQL_ID.
 */
export interface WaitEventsResponse {
  data: WaitEventsData;
}

/**
 * Wait events grouped by SQL_ID.
 */
export interface WaitEventSQLBreakdown {
  sql_id: string;
  session_count: number;
  events: string[];
}

/**
 * Current system wait events data.
 */
export interface CurrentWaitEventsData {
  timestamp: string;
  total_sessions: number;
  wait_events: CurrentWaitEvent[];
  category_breakdown: WaitEventCategory[];
  sql_id_breakdown: WaitEventSQLBreakdown[];
}

/**
 * API response for current system wait events.
 */
export interface CurrentWaitEventsResponse {
  data: CurrentWaitEventsData;
}

/**
 * Chart data for wait event visualization.
 */
export interface WaitEventChartData {
  name: string;
  value: number;
  percentage: number;
  color: string;
  category: string;
}

/**
 * Timeline chart data point.
 */
export interface TimelineDataPoint {
  time: string;
  [key: string]: number | string; // Dynamic keys for each category
}
