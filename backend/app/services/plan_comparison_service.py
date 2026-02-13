"""Plan comparison service layer."""

from typing import List, Dict, Any, Optional
import logging

from app.core.oracle.execution_plans import ExecutionPlanFetcher
from app.core.analysis.plan_comparator import PlanComparator
from app.core.oracle.connection import get_connection_manager

logger = logging.getLogger(__name__)


class PlanComparisonService:
    """Service for execution plan comparison operations."""

    def __init__(self):
        """Initialize PlanComparisonService."""
        self.connection_manager = get_connection_manager()
        self.execution_plan_fetcher = ExecutionPlanFetcher(self.connection_manager)
        self.plan_comparator = PlanComparator()

    def get_plan_versions(
        self, sql_id: str, source: str = "current"
    ) -> List[Dict[str, Any]]:
        """
        Get all execution plan versions for a SQL_ID.

        Args:
            sql_id: SQL_ID to get versions for
            source: Data source ('current', 'historical', or 'both')

        Returns:
            List of plan versions with metadata
        """
        versions = []

        try:
            if source in ["current", "both"]:
                # Get current plan versions from V$SQL_PLAN
                current_versions = self.execution_plan_fetcher.fetch_plan_history(sql_id)
                for version in current_versions:
                    version["source"] = "current"
                versions.extend(current_versions)

            if source in ["historical", "both"]:
                # Get historical plan versions from DBA_HIST_SQL_PLAN
                historical_versions = (
                    self.execution_plan_fetcher.fetch_historical_plan_versions(sql_id)
                )
                for version in historical_versions:
                    version["source"] = "historical"
                versions.extend(historical_versions)

            # Sort by last_seen descending
            versions.sort(
                key=lambda x: x.get("last_seen") or x.get("timestamp") or "",
                reverse=True,
            )

            logger.info(
                f"Found {len(versions)} plan versions for SQL_ID: {sql_id} (source: {source})"
            )

            return versions

        except Exception as e:
            logger.error(f"Error fetching plan versions: {e}", exc_info=True)
            raise

    def compare_plans(
        self,
        sql_id: str,
        current_plan_hash: Optional[int] = None,
        historical_plan_hash: Optional[int] = None,
        include_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Compare current and historical execution plans.

        Args:
            sql_id: SQL_ID to compare plans for
            current_plan_hash: Optional specific current plan hash
            historical_plan_hash: Optional specific historical plan hash
            include_recommendations: Whether to include recommendations

        Returns:
            Dictionary with comparison results
        """
        try:
            # Fetch current plan
            current_plan = self._fetch_current_plan(sql_id, current_plan_hash)

            # Fetch historical plan
            historical_plan = self._fetch_historical_plan(sql_id, historical_plan_hash)

            if not current_plan:
                return {
                    "comparison_possible": False,
                    "reason": f"Current plan not found for SQL_ID: {sql_id}",
                }

            if not historical_plan:
                return {
                    "comparison_possible": False,
                    "reason": f"Historical plan not found for SQL_ID: {sql_id}",
                }

            # Get metadata for both plans
            current_metadata = self._get_plan_metadata(
                sql_id, current_plan[0].get("plan_hash_value"), source="current"
            )
            historical_metadata = self._get_plan_metadata(
                sql_id, historical_plan[0].get("plan_hash_value"), source="historical"
            )

            # Perform comparison
            comparison_result = self.plan_comparator.compare_plans(
                current_plan=current_plan,
                historical_plan=historical_plan,
                current_metadata=current_metadata,
                historical_metadata=historical_metadata,
            )

            logger.info(
                f"Compared plans for SQL_ID: {sql_id} - "
                f"Regression detected: {comparison_result.get('regression_detected')}"
            )

            return comparison_result

        except Exception as e:
            logger.error(f"Error comparing plans: {e}", exc_info=True)
            raise

    def get_baseline_recommendation(
        self,
        sql_id: str,
        current_plan_hash: int,
        preferred_plan_hash: int,
    ) -> Dict[str, Any]:
        """
        Get SQL Plan Baseline recommendation.

        Args:
            sql_id: SQL_ID
            current_plan_hash: Current plan hash value
            preferred_plan_hash: Preferred plan hash value

        Returns:
            Baseline recommendation dictionary
        """
        try:
            # Fetch both plans for comparison
            current_plan = self._fetch_current_plan(sql_id, current_plan_hash)
            preferred_plan = self._fetch_historical_plan(sql_id, preferred_plan_hash)

            if not current_plan or not preferred_plan:
                return {
                    "recommend_baseline": False,
                    "priority": "none",
                    "reasons": ["Plans not found for comparison"],
                }

            # Perform comparison to analyze regression
            comparison_result = self.plan_comparator.compare_plans(
                current_plan=current_plan,
                historical_plan=preferred_plan,
            )

            # Get baseline recommendation
            recommendation = self.plan_comparator.recommend_plan_baseline(
                comparison_result=comparison_result,
                sql_id=sql_id,
            )

            logger.info(
                f"Generated baseline recommendation for SQL_ID: {sql_id} - "
                f"Recommend: {recommendation.get('recommend_baseline')}"
            )

            return recommendation

        except Exception as e:
            logger.error(f"Error generating baseline recommendation: {e}", exc_info=True)
            raise

    def _fetch_current_plan(
        self, sql_id: str, plan_hash_value: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch current plan from V$SQL_PLAN.

        Args:
            sql_id: SQL_ID
            plan_hash_value: Optional specific plan hash

        Returns:
            List of plan operations
        """
        try:
            if plan_hash_value:
                # Fetch specific plan
                plan = self.execution_plan_fetcher.fetch_plan_by_sql_id(
                    sql_id, plan_hash_value
                )
            else:
                # Fetch latest plan
                plan_history = self.execution_plan_fetcher.fetch_plan_history(sql_id)
                if plan_history:
                    latest_plan_hash = plan_history[0].get("plan_hash_value")
                    plan = self.execution_plan_fetcher.fetch_plan_by_sql_id(
                        sql_id, latest_plan_hash
                    )
                else:
                    plan = []

            return plan

        except Exception as e:
            logger.warning(f"Error fetching current plan: {e}")
            return []

    def _fetch_historical_plan(
        self, sql_id: str, plan_hash_value: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical plan from DBA_HIST_SQL_PLAN.

        Args:
            sql_id: SQL_ID
            plan_hash_value: Optional specific plan hash

        Returns:
            List of plan operations
        """
        try:
            if plan_hash_value:
                # Fetch specific historical plan
                plan = self.execution_plan_fetcher.fetch_historical_plan_by_sql_id(
                    sql_id, plan_hash_value
                )
            else:
                # Fetch most recent historical plan
                plan_versions = (
                    self.execution_plan_fetcher.fetch_historical_plan_versions(sql_id)
                )
                if plan_versions:
                    latest_plan_hash = plan_versions[0].get("plan_hash_value")
                    plan = self.execution_plan_fetcher.fetch_historical_plan_by_sql_id(
                        sql_id, latest_plan_hash
                    )
                else:
                    plan = []

            return plan

        except Exception as e:
            logger.warning(f"Error fetching historical plan: {e}")
            return []

    def _get_plan_metadata(
        self, sql_id: str, plan_hash_value: Optional[int], source: str
    ) -> Dict[str, Any]:
        """
        Get metadata for a plan.

        Args:
            sql_id: SQL_ID
            plan_hash_value: Plan hash value
            source: Data source ('current' or 'historical')

        Returns:
            Metadata dictionary
        """
        try:
            if source == "current":
                history = self.execution_plan_fetcher.fetch_plan_history(sql_id)
                matching = [
                    h for h in history if h.get("plan_hash_value") == plan_hash_value
                ]
                if matching:
                    return matching[0]

            elif source == "historical":
                versions = self.execution_plan_fetcher.fetch_historical_plan_versions(
                    sql_id
                )
                matching = [
                    v for v in versions if v.get("plan_hash_value") == plan_hash_value
                ]
                if matching:
                    return matching[0]

            return {}

        except Exception as e:
            logger.warning(f"Error fetching plan metadata: {e}")
            return {}
