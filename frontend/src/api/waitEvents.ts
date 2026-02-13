/**
 * API client for wait event-related endpoints.
 * Uses React Query (TanStack Query) for data fetching and caching.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import {
  WaitEventsResponse,
  CurrentWaitEventsResponse,
  WaitEventChartData,
  WaitEventCategory,
} from '../types/waitEvent';
import { ApiError } from '../types/query';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Query keys for React Query cache management.
 */
export const waitEventKeys = {
  all: ['waitEvents'] as const,
  bySqlId: (sqlId: string, hoursBack: number) =>
    [...waitEventKeys.all, sqlId, hoursBack] as const,
  current: () => [...waitEventKeys.all, 'current'] as const,
  summary: (sqlId: string, hoursBack: number) =>
    [...waitEventKeys.all, 'summary', sqlId, hoursBack] as const,
};

/**
 * Fetch wait events for a SQL_ID.
 */
export const fetchWaitEvents = async (
  sqlId: string,
  hoursBack: number = 24
): Promise<WaitEventsResponse> => {
  const response = await axios.get<WaitEventsResponse>(
    `${API_BASE_URL}/api/v1/wait-events/${sqlId}?hours_back=${hoursBack}`
  );
  return response.data;
};

/**
 * Fetch current system wait events.
 */
export const fetchCurrentWaitEvents = async (
  topN: number = 50
): Promise<CurrentWaitEventsResponse> => {
  const response = await axios.get<CurrentWaitEventsResponse>(
    `${API_BASE_URL}/api/v1/wait-events/current/system?top_n=${topN}`
  );
  return response.data;
};

/**
 * React Query hook for fetching wait events by SQL_ID.
 */
export const useWaitEvents = (
  sqlId: string,
  hoursBack: number = 24,
  enabled: boolean = true
): UseQueryResult<WaitEventsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: waitEventKeys.bySqlId(sqlId, hoursBack),
    queryFn: () => fetchWaitEvents(sqlId, hoursBack),
    enabled: enabled && !!sqlId,
    staleTime: 60000, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for fetching current system wait events.
 */
export const useCurrentWaitEvents = (
  topN: number = 50,
  enabled: boolean = true
): UseQueryResult<CurrentWaitEventsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: [...waitEventKeys.current(), topN],
    queryFn: () => fetchCurrentWaitEvents(topN),
    enabled,
    staleTime: 10000, // 10 seconds (current data changes frequently)
    refetchInterval: 30000, // Auto-refetch every 30 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * Format wait time for display (microseconds to human-readable).
 */
export const formatWaitTime = (microseconds?: number): string => {
  if (!microseconds || microseconds === 0) return '0 μs';

  if (microseconds < 1000) {
    return `${microseconds.toFixed(0)} μs`;
  } else if (microseconds < 1000000) {
    return `${(microseconds / 1000).toFixed(2)} ms`;
  } else if (microseconds < 60000000) {
    return `${(microseconds / 1000000).toFixed(2)} s`;
  } else {
    return `${(microseconds / 60000000).toFixed(2)} min`;
  }
};

/**
 * Format wait time in seconds.
 */
export const formatWaitTimeSeconds = (seconds?: number): string => {
  if (!seconds || seconds === 0) return '0s';

  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}m`;
  } else {
    return `${(seconds / 3600).toFixed(1)}h`;
  }
};

/**
 * Convert category breakdown to chart data.
 */
export const convertToChartData = (
  categories: WaitEventCategory[]
): WaitEventChartData[] => {
  return categories.map((cat) => ({
    name: cat.name,
    value: cat.total_time_waited,
    percentage: cat.percentage || 0,
    color: cat.color,
    category: cat.category,
  }));
};

/**
 * Get priority color for recommendations.
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
 * Get wait class icon.
 */
export const getWaitClassIcon = (waitClass: string): string => {
  const lowerClass = waitClass.toLowerCase();

  if (lowerClass.includes('i/o') || lowerClass.includes('disk')) return '💾';
  if (lowerClass.includes('cpu')) return '⚡';
  if (lowerClass.includes('concurrency')) return '🔒';
  if (lowerClass.includes('application')) return '📱';
  if (lowerClass.includes('network')) return '🌐';
  if (lowerClass.includes('commit')) return '✅';
  if (lowerClass.includes('idle')) return '⏸️';

  return '⏱️';
};

/**
 * Calculate percentage of total.
 */
export const calculatePercentage = (value: number, total: number): number => {
  if (total === 0) return 0;
  return (value / total) * 100;
};

/**
 * Group timeline data by time bucket.
 */
export const groupTimelineData = (timeline: any[]): any[] => {
  const grouped = new Map<string, any>();

  timeline.forEach((item) => {
    const time = item.sample_minute;
    if (!grouped.has(time)) {
      grouped.set(time, { time });
    }

    const bucket = grouped.get(time)!;
    const category = item.category || 'other';
    bucket[category] = (bucket[category] || 0) + item.total_time_waited;
  });

  return Array.from(grouped.values()).sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
  );
};
