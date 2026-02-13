"""Unit tests for QueryService."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from app.services.query_service import QueryService
from app.schemas.query import QueryFilters, QuerySort, PaginationParams


@pytest.fixture
def mock_connection_manager():
    """Create a mock ConnectionManager."""
    manager = Mock()
    manager.get_connection = MagicMock()
    return manager


@pytest.fixture
def mock_query_fetcher():
    """Create a mock QueryFetcher."""
    fetcher = Mock()
    return fetcher


@pytest.fixture
def sample_queries() -> List[Dict[str, Any]]:
    """Sample query data for testing."""
    return [
        {
            "sql_id": "abc123xyz7890",
            "sql_text": "SELECT * FROM users WHERE id = :1",
            "parsing_schema_name": "APP_USER",
            "executions": 1000,
            "elapsed_time": 5000000,
            "cpu_time": 3000000,
            "buffer_gets": 50000,
            "disk_reads": 1000,
            "rows_processed": 1000,
            "fetches": 1000,
            "first_load_time": "2024-01-01 10:00:00",
            "last_active_time": "2024-01-02 15:30:00",
        },
        {
            "sql_id": "def456uvw1234",
            "sql_text": "SELECT * FROM orders WHERE status = 'PENDING'",
            "parsing_schema_name": "APP_USER",
            "executions": 500,
            "elapsed_time": 10000000,
            "cpu_time": 8000000,
            "buffer_gets": 100000,
            "disk_reads": 5000,
            "rows_processed": 5000,
            "fetches": 500,
            "first_load_time": "2024-01-01 11:00:00",
            "last_active_time": "2024-01-02 16:00:00",
        },
        {
            "sql_id": "ghi789rst4567",
            "sql_text": "UPDATE products SET price = :1 WHERE id = :2",
            "parsing_schema_name": "ADMIN",
            "executions": 100,
            "elapsed_time": 2000000,
            "cpu_time": 1500000,
            "buffer_gets": 20000,
            "disk_reads": 500,
            "rows_processed": 100,
            "fetches": 0,
            "first_load_time": "2024-01-01 12:00:00",
            "last_active_time": "2024-01-02 14:00:00",
        },
    ]


@pytest.fixture
def query_service(mock_connection_manager, mock_query_fetcher):
    """Create QueryService with mocked dependencies."""
    with patch("app.services.query_service.get_connection_manager", return_value=mock_connection_manager):
        with patch("app.services.query_service.QueryFetcher", return_value=mock_query_fetcher):
            service = QueryService()
            service.query_fetcher = mock_query_fetcher
            return service


class TestQueryService:
    """Tests for QueryService class."""

    def test_get_queries_default_params(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_queries with default parameters."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        results, total_count = query_service.get_queries()

        assert total_count == 3
        assert len(results) == 3
        assert all("impact_score" in q for q in results)
        assert all("needs_tuning" in q for q in results)
        mock_query_fetcher.fetch_top_queries.assert_called_once()

    def test_get_queries_with_filters(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_queries with filters applied."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        filters = QueryFilters(
            schema="APP_USER",
            min_executions=200,
        )

        results, total_count = query_service.get_queries(filters=filters)

        # Should filter to only APP_USER queries with executions >= 200
        assert total_count == 2
        assert all(q["parsing_schema_name"] == "APP_USER" for q in results)
        assert all(q["executions"] >= 200 for q in results)

    def test_get_queries_with_sql_text_search(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_queries with SQL text search filter."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        filters = QueryFilters(sql_text_contains="SELECT")

        results, total_count = query_service.get_queries(filters=filters)

        # Should only return SELECT queries
        assert total_count == 2
        assert all("SELECT" in q["sql_text"] for q in results)

    def test_get_queries_with_sorting(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_queries with custom sorting."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        sort = QuerySort(sort_by="executions", order="desc")

        results, total_count = query_service.get_queries(sort=sort)

        # Should be sorted by executions descending
        assert results[0]["sql_id"] == "abc123xyz7890"  # 1000 executions
        assert results[1]["sql_id"] == "def456uvw1234"  # 500 executions
        assert results[2]["sql_id"] == "ghi789rst4567"  # 100 executions

    def test_get_queries_with_pagination(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_queries with pagination."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        pagination = PaginationParams(page=1, page_size=2)

        results, total_count = query_service.get_queries(pagination=pagination)

        assert total_count == 3
        assert len(results) == 2  # Only 2 results per page

    def test_get_queries_second_page(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_queries pagination on second page."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        pagination = PaginationParams(page=2, page_size=2)

        results, total_count = query_service.get_queries(pagination=pagination)

        assert total_count == 3
        assert len(results) == 1  # Only 1 result on page 2

    def test_get_query_by_id_found(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_query_by_id when query exists."""
        mock_query_fetcher.fetch_query_by_sql_id.return_value = sample_queries[0]
        mock_query_fetcher.get_query_statistics.return_value = {
            "total_queries": 100,
            "total_executions": 50000,
        }

        result = query_service.get_query_by_id("abc123xyz7890")

        assert result is not None
        assert "query" in result
        assert "statistics" in result
        assert result["query"]["sql_id"] == "abc123xyz7890"
        assert "impact_score" in result["query"]

    def test_get_query_by_id_not_found(self, query_service, mock_query_fetcher):
        """Test get_query_by_id when query doesn't exist."""
        mock_query_fetcher.fetch_query_by_sql_id.return_value = None

        result = query_service.get_query_by_id("nonexistent123")

        assert result is None

    def test_calculate_impact_score(self, query_service, sample_queries):
        """Test impact score calculation."""
        query = sample_queries[0].copy()

        result = query_service._calculate_impact_score(query)

        assert "impact_score" in result
        assert "needs_tuning" in result
        assert isinstance(result["impact_score"], float)
        assert isinstance(result["needs_tuning"], bool)
        assert result["impact_score"] >= 0

    def test_calculate_impact_score_high_values(self, query_service):
        """Test impact score with high resource usage."""
        query = {
            "elapsed_time": 10000000000,  # 10 seconds
            "cpu_time": 8000000000,
            "buffer_gets": 10000000,
            "disk_reads": 1000000,
        }

        result = query_service._calculate_impact_score(query)

        # High resource usage should result in high impact score
        assert result["impact_score"] > 50
        assert result["needs_tuning"] is True

    def test_calculate_impact_score_low_values(self, query_service):
        """Test impact score with low resource usage."""
        query = {
            "elapsed_time": 100000,  # 0.1ms
            "cpu_time": 50000,
            "buffer_gets": 100,
            "disk_reads": 10,
        }

        result = query_service._calculate_impact_score(query)

        # Low resource usage should result in low impact score
        assert result["impact_score"] < 10
        assert result["needs_tuning"] is False

    def test_calculate_impact_score_missing_values(self, query_service):
        """Test impact score calculation with missing values."""
        query = {"sql_id": "test123"}

        result = query_service._calculate_impact_score(query)

        # Should handle missing values gracefully
        assert result["impact_score"] == 0
        assert result["needs_tuning"] is False

    def test_get_query_summary(self, query_service, mock_query_fetcher, sample_queries):
        """Test get_query_summary."""
        mock_query_fetcher.fetch_top_queries.return_value = sample_queries.copy()

        summary = query_service.get_query_summary()

        assert "total_queries" in summary
        assert "total_executions" in summary
        assert "total_elapsed_time" in summary
        assert "avg_elapsed_time" in summary
        assert "queries_needing_tuning" in summary

        assert summary["total_queries"] == 3
        assert summary["total_executions"] == 1600  # Sum of all executions
        assert summary["total_elapsed_time"] == 17000000  # Sum of elapsed times

    def test_get_query_summary_empty(self, query_service, mock_query_fetcher):
        """Test get_query_summary with no queries."""
        mock_query_fetcher.fetch_top_queries.return_value = []

        summary = query_service.get_query_summary()

        assert summary["total_queries"] == 0
        assert summary["total_executions"] == 0
        assert summary["total_elapsed_time"] == 0
        assert summary["avg_elapsed_time"] == 0
        assert summary["queries_needing_tuning"] == 0
