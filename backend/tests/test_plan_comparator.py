"""Unit tests for plan comparator module."""

import pytest
from app.core.analysis.plan_comparator import PlanComparator


@pytest.fixture
def comparator():
    """Create PlanComparator instance."""
    return PlanComparator()


@pytest.fixture
def sample_current_plan():
    """Sample current plan with higher cost."""
    return [
        {
            "id": 0,
            "parent_id": None,
            "operation": "SELECT STATEMENT",
            "options": None,
            "object_name": None,
            "plan_hash_value": 12345,
            "cost": 1000,
            "cardinality": 10000,
            "cpu_cost": 500,
            "io_cost": 400,
            "depth": 0,
        },
        {
            "id": 1,
            "parent_id": 0,
            "operation": "TABLE ACCESS",
            "options": "FULL",
            "object_name": "EMPLOYEES",
            "plan_hash_value": 12345,
            "cost": 800,
            "cardinality": 10000,
            "depth": 1,
        },
    ]


@pytest.fixture
def sample_historical_plan():
    """Sample historical plan with lower cost."""
    return [
        {
            "id": 0,
            "parent_id": None,
            "operation": "SELECT STATEMENT",
            "options": None,
            "object_name": None,
            "plan_hash_value": 67890,
            "cost": 100,
            "cardinality": 1000,
            "cpu_cost": 50,
            "io_cost": 40,
            "depth": 0,
        },
        {
            "id": 1,
            "parent_id": 0,
            "operation": "TABLE ACCESS",
            "options": "BY INDEX ROWID",
            "object_name": "EMPLOYEES",
            "plan_hash_value": 67890,
            "cost": 80,
            "cardinality": 1000,
            "depth": 1,
        },
    ]


class TestPlanComparator:
    """Test cases for PlanComparator class."""

    def test_compare_plans_detects_regression(
        self, comparator, sample_current_plan, sample_historical_plan
    ):
        """Test that compare_plans detects cost regression."""
        result = comparator.compare_plans(sample_current_plan, sample_historical_plan)

        assert result["comparison_possible"] is True
        assert result["regression_detected"] is True
        assert result["regression_analysis"]["has_regression"] is True
        assert result["regression_analysis"]["regression_count"] > 0

    def test_compare_plans_with_empty_plans(self, comparator):
        """Test comparison with empty plans."""
        result = comparator.compare_plans([], [])

        assert result["comparison_possible"] is False
        assert "empty" in result["reason"].lower()

    def test_detect_regression_cost_increase(
        self, comparator, sample_current_plan, sample_historical_plan
    ):
        """Test detection of cost regression."""
        current_metrics = comparator._calculate_plan_metrics(sample_current_plan)
        historical_metrics = comparator._calculate_plan_metrics(sample_historical_plan)

        regression = comparator.detect_regression(current_metrics, historical_metrics)

        assert regression["has_regression"] is True
        assert any(r["type"] == "cost_increase" for r in regression["regressions"])

    def test_detect_regression_cardinality_error(self, comparator):
        """Test detection of cardinality estimation error."""
        current_metrics = {"total_cost": 100, "total_cardinality": 100000, "total_cpu_cost": 50, "total_io_cost": 40}
        historical_metrics = {"total_cost": 100, "total_cardinality": 1000, "total_cpu_cost": 50, "total_io_cost": 40}

        regression = comparator.detect_regression(current_metrics, historical_metrics)

        assert regression["has_regression"] is True
        assert any(
            "cardinality" in r["type"].lower() for r in regression["regressions"]
        )

    def test_calculate_plan_diff(
        self, comparator, sample_current_plan, sample_historical_plan
    ):
        """Test calculation of plan differences."""
        diff = comparator.calculate_plan_diff(sample_current_plan, sample_historical_plan)

        assert diff is not None
        assert "operations_added" in diff
        assert "operations_removed" in diff
        assert "operations_modified" in diff
        assert "total_changes" in diff

    def test_identify_operation_changes(
        self, comparator, sample_current_plan, sample_historical_plan
    ):
        """Test identification of operation changes."""
        changes = comparator.identify_operation_changes(
            sample_current_plan, sample_historical_plan
        )

        assert isinstance(changes, list)
        # Should detect access method change (INDEX -> FULL)
        access_method_changes = [c for c in changes if c["type"] == "access_method_change"]
        assert len(access_method_changes) > 0

    def test_recommend_plan_baseline_high_regression(
        self, comparator, sample_current_plan, sample_historical_plan
    ):
        """Test baseline recommendation for high regression."""
        comparison = comparator.compare_plans(sample_current_plan, sample_historical_plan)
        recommendation = comparator.recommend_plan_baseline(comparison, "test_sql_id")

        assert recommendation is not None
        assert "recommend_baseline" in recommendation
        if recommendation["recommend_baseline"]:
            assert "baseline_creation_sql" in recommendation
            assert "instructions" in recommendation

    def test_calculate_plan_metrics(self, comparator, sample_current_plan):
        """Test calculation of plan metrics."""
        metrics = comparator._calculate_plan_metrics(sample_current_plan)

        assert metrics["total_cost"] == 1000  # Root cost
        assert metrics["operation_count"] == 2
        assert metrics["max_depth"] == 1
        assert metrics["plan_hash_value"] == 12345

    def test_determine_overall_severity(self, comparator):
        """Test severity determination."""
        high_regressions = [{"severity": "high"}, {"severity": "medium"}]
        assert comparator._determine_overall_severity(high_regressions) == "high"

        medium_regressions = [{"severity": "medium"}, {"severity": "low"}]
        assert comparator._determine_overall_severity(medium_regressions) == "medium"

        low_regressions = [{"severity": "low"}]
        assert comparator._determine_overall_severity(low_regressions) == "low"

        no_regressions = []
        assert comparator._determine_overall_severity(no_regressions) == "none"

    def test_access_method_change_severity(self, comparator):
        """Test access method change severity assessment."""
        # INDEX to FULL is high severity
        severity1 = comparator._assess_access_change_severity(
            "INDEX ACCESS", "TABLE ACCESS FULL"
        )
        assert severity1 == "high"

        # FULL to INDEX is low severity (improvement)
        severity2 = comparator._assess_access_change_severity(
            "TABLE ACCESS FULL", "INDEX ACCESS"
        )
        assert severity2 == "low"

        # Other changes are medium severity
        severity3 = comparator._assess_access_change_severity(
            "INDEX RANGE SCAN", "INDEX UNIQUE SCAN"
        )
        assert severity3 == "medium"

    def test_generate_baseline_sql(self, comparator):
        """Test generation of baseline SQL."""
        sql = comparator._generate_baseline_sql("abc123def4567", 12345, 67890)

        assert "abc123def4567" in sql
        assert "12345" in sql
        assert "DBMS_SPM.LOAD_PLANS_FROM_CURSOR_CACHE" in sql
        assert "dba_sql_plan_baselines" in sql.lower()

    def test_plans_identical(self, comparator):
        """Test comparison of identical plans."""
        plan = [
            {
                "id": 0,
                "plan_hash_value": 12345,
                "operation": "SELECT STATEMENT",
                "cost": 100,
                "cardinality": 1000,
            }
        ]

        result = comparator.compare_plans(plan, plan)

        assert result["comparison_possible"] is True
        assert result["plans_identical"] is True

    def test_group_operations_by_object(self, comparator, sample_current_plan):
        """Test grouping operations by object name."""
        grouped = comparator._group_operations_by_object(sample_current_plan)

        assert "EMPLOYEES" in grouped
        assert len(grouped["EMPLOYEES"]) == 1

    def test_get_access_method(self, comparator):
        """Test access method extraction."""
        op1 = {"operation": "TABLE ACCESS", "options": "FULL"}
        assert comparator._get_access_method(op1) == "TABLE ACCESS FULL"

        op2 = {"operation": "TABLE ACCESS", "options": "BY INDEX ROWID"}
        assert comparator._get_access_method(op2) == "INDEX ACCESS"

        op3 = {"operation": "INDEX", "options": "RANGE SCAN"}
        assert comparator._get_access_method(op3) == "INDEX RANGE SCAN"
