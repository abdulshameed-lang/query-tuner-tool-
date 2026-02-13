/**
 * API client for query-related endpoints.
 * Uses React Query (TanStack Query) for data fetching and caching.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import {
  QueryListResponse,
  QueryDetailResponse,
  QuerySummaryResponse,
  QueryFilters,
  QuerySort,
  PaginationParams,
  ApiError,
} from '../types/query';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Query keys for React Query cache management.
 */
export const queryKeys = {
  all: ['queries'] as const,
  lists: () => [...queryKeys.all, 'list'] as const,
  list: (filters: QueryFilters, sort: QuerySort, pagination: PaginationParams) =>
    [...queryKeys.lists(), { filters, sort, pagination }] as const,
  details: () => [...queryKeys.all, 'detail'] as const,
  detail: (sqlId: string) => [...queryKeys.details(), sqlId] as const,
  summary: () => [...queryKeys.all, 'summary'] as const,
};

/**
 * Fetch list of queries with filtering, sorting, and pagination.
 */
export const fetchQueries = async (
  filters: QueryFilters = {},
  sort: QuerySort = { sort_by: 'elapsed_time', order: 'desc' },
  pagination: PaginationParams = { page: 1, page_size: 20 }
): Promise<QueryListResponse> => {
  const params = new URLSearchParams();

  // Pagination
  params.append('page', pagination.page.toString());
  params.append('page_size', pagination.page_size.toString());

  // Filters
  if (filters.min_elapsed_time !== undefined) {
    params.append('min_elapsed_time', filters.min_elapsed_time.toString());
  }
  if (filters.min_executions !== undefined) {
    params.append('min_executions', filters.min_executions.toString());
  }
  if (filters.schema) {
    params.append('schema', filters.schema);
  }
  if (filters.exclude_system_schemas !== undefined) {
    params.append('exclude_system_schemas', filters.exclude_system_schemas.toString());
  }
  if (filters.sql_text_contains) {
    params.append('sql_text_contains', filters.sql_text_contains);
  }

  // Sorting
  params.append('sort_by', sort.sort_by);
  params.append('order', sort.order);

  const response = await axios.get<QueryListResponse>(
    `${API_BASE_URL}/api/v1/queries?${params.toString()}`
  );

  return response.data;
};

/**
 * Fetch query details by SQL_ID.
 */
export const fetchQueryById = async (sqlId: string): Promise<QueryDetailResponse> => {
  const response = await axios.get<QueryDetailResponse>(
    `${API_BASE_URL}/api/v1/queries/${sqlId}`
  );

  return response.data;
};

/**
 * Fetch query summary statistics.
 */
export const fetchQuerySummary = async (): Promise<QuerySummaryResponse> => {
  const response = await axios.get<QuerySummaryResponse>(
    `${API_BASE_URL}/api/v1/queries/summary/stats`
  );

  return response.data;
};

/**
 * React Query hook for fetching queries list.
 */
export const useQueries = (
  filters: QueryFilters = {},
  sort: QuerySort = { sort_by: 'elapsed_time', order: 'desc' },
  pagination: PaginationParams = { page: 1, page_size: 20 }
): UseQueryResult<QueryListResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: queryKeys.list(filters, sort, pagination),
    queryFn: () => fetchQueries(filters, sort, pagination),
    staleTime: 30000, // 30 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for fetching query details.
 */
export const useQueryDetail = (
  sqlId: string,
  enabled: boolean = true
): UseQueryResult<QueryDetailResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: queryKeys.detail(sqlId),
    queryFn: () => fetchQueryById(sqlId),
    enabled: enabled && !!sqlId,
    staleTime: 60000, // 60 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for fetching query summary.
 */
export const useQuerySummary = (): UseQueryResult<QuerySummaryResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: queryKeys.summary(),
    queryFn: fetchQuerySummary,
    staleTime: 60000, // 60 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * Format elapsed time for display (microseconds to human-readable).
 */
export const formatElapsedTime = (microseconds: number): string => {
  if (microseconds < 1000) {
    return `${microseconds.toFixed(0)} μs`;
  } else if (microseconds < 1000000) {
    return `${(microseconds / 1000).toFixed(2)} ms`;
  } else {
    return `${(microseconds / 1000000).toFixed(2)} s`;
  }
};

/**
 * Format number with commas.
 */
export const formatNumber = (num: number): string => {
  return num.toLocaleString('en-US');
};

/**
 * Format bytes to human-readable size.
 */
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};
