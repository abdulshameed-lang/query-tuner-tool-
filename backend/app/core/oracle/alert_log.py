"""Oracle alert log parser for deadlock detection.

This module provides functionality to parse Oracle alert log files
and extract deadlock information.
"""

from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertLogParser:
    """Parses Oracle alert log files for deadlock information."""

    # Regex patterns for deadlock detection
    DEADLOCK_START_PATTERN = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)"
        r".*ORA-00060: deadlock detected"
    )
    DEADLOCK_START_PATTERN_OLD = re.compile(
        r"^(?P<day>\w{3})\s+(?P<month>\w{3})\s+(?P<date>\d+)\s+"
        r"(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<year>\d{4}).*"
        r"ORA-00060: deadlock detected"
    )

    SESSION_INFO_PATTERN = re.compile(
        r"session\s+(?P<session_id>\d+):\s*(?P<info>.*)"
    )
    SQL_ID_PATTERN = re.compile(r"sql_id\s*=\s*['\"]?(?P<sql_id>[a-zA-Z0-9]+)['\"]?")
    LOCK_INFO_PATTERN = re.compile(
        r"(?P<lock_mode>S|X|RS|RX|SRX)\s+(?P<lock_type>TX|TM|UL)\s+"
        r"(?P<id1>\d+)\s+(?P<id2>\d+)"
    )

    def __init__(self, alert_log_path: Optional[str] = None):
        """
        Initialize AlertLogParser.

        Args:
            alert_log_path: Path to Oracle alert log file
        """
        self.alert_log_path = alert_log_path

    def parse_deadlocks(
        self, alert_log_path: Optional[str] = None, max_entries: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Parse alert log and extract deadlock information.

        Args:
            alert_log_path: Path to alert log file (overrides instance path)
            max_entries: Maximum number of deadlock entries to return

        Returns:
            List of deadlock entries
        """
        log_path = alert_log_path or self.alert_log_path

        if not log_path:
            logger.warning("No alert log path specified")
            return []

        try:
            deadlocks = []
            current_deadlock = None
            in_deadlock_section = False

            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()

                    # Check for deadlock start
                    match = self.DEADLOCK_START_PATTERN.match(line)
                    if not match:
                        match = self.DEADLOCK_START_PATTERN_OLD.match(line)

                    if match:
                        # Save previous deadlock if exists
                        if current_deadlock:
                            deadlocks.append(current_deadlock)

                        # Start new deadlock entry
                        current_deadlock = self._create_deadlock_entry(match, line)
                        in_deadlock_section = True

                    elif in_deadlock_section and current_deadlock:
                        # Parse deadlock details
                        self._parse_deadlock_line(line, current_deadlock)

                        # Check for end of deadlock section
                        if line.startswith("*** ") and "END OF DEADLOCK" in line.upper():
                            deadlocks.append(current_deadlock)
                            current_deadlock = None
                            in_deadlock_section = False

                # Add last deadlock if exists
                if current_deadlock:
                    deadlocks.append(current_deadlock)

            logger.info(f"Parsed {len(deadlocks)} deadlock entries from alert log")

            # Return most recent entries
            return deadlocks[-max_entries:]

        except FileNotFoundError:
            logger.error(f"Alert log file not found: {log_path}")
            return []
        except Exception as e:
            logger.error(f"Error parsing alert log: {e}", exc_info=True)
            return []

    def parse_recent_deadlocks(
        self, alert_log_path: Optional[str] = None, hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Parse alert log for deadlocks within time range.

        Args:
            alert_log_path: Path to alert log file
            hours_back: Number of hours to look back

        Returns:
            List of recent deadlock entries
        """
        all_deadlocks = self.parse_deadlocks(alert_log_path)

        # Filter by time (simplified - would need proper timestamp parsing)
        # For now, just return all deadlocks
        return all_deadlocks

    def _create_deadlock_entry(
        self, match: re.Match, line: str
    ) -> Dict[str, Any]:
        """
        Create initial deadlock entry from matched line.

        Args:
            match: Regex match object
            line: Full line text

        Returns:
            Deadlock entry dictionary
        """
        # Try to extract timestamp
        timestamp = None
        if "timestamp" in match.groupdict():
            timestamp = match.group("timestamp")
        elif "year" in match.groupdict():
            # Old format: Wed Mar 15 10:23:45 2023
            try:
                day = match.group("day")
                month = match.group("month")
                date = match.group("date")
                time = match.group("time")
                year = match.group("year")
                timestamp_str = f"{day} {month} {date} {time} {year}"
                timestamp = datetime.strptime(
                    timestamp_str, "%a %b %d %H:%M:%S %Y"
                ).isoformat()
            except Exception:
                timestamp = None

        return {
            "timestamp": timestamp,
            "raw_text": [line],
            "sessions": [],
            "locks": [],
            "sql_ids": [],
            "victim_session": None,
            "deadlock_graph": {"nodes": [], "edges": []},
        }

    def _parse_deadlock_line(self, line: str, deadlock: Dict[str, Any]) -> None:
        """
        Parse a line within a deadlock section.

        Args:
            line: Line to parse
            deadlock: Current deadlock entry to update
        """
        # Add to raw text
        deadlock["raw_text"].append(line)

        # Look for session information
        session_match = self.SESSION_INFO_PATTERN.search(line)
        if session_match:
            session_id = session_match.group("session_id")
            info = session_match.group("info")

            session = {
                "session_id": session_id,
                "info": info,
            }

            # Check if this is the victim
            if "deadlock victim" in line.lower() or "rolled back" in line.lower():
                deadlock["victim_session"] = session_id

            # Add to sessions if not already present
            if not any(s["session_id"] == session_id for s in deadlock["sessions"]):
                deadlock["sessions"].append(session)

        # Look for SQL_ID
        sql_id_match = self.SQL_ID_PATTERN.search(line)
        if sql_id_match:
            sql_id = sql_id_match.group("sql_id")
            if sql_id not in deadlock["sql_ids"]:
                deadlock["sql_ids"].append(sql_id)

        # Look for lock information
        lock_match = self.LOCK_INFO_PATTERN.search(line)
        if lock_match:
            lock = {
                "mode": lock_match.group("lock_mode"),
                "type": lock_match.group("lock_type"),
                "id1": lock_match.group("id1"),
                "id2": lock_match.group("id2"),
            }
            deadlock["locks"].append(lock)

    def get_deadlock_summary(self, deadlocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from deadlock list.

        Args:
            deadlocks: List of deadlock entries

        Returns:
            Summary statistics
        """
        if not deadlocks:
            return {
                "total_deadlocks": 0,
                "unique_sessions": set(),
                "unique_sql_ids": set(),
                "lock_types": {},
                "most_recent": None,
            }

        unique_sessions = set()
        unique_sql_ids = set()
        lock_types = {}

        for deadlock in deadlocks:
            # Collect unique sessions
            for session in deadlock.get("sessions", []):
                unique_sessions.add(session.get("session_id"))

            # Collect unique SQL_IDs
            for sql_id in deadlock.get("sql_ids", []):
                unique_sql_ids.add(sql_id)

            # Count lock types
            for lock in deadlock.get("locks", []):
                lock_type = lock.get("type", "UNKNOWN")
                lock_types[lock_type] = lock_types.get(lock_type, 0) + 1

        return {
            "total_deadlocks": len(deadlocks),
            "unique_sessions": len(unique_sessions),
            "unique_sql_ids": len(unique_sql_ids),
            "lock_types": lock_types,
            "most_recent": deadlocks[-1] if deadlocks else None,
        }


def parse_alert_log_from_diagnostic_dest(
    diagnostic_dest: str, db_name: str
) -> List[Dict[str, Any]]:
    """
    Parse alert log from Oracle diagnostic destination.

    Args:
        diagnostic_dest: Oracle DIAGNOSTIC_DEST parameter value
        db_name: Database name

    Returns:
        List of deadlock entries
    """
    # Construct alert log path
    # Typical location: $DIAGNOSTIC_DEST/diag/rdbms/{db_name}/{db_name}/trace/alert_{db_name}.log
    alert_log_path = Path(diagnostic_dest) / "diag" / "rdbms" / db_name.lower() / db_name.lower() / "trace" / f"alert_{db_name.lower()}.log"

    if not alert_log_path.exists():
        logger.warning(f"Alert log not found at: {alert_log_path}")
        return []

    parser = AlertLogParser(str(alert_log_path))
    return parser.parse_deadlocks()
