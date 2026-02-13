/**
 * Unit tests for QueryList component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import QueryList from '../QueryList';
import * as queriesApi from '../../../api/queries';
import { QueryListResponse } from '../../../types/query';

// Mock the API module
vi.mock('../../../api/queries', () => ({
  useQueries: vi.fn(),
  formatElapsedTime: (microseconds: number) => `${microseconds} μs`,
  formatNumber: (num: number) => num.toString(),
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockQueryListResponse: QueryListResponse = {
  data: [
    {
      sql_id: 'abc123xyz7890',
      sql_text: 'SELECT * FROM users WHERE id = :1',
      parsing_schema_name: 'APP_USER',
      executions: 1000,
      elapsed_time: 5000000,
      cpu_time: 3000000,
      buffer_gets: 50000,
      disk_reads: 1000,
      rows_processed: 1000,
      fetches: 1000,
      first_load_time: '2024-01-01 10:00:00',
      last_active_time: '2024-01-02 15:30:00',
      avg_elapsed_time: 5000,
      avg_cpu_time: 3000,
      avg_buffer_gets: 50,
      avg_disk_reads: 1,
      impact_score: 25.5,
      needs_tuning: false,
    },
    {
      sql_id: 'def456uvw1234',
      sql_text: "SELECT * FROM orders WHERE status = 'PENDING'",
      parsing_schema_name: 'APP_USER',
      executions: 500,
      elapsed_time: 10000000,
      cpu_time: 8000000,
      buffer_gets: 100000,
      disk_reads: 5000,
      rows_processed: 5000,
      fetches: 500,
      first_load_time: '2024-01-01 11:00:00',
      last_active_time: '2024-01-02 16:00:00',
      avg_elapsed_time: 20000,
      avg_cpu_time: 16000,
      avg_buffer_gets: 200,
      avg_disk_reads: 10,
      impact_score: 75.2,
      needs_tuning: true,
    },
  ],
  pagination: {
    page: 1,
    page_size: 20,
    total_items: 2,
    total_pages: 1,
    has_next: false,
    has_previous: false,
  },
  filters: {
    exclude_system_schemas: true,
  },
  sort: {
    sort_by: 'elapsed_time',
    order: 'desc',
  },
};

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createQueryClient();
  return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
};

describe('QueryList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    expect(screen.getByText('SQL Queries')).toBeInTheDocument();
  });

  it('renders query list successfully', async () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    await waitFor(() => {
      expect(screen.getByText('abc123xyz7890')).toBeInTheDocument();
      expect(screen.getByText('def456uvw1234')).toBeInTheDocument();
    });

    // Check if table headers are present
    expect(screen.getByText('SQL ID')).toBeInTheDocument();
    expect(screen.getByText('Schema')).toBeInTheDocument();
    expect(screen.getByText('Executions')).toBeInTheDocument();
    expect(screen.getByText('Impact Score')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const mockError = {
      response: {
        data: {
          message: 'Database connection failed',
        },
      },
    };

    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: mockError,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    expect(screen.getByText('Error Loading Queries')).toBeInTheDocument();
    expect(screen.getByText(/Database connection failed/)).toBeInTheDocument();
  });

  it('displays TUNE tag for queries needing tuning', async () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    await waitFor(() => {
      const tuneTags = screen.getAllByText('TUNE');
      // Only the second query needs tuning
      expect(tuneTags.length).toBe(1);
    });
  });

  it('calls onQueryClick when row is clicked', async () => {
    const mockOnQueryClick = vi.fn();

    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList onQueryClick={mockOnQueryClick} />);

    await waitFor(() => {
      expect(screen.getByText('abc123xyz7890')).toBeInTheDocument();
    });

    // Find the table row and click it
    const table = screen.getByRole('table');
    const rows = within(table).getAllByRole('row');
    // Skip header row, click first data row
    fireEvent.click(rows[1]);

    expect(mockOnQueryClick).toHaveBeenCalledWith('abc123xyz7890');
  });

  it('calls refetch when refresh button is clicked', async () => {
    const mockRefetch = vi.fn();

    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    } as any);

    renderWithQueryClient(<QueryList />);

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('displays pagination information', async () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    await waitFor(() => {
      expect(screen.getByText(/Showing 2 queries/)).toBeInTheDocument();
      expect(screen.getByText(/page 1 of 1/)).toBeInTheDocument();
    });
  });

  it('renders search input', () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    const searchInput = screen.getByPlaceholderText('Search SQL text');
    expect(searchInput).toBeInTheDocument();
  });

  it('renders filter inputs', () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    expect(screen.getByPlaceholderText('Min elapsed time (μs)')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Min executions')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Schema name')).toBeInTheDocument();
  });

  it('displays correct impact scores', async () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    await waitFor(() => {
      expect(screen.getByText('25.50')).toBeInTheDocument();
      expect(screen.getByText('75.20')).toBeInTheDocument();
    });
  });

  it('displays query schemas', async () => {
    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: mockQueryListResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    await waitFor(() => {
      const schemaTexts = screen.getAllByText('APP_USER');
      // Should appear twice (once for each query)
      expect(schemaTexts.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('handles empty query list', () => {
    const emptyResponse: QueryListResponse = {
      ...mockQueryListResponse,
      data: [],
      pagination: {
        ...mockQueryListResponse.pagination,
        total_items: 0,
        total_pages: 0,
      },
    };

    vi.mocked(queriesApi.useQueries).mockReturnValue({
      data: emptyResponse,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWithQueryClient(<QueryList />);

    expect(screen.getByText(/Showing 0 queries/)).toBeInTheDocument();
  });
});
