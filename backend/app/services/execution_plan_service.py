"""Execution plan analysis service.

This module provides business logic for analyzing Oracle execution plans.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from app.core.oracle.execution_plans import ExecutionPlanFetcher
from app.core.oracle.connection import get_connection_manager

logger = logging.getLogger(__name__)


class ExecutionPlanService:
    """Service for execution plan analysis and recommendations."""

    # Operations that typically indicate performance issues
    PROBLEMATIC_OPERATIONS = {
        "TABLE ACCESS FULL": "full_table_scan",
        "INDEX FULL SCAN": "index_full_scan",
        "NESTED LOOPS": "nested_loops",
        "CARTESIAN": "cartesian_product",
        "SORT": "sort_operation",
        "HASH JOIN": "hash_join",
        "MERGE JOIN": "merge_join",
        "TEMP TABLE": "temp_table_usage",
    }

    def __init__(self):
        """Initialize ExecutionPlanService."""
        self.connection_manager = get_connection_manager()
        self.plan_fetcher = ExecutionPlanFetcher(self.connection_manager)

    def get_execution_plan(
        self, sql_id: str, plan_hash_value: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get execution plan with analysis.

        Args:
            sql_id: Oracle SQL_ID
            plan_hash_value: Optional specific plan version

        Returns:
            Dictionary with plan tree, analysis, and recommendations
        """
        # Fetch plan operations
        plan_operations = self.plan_fetcher.fetch_plan_by_sql_id(
            sql_id, plan_hash_value
        )

        if not plan_operations:
            return {}

        # Build tree structure
        plan_tree = self.plan_fetcher.build_plan_tree(plan_operations)

        # Analyze plan
        analysis = self.analyze_plan(plan_operations, plan_tree)

        # Get plan statistics if plan_hash_value provided
        statistics = {}
        if plan_hash_value:
            statistics = self.plan_fetcher.get_plan_statistics(
                sql_id, plan_hash_value
            )

        return {
            "sql_id": sql_id,
            "plan_hash_value": plan_operations[0].get("plan_hash_value")
            if plan_operations
            else None,
            "plan_tree": plan_tree,
            "plan_operations": plan_operations,
            "analysis": analysis,
            "statistics": statistics,
        }

    def get_plan_history(self, sql_id: str) -> List[Dict[str, Any]]:
        """
        Get all execution plan versions for a SQL_ID.

        Args:
            sql_id: Oracle SQL_ID

        Returns:
            List of plan versions with metadata
        """
        return self.plan_fetcher.fetch_plan_history(sql_id)

    def analyze_plan(
        self, plan_operations: List[Dict[str, Any]], plan_tree: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze execution plan and identify issues.

        Args:
            plan_operations: Flat list of plan operations
            plan_tree: Hierarchical plan tree

        Returns:
            Analysis results with issues, recommendations, and metrics
        """
        issues = []
        recommendations = []

        # Find costly operations
        costly_operations = self._find_costly_operations(plan_operations)

        # Detect full table scans
        full_scans = self._detect_full_table_scans(plan_operations)
        if full_scans:
            issues.append({
                "type": "full_table_scan",
                "severity": "medium",
                "message": f"Found {len(full_scans)} full table scan(s)",
                "operations": full_scans,
            })
            recommendations.append({
                "type": "index_recommendation",
                "priority": "medium",
                "message": "Consider adding indexes on columns used in WHERE clauses",
                "affected_tables": [op.get("object_name") for op in full_scans if op.get("object_name")],
            })

        # Detect Cartesian products
        cartesians = self._detect_cartesian_products(plan_operations)
        if cartesians:
            issues.append({
                "type": "cartesian_product",
                "severity": "high",
                "message": f"Found {len(cartesians)} Cartesian product(s) - missing join condition",
                "operations": cartesians,
            })
            recommendations.append({
                "type": "query_rewrite",
                "priority": "high",
                "message": "Add proper join conditions to eliminate Cartesian products",
            })

        # Detect missing indexes
        missing_indexes = self._detect_missing_indexes(plan_operations)
        if missing_indexes:
            recommendations.extend(missing_indexes)

        # Detect high cardinality operations
        high_cardinality = self._detect_high_cardinality_operations(plan_operations)
        if high_cardinality:
            issues.append({
                "type": "high_cardinality",
                "severity": "medium",
                "message": f"Found {len(high_cardinality)} operation(s) with high row counts",
                "operations": high_cardinality,
            })

        # Calculate plan metrics
        metrics = self._calculate_plan_metrics(plan_operations, plan_tree)

        return {
            "issues": issues,
            "recommendations": recommendations,
            "costly_operations": costly_operations,
            "metrics": metrics,
        }

    def _find_costly_operations(
        self, plan_operations: List[Dict[str, Any]], top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify the most costly operations in the plan.

        Args:
            plan_operations: List of plan operations
            top_n: Number of top operations to return

        Returns:
            List of costly operations sorted by cost
        """
        operations_with_cost = [
            op for op in plan_operations if op.get("cost") is not None and op.get("cost") > 0
        ]

        # Sort by cost descending
        sorted_ops = sorted(
            operations_with_cost,
            key=lambda x: x.get("cost", 0),
            reverse=True,
        )

        return sorted_ops[:top_n]

    def _detect_full_table_scans(
        self, plan_operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect full table scan operations.

        Args:
            plan_operations: List of plan operations

        Returns:
            List of operations performing full table scans
        """
        full_scans = []

        for op in plan_operations:
            operation = op.get("operation", "")
            options = op.get("options", "")

            if operation == "TABLE ACCESS" and options == "FULL":
                # Check if it's on a significant table (not small lookup tables)
                cardinality = op.get("cardinality", 0)
                if cardinality > 1000:  # Arbitrary threshold
                    full_scans.append(op)

        return full_scans

    def _detect_cartesian_products(
        self, plan_operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect Cartesian product operations.

        Args:
            plan_operations: List of plan operations

        Returns:
            List of Cartesian product operations
        """
        cartesians = []

        for op in plan_operations:
            operation = op.get("operation", "")

            if "CARTESIAN" in operation or operation == "MERGE JOIN CARTESIAN":
                cartesians.append(op)

        return cartesians

    def _detect_missing_indexes(
        self, plan_operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect potential missing indexes based on plan operations.

        Args:
            plan_operations: List of plan operations

        Returns:
            List of index recommendations
        """
        recommendations = []

        for op in plan_operations:
            operation = op.get("operation", "")
            options = op.get("options", "")
            object_name = op.get("object_name")
            access_predicates = op.get("access_predicates")
            filter_predicates = op.get("filter_predicates")

            # Full table scan with filter predicates suggests missing index
            if operation == "TABLE ACCESS" and options == "FULL":
                if filter_predicates and object_name:
                    recommendations.append({
                        "type": "missing_index",
                        "priority": "high",
                        "message": f"Consider adding index on {object_name} for filter conditions",
                        "table": object_name,
                        "predicates": filter_predicates,
                        "operation_id": op.get("id"),
                    })

            # Nested loops without index access
            if operation == "NESTED LOOPS":
                # Check if children use full table scans
                # This is simplified - full implementation would traverse tree
                recommendations.append({
                    "type": "nested_loop_optimization",
                    "priority": "medium",
                    "message": "Review nested loop operation for index opportunities",
                    "operation_id": op.get("id"),
                })

        return recommendations

    def _detect_high_cardinality_operations(
        self, plan_operations: List[Dict[str, Any]], threshold: int = 100000
    ) -> List[Dict[str, Any]]:
        """
        Detect operations processing high number of rows.

        Args:
            plan_operations: List of plan operations
            threshold: Cardinality threshold

        Returns:
            List of high cardinality operations
        """
        high_card_ops = []

        for op in plan_operations:
            cardinality = op.get("cardinality", 0)
            if cardinality and cardinality > threshold:
                high_card_ops.append(op)

        return high_card_ops

    def _calculate_plan_metrics(
        self, plan_operations: List[Dict[str, Any]], plan_tree: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall plan metrics.

        Args:
            plan_operations: List of plan operations
            plan_tree: Plan tree structure

        Returns:
            Dictionary of plan metrics
        """
        total_cost = sum(op.get("cost", 0) for op in plan_operations if op.get("cost"))
        total_cardinality = sum(
            op.get("cardinality", 0) for op in plan_operations if op.get("cardinality")
        )
        total_bytes = sum(
            op.get("bytes", 0) for op in plan_operations if op.get("bytes")
        )

        # Count operation types
        operation_types = {}
        for op in plan_operations:
            op_type = op.get("operation", "UNKNOWN")
            operation_types[op_type] = operation_types.get(op_type, 0) + 1

        # Plan complexity (number of operations)
        complexity = len(plan_operations)

        # Maximum depth
        max_depth = max(
            (op.get("depth", 0) for op in plan_operations), default=0
        )

        return {
            "total_cost": total_cost,
            "total_cardinality": total_cardinality,
            "total_bytes": total_bytes,
            "operation_count": len(plan_operations),
            "operation_types": operation_types,
            "complexity": complexity,
            "max_depth": max_depth,
            "parallel_operations": sum(
                1 for op in plan_operations if op.get("distribution")
            ),
        }

    def export_plan_text(self, sql_id: str, plan_hash_value: Optional[int] = None) -> str:
        """
        Export execution plan as formatted text.

        Args:
            sql_id: Oracle SQL_ID
            plan_hash_value: Optional specific plan version

        Returns:
            Formatted plan text
        """
        plan_operations = self.plan_fetcher.fetch_plan_by_sql_id(
            sql_id, plan_hash_value
        )

        if not plan_operations:
            return "No execution plan found."

        return self.plan_fetcher.format_plan_text(plan_operations)
