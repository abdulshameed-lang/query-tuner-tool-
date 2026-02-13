/**
 * API client for recommendation-related endpoints.
 * Uses React Query (TanStack Query) for data fetching and caching.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import {
  RecommendationsResponse,
  IndexRecommendationsResponse,
  SQLRewriteRecommendationsResponse,
  HintRecommendationsResponse,
  RecommendationPriority,
  RecommendationImpact,
  RecommendationType,
} from '../types/recommendation';
import { ApiError } from '../types/query';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Query keys for React Query cache management.
 */
export const recommendationKeys = {
  all: ['recommendations'] as const,
  lists: () => [...recommendationKeys.all, 'list'] as const,
  detail: (sqlId: string) => [...recommendationKeys.all, 'detail', sqlId] as const,
  index: (sqlId: string) => [...recommendationKeys.all, 'index', sqlId] as const,
  rewrite: (sqlId: string) => [...recommendationKeys.all, 'rewrite', sqlId] as const,
  hints: (sqlId: string) => [...recommendationKeys.all, 'hints', sqlId] as const,
};

/**
 * Fetch all recommendations for a SQL_ID.
 */
export const fetchRecommendations = async (
  sqlId: string,
  includeIndex: boolean = true,
  includeRewrite: boolean = true,
  includeHints: boolean = true,
  includeStatistics: boolean = true,
  includeParallelism: boolean = true
): Promise<RecommendationsResponse> => {
  const params = new URLSearchParams();
  params.append('include_index', includeIndex.toString());
  params.append('include_rewrite', includeRewrite.toString());
  params.append('include_hints', includeHints.toString());
  params.append('include_statistics', includeStatistics.toString());
  params.append('include_parallelism', includeParallelism.toString());

  const response = await axios.get<RecommendationsResponse>(
    `${API_BASE_URL}/api/v1/recommendations/${sqlId}?${params.toString()}`
  );
  return response.data;
};

/**
 * Fetch index recommendations only.
 */
export const fetchIndexRecommendations = async (
  sqlId: string
): Promise<IndexRecommendationsResponse> => {
  const response = await axios.get<IndexRecommendationsResponse>(
    `${API_BASE_URL}/api/v1/recommendations/${sqlId}/index`
  );
  return response.data;
};

/**
 * Fetch SQL rewrite recommendations only.
 */
export const fetchRewriteRecommendations = async (
  sqlId: string
): Promise<SQLRewriteRecommendationsResponse> => {
  const response = await axios.get<SQLRewriteRecommendationsResponse>(
    `${API_BASE_URL}/api/v1/recommendations/${sqlId}/rewrite`
  );
  return response.data;
};

/**
 * Fetch optimizer hint recommendations only.
 */
export const fetchHintRecommendations = async (
  sqlId: string
): Promise<HintRecommendationsResponse> => {
  const response = await axios.get<HintRecommendationsResponse>(
    `${API_BASE_URL}/api/v1/recommendations/${sqlId}/hints`
  );
  return response.data;
};

/**
 * React Query hook for fetching all recommendations.
 */
export const useRecommendations = (
  sqlId: string,
  enabled: boolean = true
): UseQueryResult<RecommendationsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: recommendationKeys.detail(sqlId),
    queryFn: () => fetchRecommendations(sqlId),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * React Query hook for fetching index recommendations.
 */
export const useIndexRecommendations = (
  sqlId: string,
  enabled: boolean = true
): UseQueryResult<IndexRecommendationsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: recommendationKeys.index(sqlId),
    queryFn: () => fetchIndexRecommendations(sqlId),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

/**
 * React Query hook for fetching rewrite recommendations.
 */
export const useRewriteRecommendations = (
  sqlId: string,
  enabled: boolean = true
): UseQueryResult<SQLRewriteRecommendationsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: recommendationKeys.rewrite(sqlId),
    queryFn: () => fetchRewriteRecommendations(sqlId),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

/**
 * React Query hook for fetching hint recommendations.
 */
export const useHintRecommendations = (
  sqlId: string,
  enabled: boolean = true
): UseQueryResult<HintRecommendationsResponse, AxiosError<ApiError>> => {
  return useQuery({
    queryKey: recommendationKeys.hints(sqlId),
    queryFn: () => fetchHintRecommendations(sqlId),
    enabled: enabled && !!sqlId,
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

/**
 * Helper function to get priority color.
 */
export const getPriorityColor = (priority: RecommendationPriority): string => {
  switch (priority) {
    case 'critical':
      return 'red';
    case 'high':
      return 'orange';
    case 'medium':
      return 'blue';
    case 'low':
      return 'default';
    default:
      return 'default';
  }
};

/**
 * Helper function to get impact color.
 */
export const getImpactColor = (impact: RecommendationImpact): string => {
  switch (impact) {
    case 'high':
      return 'green';
    case 'medium':
      return 'cyan';
    case 'low':
      return 'blue';
    case 'minimal':
      return 'default';
    default:
      return 'default';
  }
};

/**
 * Helper function to get priority icon.
 */
export const getPriorityIcon = (priority: RecommendationPriority): string => {
  switch (priority) {
    case 'critical':
      return '🔴';
    case 'high':
      return '🟠';
    case 'medium':
      return '🔵';
    case 'low':
      return '⚪';
    default:
      return '⚪';
  }
};

/**
 * Helper function to get type icon.
 */
export const getTypeIcon = (type: RecommendationType): string => {
  switch (type) {
    case 'index':
      return '🔍';
    case 'sql_rewrite':
      return '✏️';
    case 'optimizer_hint':
      return '💡';
    case 'statistics':
      return '📊';
    case 'parallel':
      return '⚡';
    default:
      return '📝';
  }
};

/**
 * Helper function to format recommendation type.
 */
export const formatRecommendationType = (type: RecommendationType): string => {
  switch (type) {
    case 'index':
      return 'Index';
    case 'sql_rewrite':
      return 'SQL Rewrite';
    case 'optimizer_hint':
      return 'Optimizer Hint';
    case 'statistics':
      return 'Statistics';
    case 'parallel':
      return 'Parallelism';
    default:
      return type;
  }
};

/**
 * Helper function to copy SQL to clipboard.
 */
export const copySQLToClipboard = async (sql?: string): Promise<boolean> => {
  if (!sql) return false;

  try {
    await navigator.clipboard.writeText(sql);
    return true;
  } catch (error) {
    console.error('Failed to copy SQL to clipboard:', error);
    return false;
  }
};

/**
 * Helper function to export recommendations as JSON.
 */
export const exportRecommendationsAsJSON = (recommendations: RecommendationsResponse): string => {
  return JSON.stringify(recommendations, null, 2);
};

/**
 * Helper function to calculate urgency score.
 */
export const calculateUrgencyScore = (
  priority: RecommendationPriority,
  impact: RecommendationImpact
): number => {
  const priorityScores: Record<RecommendationPriority, number> = {
    critical: 100,
    high: 75,
    medium: 50,
    low: 25,
  };

  const impactScores: Record<RecommendationImpact, number> = {
    high: 100,
    medium: 75,
    low: 50,
    minimal: 25,
  };

  return (priorityScores[priority] + impactScores[impact]) / 2;
};

/**
 * Helper function to sort recommendations by urgency.
 */
export const sortByUrgency = (
  recommendations: any[]
): any[] => {
  return [...recommendations].sort((a, b) => {
    const scoreA = calculateUrgencyScore(a.priority, a.estimated_impact);
    const scoreB = calculateUrgencyScore(b.priority, b.estimated_impact);
    return scoreB - scoreA;
  });
};

/**
 * Helper function to filter recommendations.
 */
export const filterRecommendations = (
  recommendations: any[],
  types?: RecommendationType[],
  priorities?: RecommendationPriority[],
  minImpact?: RecommendationImpact
): any[] => {
  let filtered = [...recommendations];

  if (types && types.length > 0) {
    filtered = filtered.filter((rec) => types.includes(rec.type));
  }

  if (priorities && priorities.length > 0) {
    filtered = filtered.filter((rec) => priorities.includes(rec.priority));
  }

  if (minImpact) {
    const impactOrder: Record<RecommendationImpact, number> = {
      high: 3,
      medium: 2,
      low: 1,
      minimal: 0,
    };
    const minScore = impactOrder[minImpact];
    filtered = filtered.filter((rec) => impactOrder[rec.estimated_impact] >= minScore);
  }

  return filtered;
};
