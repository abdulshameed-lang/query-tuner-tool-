"""Active Session History (ASH) Analyzer.

This module analyzes Active Session History data to identify
performance bottlenecks, resource consumption patterns, and
activity trends over time.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.core.oracle.awr_ash import AWRASHFetcher
from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class ASHAnalyzer:
    """Analyzer for Active Session History data."""

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize ASH Analyzer.

        Args:
            connection_manager: Oracle connection manager
        """
        self.connection_manager = connection_manager
        self.awr_fetcher = AWRASHFetcher(connection_manager)

    def analyze_sql_activity(
        self,
        sql_id: str,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze activity for a specific SQL_ID using ASH data.

        Args:
            sql_id: SQL_ID to analyze
            begin_time: Start time for analysis
            end_time: End time for analysis

        Returns:
            Activity analysis results
        """
        if not self.awr_fetcher.check_ash_availability():
            return {
                "error": "ASH data not available",
                "message": "ASH requires Oracle Diagnostics Pack license"
            }

        # Default to last hour if no time range specified
        if not end_time:
            end_time = datetime.utcnow()
        if not begin_time:
            begin_time = end_time - timedelta(hours=1)

        # Fetch ASH samples for this SQL_ID
        samples = self.awr_fetcher.fetch_ash_activity(
            sql_id=sql_id,
            begin_time=begin_time,
            end_time=end_time
        )

        if not samples:
            return {
                "sql_id": sql_id,
                "sample_count": 0,
                "message": "No ASH samples found for this SQL_ID"
            }

        # Analyze the samples
        analysis = {
            "sql_id": sql_id,
            "time_range": {
                "begin": begin_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "sample_count": len(samples),
            "activity_timeline": self._build_activity_timeline(samples),
            "wait_event_analysis": self._analyze_wait_events(samples),
            "session_analysis": self._analyze_sessions(samples),
            "blocking_analysis": self._analyze_blocking(samples),
            "execution_activity": self._analyze_execution_activity(samples),
        }

        return analysis

    def analyze_time_period(
        self,
        begin_time: datetime,
        end_time: datetime,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze database activity for a time period.

        Args:
            begin_time: Start time
            end_time: End time
            top_n: Number of top items to return

        Returns:
            Time period analysis
        """
        if not self.awr_fetcher.check_ash_availability():
            return {
                "error": "ASH data not available"
            }

        # Get ASH samples for time period
        samples = self.awr_fetcher.fetch_ash_activity(
            begin_time=begin_time,
            end_time=end_time,
            limit=10000
        )

        if not samples:
            return {
                "sample_count": 0,
                "message": "No ASH samples found for this time period"
            }

        analysis = {
            "time_range": {
                "begin": begin_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "sample_count": len(samples),
            "top_sql": self._get_top_sql_from_samples(samples, top_n),
            "top_wait_events": self._get_top_wait_events(samples, top_n),
            "top_sessions": self._get_top_sessions(samples, top_n),
            "activity_by_wait_class": self._group_by_wait_class(samples),
            "cpu_vs_wait_breakdown": self._analyze_cpu_vs_wait(samples),
            "activity_heatmap_data": self._generate_heatmap_data(samples),
        }

        return analysis

    def _build_activity_timeline(
        self,
        samples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build timeline of activity over time."""
        # Group samples by time bucket (e.g., 1 minute intervals)
        timeline = defaultdict(lambda: {
            "sample_count": 0,
            "cpu_samples": 0,
            "wait_samples": 0,
            "sessions": set(),
        })

        for sample in samples:
            sample_time = sample.get('sample_time')
            if not sample_time:
                continue

            # Parse time and round to minute
            dt = datetime.fromisoformat(sample_time)
            time_bucket = dt.replace(second=0, microsecond=0).isoformat()

            timeline[time_bucket]["sample_count"] += 1

            session_state = sample.get('session_state', '')
            if session_state == 'ON CPU':
                timeline[time_bucket]["cpu_samples"] += 1
            elif session_state == 'WAITING':
                timeline[time_bucket]["wait_samples"] += 1

            session_id = sample.get('session_id')
            if session_id:
                timeline[time_bucket]["sessions"].add(session_id)

        # Convert to list format
        timeline_list = []
        for time_bucket, stats in sorted(timeline.items()):
            timeline_list.append({
                "timestamp": time_bucket,
                "sample_count": stats["sample_count"],
                "cpu_samples": stats["cpu_samples"],
                "wait_samples": stats["wait_samples"],
                "active_sessions": len(stats["sessions"]),
            })

        return timeline_list

    def _analyze_wait_events(
        self,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze wait events from samples."""
        wait_events = defaultdict(lambda: {
            "sample_count": 0,
            "total_wait_time": 0,
            "wait_class": None,
        })

        total_samples = len(samples)
        total_wait_time = 0

        for sample in samples:
            event = sample.get('event')
            wait_time = sample.get('time_waited', 0)
            wait_class = sample.get('wait_class')

            if event:
                wait_events[event]["sample_count"] += 1
                wait_events[event]["total_wait_time"] += wait_time if wait_time else 0
                wait_events[event]["wait_class"] = wait_class
                total_wait_time += wait_time if wait_time else 0

        # Convert to list and calculate percentages
        event_list = []
        for event, stats in wait_events.items():
            event_list.append({
                "event": event,
                "wait_class": stats["wait_class"],
                "sample_count": stats["sample_count"],
                "percentage": round((stats["sample_count"] / total_samples) * 100, 2) if total_samples > 0 else 0,
                "total_wait_time": stats["total_wait_time"],
                "avg_wait_time": round(stats["total_wait_time"] / stats["sample_count"], 2) if stats["sample_count"] > 0 else 0,
            })

        # Sort by sample count
        event_list.sort(key=lambda x: x["sample_count"], reverse=True)

        return {
            "events": event_list,
            "unique_event_count": len(wait_events),
            "total_wait_time": total_wait_time,
        }

    def _analyze_sessions(
        self,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze session activity."""
        sessions = defaultdict(lambda: {
            "sample_count": 0,
            "programs": set(),
            "modules": set(),
            "sql_ids": set(),
        })

        for sample in samples:
            session_id = sample.get('session_id')
            if not session_id:
                continue

            sessions[session_id]["sample_count"] += 1

            program = sample.get('program')
            if program:
                sessions[session_id]["programs"].add(program)

            module = sample.get('module')
            if module:
                sessions[session_id]["modules"].add(module)

            sql_id = sample.get('sql_id')
            if sql_id:
                sessions[session_id]["sql_ids"].add(sql_id)

        # Convert to list
        session_list = []
        for session_id, stats in sessions.items():
            session_list.append({
                "session_id": session_id,
                "sample_count": stats["sample_count"],
                "programs": list(stats["programs"]),
                "modules": list(stats["modules"]),
                "unique_sql_count": len(stats["sql_ids"]),
            })

        # Sort by sample count
        session_list.sort(key=lambda x: x["sample_count"], reverse=True)

        return {
            "sessions": session_list,
            "unique_session_count": len(sessions),
        }

    def _analyze_blocking(
        self,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze blocking sessions."""
        blocking_events = []
        blocking_sessions = set()

        for sample in samples:
            blocking_session = sample.get('blocking_session')
            if blocking_session:
                blocking_sessions.add(blocking_session)
                blocking_events.append({
                    "sample_time": sample.get('sample_time'),
                    "blocked_session": sample.get('session_id'),
                    "blocking_session": blocking_session,
                    "wait_event": sample.get('event'),
                })

        return {
            "blocking_detected": len(blocking_events) > 0,
            "blocking_event_count": len(blocking_events),
            "unique_blocking_sessions": len(blocking_sessions),
            "blocking_events": blocking_events[:100],  # Limit to 100 events
        }

    def _analyze_execution_activity(
        self,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze execution plan activity."""
        plan_hash_values = defaultdict(int)

        for sample in samples:
            phv = sample.get('sql_plan_hash_value')
            if phv:
                plan_hash_values[phv] += 1

        # Convert to list
        plan_list = [
            {"plan_hash_value": phv, "sample_count": count}
            for phv, count in plan_hash_values.items()
        ]

        plan_list.sort(key=lambda x: x["sample_count"], reverse=True)

        return {
            "unique_plan_count": len(plan_hash_values),
            "plans": plan_list,
            "plan_instability": len(plan_hash_values) > 1,
        }

    def _get_top_sql_from_samples(
        self,
        samples: List[Dict[str, Any]],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Get top SQL from ASH samples."""
        sql_activity = defaultdict(lambda: {
            "sample_count": 0,
            "cpu_samples": 0,
            "wait_samples": 0,
        })

        for sample in samples:
            sql_id = sample.get('sql_id')
            if not sql_id:
                continue

            sql_activity[sql_id]["sample_count"] += 1

            session_state = sample.get('session_state', '')
            if session_state == 'ON CPU':
                sql_activity[sql_id]["cpu_samples"] += 1
            elif session_state == 'WAITING':
                sql_activity[sql_id]["wait_samples"] += 1

        # Convert to list
        sql_list = [
            {
                "sql_id": sql_id,
                "sample_count": stats["sample_count"],
                "cpu_samples": stats["cpu_samples"],
                "wait_samples": stats["wait_samples"],
            }
            for sql_id, stats in sql_activity.items()
        ]

        # Sort and limit
        sql_list.sort(key=lambda x: x["sample_count"], reverse=True)
        return sql_list[:top_n]

    def _get_top_wait_events(
        self,
        samples: List[Dict[str, Any]],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Get top wait events from samples."""
        wait_events = defaultdict(lambda: {
            "sample_count": 0,
            "wait_class": None,
        })

        for sample in samples:
            event = sample.get('event')
            if event:
                wait_events[event]["sample_count"] += 1
                wait_events[event]["wait_class"] = sample.get('wait_class')

        # Convert to list
        event_list = [
            {
                "event": event,
                "wait_class": stats["wait_class"],
                "sample_count": stats["sample_count"],
            }
            for event, stats in wait_events.items()
        ]

        # Sort and limit
        event_list.sort(key=lambda x: x["sample_count"], reverse=True)
        return event_list[:top_n]

    def _get_top_sessions(
        self,
        samples: List[Dict[str, Any]],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Get top sessions from samples."""
        session_activity = defaultdict(int)

        for sample in samples:
            session_id = sample.get('session_id')
            if session_id:
                session_activity[session_id] += 1

        # Convert to list
        session_list = [
            {"session_id": session_id, "sample_count": count}
            for session_id, count in session_activity.items()
        ]

        # Sort and limit
        session_list.sort(key=lambda x: x["sample_count"], reverse=True)
        return session_list[:top_n]

    def _group_by_wait_class(
        self,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Group activity by wait class."""
        wait_class_counts = defaultdict(int)

        for sample in samples:
            wait_class = sample.get('wait_class', 'Other')
            wait_class_counts[wait_class] += 1

        return dict(wait_class_counts)

    def _analyze_cpu_vs_wait(
        self,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze CPU vs wait time breakdown."""
        cpu_samples = 0
        wait_samples = 0

        for sample in samples:
            session_state = sample.get('session_state', '')
            if session_state == 'ON CPU':
                cpu_samples += 1
            elif session_state == 'WAITING':
                wait_samples += 1

        total = cpu_samples + wait_samples

        return {
            "cpu_samples": cpu_samples,
            "wait_samples": wait_samples,
            "cpu_percentage": round((cpu_samples / total) * 100, 2) if total > 0 else 0,
            "wait_percentage": round((wait_samples / total) * 100, 2) if total > 0 else 0,
        }

    def _generate_heatmap_data(
        self,
        samples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate heatmap data for visualization.

        Returns data in format suitable for heatmap charts
        showing activity intensity over time.
        """
        # Group by time bucket (e.g., 5-minute intervals)
        heatmap = defaultdict(lambda: defaultdict(int))

        for sample in samples:
            sample_time = sample.get('sample_time')
            wait_class = sample.get('wait_class', 'CPU')

            if not sample_time:
                continue

            # Parse time and round to 5-minute bucket
            dt = datetime.fromisoformat(sample_time)
            time_bucket = dt.replace(
                minute=(dt.minute // 5) * 5,
                second=0,
                microsecond=0
            ).isoformat()

            session_state = sample.get('session_state', '')
            if session_state == 'ON CPU':
                wait_class = 'CPU'

            heatmap[time_bucket][wait_class] += 1

        # Convert to list format
        heatmap_data = []
        for time_bucket, wait_classes in sorted(heatmap.items()):
            for wait_class, count in wait_classes.items():
                heatmap_data.append({
                    "timestamp": time_bucket,
                    "wait_class": wait_class,
                    "activity_count": count,
                })

        return heatmap_data

    def identify_bottlenecks(
        self,
        begin_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Identify performance bottlenecks using ASH data.

        Args:
            begin_time: Start time
            end_time: End time

        Returns:
            Bottleneck analysis with recommendations
        """
        analysis = self.analyze_time_period(begin_time, end_time, top_n=5)

        if 'error' in analysis:
            return analysis

        bottlenecks = []

        # Check CPU bottleneck
        cpu_vs_wait = analysis.get('cpu_vs_wait_breakdown', {})
        cpu_pct = cpu_vs_wait.get('cpu_percentage', 0)
        if cpu_pct > 70:
            bottlenecks.append({
                "type": "CPU",
                "severity": "high",
                "description": f"High CPU usage detected ({cpu_pct}% of samples on CPU)",
                "recommendation": "Review top SQL by CPU time and optimize CPU-intensive queries"
            })

        # Check top wait events
        top_wait_events = analysis.get('top_wait_events', [])
        if top_wait_events:
            top_event = top_wait_events[0]
            wait_class = top_event.get('wait_class', '')

            if wait_class == 'User I/O':
                bottlenecks.append({
                    "type": "I/O",
                    "severity": "high",
                    "description": f"I/O bottleneck detected: {top_event['event']}",
                    "recommendation": "Add indexes, partition tables, or optimize disk I/O"
                })
            elif wait_class == 'Concurrency':
                bottlenecks.append({
                    "type": "Concurrency",
                    "severity": "medium",
                    "description": f"Concurrency bottleneck: {top_event['event']}",
                    "recommendation": "Review locking patterns and reduce lock contention"
                })

        return {
            "time_range": analysis['time_range'],
            "bottlenecks": bottlenecks,
            "top_sql": analysis.get('top_sql', []),
            "top_wait_events": top_wait_events,
            "cpu_vs_wait": cpu_vs_wait,
        }
