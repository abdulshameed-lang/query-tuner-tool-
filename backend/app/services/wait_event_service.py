"""Wait event analysis service.

This module provides business logic for analyzing Oracle wait events.
"""

from typing import List, Dict, Any, Optional
import logging
from collections import defaultdict

from app.core.oracle.wait_events import WaitEventFetcher
from app.core.oracle.connection import get_connection_manager

logger = logging.getLogger(__name__)


class WaitEventService:
    """Service for wait event analysis and categorization."""

    # Category display names and colors
    CATEGORY_INFO = {
        "cpu": {"name": "CPU", "color": "#ff4d4f", "priority": 1},
        "io": {"name": "I/O", "color": "#1890ff", "priority": 2},
        "concurrency": {"name": "Concurrency", "color": "#faad14", "priority": 3},
        "application": {"name": "Application", "color": "#52c41a", "priority": 4},
        "network": {"name": "Network", "color": "#722ed1", "priority": 5},
        "commit": {"name": "Commit", "color": "#13c2c2", "priority": 6},
        "configuration": {"name": "Configuration", "color": "#eb2f96", "priority": 7},
        "administrative": {"name": "Administrative", "color": "#8c8c8c", "priority": 8},
        "idle": {"name": "Idle", "color": "#d9d9d9", "priority": 9},
        "other": {"name": "Other", "color": "#bfbfbf", "priority": 10},
    }

    def __init__(self):
        """Initialize WaitEventService."""
        self.connection_manager = get_connection_manager()
        self.wait_event_fetcher = WaitEventFetcher(self.connection_manager)

    def get_wait_events_for_query(
        self, sql_id: str, hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive wait event analysis for a query.

        Args:
            sql_id: Oracle SQL_ID
            hours_back: Number of hours to look back

        Returns:
            Dictionary with wait events, summary, and analysis
        """
        # Fetch raw wait events
        wait_events = self.wait_event_fetcher.fetch_wait_events_by_sql_id(
            sql_id, hours_back
        )

        # Get summary
        summary = self.wait_event_fetcher.get_wait_event_summary(sql_id, hours_back)

        # Get timeline
        timeline = self.wait_event_fetcher.get_wait_event_timeline(
            sql_id, hours_back, bucket_minutes=5
        )

        # Get blocking sessions
        blocking = self.wait_event_fetcher.get_blocking_sessions(sql_id)

        # Aggregate by category
        category_breakdown = self._aggregate_by_category(summary.get("events", []))

        # Identify top wait events
        top_events = self._get_top_wait_events(summary.get("events", []), top_n=10)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            category_breakdown, top_events, blocking
        )

        return {
            "sql_id": sql_id,
            "hours_back": hours_back,
            "total_time_waited": summary.get("total_time_waited", 0),
            "total_samples": len(wait_events),
            "wait_events": wait_events[:100],  # Limit to 100 most recent
            "category_breakdown": category_breakdown,
            "top_events": top_events,
            "timeline": timeline,
            "blocking_sessions": blocking,
            "recommendations": recommendations,
        }

    def get_current_system_wait_events(self, top_n: int = 50) -> Dict[str, Any]:
        """
        Get current wait events across the system.

        Args:
            top_n: Number of top wait events to return

        Returns:
            Dictionary with current wait events and breakdown
        """
        # Fetch current wait events
        wait_events = self.wait_event_fetcher.fetch_current_wait_events(top_n)

        # Aggregate by category
        category_breakdown = self._aggregate_current_events_by_category(wait_events)

        # Group by SQL_ID
        sql_id_breakdown = self._aggregate_by_sql_id(wait_events)

        return {
            "timestamp": None,  # Will be set by API
            "total_sessions": len(wait_events),
            "wait_events": wait_events,
            "category_breakdown": category_breakdown,
            "sql_id_breakdown": sql_id_breakdown,
        }

    def _aggregate_by_category(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate wait events by category.

        Args:
            events: List of wait event summaries

        Returns:
            List of category aggregations
        """
        category_totals = defaultdict(
            lambda: {"total_time": 0, "wait_count": 0, "event_types": 0}
        )

        for event in events:
            category = event.get("category", "other")
            category_totals[category]["total_time"] += event.get(
                "total_time_waited", 0
            ) or 0
            category_totals[category]["wait_count"] += event.get("wait_count", 0) or 0
            category_totals[category]["event_types"] += 1

        # Calculate total time for percentages
        total_time = sum(cat["total_time"] for cat in category_totals.values())

        # Convert to list with metadata
        result = []
        for category, data in category_totals.items():
            cat_info = self.CATEGORY_INFO.get(category, self.CATEGORY_INFO["other"])
            result.append(
                {
                    "category": category,
                    "name": cat_info["name"],
                    "color": cat_info["color"],
                    "total_time_waited": data["total_time"],
                    "wait_count": data["wait_count"],
                    "event_types": data["event_types"],
                    "percentage": (
                        (data["total_time"] / total_time * 100) if total_time > 0 else 0
                    ),
                }
            )

        # Sort by total time descending
        result.sort(key=lambda x: x["total_time_waited"], reverse=True)

        return result

    def _aggregate_current_events_by_category(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate current wait events by category.

        Args:
            events: List of current wait events

        Returns:
            List of category aggregations
        """
        category_totals = defaultdict(lambda: {"session_count": 0, "total_wait_time": 0})

        for event in events:
            category = event.get("category", "other")
            category_totals[category]["session_count"] += 1
            category_totals[category]["total_wait_time"] += event.get(
                "seconds_in_wait", 0
            ) or 0

        # Convert to list with metadata
        result = []
        for category, data in category_totals.items():
            cat_info = self.CATEGORY_INFO.get(category, self.CATEGORY_INFO["other"])
            result.append(
                {
                    "category": category,
                    "name": cat_info["name"],
                    "color": cat_info["color"],
                    "session_count": data["session_count"],
                    "total_wait_time": data["total_wait_time"],
                }
            )

        # Sort by session count descending
        result.sort(key=lambda x: x["session_count"], reverse=True)

        return result

    def _aggregate_by_sql_id(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate current wait events by SQL_ID.

        Args:
            events: List of current wait events

        Returns:
            List of SQL_ID aggregations
        """
        sql_id_totals = defaultdict(lambda: {"session_count": 0, "events": []})

        for event in events:
            sql_id = event.get("sql_id")
            if sql_id:
                sql_id_totals[sql_id]["session_count"] += 1
                sql_id_totals[sql_id]["events"].append(event.get("event"))

        # Convert to list
        result = []
        for sql_id, data in sql_id_totals.items():
            result.append(
                {
                    "sql_id": sql_id,
                    "session_count": data["session_count"],
                    "events": list(set(data["events"])),  # Unique events
                }
            )

        # Sort by session count descending
        result.sort(key=lambda x: x["session_count"], reverse=True)

        return result[:10]  # Top 10 SQL_IDs

    def _get_top_wait_events(
        self, events: List[Dict[str, Any]], top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top wait events by time waited.

        Args:
            events: List of wait event summaries
            top_n: Number of top events to return

        Returns:
            List of top wait events
        """
        # Sort by total_time_waited descending
        sorted_events = sorted(
            events, key=lambda x: x.get("total_time_waited", 0) or 0, reverse=True
        )

        return sorted_events[:top_n]

    def _generate_recommendations(
        self,
        category_breakdown: List[Dict[str, Any]],
        top_events: List[Dict[str, Any]],
        blocking_sessions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on wait event patterns.

        Args:
            category_breakdown: Wait events by category
            top_events: Top wait events
            blocking_sessions: Blocking sessions

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for high I/O waits
        io_category = next(
            (cat for cat in category_breakdown if cat["category"] == "io"), None
        )
        if io_category and io_category["percentage"] > 30:
            recommendations.append(
                {
                    "type": "io_optimization",
                    "priority": "high",
                    "message": f"High I/O wait detected ({io_category['percentage']:.1f}% of total time)",
                    "suggestions": [
                        "Review disk I/O patterns and consider SSD storage",
                        "Check for missing indexes causing full table scans",
                        "Analyze if data can be partitioned for better I/O",
                        "Consider increasing db_file_multiblock_read_count",
                    ],
                }
            )

        # Check for CPU bottlenecks
        cpu_category = next(
            (cat for cat in category_breakdown if cat["category"] == "cpu"), None
        )
        if cpu_category and cpu_category["percentage"] > 40:
            recommendations.append(
                {
                    "type": "cpu_optimization",
                    "priority": "high",
                    "message": f"High CPU usage detected ({cpu_category['percentage']:.1f}% of total time)",
                    "suggestions": [
                        "Review query execution plans for inefficient operations",
                        "Consider adding indexes to reduce CPU overhead",
                        "Optimize SQL with excessive function calls",
                        "Check for queries with high parse counts",
                    ],
                }
            )

        # Check for concurrency issues
        concurrency_category = next(
            (cat for cat in category_breakdown if cat["category"] == "concurrency"),
            None,
        )
        if concurrency_category and concurrency_category["percentage"] > 20:
            recommendations.append(
                {
                    "type": "concurrency_optimization",
                    "priority": "medium",
                    "message": f"Concurrency waits detected ({concurrency_category['percentage']:.1f}% of total time)",
                    "suggestions": [
                        "Review locking mechanisms and transaction isolation levels",
                        "Consider shorter transactions to reduce lock duration",
                        "Analyze blocking sessions and optimize lock ordering",
                        "Review use of SELECT FOR UPDATE statements",
                    ],
                }
            )

        # Check for blocking sessions
        if blocking_sessions:
            recommendations.append(
                {
                    "type": "blocking_sessions",
                    "priority": "high",
                    "message": f"Found {len(blocking_sessions)} blocking session(s)",
                    "suggestions": [
                        "Identify and optimize long-running transactions",
                        "Review application logic for proper commit frequency",
                        "Consider using NOWAIT or SKIP LOCKED clauses",
                        "Monitor for deadlock scenarios",
                    ],
                    "blocking_sessions": blocking_sessions,
                }
            )

        # Check specific wait events
        for event in top_events[:3]:  # Top 3 events
            event_name = event.get("event", "").lower()

            if "direct path" in event_name and event.get("percentage", 0) > 15:
                recommendations.append(
                    {
                        "type": "direct_path_optimization",
                        "priority": "medium",
                        "message": f"High direct path I/O wait: {event.get('event')}",
                        "suggestions": [
                            "Review direct path operations (parallel queries, CTAS, bulk loads)",
                            "Consider tuning parallel execution parameters",
                            "Check if temporary tablespace is appropriately sized",
                        ],
                    }
                )

            if "log file sync" in event_name and event.get("percentage", 0) > 10:
                recommendations.append(
                    {
                        "type": "commit_optimization",
                        "priority": "medium",
                        "message": f"High log file sync wait: {event.get('event')}",
                        "suggestions": [
                            "Reduce commit frequency in application",
                            "Use batch commits where possible",
                            "Check redo log configuration and disk I/O",
                            "Consider COMMIT NOWAIT if appropriate",
                        ],
                    }
                )

        return recommendations
