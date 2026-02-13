"""AWR and ASH service layer."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.oracle.connection import get_connection_manager
from app.core.oracle.awr_ash import AWRASHFetcher
from app.core.analysis.awr_report_generator import AWRReportGenerator
from app.core.analysis.ash_analyzer import ASHAnalyzer
from app.core.analysis.historical_comparator import HistoricalComparator

logger = logging.getLogger(__name__)


class AWRASHService:
    """Service for AWR and ASH operations."""

    def __init__(self):
        """Initialize AWR/ASH Service."""
        self.connection_manager = get_connection_manager()
        self.awr_fetcher = AWRASHFetcher(self.connection_manager)
        self.awr_report_generator = AWRReportGenerator(self.connection_manager)
        self.ash_analyzer = ASHAnalyzer(self.connection_manager)
        self.historical_comparator = HistoricalComparator(self.connection_manager)

    def get_snapshots(
        self,
        days_back: int = 7,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get available AWR snapshots.

        Args:
            days_back: Number of days to look back
            limit: Maximum number of snapshots

        Returns:
            Dictionary with snapshots and metadata
        """
        try:
            if not self.awr_fetcher.check_awr_availability():
                return {
                    "snapshots": [],
                    "total_count": 0,
                    "awr_available": False,
                    "message": "AWR not available - requires Oracle Diagnostics Pack"
                }

            snapshots = self.awr_fetcher.fetch_snapshots(
                days_back=days_back,
                limit=limit
            )

            return {
                "snapshots": snapshots,
                "total_count": len(snapshots),
                "awr_available": True,
            }

        except Exception as e:
            logger.error(f"Error fetching snapshots: {e}", exc_info=True)
            raise

    def generate_awr_report(
        self,
        begin_snap_id: int,
        end_snap_id: int,
        top_n: int = 10,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate AWR report between two snapshots.

        Args:
            begin_snap_id: Beginning snapshot ID
            end_snap_id: Ending snapshot ID
            top_n: Number of top items to include
            format: Output format (json or html)

        Returns:
            AWR report
        """
        try:
            if not self.awr_fetcher.check_awr_availability():
                return {
                    "error": "AWR not available",
                    "message": "AWR requires Oracle Diagnostics Pack license"
                }

            # Generate report
            report = self.awr_report_generator.generate_report(
                begin_snap_id=begin_snap_id,
                end_snap_id=end_snap_id,
                top_n=top_n
            )

            # Export to HTML if requested
            if format.lower() == "html":
                html_report = self.awr_report_generator.export_report_html(report)
                report["html_export"] = html_report

            return report

        except Exception as e:
            logger.error(f"Error generating AWR report: {e}", exc_info=True)
            raise

    def get_ash_activity(
        self,
        sql_id: Optional[str] = None,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        minutes_back: Optional[int] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Get ASH activity samples.

        Args:
            sql_id: Optional SQL_ID filter
            begin_time: Start time
            end_time: End time
            minutes_back: Minutes to look back (if times not specified)
            limit: Maximum samples to return

        Returns:
            ASH activity data
        """
        try:
            if not self.awr_fetcher.check_ash_availability():
                return {
                    "samples": [],
                    "sample_count": 0,
                    "ash_available": False,
                    "message": "ASH not available - requires Oracle Diagnostics Pack"
                }

            # Set default time range if not specified
            if not end_time:
                end_time = datetime.utcnow()
            if not begin_time:
                if minutes_back:
                    begin_time = end_time - timedelta(minutes=minutes_back)
                else:
                    begin_time = end_time - timedelta(hours=1)

            # Fetch samples
            samples = self.awr_fetcher.fetch_ash_activity(
                sql_id=sql_id,
                begin_time=begin_time,
                end_time=end_time,
                limit=limit
            )

            return {
                "samples": samples,
                "sample_count": len(samples),
                "ash_available": True,
                "time_range": {
                    "begin": begin_time.isoformat(),
                    "end": end_time.isoformat(),
                }
            }

        except Exception as e:
            logger.error(f"Error fetching ASH activity: {e}", exc_info=True)
            raise

    def analyze_sql_ash_activity(
        self,
        sql_id: str,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        minutes_back: int = 60
    ) -> Dict[str, Any]:
        """
        Analyze ASH activity for a specific SQL_ID.

        Args:
            sql_id: SQL_ID to analyze
            begin_time: Start time
            end_time: End time
            minutes_back: Minutes to look back if times not specified

        Returns:
            ASH analysis results
        """
        try:
            if not self.awr_fetcher.check_ash_availability():
                return {
                    "error": "ASH not available",
                    "message": "ASH requires Oracle Diagnostics Pack license"
                }

            # Set default time range
            if not end_time:
                end_time = datetime.utcnow()
            if not begin_time:
                begin_time = end_time - timedelta(minutes=minutes_back)

            # Analyze activity
            analysis = self.ash_analyzer.analyze_sql_activity(
                sql_id=sql_id,
                begin_time=begin_time,
                end_time=end_time
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing SQL ASH activity: {e}", exc_info=True)
            raise

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
            top_n: Number of top items

        Returns:
            Time period analysis
        """
        try:
            if not self.awr_fetcher.check_ash_availability():
                return {
                    "error": "ASH not available",
                    "message": "ASH requires Oracle Diagnostics Pack license"
                }

            analysis = self.ash_analyzer.analyze_time_period(
                begin_time=begin_time,
                end_time=end_time,
                top_n=top_n
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing time period: {e}", exc_info=True)
            raise

    def identify_bottlenecks(
        self,
        begin_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Identify performance bottlenecks.

        Args:
            begin_time: Start time
            end_time: End time

        Returns:
            Bottleneck analysis
        """
        try:
            if not self.awr_fetcher.check_ash_availability():
                return {
                    "error": "ASH not available",
                    "message": "ASH requires Oracle Diagnostics Pack license"
                }

            bottlenecks = self.ash_analyzer.identify_bottlenecks(
                begin_time=begin_time,
                end_time=end_time
            )

            return bottlenecks

        except Exception as e:
            logger.error(f"Error identifying bottlenecks: {e}", exc_info=True)
            raise

    def get_historical_sql_performance(
        self,
        sql_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get historical performance for a SQL_ID.

        Args:
            sql_id: SQL_ID
            days_back: Days of history

        Returns:
            Historical performance data
        """
        try:
            if not self.awr_fetcher.check_awr_availability():
                return {
                    "sql_id": sql_id,
                    "statistics": [],
                    "sample_count": 0,
                    "awr_available": False,
                    "message": "AWR not available - requires Oracle Diagnostics Pack"
                }

            # Fetch historical stats
            statistics = self.awr_fetcher.fetch_historical_sql_stats(
                sql_id=sql_id,
                days_back=days_back
            )

            # Calculate summary
            summary = self.awr_fetcher.calculate_sql_statistics_summary(
                sql_id=sql_id,
                days_back=days_back
            )

            return {
                "sql_id": sql_id,
                "statistics": statistics,
                "sample_count": len(statistics),
                "summary": summary,
                "time_range": {
                    "begin": statistics[0]['begin_interval_time'] if statistics else None,
                    "end": statistics[-1]['end_interval_time'] if statistics else None,
                },
                "awr_available": True,
            }

        except Exception as e:
            logger.error(f"Error fetching historical SQL performance: {e}", exc_info=True)
            raise

    def compare_current_vs_historical(
        self,
        sql_id: str,
        days_back: int = 7,
        threshold_percent: float = 20.0
    ) -> Dict[str, Any]:
        """
        Compare current performance vs historical baseline.

        Args:
            sql_id: SQL_ID
            days_back: Days of history to compare against
            threshold_percent: Threshold for regression detection

        Returns:
            Comparison results
        """
        try:
            if not self.awr_fetcher.check_awr_availability():
                return {
                    "sql_id": sql_id,
                    "error": "AWR not available",
                    "message": "AWR requires Oracle Diagnostics Pack license"
                }

            comparison = self.historical_comparator.compare_current_vs_historical(
                sql_id=sql_id,
                days_back=days_back,
                threshold_percent=threshold_percent
            )

            return comparison

        except Exception as e:
            logger.error(f"Error comparing current vs historical: {e}", exc_info=True)
            raise

    def analyze_performance_trend(
        self,
        sql_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze performance trend over time.

        Args:
            sql_id: SQL_ID
            days_back: Days to analyze

        Returns:
            Trend analysis
        """
        try:
            if not self.awr_fetcher.check_awr_availability():
                return {
                    "sql_id": sql_id,
                    "error": "AWR not available",
                    "message": "AWR requires Oracle Diagnostics Pack license"
                }

            trend = self.historical_comparator.analyze_performance_trend(
                sql_id=sql_id,
                days_back=days_back
            )

            return trend

        except Exception as e:
            logger.error(f"Error analyzing performance trend: {e}", exc_info=True)
            raise

    def detect_regression(
        self,
        sql_id: str,
        baseline_days: int = 14,
        recent_days: int = 1,
        threshold_percent: float = 30.0
    ) -> Dict[str, Any]:
        """
        Detect performance regression.

        Args:
            sql_id: SQL_ID
            baseline_days: Days for baseline
            recent_days: Days for recent period
            threshold_percent: Regression threshold

        Returns:
            Regression detection results
        """
        try:
            if not self.awr_fetcher.check_awr_availability():
                return {
                    "sql_id": sql_id,
                    "regression_detected": False,
                    "error": "AWR not available",
                    "message": "AWR requires Oracle Diagnostics Pack license"
                }

            regression = self.historical_comparator.detect_performance_regression(
                sql_id=sql_id,
                baseline_days=baseline_days,
                recent_days=recent_days,
                threshold_percent=threshold_percent
            )

            return regression

        except Exception as e:
            logger.error(f"Error detecting regression: {e}", exc_info=True)
            raise

    def get_top_sql_from_ash(
        self,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        minutes_back: int = 60,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Get top SQL from ASH data.

        Args:
            begin_time: Start time
            end_time: End time
            minutes_back: Minutes to look back
            top_n: Number of top SQL

        Returns:
            Top SQL list
        """
        try:
            if not self.awr_fetcher.check_ash_availability():
                return {
                    "top_sql": [],
                    "ash_available": False,
                    "message": "ASH not available - requires Oracle Diagnostics Pack"
                }

            # Set default time range
            if not end_time:
                end_time = datetime.utcnow()
            if not begin_time:
                begin_time = end_time - timedelta(minutes=minutes_back)

            top_sql = self.awr_fetcher.fetch_ash_top_sql(
                begin_time=begin_time,
                end_time=end_time,
                top_n=top_n
            )

            return {
                "top_sql": top_sql,
                "ash_available": True,
                "time_range": {
                    "begin": begin_time.isoformat(),
                    "end": end_time.isoformat(),
                }
            }

        except Exception as e:
            logger.error(f"Error fetching top SQL from ASH: {e}", exc_info=True)
            raise
