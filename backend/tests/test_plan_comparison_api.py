"""Integration tests for plan comparison API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_comparison_service():
    """Mock PlanComparisonService."""
    with patch("app.api.v1.plan_comparison.PlanComparisonService") as mock:
        yield mock


@pytest.fixture
def sample_comparison_result():
    """Sample comparison result."""
    return {
        "comparison_possible": True,
        "plans_identical": False,
        "current_plan_hash": 12345,
        "historical_plan_hash": 67890,
        "current_metadata": {},
        "historical_metadata": {},
        "current_metrics": {"total_cost": 1000},
        "historical_metrics": {"total_cost": 100},
        "regression_detected": True,
        "regression_analysis": {
            "has_regression": True,
            "regression_count": 2,
            "improvement_count": 0,
            "severity": "high",
            "regressions": [
                {
                    "type": "cost_increase",
                    "severity": "high",
                    "message": "Cost increased significantly",
                }
            ],
            "improvements": [],
        },
        "plan_diff": {
            "operations_added": 1,
            "operations_removed": 0,
            "operations_modified": 1,
            "total_changes": 2,
            "added_details": [],
            "removed_details": [],
            "modified_details": [],
        },
        "operation_changes": [
            {
                "type": "access_method_change",
                "object_name": "EMPLOYEES",
                "historical_method": "INDEX ACCESS",
                "current_method": "TABLE ACCESS FULL",
                "severity": "high",
                "message": "Access method changed",
            }
        ],
        "recommendations": [
            {
                "type": "action_required",
                "priority": "high",
                "message": "Create plan baseline",
                "actions": ["Run baseline SQL"],
            }
        ],
        "comparison_timestamp": "2024-01-01T12:00:00",
    }


@pytest.fixture
def sample_versions():
    """Sample plan versions."""
    return [
        {
            "sql_id": "abc123def4567",
            "plan_hash_value": 12345,
            "first_seen": "2024-01-01T10:00:00",
            "last_seen": "2024-01-01T12:00:00",
            "source": "current",
        },
        {
            "sql_id": "abc123def4567",
            "plan_hash_value": 67890,
            "first_seen": "2023-12-01T10:00:00",
            "last_seen": "2023-12-31T12:00:00",
            "source": "historical",
        },
    ]


class TestPlanComparisonAPI:
    """Test cases for plan comparison API endpoints."""

    def test_get_plan_versions_success(self, mock_comparison_service, sample_versions):
        """Test successful retrieval of plan versions."""
        mock_service = Mock()
        mock_service.get_plan_versions.return_value = sample_versions
        mock_comparison_service.return_value = mock_service

        response = client.get("/api/v1/plan-comparison/abc123def4567/versions?source=both")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_count" in data
        assert data["total_count"] == 2

    def test_get_plan_versions_invalid_sql_id(self):
        """Test plan versions with invalid SQL_ID."""
        response = client.get("/api/v1/plan-comparison/invalid/versions")

        assert response.status_code == 400
        assert "INVALID_SQL_ID" in response.json()["detail"]["code"]

    def test_get_plan_versions_invalid_source(self):
        """Test plan versions with invalid source."""
        response = client.get(
            "/api/v1/plan-comparison/abc123def4567/versions?source=invalid"
        )

        assert response.status_code == 400
        assert "INVALID_SOURCE" in response.json()["detail"]["code"]

    def test_compare_plans_success(
        self, mock_comparison_service, sample_comparison_result
    ):
        """Test successful plan comparison."""
        mock_service = Mock()
        mock_service.compare_plans.return_value = sample_comparison_result
        mock_comparison_service.return_value = mock_service

        response = client.get("/api/v1/plan-comparison/abc123def4567/compare")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["comparison_possible"] is True
        assert data["data"]["regression_detected"] is True

    def test_compare_plans_with_hashes(
        self, mock_comparison_service, sample_comparison_result
    ):
        """Test plan comparison with specific plan hashes."""
        mock_service = Mock()
        mock_service.compare_plans.return_value = sample_comparison_result
        mock_comparison_service.return_value = mock_service

        response = client.get(
            "/api/v1/plan-comparison/abc123def4567/compare"
            "?current_plan_hash=12345&historical_plan_hash=67890"
        )

        assert response.status_code == 200
        mock_service.compare_plans.assert_called_once()

    def test_compare_plans_not_possible(self, mock_comparison_service):
        """Test comparison not possible."""
        mock_service = Mock()
        mock_service.compare_plans.return_value = {
            "comparison_possible": False,
            "reason": "Plans not found",
        }
        mock_comparison_service.return_value = mock_service

        response = client.get("/api/v1/plan-comparison/abc123def4567/compare")

        assert response.status_code == 404
        assert "COMPARISON_NOT_POSSIBLE" in response.json()["detail"]["code"]

    def test_compare_specific_plan(
        self, mock_comparison_service, sample_comparison_result
    ):
        """Test comparison of specific plan version."""
        mock_service = Mock()
        mock_service.compare_plans.return_value = sample_comparison_result
        mock_comparison_service.return_value = mock_service

        response = client.get(
            "/api/v1/plan-comparison/abc123def4567/compare/12345?compare_to=67890"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["comparison_possible"] is True

    def test_get_baseline_recommendation_success(self, mock_comparison_service):
        """Test successful baseline recommendation."""
        mock_service = Mock()
        mock_service.get_baseline_recommendation.return_value = {
            "recommend_baseline": True,
            "priority": "high",
            "reasons": ["Significant regression"],
            "sql_id": "abc123def4567",
            "preferred_plan_hash": 67890,
            "baseline_creation_sql": "BEGIN ... END;",
            "instructions": ["Step 1", "Step 2"],
        }
        mock_comparison_service.return_value = mock_service

        request_body = {
            "sql_id": "abc123def4567",
            "current_plan_hash": 12345,
            "preferred_plan_hash": 67890,
        }

        response = client.post(
            "/api/v1/plan-comparison/abc123def4567/baseline-recommendation",
            json=request_body,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recommend_baseline"] is True
        assert data["priority"] == "high"
        assert "baseline_creation_sql" in data

    def test_get_baseline_recommendation_sql_id_mismatch(self):
        """Test baseline recommendation with mismatched SQL_ID."""
        request_body = {
            "sql_id": "different_id",
            "current_plan_hash": 12345,
            "preferred_plan_hash": 67890,
        }

        response = client.post(
            "/api/v1/plan-comparison/abc123def4567/baseline-recommendation",
            json=request_body,
        )

        assert response.status_code == 400
        assert "SQL_ID_MISMATCH" in response.json()["detail"]["code"]

    def test_get_plan_versions_no_results(self, mock_comparison_service):
        """Test plan versions with no results."""
        mock_service = Mock()
        mock_service.get_plan_versions.return_value = []
        mock_comparison_service.return_value = mock_service

        response = client.get("/api/v1/plan-comparison/abc123def4567/versions")

        assert response.status_code == 404
        assert "NO_PLAN_VERSIONS" in response.json()["detail"]["code"]

    def test_compare_plans_invalid_sql_id(self):
        """Test compare plans with invalid SQL_ID."""
        response = client.get("/api/v1/plan-comparison/invalid/compare")

        assert response.status_code == 400
        assert "INVALID_SQL_ID" in response.json()["detail"]["code"]

    def test_baseline_recommendation_invalid_sql_id(self):
        """Test baseline recommendation with invalid SQL_ID."""
        response = client.get("/api/v1/plan-comparison/invalid/baseline-recommendation")

        # Should be method not allowed since we're using GET instead of POST
        assert response.status_code == 405
