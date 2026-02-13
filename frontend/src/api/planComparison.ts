/**
 * API client for plan comparison-related endpoints.
 * Uses React Query (TanStack Query) for data fetching and caching.
 */

import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import {
  PlanComparisonResponse,
  PlanVersionsResponse,
  BaselineRecommendation,
  CompareRequest,
  BaselineRequest,
  PlanVersionSource,
  RegressionChartData,
  Severity,
  Priority,
} from '../types/planComparison';
import { ApiError } from '../types/query';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Query keys for React Query cache management.
 */
export const planComparisonKeys = {
  all: ['planComparison'] as const,
  versions: (sqlId: string, source?: PlanVersionSource) =>
    [...planComparisonKeys.all, 'versions', sqlId, source] as const,
  comparison: (
    sqlId: string,
    currentPlanHash?: number,
    historicalPlanHash?: number
  ) =>
    [...planComparisonKeys.all, 'comparison', sqlId, currentPlanHash, historicalPlanHash] as const,
  baseline: (sqlId: string, currentPlanHash: number, preferredPlanHash: number) =>
    [...planComparisonKeys.all, 'baseline', sqlId, currentPlanHash, preferredPlanHash] as const,
};

/**
 * Fetch all plan versions for a SQL_ID.
 */
export const fetchPlanVersions = async (
  sqlId: string,
  source: PlanVersionSource = 'both'
): Promise<PlanVersionsResponse> => {
  const params = new URLSearchParams();
  params.append('source', source);

  const response = await axios.get<PlanVersionsResponse>(
    `${API_BASE_URL}/api/v1/plan-comparison/${sqlId}/versions?${params.toString()}`
  );
  return response.data;
};

/**
 * Compare execution plans for a SQL_ID.
 */
export const comparePlans = async (
  sqlId: string,
  currentPlanHash?: number,
  historicalPlanHash?: number,
  includeRecommendations: boolean = true
): Promise<PlanComparisonResponse> => {
  const params = new URLSearchParams();
  if (currentPlanHash) {
    params.append('current_plan_hash', currentPlanHash.toString());
  }
  if (historicalPlanHash) {
    params.append('historical_plan_hash', historicalPlanHash.toString());
  }
  params.append('include_recommendations', includeRecommendations.toString());

  const url = `${API_BASE_URL}/api/v1/plan-comparison/${sqlId}/compare${
    params.toString() ? `?${params.toString()}` : ''
  }`;

  const response = await axios.get<PlanComparisonResponse>(url);
  return response.data;
};

/**
 * Compare specific plan versions.
 */
export const compareSpecificPlan = async (
  sqlId: string,
  planHashValue: number,
  compareTo?: number
): Promise<PlanComparisonResponse> => {
  const params = new URLSearchParams();
  if (compareTo) {
    params.append('compare_to', compareTo.toString());
  }

  const url = `${API_BASE_URL}/api/v1/plan-comparison/${sqlId}/compare/${planHashValue}${
    params.toString() ? `?${params.toString()}` : ''
  }`;

  const response = await axios.get<PlanComparisonResponse>(url);
  return response.data;
};

/**
 * Get baseline recommendation for a SQL_ID.
 */
export const getBaselineRecommendation = async (
  request: BaselineRequest
): Promise<BaselineRecommendation> => {
  const response = await axios.post<BaselineRecommendation>(
    `${API_BASE_URL}/api/v1/plan-comparison/${request.sql_id}/baseline-recommendation`,
    request
  );
  return response.data;
};

/**
 * React Query hook for fetching plan versions.
 */
export const usePlanVersions = (
  sqlId: string,
  source: PlanVersionSource = 'both',
  enabled: boolean = true
): UseQueryResult<PlanVersionsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: planComparisonKeys.versions(sqlId, source),
    queryFn: () => fetchPlanVersions(sqlId, source),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for comparing plans.
 */
export const usePlanComparison = (
  sqlId: string,
  currentPlanHash?: number,
  historicalPlanHash?: number,
  includeRecommendations: boolean = true,
  enabled: boolean = true
): UseQueryResult<PlanComparisonResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: planComparisonKeys.comparison(sqlId, currentPlanHash, historicalPlanHash),
    queryFn: () => comparePlans(sqlId, currentPlanHash, historicalPlanHash, includeRecommendations),
    enabled: enabled && !!sqlId,
    staleTime: 180000, // 3 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for comparing specific plan.
 */
export const useSpecificPlanComparison = (
  sqlId: string,
  planHashValue: number,
  compareTo?: number,
  enabled: boolean = true
): UseQueryResult<PlanComparisonResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: planComparisonKeys.comparison(sqlId, planHashValue, compareTo),
    queryFn: () => compareSpecificPlan(sqlId, planHashValue, compareTo),
    enabled: enabled && !!sqlId && !!planHashValue,
    staleTime: 180000, // 3 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query mutation hook for getting baseline recommendation.
 */
export const useBaselineRecommendation = (): UseMutationResult<
  BaselineRecommendation,
  AxiosError<ApiError>,
  BaselineRequest
> => {
  return useMutation({
    mutationFn: getBaselineRecommendation,
    retry: 1,
  });
};

/**
 * Helper function to get severity color for UI components.
 */
export const getSeverityColor = (severity: Severity): string => {
  switch (severity) {
    case 'critical':
      return 'red';
    case 'high':
      return 'red';
    case 'medium':
      return 'orange';
    case 'low':
      return 'yellow';
    case 'none':
      return 'green';
    default:
      return 'default';
  }
};

/**
 * Helper function to get priority color for UI components.
 */
export const getPriorityColor = (priority: Priority): string => {
  switch (priority) {
    case 'high':
      return 'red';
    case 'medium':
      return 'orange';
    case 'low':
      return 'blue';
    case 'none':
      return 'default';
    default:
      return 'default';
  }
};

/**
 * Helper function to get severity badge icon.
 */
export const getSeverityIcon = (severity: Severity): string => {
  switch (severity) {
    case 'critical':
      return '🔴';
    case 'high':
      return '🔴';
    case 'medium':
      return '🟠';
    case 'low':
      return '🟡';
    case 'none':
      return '🟢';
    default:
      return '⚪';
  }
};

/**
 * Helper function to format percentage change.
 */
export const formatPercentageChange = (changePercent?: number): string => {
  if (changePercent === undefined || changePercent === null) {
    return 'N/A';
  }

  const sign = changePercent >= 0 ? '+' : '';
  return `${sign}${changePercent.toFixed(1)}%`;
};

/**
 * Helper function to format ratio.
 */
export const formatRatio = (ratio?: number): string => {
  if (ratio === undefined || ratio === null) {
    return 'N/A';
  }

  return `${ratio.toFixed(2)}x`;
};

/**
 * Helper function to determine if change is a regression.
 */
export const isRegression = (changePercent?: number, threshold: number = 20): boolean => {
  return changePercent !== undefined && changePercent > threshold;
};

/**
 * Helper function to determine if change is an improvement.
 */
export const isImprovement = (changePercent?: number, threshold: number = -20): boolean => {
  return changePercent !== undefined && changePercent < threshold;
};

/**
 * Helper function to convert comparison data to chart format.
 */
export const toRegressionChartData = (
  currentMetrics?: Record<string, any>,
  historicalMetrics?: Record<string, any>
): RegressionChartData[] => {
  if (!currentMetrics || !historicalMetrics) {
    return [];
  }

  const chartData: RegressionChartData[] = [];
  const metricsToCompare = ['total_cost', 'total_cardinality', 'total_cpu_cost', 'total_io_cost'];

  for (const metric of metricsToCompare) {
    const current = currentMetrics[metric] || 0;
    const historical = historicalMetrics[metric] || 0;

    if (historical > 0) {
      const changePercent = ((current - historical) / historical) * 100;

      chartData.push({
        metric: formatMetricName(metric),
        current,
        historical,
        change_percent: changePercent,
        is_regression: changePercent > 20,
      });
    }
  }

  return chartData;
};

/**
 * Helper function to format metric names for display.
 */
export const formatMetricName = (metric: string): string => {
  return metric
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace('Total ', '');
};

/**
 * Helper function to get change type icon.
 */
export const getChangeTypeIcon = (changeType: string): string => {
  switch (changeType.toLowerCase()) {
    case 'access_method_change':
      return '🔄';
    case 'join_order_change':
      return '🔀';
    case 'new_object_access':
      return '➕';
    case 'removed_object_access':
      return '➖';
    default:
      return '📝';
  }
};

/**
 * Helper function to format plan version source.
 */
export const formatPlanSource = (source?: string): string => {
  if (!source) return 'Unknown';

  switch (source.toLowerCase()) {
    case 'current':
      return 'Current (V$SQL_PLAN)';
    case 'historical':
      return 'Historical (AWR)';
    default:
      return source;
  }
};

/**
 * Helper function to get recommendation type icon.
 */
export const getRecommendationTypeIcon = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'action_required':
      return '⚠️';
    case 'access_method_regression':
      return '🔴';
    case 'positive':
      return '✅';
    case 'info':
      return 'ℹ️';
    default:
      return '💡';
  }
};

/**
 * Helper function to calculate overall comparison score.
 */
export const calculateComparisonScore = (
  regressionCount: number,
  improvementCount: number,
  totalChanges: number
): number => {
  if (totalChanges === 0) return 100;

  const regressionPenalty = regressionCount * 20;
  const improvementBonus = improvementCount * 5;
  const changePenalty = totalChanges * 2;

  const score = 100 - regressionPenalty + improvementBonus - changePenalty;

  return Math.max(0, Math.min(100, score));
};

/**
 * Helper function to format timestamp for display.
 */
export const formatComparisonTimestamp = (timestamp?: string): string => {
  if (!timestamp) return 'N/A';

  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Helper function to get access method icon.
 */
export const getAccessMethodIcon = (method?: string): string => {
  if (!method) return '❓';

  const methodUpper = method.toUpperCase();

  if (methodUpper.includes('INDEX')) return '🔍';
  if (methodUpper.includes('FULL')) return '📊';
  if (methodUpper.includes('ROWID')) return '🎯';
  if (methodUpper.includes('HASH')) return '🔗';
  if (methodUpper.includes('NESTED')) return '🔄';
  if (methodUpper.includes('MERGE')) return '🔀';

  return '▪️';
};

/**
 * Helper function to determine if baseline is needed.
 */
export const shouldRecommendBaseline = (
  regressionCount: number,
  severity: Severity,
  totalChanges: number
): boolean => {
  if (severity === 'high' || severity === 'critical') return true;
  if (regressionCount >= 3) return true;
  if (totalChanges >= 5) return true;

  return false;
};

/**
 * Helper function to export comparison data as JSON.
 */
export const exportComparisonAsJSON = (comparison: PlanComparisonResponse): string => {
  return JSON.stringify(comparison.data, null, 2);
};

/**
 * Helper function to copy baseline SQL to clipboard.
 */
export const copyBaselineSQLToClipboard = async (sql?: string): Promise<boolean> => {
  if (!sql) return false;

  try {
    await navigator.clipboard.writeText(sql);
    return true;
  } catch (error) {
    console.error('Failed to copy SQL to clipboard:', error);
    return false;
  }
};
