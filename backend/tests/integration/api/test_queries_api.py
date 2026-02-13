"""Integration tests for query API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.core.oracle.connection import OracleConnectionError


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_query_service():
    """Create mock QueryService."""
    with patch("app.api.v1.queries.QueryService") as mock:
        service = Mock()
        mock.return_value = service
        yield service


@pytest.fixture
def sample_queries_response():
    """Sample queries response data."""
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
            "avg_elapsed_time": 5000,
            "avg_cpu_time": 3000,
            "avg_buffer_gets": 50,
            "avg_disk_reads": 1,
            "impact_score": 25.5,
            "needs_tuning": False,
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
            "avg_elapsed_time": 20000,
            "avg_cpu_time": 16000,
            "avg_buffer_gets": 200,
            "avg_disk_reads": 10,
            "impact_score": 75.2,
            "needs_tuning": True,
        },
    ]


class TestQueriesListEndpoint:
    """Tests for GET /api/v1/queries endpoint."""

    def test_get_queries_default(self, client, mock_query_service, sample_queries_response):
        """Test GET /queries with default parameters."""
        mock_query_service.get_queries.return_value = (sample_queries_response, 2)

        response = client.get("/api/v1/queries")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert "filters" in data
        assert "sort" in data
        assert len(data["data"]) == 2
        assert data["pagination"]["total_items"] == 2

    def test_get_queries_with_pagination(self, client, mock_query_service, sample_queries_response):
        """Test GET /queries with pagination parameters."""
        mock_query_service.get_queries.return_value = (sample_queries_response, 2)

        response = client.get("/api/v1/queries?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10

    def test_get_queries_with_filters(self, client, mock_query_service, sample_queries_response):
        """Test GET /queries with filter parameters."""
        mock_query_service.get_queries.return_value = ([sample_queries_response[1]], 1)

        response = client.get(
            "/api/v1/queries?min_elapsed_time=5000000&min_executions=100&schema=APP_USER"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["min_elapsed_time"] == 5000000
        assert data["filters"]["min_executions"] == 100
        assert data["filters"]["schema"] == "APP_USER"

    def test_get_queries_with_text_search(self, client, mock_query_service, sample_queries_response):
        """Test GET /queries with SQL text search."""
        mock_query_service.get_queries.return_value = ([sample_queries_response[0]], 1)

        response = client.get("/api/v1/queries?sql_text_contains=users")

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["sql_text_contains"] == "users"
        assert len(data["data"]) == 1

    def test_get_queries_with_sorting(self, client, mock_query_service, sample_queries_response):
        """Test GET /queries with sorting parameters."""
        mock_query_service.get_queries.return_value = (sample_queries_response, 2)

        response = client.get("/api/v1/queries?sort_by=cpu_time&order=asc")

        assert response.status_code == 200
        data = response.json()
        assert data["sort"]["sort_by"] == "cpu_time"
        assert data["sort"]["order"] == "asc"

    def test_get_queries_invalid_pagination(self, client):
        """Test GET /queries with invalid pagination parameters."""
        response = client.get("/api/v1/queries?page=0&page_size=200")

        assert response.status_code == 422  # Validation error

    def test_get_queries_oracle_error(self, client, mock_query_service):
        """Test GET /queries when Oracle connection fails."""
        mock_query_service.get_queries.side_effect = OracleConnectionError(
            "ORA-12541", "TNS:no listener"
        )

        response = client.get("/api/v1/queries")

        assert response.status_code == 502
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "ORA-12541"

    def test_get_queries_validation_error(self, client, mock_query_service):
        """Test GET /queries with validation error."""
        mock_query_service.get_queries.side_effect = ValueError("Invalid sort field")

        response = client.get("/api/v1/queries")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "VALIDATION_ERROR"

    def test_get_queries_internal_error(self, client, mock_query_service):
        """Test GET /queries with unexpected error."""
        mock_query_service.get_queries.side_effect = Exception("Unexpected error")

        response = client.get("/api/v1/queries")

        assert response.status_code == 500


class TestQueryDetailEndpoint:
    """Tests for GET /api/v1/queries/{sql_id} endpoint."""

    def test_get_query_by_id_found(self, client, mock_query_service):
        """Test GET /queries/{sql_id} when query exists."""
        mock_query_service.get_query_by_id.return_value = {
            "query": {
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
                "avg_elapsed_time": 5000,
                "avg_cpu_time": 3000,
                "avg_buffer_gets": 50,
                "avg_disk_reads": 1,
                "impact_score": 25.5,
                "needs_tuning": False,
            },
            "statistics": {
                "total_queries": 100,
                "total_executions": 50000,
                "total_elapsed_time": 500000000,
                "avg_elapsed_time": 5000000,
            },
        }

        response = client.get("/api/v1/queries/abc123xyz7890")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "statistics" in data
        assert data["data"]["sql_id"] == "abc123xyz7890"

    def test_get_query_by_id_not_found(self, client, mock_query_service):
        """Test GET /queries/{sql_id} when query doesn't exist."""
        mock_query_service.get_query_by_id.return_value = None

        response = client.get("/api/v1/queries/nonexistent123")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "QUERY_NOT_FOUND"
        assert data["detail"]["sql_id"] == "nonexistent123"

    def test_get_query_by_id_invalid_format(self, client):
        """Test GET /queries/{sql_id} with invalid SQL_ID format."""
        # Too short
        response = client.get("/api/v1/queries/abc123")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_SQL_ID"

        # Non-alphanumeric
        response = client.get("/api/v1/queries/abc123xyz789!")
        assert response.status_code == 400

    def test_get_query_by_id_oracle_error(self, client, mock_query_service):
        """Test GET /queries/{sql_id} with Oracle connection error."""
        mock_query_service.get_query_by_id.side_effect = OracleConnectionError(
            "ORA-12541", "TNS:no listener"
        )

        response = client.get("/api/v1/queries/abc123xyz7890")

        assert response.status_code == 502

    def test_get_query_by_id_internal_error(self, client, mock_query_service):
        """Test GET /queries/{sql_id} with unexpected error."""
        mock_query_service.get_query_by_id.side_effect = Exception("Unexpected error")

        response = client.get("/api/v1/queries/abc123xyz7890")

        assert response.status_code == 500


class TestQuerySummaryEndpoint:
    """Tests for GET /api/v1/queries/summary/stats endpoint."""

    def test_get_query_summary(self, client, mock_query_service):
        """Test GET /queries/summary/stats."""
        mock_query_service.get_query_summary.return_value = {
            "total_queries": 150,
            "total_executions": 75000,
            "total_elapsed_time": 750000000,
            "avg_elapsed_time": 5000000,
            "queries_needing_tuning": 25,
        }

        response = client.get("/api/v1/queries/summary/stats")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["total_queries"] == 150
        assert data["data"]["queries_needing_tuning"] == 25

    def test_get_query_summary_oracle_error(self, client, mock_query_service):
        """Test GET /queries/summary/stats with Oracle error."""
        mock_query_service.get_query_summary.side_effect = OracleConnectionError(
            "ORA-12541", "TNS:no listener"
        )

        response = client.get("/api/v1/queries/summary/stats")

        assert response.status_code == 502

    def test_get_query_summary_internal_error(self, client, mock_query_service):
        """Test GET /queries/summary/stats with unexpected error."""
        mock_query_service.get_query_summary.side_effect = Exception("Unexpected error")

        response = client.get("/api/v1/queries/summary/stats")

        assert response.status_code == 500
