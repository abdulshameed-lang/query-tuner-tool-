"""Oracle V$SQL query module for retrieving SQL statements and performance metrics."""

from typing import List, Dict, Any, Optional
import logging
import cx_Oracle

from app.core.oracle.connection import ConnectionManager, OracleConnectionError

logger = logging.getLogger(__name__)


class QueryFetcher:
    """Fetches queries from Oracle V$SQL view."""

    # System schemas to exclude by default
    SYSTEM_SCHEMAS = ["SYS", "SYSTEM", "XDB", "MDSYS", "CTXSYS", "ORDSYS"]

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize QueryFetcher.

        Args:
            connection_manager: Oracle connection manager instance
        """
        self.connection_manager = connection_manager

    def fetch_top_queries(
        self,
        top_n: int = 20,
        min_elapsed_time: Optional[float] = None,
        min_executions: Optional[int] = None,
        exclude_system_schemas: bool = True,
        order_by: str = "elapsed_time",
    ) -> List[Dict[str, Any]]:
        """
        Fetch top queries from V$SQL ordered by specified metric.

        Args:
            top_n: Number of top queries to return
            min_elapsed_time: Minimum elapsed time in microseconds
            min_executions: Minimum number of executions
            exclude_system_schemas: Whether to exclude system schemas
            order_by: Column to order by (elapsed_time, cpu_time, executions, buffer_gets)

        Returns:
            List of query dictionaries with performance metrics

        Raises:
            OracleConnectionError: If query execution fails
        """
        try:
            # Build WHERE clause conditions
            where_conditions = []
            bind_params = {"top_n": top_n}

            if min_elapsed_time is not None:
                where_conditions.append("elapsed_time > :min_elapsed_time")
                bind_params["min_elapsed_time"] = min_elapsed_time

            if min_executions is not None:
                where_conditions.append("executions > :min_executions")
                bind_params["min_executions"] = min_executions

            if exclude_system_schemas:
                placeholders = ", ".join(f":schema{i}" for i in range(len(self.SYSTEM_SCHEMAS)))
                where_conditions.append(f"parsing_schema_name NOT IN ({placeholders})")
                for i, schema in enumerate(self.SYSTEM_SCHEMAS):
                    bind_params[f"schema{i}"] = schema

            # Build WHERE clause
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Validate order_by to prevent SQL injection
            valid_order_columns = ["elapsed_time", "cpu_time", "executions", "buffer_gets", "disk_reads"]
            if order_by not in valid_order_columns:
                order_by = "elapsed_time"

            # Build SQL query
            sql = f"""
                SELECT * FROM (
                    SELECT
                        sql_id,
                        sql_text,
                        parsing_schema_name,
                        elapsed_time,
                        cpu_time,
                        executions,
                        buffer_gets,
                        disk_reads,
                        rows_processed,
                        fetches,
                        sorts,
                        loads,
                        invalidations,
                        parse_calls,
                        optimizer_cost,
                        optimizer_mode,
                        last_active_time,
                        first_load_time,
                        ROUND(elapsed_time / DECODE(executions, 0, 1, executions), 2) as avg_elapsed_time,
                        ROUND(cpu_time / DECODE(executions, 0, 1, executions), 2) as avg_cpu_time,
                        ROUND(buffer_gets / DECODE(executions, 0, 1, executions), 2) as avg_buffer_gets
                    FROM v$sql
                    WHERE {where_clause}
                    ORDER BY {order_by} DESC
                )
                WHERE rownum <= :top_n
            """

            logger.debug(f"Executing query: {sql}")
            logger.debug(f"Bind parameters: {bind_params}")

            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, bind_params)

                # Get column names
                columns = [desc[0].lower() for desc in cursor.description]

                # Fetch results
                rows = cursor.fetchall()
                cursor.close()

                # Convert to list of dictionaries
                queries = []
                for row in rows:
                    query_dict = dict(zip(columns, row))
                    # Convert Oracle types to Python types
                    query_dict = self._convert_oracle_types(query_dict)
                    queries.append(query_dict)

                logger.info(f"Fetched {len(queries)} queries")
                return queries

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            error_message = f"Failed to fetch queries: {error.message}"
            logger.error(error_message)
            raise OracleConnectionError(error_message) from e

    def fetch_query_by_sql_id(self, sql_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch specific query by SQL_ID.

        Args:
            sql_id: Oracle SQL_ID (13 character alphanumeric)

        Returns:
            Query dictionary with performance metrics or None if not found

        Raises:
            OracleConnectionError: If query execution fails
        """
        try:
            sql = """
                SELECT
                    sql_id,
                    sql_fulltext,
                    sql_text,
                    parsing_schema_name,
                    module,
                    action,
                    elapsed_time,
                    cpu_time,
                    executions,
                    buffer_gets,
                    disk_reads,
                    direct_writes,
                    rows_processed,
                    fetches,
                    sorts,
                    loads,
                    invalidations,
                    parse_calls,
                    optimizer_cost,
                    optimizer_mode,
                    optimizer_env_hash_value,
                    sharable_mem,
                    persistent_mem,
                    runtime_mem,
                    last_active_time,
                    first_load_time,
                    last_load_time,
                    plan_hash_value,
                    child_number,
                    command_type,
                    ROUND(elapsed_time / DECODE(executions, 0, 1, executions), 2) as avg_elapsed_time,
                    ROUND(cpu_time / DECODE(executions, 0, 1, executions), 2) as avg_cpu_time,
                    ROUND(buffer_gets / DECODE(executions, 0, 1, executions), 2) as avg_buffer_gets,
                    ROUND(disk_reads / DECODE(executions, 0, 1, executions), 2) as avg_disk_reads
                FROM v$sql
                WHERE sql_id = :sql_id
                AND rownum = 1
            """

            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, {"sql_id": sql_id})

                # Get column names
                columns = [desc[0].lower() for desc in cursor.description]

                # Fetch result
                row = cursor.fetchone()
                cursor.close()

                if not row:
                    logger.info(f"Query not found: {sql_id}")
                    return None

                # Convert to dictionary
                query_dict = dict(zip(columns, row))
                query_dict = self._convert_oracle_types(query_dict)

                logger.info(f"Fetched query: {sql_id}")
                return query_dict

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            error_message = f"Failed to fetch query {sql_id}: {error.message}"
            logger.error(error_message)
            raise OracleConnectionError(error_message) from e

    def get_query_statistics(self, sql_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific query.

        Args:
            sql_id: Oracle SQL_ID

        Returns:
            Dictionary with detailed query statistics

        Raises:
            OracleConnectionError: If query execution fails
        """
        try:
            sql = """
                SELECT
                    COUNT(*) as child_cursors,
                    SUM(executions) as total_executions,
                    SUM(elapsed_time) as total_elapsed_time,
                    SUM(cpu_time) as total_cpu_time,
                    SUM(buffer_gets) as total_buffer_gets,
                    SUM(disk_reads) as total_disk_reads,
                    SUM(rows_processed) as total_rows_processed,
                    AVG(elapsed_time / DECODE(executions, 0, 1, executions)) as avg_elapsed_per_exec,
                    MAX(elapsed_time) as max_elapsed_time,
                    MIN(DECODE(executions, 0, NULL, elapsed_time / executions)) as min_elapsed_per_exec,
                    MAX(last_active_time) as last_active_time,
                    MIN(first_load_time) as first_load_time
                FROM v$sql
                WHERE sql_id = :sql_id
            """

            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, {"sql_id": sql_id})

                columns = [desc[0].lower() for desc in cursor.description]
                row = cursor.fetchone()
                cursor.close()

                if not row:
                    return {}

                stats = dict(zip(columns, row))
                stats = self._convert_oracle_types(stats)

                return stats

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            error_message = f"Failed to fetch statistics for {sql_id}: {error.message}"
            logger.error(error_message)
            raise OracleConnectionError(error_message) from e

    def _convert_oracle_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Oracle-specific types to Python types.

        Args:
            data: Dictionary with Oracle data types

        Returns:
            Dictionary with converted Python types
        """
        converted = {}
        for key, value in data.items():
            if value is None:
                converted[key] = None
            elif isinstance(value, cx_Oracle.LOB):
                # Convert LOB to string
                converted[key] = value.read()
            elif hasattr(value, 'isoformat'):
                # Convert datetime to ISO format string
                converted[key] = value.isoformat()
            else:
                converted[key] = value

        return converted
