"""Base WebSocket handler for real-time monitoring."""

from typing import Dict, Any, Optional, Callable, Awaitable
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
import uuid

from app.core.websocket.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)


class BaseWebSocketHandler:
    """Base class for WebSocket handlers."""

    def __init__(
        self,
        websocket: WebSocket,
        topic: str,
        poll_interval: float = 5.0
    ):
        """
        Initialize WebSocket handler.

        Args:
            websocket: WebSocket connection
            topic: Topic name for this handler
            poll_interval: Polling interval in seconds
        """
        self.websocket = websocket
        self.topic = topic
        self.poll_interval = poll_interval
        self.connection_id = str(uuid.uuid4())
        self.connection_manager = get_connection_manager()
        self.is_running = False

    async def handle_connection(self) -> None:
        """Handle WebSocket connection lifecycle."""
        try:
            # Accept connection
            await self.connection_manager.connect(
                self.websocket,
                self.connection_id,
                metadata={"topic": self.topic}
            )

            # Subscribe to topic
            self.connection_manager.subscribe(self.connection_id, self.topic)

            # Start polling and listening tasks
            self.is_running = True

            await asyncio.gather(
                self._poll_loop(),
                self._listen_loop(),
            )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected normally: {self.connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.connection_manager.disconnect(self.connection_id)

    async def _poll_loop(self) -> None:
        """Polling loop for fetching and broadcasting data."""
        while self.is_running:
            try:
                # Fetch data
                data = await self.fetch_data()

                if data is not None:
                    # Prepare message
                    message = {
                        "type": "data",
                        "topic": self.topic,
                        "data": data,
                        "timestamp": asyncio.get_event_loop().time(),
                    }

                    # Broadcast to all subscribers
                    await self.connection_manager.broadcast(self.topic, message)

                # Wait for next poll
                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error in poll loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    async def _listen_loop(self) -> None:
        """Listen loop for receiving client messages."""
        while self.is_running:
            try:
                # Receive message from client
                data = await self.websocket.receive_text()
                message = json.loads(data)

                # Handle message
                await self.handle_message(message)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await self.send_error("Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in listen loop: {e}", exc_info=True)

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming message from client.

        Args:
            message: Received message
        """
        message_type = message.get("type")

        if message_type == "ping":
            await self.connection_manager.handle_heartbeat(self.connection_id)

        elif message_type == "subscribe":
            topic = message.get("topic")
            if topic:
                self.connection_manager.subscribe(self.connection_id, topic)

        elif message_type == "unsubscribe":
            topic = message.get("topic")
            if topic:
                self.connection_manager.unsubscribe(self.connection_id, topic)

        elif message_type == "configure":
            # Handle configuration changes
            await self.handle_configure(message.get("config", {}))

        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def handle_configure(self, config: Dict[str, Any]) -> None:
        """
        Handle configuration message.

        Args:
            config: Configuration parameters
        """
        if "poll_interval" in config:
            self.poll_interval = max(1.0, float(config["poll_interval"]))
            logger.info(f"Updated poll interval to {self.poll_interval}s")

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data to broadcast.

        This method should be overridden by subclasses.

        Returns:
            Data to broadcast or None
        """
        raise NotImplementedError("Subclasses must implement fetch_data")

    async def send_error(self, error_message: str) -> None:
        """
        Send error message to client.

        Args:
            error_message: Error message
        """
        await self.connection_manager.send_personal_message(
            self.connection_id,
            {
                "type": "error",
                "error": error_message,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )
