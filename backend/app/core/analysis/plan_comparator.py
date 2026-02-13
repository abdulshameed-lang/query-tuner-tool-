"""Execution plan comparison and regression detection.

This module provides functionality to compare execution plans and detect
performance regressions between current and historical plans.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PlanComparator:
    """Compares execution plans and detects regressions."""

    # Thresholds for regression detection
    COST_REGRESSION_THRESHOLD = 1.5  # 50% increase
    CARDINALITY_ESTIMATION_ERROR_THRESHOLD = 10.0  # 10x difference
    SIGNIFICANT_COST_CHANGE = 1.2  # 20% change

    def __init__(self):
        """Initialize PlanComparator."""
        pass

    def compare_plans(
        self,
        current_plan: List[Dict[str, Any]],
        historical_plan: List[Dict[str, Any]],
        current_metadata: Optional[Dict[str, Any]] = None,
        historical_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compare two execution plans and generate comprehensive analysis.

        Args:
            current_plan: Current plan operations
            historical_plan: Historical plan operations
            current_metadata: Metadata about current plan (timestamps, etc.)
            historical_metadata: Metadata about historical plan

        Returns:
            Dictionary with comparison results
        """
        if not current_plan or not historical_plan:
            return {
                "comparison_possible": False,
                "reason": "One or both plans are empty",
            }

        # Extract plan hash values
        current_hash = current_plan[0].get("plan_hash_value") if current_plan else None
        historical_hash = historical_plan[0].get("plan_hash_value") if historical_plan else None

        # Check if plans are identical
        plans_identical = current_hash == historical_hash

        # Calculate overall metrics
        current_metrics = self._calculate_plan_metrics(current_plan)
        historical_metrics = self._calculate_plan_metrics(historical_plan)

        # Detect regression
        regression_analysis = self.detect_regression(
            current_metrics, historical_metrics
        )

        # Calculate detailed diff
        plan_diff = self.calculate_plan_diff(current_plan, historical_plan)

        # Identify operation changes
        operation_changes = self.identify_operation_changes(
            current_plan, historical_plan
        )

        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(
            regression_analysis, operation_changes, plans_identical
        )

        return {
            "comparison_possible": True,
            "plans_identical": plans_identical,
            "current_plan_hash": current_hash,
            "historical_plan_hash": historical_hash,
            "current_metadata": current_metadata or {},
            "historical_metadata": historical_metadata or {},
            "current_metrics": current_metrics,
            "historical_metrics": historical_metrics,
            "regression_detected": regression_analysis["has_regression"],
            "regression_analysis": regression_analysis,
            "plan_diff": plan_diff,
            "operation_changes": operation_changes,
            "recommendations": recommendations,
            "comparison_timestamp": datetime.utcnow().isoformat(),
        }

    def detect_regression(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Detect if current plan has regressed compared to historical plan.

        Args:
            current_metrics: Metrics from current plan
            historical_metrics: Metrics from historical plan

        Returns:
            Dictionary with regression analysis
        """
        regressions = []
        improvements = []

        # Cost comparison
        current_cost = current_metrics.get("total_cost", 0) or 0
        historical_cost = historical_metrics.get("total_cost", 0) or 0

        if historical_cost > 0:
            cost_ratio = current_cost / historical_cost
            cost_change_pct = ((current_cost - historical_cost) / historical_cost) * 100

            if cost_ratio >= self.COST_REGRESSION_THRESHOLD:
                regressions.append({
                    "type": "cost_increase",
                    "severity": "high" if cost_ratio >= 2.0 else "medium",
                    "current_value": current_cost,
                    "historical_value": historical_cost,
                    "ratio": round(cost_ratio, 2),
                    "change_percent": round(cost_change_pct, 2),
                    "message": f"Plan cost increased by {cost_change_pct:.1f}% "
                               f"({historical_cost} → {current_cost})",
                })
            elif cost_ratio <= (1 / self.SIGNIFICANT_COST_CHANGE):
                improvements.append({
                    "type": "cost_decrease",
                    "current_value": current_cost,
                    "historical_value": historical_cost,
                    "ratio": round(cost_ratio, 2),
                    "change_percent": round(cost_change_pct, 2),
                    "message": f"Plan cost decreased by {abs(cost_change_pct):.1f}%",
                })

        # Cardinality comparison
        current_cardinality = current_metrics.get("total_cardinality", 0) or 0
        historical_cardinality = historical_metrics.get("total_cardinality", 0) or 0

        if historical_cardinality > 0 and current_cardinality > 0:
            cardinality_ratio = current_cardinality / historical_cardinality

            if cardinality_ratio >= self.CARDINALITY_ESTIMATION_ERROR_THRESHOLD:
                regressions.append({
                    "type": "cardinality_overestimation",
                    "severity": "high",
                    "current_value": current_cardinality,
                    "historical_value": historical_cardinality,
                    "ratio": round(cardinality_ratio, 2),
                    "message": f"Cardinality overestimated by {cardinality_ratio:.1f}x",
                })
            elif cardinality_ratio <= (1 / self.CARDINALITY_ESTIMATION_ERROR_THRESHOLD):
                regressions.append({
                    "type": "cardinality_underestimation",
                    "severity": "high",
                    "current_value": current_cardinality,
                    "historical_value": historical_cardinality,
                    "ratio": round(cardinality_ratio, 2),
                    "message": f"Cardinality underestimated by {1/cardinality_ratio:.1f}x",
                })

        # CPU cost comparison
        current_cpu = current_metrics.get("total_cpu_cost", 0) or 0
        historical_cpu = historical_metrics.get("total_cpu_cost", 0) or 0

        if historical_cpu > 0:
            cpu_ratio = current_cpu / historical_cpu
            if cpu_ratio >= self.COST_REGRESSION_THRESHOLD:
                regressions.append({
                    "type": "cpu_cost_increase",
                    "severity": "medium",
                    "current_value": current_cpu,
                    "historical_value": historical_cpu,
                    "ratio": round(cpu_ratio, 2),
                    "message": f"CPU cost increased by {cpu_ratio:.1f}x",
                })

        # I/O cost comparison
        current_io = current_metrics.get("total_io_cost", 0) or 0
        historical_io = historical_metrics.get("total_io_cost", 0) or 0

        if historical_io > 0:
            io_ratio = current_io / historical_io
            if io_ratio >= self.COST_REGRESSION_THRESHOLD:
                regressions.append({
                    "type": "io_cost_increase",
                    "severity": "medium",
                    "current_value": current_io,
                    "historical_value": historical_io,
                    "ratio": round(io_ratio, 2),
                    "message": f"I/O cost increased by {io_ratio:.1f}x",
                })

        # Plan depth comparison (deeper plans might be more complex)
        current_depth = current_metrics.get("max_depth", 0)
        historical_depth = historical_metrics.get("max_depth", 0)

        if current_depth > historical_depth + 2:
            regressions.append({
                "type": "plan_complexity_increase",
                "severity": "low",
                "current_value": current_depth,
                "historical_value": historical_depth,
                "message": f"Plan became more complex (depth {historical_depth} → {current_depth})",
            })

        return {
            "has_regression": len(regressions) > 0,
            "regression_count": len(regressions),
            "improvement_count": len(improvements),
            "regressions": regressions,
            "improvements": improvements,
            "severity": self._determine_overall_severity(regressions),
        }

    def calculate_plan_diff(
        self,
        current_plan: List[Dict[str, Any]],
        historical_plan: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate detailed differences between two plans.

        Args:
            current_plan: Current plan operations
            historical_plan: Historical plan operations

        Returns:
            Dictionary with plan differences
        """
        # Create operation signatures for comparison
        current_ops = self._create_operation_signatures(current_plan)
        historical_ops = self._create_operation_signatures(historical_plan)

        # Find added, removed, and modified operations
        current_signatures = set(current_ops.keys())
        historical_signatures = set(historical_ops.keys())

        added_operations = current_signatures - historical_signatures
        removed_operations = historical_signatures - current_signatures
        common_operations = current_signatures & historical_signatures

        modified_operations = []
        for sig in common_operations:
            current_op = current_ops[sig]
            historical_op = historical_ops[sig]

            if self._operations_differ(current_op, historical_op):
                modified_operations.append({
                    "signature": sig,
                    "current": current_op,
                    "historical": historical_op,
                    "changes": self._identify_operation_differences(
                        current_op, historical_op
                    ),
                })

        return {
            "operations_added": len(added_operations),
            "operations_removed": len(removed_operations),
            "operations_modified": len(modified_operations),
            "added_details": [current_ops[sig] for sig in added_operations],
            "removed_details": [historical_ops[sig] for sig in removed_operations],
            "modified_details": modified_operations,
            "total_changes": len(added_operations) + len(removed_operations) + len(modified_operations),
        }

    def identify_operation_changes(
        self,
        current_plan: List[Dict[str, Any]],
        historical_plan: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Identify significant operation changes between plans.

        Args:
            current_plan: Current plan operations
            historical_plan: Historical plan operations

        Returns:
            List of significant operation changes
        """
        changes = []

        # Group operations by object for comparison
        current_by_object = self._group_operations_by_object(current_plan)
        historical_by_object = self._group_operations_by_object(historical_plan)

        # Check for access method changes
        all_objects = set(current_by_object.keys()) | set(historical_by_object.keys())

        for obj_name in all_objects:
            current_ops = current_by_object.get(obj_name, [])
            historical_ops = historical_by_object.get(obj_name, [])

            # Object accessed in both plans
            if current_ops and historical_ops:
                current_access = self._get_access_method(current_ops[0])
                historical_access = self._get_access_method(historical_ops[0])

                if current_access != historical_access:
                    changes.append({
                        "type": "access_method_change",
                        "object_name": obj_name,
                        "historical_method": historical_access,
                        "current_method": current_access,
                        "severity": self._assess_access_change_severity(
                            historical_access, current_access
                        ),
                        "message": f"{obj_name}: {historical_access} → {current_access}",
                    })

            # Object only in current plan
            elif current_ops and not historical_ops:
                changes.append({
                    "type": "new_object_access",
                    "object_name": obj_name,
                    "access_method": self._get_access_method(current_ops[0]),
                    "severity": "low",
                    "message": f"New table accessed: {obj_name}",
                })

            # Object only in historical plan
            elif historical_ops and not current_ops:
                changes.append({
                    "type": "removed_object_access",
                    "object_name": obj_name,
                    "access_method": self._get_access_method(historical_ops[0]),
                    "severity": "low",
                    "message": f"Table no longer accessed: {obj_name}",
                })

        # Check for join order changes
        current_joins = self._extract_join_sequence(current_plan)
        historical_joins = self._extract_join_sequence(historical_plan)

        if current_joins != historical_joins:
            changes.append({
                "type": "join_order_change",
                "historical_sequence": historical_joins,
                "current_sequence": current_joins,
                "severity": "medium",
                "message": "Join order has changed",
            })

        return changes

    def recommend_plan_baseline(
        self,
        comparison_result: Dict[str, Any],
        sql_id: str,
    ) -> Dict[str, Any]:
        """
        Recommend whether to create a SQL Plan Baseline.

        Args:
            comparison_result: Result from compare_plans()
            sql_id: SQL_ID for the query

        Returns:
            Recommendation dictionary
        """
        should_baseline = False
        reasons = []
        priority = "low"

        regression_analysis = comparison_result.get("regression_analysis", {})
        has_regression = regression_analysis.get("has_regression", False)
        severity = regression_analysis.get("severity", "none")

        if has_regression:
            if severity in ["high", "critical"]:
                should_baseline = True
                priority = "high"
                reasons.append(
                    f"Significant performance regression detected ({severity} severity)"
                )
            elif severity == "medium":
                should_baseline = True
                priority = "medium"
                reasons.append("Moderate performance regression detected")

        # Check for plan instability
        operation_changes = comparison_result.get("operation_changes", [])
        if len(operation_changes) >= 3:
            should_baseline = True
            priority = max(priority, "medium", key=lambda x: ["low", "medium", "high"].index(x))
            reasons.append(
                f"Plan instability detected ({len(operation_changes)} operation changes)"
            )

        # Check for access method changes
        access_changes = [
            c for c in operation_changes if c.get("type") == "access_method_change"
        ]
        if access_changes:
            high_severity_changes = [
                c for c in access_changes if c.get("severity") == "high"
            ]
            if high_severity_changes:
                should_baseline = True
                priority = "high"
                reasons.append(
                    f"Critical access method changes ({len(high_severity_changes)} found)"
                )

        if should_baseline:
            baseline_sql = self._generate_baseline_sql(
                sql_id,
                comparison_result.get("historical_plan_hash"),
                comparison_result.get("current_plan_hash"),
            )

            return {
                "recommend_baseline": True,
                "priority": priority,
                "reasons": reasons,
                "sql_id": sql_id,
                "preferred_plan_hash": comparison_result.get("historical_plan_hash"),
                "baseline_creation_sql": baseline_sql,
                "instructions": [
                    "Review the historical plan to ensure it's the desired plan",
                    "Execute the baseline creation SQL as a privileged user",
                    "Verify the baseline is active using DBA_SQL_PLAN_BASELINES",
                    "Monitor query performance after baseline creation",
                ],
            }
        else:
            return {
                "recommend_baseline": False,
                "priority": "none",
                "reasons": ["No significant regression or instability detected"],
            }

    def _calculate_plan_metrics(
        self, plan_operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate metrics for a plan.

        Args:
            plan_operations: List of plan operations

        Returns:
            Dictionary with plan metrics
        """
        if not plan_operations:
            return {}

        total_cost = 0
        total_cardinality = 0
        total_cpu_cost = 0
        total_io_cost = 0
        max_depth = 0
        operation_count = len(plan_operations)

        for op in plan_operations:
            total_cost += op.get("cost") or 0
            total_cardinality += op.get("cardinality") or 0
            total_cpu_cost += op.get("cpu_cost") or 0
            total_io_cost += op.get("io_cost") or 0
            max_depth = max(max_depth, op.get("depth") or 0)

        # Get root operation cost (most accurate)
        root_cost = plan_operations[0].get("cost") or 0

        return {
            "total_cost": root_cost,  # Use root cost as overall cost
            "total_cardinality": total_cardinality,
            "total_cpu_cost": total_cpu_cost,
            "total_io_cost": total_io_cost,
            "max_depth": max_depth,
            "operation_count": operation_count,
            "plan_hash_value": plan_operations[0].get("plan_hash_value"),
        }

    def _create_operation_signatures(
        self, plan_operations: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create unique signatures for plan operations.

        Args:
            plan_operations: List of plan operations

        Returns:
            Dictionary mapping signatures to operations
        """
        signatures = {}

        for op in plan_operations:
            # Create signature from operation details
            signature = f"{op.get('id')}:{op.get('operation')}:{op.get('options')}:{op.get('object_name')}"
            signatures[signature] = op

        return signatures

    def _operations_differ(
        self, op1: Dict[str, Any], op2: Dict[str, Any]
    ) -> bool:
        """
        Check if two operations differ significantly.

        Args:
            op1: First operation
            op2: Second operation

        Returns:
            True if operations differ significantly
        """
        # Compare key fields
        cost1 = op1.get("cost") or 0
        cost2 = op2.get("cost") or 0

        if cost2 > 0:
            cost_ratio = cost1 / cost2
            if cost_ratio >= self.SIGNIFICANT_COST_CHANGE or cost_ratio <= (1 / self.SIGNIFICANT_COST_CHANGE):
                return True

        # Check for different access predicates
        if op1.get("access_predicates") != op2.get("access_predicates"):
            return True

        # Check for different filter predicates
        if op1.get("filter_predicates") != op2.get("filter_predicates"):
            return True

        return False

    def _identify_operation_differences(
        self, op1: Dict[str, Any], op2: Dict[str, Any]
    ) -> List[str]:
        """
        Identify specific differences between two operations.

        Args:
            op1: Current operation
            op2: Historical operation

        Returns:
            List of difference descriptions
        """
        differences = []

        cost1 = op1.get("cost") or 0
        cost2 = op2.get("cost") or 0
        if cost2 > 0 and abs(cost1 - cost2) > 0:
            cost_change_pct = ((cost1 - cost2) / cost2) * 100
            differences.append(f"Cost changed by {cost_change_pct:+.1f}%")

        if op1.get("access_predicates") != op2.get("access_predicates"):
            differences.append("Access predicates changed")

        if op1.get("filter_predicates") != op2.get("filter_predicates"):
            differences.append("Filter predicates changed")

        cardinality1 = op1.get("cardinality") or 0
        cardinality2 = op2.get("cardinality") or 0
        if cardinality2 > 0 and abs(cardinality1 - cardinality2) > 0:
            card_change_pct = ((cardinality1 - cardinality2) / cardinality2) * 100
            if abs(card_change_pct) > 20:
                differences.append(f"Cardinality changed by {card_change_pct:+.1f}%")

        return differences

    def _group_operations_by_object(
        self, plan_operations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group plan operations by object name.

        Args:
            plan_operations: List of plan operations

        Returns:
            Dictionary mapping object names to operations
        """
        grouped = {}

        for op in plan_operations:
            obj_name = op.get("object_name")
            if obj_name:
                if obj_name not in grouped:
                    grouped[obj_name] = []
                grouped[obj_name].append(op)

        return grouped

    def _get_access_method(self, operation: Dict[str, Any]) -> str:
        """
        Get access method description for an operation.

        Args:
            operation: Plan operation

        Returns:
            Access method string
        """
        op_name = operation.get("operation", "")
        options = operation.get("options", "")

        if op_name == "TABLE ACCESS":
            if "FULL" in options:
                return "TABLE ACCESS FULL"
            elif "BY INDEX ROWID" in options:
                return "INDEX ACCESS"
            elif "BY USER ROWID" in options:
                return "ROWID ACCESS"
            else:
                return f"TABLE ACCESS {options}".strip()
        elif op_name == "INDEX":
            return f"INDEX {options}".strip()
        else:
            return f"{op_name} {options}".strip()

    def _assess_access_change_severity(
        self, historical_method: str, current_method: str
    ) -> str:
        """
        Assess severity of access method change.

        Args:
            historical_method: Historical access method
            current_method: Current access method

        Returns:
            Severity level (low, medium, high)
        """
        # Full table scan from index access is typically bad
        if "INDEX" in historical_method and "FULL" in current_method:
            return "high"

        # Index access from full scan might be good
        if "FULL" in historical_method and "INDEX" in current_method:
            return "low"

        # Other changes are medium severity
        return "medium"

    def _extract_join_sequence(
        self, plan_operations: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract join sequence from plan operations.

        Args:
            plan_operations: List of plan operations

        Returns:
            List of joined table names in order
        """
        join_sequence = []

        for op in plan_operations:
            operation = op.get("operation", "")
            if "JOIN" in operation:
                obj_name = op.get("object_name")
                if obj_name:
                    join_sequence.append(obj_name)

        return join_sequence

    def _determine_overall_severity(
        self, regressions: List[Dict[str, Any]]
    ) -> str:
        """
        Determine overall severity from list of regressions.

        Args:
            regressions: List of regression findings

        Returns:
            Overall severity level
        """
        if not regressions:
            return "none"

        severities = [r.get("severity", "low") for r in regressions]

        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

    def _generate_comparison_recommendations(
        self,
        regression_analysis: Dict[str, Any],
        operation_changes: List[Dict[str, Any]],
        plans_identical: bool,
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on plan comparison.

        Args:
            regression_analysis: Regression analysis results
            operation_changes: List of operation changes
            plans_identical: Whether plans are identical

        Returns:
            List of recommendations
        """
        recommendations = []

        if plans_identical:
            recommendations.append({
                "type": "info",
                "priority": "low",
                "message": "Plans are identical - no action needed",
            })
            return recommendations

        # Regression recommendations
        if regression_analysis.get("has_regression"):
            severity = regression_analysis.get("severity")

            if severity == "high":
                recommendations.append({
                    "type": "action_required",
                    "priority": "high",
                    "message": "Significant performance regression detected",
                    "actions": [
                        "Consider creating a SQL Plan Baseline with the historical plan",
                        "Check for missing or stale statistics",
                        "Review recent database changes or upgrades",
                        "Analyze bind variable values for cardinality estimation errors",
                    ],
                })

        # Access method change recommendations
        access_changes = [
            c for c in operation_changes if c.get("type") == "access_method_change"
        ]

        for change in access_changes:
            if change.get("severity") == "high":
                recommendations.append({
                    "type": "access_method_regression",
                    "priority": "high",
                    "message": f"Critical access method change: {change.get('message')}",
                    "actions": [
                        "Verify index exists and is visible",
                        "Check index statistics are current",
                        "Consider creating a better index if none exists",
                    ],
                })

        # Improvement recommendations
        improvements = regression_analysis.get("improvements", [])
        if improvements:
            recommendations.append({
                "type": "positive",
                "priority": "low",
                "message": f"Plan improvements detected ({len(improvements)} improvements)",
                "details": [imp.get("message") for imp in improvements],
            })

        return recommendations

    def _generate_baseline_sql(
        self, sql_id: str, preferred_plan_hash: Optional[int], current_plan_hash: Optional[int]
    ) -> str:
        """
        Generate SQL to create a plan baseline.

        Args:
            sql_id: SQL_ID
            preferred_plan_hash: Preferred plan hash value
            current_plan_hash: Current plan hash value

        Returns:
            SQL statement to create baseline
        """
        return f"""-- Create SQL Plan Baseline for SQL_ID: {sql_id}
-- This will fix the execution plan to plan_hash_value: {preferred_plan_hash}

DECLARE
  l_plans_loaded PLS_INTEGER;
BEGIN
  l_plans_loaded := DBMS_SPM.LOAD_PLANS_FROM_CURSOR_CACHE(
    sql_id          => '{sql_id}',
    plan_hash_value => {preferred_plan_hash},
    fixed           => 'YES',
    enabled         => 'YES'
  );

  DBMS_OUTPUT.PUT_LINE('Plans loaded: ' || l_plans_loaded);
END;
/

-- Verify baseline creation
SELECT sql_handle, plan_name, enabled, accepted, fixed
FROM dba_sql_plan_baselines
WHERE sql_text LIKE '%{sql_id}%'
ORDER BY created DESC;
"""
