"""Oracle execution plan fetcher and parser.

This module provides functionality to fetch and parse execution plans from V$SQL_PLAN.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class ExecutionPlanFetcher:
    """Fetches and parses execution plans from Oracle V$SQL_PLAN view."""

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize ExecutionPlanFetcher.

        Args:
            connection_manager: Oracle connection manager instance
        """
        self.connection_manager = connection_manager

    def fetch_plan_by_sql_id(
        self, sql_id: str, plan_hash_value: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch execution plan for a SQL_ID from V$SQL_PLAN.

        Args:
            sql_id: Oracle SQL_ID (13 character identifier)
            plan_hash_value: Optional specific plan hash value

        Returns:
            List of plan operations as dictionaries

        Raises:
            OracleConnectionError: If database connection fails
        """
        query = """
            SELECT
                sql_id,
                plan_hash_value,
                id,
                parent_id,
                operation,
                options,
                object_owner,
                object_name,
                object_alias,
                object_type,
                optimizer,
                cost,
                cardinality,
                bytes,
                cpu_cost,
                io_cost,
                temp_space,
                access_predicates,
                filter_predicates,
                projection,
                time,
                qblock_name,
                remarks,
                depth,
                position,
                search_columns,
                partition_start,
                partition_stop,
                partition_id,
                distribution
            FROM v$sql_plan
            WHERE sql_id = :sql_id
        """

        bind_params = {"sql_id": sql_id}

        if plan_hash_value is not None:
            query += " AND plan_hash_value = :plan_hash_value"
            bind_params["plan_hash_value"] = plan_hash_value

        query += " ORDER BY id"

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                plans = []
                for row in rows:
                    plan_op = dict(zip(columns, row))
                    plan_op = self._convert_oracle_types(plan_op)
                    plans.append(plan_op)

                logger.info(
                    f"Fetched {len(plans)} plan operations for SQL_ID: {sql_id}"
                    + (f", PLAN_HASH_VALUE: {plan_hash_value}" if plan_hash_value else "")
                )

                return plans

            finally:
                cursor.close()

    def fetch_plan_history(self, sql_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all execution plan versions for a SQL_ID.

        Args:
            sql_id: Oracle SQL_ID

        Returns:
            List of plan metadata with plan_hash_value, timestamp, etc.
        """
        query = """
            SELECT DISTINCT
                sql_id,
                plan_hash_value,
                timestamp,
                child_number
            FROM v$sql_plan
            WHERE sql_id = :sql_id
            ORDER BY timestamp DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"sql_id": sql_id})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                plans = []
                for row in rows:
                    plan_meta = dict(zip(columns, row))
                    plan_meta = self._convert_oracle_types(plan_meta)
                    plans.append(plan_meta)

                logger.info(f"Found {len(plans)} plan versions for SQL_ID: {sql_id}")

                return plans

            finally:
                cursor.close()

    def get_plan_statistics(self, sql_id: str, plan_hash_value: int) -> Dict[str, Any]:
        """
        Get statistics for a specific execution plan.

        Args:
            sql_id: Oracle SQL_ID
            plan_hash_value: Plan hash value

        Returns:
            Dictionary with plan statistics
        """
        query = """
            SELECT
                COUNT(DISTINCT child_number) as execution_count,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM v$sql_plan
            WHERE sql_id = :sql_id
              AND plan_hash_value = :plan_hash_value
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    query, {"sql_id": sql_id, "plan_hash_value": plan_hash_value}
                )
                columns = [col[0].lower() for col in cursor.description]
                row = cursor.fetchone()

                if row:
                    stats = dict(zip(columns, row))
                    return self._convert_oracle_types(stats)

                return {}

            finally:
                cursor.close()

    def build_plan_tree(self, plan_operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from flat plan operations.

        Args:
            plan_operations: List of plan operations from V$SQL_PLAN

        Returns:
            Root node of plan tree with nested children
        """
        if not plan_operations:
            return {}

        # Create a mapping of id -> operation
        operations_map = {op["id"]: op for op in plan_operations}

        # Initialize children lists
        for op in plan_operations:
            op["children"] = []

        # Build tree by linking children to parents
        root = None
        for op in plan_operations:
            parent_id = op.get("parent_id")
            if parent_id is None:
                # This is the root node
                root = op
            elif parent_id in operations_map:
                # Add this operation as child of its parent
                operations_map[parent_id]["children"].append(op)

        # Calculate cumulative costs
        if root:
            self._calculate_cumulative_costs(root)

        return root or {}

    def _calculate_cumulative_costs(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cumulative costs for a plan node and its children.

        Args:
            node: Plan operation node

        Returns:
            Node with cumulative_cost added
        """
        node_cost = node.get("cost") or 0
        node_cardinality = node.get("cardinality") or 0

        if not node.get("children"):
            node["cumulative_cost"] = node_cost
            node["cumulative_cardinality"] = node_cardinality
            return node

        # Recursively calculate for children
        children_cumulative_cost = 0
        children_cumulative_cardinality = 0

        for child in node["children"]:
            self._calculate_cumulative_costs(child)
            children_cumulative_cost += child.get("cumulative_cost", 0)
            children_cumulative_cardinality += child.get("cumulative_cardinality", 0)

        node["cumulative_cost"] = node_cost + children_cumulative_cost
        node["cumulative_cardinality"] = max(
            node_cardinality, children_cumulative_cardinality
        )

        return node

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

    def fetch_historical_plan_by_sql_id(
        self, sql_id: str, plan_hash_value: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical execution plan from DBA_HIST_SQL_PLAN (AWR).

        Args:
            sql_id: Oracle SQL_ID
            plan_hash_value: Optional specific plan hash value

        Returns:
            List of historical plan operations

        Raises:
            OracleConnectionError: If database connection fails
        """
        query = """
            SELECT
                sql_id,
                plan_hash_value,
                id,
                parent_id,
                operation,
                options,
                object_owner,
                object_name,
                object_alias,
                object_type,
                optimizer,
                cost,
                cardinality,
                bytes,
                cpu_cost,
                io_cost,
                temp_space,
                access_predicates,
                filter_predicates,
                projection,
                time,
                qblock_name,
                remarks,
                depth,
                position,
                search_columns,
                partition_start,
                partition_stop,
                partition_id,
                distribution
            FROM dba_hist_sql_plan
            WHERE sql_id = :sql_id
        """

        bind_params = {"sql_id": sql_id}

        if plan_hash_value is not None:
            query += " AND plan_hash_value = :plan_hash_value"
            bind_params["plan_hash_value"] = plan_hash_value

        query += " ORDER BY id"

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, bind_params)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                plans = []
                for row in rows:
                    plan_op = dict(zip(columns, row))
                    plan_op = self._convert_oracle_types(plan_op)
                    plans.append(plan_op)

                logger.info(
                    f"Fetched {len(plans)} historical plan operations for SQL_ID: {sql_id}"
                    + (f", PLAN_HASH_VALUE: {plan_hash_value}" if plan_hash_value else "")
                )

                return plans

            finally:
                cursor.close()

    def fetch_historical_plan_versions(self, sql_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all historical plan versions for a SQL_ID from AWR.

        Args:
            sql_id: Oracle SQL_ID

        Returns:
            List of plan versions with metadata
        """
        query = """
            SELECT DISTINCT
                hsp.sql_id,
                hsp.plan_hash_value,
                MIN(hs.snap_id) as first_snap_id,
                MAX(hs.snap_id) as last_snap_id,
                MIN(ss.begin_interval_time) as first_seen,
                MAX(ss.end_interval_time) as last_seen,
                COUNT(DISTINCT hs.snap_id) as snap_count
            FROM dba_hist_sql_plan hsp
            JOIN dba_hist_sqlstat hs ON hsp.sql_id = hs.sql_id
                AND hsp.plan_hash_value = hs.plan_hash_value
            JOIN dba_hist_snapshot ss ON hs.snap_id = ss.snap_id
            WHERE hsp.sql_id = :sql_id
            GROUP BY hsp.sql_id, hsp.plan_hash_value
            ORDER BY MAX(ss.end_interval_time) DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, {"sql_id": sql_id})
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                versions = []
                for row in rows:
                    version = dict(zip(columns, row))
                    version = self._convert_oracle_types(version)
                    versions.append(version)

                logger.info(
                    f"Found {len(versions)} historical plan versions for SQL_ID: {sql_id}"
                )

                return versions

            finally:
                cursor.close()

    def format_plan_text(self, plan_operations: List[Dict[str, Any]]) -> str:
        """
        Format execution plan as text (similar to EXPLAIN PLAN output).

        Args:
            plan_operations: List of plan operations

        Returns:
            Formatted plan text
        """
        lines = []
        lines.append("-" * 100)
        lines.append(
            f"| Id  | Operation{' ' * 40} | Name{' ' * 20} | Rows  | Bytes | Cost  |"
        )
        lines.append("-" * 100)

        for op in plan_operations:
            depth = op.get("depth", 0)
            indent = "  " * depth

            op_name = op.get("operation", "")
            options = op.get("options", "")
            full_op = f"{op_name} {options}".strip()

            obj_name = op.get("object_name", "")
            rows = op.get("cardinality") or 0
            bytes_val = op.get("bytes") or 0
            cost = op.get("cost") or 0

            line = (
                f"| {op['id']:3d} | {indent}{full_op:48s} | "
                f"{obj_name:24s} | {rows:5d} | {bytes_val:5d} | {cost:5d} |"
            )
            lines.append(line)

        lines.append("-" * 100)

        # Add predicates if present
        for op in plan_operations:
            if op.get("access_predicates"):
                lines.append(f"\nAccess Predicates (Id={op['id']}):")
                lines.append(f"  {op['access_predicates']}")

            if op.get("filter_predicates"):
                lines.append(f"\nFilter Predicates (Id={op['id']}):")
                lines.append(f"  {op['filter_predicates']}")

        return "\n".join(lines)
