"""Oracle deadlock detection and lock analysis.

This module provides functionality to detect deadlocks and analyze
lock dependencies using V$LOCK and related views.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from collections import defaultdict

from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class DeadlockDetector:
    """Detects deadlocks and analyzes lock dependencies."""

    # Lock mode descriptions
    LOCK_MODES = {
        0: "None",
        1: "Null (NULL)",
        2: "Row-S (SS)",
        3: "Row-X (SX)",
        4: "Share (S)",
        5: "S/Row-X (SSX)",
        6: "Exclusive (X)",
    }

    # Lock type descriptions
    LOCK_TYPES = {
        "TX": "Transaction",
        "TM": "DML",
        "UL": "User",
        "DX": "Distributed Transaction",
        "CF": "Control File",
        "IS": "Instance State",
        "FS": "File Set",
        "IR": "Instance Recovery",
        "RT": "Redo Thread",
        "TS": "Temporary Segment",
        "TD": "DDL",
        "JQ": "Job Queue",
        "ST": "Space Transaction",
        "TE": "Extend Table",
        "TT": "Temp Table",
    }

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize DeadlockDetector.

        Args:
            connection_manager: Oracle connection manager instance
        """
        self.connection_manager = connection_manager

    def fetch_current_locks(self) -> List[Dict[str, Any]]:
        """
        Fetch current locks from V$LOCK.

        Returns:
            List of current locks with details
        """
        query = """
            SELECT
                l.sid,
                s.serial#,
                s.username,
                s.program,
                s.sql_id,
                l.type as lock_type,
                l.id1,
                l.id2,
                l.lmode as lock_mode_held,
                l.request as lock_mode_requested,
                l.ctime as lock_held_seconds,
                l.block,
                o.object_name,
                o.object_type
            FROM v$lock l
            JOIN v$session s ON l.sid = s.sid
            LEFT JOIN dba_objects o ON l.id1 = o.object_id
            WHERE s.username IS NOT NULL
              AND (l.lmode > 0 OR l.request > 0)
            ORDER BY l.ctime DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                locks = []
                for row in rows:
                    lock = dict(zip(columns, row))
                    lock = self._convert_oracle_types(lock)
                    # Add human-readable lock modes
                    lock["lock_mode_held_desc"] = self.LOCK_MODES.get(
                        lock.get("lock_mode_held", 0), "Unknown"
                    )
                    lock["lock_mode_requested_desc"] = self.LOCK_MODES.get(
                        lock.get("lock_mode_requested", 0), "Unknown"
                    )
                    lock["lock_type_desc"] = self.LOCK_TYPES.get(
                        lock.get("lock_type", ""), "Unknown"
                    )
                    locks.append(lock)

                logger.info(f"Fetched {len(locks)} current locks")

                return locks

            finally:
                cursor.close()

    def fetch_blocking_locks(self) -> List[Dict[str, Any]]:
        """
        Fetch locks that are blocking other sessions.

        Returns:
            List of blocking locks with waiter information
        """
        query = """
            SELECT
                l1.sid as blocking_sid,
                s1.serial# as blocking_serial,
                s1.username as blocking_username,
                s1.program as blocking_program,
                s1.sql_id as blocking_sql_id,
                l1.type as lock_type,
                l1.id1,
                l1.id2,
                l1.lmode as lock_mode_held,
                l1.ctime as lock_held_seconds,
                l2.sid as waiting_sid,
                s2.serial# as waiting_serial,
                s2.username as waiting_username,
                s2.program as waiting_program,
                s2.sql_id as waiting_sql_id,
                l2.request as lock_mode_requested,
                s2.seconds_in_wait as wait_seconds,
                o.object_name,
                o.object_type
            FROM v$lock l1
            JOIN v$session s1 ON l1.sid = s1.sid
            JOIN v$lock l2 ON l1.id1 = l2.id1 AND l1.id2 = l2.id2
            JOIN v$session s2 ON l2.sid = s2.sid
            LEFT JOIN dba_objects o ON l1.id1 = o.object_id
            WHERE l1.block = 1
              AND l2.request > 0
              AND l1.sid != l2.sid
            ORDER BY l1.ctime DESC
        """

        with self.connection_manager.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()

                blocking_locks = []
                for row in rows:
                    lock = dict(zip(columns, row))
                    lock = self._convert_oracle_types(lock)
                    # Add descriptions
                    lock["lock_mode_held_desc"] = self.LOCK_MODES.get(
                        lock.get("lock_mode_held", 0), "Unknown"
                    )
                    lock["lock_mode_requested_desc"] = self.LOCK_MODES.get(
                        lock.get("lock_mode_requested", 0), "Unknown"
                    )
                    lock["lock_type_desc"] = self.LOCK_TYPES.get(
                        lock.get("lock_type", ""), "Unknown"
                    )
                    blocking_locks.append(lock)

                logger.info(f"Found {len(blocking_locks)} blocking lock situations")

                return blocking_locks

            finally:
                cursor.close()

    def build_lock_dependency_graph(
        self, blocking_locks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build directed graph of lock dependencies.

        Args:
            blocking_locks: List of blocking locks (fetches if None)

        Returns:
            Graph structure with nodes and edges
        """
        if blocking_locks is None:
            blocking_locks = self.fetch_blocking_locks()

        # Build graph structure
        nodes = {}  # sid -> node info
        edges = []  # List of (blocker_sid, waiter_sid) tuples
        adjacency = defaultdict(list)  # sid -> list of blocked sids

        for lock in blocking_locks:
            blocker_sid = lock.get("blocking_sid")
            waiter_sid = lock.get("waiting_sid")

            # Add blocker node
            if blocker_sid not in nodes:
                nodes[blocker_sid] = {
                    "sid": blocker_sid,
                    "serial": lock.get("blocking_serial"),
                    "username": lock.get("blocking_username"),
                    "program": lock.get("blocking_program"),
                    "sql_id": lock.get("blocking_sql_id"),
                    "type": "blocker",
                    "locks_held": [],
                }

            # Add waiter node
            if waiter_sid not in nodes:
                nodes[waiter_sid] = {
                    "sid": waiter_sid,
                    "serial": lock.get("waiting_serial"),
                    "username": lock.get("waiting_username"),
                    "program": lock.get("waiting_program"),
                    "sql_id": lock.get("waiting_sql_id"),
                    "type": "waiter",
                    "waiting_for": [],
                }

            # Add lock to blocker's held locks
            nodes[blocker_sid]["locks_held"].append({
                "lock_type": lock.get("lock_type"),
                "object_name": lock.get("object_name"),
                "lock_mode": lock.get("lock_mode_held_desc"),
            })

            # Add lock to waiter's waiting list
            nodes[waiter_sid]["waiting_for"].append({
                "lock_type": lock.get("lock_type"),
                "object_name": lock.get("object_name"),
                "lock_mode_requested": lock.get("lock_mode_requested_desc"),
            })

            # Add edge
            edge = {
                "from": blocker_sid,
                "to": waiter_sid,
                "lock_type": lock.get("lock_type"),
                "object_name": lock.get("object_name"),
                "wait_seconds": lock.get("wait_seconds"),
            }
            edges.append(edge)
            adjacency[blocker_sid].append(waiter_sid)

        # Detect cycles (deadlocks)
        cycles = self._detect_cycles(adjacency)

        graph = {
            "nodes": list(nodes.values()),
            "edges": edges,
            "has_deadlock": len(cycles) > 0,
            "deadlock_cycles": cycles,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

        logger.info(
            f"Built lock dependency graph: {len(nodes)} nodes, "
            f"{len(edges)} edges, {len(cycles)} cycles"
        )

        return graph

    def _detect_cycles(
        self, adjacency: Dict[int, List[int]]
    ) -> List[List[int]]:
        """
        Detect cycles in the lock dependency graph using DFS.

        Args:
            adjacency: Adjacency list representation of graph

        Returns:
            List of cycles (each cycle is a list of session IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: int) -> bool:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all neighbors
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        # Run DFS from each unvisited node
        for node in adjacency.keys():
            if node not in visited:
                dfs(node)

        return cycles

    def analyze_deadlock_cycle(
        self, cycle: List[int], locks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a detected deadlock cycle.

        Args:
            cycle: List of session IDs in the cycle
            locks: List of all locks

        Returns:
            Analysis of the deadlock cycle
        """
        cycle_sessions = []
        cycle_locks = []

        # Extract information for each session in the cycle
        for sid in cycle:
            session_locks = [l for l in locks if l.get("blocking_sid") == sid or l.get("waiting_sid") == sid]

            session_info = {
                "sid": sid,
                "locks": session_locks,
            }

            # Get session details from first lock
            if session_locks:
                if session_locks[0].get("blocking_sid") == sid:
                    session_info.update({
                        "username": session_locks[0].get("blocking_username"),
                        "program": session_locks[0].get("blocking_program"),
                        "sql_id": session_locks[0].get("blocking_sql_id"),
                    })
                else:
                    session_info.update({
                        "username": session_locks[0].get("waiting_username"),
                        "program": session_locks[0].get("waiting_program"),
                        "sql_id": session_locks[0].get("waiting_sql_id"),
                    })

            cycle_sessions.append(session_info)
            cycle_locks.extend(session_locks)

        return {
            "cycle_length": len(cycle),
            "sessions": cycle_sessions,
            "cycle_path": cycle,
            "affected_objects": list(set(
                l.get("object_name")
                for l in cycle_locks
                if l.get("object_name")
            )),
        }

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
            # Handle None/NULL
            elif value is None:
                converted[key] = None
            else:
                converted[key] = value

        return converted
