"""Recommendation engine for query tuning.

This module analyzes execution plans and SQL queries to generate
actionable recommendations for performance improvement.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates actionable query tuning recommendations."""

    # Recommendation types
    TYPE_INDEX = "index"
    TYPE_SQL_REWRITE = "sql_rewrite"
    TYPE_OPTIMIZER_HINT = "optimizer_hint"
    TYPE_STATISTICS = "statistics"
    TYPE_PARTITION = "partition"
    TYPE_PARALLEL = "parallel"

    # Priority levels
    PRIORITY_CRITICAL = "critical"
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"

    # Impact estimation levels
    IMPACT_HIGH = "high"  # 50%+ improvement expected
    IMPACT_MEDIUM = "medium"  # 20-50% improvement
    IMPACT_LOW = "low"  # 5-20% improvement
    IMPACT_MINIMAL = "minimal"  # <5% improvement

    def __init__(self):
        """Initialize RecommendationEngine."""
        self.recommendations = []

    def analyze_and_recommend(
        self,
        sql_text: str,
        plan_operations: List[Dict[str, Any]],
        query_metrics: Optional[Dict[str, Any]] = None,
        statistics_info: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyze query and generate comprehensive recommendations.

        Args:
            sql_text: SQL query text
            plan_operations: List of execution plan operations
            query_metrics: Optional query performance metrics
            statistics_info: Optional table/index statistics information

        Returns:
            List of recommendations sorted by priority and impact
        """
        self.recommendations = []

        # Generate different types of recommendations
        self._analyze_for_index_recommendations(plan_operations, sql_text)
        self._analyze_for_sql_rewrite_recommendations(sql_text, plan_operations)
        self._analyze_for_optimizer_hints(plan_operations, query_metrics)
        self._analyze_for_statistics_recommendations(plan_operations, statistics_info)
        self._analyze_for_parallelism(plan_operations, query_metrics)

        # Sort by priority and estimated impact
        sorted_recommendations = self._sort_recommendations(self.recommendations)

        logger.info(
            f"Generated {len(sorted_recommendations)} recommendations for query analysis"
        )

        return sorted_recommendations

    def _analyze_for_index_recommendations(
        self, plan_operations: List[Dict[str, Any]], sql_text: str
    ) -> None:
        """
        Analyze execution plan for missing index opportunities.

        Args:
            plan_operations: List of plan operations
            sql_text: SQL query text
        """
        for op in plan_operations:
            operation = op.get("operation", "")
            options = op.get("options", "")
            object_name = op.get("object_name")
            cost = op.get("cost", 0)
            cardinality = op.get("cardinality", 0)

            # Full table scan on large tables
            if operation == "TABLE ACCESS" and "FULL" in options:
                if object_name and cost and cost > 100:
                    filter_predicates = op.get("filter_predicates")
                    access_predicates = op.get("access_predicates")

                    # Extract columns from predicates
                    columns = self._extract_columns_from_predicates(
                        filter_predicates, access_predicates
                    )

                    if columns:
                        priority = self._determine_index_priority(cost, cardinality)
                        impact = self._estimate_index_impact(cost, cardinality)

                        self.recommendations.append({
                            "type": self.TYPE_INDEX,
                            "subtype": "missing_index",
                            "priority": priority,
                            "estimated_impact": impact,
                            "table": object_name,
                            "columns": columns,
                            "current_operation": f"{operation} {options}",
                            "cost": cost,
                            "cardinality": cardinality,
                            "title": f"Create index on {object_name}",
                            "description": f"Full table scan detected on {object_name} with cost {cost}. "
                                         f"Consider creating an index on columns: {', '.join(columns)}",
                            "sql": self._generate_index_creation_sql(object_name, columns),
                            "rationale": [
                                f"Current cost: {cost}",
                                f"Estimated rows: {cardinality:,}",
                                f"Full table scan is inefficient for selective queries",
                                f"Index could reduce I/O and improve response time"
                            ],
                            "implementation_notes": [
                                "Verify table size and data distribution",
                                "Check for existing similar indexes",
                                "Consider impact on DML operations",
                                "Test in non-production environment first"
                            ],
                        })

            # Index range scan with high cost (inefficient index)
            elif operation == "INDEX" and "RANGE SCAN" in options and cost and cost > 50:
                if object_name:
                    self.recommendations.append({
                        "type": self.TYPE_INDEX,
                        "subtype": "inefficient_index",
                        "priority": self.PRIORITY_MEDIUM,
                        "estimated_impact": self.IMPACT_MEDIUM,
                        "index_name": object_name,
                        "cost": cost,
                        "title": f"Review index {object_name}",
                        "description": f"Index range scan on {object_name} has high cost ({cost}). "
                                     "Index may be inefficient or not selective enough.",
                        "rationale": [
                            f"Index scan cost: {cost}",
                            "Index may have low selectivity",
                            "Consider composite index or index redesign"
                        ],
                    })

    def _analyze_for_sql_rewrite_recommendations(
        self, sql_text: str, plan_operations: List[Dict[str, Any]]
    ) -> None:
        """
        Analyze SQL text for rewrite opportunities.

        Args:
            sql_text: SQL query text
            plan_operations: List of plan operations
        """
        sql_upper = sql_text.upper()

        # Check for OR conditions that could use UNION ALL
        if " OR " in sql_upper and self._count_occurrences(sql_upper, " OR ") >= 2:
            self.recommendations.append({
                "type": self.TYPE_SQL_REWRITE,
                "subtype": "or_to_union",
                "priority": self.PRIORITY_MEDIUM,
                "estimated_impact": self.IMPACT_MEDIUM,
                "title": "Consider replacing OR with UNION ALL",
                "description": "Multiple OR conditions detected. UNION ALL can be more efficient "
                             "as it allows separate index access paths.",
                "original_pattern": "WHERE col1 = ? OR col2 = ? OR col3 = ?",
                "suggested_pattern": "SELECT ... WHERE col1 = ? UNION ALL SELECT ... WHERE col2 = ? ...",
                "rationale": [
                    "OR conditions may prevent index usage",
                    "UNION ALL allows optimizer to use different indexes per branch",
                    "Can significantly improve performance for selective conditions"
                ],
                "implementation_notes": [
                    "Verify no duplicate elimination is needed (use UNION if needed)",
                    "Ensure bind variables are correctly handled",
                    "Test with representative data volumes"
                ],
            })

        # Check for NOT IN that could use NOT EXISTS
        if " NOT IN " in sql_upper:
            self.recommendations.append({
                "type": self.TYPE_SQL_REWRITE,
                "subtype": "not_in_to_not_exists",
                "priority": self.PRIORITY_MEDIUM,
                "estimated_impact": self.IMPACT_MEDIUM,
                "title": "Replace NOT IN with NOT EXISTS",
                "description": "NOT IN subquery detected. NOT EXISTS is generally more efficient "
                             "and handles NULLs correctly.",
                "original_pattern": "WHERE col NOT IN (SELECT ...)",
                "suggested_pattern": "WHERE NOT EXISTS (SELECT 1 FROM ... WHERE ...)",
                "rationale": [
                    "NOT IN can be very slow with large result sets",
                    "NOT IN returns no rows if subquery contains NULL",
                    "NOT EXISTS short-circuits on first match"
                ],
            })

        # Check for DISTINCT that might be unnecessary
        if "SELECT DISTINCT" in sql_upper:
            # Check if plan has SORT UNIQUE operation
            has_sort_unique = any(
                "SORT" in op.get("operation", "") and "UNIQUE" in op.get("options", "")
                for op in plan_operations
            )
            if has_sort_unique:
                self.recommendations.append({
                    "type": self.TYPE_SQL_REWRITE,
                    "subtype": "eliminate_distinct",
                    "priority": self.PRIORITY_LOW,
                    "estimated_impact": self.IMPACT_LOW,
                    "title": "Review DISTINCT necessity",
                    "description": "DISTINCT causes sort operation. Verify if duplicates are actually "
                                 "possible or if DISTINCT can be eliminated.",
                    "rationale": [
                        "DISTINCT adds sorting overhead",
                        "May be unnecessary if primary key is in SELECT list",
                        "Consider if application can handle duplicates"
                    ],
                })

        # Check for scalar subqueries in SELECT
        if re.search(r"SELECT.*\(SELECT.*FROM", sql_text, re.IGNORECASE | re.DOTALL):
            self.recommendations.append({
                "type": self.TYPE_SQL_REWRITE,
                "subtype": "scalar_subquery_to_join",
                "priority": self.PRIORITY_HIGH,
                "estimated_impact": self.IMPACT_HIGH,
                "title": "Convert scalar subqueries to JOINs",
                "description": "Scalar subqueries in SELECT list can execute for each row. "
                             "Consider rewriting as LEFT JOIN.",
                "original_pattern": "SELECT col1, (SELECT ... FROM t2 WHERE ...) FROM t1",
                "suggested_pattern": "SELECT t1.col1, t2.col FROM t1 LEFT JOIN t2 ON ...",
                "rationale": [
                    "Scalar subqueries execute per row (N+1 query problem)",
                    "JOIN allows optimizer to choose efficient access path",
                    "Can provide orders of magnitude improvement"
                ],
            })

        # Check for SELECT * usage
        if re.search(r"SELECT\s+\*\s+FROM", sql_text, re.IGNORECASE):
            self.recommendations.append({
                "type": self.TYPE_SQL_REWRITE,
                "subtype": "select_star",
                "priority": self.PRIORITY_LOW,
                "estimated_impact": self.IMPACT_MINIMAL,
                "title": "Avoid SELECT *",
                "description": "SELECT * retrieves all columns. Specify only needed columns to reduce I/O.",
                "rationale": [
                    "Reduces data transfer and memory usage",
                    "May prevent index-only scans",
                    "Improves query maintainability"
                ],
            })

    def _analyze_for_optimizer_hints(
        self, plan_operations: List[Dict[str, Any]], query_metrics: Optional[Dict[str, Any]]
    ) -> None:
        """
        Analyze execution plan for optimizer hint opportunities.

        Args:
            plan_operations: List of plan operations
            query_metrics: Optional query performance metrics
        """
        # Check for suboptimal join methods
        for op in plan_operations:
            operation = op.get("operation", "")
            options = op.get("options", "")
            cost = op.get("cost", 0)
            cardinality = op.get("cardinality", 0)

            # Nested loops with large cardinality
            if "NESTED LOOPS" in operation and cardinality > 10000:
                self.recommendations.append({
                    "type": self.TYPE_OPTIMIZER_HINT,
                    "subtype": "join_method",
                    "priority": self.PRIORITY_HIGH,
                    "estimated_impact": self.IMPACT_HIGH,
                    "title": "Consider HASH JOIN instead of NESTED LOOPS",
                    "description": f"Nested loops join processing {cardinality:,} rows. "
                                 "Hash join may be more efficient for large datasets.",
                    "hint": "/*+ USE_HASH(table_alias) */",
                    "affected_operation": f"{operation} {options}",
                    "cardinality": cardinality,
                    "rationale": [
                        "Nested loops efficient for small datasets only",
                        f"Current cardinality: {cardinality:,} rows",
                        "Hash join better for large result sets"
                    ],
                })

            # Hash join with small cardinality
            elif "HASH JOIN" in operation and cardinality < 100:
                self.recommendations.append({
                    "type": self.TYPE_OPTIMIZER_HINT,
                    "subtype": "join_method",
                    "priority": self.PRIORITY_MEDIUM,
                    "estimated_impact": self.IMPACT_MEDIUM,
                    "title": "Consider NESTED LOOPS instead of HASH JOIN",
                    "description": f"Hash join for small dataset ({cardinality} rows). "
                                 "Nested loops may be more efficient.",
                    "hint": "/*+ USE_NL(table_alias) */",
                    "affected_operation": f"{operation} {options}",
                    "cardinality": cardinality,
                })

            # Full table scan with cardinality mismatch
            if operation == "TABLE ACCESS" and "FULL" in options:
                object_name = op.get("object_name")
                if object_name and cardinality and cardinality < 100:
                    self.recommendations.append({
                        "type": self.TYPE_OPTIMIZER_HINT,
                        "subtype": "index_hint",
                        "priority": self.PRIORITY_HIGH,
                        "estimated_impact": self.IMPACT_HIGH,
                        "title": f"Force index usage on {object_name}",
                        "description": f"Full table scan for selective query ({cardinality} rows expected). "
                                     "Consider forcing index usage.",
                        "hint": f"/*+ INDEX(table_alias index_name) */",
                        "table": object_name,
                        "cardinality": cardinality,
                    })

        # Check for missing parallelism
        has_parallel = any("PARALLEL" in str(op.get("operation", "")) for op in plan_operations)
        total_cost = sum(op.get("cost", 0) for op in plan_operations)

        if not has_parallel and total_cost > 1000:
            self.recommendations.append({
                "type": self.TYPE_OPTIMIZER_HINT,
                "subtype": "parallel_hint",
                "priority": self.PRIORITY_MEDIUM,
                "estimated_impact": self.IMPACT_MEDIUM,
                "title": "Consider parallel execution",
                "description": f"High-cost query (cost: {total_cost}) without parallelism. "
                             "Parallel execution may improve performance.",
                "hint": "/*+ PARALLEL(table_alias, 4) */",
                "total_cost": total_cost,
                "rationale": [
                    f"Total query cost: {total_cost}",
                    "No parallel operations detected",
                    "Parallel execution can utilize multiple CPUs"
                ],
                "implementation_notes": [
                    "Verify sufficient parallel servers available",
                    "Check parallel_max_servers parameter",
                    "Monitor system resource usage"
                ],
            })

    def _analyze_for_statistics_recommendations(
        self, plan_operations: List[Dict[str, Any]], statistics_info: Optional[Dict[str, Any]]
    ) -> None:
        """
        Analyze for stale or missing statistics.

        Args:
            plan_operations: List of plan operations
            statistics_info: Optional statistics information
        """
        # Extract tables from plan
        tables = set()
        for op in plan_operations:
            if op.get("object_name") and op.get("object_type") == "TABLE":
                tables.add(op.get("object_name"))

        if statistics_info:
            stale_tables = statistics_info.get("stale_tables", [])
            never_analyzed_tables = statistics_info.get("never_analyzed_tables", [])

            for table in tables:
                if table in stale_tables:
                    self.recommendations.append({
                        "type": self.TYPE_STATISTICS,
                        "subtype": "stale_statistics",
                        "priority": self.PRIORITY_HIGH,
                        "estimated_impact": self.IMPACT_HIGH,
                        "title": f"Gather statistics on {table}",
                        "description": f"Table {table} has stale statistics. "
                                     "This can lead to suboptimal execution plans.",
                        "table": table,
                        "sql": f"BEGIN\n"
                               f"  DBMS_STATS.GATHER_TABLE_STATS(\n"
                               f"    ownname => USER,\n"
                               f"    tabname => '{table}',\n"
                               f"    estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE,\n"
                               f"    method_opt => 'FOR ALL COLUMNS SIZE AUTO'\n"
                               f"  );\n"
                               f"END;",
                        "rationale": [
                            "Stale statistics detected",
                            "Optimizer relies on accurate statistics",
                            "May cause poor cardinality estimates"
                        ],
                    })

                elif table in never_analyzed_tables:
                    self.recommendations.append({
                        "type": self.TYPE_STATISTICS,
                        "subtype": "missing_statistics",
                        "priority": self.PRIORITY_CRITICAL,
                        "estimated_impact": self.IMPACT_HIGH,
                        "title": f"Gather statistics on {table} (never analyzed)",
                        "description": f"Table {table} has never been analyzed. "
                                     "Statistics are essential for optimal execution plans.",
                        "table": table,
                        "sql": f"BEGIN\n"
                               f"  DBMS_STATS.GATHER_TABLE_STATS(\n"
                               f"    ownname => USER,\n"
                               f"    tabname => '{table}',\n"
                               f"    estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE,\n"
                               f"    method_opt => 'FOR ALL COLUMNS SIZE AUTO'\n"
                               f"  );\n"
                               f"END;",
                    })

    def _analyze_for_parallelism(
        self, plan_operations: List[Dict[str, Any]], query_metrics: Optional[Dict[str, Any]]
    ) -> None:
        """
        Analyze for parallel execution opportunities.

        Args:
            plan_operations: List of plan operations
            query_metrics: Optional query performance metrics
        """
        # Check for large full table scans without parallelism
        for op in plan_operations:
            if op.get("operation") == "TABLE ACCESS" and "FULL" in op.get("options", ""):
                cardinality = op.get("cardinality", 0)
                cost = op.get("cost", 0)
                object_name = op.get("object_name")

                # Check if already parallel
                is_parallel = "PARALLEL" in str(op.get("other", ""))

                if not is_parallel and cardinality > 100000 and cost > 500:
                    self.recommendations.append({
                        "type": self.TYPE_PARALLEL,
                        "subtype": "parallel_scan",
                        "priority": self.PRIORITY_MEDIUM,
                        "estimated_impact": self.IMPACT_MEDIUM,
                        "title": f"Enable parallel scan on {object_name}",
                        "description": f"Large full table scan ({cardinality:,} rows) without parallelism. "
                                     "Parallel execution can improve performance.",
                        "table": object_name,
                        "cardinality": cardinality,
                        "cost": cost,
                        "sql": f"ALTER TABLE {object_name} PARALLEL 4;",
                        "hint": f"/*+ PARALLEL({object_name}, 4) */",
                    })

    def _extract_columns_from_predicates(
        self, filter_predicates: Optional[str], access_predicates: Optional[str]
    ) -> List[str]:
        """
        Extract column names from predicates.

        Args:
            filter_predicates: Filter predicate text
            access_predicates: Access predicate text

        Returns:
            List of column names
        """
        columns = []
        predicates = []

        if filter_predicates:
            predicates.append(filter_predicates)
        if access_predicates:
            predicates.append(access_predicates)

        for predicate in predicates:
            # Extract column names (simplified pattern)
            # Format: "TABLE"."COLUMN" or COLUMN
            matches = re.findall(r'"([^"]+)"\."([^"]+)"', predicate)
            for match in matches:
                columns.append(match[1])  # Column name

            # Also try without quotes
            matches = re.findall(r'\b([A-Z_][A-Z0-9_]*)\s*[=<>]', predicate)
            columns.extend(matches)

        # Return unique columns
        return list(set(columns))

    def _generate_index_creation_sql(self, table_name: str, columns: List[str]) -> str:
        """
        Generate CREATE INDEX SQL statement.

        Args:
            table_name: Table name
            columns: List of columns

        Returns:
            CREATE INDEX SQL statement
        """
        index_name = f"IDX_{table_name}_{'_'.join(columns[:3])}"[:30]
        column_list = ", ".join(columns)

        return f"""-- Recommended index creation
CREATE INDEX {index_name}
ON {table_name} ({column_list})
PARALLEL 4
NOLOGGING;

-- After creation, set back to non-parallel
ALTER INDEX {index_name} NOPARALLEL;"""

    def _determine_index_priority(self, cost: int, cardinality: int) -> str:
        """
        Determine priority for index recommendation.

        Args:
            cost: Operation cost
            cardinality: Estimated rows

        Returns:
            Priority level
        """
        if cost > 1000 or cardinality > 100000:
            return self.PRIORITY_CRITICAL
        elif cost > 500 or cardinality > 10000:
            return self.PRIORITY_HIGH
        elif cost > 100 or cardinality > 1000:
            return self.PRIORITY_MEDIUM
        else:
            return self.PRIORITY_LOW

    def _estimate_index_impact(self, cost: int, cardinality: int) -> str:
        """
        Estimate impact of index creation.

        Args:
            cost: Current operation cost
            cardinality: Estimated rows

        Returns:
            Impact level
        """
        if cost > 1000:
            return self.IMPACT_HIGH
        elif cost > 500:
            return self.IMPACT_MEDIUM
        elif cost > 100:
            return self.IMPACT_LOW
        else:
            return self.IMPACT_MINIMAL

    def _count_occurrences(self, text: str, pattern: str) -> int:
        """Count occurrences of pattern in text."""
        return text.count(pattern)

    def _sort_recommendations(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort recommendations by priority and impact.

        Args:
            recommendations: List of recommendations

        Returns:
            Sorted list of recommendations
        """
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3,
        }

        impact_order = {
            self.IMPACT_HIGH: 0,
            self.IMPACT_MEDIUM: 1,
            self.IMPACT_LOW: 2,
            self.IMPACT_MINIMAL: 3,
        }

        return sorted(
            recommendations,
            key=lambda r: (
                priority_order.get(r.get("priority", self.PRIORITY_LOW), 99),
                impact_order.get(r.get("estimated_impact", self.IMPACT_MINIMAL), 99),
            ),
        )
