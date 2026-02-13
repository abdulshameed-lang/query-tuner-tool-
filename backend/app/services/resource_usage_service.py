"""Resource usage and session analysis service.

This module provides business logic for analyzing user resource consumption
and session activity.
"""

from typing import List, Dict, Any, Optional
import logging

from app.core.oracle.system_views import SystemViewsFetcher
from app.core.oracle.connection import get_connection_manager

logger = logging.getLogger(__name__)


class ResourceUsageService:
    """Service for resource usage and session analysis."""

    def __init__(self):
        """Initialize ResourceUsageService."""
        self.connection_manager = get_connection_manager()
        self.system_views_fetcher = SystemViewsFetcher(self.connection_manager)

    def get_users_with_resource_usage(
        self, exclude_system: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all users with aggregated resource usage.

        Args:
            exclude_system: Exclude system schemas

        Returns:
            List of users with resource metrics and rankings
        """
        users = self.system_views_fetcher.fetch_user_resource_usage(
            username=None, exclude_system=exclude_system
        )

        # Calculate rankings and add metadata
        for i, user in enumerate(users):
            user["rank"] = i + 1
            user["resource_score"] = self._calculate_resource_score(user)
            user["risk_level"] = self._assess_risk_level(user)

        return users

    def get_user_details(
        self, username: str, top_queries: int = 20
    ) -> Dict[str, Any]:
        """
        Get detailed resource usage for a specific user.

        Args:
            username: Username to analyze
            top_queries: Number of top queries to include

        Returns:
            Dictionary with user details and resource usage
        """
        # Get user resource summary
        user_data = self.system_views_fetcher.fetch_user_resource_usage(
            username=username, exclude_system=False
        )

        if not user_data:
            return {}

        user = user_data[0]

        # Get user's active sessions
        all_sessions = self.system_views_fetcher.fetch_active_sessions(
            exclude_system=False, include_background=False
        )
        user_sessions = [s for s in all_sessions if s.get("username") == username.upper()]

        # Get user's top queries
        top_queries_list = self.system_views_fetcher.fetch_user_queries(
            username, top_n=top_queries
        )

        # Calculate statistics
        user["resource_score"] = self._calculate_resource_score(user)
        user["risk_level"] = self._assess_risk_level(user)
        user["sessions"] = user_sessions
        user["top_queries"] = top_queries_list
        user["avg_query_time"] = self._calculate_avg_query_time(top_queries_list)

        return user

    def get_active_sessions_analysis(
        self, exclude_system: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive analysis of active sessions.

        Args:
            exclude_system: Exclude system schema sessions

        Returns:
            Dictionary with session analysis
        """
        sessions = self.system_views_fetcher.fetch_active_sessions(
            exclude_system=exclude_system, include_background=False
        )

        # Categorize sessions
        active = [s for s in sessions if s.get("status") == "ACTIVE"]
        inactive = [s for s in sessions if s.get("status") == "INACTIVE"]
        waiting = [s for s in sessions if s.get("wait_class") and s.get("wait_class") != "Idle"]
        blocked = [s for s in sessions if s.get("blocking_session") is not None]

        # Get long-running sessions
        long_running = self.system_views_fetcher.fetch_long_running_sessions(
            threshold_seconds=300  # 5 minutes
        )

        # Identify problematic sessions
        problematic = self._identify_problematic_sessions(sessions)

        return {
            "total_sessions": len(sessions),
            "active_sessions": len(active),
            "inactive_sessions": len(inactive),
            "waiting_sessions": len(waiting),
            "blocked_sessions": len(blocked),
            "long_running_sessions": len(long_running),
            "problematic_sessions": len(problematic),
            "sessions": sessions,
            "long_running": long_running[:10],  # Top 10
            "problematic": problematic[:10],  # Top 10
            "by_status": self._aggregate_by_status(sessions),
            "by_wait_class": self._aggregate_by_wait_class(waiting),
        }

    def get_session_details(
        self, sid: int, serial: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific session.

        Args:
            sid: Session ID
            serial: Session serial number

        Returns:
            Dictionary with session details and statistics
        """
        session = self.system_views_fetcher.fetch_session_by_sid(sid, serial)

        if not session:
            return {}

        # Get session statistics
        statistics = self.system_views_fetcher.fetch_session_statistics(sid)

        # Categorize statistics
        categorized_stats = self._categorize_statistics(statistics)

        session["statistics"] = categorized_stats
        session["total_statistics"] = len(statistics)
        session["risk_level"] = self._assess_session_risk(session)

        return session

    def _calculate_resource_score(self, user: Dict[str, Any]) -> float:
        """
        Calculate resource consumption score for a user.

        Args:
            user: User resource data

        Returns:
            Resource score (0-100)
        """
        try:
            # Weighted scoring
            cpu_score = min((user.get("total_cpu_time", 0) or 0) / 1000000, 100) * 0.4
            logical_score = min((user.get("total_logical_reads", 0) or 0) / 10000000, 100) * 0.3
            physical_score = min((user.get("total_physical_reads", 0) or 0) / 1000000, 100) * 0.2
            session_score = min((user.get("active_sessions", 0) or 0) / 10, 100) * 0.1

            return round(cpu_score + logical_score + physical_score + session_score, 2)
        except Exception as e:
            logger.warning(f"Failed to calculate resource score: {e}")
            return 0.0

    def _assess_risk_level(self, user: Dict[str, Any]) -> str:
        """
        Assess risk level based on resource usage patterns.

        Args:
            user: User resource data

        Returns:
            Risk level (low, medium, high, critical)
        """
        score = self._calculate_resource_score(user)
        blocked = user.get("blocked_count", 0) or 0
        max_duration = user.get("max_session_duration", 0) or 0

        if score > 75 or blocked > 5 or max_duration > 3600:
            return "critical"
        elif score > 50 or blocked > 2 or max_duration > 1800:
            return "high"
        elif score > 25 or blocked > 0 or max_duration > 600:
            return "medium"
        else:
            return "low"

    def _assess_session_risk(self, session: Dict[str, Any]) -> str:
        """
        Assess risk level for a specific session.

        Args:
            session: Session data

        Returns:
            Risk level (low, medium, high, critical)
        """
        duration = session.get("last_call_et", 0) or 0
        is_blocked = session.get("blocking_session") is not None
        is_active = session.get("status") == "ACTIVE"

        if duration > 3600 or (is_blocked and is_active):
            return "critical"
        elif duration > 1800 or is_blocked:
            return "high"
        elif duration > 600:
            return "medium"
        else:
            return "low"

    def _calculate_avg_query_time(self, queries: List[Dict[str, Any]]) -> float:
        """
        Calculate average query elapsed time.

        Args:
            queries: List of queries

        Returns:
            Average elapsed time in microseconds
        """
        if not queries:
            return 0.0

        total_time = sum(q.get("elapsed_time", 0) or 0 for q in queries)
        return round(total_time / len(queries), 2)

    def _identify_problematic_sessions(
        self, sessions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify sessions with potential issues.

        Args:
            sessions: List of all sessions

        Returns:
            List of problematic sessions
        """
        problematic = []

        for session in sessions:
            issues = []

            # Long running
            duration = session.get("last_call_et", 0) or 0
            if duration > 600:  # 10 minutes
                issues.append("long_running")

            # Blocked
            if session.get("blocking_session") is not None:
                issues.append("blocked")

            # High wait time
            wait_time = session.get("seconds_in_wait", 0) or 0
            if wait_time > 300:  # 5 minutes
                issues.append("high_wait_time")

            # Inactive with open transaction
            if session.get("status") == "INACTIVE" and duration > 300:
                issues.append("inactive_with_transaction")

            if issues:
                session["issues"] = issues
                session["issue_count"] = len(issues)
                problematic.append(session)

        # Sort by issue count and duration
        problematic.sort(
            key=lambda x: (x.get("issue_count", 0), x.get("last_call_et", 0)),
            reverse=True
        )

        return problematic

    def _aggregate_by_status(
        self, sessions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Aggregate sessions by status.

        Args:
            sessions: List of sessions

        Returns:
            Dictionary of status counts
        """
        status_counts = {}
        for session in sessions:
            status = session.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts

    def _aggregate_by_wait_class(
        self, sessions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Aggregate waiting sessions by wait class.

        Args:
            sessions: List of waiting sessions

        Returns:
            Dictionary of wait class counts
        """
        wait_counts = {}
        for session in sessions:
            wait_class = session.get("wait_class", "Other")
            if wait_class and wait_class != "Idle":
                wait_counts[wait_class] = wait_counts.get(wait_class, 0) + 1

        return wait_counts

    def _categorize_statistics(
        self, statistics: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize session statistics by type.

        Args:
            statistics: List of session statistics

        Returns:
            Dictionary of categorized statistics
        """
        categories = {
            "cpu": [],
            "io": [],
            "memory": [],
            "parse": [],
            "execute": [],
            "other": [],
        }

        for stat in statistics:
            name = stat.get("statistic_name", "").lower()

            if "cpu" in name:
                categories["cpu"].append(stat)
            elif any(keyword in name for keyword in ["read", "write", "physical", "logical"]):
                categories["io"].append(stat)
            elif "memory" in name or "pga" in name or "uga" in name:
                categories["memory"].append(stat)
            elif "parse" in name:
                categories["parse"].append(stat)
            elif "execute" in name:
                categories["execute"].append(stat)
            else:
                categories["other"].append(stat)

        return categories
