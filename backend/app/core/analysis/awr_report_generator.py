"""AWR Report Generator.

This module generates AWR-like performance reports based on
snapshot data from the Oracle AWR repository.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.oracle.awr_ash import AWRASHFetcher
from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class AWRReportGenerator:
    """Generator for AWR-style performance reports."""

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize AWR Report Generator.

        Args:
            connection_manager: Oracle connection manager
        """
        self.connection_manager = connection_manager
        self.awr_fetcher = AWRASHFetcher(connection_manager)

    def generate_report(
        self,
        begin_snap_id: int,
        end_snap_id: int,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AWR report between two snapshots.

        Args:
            begin_snap_id: Beginning snapshot ID
            end_snap_id: Ending snapshot ID
            top_n: Number of top items to include

        Returns:
            Complete AWR report dictionary
        """
        if not self.awr_fetcher.check_awr_availability():
            return {
                "error": "AWR data not available",
                "message": "AWR requires Oracle Diagnostics Pack license"
            }

        try:
            logger.info(f"Generating AWR report: snapshots {begin_snap_id} to {end_snap_id}")

            # Get snapshot information
            snapshots = self._get_snapshot_info(begin_snap_id, end_snap_id)

            if not snapshots or len(snapshots) < 2:
                return {
                    "error": "Invalid snapshots",
                    "message": "Could not find begin and end snapshots"
                }

            begin_snapshot = snapshots[0]
            end_snapshot = snapshots[1]

            # Calculate elapsed time
            elapsed_time = self._calculate_elapsed_time(begin_snapshot, end_snapshot)

            # Build report sections
            report = {
                "report_info": {
                    "begin_snap_id": begin_snap_id,
                    "end_snap_id": end_snap_id,
                    "begin_time": begin_snapshot.get('begin_interval_time'),
                    "end_time": end_snapshot.get('end_interval_time'),
                    "elapsed_time_minutes": elapsed_time,
                    "generated_at": datetime.utcnow().isoformat(),
                },
                "database_info": self._get_database_info(),
                "load_profile": self._generate_load_profile(begin_snap_id, end_snap_id, elapsed_time),
                "top_sql_by_elapsed_time": self._get_top_sql_by_metric(
                    begin_snap_id, end_snap_id, "elapsed_time", top_n
                ),
                "top_sql_by_cpu": self._get_top_sql_by_metric(
                    begin_snap_id, end_snap_id, "cpu_time", top_n
                ),
                "top_sql_by_gets": self._get_top_sql_by_metric(
                    begin_snap_id, end_snap_id, "buffer_gets", top_n
                ),
                "top_sql_by_reads": self._get_top_sql_by_metric(
                    begin_snap_id, end_snap_id, "disk_reads", top_n
                ),
                "top_sql_by_executions": self._get_top_sql_by_metric(
                    begin_snap_id, end_snap_id, "executions", top_n
                ),
                "wait_events": self.awr_fetcher.fetch_system_wait_events(
                    begin_snap_id, end_snap_id
                ),
                "wait_events_summary": self._summarize_wait_events(
                    begin_snap_id, end_snap_id
                ),
                "time_model_statistics": self._get_time_model_stats(
                    begin_snap_id, end_snap_id
                ),
                "instance_efficiency": self._calculate_instance_efficiency(
                    begin_snap_id, end_snap_id
                ),
                "recommendations": self._generate_recommendations(
                    begin_snap_id, end_snap_id
                ),
            }

            logger.info(f"AWR report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Error generating AWR report: {e}", exc_info=True)
            raise

    def _get_snapshot_info(
        self,
        begin_snap_id: int,
        end_snap_id: int
    ) -> List[Dict[str, Any]]:
        """Get information for begin and end snapshots."""
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
                WHERE snap_id IN (:begin_snap_id, :end_snap_id)
                ORDER BY snap_id
            """

            cursor.execute(query, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id)

            columns = [col[0].lower() for col in cursor.description]
            snapshots = []

            for row in cursor:
                snapshot = dict(zip(columns, row))
                # Convert datetime objects
                for key in ['begin_interval_time', 'end_interval_time', 'startup_time']:
                    if key in snapshot and snapshot[key]:
                        snapshot[key] = snapshot[key].isoformat()
                snapshots.append(snapshot)

            cursor.close()
            return snapshots

        except Exception as e:
            logger.error(f"Error fetching snapshot info: {e}", exc_info=True)
            return []

    def _calculate_elapsed_time(
        self,
        begin_snapshot: Dict[str, Any],
        end_snapshot: Dict[str, Any]
    ) -> float:
        """Calculate elapsed time between snapshots in minutes."""
        try:
            begin_time = datetime.fromisoformat(begin_snapshot['begin_interval_time'])
            end_time = datetime.fromisoformat(end_snapshot['end_interval_time'])
            elapsed = (end_time - begin_time).total_seconds() / 60
            return round(elapsed, 2)
        except Exception as e:
            logger.warning(f"Could not calculate elapsed time: {e}")
            return 0.0

    def _get_database_info(self) -> Dict[str, Any]:
        """Get database instance information."""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    instance_name,
                    host_name,
                    version,
                    startup_time,
                    status,
                    database_role
                FROM v$instance
            """

            cursor.execute(query)
            row = cursor.fetchone()

            if row:
                columns = [col[0].lower() for col in cursor.description]
                info = dict(zip(columns, row))
                if 'startup_time' in info and info['startup_time']:
                    info['startup_time'] = info['startup_time'].isoformat()
                cursor.close()
                return info

            cursor.close()
            return {}

        except Exception as e:
            logger.warning(f"Could not get database info: {e}")
            return {}

    def _generate_load_profile(
        self,
        begin_snap_id: int,
        end_snap_id: int,
        elapsed_time_minutes: float
    ) -> Dict[str, Any]:
        """Generate load profile statistics."""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            # Get system statistics delta between snapshots
            query = """
                SELECT
                    stat_name,
                    value - LAG(value) OVER (PARTITION BY stat_name ORDER BY snap_id) as value_delta
                FROM dba_hist_sysstat
                WHERE snap_id IN (:begin_snap_id, :end_snap_id)
                    AND stat_name IN (
                        'user commits',
                        'user rollbacks',
                        'user calls',
                        'execute count',
                        'parse count (total)',
                        'parse count (hard)',
                        'physical reads',
                        'physical writes',
                        'redo size',
                        'session logical reads',
                        'db block changes'
                    )
                    AND snap_id = :end_snap_id
            """

            cursor.execute(query, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id)

            load_profile = {}
            for row in cursor:
                stat_name, value_delta = row
                if value_delta and elapsed_time_minutes > 0:
                    # Calculate per second and per transaction rates
                    per_second = value_delta / (elapsed_time_minutes * 60)
                    load_profile[stat_name] = {
                        "total": value_delta,
                        "per_second": round(per_second, 2),
                    }

            cursor.close()
            return load_profile

        except Exception as e:
            logger.warning(f"Could not generate load profile: {e}")
            return {}

    def _get_top_sql_by_metric(
        self,
        begin_snap_id: int,
        end_snap_id: int,
        metric: str,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """
        Get top SQL statements by specified metric.

        Args:
            begin_snap_id: Beginning snapshot
            end_snap_id: Ending snapshot
            metric: Metric name (elapsed_time, cpu_time, buffer_gets, etc.)
            top_n: Number of top SQL to return

        Returns:
            List of top SQL statements
        """
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            # Map metric names to column names
            metric_column_map = {
                "elapsed_time": "elapsed_time_delta",
                "cpu_time": "cpu_time_delta",
                "buffer_gets": "buffer_gets_delta",
                "disk_reads": "disk_reads_delta",
                "executions": "executions_delta",
                "rows_processed": "rows_processed_delta",
            }

            column_name = metric_column_map.get(metric, "elapsed_time_delta")

            query = f"""
                SELECT
                    sql_id,
                    plan_hash_value,
                    SUM(executions_delta) as executions,
                    SUM(elapsed_time_delta) / 1000000 as elapsed_time_sec,
                    SUM(cpu_time_delta) / 1000000 as cpu_time_sec,
                    SUM(buffer_gets_delta) as buffer_gets,
                    SUM(disk_reads_delta) as disk_reads,
                    SUM(rows_processed_delta) as rows_processed,
                    SUM(parse_calls_delta) as parse_calls,
                    CASE WHEN SUM(executions_delta) > 0
                        THEN SUM(elapsed_time_delta) / SUM(executions_delta) / 1000000
                        ELSE 0
                    END as avg_elapsed_sec
                FROM dba_hist_sqlstat
                WHERE snap_id BETWEEN :begin_snap_id AND :end_snap_id
                GROUP BY sql_id, plan_hash_value
                ORDER BY SUM({column_name}) DESC
                FETCH FIRST :top_n ROWS ONLY
            """

            cursor.execute(query, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id, top_n=top_n)

            columns = [col[0].lower() for col in cursor.description]
            top_sql = []

            for row in cursor:
                sql_stat = dict(zip(columns, row))
                top_sql.append(sql_stat)

            cursor.close()
            logger.info(f"Fetched top {len(top_sql)} SQL by {metric}")

            return top_sql

        except Exception as e:
            logger.error(f"Error fetching top SQL by {metric}: {e}", exc_info=True)
            return []

    def _summarize_wait_events(
        self,
        begin_snap_id: int,
        end_snap_id: int
    ) -> Dict[str, Any]:
        """Summarize wait events by wait class."""
        wait_events = self.awr_fetcher.fetch_system_wait_events(begin_snap_id, end_snap_id)

        if not wait_events:
            return {}

        # Group by wait class
        wait_class_summary = {}
        total_time = sum(e.get('time_waited_sec', 0) for e in wait_events)

        for event in wait_events:
            wait_class = event.get('wait_class', 'Other')
            time_waited = event.get('time_waited_sec', 0)

            if wait_class not in wait_class_summary:
                wait_class_summary[wait_class] = {
                    "total_time_sec": 0,
                    "total_waits": 0,
                    "event_count": 0,
                }

            wait_class_summary[wait_class]["total_time_sec"] += time_waited
            wait_class_summary[wait_class]["total_waits"] += event.get('total_waits_delta', 0)
            wait_class_summary[wait_class]["event_count"] += 1

        # Calculate percentages
        for wait_class in wait_class_summary:
            time_sec = wait_class_summary[wait_class]["total_time_sec"]
            if total_time > 0:
                wait_class_summary[wait_class]["percentage"] = round(
                    (time_sec / total_time) * 100, 2
                )
            else:
                wait_class_summary[wait_class]["percentage"] = 0

        return {
            "by_wait_class": wait_class_summary,
            "total_wait_time_sec": total_time,
            "top_wait_class": max(
                wait_class_summary.items(),
                key=lambda x: x[1]["total_time_sec"]
            )[0] if wait_class_summary else None
        }

    def _get_time_model_stats(
        self,
        begin_snap_id: int,
        end_snap_id: int
    ) -> Dict[str, Any]:
        """Get time model statistics."""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = """
                SELECT
                    stat_name,
                    value - LAG(value) OVER (PARTITION BY stat_name ORDER BY snap_id) as value_delta
                FROM dba_hist_sys_time_model
                WHERE snap_id IN (:begin_snap_id, :end_snap_id)
                    AND snap_id = :end_snap_id
                ORDER BY value_delta DESC NULLS LAST
            """

            cursor.execute(query, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id)

            time_model = {}
            total_db_time = 0

            for row in cursor:
                stat_name, value_delta = row
                if value_delta and value_delta > 0:
                    time_sec = value_delta / 1000000  # Convert microseconds to seconds
                    time_model[stat_name] = {
                        "time_sec": round(time_sec, 2)
                    }
                    if stat_name == "DB time":
                        total_db_time = time_sec

            # Calculate percentages of DB time
            if total_db_time > 0:
                for stat_name in time_model:
                    if stat_name != "DB time":
                        time_sec = time_model[stat_name]["time_sec"]
                        time_model[stat_name]["percentage_of_db_time"] = round(
                            (time_sec / total_db_time) * 100, 2
                        )

            cursor.close()
            return time_model

        except Exception as e:
            logger.warning(f"Could not get time model stats: {e}")
            return {}

    def _calculate_instance_efficiency(
        self,
        begin_snap_id: int,
        end_snap_id: int
    ) -> Dict[str, Any]:
        """Calculate instance efficiency percentages."""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            # Get statistics needed for efficiency calculations
            query = """
                SELECT
                    stat_name,
                    value - LAG(value) OVER (PARTITION BY stat_name ORDER BY snap_id) as value_delta
                FROM dba_hist_sysstat
                WHERE snap_id IN (:begin_snap_id, :end_snap_id)
                    AND stat_name IN (
                        'session logical reads',
                        'physical reads',
                        'physical reads cache',
                        'db block gets',
                        'consistent gets',
                        'execute count',
                        'parse count (total)',
                        'parse count (hard)'
                    )
                    AND snap_id = :end_snap_id
            """

            cursor.execute(query, begin_snap_id=begin_snap_id, end_snap_id=end_snap_id)

            stats = {}
            for row in cursor:
                stat_name, value_delta = row
                if value_delta:
                    stats[stat_name] = value_delta

            cursor.close()

            # Calculate efficiency ratios
            efficiency = {}

            # Buffer Hit Ratio
            logical_reads = stats.get('session logical reads', 0)
            physical_reads = stats.get('physical reads', 0)
            if logical_reads > 0:
                buffer_hit_ratio = ((logical_reads - physical_reads) / logical_reads) * 100
                efficiency['buffer_cache_hit_ratio'] = round(buffer_hit_ratio, 2)

            # Library Cache Hit Ratio (soft parse ratio)
            total_parses = stats.get('parse count (total)', 0)
            hard_parses = stats.get('parse count (hard)', 0)
            if total_parses > 0:
                soft_parse_ratio = ((total_parses - hard_parses) / total_parses) * 100
                efficiency['soft_parse_ratio'] = round(soft_parse_ratio, 2)

            # Execute to Parse Ratio
            executions = stats.get('execute count', 0)
            if executions > 0 and total_parses > 0:
                execute_to_parse = (executions / total_parses)
                efficiency['execute_to_parse_ratio'] = round(execute_to_parse, 2)

            return efficiency

        except Exception as e:
            logger.warning(f"Could not calculate instance efficiency: {e}")
            return {}

    def _generate_recommendations(
        self,
        begin_snap_id: int,
        end_snap_id: int
    ) -> List[str]:
        """Generate performance recommendations based on AWR data."""
        recommendations = []

        # Check efficiency metrics
        efficiency = self._calculate_instance_efficiency(begin_snap_id, end_snap_id)

        buffer_hit_ratio = efficiency.get('buffer_cache_hit_ratio', 100)
        if buffer_hit_ratio < 90:
            recommendations.append(
                f"Buffer cache hit ratio is {buffer_hit_ratio}%. "
                "Consider increasing buffer cache size (db_cache_size)."
            )

        soft_parse_ratio = efficiency.get('soft_parse_ratio', 100)
        if soft_parse_ratio < 80:
            recommendations.append(
                f"Soft parse ratio is {soft_parse_ratio}%. "
                "Consider using bind variables to reduce hard parsing."
            )

        # Check wait events
        wait_summary = self._summarize_wait_events(begin_snap_id, end_snap_id)
        top_wait_class = wait_summary.get('top_wait_class')

        if top_wait_class == 'User I/O':
            recommendations.append(
                "User I/O is the top wait class. "
                "Consider adding indexes, partitioning, or optimizing SQL to reduce I/O."
            )
        elif top_wait_class == 'Concurrency':
            recommendations.append(
                "Concurrency waits detected. "
                "Review locking strategy and consider reducing lock contention."
            )

        if not recommendations:
            recommendations.append("System performance appears healthy. No critical issues detected.")

        return recommendations

    def export_report_html(self, report: Dict[str, Any]) -> str:
        """
        Export AWR report to HTML format.

        Args:
            report: AWR report dictionary

        Returns:
            HTML string
        """
        # Simple HTML export - can be enhanced with templates
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AWR Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 1px solid #ccc; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .info {{ background-color: #e7f3fe; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>AWR Performance Report</h1>
            <div class="info">
                <p><strong>Begin Snapshot:</strong> {report['report_info']['begin_snap_id']}
                   ({report['report_info']['begin_time']})</p>
                <p><strong>End Snapshot:</strong> {report['report_info']['end_snap_id']}
                   ({report['report_info']['end_time']})</p>
                <p><strong>Elapsed Time:</strong> {report['report_info']['elapsed_time_minutes']} minutes</p>
            </div>

            <h2>Recommendations</h2>
            <ul>
                {''.join(f'<li>{r}</li>' for r in report.get('recommendations', []))}
            </ul>

            <h2>Top SQL by Elapsed Time</h2>
            {self._sql_table_html(report.get('top_sql_by_elapsed_time', []))}

            <h2>Wait Events Summary</h2>
            {self._wait_events_html(report.get('wait_events_summary', {}))}
        </body>
        </html>
        """
        return html

    def _sql_table_html(self, sql_list: List[Dict[str, Any]]) -> str:
        """Generate HTML table for SQL list."""
        if not sql_list:
            return "<p>No data available</p>"

        html = """
        <table>
            <tr>
                <th>SQL_ID</th>
                <th>Executions</th>
                <th>Elapsed Time (s)</th>
                <th>CPU Time (s)</th>
                <th>Buffer Gets</th>
            </tr>
        """

        for sql in sql_list:
            html += f"""
            <tr>
                <td>{sql.get('sql_id', 'N/A')}</td>
                <td>{sql.get('executions', 0)}</td>
                <td>{sql.get('elapsed_time_sec', 0):.2f}</td>
                <td>{sql.get('cpu_time_sec', 0):.2f}</td>
                <td>{sql.get('buffer_gets', 0)}</td>
            </tr>
            """

        html += "</table>"
        return html

    def _wait_events_html(self, wait_summary: Dict[str, Any]) -> str:
        """Generate HTML for wait events summary."""
        if not wait_summary:
            return "<p>No data available</p>"

        by_wait_class = wait_summary.get('by_wait_class', {})

        html = """
        <table>
            <tr>
                <th>Wait Class</th>
                <th>Time Waited (s)</th>
                <th>% of Total</th>
            </tr>
        """

        for wait_class, stats in sorted(
            by_wait_class.items(),
            key=lambda x: x[1]['total_time_sec'],
            reverse=True
        ):
            html += f"""
            <tr>
                <td>{wait_class}</td>
                <td>{stats['total_time_sec']:.2f}</td>
                <td>{stats['percentage']:.1f}%</td>
            </tr>
            """

        html += "</table>"
        return html
