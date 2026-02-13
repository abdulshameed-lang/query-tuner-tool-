"""Historical Performance Comparator.

This module compares current query performance against historical baselines
to detect regressions, improvements, and anomalies.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics
import logging

from app.core.oracle.awr_ash import AWRASHFetcher
from app.core.oracle.queries import QueryFetcher
from app.core.oracle.connection import ConnectionManager

logger = logging.getLogger(__name__)


class PerformanceTrend:
    """Performance trend classification."""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    ANOMALY = "anomaly"
    INSUFFICIENT_DATA = "insufficient_data"


class HistoricalComparator:
    """Compares current vs historical performance."""

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize Historical Comparator.

        Args:
            connection_manager: Oracle connection manager
        """
        self.connection_manager = connection_manager
        self.awr_fetcher = AWRASHFetcher(connection_manager)
        self.query_fetcher = QueryFetcher(connection_manager)

    def compare_current_vs_historical(
        self,
        sql_id: str,
        days_back: int = 7,
        threshold_percent: float = 20.0
    ) -> Dict[str, Any]:
        """
        Compare current performance against historical average.

        Args:
            sql_id: SQL_ID to compare
            days_back: Number of days of history to compare against
            threshold_percent: Percentage threshold for regression detection

        Returns:
            Comparison results with trend analysis
        """
        # Get current performance
        current_query = self.query_fetcher.fetch_query_by_sql_id(sql_id)

        if not current_query:
            return {
                "sql_id": sql_id,
                "error": "Query not found in V$SQL"
            }

        # Get historical performance
        historical_stats = self.awr_fetcher.fetch_historical_sql_stats(
            sql_id=sql_id,
            days_back=days_back
        )

        if not historical_stats or len(historical_stats) < 3:
            return {
                "sql_id": sql_id,
                "current": self._extract_current_metrics(current_query),
                "historical": None,
                "comparison": None,
                "trend": PerformanceTrend.INSUFFICIENT_DATA,
                "message": "Insufficient historical data for comparison"
            }

        # Calculate historical baseline
        historical_baseline = self._calculate_baseline(historical_stats)

        # Extract current metrics
        current_metrics = self._extract_current_metrics(current_query)

        # Perform comparison
        comparison = self._compare_metrics(
            current_metrics,
            historical_baseline,
            threshold_percent
        )

        # Determine trend
        trend = self._determine_trend(comparison, threshold_percent)

        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(
            comparison,
            trend
        )

        return {
            "sql_id": sql_id,
            "current": current_metrics,
            "historical": historical_baseline,
            "comparison": comparison,
            "trend": trend,
            "threshold_percent": threshold_percent,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    def analyze_performance_trend(
        self,
        sql_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze performance trend over time.

        Args:
            sql_id: SQL_ID to analyze
            days_back: Number of days to analyze

        Returns:
            Trend analysis with time-series data
        """
        historical_stats = self.awr_fetcher.fetch_historical_sql_stats(
            sql_id=sql_id,
            days_back=days_back
        )

        if not historical_stats or len(historical_stats) < 5:
            return {
                "sql_id": sql_id,
                "trend": PerformanceTrend.INSUFFICIENT_DATA,
                "message": "Insufficient data for trend analysis (minimum 5 samples required)"
            }

        # Build time series data
        time_series = self._build_time_series(historical_stats)

        # Calculate trend direction for key metrics
        metrics_trends = {
            "elapsed_time": self._calculate_trend_direction(
                [p['elapsed_time_sec'] for p in time_series if p.get('elapsed_time_sec')]
            ),
            "cpu_time": self._calculate_trend_direction(
                [p['cpu_time_sec'] for p in time_series if p.get('cpu_time_sec')]
            ),
            "buffer_gets": self._calculate_trend_direction(
                [p['buffer_gets_delta'] for p in time_series if p.get('buffer_gets_delta')]
            ),
            "executions": self._calculate_trend_direction(
                [p['executions_delta'] for p in time_series if p.get('executions_delta')]
            ),
        }

        # Overall trend assessment
        overall_trend = self._assess_overall_trend(metrics_trends)

        # Detect anomalies
        anomalies = self._detect_anomalies(time_series)

        return {
            "sql_id": sql_id,
            "time_series": time_series,
            "metrics_trends": metrics_trends,
            "overall_trend": overall_trend,
            "anomalies": anomalies,
            "sample_count": len(time_series),
            "time_range": {
                "begin": time_series[0]['timestamp'] if time_series else None,
                "end": time_series[-1]['timestamp'] if time_series else None,
            }
        }

    def detect_performance_regression(
        self,
        sql_id: str,
        baseline_days: int = 14,
        recent_days: int = 1,
        threshold_percent: float = 30.0
    ) -> Dict[str, Any]:
        """
        Detect performance regression by comparing recent vs baseline period.

        Args:
            sql_id: SQL_ID to check
            baseline_days: Days for baseline period
            recent_days: Days for recent period
            threshold_percent: Regression threshold

        Returns:
            Regression detection results
        """
        # Get baseline performance (older data)
        baseline_stats = self.awr_fetcher.fetch_historical_sql_stats(
            sql_id=sql_id,
            days_back=baseline_days
        )

        # Filter to only baseline period (exclude recent days)
        baseline_stats = [
            s for s in baseline_stats
            if self._days_ago(s.get('end_interval_time')) > recent_days
        ]

        # Get recent performance
        recent_stats = self.awr_fetcher.fetch_historical_sql_stats(
            sql_id=sql_id,
            days_back=recent_days
        )

        if not baseline_stats or not recent_stats:
            return {
                "sql_id": sql_id,
                "regression_detected": False,
                "message": "Insufficient data for regression detection"
            }

        # Calculate metrics for both periods
        baseline_metrics = self._calculate_baseline(baseline_stats)
        recent_metrics = self._calculate_baseline(recent_stats)

        # Compare
        comparison = self._compare_metrics(
            recent_metrics,
            baseline_metrics,
            threshold_percent
        )

        # Check for regression
        regression_detected = any(
            metric.get('change_percent', 0) > threshold_percent
            for metric in comparison.values()
            if isinstance(metric, dict) and 'change_percent' in metric
        )

        severity = "none"
        if regression_detected:
            max_regression = max(
                metric.get('change_percent', 0)
                for metric in comparison.values()
                if isinstance(metric, dict) and 'change_percent' in metric
            )
            if max_regression > 100:
                severity = "critical"
            elif max_regression > 50:
                severity = "high"
            else:
                severity = "medium"

        return {
            "sql_id": sql_id,
            "regression_detected": regression_detected,
            "severity": severity,
            "baseline_period": {
                "days": baseline_days,
                "sample_count": len(baseline_stats),
                "metrics": baseline_metrics,
            },
            "recent_period": {
                "days": recent_days,
                "sample_count": len(recent_stats),
                "metrics": recent_metrics,
            },
            "comparison": comparison,
            "threshold_percent": threshold_percent,
        }

    def _extract_current_metrics(
        self,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract metrics from current V$SQL query."""
        executions = query.get('executions', 1) or 1

        return {
            "executions": query.get('executions', 0),
            "elapsed_time_sec": query.get('elapsed_time', 0) / 1000000 / executions,
            "cpu_time_sec": query.get('cpu_time', 0) / 1000000 / executions,
            "buffer_gets_per_exec": query.get('buffer_gets', 0) / executions,
            "disk_reads_per_exec": query.get('disk_reads', 0) / executions,
            "rows_processed_per_exec": query.get('rows_processed', 0) / executions,
        }

    def _calculate_baseline(
        self,
        historical_stats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate baseline statistics from historical data."""
        # Aggregate metrics
        elapsed_times = []
        cpu_times = []
        buffer_gets = []
        disk_reads = []

        for stat in historical_stats:
            executions = stat.get('executions_delta', 1) or 1

            elapsed_times.append(stat.get('elapsed_time_sec', 0) / executions)
            cpu_times.append(stat.get('cpu_time_sec', 0) / executions)
            buffer_gets.append(stat.get('buffer_gets_delta', 0) / executions)
            disk_reads.append(stat.get('disk_reads_delta', 0) / executions)

        # Calculate statistics
        return {
            "sample_count": len(historical_stats),
            "elapsed_time_sec": {
                "mean": statistics.mean(elapsed_times) if elapsed_times else 0,
                "median": statistics.median(elapsed_times) if elapsed_times else 0,
                "stdev": statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
                "p95": self._percentile(elapsed_times, 0.95),
            },
            "cpu_time_sec": {
                "mean": statistics.mean(cpu_times) if cpu_times else 0,
                "median": statistics.median(cpu_times) if cpu_times else 0,
                "stdev": statistics.stdev(cpu_times) if len(cpu_times) > 1 else 0,
                "p95": self._percentile(cpu_times, 0.95),
            },
            "buffer_gets_per_exec": {
                "mean": statistics.mean(buffer_gets) if buffer_gets else 0,
                "median": statistics.median(buffer_gets) if buffer_gets else 0,
                "stdev": statistics.stdev(buffer_gets) if len(buffer_gets) > 1 else 0,
                "p95": self._percentile(buffer_gets, 0.95),
            },
            "disk_reads_per_exec": {
                "mean": statistics.mean(disk_reads) if disk_reads else 0,
                "median": statistics.median(disk_reads) if disk_reads else 0,
                "stdev": statistics.stdev(disk_reads) if len(disk_reads) > 1 else 0,
                "p95": self._percentile(disk_reads, 0.95),
            },
        }

    def _compare_metrics(
        self,
        current: Dict[str, Any],
        baseline: Dict[str, Any],
        threshold: float
    ) -> Dict[str, Any]:
        """Compare current metrics against baseline."""
        comparison = {}

        for metric in ['elapsed_time_sec', 'cpu_time_sec', 'buffer_gets_per_exec', 'disk_reads_per_exec']:
            current_value = current.get(metric, 0)
            baseline_stats = baseline.get(metric, {})
            baseline_mean = baseline_stats.get('mean', 0)

            if baseline_mean > 0:
                change = current_value - baseline_mean
                change_percent = (change / baseline_mean) * 100

                comparison[metric] = {
                    "current": round(current_value, 2),
                    "baseline_mean": round(baseline_mean, 2),
                    "baseline_median": round(baseline_stats.get('median', 0), 2),
                    "baseline_p95": round(baseline_stats.get('p95', 0), 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "regression": change_percent > threshold,
                    "improvement": change_percent < -threshold,
                }
            else:
                comparison[metric] = {
                    "current": round(current_value, 2),
                    "baseline_mean": 0,
                    "change": 0,
                    "change_percent": 0,
                    "regression": False,
                    "improvement": False,
                }

        return comparison

    def _determine_trend(
        self,
        comparison: Dict[str, Any],
        threshold: float
    ) -> str:
        """Determine overall performance trend."""
        regressions = sum(
            1 for metric in comparison.values()
            if isinstance(metric, dict) and metric.get('regression', False)
        )

        improvements = sum(
            1 for metric in comparison.values()
            if isinstance(metric, dict) and metric.get('improvement', False)
        )

        if regressions > improvements:
            return PerformanceTrend.DEGRADING
        elif improvements > regressions and improvements > 0:
            return PerformanceTrend.IMPROVING
        else:
            return PerformanceTrend.STABLE

    def _generate_comparison_recommendations(
        self,
        comparison: Dict[str, Any],
        trend: str
    ) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []

        if trend == PerformanceTrend.DEGRADING:
            # Check which metrics regressed
            elapsed_regressed = comparison.get('elapsed_time_sec', {}).get('regression', False)
            buffer_gets_regressed = comparison.get('buffer_gets_per_exec', {}).get('regression', False)
            disk_reads_regressed = comparison.get('disk_reads_per_exec', {}).get('regression', False)

            if elapsed_regressed:
                recommendations.append(
                    "Query elapsed time has regressed significantly. "
                    "Review recent execution plan changes."
                )

            if buffer_gets_regressed:
                recommendations.append(
                    "Buffer gets have increased. "
                    "Check for missing indexes or inefficient joins."
                )

            if disk_reads_regressed:
                recommendations.append(
                    "Disk reads have increased. "
                    "Consider gathering statistics or checking buffer cache sizing."
                )

        elif trend == PerformanceTrend.IMPROVING:
            recommendations.append(
                "Performance has improved compared to historical baseline. "
                "No action needed."
            )

        else:
            recommendations.append(
                "Performance is stable. Continue monitoring."
            )

        return recommendations

    def _build_time_series(
        self,
        historical_stats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build time-series data from historical stats."""
        time_series = []

        for stat in historical_stats:
            executions = stat.get('executions_delta', 1) or 1

            time_series.append({
                "timestamp": stat.get('end_interval_time'),
                "snap_id": stat.get('snap_id'),
                "elapsed_time_sec": stat.get('elapsed_time_sec', 0) / executions,
                "cpu_time_sec": stat.get('cpu_time_sec', 0) / executions,
                "buffer_gets_delta": stat.get('buffer_gets_delta', 0) / executions,
                "disk_reads_delta": stat.get('disk_reads_delta', 0) / executions,
                "executions_delta": stat.get('executions_delta', 0),
            })

        return time_series

    def _calculate_trend_direction(
        self,
        values: List[float]
    ) -> Dict[str, Any]:
        """Calculate trend direction for a metric."""
        if len(values) < 3:
            return {"direction": "unknown", "confidence": 0}

        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        y = values

        # Calculate slope
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # Determine direction
        if slope > 0.1:
            direction = "increasing"
        elif slope < -0.1:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "slope": round(slope, 4),
            "values": values,
        }

    def _assess_overall_trend(
        self,
        metrics_trends: Dict[str, Any]
    ) -> str:
        """Assess overall performance trend."""
        elapsed_direction = metrics_trends.get('elapsed_time', {}).get('direction')

        if elapsed_direction == "increasing":
            return PerformanceTrend.DEGRADING
        elif elapsed_direction == "decreasing":
            return PerformanceTrend.IMPROVING
        else:
            return PerformanceTrend.STABLE

    def _detect_anomalies(
        self,
        time_series: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in time-series data."""
        anomalies = []

        if len(time_series) < 5:
            return anomalies

        # Check elapsed time for anomalies
        elapsed_times = [p.get('elapsed_time_sec', 0) for p in time_series]
        mean_elapsed = statistics.mean(elapsed_times)
        stdev_elapsed = statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0

        # Flag points > 2 standard deviations from mean
        if stdev_elapsed > 0:
            for i, point in enumerate(time_series):
                elapsed = point.get('elapsed_time_sec', 0)
                z_score = abs(elapsed - mean_elapsed) / stdev_elapsed

                if z_score > 2:
                    anomalies.append({
                        "timestamp": point.get('timestamp'),
                        "snap_id": point.get('snap_id'),
                        "metric": "elapsed_time_sec",
                        "value": elapsed,
                        "mean": mean_elapsed,
                        "z_score": round(z_score, 2),
                        "severity": "high" if z_score > 3 else "medium",
                    })

        return anomalies

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _days_ago(self, timestamp_str: Optional[str]) -> int:
        """Calculate days ago from timestamp string."""
        if not timestamp_str:
            return 999

        try:
            dt = datetime.fromisoformat(timestamp_str)
            delta = datetime.utcnow() - dt
            return delta.days
        except Exception:
            return 999
