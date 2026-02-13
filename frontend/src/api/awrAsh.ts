/**
 * AWR/ASH API client with React Query hooks
 */

import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  SnapshotListResponse,
  AWRReport,
  ASHActivityResponse,
  HistoricalSQLResponse,
  HistoricalComparisonResult,
  PerformanceTrendResult,
  RegressionDetectionResult,
  ASHSQLAnalysis,
  AWRReportParams,
  ASHActivityParams,
  HistoricalComparisonParams,
  PerformanceTrendParams,
  RegressionDetectionParams,
} from "../types/awrAsh";

const AWR_ASH_BASE_URL = "/api/v1/awr-ash";

/**
 * Query keys for AWR/ASH
 */
export const awrAshKeys = {
  all: ["awr-ash"] as const,
  snapshots: () => [...awrAshKeys.all, "snapshots"] as const,
  snapshotList: (daysBack: number) => [...awrAshKeys.snapshots(), daysBack] as const,
  reports: () => [...awrAshKeys.all, "reports"] as const,
  report: (params: AWRReportParams) => [...awrAshKeys.reports(), params] as const,
  ashActivity: () => [...awrAshKeys.all, "ash-activity"] as const,
  ashActivityQuery: (params: ASHActivityParams) => [...awrAshKeys.ashActivity(), params] as const,
  ashSqlAnalysis: (sqlId: string, minutesBack: number) =>
    [...awrAshKeys.all, "ash-sql", sqlId, minutesBack] as const,
  historical: () => [...awrAshKeys.all, "historical"] as const,
  historicalSql: (sqlId: string, daysBack: number) =>
    [...awrAshKeys.historical(), "sql", sqlId, daysBack] as const,
  comparison: (params: HistoricalComparisonParams) =>
    [...awrAshKeys.historical(), "comparison", params] as const,
  trends: (params: PerformanceTrendParams) =>
    [...awrAshKeys.historical(), "trends", params] as const,
  regression: (params: RegressionDetectionParams) =>
    [...awrAshKeys.historical(), "regression", params] as const,
};

/**
 * Fetch AWR snapshots
 */
export async function fetchAWRSnapshots(
  daysBack: number = 7,
  limit?: number
): Promise<SnapshotListResponse> {
  const params = new URLSearchParams();
  params.append("days_back", daysBack.toString());
  if (limit) {
    params.append("limit", limit.toString());
  }

  const response = await apiClient.get<SnapshotListResponse>(
    `${AWR_ASH_BASE_URL}/snapshots?${params.toString()}`
  );
  return response.data;
}

/**
 * Hook to fetch AWR snapshots
 */
export function useAWRSnapshots(
  daysBack: number = 7,
  limit?: number,
  enabled: boolean = true
): UseQueryResult<SnapshotListResponse, Error> {
  return useQuery({
    queryKey: awrAshKeys.snapshotList(daysBack),
    queryFn: () => fetchAWRSnapshots(daysBack, limit),
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Generate AWR report
 */
export async function generateAWRReport(
  params: AWRReportParams
): Promise<AWRReport> {
  const queryParams = new URLSearchParams();
  queryParams.append("begin_snap_id", params.begin_snap_id.toString());
  queryParams.append("end_snap_id", params.end_snap_id.toString());
  if (params.top_n) {
    queryParams.append("top_n", params.top_n.toString());
  }
  if (params.format) {
    queryParams.append("format", params.format);
  }

  const response = await apiClient.get<AWRReport>(
    `${AWR_ASH_BASE_URL}/report?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * Hook to generate AWR report
 */
export function useAWRReport(
  params: AWRReportParams,
  enabled: boolean = true
): UseQueryResult<AWRReport, Error> {
  return useQuery({
    queryKey: awrAshKeys.report(params),
    queryFn: () => generateAWRReport(params),
    enabled: enabled && params.begin_snap_id > 0 && params.end_snap_id > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetch ASH activity samples
 */
export async function fetchASHActivity(
  params: ASHActivityParams
): Promise<ASHActivityResponse> {
  const queryParams = new URLSearchParams();

  if (params.sql_id) {
    queryParams.append("sql_id", params.sql_id);
  }
  if (params.begin_time) {
    queryParams.append("begin_time", params.begin_time);
  }
  if (params.end_time) {
    queryParams.append("end_time", params.end_time);
  }
  if (params.minutes_back) {
    queryParams.append("minutes_back", params.minutes_back.toString());
  }
  if (params.limit) {
    queryParams.append("limit", params.limit.toString());
  }

  const response = await apiClient.get<ASHActivityResponse>(
    `${AWR_ASH_BASE_URL}/ash/activity?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * Hook to fetch ASH activity
 */
export function useASHActivity(
  params: ASHActivityParams,
  enabled: boolean = true
): UseQueryResult<ASHActivityResponse, Error> {
  return useQuery({
    queryKey: awrAshKeys.ashActivityQuery(params),
    queryFn: () => fetchASHActivity(params),
    enabled,
    staleTime: 30 * 1000, // 30 seconds (real-time data)
  });
}

/**
 * Analyze SQL ASH activity
 */
export async function analyzeASHForSQL(
  sqlId: string,
  minutesBack: number = 60
): Promise<ASHSQLAnalysis> {
  const params = new URLSearchParams();
  params.append("minutes_back", minutesBack.toString());

  const response = await apiClient.get<ASHSQLAnalysis>(
    `${AWR_ASH_BASE_URL}/ash/sql/${sqlId}?${params.toString()}`
  );
  return response.data;
}

/**
 * Hook to analyze SQL ASH activity
 */
export function useASHSQLAnalysis(
  sqlId: string,
  minutesBack: number = 60,
  enabled: boolean = true
): UseQueryResult<ASHSQLAnalysis, Error> {
  return useQuery({
    queryKey: awrAshKeys.ashSqlAnalysis(sqlId, minutesBack),
    queryFn: () => analyzeASHForSQL(sqlId, minutesBack),
    enabled: enabled && !!sqlId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

/**
 * Fetch historical SQL performance
 */
export async function fetchHistoricalSQLPerformance(
  sqlId: string,
  daysBack: number = 7
): Promise<HistoricalSQLResponse> {
  const params = new URLSearchParams();
  params.append("days_back", daysBack.toString());

  const response = await apiClient.get<HistoricalSQLResponse>(
    `${AWR_ASH_BASE_URL}/historical/sql/${sqlId}?${params.toString()}`
  );
  return response.data;
}

/**
 * Hook to fetch historical SQL performance
 */
export function useHistoricalSQLPerformance(
  sqlId: string,
  daysBack: number = 7,
  enabled: boolean = true
): UseQueryResult<HistoricalSQLResponse, Error> {
  return useQuery({
    queryKey: awrAshKeys.historicalSql(sqlId, daysBack),
    queryFn: () => fetchHistoricalSQLPerformance(sqlId, daysBack),
    enabled: enabled && !!sqlId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Compare current vs historical performance
 */
export async function compareCurrentVsHistorical(
  params: HistoricalComparisonParams
): Promise<HistoricalComparisonResult> {
  const queryParams = new URLSearchParams();
  if (params.days_back) {
    queryParams.append("days_back", params.days_back.toString());
  }
  if (params.threshold_percent) {
    queryParams.append("threshold_percent", params.threshold_percent.toString());
  }

  const response = await apiClient.get<HistoricalComparisonResult>(
    `${AWR_ASH_BASE_URL}/historical/compare/${params.sql_id}?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * Hook to compare current vs historical
 */
export function useHistoricalComparison(
  params: HistoricalComparisonParams,
  enabled: boolean = true
): UseQueryResult<HistoricalComparisonResult, Error> {
  return useQuery({
    queryKey: awrAshKeys.comparison(params),
    queryFn: () => compareCurrentVsHistorical(params),
    enabled: enabled && !!params.sql_id,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Analyze performance trend
 */
export async function analyzePerformanceTrend(
  params: PerformanceTrendParams
): Promise<PerformanceTrendResult> {
  const queryParams = new URLSearchParams();
  if (params.days_back) {
    queryParams.append("days_back", params.days_back.toString());
  }

  const response = await apiClient.get<PerformanceTrendResult>(
    `${AWR_ASH_BASE_URL}/historical/trends/${params.sql_id}?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * Hook to analyze performance trend
 */
export function usePerformanceTrend(
  params: PerformanceTrendParams,
  enabled: boolean = true
): UseQueryResult<PerformanceTrendResult, Error> {
  return useQuery({
    queryKey: awrAshKeys.trends(params),
    queryFn: () => analyzePerformanceTrend(params),
    enabled: enabled && !!params.sql_id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Detect performance regression
 */
export async function detectPerformanceRegression(
  params: RegressionDetectionParams
): Promise<RegressionDetectionResult> {
  const queryParams = new URLSearchParams();
  if (params.baseline_days) {
    queryParams.append("baseline_days", params.baseline_days.toString());
  }
  if (params.recent_days) {
    queryParams.append("recent_days", params.recent_days.toString());
  }
  if (params.threshold_percent) {
    queryParams.append("threshold_percent", params.threshold_percent.toString());
  }

  const response = await apiClient.get<RegressionDetectionResult>(
    `${AWR_ASH_BASE_URL}/historical/regression/${params.sql_id}?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * Hook to detect performance regression
 */
export function useRegressionDetection(
  params: RegressionDetectionParams,
  enabled: boolean = true
): UseQueryResult<RegressionDetectionResult, Error> {
  return useQuery({
    queryKey: awrAshKeys.regression(params),
    queryFn: () => detectPerformanceRegression(params),
    enabled: enabled && !!params.sql_id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Utility: Format time range for display
 */
export function formatTimeRange(begin: string, end: string): string {
  const beginDate = new Date(begin);
  const endDate = new Date(end);
  const duration = (endDate.getTime() - beginDate.getTime()) / 1000 / 60; // minutes

  return `${duration.toFixed(0)} minutes`;
}

/**
 * Utility: Get trend color
 */
export function getTrendColor(trend: string): string {
  switch (trend.toLowerCase()) {
    case "improving":
      return "green";
    case "degrading":
      return "red";
    case "stable":
      return "blue";
    case "anomaly":
      return "orange";
    default:
      return "gray";
  }
}

/**
 * Utility: Get regression severity color
 */
export function getRegressionSeverityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical":
      return "red";
    case "high":
      return "orange";
    case "medium":
      return "gold";
    case "none":
      return "green";
    default:
      return "default";
  }
}

/**
 * Utility: Format snapshot time
 */
export function formatSnapshotTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

/**
 * Utility: Calculate elapsed time between snapshots
 */
export function calculateElapsedTime(begin: string, end: string): number {
  const beginDate = new Date(begin);
  const endDate = new Date(end);
  return (endDate.getTime() - beginDate.getTime()) / 1000 / 60; // minutes
}

/**
 * Utility: Format metric value
 */
export function formatMetricValue(value: number, metric: string): string {
  if (metric.includes("time") || metric.includes("sec")) {
    return `${value.toFixed(2)}s`;
  } else if (metric.includes("gets") || metric.includes("reads")) {
    return value.toLocaleString();
  } else {
    return value.toFixed(2);
  }
}

/**
 * Utility: Get wait class color
 */
export function getWaitClassColor(waitClass: string): string {
  switch (waitClass.toLowerCase()) {
    case "user i/o":
      return "#1890ff"; // blue
    case "concurrency":
      return "#f5222d"; // red
    case "system i/o":
      return "#52c41a"; // green
    case "application":
      return "#fa8c16"; // orange
    case "commit":
      return "#722ed1"; // purple
    case "configuration":
      return "#eb2f96"; // magenta
    case "network":
      return "#13c2c2"; // cyan
    case "cpu":
      return "#faad14"; // gold
    default:
      return "#8c8c8c"; // gray
  }
}
