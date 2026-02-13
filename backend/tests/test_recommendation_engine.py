"""Unit tests for recommendation engine."""

import pytest
from app.core.analysis.recommendation_engine import RecommendationEngine


@pytest.fixture
def engine():
    """Create RecommendationEngine instance."""
    return RecommendationEngine()


@pytest.fixture
def sample_plan_with_full_scan():
    """Sample plan with full table scan."""
    return [
        {
            "id": 0,
            "operation": "SELECT STATEMENT",
            "options": None,
            "object_name": None,
            "cost": 1000,
            "cardinality": 50000,
        },
        {
            "id": 1,
            "operation": "TABLE ACCESS",
            "options": "FULL",
            "object_name": "EMPLOYEES",
            "object_type": "TABLE",
            "cost": 900,
            "cardinality": 50000,
            "filter_predicates": '"EMPLOYEES"."DEPARTMENT_ID"=:B1',
        },
    ]


@pytest.fixture
def sample_plan_with_nested_loops():
    """Sample plan with nested loops join."""
    return [
        {
            "id": 0,
            "operation": "SELECT STATEMENT",
            "options": None,
            "object_name": None,
            "cost": 500,
            "cardinality": 20000,
        },
        {
            "id": 1,
            "operation": "NESTED LOOPS",
            "options": None,
            "object_name": None,
            "cost": 400,
            "cardinality": 20000,
        },
    ]


class TestRecommendationEngine:
    """Test cases for RecommendationEngine class."""

    def test_analyze_detects_full_table_scan(
        self, engine, sample_plan_with_full_scan
    ):
        """Test detection of full table scan requiring index."""
        sql_text = "SELECT * FROM employees WHERE department_id = :B1"

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=sample_plan_with_full_scan,
        )

        # Should have index recommendation
        index_recs = [r for r in recommendations if r["type"] == engine.TYPE_INDEX]
        assert len(index_recs) > 0
        assert index_recs[0]["table"] == "EMPLOYEES"
        assert "DEPARTMENT_ID" in index_recs[0]["columns"]

    def test_analyze_detects_or_conditions(self, engine):
        """Test detection of OR conditions for UNION rewrite."""
        sql_text = "SELECT * FROM employees WHERE dept_id = 10 OR dept_id = 20 OR dept_id = 30"
        plan_operations = []

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should have SQL rewrite recommendation
        rewrite_recs = [r for r in recommendations if r["type"] == engine.TYPE_SQL_REWRITE]
        or_rewrite = [r for r in rewrite_recs if r["subtype"] == "or_to_union"]
        assert len(or_rewrite) > 0

    def test_analyze_detects_not_in(self, engine):
        """Test detection of NOT IN for NOT EXISTS rewrite."""
        sql_text = "SELECT * FROM employees WHERE emp_id NOT IN (SELECT mgr_id FROM managers)"
        plan_operations = []

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should have NOT IN rewrite recommendation
        rewrite_recs = [r for r in recommendations if r["type"] == engine.TYPE_SQL_REWRITE]
        not_in_recs = [r for r in rewrite_recs if r["subtype"] == "not_in_to_not_exists"]
        assert len(not_in_recs) > 0

    def test_analyze_detects_select_star(self, engine):
        """Test detection of SELECT * usage."""
        sql_text = "SELECT * FROM employees"
        plan_operations = []

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should have SELECT * recommendation
        select_star_recs = [
            r for r in recommendations
            if r.get("subtype") == "select_star"
        ]
        assert len(select_star_recs) > 0

    def test_analyze_detects_scalar_subquery(self, engine):
        """Test detection of scalar subqueries."""
        sql_text = "SELECT emp_id, (SELECT dept_name FROM departments d WHERE d.dept_id = e.dept_id) FROM employees e"
        plan_operations = []

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should have scalar subquery recommendation
        scalar_recs = [
            r for r in recommendations
            if r.get("subtype") == "scalar_subquery_to_join"
        ]
        assert len(scalar_recs) > 0

    def test_analyze_detects_nested_loops_with_large_cardinality(
        self, engine, sample_plan_with_nested_loops
    ):
        """Test detection of inefficient nested loops."""
        sql_text = "SELECT * FROM table1 JOIN table2 ON ..."

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=sample_plan_with_nested_loops,
        )

        # Should have join method hint recommendation
        hint_recs = [r for r in recommendations if r["type"] == engine.TYPE_OPTIMIZER_HINT]
        join_recs = [r for r in hint_recs if r.get("subtype") == "join_method"]
        assert len(join_recs) > 0
        assert "HASH" in join_recs[0]["hint"]

    def test_analyze_detects_missing_parallelism(self, engine):
        """Test detection of missing parallel execution."""
        plan_operations = [
            {
                "id": 0,
                "operation": "SELECT STATEMENT",
                "cost": 2000,
            },
            {
                "id": 1,
                "operation": "TABLE ACCESS",
                "options": "FULL",
                "object_name": "BIG_TABLE",
                "cost": 1900,
                "cardinality": 200000,
            },
        ]
        sql_text = "SELECT * FROM big_table"

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should have parallelism recommendations
        parallel_recs = [
            r for r in recommendations
            if r["type"] in [engine.TYPE_OPTIMIZER_HINT, engine.TYPE_PARALLEL]
        ]
        # May have parallel hint or parallel scan recommendation
        assert len(parallel_recs) > 0

    def test_extract_columns_from_predicates(self, engine):
        """Test column extraction from predicates."""
        filter_predicates = '"EMPLOYEES"."DEPARTMENT_ID"=:B1 AND "EMPLOYEES"."SALARY">:B2'

        columns = engine._extract_columns_from_predicates(filter_predicates, None)

        assert "DEPARTMENT_ID" in columns
        assert "SALARY" in columns

    def test_generate_index_creation_sql(self, engine):
        """Test index creation SQL generation."""
        sql = engine._generate_index_creation_sql("EMPLOYEES", ["DEPT_ID", "SALARY"])

        assert "CREATE INDEX" in sql
        assert "EMPLOYEES" in sql
        assert "DEPT_ID" in sql
        assert "SALARY" in sql
        assert "PARALLEL" in sql

    def test_determine_index_priority(self, engine):
        """Test index priority determination."""
        # High cost and cardinality
        priority1 = engine._determine_index_priority(2000, 200000)
        assert priority1 == engine.PRIORITY_CRITICAL

        # Medium cost
        priority2 = engine._determine_index_priority(600, 15000)
        assert priority2 == engine.PRIORITY_HIGH

        # Low cost
        priority3 = engine._determine_index_priority(150, 2000)
        assert priority3 == engine.PRIORITY_MEDIUM

        # Very low cost
        priority4 = engine._determine_index_priority(50, 500)
        assert priority4 == engine.PRIORITY_LOW

    def test_estimate_index_impact(self, engine):
        """Test index impact estimation."""
        # High cost
        impact1 = engine._estimate_index_impact(2000, 10000)
        assert impact1 == engine.IMPACT_HIGH

        # Medium cost
        impact2 = engine._estimate_index_impact(600, 5000)
        assert impact2 == engine.IMPACT_MEDIUM

        # Low cost
        impact3 = engine._estimate_index_impact(150, 1000)
        assert impact3 == engine.IMPACT_LOW

        # Minimal cost
        impact4 = engine._estimate_index_impact(50, 100)
        assert impact4 == engine.IMPACT_MINIMAL

    def test_sort_recommendations(self, engine):
        """Test recommendation sorting by priority and impact."""
        recommendations = [
            {
                "priority": engine.PRIORITY_LOW,
                "estimated_impact": engine.IMPACT_LOW,
            },
            {
                "priority": engine.PRIORITY_CRITICAL,
                "estimated_impact": engine.IMPACT_HIGH,
            },
            {
                "priority": engine.PRIORITY_HIGH,
                "estimated_impact": engine.IMPACT_MEDIUM,
            },
        ]

        sorted_recs = engine._sort_recommendations(recommendations)

        # Critical should be first
        assert sorted_recs[0]["priority"] == engine.PRIORITY_CRITICAL
        # Low should be last
        assert sorted_recs[-1]["priority"] == engine.PRIORITY_LOW

    def test_analyze_empty_plan(self, engine):
        """Test analysis with empty plan."""
        sql_text = "SELECT * FROM table1"
        plan_operations = []

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should still generate some recommendations from SQL text analysis
        assert isinstance(recommendations, list)
        # May have rewrite recommendations even without plan
        assert len(recommendations) >= 0

    def test_statistics_recommendations(self, engine):
        """Test statistics gathering recommendations."""
        plan_operations = [
            {
                "id": 0,
                "operation": "TABLE ACCESS",
                "options": "FULL",
                "object_name": "TEST_TABLE",
                "object_type": "TABLE",
                "cost": 500,
            }
        ]
        statistics_info = {
            "stale_tables": ["TEST_TABLE"],
            "never_analyzed_tables": [],
        }

        recommendations = engine.analyze_and_recommend(
            sql_text="SELECT * FROM test_table",
            plan_operations=plan_operations,
            statistics_info=statistics_info,
        )

        # Should have statistics recommendation
        stats_recs = [r for r in recommendations if r["type"] == engine.TYPE_STATISTICS]
        assert len(stats_recs) > 0
        assert stats_recs[0]["table"] == "TEST_TABLE"
        assert "DBMS_STATS" in stats_recs[0]["sql"]

    def test_multiple_recommendation_types(self, engine):
        """Test generation of multiple recommendation types."""
        sql_text = "SELECT * FROM employees WHERE dept_id = 10 OR dept_id = 20"
        plan_operations = [
            {
                "id": 0,
                "operation": "TABLE ACCESS",
                "options": "FULL",
                "object_name": "EMPLOYEES",
                "object_type": "TABLE",
                "cost": 1000,
                "cardinality": 50000,
                "filter_predicates": '"EMPLOYEES"."DEPT_ID"=:B1',
            }
        ]

        recommendations = engine.analyze_and_recommend(
            sql_text=sql_text,
            plan_operations=plan_operations,
        )

        # Should have multiple types
        types = set(r["type"] for r in recommendations)
        assert len(types) > 1
        # Should have at least index and rewrite recommendations
        assert engine.TYPE_INDEX in types
        assert engine.TYPE_SQL_REWRITE in types
