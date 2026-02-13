/**
 * API client for execution plan-related endpoints.
 * Uses React Query (TanStack Query) for data fetching and caching.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import {
  ExecutionPlanResponse,
  PlanHistoryResponse,
  PlanExportResponse,
  PlanExportFormat,
} from '../types/executionPlan';
import { ApiError } from '../types/query';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Query keys for React Query cache management.
 */
export const executionPlanKeys = {
  all: ['executionPlans'] as const,
  lists: () => [...executionPlanKeys.all, 'list'] as const,
  details: () => [...executionPlanKeys.all, 'detail'] as const,
  detail: (sqlId: string, planHashValue?: number) =>
    [...executionPlanKeys.details(), sqlId, planHashValue] as const,
  history: (sqlId: string) => [...executionPlanKeys.all, 'history', sqlId] as const,
  export: (sqlId: string, planHashValue?: number, format?: PlanExportFormat) =>
    [...executionPlanKeys.all, 'export', sqlId, planHashValue, format] as const,
};

/**
 * Fetch execution plan for a SQL_ID.
 */
export const fetchExecutionPlan = async (
  sqlId: string,
  planHashValue?: number
): Promise<ExecutionPlanResponse> => {
  const params = new URLSearchParams();
  if (planHashValue) {
    params.append('plan_hash_value', planHashValue.toString());
  }

  const url = `${API_BASE_URL}/api/v1/execution-plans/${sqlId}${
    params.toString() ? `?${params.toString()}` : ''
  }`;

  const response = await axios.get<ExecutionPlanResponse>(url);
  return response.data;
};

/**
 * Fetch execution plan history for a SQL_ID.
 */
export const fetchPlanHistory = async (sqlId: string): Promise<PlanHistoryResponse> => {
  const response = await axios.get<PlanHistoryResponse>(
    `${API_BASE_URL}/api/v1/execution-plans/${sqlId}/history`
  );
  return response.data;
};

/**
 * Export execution plan in specified format.
 */
export const exportExecutionPlan = async (
  sqlId: string,
  format: PlanExportFormat = 'text',
  planHashValue?: number
): Promise<PlanExportResponse> => {
  const params = new URLSearchParams();
  params.append('format', format);
  if (planHashValue) {
    params.append('plan_hash_value', planHashValue.toString());
  }

  const response = await axios.get<PlanExportResponse>(
    `${API_BASE_URL}/api/v1/execution-plans/${sqlId}/export?${params.toString()}`
  );
  return response.data;
};

/**
 * React Query hook for fetching execution plan.
 */
export const useExecutionPlan = (
  sqlId: string,
  planHashValue?: number,
  enabled: boolean = true
): UseQueryResult<ExecutionPlanResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: executionPlanKeys.detail(sqlId, planHashValue),
    queryFn: () => fetchExecutionPlan(sqlId, planHashValue),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for fetching plan history.
 */
export const usePlanHistory = (
  sqlId: string,
  enabled: boolean = true
): UseQueryResult<PlanHistoryResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: executionPlanKeys.history(sqlId),
    queryFn: () => fetchPlanHistory(sqlId),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for exporting plan.
 */
export const usePlanExport = (
  sqlId: string,
  format: PlanExportFormat = 'text',
  planHashValue?: number,
  enabled: boolean = false
): UseQueryResult<PlanExportResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: executionPlanKeys.export(sqlId, planHashValue, format),
    queryFn: () => exportExecutionPlan(sqlId, format, planHashValue),
    enabled: enabled && !!sqlId,
    staleTime: Infinity, // Export results don't change
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * Helper function to get operation display name.
 */
export const getOperationDisplayName = (operation: string, options?: string): string => {
  if (options) {
    return `${operation} ${options}`;
  }
  return operation;
};

/**
 * Helper function to get severity color.
 */
export const getSeverityColor = (severity: string): string => {
  switch (severity.toLowerCase()) {
    case 'high':
      return 'red';
    case 'medium':
      return 'orange';
    case 'low':
      return 'yellow';
    default:
      return 'default';
  }
};

/**
 * Helper function to get priority color.
 */
export const getPriorityColor = (priority: string): string => {
  switch (priority.toLowerCase()) {
    case 'high':
      return 'red';
    case 'medium':
      return 'orange';
    case 'low':
      return 'blue';
    default:
      return 'default';
  }
};

/**
 * Helper function to format operation cost.
 */
export const formatCost = (cost?: number): string => {
  if (cost === undefined || cost === null) {
    return 'N/A';
  }
  return cost.toLocaleString('en-US');
};

/**
 * Helper function to format cardinality.
 */
export const formatCardinality = (cardinality?: number): string => {
  if (cardinality === undefined || cardinality === null) {
    return 'N/A';
  }
  if (cardinality >= 1000000) {
    return `${(cardinality / 1000000).toFixed(2)}M`;
  }
  if (cardinality >= 1000) {
    return `${(cardinality / 1000).toFixed(2)}K`;
  }
  return cardinality.toLocaleString('en-US');
};

/**
 * Helper function to determine if operation is costly.
 */
export const isCostlyOperation = (cost?: number, threshold: number = 1000): boolean => {
  return cost !== undefined && cost >= threshold;
};

/**
 * Helper function to get operation icon based on type.
 */
export const getOperationIcon = (operation: string): string => {
  const op = operation.toUpperCase();

  if (op.includes('TABLE ACCESS')) return '📊';
  if (op.includes('INDEX')) return '🔍';
  if (op.includes('HASH JOIN')) return '🔗';
  if (op.includes('NESTED LOOPS')) return '🔄';
  if (op.includes('MERGE JOIN')) return '🔀';
  if (op.includes('SORT')) return '📈';
  if (op.includes('FILTER')) return '🔽';
  if (op.includes('VIEW')) return '👁️';
  if (op.includes('UNION')) return '⚡';
  if (op.includes('AGGREGATE')) return '📊';

  return '▪️';
};
