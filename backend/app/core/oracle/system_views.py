"""Oracle system views fetcher for sessions and resource usage.

This module provides functionality to fetch session and resource data from
V$SESSION, V$SESSTAT, and related system views.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class SystemViewsFetcher:
    """Fetches session and resource usage data from Oracle system views."""

    # System schemas to exclude from user analysis
    SYSTEM_SCHEMAS = ["SYS", "SYSTEM", "DBSNMP", "SYSMAN", "OUTLN", "MDSYS", "ORDSYS",
                      "EXFSYS", "WMSYS", "APPQOSSYS", "APEX_050000", "OWBSYS", "OWBSYS_AUDIT",
                      "ORACLE_OCM", "XDB", "ANONYMOUS", "CTXSYS", "SI_INFORMTN_SCHEMA",
                      "OLAPSYS", "ORDDATA", "ORDPLUGINS", "FLOWS_FILES"]

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize SystemViewsFetcher.

        Args:
            connection_manager: Oracle connection manager instance
        """
        self.connection_manager = connection_manager

    def fetch_active_sessions(
        self, exclude_system: bool = True, include_background: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch active sessions from V$SESSION.

        Args:
            exclude_system: Exclude system schema sessions
            include_background: Include background processes

        Returns:
            List of active sessions with details
        """
        query = """
            SELECT
                s.sid,
                s.serial#,
                s.username,
                s.osuser,
                s.machine,
                s.program,
                s.module,
                s.action,
                s.client_identifier,
                s.status,
                s.sql_id,
                s.sql_child_number,
                s.prev_sql_id,
                s.logon_time,
                s.last_call_et,
                s.blocking_session,
                s.blocking_session_status,
                s.event,
                s.wait_class,
                s.wait_time,
                s.seconds_in_wait,
                s.state,
                s.service_name,
                s.client_info,
                s.process,
                s.paddr
            FROM v$session s
            WHERE 1=1
        """

        conditions = []
        bind_params = {}

        if exclude_system:
            placeholders = ", ".join([f":schema{i}" for i in range(len(self.SYSTEM_SCHEMAS))])
            conditions.append(f"s.username NOT IN ({placeholders})")
            for i, schema in enumerate(self.SYSTEM_SCHEMAS):
                bind_params[f"schema{i}"] = schema

        if not include_background:
            conditions.append("s.type != 'BACKGROUND'")

        conditions.append("s.username IS NOT NULL")

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY s.last_call_et DESC"

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                sessions = []
                for row in rows:
                    session = dict(zip(columns, row))
                    session = self._convert_oracle_types(session)
                    sessions.append(session)

                logger.info(f"Fetched {len(sessions)} active sessions")

                return sessions

            finally:
                cursor.close()

    def fetch_session_by_sid(self, sid: int, serial: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch specific session details by SID.

        Args:
            sid: Session ID
            serial: Session serial number (optional)

        Returns:
            Session details or None if not found
        """
        query = """
            SELECT
                s.sid,
                s.serial#,
                s.username,
                s.osuser,
                s.machine,
                s.program,
                s.module,
                s.action,
                s.client_identifier,
                s.status,
                s.sql_id,
                s.sql_child_number,
                s.prev_sql_id,
                s.logon_time,
                s.last_call_et,
                s.blocking_session,
                s.blocking_session_status,
                s.event,
                s.wait_class,
                s.wait_time,
                s.seconds_in_wait,
                s.state,
                s.service_name,
                s.client_info,
                s.process,
                s.paddr,
                sq.sql_text as current_sql_text
            FROM v$session s
            LEFT JOIN v$sql sq ON s.sql_id = sq.sql_id AND s.sql_child_number = sq.child_number
            WHERE s.sid = :sid
        """

        bind_params = {"sid": sid}

        if serial is not None:
            query += " AND s.serial# = :serial"
            bind_params["serial"] = serial

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                row = cursor.fetchone()

                if row:
                    session = dict(zip(columns, row))
                    return self._convert_oracle_types(session)

                return None

            finally:
                cursor.close()

    def fetch_session_statistics(self, sid: int) -> List[Dict[str, Any]]:
        """
        Fetch session statistics from V$SESSTAT.

        Args:
            sid: Session ID

        Returns:
            List of session statistics
        """
        query = """
            SELECT
                st.sid,
                sn.name as statistic_name,
                st.value,
                sn.statistic#,
                sn.class
            FROM v$sesstat st
            JOIN v$statname sn ON st.statistic# = sn.statistic#
            WHERE st.sid = :sid
              AND st.value > 0
            ORDER BY st.value DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"sid": sid})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                statistics = []
                for row in rows:
                    stat = dict(zip(columns, row))
                    stat = self._convert_oracle_types(stat)
                    statistics.append(stat)

                return statistics

            finally:
                cursor.close()

    def fetch_user_resource_usage(
        self, username: Optional[str] = None, exclude_system: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch resource usage aggregated by user.

        Args:
            username: Specific username to fetch (None for all)
            exclude_system: Exclude system schemas

        Returns:
            List of users with resource usage metrics
        """
        query = """
            SELECT
                s.username,
                COUNT(DISTINCT s.sid) as active_sessions,
                COUNT(DISTINCT s.sql_id) as unique_queries,
                SUM(CASE WHEN s.status = 'ACTIVE' THEN 1 ELSE 0 END) as active_count,
                SUM(CASE WHEN s.blocking_session IS NOT NULL THEN 1 ELSE 0 END) as blocked_count,
                MAX(s.last_call_et) as max_session_duration,
                SUM(ss_cpu.value) as total_cpu_time,
                SUM(ss_logical.value) as total_logical_reads,
                SUM(ss_physical.value) as total_physical_reads,
                SUM(ss_sorts.value) as total_sorts,
                SUM(ss_parses.value) as total_parses,
                SUM(ss_executes.value) as total_executions
            FROM v$session s
            LEFT JOIN v$sesstat ss_cpu ON s.sid = ss_cpu.sid
                AND ss_cpu.statistic# = (SELECT statistic# FROM v$statname WHERE name = 'CPU used by this session')
            LEFT JOIN v$sesstat ss_logical ON s.sid = ss_logical.sid
                AND ss_logical.statistic# = (SELECT statistic# FROM v$statname WHERE name = 'session logical reads')
            LEFT JOIN v$sesstat ss_physical ON s.sid = ss_physical.sid
                AND ss_physical.statistic# = (SELECT statistic# FROM v$statname WHERE name = 'physical reads')
            LEFT JOIN v$sesstat ss_sorts ON s.sid = ss_sorts.sid
                AND ss_sorts.statistic# = (SELECT statistic# FROM v$statname WHERE name = 'sorts (memory)')
            LEFT JOIN v$sesstat ss_parses ON s.sid = ss_parses.sid
                AND ss_parses.statistic# = (SELECT statistic# FROM v$statname WHERE name = 'parse count (total)')
            LEFT JOIN v$sesstat ss_executes ON s.sid = ss_executes.sid
                AND ss_executes.statistic# = (SELECT statistic# FROM v$statname WHERE name = 'execute count')
            WHERE s.username IS NOT NULL
              AND s.type != 'BACKGROUND'
        """

        bind_params = {}

        if exclude_system:
            placeholders = ", ".join([f":schema{i}" for i in range(len(self.SYSTEM_SCHEMAS))])
            query += f" AND s.username NOT IN ({placeholders})"
            for i, schema in enumerate(self.SYSTEM_SCHEMAS):
                bind_params[f"schema{i}"] = schema

        if username:
            query += " AND s.username = :username"
            bind_params["username"] = username.upper()

        query += """
            GROUP BY s.username
            ORDER BY SUM(ss_cpu.value) DESC NULLS LAST
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                users = []
                for row in rows:
                    user = dict(zip(columns, row))
                    user = self._convert_oracle_types(user)
                    users.append(user)

                logger.info(f"Fetched resource usage for {len(users)} users")

                return users

            finally:
                cursor.close()

    def fetch_user_queries(self, username: str, top_n: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch top queries executed by a specific user.

        Args:
            username: Username to fetch queries for
            top_n: Number of top queries to return

        Returns:
            List of queries with performance metrics
        """
        query = """
            SELECT
                sql_id,
                sql_text,
                parsing_schema_name,
                executions,
                elapsed_time,
                cpu_time,
                buffer_gets,
                disk_reads,
                rows_processed,
                fetches,
                first_load_time,
                last_active_time
            FROM v$sql
            WHERE parsing_schema_name = :username
            ORDER BY elapsed_time DESC
            FETCH FIRST :top_n ROWS ONLY
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"username": username.upper(), "top_n": top_n})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                queries = []
                for row in rows:
                    query_data = dict(zip(columns, row))
                    query_data = self._convert_oracle_types(query_data)
                    queries.append(query_data)

                return queries

            finally:
                cursor.close()

    def fetch_long_running_sessions(
        self, threshold_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Fetch sessions running longer than threshold.

        Args:
            threshold_seconds: Minimum duration in seconds

        Returns:
            List of long-running sessions
        """
        query = """
            SELECT
                s.sid,
                s.serial#,
                s.username,
                s.program,
                s.sql_id,
                s.status,
                s.last_call_et as duration_seconds,
                s.event,
                s.wait_class,
                sq.sql_text
            FROM v$session s
            LEFT JOIN v$sql sq ON s.sql_id = sq.sql_id
            WHERE s.username IS NOT NULL
              AND s.type != 'BACKGROUND'
              AND s.last_call_et >= :threshold
            ORDER BY s.last_call_et DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"threshold": threshold_seconds})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                sessions = []
                for row in rows:
                    session = dict(zip(columns, row))
                    session = self._convert_oracle_types(session)
                    sessions.append(session)

                logger.info(
                    f"Found {len(sessions)} long-running sessions "
                    f"(>{threshold_seconds}s)"
                )

                return sessions

            finally:
                cursor.close()

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
