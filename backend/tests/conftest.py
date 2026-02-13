"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_oracle_connection(mocker):
    """Mock Oracle connection fixture."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def sample_query_data():
    """Sample query data fixture."""
    return {
        "sql_id": "abc123xyz4567",
        "sql_text": "SELECT * FROM users WHERE id = :1",
        "elapsed_time": 1234.56,
        "executions": 100,
        "cpu_time": 987.65,
        "buffer_gets": 50000,
        "disk_reads": 1000,
        "rows_processed": 1,
    }
