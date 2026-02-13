/**
 * Bug detection types matching backend Pydantic schemas
 */

/**
 * Evidence for bug detection
 */
export interface BugEvidence {
  execution_plan?: Record<string, any>;
  parameters?: Record<string, any>;
  query_characteristics?: Record<string, any>;
  wait_events?: Record<string, any>;
  sql_characteristics?: Record<string, any>;
  alert_log?: Record<string, any>;
}

/**
 * Oracle bug information
 */
export interface Bug {
  bug_number: string;
  title: string;
  category: string;
  severity: string;
  description: string;
  symptoms: string[];
  affected_versions: string[];
  fixed_versions: string[];
  workarounds: string[];
  remediation_sql?: string;
  my_oracle_support_url?: string;
}

/**
 * Detected bug match with confidence
 */
export interface BugMatch {
  bug: Bug;
  confidence: number;
  matched_patterns: string[];
  evidence: BugEvidence;
  sql_id?: string;
}

/**
 * Summary of bug detection results
 */
export interface BugDetectionSummary {
  total_bugs: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  high_confidence_count: number;
  critical_count: number;
}

/**
 * Bug detection API response
 */
export interface BugDetectionResponse {
  sql_id?: string;
  detected_bugs: BugMatch[];
  summary: BugDetectionSummary;
  database_version?: string;
  detection_timestamp: string;
}

/**
 * Bug list API response
 */
export interface BugListResponse {
  bugs: Bug[];
  total_count: number;
  filters_applied?: Record<string, any>;
}

/**
 * Alert log bug detection response
 */
export interface AlertLogBugResponse {
  detected_bugs: BugMatch[];
  total_count: number;
  summary: BugDetectionSummary;
}

/**
 * Version-specific bug check response
 */
export interface VersionCheckResponse {
  database_version: string;
  bugs_affecting_version: Bug[];
  total_count: number;
  critical_count: number;
  recommendation: string;
}

/**
 * Bug detection filters
 */
export interface BugFilters {
  category?: string;
  severity?: string;
  version?: string;
}

/**
 * Bug severity levels
 */
export enum BugSeverity {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

/**
 * Bug categories
 */
export enum BugCategory {
  OPTIMIZER = "optimizer",
  EXECUTION = "execution",
  STATISTICS = "statistics",
  PARALLEL = "parallel",
  PARTITIONING = "partitioning",
  PARSING = "parsing",
  MEMORY = "memory",
  LOCKING = "locking",
  NETWORK = "network",
  OTHER = "other",
}

/**
 * Bug detection request parameters
 */
export interface BugDetectionParams {
  sql_id: string;
  database_version?: string;
}

/**
 * Version check request parameters
 */
export interface VersionCheckParams {
  database_version: string;
}
