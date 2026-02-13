"""Unit tests for Oracle connection management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import cx_Oracle

from app.core.oracle.connection import (
    ConnectionManager,
    OracleConnectionError,
)


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_init(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/XEPDB1",
            min_pool_size=3,
            max_pool_size=10,
        )

        assert manager.user == "test_user"
        assert manager.password == "test_pass"
        assert manager.dsn == "localhost:1521/XEPDB1"
        assert manager.min_pool_size == 3
        assert manager.max_pool_size == 10
        assert manager._pool is None

    @patch('cx_Oracle.SessionPool')
    def test_create_pool_success(self, mock_pool_class):
        """Test successful connection pool creation."""
        # Setup mock
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        manager = ConnectionManager(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/XEPDB1",
        )

        # Create pool
        pool = manager.create_pool()

        # Verify
        assert pool == mock_pool
        assert manager._pool == mock_pool
        mock_pool_class.assert_called_once()

    @patch('cx_Oracle.SessionPool')
    def test_create_pool_database_error(self, mock_pool_class):
        """Test pool creation with database error."""
        # Setup mock to raise error
        error = cx_Oracle.DatabaseError("Connection failed")
        error.args = (Mock(message="Connection failed"),)
        mock_pool_class.side_effect = error

        manager = ConnectionManager(
            user="bad_user",
            password="bad_pass",
            dsn="invalid:1521/XEPDB1",
        )

        # Verify exception is raised
        with pytest.raises(OracleConnectionError) as exc_info:
            manager.create_pool()

        assert "Failed to create connection pool" in str(exc_info.value)

    @patch('cx_Oracle.SessionPool')
    def test_get_connection_context_manager(self, mock_pool_class):
        """Test get_connection context manager."""
        # Setup mocks
        mock_pool = Mock()
        mock_connection = Mock()
        mock_pool.acquire.return_value = mock_connection
        mock_pool_class.return_value = mock_pool

        manager = ConnectionManager(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/XEPDB1",
        )

        # Use context manager
        with manager.get_connection() as conn:
            assert conn == mock_connection

        # Verify connection was released
        mock_pool.release.assert_called_once_with(mock_connection)

    @patch('cx_Oracle.SessionPool')
    def test_test_connection_success(self, mock_pool_class):
        """Test successful connection test."""
        # Setup mocks
        mock_pool = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()

        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_pool_class.return_value = mock_pool

        # Mock query results
        mock_cursor.fetchone.side_effect = [
            ("Oracle Database 19c Enterprise Edition",),  # version
            ("TESTDB",),  # database name
            ("TEST_USER",),  # current user
        ]

        manager = ConnectionManager(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/XEPDB1",
        )

        # Test connection
        result = manager.test_connection()

        # Verify
        assert result["status"] == "connected"
        assert "Oracle Database 19c" in result["version"]
        assert result["database"] == "TESTDB"
        assert result["user"] == "TEST_USER"
        assert result["dsn"] == "localhost:1521/XEPDB1"

    def test_get_pool_stats_not_initialized(self):
        """Test getting pool stats when pool is not initialized."""
        manager = ConnectionManager(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/XEPDB1",
        )

        stats = manager.get_pool_stats()

        assert stats["status"] == "not_initialized"

    @patch('cx_Oracle.SessionPool')
    def test_get_pool_stats_active(self, mock_pool_class):
        """Test getting pool stats when pool is active."""
        # Setup mock
        mock_pool = Mock()
        mock_pool.min = 5
        mock_pool.max = 20
        mock_pool.busy = 3
        mock_pool.opened = 8
        mock_pool.timeout = 300
        mock_pool_class.return_value = mock_pool

        manager = ConnectionManager(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/XEPDB1",
        )
        manager.create_pool()

        stats = manager.get_pool_stats()

        assert stats["status"] == "active"
        assert stats["min_size"] == 5
        assert stats["max_size"] == 20
        assert stats["busy_count"] == 3
        assert stats["open_count"] == 8
        assert stats["timeout"] == 300
