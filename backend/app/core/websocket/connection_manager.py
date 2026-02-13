"""WebSocket connection manager for handling multiple clients."""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time monitoring."""

    def __init__(self):
        """Initialize connection manager."""
        # Active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}

        # Subscriptions: topic -> set of connection IDs
        self.subscriptions: Dict[str, Set[str]] = {}

        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # Heartbeat tracking
        self.last_heartbeat: Dict[str, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            metadata: Optional connection metadata
        """
        await websocket.accept()

        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = metadata or {}
        self.last_heartbeat[connection_id] = datetime.utcnow()

        logger.info(f"WebSocket connected: {connection_id}")

        # Send welcome message
        await self.send_personal_message(
            connection_id,
            {
                "type": "connected",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def disconnect(self, connection_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            connection_id: Connection identifier
        """
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Remove from all subscriptions
        for topic in list(self.subscriptions.keys()):
            if connection_id in self.subscriptions[topic]:
                self.subscriptions[topic].remove(connection_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]

        # Remove metadata and heartbeat
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        if connection_id in self.last_heartbeat:
            del self.last_heartbeat[connection_id]

        logger.info(f"WebSocket disconnected: {connection_id}")

    def subscribe(self, connection_id: str, topic: str) -> None:
        """
        Subscribe a connection to a topic.

        Args:
            connection_id: Connection identifier
            topic: Topic to subscribe to
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()

        self.subscriptions[topic].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to {topic}")

    def unsubscribe(self, connection_id: str, topic: str) -> None:
        """
        Unsubscribe a connection from a topic.

        Args:
            connection_id: Connection identifier
            topic: Topic to unsubscribe from
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]

        logger.debug(f"Connection {connection_id} unsubscribed from {topic}")

    async def send_personal_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: Connection identifier
            message: Message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        if connection_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            self.disconnect(connection_id)
            return False

    async def broadcast(
        self,
        topic: str,
        message: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to all subscribers of a topic.

        Args:
            topic: Topic to broadcast to
            message: Message to broadcast

        Returns:
            Number of connections that received the message
        """
        if topic not in self.subscriptions:
            return 0

        sent_count = 0
        disconnected = []

        for connection_id in self.subscriptions[topic]:
            if connection_id in self.active_connections:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)

        return sent_count

    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message to broadcast

        Returns:
            Number of connections that received the message
        """
        sent_count = 0
        disconnected = []

        for connection_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)

        return sent_count

    async def handle_heartbeat(self, connection_id: str) -> None:
        """
        Handle heartbeat from a connection.

        Args:
            connection_id: Connection identifier
        """
        self.last_heartbeat[connection_id] = datetime.utcnow()

        await self.send_personal_message(
            connection_id,
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def check_stale_connections(
        self,
        timeout_seconds: int = 60
    ) -> None:
        """
        Check for stale connections and disconnect them.

        Args:
            timeout_seconds: Timeout in seconds
        """
        now = datetime.utcnow()
        stale_connections = []

        for connection_id, last_beat in self.last_heartbeat.items():
            if (now - last_beat).total_seconds() > timeout_seconds:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            logger.warning(f"Disconnecting stale connection: {connection_id}")
            self.disconnect(connection_id)

    def get_active_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            Number of active connections
        """
        return len(self.active_connections)

    def get_subscription_count(self, topic: str) -> int:
        """
        Get the number of subscribers for a topic.

        Args:
            topic: Topic name

        Returns:
            Number of subscribers
        """
        if topic not in self.subscriptions:
            return 0
        return len(self.subscriptions[topic])

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Connection information or None
        """
        if connection_id not in self.active_connections:
            return None

        return {
            "connection_id": connection_id,
            "metadata": self.connection_metadata.get(connection_id, {}),
            "last_heartbeat": self.last_heartbeat.get(connection_id),
            "subscriptions": [
                topic for topic, subs in self.subscriptions.items()
                if connection_id in subs
            ],
        }

    def get_all_connections_info(self) -> list:
        """
        Get information about all active connections.

        Returns:
            List of connection information
        """
        return [
            self.get_connection_info(conn_id)
            for conn_id in self.active_connections.keys()
        ]


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.

    Returns:
        ConnectionManager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
