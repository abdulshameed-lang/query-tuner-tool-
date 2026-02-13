"""Bug detection service layer."""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.oracle.connection import get_connection_manager
from app.core.oracle.queries import QueryFetcher
from app.core.oracle.execution_plans import ExecutionPlanFetcher
from app.core.analysis.bug_detector import BugDetector
from app.core.oracle.bug_patterns import BugPatternDatabase

logger = logging.getLogger(__name__)


class BugDetectionService:
    """Service for detecting Oracle bugs."""

    def __init__(self):
        """Initialize BugDetectionService."""
        self.connection_manager = get_connection_manager()
        self.query_fetcher = QueryFetcher(self.connection_manager)
        self.execution_plan_fetcher = ExecutionPlanFetcher(self.connection_manager)
        self.bug_detector = BugDetector()
        self.bug_db = BugPatternDatabase()

    def detect_bugs_for_query(
        self, sql_id: str, database_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect bugs for a specific SQL_ID.

        Args:
            sql_id: SQL_ID to analyze
            database_version: Optional database version

        Returns:
            Dictionary with detected bugs and summary
        """
        try:
            # Fetch query information
            query = self.query_fetcher.fetch_query_by_sql_id(sql_id)
            if not query:
                return {
                    "sql_id": sql_id,
                    "detected_bugs": [],
                    "summary": self._create_empty_summary(),
                    "database_version": database_version,
                    "detection_timestamp": datetime.utcnow().isoformat(),
                    "error": "Query not found",
                }

            # Fetch execution plan
            plan_operations = self.execution_plan_fetcher.fetch_plan_by_sql_id(sql_id)

            # Prepare query metrics
            query_metrics = {
                "executions": query.get("executions"),
                "parse_calls": query.get("parse_calls"),
                "buffer_gets": query.get("buffer_gets"),
                "disk_reads": query.get("disk_reads"),
                "version_count": query.get("version_count"),
            }

            # Detect bugs
            detected_bugs = self.bug_detector.detect_bugs(
                sql_id=sql_id,
                sql_text=query.get("sql_fulltext"),
                plan_operations=plan_operations,
                query_metrics=query_metrics,
                database_version=database_version,
            )

            # Generate summary
            summary = self.bug_detector.get_detection_summary(detected_bugs)

            logger.info(f"Detected {len(detected_bugs)} bugs for SQL_ID: {sql_id}")

            return {
                "sql_id": sql_id,
                "detected_bugs": detected_bugs,
                "summary": summary,
                "database_version": database_version,
                "detection_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error detecting bugs: {e}", exc_info=True)
            raise

    def get_all_bugs(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all bugs with optional filters.

        Args:
            category: Filter by category
            severity: Filter by severity
            version: Filter by affected version

        Returns:
            Dictionary with bugs and metadata
        """
        bugs = self.bug_db.get_all_bugs()

        # Apply filters
        if category:
            bugs = [b for b in bugs if b["category"] == category]
        if severity:
            bugs = [b for b in bugs if b["severity"] == severity]
        if version:
            bugs = [
                b for b in bugs
                if self.bug_db._version_affected(version, b.get("affected_versions", []))
            ]

        return {
            "bugs": bugs,
            "total_count": len(bugs),
            "filters_applied": {
                "category": category,
                "severity": severity,
                "version": version,
            },
        }

    def check_version_bugs(self, database_version: str) -> Dict[str, Any]:
        """
        Check bugs affecting a specific database version.

        Args:
            database_version: Oracle database version

        Returns:
            Dictionary with bugs and recommendation
        """
        bugs = self.bug_db.get_bugs_by_version(database_version)
        critical_bugs = [b for b in bugs if b["severity"] == "critical"]

        # Generate recommendation
        if len(critical_bugs) > 0:
            recommendation = (
                f"CRITICAL: {len(critical_bugs)} critical bugs affect version {database_version}. "
                "Immediate patching or upgrade recommended."
            )
        elif len(bugs) > 5:
            recommendation = (
                f"WARNING: {len(bugs)} known bugs affect version {database_version}. "
                "Consider upgrading to a newer version."
            )
        elif len(bugs) > 0:
            recommendation = (
                f"INFO: {len(bugs)} known bugs affect version {database_version}. "
                "Review bugs and apply patches as needed."
            )
        else:
            recommendation = f"No known bugs in database for version {database_version}."

        return {
            "database_version": database_version,
            "bugs_affecting_version": bugs,
            "total_count": len(bugs),
            "critical_count": len(critical_bugs),
            "recommendation": recommendation,
        }

    def _create_empty_summary(self) -> Dict[str, Any]:
        """Create empty detection summary."""
        return {
            "total_bugs": 0,
            "by_severity": {},
            "by_category": {},
            "high_confidence_count": 0,
            "critical_count": 0,
        }
