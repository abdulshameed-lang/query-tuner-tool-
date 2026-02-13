"""Unit tests for AWR/ASH fetcher."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.core.oracle.awr_ash import AWRASHFetcher


class TestAWRASHFetcher:
    """Test cases for AWRASHFetcher class."""

    @pytest.fixture
    def connection_manager(self):
        """Create mock connection manager."""
        mock_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_conn.cursor.return_value = mock_cursor
        mock_manager.get_connection.return_value = mock_conn

        return mock_manager

    @pytest.fixture
    def awr_fetcher(self, connection_manager):
        """Create AWRASHFetcher instance."""
        return AWRASHFetcher(connection_manager)

    def test_check_awr_availability_true(self, awr_fetcher, connection_manager):
        """Test AWR availability check when AWR is available."""
        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.fetchone.return_value = (10,)  # Some snapshots exist

        result = awr_fetcher.check_awr_availability()

        assert result is True
        assert awr_fetcher._awr_available is True

    def test_check_awr_availability_false(self, awr_fetcher, connection_manager):
        """Test AWR availability check when AWR is not available."""
        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.execute.side_effect = Exception("Table not found")

        result = awr_fetcher.check_awr_availability()

        assert result is False
        assert awr_fetcher._awr_available is False

    def test_check_awr_availability_cached(self, awr_fetcher):
        """Test that AWR availability is cached."""
        awr_fetcher._awr_available = True

        result = awr_fetcher.check_awr_availability()

        assert result is True
        # Should not execute query again

    def test_fetch_snapshots_success(self, awr_fetcher, connection_manager):
        """Test fetching AWR snapshots successfully."""
        awr_fetcher._awr_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [
            ('SNAP_ID',), ('DBID',), ('INSTANCE_NUMBER',),
            ('BEGIN_INTERVAL_TIME',), ('END_INTERVAL_TIME',),
            ('STARTUP_TIME',), ('SNAP_LEVEL',)
        ]

        now = datetime.now()
        mock_cursor.__iter__ = Mock(return_value=iter([
            (100, 12345, 1, now - timedelta(hours=2), now - timedelta(hours=1), now - timedelta(days=1), 1),
            (101, 12345, 1, now - timedelta(hours=1), now, now - timedelta(days=1), 1),
        ]))

        snapshots = awr_fetcher.fetch_snapshots(days_back=1)

        assert len(snapshots) == 2
        assert snapshots[0]['snap_id'] == 100
        assert snapshots[1]['snap_id'] == 101

    def test_fetch_snapshots_with_limit(self, awr_fetcher, connection_manager):
        """Test fetching snapshots with limit."""
        awr_fetcher._awr_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [('SNAP_ID',), ('DBID',), ('INSTANCE_NUMBER',), ('BEGIN_INTERVAL_TIME',), ('END_INTERVAL_TIME',), ('STARTUP_TIME',), ('SNAP_LEVEL',)]
        mock_cursor.__iter__ = Mock(return_value=iter([]))

        awr_fetcher.fetch_snapshots(days_back=7, limit=10)

        # Verify limit was applied in query
        assert mock_cursor.execute.called

    def test_fetch_snapshots_awr_not_available(self, awr_fetcher):
        """Test fetching snapshots when AWR not available."""
        awr_fetcher._awr_available = False

        snapshots = awr_fetcher.fetch_snapshots(days_back=7)

        assert snapshots == []

    def test_fetch_historical_sql_stats_success(self, awr_fetcher, connection_manager):
        """Test fetching historical SQL statistics."""
        awr_fetcher._awr_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [
            ('SNAP_ID',), ('INSTANCE_NUMBER',), ('BEGIN_INTERVAL_TIME',),
            ('END_INTERVAL_TIME',), ('PLAN_HASH_VALUE',), ('EXECUTIONS_DELTA',),
            ('ELAPSED_TIME_SEC',), ('CPU_TIME_SEC',), ('BUFFER_GETS_DELTA',),
            ('DISK_READS_DELTA',), ('ROWS_PROCESSED_DELTA',),
            ('PARSE_CALLS_DELTA',), ('VERSION_COUNT',)
        ]

        now = datetime.now()
        mock_cursor.__iter__ = Mock(return_value=iter([
            (100, 1, now - timedelta(hours=1), now, 123456, 10, 1.5, 0.5, 1000, 10, 100, 5, 1),
        ]))

        stats = awr_fetcher.fetch_historical_sql_stats(
            sql_id="abc123def4567",
            days_back=7
        )

        assert len(stats) == 1
        assert stats[0]['snap_id'] == 100
        assert stats[0]['plan_hash_value'] == 123456

    def test_fetch_historical_sql_stats_with_snap_ids(self, awr_fetcher, connection_manager):
        """Test fetching stats with specific snapshot IDs."""
        awr_fetcher._awr_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [('SNAP_ID',), ('INSTANCE_NUMBER',), ('BEGIN_INTERVAL_TIME',), ('END_INTERVAL_TIME',), ('PLAN_HASH_VALUE',), ('EXECUTIONS_DELTA',), ('ELAPSED_TIME_SEC',), ('CPU_TIME_SEC',), ('BUFFER_GETS_DELTA',), ('DISK_READS_DELTA',), ('ROWS_PROCESSED_DELTA',), ('PARSE_CALLS_DELTA',), ('VERSION_COUNT',)]
        mock_cursor.__iter__ = Mock(return_value=iter([]))

        awr_fetcher.fetch_historical_sql_stats(
            sql_id="abc123def4567",
            begin_snap_id=100,
            end_snap_id=105
        )

        # Verify snap IDs were used in query
        assert mock_cursor.execute.called

    def test_fetch_ash_activity_success(self, awr_fetcher, connection_manager):
        """Test fetching ASH activity samples."""
        awr_fetcher._ash_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [
            ('SAMPLE_ID',), ('SAMPLE_TIME',), ('SESSION_ID',),
            ('SESSION_SERIAL#',), ('SQL_ID',), ('SQL_PLAN_HASH_VALUE',),
            ('EVENT',), ('WAIT_CLASS',), ('WAIT_TIME',), ('TIME_WAITED',),
            ('SESSION_STATE',), ('SESSION_TYPE',), ('BLOCKING_SESSION',),
            ('CURRENT_OBJ#',), ('PROGRAM',), ('MODULE',)
        ]

        now = datetime.now()
        mock_cursor.__iter__ = Mock(return_value=iter([
            (1, now, 100, 1, "abc123def4567", 123456, "db file sequential read", "User I/O", 10, 100, "WAITING", "USER", None, 12345, "sqlplus", "SQL*Plus"),
        ]))

        samples = awr_fetcher.fetch_ash_activity(
            sql_id="abc123def4567",
            limit=1000
        )

        assert len(samples) == 1
        assert samples[0]['sql_id'] == "abc123def4567"
        assert samples[0]['wait_class'] == "User I/O"

    def test_fetch_ash_activity_with_filters(self, awr_fetcher, connection_manager):
        """Test fetching ASH activity with filters."""
        awr_fetcher._ash_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [('SAMPLE_ID',), ('SAMPLE_TIME',), ('SESSION_ID',), ('SESSION_SERIAL#',), ('SQL_ID',), ('SQL_PLAN_HASH_VALUE',), ('EVENT',), ('WAIT_CLASS',), ('WAIT_TIME',), ('TIME_WAITED',), ('SESSION_STATE',), ('SESSION_TYPE',), ('BLOCKING_SESSION',), ('CURRENT_OBJ#',), ('PROGRAM',), ('MODULE',)]
        mock_cursor.__iter__ = Mock(return_value=iter([]))

        begin_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        awr_fetcher.fetch_ash_activity(
            sql_id="abc123def4567",
            begin_time=begin_time,
            end_time=end_time,
            limit=500
        )

        # Verify filters were applied
        assert mock_cursor.execute.called

    def test_calculate_sql_statistics_summary(self, awr_fetcher, connection_manager):
        """Test calculating SQL statistics summary."""
        awr_fetcher._awr_available = True

        # Mock fetch_historical_sql_stats
        now = datetime.now()
        mock_stats = [
            {
                'snap_id': 100,
                'begin_interval_time': (now - timedelta(hours=2)).isoformat(),
                'end_interval_time': (now - timedelta(hours=1)).isoformat(),
                'executions_delta': 10,
                'elapsed_time_sec': 1.5,
                'cpu_time_sec': 0.5,
                'buffer_gets_delta': 1000,
            },
            {
                'snap_id': 101,
                'begin_interval_time': (now - timedelta(hours=1)).isoformat(),
                'end_interval_time': now.isoformat(),
                'executions_delta': 15,
                'elapsed_time_sec': 1.2,
                'cpu_time_sec': 0.4,
                'buffer_gets_delta': 800,
            },
        ]

        with patch.object(awr_fetcher, 'fetch_historical_sql_stats', return_value=mock_stats):
            summary = awr_fetcher.calculate_sql_statistics_summary(
                sql_id="abc123def4567",
                days_back=7
            )

        assert summary['sql_id'] == "abc123def4567"
        assert summary['sample_count'] == 2
        assert 'elapsed_time' in summary
        assert 'mean' in summary['elapsed_time']
        assert 'p95' in summary['elapsed_time']

    def test_fetch_system_wait_events(self, awr_fetcher, connection_manager):
        """Test fetching system wait events."""
        awr_fetcher._awr_available = True

        mock_cursor = connection_manager.get_connection().cursor()
        mock_cursor.description = [
            ('EVENT_NAME',), ('WAIT_CLASS',), ('TOTAL_WAITS_DELTA',),
            ('TOTAL_TIMEOUTS_DELTA',), ('TIME_WAITED_SEC',), ('AVG_WAIT_MS',)
        ]

        mock_cursor.__iter__ = Mock(return_value=iter([
            ("db file sequential read", "User I/O", 1000, 10, 50.5, 50.5),
            ("log file sync", "Commit", 500, 5, 10.2, 20.4),
        ]))

        events = awr_fetcher.fetch_system_wait_events(
            begin_snap_id=100,
            end_snap_id=105
        )

        assert len(events) == 2
        assert events[0]['event_name'] == "db file sequential read"
        assert events[1]['wait_class'] == "Commit"
