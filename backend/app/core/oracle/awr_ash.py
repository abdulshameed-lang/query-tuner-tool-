"""AWR and ASH data fetcher module.

This module provides access to Oracle Automatic Workload Repository (AWR)
and Active Session History (ASH) data for historical performance analysis.

Note: AWR and ASH require Oracle Diagnostics Pack license.
This module implements graceful degradation if license is not available.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import oracledb

from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class AWRASHFetcher:
    """Fetcher for AWR and ASH historical data."""

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize AWRASHFetcher.

        Args:
            connection_manager: Oracle connection manager
        """
        self.connection_manager = connection_manager
        self._awr_available = None
        self._ash_available = None

    def check_awr_availability(self) -> bool:
        """
        Check if AWR data is available (requires Diagnostics Pack license).

        Returns:
            True if AWR is available, False otherwise
        """
        if self._awr_available is not None:
            return self._awr_available

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            # Check if DBA_HIST_SNAPSHOT exists and has data
            query = """
                SELECT COUNT(*)
                FROM dba_hist_snapshot
                WHERE ROWNUM = 1
            """

            cursor.execute(query)
            result = cursor.fetchone()

            self._awr_available = result and result[0] > 0

            cursor.close()
            logger.info(f"AWR availability check: {self._awr_available}")

            return self._awr_available

        except Exception as e:
            logger.warning(f"AWR not available: {e}")
            self._awr_available = False
            return False

    def check_ash_availability(self) -> bool:
        """
        Check if ASH data is available (requires Diagnostics Pack license).

        Returns:
            True if ASH is available, False otherwise
        """
        if self._ash_available is not None:
            return self._ash_available

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            # Check if DBA_HIST_ACTIVE_SESS_HISTORY exists and has data
            query = """
                SELECT COUNT(*)
                FROM dba_hist_active_sess_history
                WHERE ROWNUM = 1
            """

            cursor.execute(query)
            result = cursor.fetchone()

            self._ash_available = result and result[0] > 0

            cursor.close()
            logger.info(f"ASH availability check: {self._ash_available}")

            return self._ash_available

        except Exception as e:
            logger.warning(f"ASH not available: {e}")
            self._ash_available = False
            return False

    def fetch_snapshots(
        self,
        days_back: int = 7,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch AWR snapshots.

        Args:
            days_back: Number of days to look back
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot information
        """
        if not self.check_awr_availability():
            logger.warning("AWR not available, returning empty snapshot list")
            return []

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    snap_id,
                    dbid,
                    instance_number,
                    begin_interval_time,
                    end_interval_time,
                    startup_time,
                    snap_level
                FROM dba_hist_snapshot
                WHERE begin_interval_time >= SYSDATE - :days_back
                ORDER BY snap_id DESC
            """

            if limit:
                query = f"SELECT * FROM ({query}) WHERE ROWNUM <= :limit"
                cursor.execute(query, days_back=days_back, limit=limit)
            else:
                cursor.execute(query, days_back=days_back)

            columns = [col[0].lower() for col in cursor.description]
            snapshots = []

            for row in cursor:
                snapshot = dict(zip(columns, row))
                # Convert datetime objects to ISO format
                for key in ['begin_interval_time', 'end_interval_time', 'startup_time']:
                    if key in snapshot and snapshot[key]:
                        snapshot[key] = snapshot[key].isoformat()
                snapshots.append(snapshot)

            cursor.close()
            logger.info(f"Fetched {len(snapshots)} AWR snapshots")

            return snapshots

        except Exception as e:
            logger.error(f"Error fetching AWR snapshots: {e}", exc_info=True)
            raise

    def fetch_historical_sql_stats(
        self,
        sql_id: str,
        begin_snap_id: Optional[int] = None,
        end_snap_id: Optional[int] = None,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical SQL statistics from AWR.

        Args:
            sql_id: SQL_ID to fetch statistics for
            begin_snap_id: Beginning snapshot ID
            end_snap_id: Ending snapshot ID
            days_back: Number of days to look back if snap IDs not provided

        Returns:
            List of historical SQL statistics
        """
        if not self.check_awr_availability():
            logger.warning("AWR not available, returning empty statistics")
            return []

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            if begin_snap_id and end_snap_id:
                query = """
                    SELECT
                        s.snap_id,
                        s.instance_number,
                        sn.begin_interval_time,
                        sn.end_interval_time,
                        s.plan_hash_value,
                        s.executions_delta,
                        s.elapsed_time_delta / 1000000 as elapsed_time_sec,
                        s.cpu_time_delta / 1000000 as cpu_time_sec,
                        s.buffer_gets_delta,
                        s.disk_reads_delta,
                        s.rows_processed_delta,
                        s.parse_calls_delta,
                        s.version_count
                    FROM dba_hist_sqlstat s
                    JOIN dba_hist_snapshot sn ON s.snap_id = sn.snap_id
                        AND s.instance_number = sn.instance_number
                    WHERE s.sql_id = :sql_id
                        AND s.snap_id BETWEEN :begin_snap_id AND :end_snap_id
                    ORDER BY s.snap_id
                """
                cursor.execute(query, sql_id=sql_id, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id)
            else:
                query = """
                    SELECT
                        s.snap_id,
                        s.instance_number,
                        sn.begin_interval_time,
                        sn.end_interval_time,
                        s.plan_hash_value,
                        s.executions_delta,
                        s.elapsed_time_delta / 1000000 as elapsed_time_sec,
                        s.cpu_time_delta / 1000000 as cpu_time_sec,
                        s.buffer_gets_delta,
                        s.disk_reads_delta,
                        s.rows_processed_delta,
                        s.parse_calls_delta,
                        s.version_count
                    FROM dba_hist_sqlstat s
                    JOIN dba_hist_snapshot sn ON s.snap_id = sn.snap_id
                        AND s.instance_number = sn.instance_number
                    WHERE s.sql_id = :sql_id
                        AND sn.begin_interval_time >= SYSDATE - :days_back
                    ORDER BY s.snap_id
                """
                cursor.execute(query, sql_id=sql_id, days_back=days_back)

            columns = [col[0].lower() for col in cursor.description]
            stats = []

            for row in cursor:
                stat = dict(zip(columns, row))
                # Convert datetime objects
                for key in ['begin_interval_time', 'end_interval_time']:
                    if key in stat and stat[key]:
                        stat[key] = stat[key].isoformat()
                stats.append(stat)

            cursor.close()
            logger.info(f"Fetched {len(stats)} historical statistics for SQL_ID: {sql_id}")

            return stats

        except Exception as e:
            logger.error(f"Error fetching historical SQL stats: {e}", exc_info=True)
            raise

    def fetch_historical_execution_plan(
        self,
        sql_id: str,
        plan_hash_value: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical execution plan from AWR.

        Args:
            sql_id: SQL_ID
            plan_hash_value: Plan hash value

        Returns:
            List of plan operations
        """
        if not self.check_awr_availability():
            logger.warning("AWR not available, returning empty plan")
            return []

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    id,
                    parent_id,
                    operation,
                    options,
                    object_owner,
                    object_name,
                    object_type,
                    cost,
                    cardinality,
                    bytes,
                    cpu_cost,
                    io_cost,
                    access_predicates,
                    filter_predicates,
                    partition_start,
                    partition_stop
                FROM dba_hist_sql_plan
                WHERE sql_id = :sql_id
                    AND plan_hash_value = :plan_hash_value
                ORDER BY id
            """

            cursor.execute(query, sql_id=sql_id, plan_hash_value=plan_hash_value)

            columns = [col[0].lower() for col in cursor.description]
            operations = []

            for row in cursor:
                operation = dict(zip(columns, row))
                operations.append(operation)

            cursor.close()
            logger.info(f"Fetched historical plan for SQL_ID: {sql_id}, PHV: {plan_hash_value}")

            return operations

        except Exception as e:
            logger.error(f"Error fetching historical execution plan: {e}", exc_info=True)
            raise

    def fetch_ash_activity(
        self,
        sql_id: Optional[str] = None,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch Active Session History samples.

        Args:
            sql_id: Optional SQL_ID filter
            begin_time: Start time for samples
            end_time: End time for samples
            limit: Maximum number of samples to return

        Returns:
            List of ASH samples
        """
        if not self.check_ash_availability():
            logger.warning("ASH not available, returning empty samples")
            return []

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            # Build query with optional filters
            query = """
                SELECT
                    sample_id,
                    sample_time,
                    session_id,
                    session_serial#,
                    sql_id,
                    sql_plan_hash_value,
                    event,
                    wait_class,
                    wait_time,
                    time_waited,
                    session_state,
                    session_type,
                    blocking_session,
                    current_obj#,
                    program,
                    module
                FROM dba_hist_active_sess_history
                WHERE 1=1
            """

            params = {}

            if sql_id:
                query += " AND sql_id = :sql_id"
                params['sql_id'] = sql_id

            if begin_time:
                query += " AND sample_time >= :begin_time"
                params['begin_time'] = begin_time

            if end_time:
                query += " AND sample_time <= :end_time"
                params['end_time'] = end_time

            query += " ORDER BY sample_time DESC"

            # Apply limit
            query = f"SELECT * FROM ({query}) WHERE ROWNUM <= :limit"
            params['limit'] = limit

            cursor.execute(query, **params)

            columns = [col[0].lower() for col in cursor.description]
            samples = []

            for row in cursor:
                sample = dict(zip(columns, row))
                # Convert datetime
                if 'sample_time' in sample and sample['sample_time']:
                    sample['sample_time'] = sample['sample_time'].isoformat()
                samples.append(sample)

            cursor.close()
            logger.info(f"Fetched {len(samples)} ASH samples")

            return samples

        except Exception as e:
            logger.error(f"Error fetching ASH activity: {e}", exc_info=True)
            raise

    def fetch_ash_top_sql(
        self,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch top SQL statements from ASH data.

        Args:
            begin_time: Start time
            end_time: End time
            top_n: Number of top SQL to return

        Returns:
            List of top SQL by activity
        """
        if not self.check_ash_availability():
            logger.warning("ASH not available, returning empty top SQL")
            return []

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    sql_id,
                    COUNT(*) as sample_count,
                    SUM(CASE WHEN session_state = 'ON CPU' THEN 1 ELSE 0 END) as cpu_samples,
                    SUM(CASE WHEN session_state = 'WAITING' THEN 1 ELSE 0 END) as wait_samples,
                    COUNT(DISTINCT session_id) as session_count,
                    wait_class,
                    event
                FROM dba_hist_active_sess_history
                WHERE sql_id IS NOT NULL
            """

            params = {}

            if begin_time:
                query += " AND sample_time >= :begin_time"
                params['begin_time'] = begin_time

            if end_time:
                query += " AND sample_time <= :end_time"
                params['end_time'] = end_time

            query += """
                GROUP BY sql_id, wait_class, event
                ORDER BY sample_count DESC
            """

            # Apply limit
            query = f"SELECT * FROM ({query}) WHERE ROWNUM <= :top_n"
            params['top_n'] = top_n

            cursor.execute(query, **params)

            columns = [col[0].lower() for col in cursor.description]
            top_sql = []

            for row in cursor:
                sql_stat = dict(zip(columns, row))
                top_sql.append(sql_stat)

            cursor.close()
            logger.info(f"Fetched top {len(top_sql)} SQL from ASH")

            return top_sql

        except Exception as e:
            logger.error(f"Error fetching ASH top SQL: {e}", exc_info=True)
            raise

    def fetch_system_wait_events(
        self,
        begin_snap_id: int,
        end_snap_id: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch system-level wait events from AWR.

        Args:
            begin_snap_id: Beginning snapshot ID
            end_snap_id: Ending snapshot ID

        Returns:
            List of wait event statistics
        """
        if not self.check_awr_availability():
            logger.warning("AWR not available, returning empty wait events")
            return []

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    e.event_name,
                    e.wait_class,
                    e.total_waits_delta,
                    e.total_timeouts_delta,
                    e.time_waited_micro_delta / 1000000 as time_waited_sec,
                    CASE
                        WHEN e.total_waits_delta > 0
                        THEN e.time_waited_micro_delta / e.total_waits_delta / 1000
                        ELSE 0
                    END as avg_wait_ms
                FROM
                    (SELECT
                        event_name,
                        wait_class,
                        SUM(total_waits) - LAG(SUM(total_waits))
                            OVER (PARTITION BY event_name ORDER BY snap_id) as total_waits_delta,
                        SUM(total_timeouts) - LAG(SUM(total_timeouts))
                            OVER (PARTITION BY event_name ORDER BY snap_id) as total_timeouts_delta,
                        SUM(time_waited_micro) - LAG(SUM(time_waited_micro))
                            OVER (PARTITION BY event_name ORDER BY snap_id) as time_waited_micro_delta,
                        snap_id
                     FROM dba_hist_system_event
                     WHERE snap_id IN (:begin_snap_id, :end_snap_id)
                        AND wait_class != 'Idle'
                     GROUP BY event_name, wait_class, snap_id
                    ) e
                WHERE e.snap_id = :end_snap_id
                    AND e.total_waits_delta > 0
                ORDER BY time_waited_sec DESC
            """

            cursor.execute(query, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id)

            columns = [col[0].lower() for col in cursor.description]
            wait_events = []

            for row in cursor:
                event = dict(zip(columns, row))
                wait_events.append(event)

            cursor.close()
            logger.info(f"Fetched {len(wait_events)} system wait events")

            return wait_events

        except Exception as e:
            logger.error(f"Error fetching system wait events: {e}", exc_info=True)
            raise

    def calculate_sql_statistics_summary(
        self,
        sql_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for a SQL statement from AWR data.

        Args:
            sql_id: SQL_ID
            days_back: Number of days to analyze

        Returns:
            Summary statistics (min, max, avg, percentiles)
        """
        stats = self.fetch_historical_sql_stats(sql_id, days_back=days_back)

        if not stats:
            return {
                "sql_id": sql_id,
                "sample_count": 0,
                "error": "No historical data available"
            }

        # Calculate metrics
        elapsed_times = [s['elapsed_time_sec'] for s in stats if s['elapsed_time_sec']]
        cpu_times = [s['cpu_time_sec'] for s in stats if s['cpu_time_sec']]
        executions = [s['executions_delta'] for s in stats if s['executions_delta']]
        buffer_gets = [s['buffer_gets_delta'] for s in stats if s['buffer_gets_delta']]

        def calculate_percentiles(values):
            if not values:
                return {}
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            return {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / n,
                "median": sorted_vals[n // 2],
                "p95": sorted_vals[int(n * 0.95)] if n > 0 else 0,
                "p99": sorted_vals[int(n * 0.99)] if n > 0 else 0,
            }

        return {
            "sql_id": sql_id,
            "sample_count": len(stats),
            "time_range": {
                "begin": stats[0]['begin_interval_time'] if stats else None,
                "end": stats[-1]['end_interval_time'] if stats else None,
            },
            "elapsed_time": calculate_percentiles(elapsed_times),
            "cpu_time": calculate_percentiles(cpu_times),
            "executions": calculate_percentiles(executions),
            "buffer_gets": calculate_percentiles(buffer_gets),
        }
