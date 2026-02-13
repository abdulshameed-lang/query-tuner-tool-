"""Oracle wait event fetcher and analyzer.

This module provides functionality to fetch wait events from V$SESSION_WAIT
and V$ACTIVE_SESSION_HISTORY views.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class WaitEventFetcher:
    """Fetches wait events from Oracle system views."""

    # Wait event class categorization
    WAIT_EVENT_CATEGORIES = {
        "User I/O": "io",
        "System I/O": "io",
        "DB File": "io",
        "Direct path": "io",
        "log file": "io",
        "CPU": "cpu",
        "Concurrency": "concurrency",
        "Application": "application",
        "Configuration": "configuration",
        "Administrative": "administrative",
        "Network": "network",
        "Commit": "commit",
        "Idle": "idle",
        "Other": "other",
    }

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize WaitEventFetcher.

        Args:
            connection_manager: Oracle connection manager instance
        """
        self.connection_manager = connection_manager

    def fetch_wait_events_by_sql_id(
        self, sql_id: str, hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Fetch wait events for a specific SQL_ID from ASH.

        Args:
            sql_id: Oracle SQL_ID
            hours_back: Number of hours to look back (default 24)

        Returns:
            List of wait events with timing information
        """
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)

        query = """
            SELECT
                sql_id,
                sample_time,
                session_id,
                session_serial#,
                event,
                wait_class,
                wait_time,
                time_waited,
                p1text,
                p1,
                p2text,
                p2,
                p3text,
                p3,
                current_obj#,
                current_file#,
                current_block#,
                session_state,
                blocking_session,
                blocking_session_serial#,
                sql_plan_hash_value,
                sql_plan_line_id
            FROM v$active_session_history
            WHERE sql_id = :sql_id
              AND sample_time >= :start_time
              AND sample_time <= :end_time
            ORDER BY sample_time DESC
        """

        bind_params = {
            "sql_id": sql_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                wait_events = []
                for row in rows:
                    wait_event = dict(zip(columns, row))
                    wait_event = self._convert_oracle_types(wait_event)
                    # Add category
                    wait_event["category"] = self._categorize_wait_event(
                        wait_event.get("wait_class")
                    )
                    wait_events.append(wait_event)

                logger.info(
                    f"Fetched {len(wait_events)} wait events for SQL_ID: {sql_id}"
                )

                return wait_events

            finally:
                cursor.close()

    def fetch_current_wait_events(
        self, top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch current wait events from V$SESSION_WAIT.

        Args:
            top_n: Number of top wait events to return

        Returns:
            List of current wait events
        """
        query = """
            SELECT
                s.sid,
                s.serial#,
                s.username,
                s.program,
                s.sql_id,
                w.event,
                w.wait_class,
                w.state,
                w.wait_time,
                w.seconds_in_wait,
                w.p1text,
                w.p1,
                w.p2text,
                w.p2,
                w.p3text,
                w.p3
            FROM v$session s
            JOIN v$session_wait w ON s.sid = w.sid
            WHERE s.username IS NOT NULL
              AND w.wait_class != 'Idle'
            ORDER BY w.seconds_in_wait DESC
            FETCH FIRST :top_n ROWS ONLY
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"top_n": top_n})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                wait_events = []
                for row in rows:
                    wait_event = dict(zip(columns, row))
                    wait_event = self._convert_oracle_types(wait_event)
                    wait_event["category"] = self._categorize_wait_event(
                        wait_event.get("wait_class")
                    )
                    wait_events.append(wait_event)

                logger.info(f"Fetched {len(wait_events)} current wait events")

                return wait_events

            finally:
                cursor.close()

    def get_wait_event_summary(self, sql_id: str, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get aggregated wait event summary for a SQL_ID.

        Args:
            sql_id: Oracle SQL_ID
            hours_back: Number of hours to look back

        Returns:
            Dictionary with aggregated wait statistics
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)

        query = """
            SELECT
                event,
                wait_class,
                COUNT(*) as wait_count,
                SUM(time_waited) as total_time_waited,
                AVG(time_waited) as avg_time_waited,
                MAX(time_waited) as max_time_waited
            FROM v$active_session_history
            WHERE sql_id = :sql_id
              AND sample_time >= :start_time
              AND sample_time <= :end_time
              AND event IS NOT NULL
            GROUP BY event, wait_class
            ORDER BY total_time_waited DESC
        """

        bind_params = {
            "sql_id": sql_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                wait_summary = []
                total_time = 0

                for row in rows:
                    summary = dict(zip(columns, row))
                    summary = self._convert_oracle_types(summary)
                    summary["category"] = self._categorize_wait_event(
                        summary.get("wait_class")
                    )
                    wait_summary.append(summary)
                    total_time += summary.get("total_time_waited", 0) or 0

                # Calculate percentages
                for summary in wait_summary:
                    time_waited = summary.get("total_time_waited", 0) or 0
                    summary["percentage"] = (
                        (time_waited / total_time * 100) if total_time > 0 else 0
                    )

                logger.info(
                    f"Generated wait event summary for SQL_ID: {sql_id} "
                    f"({len(wait_summary)} event types)"
                )

                return {
                    "sql_id": sql_id,
                    "hours_back": hours_back,
                    "total_time_waited": total_time,
                    "event_count": len(wait_summary),
                    "events": wait_summary,
                }

            finally:
                cursor.close()

    def get_wait_event_timeline(
        self, sql_id: str, hours_back: int = 24, bucket_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get wait events grouped by time buckets for timeline visualization.

        Args:
            sql_id: Oracle SQL_ID
            hours_back: Number of hours to look back
            bucket_minutes: Size of time buckets in minutes

        Returns:
            List of time buckets with wait event data
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)

        query = """
            SELECT
                TRUNC(sample_time, 'MI') as sample_minute,
                wait_class,
                COUNT(*) as sample_count,
                SUM(time_waited) as total_time_waited
            FROM v$active_session_history
            WHERE sql_id = :sql_id
              AND sample_time >= :start_time
              AND sample_time <= :end_time
              AND event IS NOT NULL
            GROUP BY TRUNC(sample_time, 'MI'), wait_class
            ORDER BY sample_minute, wait_class
        """

        bind_params = {
            "sql_id": sql_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                timeline = []
                for row in rows:
                    bucket = dict(zip(columns, row))
                    bucket = self._convert_oracle_types(bucket)
                    bucket["category"] = self._categorize_wait_event(
                        bucket.get("wait_class")
                    )
                    timeline.append(bucket)

                logger.info(
                    f"Generated wait event timeline for SQL_ID: {sql_id} "
                    f"({len(timeline)} time buckets)"
                )

                return timeline

            finally:
                cursor.close()

    def get_blocking_sessions(self, sql_id: str) -> List[Dict[str, Any]]:
        """
        Get sessions blocking the given SQL_ID.

        Args:
            sql_id: Oracle SQL_ID

        Returns:
            List of blocking sessions
        """
        query = """
            SELECT DISTINCT
                ash.blocking_session,
                ash.blocking_session_serial#,
                s.username as blocking_username,
                s.program as blocking_program,
                s.sql_id as blocking_sql_id,
                ash.event,
                COUNT(*) as block_count
            FROM v$active_session_history ash
            JOIN v$session s ON ash.blocking_session = s.sid
            WHERE ash.sql_id = :sql_id
              AND ash.blocking_session IS NOT NULL
              AND ash.sample_time >= SYSDATE - INTERVAL '1' HOUR
            GROUP BY
                ash.blocking_session,
                ash.blocking_session_serial#,
                s.username,
                s.program,
                s.sql_id,
                ash.event
            ORDER BY block_count DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"sql_id": sql_id})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                blocking_sessions = []
                for row in rows:
                    session = dict(zip(columns, row))
                    session = self._convert_oracle_types(session)
                    blocking_sessions.append(session)

                return blocking_sessions

            finally:
                cursor.close()

    def _categorize_wait_event(self, wait_class: Optional[str]) -> str:
        """
        Categorize wait event by wait class.

        Args:
            wait_class: Oracle wait class

        Returns:
            Simplified category name
        """
        if not wait_class:
            return "other"

        for key, category in self.WAIT_EVENT_CATEGORIES.items():
            if key.lower() in wait_class.lower():
                return category

        return "other"

    def _convert_oracle_types(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Oracle-specific types to Python types.

        Args:
            row_dict: Dictionary with Oracle types

        Returns:
            Dictionary with converted types
        """
        converted = {}
        for key, value in row_dict.items():
            # Handle LOB objects
            if hasattr(value, "read"):
                try:
                    converted[key] = value.read()
                except Exception as e:
                    logger.warning(f"Failed to read LOB for {key}: {e}")
                    converted[key] = None
            # Handle datetime objects
            elif isinstance(value, datetime):
                converted[key] = value.isoformat()
            # Handle None/NULL
            elif value is None:
                converted[key] = None
            else:
                converted[key] = value

        return converted
