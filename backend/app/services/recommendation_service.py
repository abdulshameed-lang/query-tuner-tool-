"""Recommendation service layer."""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.oracle.connection import get_connection_manager
from app.core.oracle.queries import QueryFetcher
from app.core.oracle.execution_plans import ExecutionPlanFetcher
from app.core.oracle.statistics import StatisticsChecker
from app.core.analysis.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating query tuning recommendations."""

    def __init__(self):
        """Initialize RecommendationService."""
        self.connection_manager = get_connection_manager()
        self.query_fetcher = QueryFetcher(self.connection_manager)
        self.execution_plan_fetcher = ExecutionPlanFetcher(self.connection_manager)
        self.statistics_checker = StatisticsChecker(self.connection_manager)
        self.recommendation_engine = RecommendationEngine()

    def get_recommendations(
        self,
        sql_id: str,
        include_index: bool = True,
        include_rewrite: bool = True,
        include_hints: bool = True,
        include_statistics: bool = True,
        include_parallelism: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations for a SQL_ID.

        Args:
            sql_id: SQL_ID to analyze
            include_index: Include index recommendations
            include_rewrite: Include SQL rewrite recommendations
            include_hints: Include optimizer hint recommendations
            include_statistics: Include statistics recommendations
            include_parallelism: Include parallelism recommendations

        Returns:
            Dictionary with recommendations and summary
        """
        try:
            # Fetch query information
            query_info = self._fetch_query_info(sql_id)

            if not query_info:
                return {
                    "sql_id": sql_id,
                    "recommendations": [],
                    "summary": self._create_empty_summary(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "error": "Query not found",
                }

            sql_text = query_info.get("sql_fulltext", "")
            plan_operations = query_info.get("plan_operations", [])

            # Get statistics information if needed
            statistics_info = None
            if include_statistics:
                statistics_info = self._get_statistics_info(plan_operations)

            # Generate recommendations
            recommendations = self.recommendation_engine.analyze_and_recommend(
                sql_text=sql_text,
                plan_operations=plan_operations,
                query_metrics=query_info.get("metrics"),
                statistics_info=statistics_info,
            )

            # Filter recommendations based on include flags
            filtered_recommendations = self._filter_recommendations(
                recommendations,
                include_index=include_index,
                include_rewrite=include_rewrite,
                include_hints=include_hints,
                include_statistics=include_statistics,
                include_parallelism=include_parallelism,
            )

            # Create summary
            summary = self._create_summary(filtered_recommendations)

            logger.info(
                f"Generated {len(filtered_recommendations)} recommendations for SQL_ID: {sql_id}"
            )

            return {
                "sql_id": sql_id,
                "recommendations": filtered_recommendations,
                "summary": summary,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            raise

    def get_index_recommendations(self, sql_id: str) -> Dict[str, Any]:
        """
        Get index recommendations only.

        Args:
            sql_id: SQL_ID to analyze

        Returns:
            Dictionary with index recommendations
        """
        result = self.get_recommendations(
            sql_id,
            include_index=True,
            include_rewrite=False,
            include_hints=False,
            include_statistics=False,
            include_parallelism=False,
        )

        return {
            "sql_id": sql_id,
            "recommendations": result["recommendations"],
            "total_count": len(result["recommendations"]),
        }

    def get_rewrite_recommendations(self, sql_id: str) -> Dict[str, Any]:
        """
        Get SQL rewrite recommendations only.

        Args:
            sql_id: SQL_ID to analyze

        Returns:
            Dictionary with rewrite recommendations
        """
        result = self.get_recommendations(
            sql_id,
            include_index=False,
            include_rewrite=True,
            include_hints=False,
            include_statistics=False,
            include_parallelism=False,
        )

        return {
            "sql_id": sql_id,
            "recommendations": result["recommendations"],
            "total_count": len(result["recommendations"]),
        }

    def get_hint_recommendations(self, sql_id: str) -> Dict[str, Any]:
        """
        Get optimizer hint recommendations only.

        Args:
            sql_id: SQL_ID to analyze

        Returns:
            Dictionary with hint recommendations
        """
        result = self.get_recommendations(
            sql_id,
            include_index=False,
            include_rewrite=False,
            include_hints=True,
            include_statistics=False,
            include_parallelism=False,
        )

        return {
            "sql_id": sql_id,
            "recommendations": result["recommendations"],
            "total_count": len(result["recommendations"]),
        }

    def _fetch_query_info(self, sql_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch query information including SQL text and execution plan.

        Args:
            sql_id: SQL_ID

        Returns:
            Dictionary with query information
        """
        try:
            # Fetch query details
            query = self.query_fetcher.fetch_query_by_sql_id(sql_id)

            if not query:
                return None

            # Fetch execution plan
            plan_operations = self.execution_plan_fetcher.fetch_plan_by_sql_id(sql_id)

            return {
                "sql_id": sql_id,
                "sql_fulltext": query.get("sql_fulltext"),
                "plan_operations": plan_operations,
                "metrics": {
                    "executions": query.get("executions"),
                    "elapsed_time": query.get("elapsed_time"),
                    "cpu_time": query.get("cpu_time"),
                    "disk_reads": query.get("disk_reads"),
                    "buffer_gets": query.get("buffer_gets"),
                },
            }

        except Exception as e:
            logger.warning(f"Error fetching query info: {e}")
            return None

    def _get_statistics_info(
        self, plan_operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics information for tables in execution plan.

        Args:
            plan_operations: List of plan operations

        Returns:
            Dictionary with statistics information
        """
        try:
            # Extract unique tables from plan
            tables = set()
            for op in plan_operations:
                if op.get("object_name") and op.get("object_type") == "TABLE":
                    tables.add(op.get("object_name"))

            # Check statistics health
            stale_tables = []
            never_analyzed_tables = []

            for table in tables:
                # Simplified check - in production, query DBA_TAB_STATISTICS
                # For now, return empty lists
                pass

            return {
                "stale_tables": stale_tables,
                "never_analyzed_tables": never_analyzed_tables,
            }

        except Exception as e:
            logger.warning(f"Error getting statistics info: {e}")
            return {"stale_tables": [], "never_analyzed_tables": []}

    def _filter_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        include_index: bool,
        include_rewrite: bool,
        include_hints: bool,
        include_statistics: bool,
        include_parallelism: bool,
    ) -> List[Dict[str, Any]]:
        """
        Filter recommendations based on include flags.

        Args:
            recommendations: List of all recommendations
            include_* flags: Flags for what to include

        Returns:
            Filtered list of recommendations
        """
        filtered = []

        for rec in recommendations:
            rec_type = rec.get("type")

            if rec_type == "index" and include_index:
                filtered.append(rec)
            elif rec_type == "sql_rewrite" and include_rewrite:
                filtered.append(rec)
            elif rec_type == "optimizer_hint" and include_hints:
                filtered.append(rec)
            elif rec_type == "statistics" and include_statistics:
                filtered.append(rec)
            elif rec_type == "parallel" and include_parallelism:
                filtered.append(rec)

        return filtered

    def _create_summary(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create summary statistics for recommendations.

        Args:
            recommendations: List of recommendations

        Returns:
            Summary dictionary
        """
        by_type = {}
        by_priority = {}
        by_impact = {}
        critical_count = 0
        high_impact_count = 0

        for rec in recommendations:
            # Count by type
            rec_type = rec.get("type", "unknown")
            by_type[rec_type] = by_type.get(rec_type, 0) + 1

            # Count by priority
            priority = rec.get("priority", "low")
            by_priority[priority] = by_priority.get(priority, 0) + 1
            if priority == "critical":
                critical_count += 1

            # Count by impact
            impact = rec.get("estimated_impact", "minimal")
            by_impact[impact] = by_impact.get(impact, 0) + 1
            if impact == "high":
                high_impact_count += 1

        return {
            "total_count": len(recommendations),
            "by_type": by_type,
            "by_priority": by_priority,
            "by_impact": by_impact,
            "critical_count": critical_count,
            "high_impact_count": high_impact_count,
        }

    def _create_empty_summary(self) -> Dict[str, Any]:
        """Create empty summary."""
        return {
            "total_count": 0,
            "by_type": {},
            "by_priority": {},
            "by_impact": {},
            "critical_count": 0,
            "high_impact_count": 0,
        }
