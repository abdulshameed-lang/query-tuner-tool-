"""Unit tests for ExecutionPlanService."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from app.services.execution_plan_service import ExecutionPlanService


@pytest.fixture
def mock_connection_manager():
    """Create a mock ConnectionManager."""
    manager = Mock()
    manager.get_connection = MagicMock()
    return manager


@pytest.fixture
def mock_plan_fetcher():
    """Create a mock ExecutionPlanFetcher."""
    fetcher = Mock()
    return fetcher


@pytest.fixture
def sample_plan_operations() -> List[Dict[str, Any]]:
    """Sample plan operations for testing."""
    return [
        {
            "id": 0,
            "parent_id": None,
            "operation": "SELECT STATEMENT",
            "options": None,
            "object_name": None,
            "cost": 100,
            "cardinality": 1000,
            "bytes": 50000,
            "depth": 0,
            "children": [],
        },
        {
            "id": 1,
            "parent_id": 0,
            "operation": "TABLE ACCESS",
            "options": "FULL",
            "object_name": "USERS",
            "cost": 80,
            "cardinality": 10000,
            "bytes": 500000,
            "depth": 1,
            "filter_predicates": "ID > 100",
            "children": [],
        },
        {
            "id": 2,
            "parent_id": 0,
            "operation": "INDEX",
            "options": "RANGE SCAN",
            "object_name": "IDX_USERS",
            "cost": 20,
            "cardinality": 100,
            "bytes": 5000,
            "depth": 1,
            "children": [],
        },
    ]


@pytest.fixture
def execution_plan_service(mock_connection_manager, mock_plan_fetcher):
    """Create ExecutionPlanService with mocked dependencies."""
    with patch(
        "app.services.execution_plan_service.get_connection_manager",
        return_value=mock_connection_manager,
    ):
        with patch(
            "app.services.execution_plan_service.ExecutionPlanFetcher",
            return_value=mock_plan_fetcher,
        ):
            service = ExecutionPlanService()
            service.plan_fetcher = mock_plan_fetcher
            return service


class TestExecutionPlanService:
    """Tests for ExecutionPlanService class."""

    def test_get_execution_plan_success(
        self, execution_plan_service, mock_plan_fetcher, sample_plan_operations
    ):
        """Test get_execution_plan returns plan with analysis."""
        mock_plan_fetcher.fetch_plan_by_sql_id.return_value = sample_plan_operations
        mock_plan_fetcher.build_plan_tree.return_value = sample_plan_operations[0]
        mock_plan_fetcher.get_plan_statistics.return_value = {
            "execution_count": 5,
            "first_seen": "2024-01-01",
            "last_seen": "2024-01-02",
        }

        result = execution_plan_service.get_execution_plan("abc123xyz7890", 12345)

        assert result["sql_id"] == "abc123xyz7890"
        assert "plan_tree" in result
        assert "plan_operations" in result
        assert "analysis" in result
        assert "statistics" in result
        mock_plan_fetcher.fetch_plan_by_sql_id.assert_called_once_with(
            "abc123xyz7890", 12345
        )

    def test_get_execution_plan_not_found(
        self, execution_plan_service, mock_plan_fetcher
    ):
        """Test get_execution_plan returns empty dict when plan not found."""
        mock_plan_fetcher.fetch_plan_by_sql_id.return_value = []

        result = execution_plan_service.get_execution_plan("nonexistent123")

        assert result == {}

    def test_get_plan_history(self, execution_plan_service, mock_plan_fetcher):
        """Test get_plan_history returns plan versions."""
        mock_history = [
            {
                "sql_id": "abc123xyz7890",
                "plan_hash_value": 12345,
                "timestamp": "2024-01-01",
            },
            {
                "sql_id": "abc123xyz7890",
                "plan_hash_value": 67890,
                "timestamp": "2024-01-02",
            },
        ]
        mock_plan_fetcher.fetch_plan_history.return_value = mock_history

        result = execution_plan_service.get_plan_history("abc123xyz7890")

        assert len(result) == 2
        assert result[0]["plan_hash_value"] == 12345
        mock_plan_fetcher.fetch_plan_history.assert_called_once_with("abc123xyz7890")

    def test_analyze_plan_detects_full_table_scans(
        self, execution_plan_service, sample_plan_operations
    ):
        """Test analyze_plan detects full table scans."""
        analysis = execution_plan_service.analyze_plan(
            sample_plan_operations, sample_plan_operations[0]
        )

        # Should detect TABLE ACCESS FULL operation
        assert len(analysis["issues"]) > 0
        full_scan_issue = next(
            (i for i in analysis["issues"] if i["type"] == "full_table_scan"), None
        )
        assert full_scan_issue is not None
        assert full_scan_issue["severity"] == "medium"

    def test_analyze_plan_detects_cartesian_products(self, execution_plan_service):
        """Test analyze_plan detects Cartesian products."""
        ops = [
            {
                "id": 0,
                "operation": "MERGE JOIN CARTESIAN",
                "cost": 1000,
                "cardinality": 100000,
            }
        ]

        analysis = execution_plan_service.analyze_plan(ops, ops[0])

        cartesian_issue = next(
            (i for i in analysis["issues"] if i["type"] == "cartesian_product"), None
        )
        assert cartesian_issue is not None
        assert cartesian_issue["severity"] == "high"

    def test_find_costly_operations(
        self, execution_plan_service, sample_plan_operations
    ):
        """Test _find_costly_operations returns operations sorted by cost."""
        costly = execution_plan_service._find_costly_operations(
            sample_plan_operations, top_n=2
        )

        assert len(costly) == 2
        # Should be sorted by cost descending
        assert costly[0]["cost"] >= costly[1]["cost"]

    def test_detect_full_table_scans(
        self, execution_plan_service, sample_plan_operations
    ):
        """Test _detect_full_table_scans finds TABLE ACCESS FULL."""
        scans = execution_plan_service._detect_full_table_scans(sample_plan_operations)

        assert len(scans) == 1
        assert scans[0]["operation"] == "TABLE ACCESS"
        assert scans[0]["options"] == "FULL"

    def test_detect_full_table_scans_filters_small_tables(
        self, execution_plan_service
    ):
        """Test _detect_full_table_scans filters out small tables."""
        ops = [
            {
                "id": 1,
                "operation": "TABLE ACCESS",
                "options": "FULL",
                "cardinality": 10,  # Small table
            }
        ]

        scans = execution_plan_service._detect_full_table_scans(ops)

        assert len(scans) == 0  # Should be filtered out

    def test_detect_cartesian_products(self, execution_plan_service):
        """Test _detect_cartesian_products finds Cartesian operations."""
        ops = [
            {"id": 1, "operation": "MERGE JOIN CARTESIAN", "cost": 1000},
            {"id": 2, "operation": "CARTESIAN", "cost": 500},
            {"id": 3, "operation": "HASH JOIN", "cost": 100},
        ]

        cartesians = execution_plan_service._detect_cartesian_products(ops)

        assert len(cartesians) == 2
        assert all("CARTESIAN" in op["operation"] for op in cartesians)

    def test_detect_missing_indexes(self, execution_plan_service):
        """Test _detect_missing_indexes provides recommendations."""
        ops = [
            {
                "id": 1,
                "operation": "TABLE ACCESS",
                "options": "FULL",
                "object_name": "USERS",
                "filter_predicates": "ID > 100",
            }
        ]

        recommendations = execution_plan_service._detect_missing_indexes(ops)

        assert len(recommendations) > 0
        assert any(
            rec["type"] == "missing_index" for rec in recommendations
        )

    def test_detect_high_cardinality_operations(self, execution_plan_service):
        """Test _detect_high_cardinality_operations finds high-cardinality ops."""
        ops = [
            {"id": 1, "operation": "TABLE ACCESS", "cardinality": 200000},
            {"id": 2, "operation": "INDEX SCAN", "cardinality": 100},
        ]

        high_card = execution_plan_service._detect_high_cardinality_operations(
            ops, threshold=100000
        )

        assert len(high_card) == 1
        assert high_card[0]["id"] == 1

    def test_calculate_plan_metrics(
        self, execution_plan_service, sample_plan_operations
    ):
        """Test _calculate_plan_metrics computes correct metrics."""
        metrics = execution_plan_service._calculate_plan_metrics(
            sample_plan_operations, sample_plan_operations[0]
        )

        assert "total_cost" in metrics
        assert "total_cardinality" in metrics
        assert "operation_count" in metrics
        assert "operation_types" in metrics
        assert "complexity" in metrics
        assert "max_depth" in metrics

        assert metrics["operation_count"] == 3
        assert metrics["total_cost"] == 200  # Sum of all costs
        assert metrics["max_depth"] == 1

    def test_export_plan_text(
        self, execution_plan_service, mock_plan_fetcher, sample_plan_operations
    ):
        """Test export_plan_text returns formatted text."""
        mock_plan_fetcher.fetch_plan_by_sql_id.return_value = sample_plan_operations
        mock_plan_fetcher.format_plan_text.return_value = "Formatted plan text"

        result = execution_plan_service.export_plan_text("abc123xyz7890")

        assert result == "Formatted plan text"
        mock_plan_fetcher.format_plan_text.assert_called_once_with(
            sample_plan_operations
        )

    def test_export_plan_text_not_found(
        self, execution_plan_service, mock_plan_fetcher
    ):
        """Test export_plan_text returns message when plan not found."""
        mock_plan_fetcher.fetch_plan_by_sql_id.return_value = []

        result = execution_plan_service.export_plan_text("nonexistent123")

        assert "No execution plan found" in result
