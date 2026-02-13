"""WebSocket endpoints for real-time monitoring."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, Dict, Any
import logging

from app.core.websocket.base import BaseWebSocketHandler
from app.core.oracle.connection import get_connection_manager as get_oracle_connection_manager
from app.core.oracle.queries import QueryFetcher

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryMonitoringHandler(BaseWebSocketHandler):
    """WebSocket handler for real-time query monitoring."""

    def __init__(
        self,
        websocket: WebSocket,
        poll_interval: float = 5.0,
        min_elapsed_time: float = 0.1,
        limit: int = 10
    ):
        """
        Initialize query monitoring handler.

        Args:
            websocket: WebSocket connection
            poll_interval: Polling interval in seconds
            min_elapsed_time: Minimum elapsed time threshold
            limit: Maximum number of queries to return
        """
        super().__init__(websocket, "queries", poll_interval)
        self.min_elapsed_time = min_elapsed_time
        self.limit = limit
        self.oracle_conn_manager = get_oracle_connection_manager()
        self.query_fetcher = QueryFetcher(self.oracle_conn_manager)
        self.previous_queries = {}

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch top queries from V$SQL."""
        try:
            # Fetch top queries
            queries = self.query_fetcher.fetch_top_queries(
                limit=self.limit,
                order_by="elapsed_time",
                min_elapsed_time=self.min_elapsed_time * 1000000  # Convert to microseconds
            )

            # Track new queries
            new_queries = []
            updated_queries = []

            current_sql_ids = set()

            for query in queries:
                sql_id = query.get("sql_id")
                if not sql_id:
                    continue

                current_sql_ids.add(sql_id)

                if sql_id not in self.previous_queries:
                    new_queries.append(sql_id)
                else:
                    # Check if metrics changed significantly
                    prev = self.previous_queries[sql_id]
                    curr_elapsed = query.get("elapsed_time", 0)
                    prev_elapsed = prev.get("elapsed_time", 0)

                    if curr_elapsed > prev_elapsed * 1.1:  # 10% increase
                        updated_queries.append(sql_id)

                self.previous_queries[sql_id] = query

            # Clean up queries no longer in top list
            removed_sql_ids = set(self.previous_queries.keys()) - current_sql_ids
            for sql_id in removed_sql_ids:
                del self.previous_queries[sql_id]

            return {
                "queries": queries,
                "new_queries": new_queries,
                "updated_queries": updated_queries,
                "total_count": len(queries),
            }

        except Exception as e:
            logger.error(f"Error fetching queries: {e}", exc_info=True)
            return None


class SessionMonitoringHandler(BaseWebSocketHandler):
    """WebSocket handler for real-time session monitoring."""

    def __init__(
        self,
        websocket: WebSocket,
        poll_interval: float = 5.0,
        show_inactive: bool = False
    ):
        """
        Initialize session monitoring handler.

        Args:
            websocket: WebSocket connection
            poll_interval: Polling interval in seconds
            show_inactive: Include inactive sessions
        """
        super().__init__(websocket, "sessions", poll_interval)
        self.show_inactive = show_inactive
        self.oracle_conn_manager = get_oracle_connection_manager()

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch active sessions from V$SESSION."""
        try:
            connection = self.oracle_conn_manager.get_connection()
            cursor = connection.cursor()

            # Build query
            query = """
                SELECT
                    sid,
                    serial#,
                    username,
                    status,
                    osuser,
                    machine,
                    program,
                    sql_id,
                    sql_exec_start,
                    blocking_session,
                    blocking_session_status,
                    event,
                    wait_class,
                    seconds_in_wait,
                    state,
                    last_call_et
                FROM v$session
                WHERE type = 'USER'
            """

            if not self.show_inactive:
                query += " AND status = 'ACTIVE'"

            query += " ORDER BY last_call_et DESC"

            cursor.execute(query)

            columns = [col[0].lower() for col in cursor.description]
            sessions = []

            for row in cursor:
                session = dict(zip(columns, row))

                # Convert datetime objects
                if session.get('sql_exec_start'):
                    session['sql_exec_start'] = session['sql_exec_start'].isoformat()

                sessions.append(session)

            cursor.close()

            # Calculate summary statistics
            active_count = sum(1 for s in sessions if s.get('status') == 'ACTIVE')
            blocked_count = sum(1 for s in sessions if s.get('blocking_session') is not None)

            return {
                "sessions": sessions,
                "total_count": len(sessions),
                "active_count": active_count,
                "blocked_count": blocked_count,
            }

        except Exception as e:
            logger.error(f"Error fetching sessions: {e}", exc_info=True)
            return None


class WaitEventsMonitoringHandler(BaseWebSocketHandler):
    """WebSocket handler for real-time wait event monitoring."""

    def __init__(
        self,
        websocket: WebSocket,
        poll_interval: float = 5.0
    ):
        """
        Initialize wait events monitoring handler.

        Args:
            websocket: WebSocket connection
            poll_interval: Polling interval in seconds
        """
        super().__init__(websocket, "wait-events", poll_interval)
        self.oracle_conn_manager = get_oracle_connection_manager()
        self.previous_stats = {}

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch wait events from V$SYSTEM_EVENT."""
        try:
            connection = self.oracle_conn_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    event,
                    wait_class,
                    total_waits,
                    total_timeouts,
                    time_waited,
                    average_wait
                FROM v$system_event
                WHERE wait_class != 'Idle'
                ORDER BY time_waited DESC
                FETCH FIRST 20 ROWS ONLY
            """

            cursor.execute(query)

            columns = [col[0].lower() for col in cursor.description]
            current_events = []

            for row in cursor:
                event = dict(zip(columns, row))
                current_events.append(event)

            cursor.close()

            # Calculate deltas
            events_with_delta = []
            for event in current_events:
                event_name = event['event']

                if event_name in self.previous_stats:
                    prev = self.previous_stats[event_name]
                    delta_waits = event['total_waits'] - prev.get('total_waits', 0)
                    delta_time = event['time_waited'] - prev.get('time_waited', 0)

                    event['delta_waits'] = delta_waits
                    event['delta_time_waited'] = delta_time
                else:
                    event['delta_waits'] = 0
                    event['delta_time_waited'] = 0

                events_with_delta.append(event)
                self.previous_stats[event_name] = event

            # Group by wait class
            wait_class_summary = {}
            for event in events_with_delta:
                wait_class = event['wait_class']
                if wait_class not in wait_class_summary:
                    wait_class_summary[wait_class] = {
                        'total_time': 0,
                        'event_count': 0,
                    }

                wait_class_summary[wait_class]['total_time'] += event['time_waited']
                wait_class_summary[wait_class]['event_count'] += 1

            return {
                "events": events_with_delta,
                "wait_class_summary": wait_class_summary,
                "total_events": len(events_with_delta),
            }

        except Exception as e:
            logger.error(f"Error fetching wait events: {e}", exc_info=True)
            return None


class MetricsMonitoringHandler(BaseWebSocketHandler):
    """WebSocket handler for real-time database metrics."""

    def __init__(
        self,
        websocket: WebSocket,
        poll_interval: float = 5.0
    ):
        """
        Initialize metrics monitoring handler.

        Args:
            websocket: WebSocket connection
            poll_interval: Polling interval in seconds
        """
        super().__init__(websocket, "metrics", poll_interval)
        self.oracle_conn_manager = get_oracle_connection_manager()
        self.previous_stats = {}

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch database metrics from V$SYSSTAT."""
        try:
            connection = self.oracle_conn_manager.get_connection()
            cursor = connection.cursor()

            # Key metrics to monitor
            metrics_to_fetch = [
                'user commits',
                'user rollbacks',
                'user calls',
                'execute count',
                'parse count (total)',
                'parse count (hard)',
                'physical reads',
                'physical writes',
                'session logical reads',
                'redo size',
                'db block changes',
            ]

            placeholders = ','.join([f":{i+1}" for i in range(len(metrics_to_fetch))])

            query = f"""
                SELECT name, value
                FROM v$sysstat
                WHERE name IN ({placeholders})
            """

            cursor.execute(query, metrics_to_fetch)

            current_stats = {}
            for row in cursor:
                name, value = row
                current_stats[name] = value

            cursor.close()

            # Calculate deltas and rates
            metrics_with_delta = {}
            elapsed_time = self.poll_interval

            for name, value in current_stats.items():
                if name in self.previous_stats:
                    delta = value - self.previous_stats[name]
                    rate_per_sec = delta / elapsed_time if elapsed_time > 0 else 0

                    metrics_with_delta[name] = {
                        'value': value,
                        'delta': delta,
                        'rate_per_sec': round(rate_per_sec, 2),
                    }
                else:
                    metrics_with_delta[name] = {
                        'value': value,
                        'delta': 0,
                        'rate_per_sec': 0,
                    }

                self.previous_stats[name] = value

            # Calculate derived metrics
            if 'session logical reads' in current_stats and 'physical reads' in current_stats:
                logical_reads = current_stats.get('session logical reads', 0)
                physical_reads = current_stats.get('physical reads', 0)

                if logical_reads > 0:
                    buffer_hit_ratio = ((logical_reads - physical_reads) / logical_reads) * 100
                    metrics_with_delta['buffer_cache_hit_ratio'] = {
                        'value': round(buffer_hit_ratio, 2),
                        'delta': 0,
                        'rate_per_sec': 0,
                    }

            return {
                "metrics": metrics_with_delta,
                "timestamp": elapsed_time,
            }

        except Exception as e:
            logger.error(f"Error fetching metrics: {e}", exc_info=True)
            return None


@router.websocket("/ws/queries")
async def websocket_queries(
    websocket: WebSocket,
    poll_interval: float = Query(5.0, ge=1.0, le=60.0),
    min_elapsed_time: float = Query(0.1, ge=0.0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    WebSocket endpoint for real-time query monitoring.

    Args:
        websocket: WebSocket connection
        poll_interval: Polling interval in seconds (1-60)
        min_elapsed_time: Minimum elapsed time threshold in seconds
        limit: Maximum number of queries to return (1-100)
    """
    handler = QueryMonitoringHandler(
        websocket,
        poll_interval=poll_interval,
        min_elapsed_time=min_elapsed_time,
        limit=limit
    )
    await handler.handle_connection()


@router.websocket("/ws/sessions")
async def websocket_sessions(
    websocket: WebSocket,
    poll_interval: float = Query(5.0, ge=1.0, le=60.0),
    show_inactive: bool = Query(False)
):
    """
    WebSocket endpoint for real-time session monitoring.

    Args:
        websocket: WebSocket connection
        poll_interval: Polling interval in seconds (1-60)
        show_inactive: Include inactive sessions
    """
    handler = SessionMonitoringHandler(
        websocket,
        poll_interval=poll_interval,
        show_inactive=show_inactive
    )
    await handler.handle_connection()


@router.websocket("/ws/wait-events")
async def websocket_wait_events(
    websocket: WebSocket,
    poll_interval: float = Query(5.0, ge=1.0, le=60.0)
):
    """
    WebSocket endpoint for real-time wait event monitoring.

    Args:
        websocket: WebSocket connection
        poll_interval: Polling interval in seconds (1-60)
    """
    handler = WaitEventsMonitoringHandler(
        websocket,
        poll_interval=poll_interval
    )
    await handler.handle_connection()


@router.websocket("/ws/metrics")
async def websocket_metrics(
    websocket: WebSocket,
    poll_interval: float = Query(5.0, ge=1.0, le=60.0)
):
    """
    WebSocket endpoint for real-time database metrics monitoring.

    Args:
        websocket: WebSocket connection
        poll_interval: Polling interval in seconds (1-60)
    """
    handler = MetricsMonitoringHandler(
        websocket,
        poll_interval=poll_interval
    )
    await handler.handle_connection()
