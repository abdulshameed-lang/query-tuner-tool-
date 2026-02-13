/**
 * Bug detection API client with React Query hooks
 */

import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  Bug,
  BugDetectionResponse,
  BugListResponse,
  VersionCheckResponse,
  BugFilters,
  BugDetectionParams,
  VersionCheckParams,
} from "../types/bug";

const BUGS_BASE_URL = "/api/v1/bugs";

/**
 * Query keys for bug detection
 */
export const bugKeys = {
  all: ["bugs"] as const,
  lists: () => [...bugKeys.all, "list"] as const,
  list: (filters: BugFilters) => [...bugKeys.lists(), filters] as const,
  detections: () => [...bugKeys.all, "detection"] as const,
  detection: (params: BugDetectionParams) => [...bugKeys.detections(), params] as const,
  versions: () => [...bugKeys.all, "version"] as const,
  version: (version: string) => [...bugKeys.versions(), version] as const,
};

/**
 * Fetch all bugs with optional filters
 */
export async function fetchAllBugs(filters?: BugFilters): Promise<BugListResponse> {
  const params = new URLSearchParams();

  if (filters?.category) {
    params.append("category", filters.category);
  }
  if (filters?.severity) {
    params.append("severity", filters.severity);
  }
  if (filters?.version) {
    params.append("version", filters.version);
  }

  const url = params.toString()
    ? `${BUGS_BASE_URL}?${params.toString()}`
    : BUGS_BASE_URL;

  const response = await apiClient.get<BugListResponse>(url);
  return response.data;
}

/**
 * Hook to fetch all bugs with optional filters
 */
export function useAllBugs(
  filters?: BugFilters,
  enabled: boolean = true
): UseQueryResult<BugListResponse, Error> {
  return useQuery({
    queryKey: bugKeys.list(filters || {}),
    queryFn: () => fetchAllBugs(filters),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch bug detection for a specific SQL_ID
 */
export async function fetchBugDetection(
  params: BugDetectionParams
): Promise<BugDetectionResponse> {
  const url = params.database_version
    ? `${BUGS_BASE_URL}/${params.sql_id}?database_version=${params.database_version}`
    : `${BUGS_BASE_URL}/${params.sql_id}`;

  const response = await apiClient.get<BugDetectionResponse>(url);
  return response.data;
}

/**
 * Hook to detect bugs for a specific SQL_ID
 */
export function useBugDetection(
  params: BugDetectionParams,
  enabled: boolean = true
): UseQueryResult<BugDetectionResponse, Error> {
  return useQuery({
    queryKey: bugKeys.detection(params),
    queryFn: () => fetchBugDetection(params),
    enabled: enabled && !!params.sql_id,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Fetch bugs affecting a specific database version
 */
export async function fetchVersionBugs(
  version: string
): Promise<VersionCheckResponse> {
  const response = await apiClient.get<VersionCheckResponse>(
    `${BUGS_BASE_URL}/version/${version}`
  );
  return response.data;
}

/**
 * Hook to check bugs affecting a specific database version
 */
export function useVersionBugs(
  version: string,
  enabled: boolean = true
): UseQueryResult<VersionCheckResponse, Error> {
  return useQuery({
    queryKey: bugKeys.version(version),
    queryFn: () => fetchVersionBugs(version),
    enabled: enabled && !!version,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Get bug by bug number from list
 */
export function getBugByNumber(bugs: Bug[], bugNumber: string): Bug | undefined {
  return bugs.find((bug) => bug.bug_number === bugNumber);
}

/**
 * Filter bugs by severity
 */
export function filterBugsBySeverity(bugs: Bug[], severity: string): Bug[] {
  return bugs.filter((bug) => bug.severity === severity);
}

/**
 * Filter bugs by category
 */
export function filterBugsByCategory(bugs: Bug[], category: string): Bug[] {
  return bugs.filter((bug) => bug.category === category);
}

/**
 * Check if bug affects a specific version
 */
export function bugAffectsVersion(bug: Bug, version: string): boolean {
  return bug.affected_versions.some((v) => {
    // Handle wildcard versions like "12.1.%"
    if (v.includes("%")) {
      const pattern = v.replace(/%/g, ".*");
      const regex = new RegExp(`^${pattern}$`);
      return regex.test(version);
    }
    return v === version;
  });
}

/**
 * Get severity badge color
 */
export function getSeverityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical":
      return "red";
    case "high":
      return "orange";
    case "medium":
      return "gold";
    case "low":
      return "blue";
    default:
      return "default";
  }
}

/**
 * Get confidence level label
 */
export function getConfidenceLevel(confidence: number): string {
  if (confidence >= 90) return "Very High";
  if (confidence >= 75) return "High";
  if (confidence >= 60) return "Medium";
  if (confidence >= 50) return "Low";
  return "Very Low";
}

/**
 * Get confidence color
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 90) return "green";
  if (confidence >= 75) return "blue";
  if (confidence >= 60) return "gold";
  if (confidence >= 50) return "orange";
  return "red";
}

/**
 * Format bug number for display
 */
export function formatBugNumber(bugNumber: string): string {
  return `Bug ${bugNumber}`;
}

/**
 * Get category icon name (for Ant Design icons)
 */
export function getCategoryIcon(category: string): string {
  switch (category.toLowerCase()) {
    case "optimizer":
      return "BulbOutlined";
    case "execution":
      return "ThunderboltOutlined";
    case "statistics":
      return "BarChartOutlined";
    case "parallel":
      return "NodeIndexOutlined";
    case "partitioning":
      return "SplitCellsOutlined";
    case "parsing":
      return "FileTextOutlined";
    case "memory":
      return "DatabaseOutlined";
    case "locking":
      return "LockOutlined";
    case "network":
      return "GlobalOutlined";
    default:
      return "BugOutlined";
  }
}
