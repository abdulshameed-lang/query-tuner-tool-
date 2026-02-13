"""Integration tests for AWR/ASH API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime
from app.main import app

client = TestClient(app)


class TestAWRASHAPI:
    """Test cases for AWR/ASH API endpoints."""

    @pytest.fixture
    def sample_snapshots(self):
        """Create sample snapshots for testing."""
        now = datetime.now()
        return {
            "snapshots": [
                {
                    "snap_id": 100,
                    "dbid": 12345,
                    "instance_number": 1,
                    "begin_interval_time": now.isoformat(),
                    "end_interval_time": now.isoformat(),
                    "startup_time": now.isoformat(),
                    "snap_level": 1,
                }
            ],
            "total_count": 1,
            "awr_available": True,
        }

    def test_get_snapshots_success(self, sample_snapshots):
        """Test getting AWR snapshots successfully."""
        with patch("app.services.awr_ash_service.AWRASHService.get_snapshots") as mock_get:
            mock_get.return_value = sample_snapshots

            response = client.get("/api/v1/awr-ash/snapshots?days_back=7")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
            assert len(data["snapshots"]) == 1

    def test_get_snapshots_with_limit(self, sample_snapshots):
        """Test getting snapshots with limit parameter."""
        with patch("app.services.awr_ash_service.AWRASHService.get_snapshots") as mock_get:
            mock_get.return_value = sample_snapshots

            response = client.get("/api/v1/awr-ash/snapshots?days_back=7&limit=50")

            assert response.status_code == 200

    def test_generate_awr_report_success(self):
        """Test generating AWR report successfully."""
        now = datetime.now()
        mock_report = {
            "report_info": {
                "begin_snap_id": 100,
                "end_snap_id": 105,
                "begin_time": now.isoformat(),
                "end_time": now.isoformat(),
                "elapsed_time_minutes": 60.0,
                "generated_at": now.isoformat(),
            },
            "database_info": {},
            "load_profile": {},
            "top_sql_by_elapsed_time": [],
            "top_sql_by_cpu": [],
            "top_sql_by_gets": [],
            "top_sql_by_reads": [],
            "top_sql_by_executions": [],
            "wait_events": [],
            "wait_events_summary": {
                "by_wait_class": {},
                "total_wait_time_sec": 0,
                "top_wait_class": None,
            },
            "time_model_statistics": {},
            "instance_efficiency": {},
            "recommendations": [],
        }

        with patch("app.services.awr_ash_service.AWRASHService.generate_awr_report") as mock_gen:
            mock_gen.return_value = mock_report

            response = client.get("/api/v1/awr-ash/report?begin_snap_id=100&end_snap_id=105")

            assert response.status_code == 200
            data = response.json()
            assert data["report_info"]["begin_snap_id"] == 100

    def test_generate_awr_report_invalid_snapshots(self):
        """Test generating report with invalid snapshot IDs."""
        response = client.get("/api/v1/awr-ash/report?begin_snap_id=105&end_snap_id=100")

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_SNAPSHOTS"

    def test_get_ash_activity_success(self):
        """Test getting ASH activity successfully."""
        now = datetime.now()
        mock_result = {
            "samples": [
                {
                    "sample_time": now.isoformat(),
                    "session_id": 100,
                    "sql_id": "abc123def4567",
                    "event": "db file sequential read",
                    "wait_class": "User I/O",
                }
            ],
            "sample_count": 1,
            "ash_available": True,
            "time_range": {
                "begin": now.isoformat(),
                "end": now.isoformat(),
            },
        }

        with patch("app.services.awr_ash_service.AWRASHService.get_ash_activity") as mock_get:
            mock_get.return_value = mock_result

            response = client.get("/api/v1/awr-ash/ash/activity?minutes_back=60")

            assert response.status_code == 200
            data = response.json()
            assert data["sample_count"] == 1

    def test_analyze_sql_ash_activity_success(self):
        """Test analyzing SQL ASH activity."""
        now = datetime.now()
        mock_analysis = {
            "sql_id": "abc123def4567",
            "time_range": {
                "begin": now.isoformat(),
                "end": now.isoformat(),
            },
            "sample_count": 10,
            "activity_timeline": [],
            "wait_event_analysis": {
                "events": [],
                "unique_event_count": 0,
                "total_wait_time": 0,
            },
            "session_analysis": {},
            "blocking_analysis": {},
            "execution_activity": {},
        }

        with patch("app.services.awr_ash_service.AWRASHService.analyze_sql_ash_activity") as mock_analyze:
            mock_analyze.return_value = mock_analysis

            response = client.get("/api/v1/awr-ash/ash/sql/abc123def4567?minutes_back=60")

            assert response.status_code == 200
            data = response.json()
            assert data["sql_id"] == "abc123def4567"

    def test_analyze_sql_ash_activity_invalid_sql_id(self):
        """Test analyzing ASH with invalid SQL_ID."""
        response = client.get("/api/v1/awr-ash/ash/sql/invalid")

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_SQL_ID"

    def test_get_historical_sql_performance(self):
        """Test getting historical SQL performance."""
        mock_result = {
            "sql_id": "abc123def4567",
            "statistics": [],
            "sample_count": 0,
            "time_range": {},
            "awr_available": True,
        }

        with patch("app.services.awr_ash_service.AWRASHService.get_historical_sql_performance") as mock_get:
            mock_get.return_value = mock_result

            response = client.get("/api/v1/awr-ash/historical/sql/abc123def4567?days_back=7")

            assert response.status_code == 200
            data = response.json()
            assert data["sql_id"] == "abc123def4567"

    def test_compare_current_vs_historical(self):
        """Test comparing current vs historical performance."""
        now = datetime.now()
        mock_comparison = {
            "sql_id": "abc123def4567",
            "current": {
                "executions": 100,
                "elapsed_time_sec": 1.5,
                "cpu_time_sec": 0.5,
                "buffer_gets_per_exec": 1000,
                "disk_reads_per_exec": 10,
                "rows_processed_per_exec": 100,
            },
            "historical": None,
            "comparison": None,
            "trend": "insufficient_data",
            "threshold_percent": 20.0,
            "recommendations": [],
            "analysis_timestamp": now.isoformat(),
        }

        with patch("app.services.awr_ash_service.AWRASHService.compare_current_vs_historical") as mock_compare:
            mock_compare.return_value = mock_comparison

            response = client.get("/api/v1/awr-ash/historical/compare/abc123def4567")

            assert response.status_code == 200
            data = response.json()
            assert data["sql_id"] == "abc123def4567"

    def test_analyze_performance_trend(self):
        """Test analyzing performance trend."""
        mock_trend = {
            "sql_id": "abc123def4567",
            "time_series": [],
            "metrics_trends": {},
            "overall_trend": "stable",
            "anomalies": [],
            "sample_count": 10,
            "time_range": {},
        }

        with patch("app.services.awr_ash_service.AWRASHService.analyze_performance_trend") as mock_analyze:
            mock_analyze.return_value = mock_trend

            response = client.get("/api/v1/awr-ash/historical/trends/abc123def4567?days_back=30")

            assert response.status_code == 200
            data = response.json()
            assert data["sql_id"] == "abc123def4567"

    def test_detect_performance_regression(self):
        """Test detecting performance regression."""
        mock_regression = {
            "sql_id": "abc123def4567",
            "regression_detected": False,
            "severity": "none",
            "baseline_period": {
                "days": 14,
                "sample_count": 10,
                "metrics": {
                    "sample_count": 10,
                    "elapsed_time_sec": {"mean": 1.0, "median": 1.0, "stdev": 0.1, "p95": 1.2},
                    "cpu_time_sec": {"mean": 0.5, "median": 0.5, "stdev": 0.05, "p95": 0.6},
                    "buffer_gets_per_exec": {"mean": 1000, "median": 1000, "stdev": 100, "p95": 1200},
                    "disk_reads_per_exec": {"mean": 10, "median": 10, "stdev": 2, "p95": 14},
                },
            },
            "recent_period": {
                "days": 1,
                "sample_count": 5,
                "metrics": {
                    "sample_count": 5,
                    "elapsed_time_sec": {"mean": 1.0, "median": 1.0, "stdev": 0.1, "p95": 1.2},
                    "cpu_time_sec": {"mean": 0.5, "median": 0.5, "stdev": 0.05, "p95": 0.6},
                    "buffer_gets_per_exec": {"mean": 1000, "median": 1000, "stdev": 100, "p95": 1200},
                    "disk_reads_per_exec": {"mean": 10, "median": 10, "stdev": 2, "p95": 14},
                },
            },
            "comparison": {},
            "threshold_percent": 30.0,
        }

        with patch("app.services.awr_ash_service.AWRASHService.detect_regression") as mock_detect:
            mock_detect.return_value = mock_regression

            response = client.get("/api/v1/awr-ash/historical/regression/abc123def4567")

            assert response.status_code == 200
            data = response.json()
            assert data["sql_id"] == "abc123def4567"
            assert data["regression_detected"] is False

    def test_detect_regression_invalid_periods(self):
        """Test regression detection with invalid period parameters."""
        response = client.get("/api/v1/awr-ash/historical/regression/abc123def4567?baseline_days=7&recent_days=10")

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_PERIODS"
