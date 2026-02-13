"""Integration tests for WebSocket endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app

client = TestClient(app)


class TestWebSocketEndpoints:
    """Test cases for WebSocket monitoring endpoints."""

    def test_websocket_queries_connection(self):
        """Test WebSocket connection for queries monitoring."""
        with client.websocket_connect("/api/v1/ws/queries") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "connection_id" in data

    def test_websocket_sessions_connection(self):
        """Test WebSocket connection for sessions monitoring."""
        with client.websocket_connect("/api/v1/ws/sessions") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_websocket_wait_events_connection(self):
        """Test WebSocket connection for wait events monitoring."""
        with client.websocket_connect("/api/v1/ws/wait-events") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_websocket_metrics_connection(self):
        """Test WebSocket connection for metrics monitoring."""
        with client.websocket_connect("/api/v1/ws/metrics") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_websocket_queries_with_parameters(self):
        """Test queries WebSocket with custom parameters."""
        with client.websocket_connect(
            "/api/v1/ws/queries?poll_interval=2&min_elapsed_time=0.5&limit=5"
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

    def test_websocket_heartbeat(self):
        """Test WebSocket heartbeat mechanism."""
        with client.websocket_connect("/api/v1/ws/queries") as websocket:
            # Receive welcome message
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_invalid_message(self):
        """Test handling of invalid WebSocket message."""
        with client.websocket_connect("/api/v1/ws/queries") as websocket:
            websocket.receive_json()  # Welcome message

            # Send invalid JSON
            websocket.send_text("invalid json{")

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"

    def test_websocket_subscription(self):
        """Test topic subscription via WebSocket."""
        with client.websocket_connect("/api/v1/ws/queries") as websocket:
            websocket.receive_json()  # Welcome message

            # Subscribe to additional topic
            websocket.send_json({"type": "subscribe", "topic": "alerts"})

            # Unsubscribe
            websocket.send_json({"type": "unsubscribe", "topic": "alerts"})

    def test_websocket_configure(self):
        """Test WebSocket configuration update."""
        with client.websocket_connect("/api/v1/ws/queries") as websocket:
            websocket.receive_json()  # Welcome message

            # Update poll interval
            websocket.send_json({
                "type": "configure",
                "config": {"poll_interval": 10}
            })

    @pytest.mark.asyncio
    async def test_connection_manager_multiple_clients(self):
        """Test connection manager with multiple clients."""
        from app.core.websocket.connection_manager import ConnectionManager

        manager = ConnectionManager()

        # Add multiple connections
        mock_ws1 = Mock()
        mock_ws2 = Mock()

        await manager.connect(mock_ws1, "conn1")
        await manager.connect(mock_ws2, "conn2")

        assert manager.get_active_connection_count() == 2

        # Disconnect one
        manager.disconnect("conn1")
        assert manager.get_active_connection_count() == 1

        # Cleanup
        manager.disconnect("conn2")
        assert manager.get_active_connection_count() == 0

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """Test broadcasting to topic subscribers."""
        from app.core.websocket.connection_manager import ConnectionManager

        manager = ConnectionManager()

        mock_ws1 = Mock()
        mock_ws2 = Mock()

        # Mock send_json as coroutine
        async def mock_send_json(data):
            pass

        mock_ws1.send_json = mock_send_json
        mock_ws2.send_json = mock_send_json

        await manager.connect(mock_ws1, "conn1")
        await manager.connect(mock_ws2, "conn2")

        # Subscribe to topic
        manager.subscribe("conn1", "test_topic")
        manager.subscribe("conn2", "test_topic")

        # Broadcast message
        count = await manager.broadcast("test_topic", {"data": "test"})
        assert count == 2

        # Cleanup
        manager.disconnect("conn1")
        manager.disconnect("conn2")

    @pytest.mark.asyncio
    async def test_connection_manager_heartbeat(self):
        """Test heartbeat handling."""
        from app.core.websocket.connection_manager import ConnectionManager

        manager = ConnectionManager()

        mock_ws = Mock()

        async def mock_send_json(data):
            pass

        mock_ws.send_json = mock_send_json

        await manager.connect(mock_ws, "conn1")

        # Handle heartbeat
        await manager.handle_heartbeat("conn1")

        # Check last heartbeat was updated
        info = manager.get_connection_info("conn1")
        assert info is not None
        assert "last_heartbeat" in info

        # Cleanup
        manager.disconnect("conn1")
