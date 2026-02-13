"""Integration tests for execution plan API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.oracle.connection import OracleConnectionError


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_execution_plan_service():
    """Create mock ExecutionPlanService."""
    with patch("app.api.v1.execution_plans.ExecutionPlanService") as mock:
        service = Mock()
        mock.return_value = service
        yield service


@pytest.fixture
def sample_execution_plan():
    """Sample execution plan data."""
    return {
        "sql_id": "abc123xyz7890",
        "plan_hash_value": 12345,
        "plan_tree": {
            "id": 0,
            "operation": "SELECT STATEMENT",
            "cost": 100,
            "cardinality": 1000,
            "bytes": 50000,
            "children": [],
        },
        "plan_operations": [
            {
                "id": 0,
                "operation": "SELECT STATEMENT",
                "cost": 100,
                "cardinality": 1000,
                "bytes": 50000,
            }
        ],
        "analysis": {
            "issues": [],
            "recommendations": [],
            "costly_operations": [],
            "metrics": {
                "total_cost": 100,
                "total_cardinality": 1000,
                "total_bytes": 50000,
                "operation_count": 1,
                "operation_types": {"SELECT STATEMENT": 1},
                "complexity": 1,
                "max_depth": 0,
                "parallel_operations": 0,
            },
        },
        "statistics": {
            "execution_count": 5,
            "first_seen": "2024-01-01",
            "last_seen": "2024-01-02",
        },
    }


class TestExecutionPlanEndpoint:
    """Tests for GET /api/v1/execution-plans/{sql_id} endpoint."""

    def test_get_execution_plan_success(
        self, client, mock_execution_plan_service, sample_execution_plan
    ):
        """Test GET /execution-plans/{sql_id} returns plan successfully."""
        mock_execution_plan_service.get_execution_plan.return_value = (
            sample_execution_plan
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["sql_id"] == "abc123xyz7890"
        assert data["data"]["plan_hash_value"] == 12345

    def test_get_execution_plan_with_plan_hash_value(
        self, client, mock_execution_plan_service, sample_execution_plan
    ):
        """Test GET /execution-plans/{sql_id} with plan_hash_value parameter."""
        mock_execution_plan_service.get_execution_plan.return_value = (
            sample_execution_plan
        )

        response = client.get(
            "/api/v1/execution-plans/abc123xyz7890?plan_hash_value=12345"
        )

        assert response.status_code == 200
        mock_execution_plan_service.get_execution_plan.assert_called_once_with(
            "ABC123XYZ7890", 12345
        )

    def test_get_execution_plan_not_found(
        self, client, mock_execution_plan_service
    ):
        """Test GET /execution-plans/{sql_id} when plan not found."""
        mock_execution_plan_service.get_execution_plan.return_value = {}

        response = client.get("/api/v1/execution-plans/nonexistent123")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PLAN_NOT_FOUND"

    def test_get_execution_plan_invalid_sql_id(self, client):
        """Test GET /execution-plans/{sql_id} with invalid SQL_ID."""
        # Too short
        response = client.get("/api/v1/execution-plans/abc123")
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_SQL_ID"

        # Non-alphanumeric
        response = client.get("/api/v1/execution-plans/abc123xyz789!")
        assert response.status_code == 400

    def test_get_execution_plan_oracle_error(
        self, client, mock_execution_plan_service
    ):
        """Test GET /execution-plans/{sql_id} with Oracle connection error."""
        mock_execution_plan_service.get_execution_plan.side_effect = (
            OracleConnectionError("ORA-12541", "TNS:no listener")
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890")

        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["code"] == "ORA-12541"


class TestPlanHistoryEndpoint:
    """Tests for GET /api/v1/execution-plans/{sql_id}/history endpoint."""

    def test_get_plan_history_success(self, client, mock_execution_plan_service):
        """Test GET /execution-plans/{sql_id}/history returns plan versions."""
        mock_history = [
            {
                "sql_id": "abc123xyz7890",
                "plan_hash_value": 12345,
                "timestamp": "2024-01-01",
                "child_number": 0,
            },
            {
                "sql_id": "abc123xyz7890",
                "plan_hash_value": 67890,
                "timestamp": "2024-01-02",
                "child_number": 1,
            },
        ]
        mock_execution_plan_service.get_plan_history.return_value = mock_history

        response = client.get("/api/v1/execution-plans/abc123xyz7890/history")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_count" in data
        assert len(data["data"]) == 2
        assert data["total_count"] == 2

    def test_get_plan_history_empty(self, client, mock_execution_plan_service):
        """Test GET /execution-plans/{sql_id}/history with no history."""
        mock_execution_plan_service.get_plan_history.return_value = []

        response = client.get("/api/v1/execution-plans/abc123xyz7890/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["total_count"] == 0

    def test_get_plan_history_invalid_sql_id(self, client):
        """Test GET /execution-plans/{sql_id}/history with invalid SQL_ID."""
        response = client.get("/api/v1/execution-plans/invalid/history")

        assert response.status_code == 400

    def test_get_plan_history_oracle_error(
        self, client, mock_execution_plan_service
    ):
        """Test GET /execution-plans/{sql_id}/history with Oracle error."""
        mock_execution_plan_service.get_plan_history.side_effect = (
            OracleConnectionError("ORA-12541", "TNS:no listener")
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890/history")

        assert response.status_code == 502


class TestPlanExportEndpoint:
    """Tests for GET /api/v1/execution-plans/{sql_id}/export endpoint."""

    def test_export_plan_text_format(self, client, mock_execution_plan_service):
        """Test GET /execution-plans/{sql_id}/export with text format."""
        mock_execution_plan_service.export_plan_text.return_value = (
            "Formatted plan text"
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890/export?format=text")

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "text"
        assert data["content"] == "Formatted plan text"

    def test_export_plan_json_format(
        self, client, mock_execution_plan_service, sample_execution_plan
    ):
        """Test GET /execution-plans/{sql_id}/export with JSON format."""
        mock_execution_plan_service.get_execution_plan.return_value = (
            sample_execution_plan
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890/export?format=json")

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert "content" in data
        # Content should be JSON string
        import json
        parsed = json.loads(data["content"])
        assert parsed["sql_id"] == "abc123xyz7890"

    def test_export_plan_xml_format(
        self, client, mock_execution_plan_service, sample_execution_plan
    ):
        """Test GET /execution-plans/{sql_id}/export with XML format."""
        mock_execution_plan_service.get_execution_plan.return_value = (
            sample_execution_plan
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890/export?format=xml")

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "xml"
        assert "<?xml version" in data["content"]

    def test_export_plan_default_format(self, client, mock_execution_plan_service):
        """Test GET /execution-plans/{sql_id}/export with default format."""
        mock_execution_plan_service.export_plan_text.return_value = "Plan text"

        response = client.get("/api/v1/execution-plans/abc123xyz7890/export")

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "text"  # Default format

    def test_export_plan_invalid_format(self, client):
        """Test GET /execution-plans/{sql_id}/export with invalid format."""
        response = client.get("/api/v1/execution-plans/abc123xyz7890/export?format=pdf")

        assert response.status_code == 422  # Validation error

    def test_export_plan_not_found(self, client, mock_execution_plan_service):
        """Test GET /execution-plans/{sql_id}/export when plan not found."""
        mock_execution_plan_service.get_execution_plan.return_value = {}

        response = client.get("/api/v1/execution-plans/abc123xyz7890/export?format=json")

        assert response.status_code == 404

    def test_export_plan_oracle_error(self, client, mock_execution_plan_service):
        """Test GET /execution-plans/{sql_id}/export with Oracle error."""
        mock_execution_plan_service.export_plan_text.side_effect = (
            OracleConnectionError("ORA-12541", "TNS:no listener")
        )

        response = client.get("/api/v1/execution-plans/abc123xyz7890/export?format=text")

        assert response.status_code == 502
