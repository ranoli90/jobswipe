"""
WebSocket Manager for Real-Time Features

Manages WebSocket connections for real-time job updates, notifications, and more.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionType(str, Enum):
    """Type of WebSocket connection"""

    JOB_UPDATES = "job_updates"
    NOTIFICATIONS = "notifications"
    APPLICATION_STATUS = "application_status"
    MATCHES = "matches"


@dataclass
class WebSocketConnection:
    """WebSocket connection data"""

    websocket: WebSocket
    user_id: Optional[str] = None
    connection_types: Set[ConnectionType] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time features.

    Features:
    - Multiple connection types per user
    - Heartbeat/ping-pong for connection health
    - Automatic reconnection handling
    - Message broadcasting to specific users or all connections
    - Connection rate limiting
    """

    def __init__(self):
        # Mapping of connection_id -> WebSocketConnection
        self._connections: Dict[str, WebSocketConnection] = {}
        # Mapping of user_id -> set of connection_ids
        self._user_connections: Dict[str, Set[str]] = {}
        # Mapping of connection_type -> set of connection_ids
        self._type_connections: Dict[ConnectionType, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        # Connection ID counter
        self._connection_counter = 0

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        connection_types: Optional[Set[ConnectionType]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Accept a new WebSocket connection

        Args:
            websocket: FastAPI WebSocket
            user_id: User ID (optional for anonymous connections)
            connection_types: Types of connections to subscribe to
            metadata: Additional connection metadata

        Returns:
            Connection ID
        """
        await websocket.accept()

        async with self._lock:
            self._connection_counter += 1
            connection_id = f"conn_{self._connection_counter}"

            conn = WebSocketConnection(
                websocket=websocket,
                user_id=user_id,
                connection_types=connection_types or {ConnectionType.NOTIFICATIONS},
                metadata=metadata or {},
            )

            self._connections[connection_id] = conn

            if user_id:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(connection_id)

            for conn_type in conn.connection_types:
                if conn_type not in self._type_connections:
                    self._type_connections[conn_type] = set()
                self._type_connections[conn_type].add(connection_id)

            logger.info("WebSocket connected: %s (user: %s)", ('connection_id', 'user_id'))

        # Start heartbeat for this connection
        asyncio.create_task(self._heartbeat(connection_id))

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect a WebSocket connection

        Args:
            connection_id: Connection ID to disconnect
        """
        async with self._lock:
            conn = self._connections.pop(connection_id, None)
            if not conn:
                return

            if conn.user_id and conn.user_id in self._user_connections:
                self._user_connections[conn.user_id].discard(connection_id)
                if not self._user_connections[conn.user_id]:
                    del self._user_connections[conn.user_id]

            for conn_type in conn.connection_types:
                if conn_type in self._type_connections:
                    self._type_connections[conn_type].discard(connection_id)

            logger.info("WebSocket disconnected: %s", connection_id)

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        user_id: str,
    ) -> int:
        """
        Send message to all connections for a specific user

        Args:
            message: Message to send (will be JSON serialized)
            user_id: Target user ID

        Returns:
            Number of connections message was sent to
        """
        sent_count = 0

        async with self._lock:
            connection_ids = self._user_connections.get(user_id, set()).copy()

        for connection_id in connection_ids:
            if await self._send_message(connection_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_to_type(
        self,
        message: Dict[str, Any],
        connection_type: ConnectionType,
    ) -> int:
        """
        Broadcast message to all connections of a specific type

        Args:
            message: Message to send
            connection_type: Type of connections to target

        Returns:
            Number of connections message was sent to
        """
        sent_count = 0

        async with self._lock:
            connection_ids = self._type_connections.get(connection_type, set()).copy()

        for connection_id in connection_ids:
            if await self._send_message(connection_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """
        Broadcast message to all connected clients

        Args:
            message: Message to send

        Returns:
            Number of connections message was sent to
        """
        sent_count = 0

        async with self._lock:
            connection_ids = list(self._connections.keys())

        for connection_id in connection_ids:
            if await self._send_message(connection_id, message):
                sent_count += 1

        return sent_count

    async def _send_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """
        Send message to a specific connection

        Args:
            connection_id: Target connection ID
            message: Message to send

        Returns:
            True if message was sent successfully
        """
        async with self._lock:
            conn = self._connections.get(connection_id)
            if not conn:
                return False

        try:
            await conn.websocket.send_json(message)
            return True
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error("Failed to send message to %s: %s", ('connection_id', 'e'))
            return False

    async def _heartbeat(self, connection_id: str) -> None:
        """
        Send periodic heartbeat to connection

        Args:
            connection_id: Connection ID
        """
        while True:
            await asyncio.sleep(30)  # 30 second heartbeat

            async with self._lock:
                conn = self._connections.get(connection_id)
                if not conn:
                    return

            try:
                # Send ping
                await conn.websocket.send_json(
                    {
                        "type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

                # Update last ping time
                conn.last_ping = datetime.now(timezone.utc)
            except WebSocketDisconnect:
                await self.disconnect(connection_id)
                return
            except Exception as e:
                logger.error("Heartbeat failed for %s: %s", ('connection_id', 'e'))
                await self.disconnect(connection_id)
                return

    async def handle_pong(self, connection_id: str) -> None:
        """Handle pong response from client"""
        async with self._lock:
            conn = self._connections.get(connection_id)
            if conn:
                conn.last_ping = datetime.now(timezone.utc)

    def get_connection_count(self) -> int:
        """Get total number of connections"""
        return len(self._connections)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user"""
        return len(self._user_connections.get(user_id, set()))

    def get_type_connection_count(self, connection_type: ConnectionType) -> int:
        """Get number of connections for a specific type"""
        return len(self._type_connections.get(connection_type, set()))

    async def cleanup_stale_connections(self, max_age_seconds: int = 300) -> int:
        """
        Remove connections that haven't sent a pong in max_age_seconds

        Args:
            max_age_seconds: Maximum time since last ping

        Returns:
            Number of connections removed
        """
        removed = 0
        now = datetime.now(timezone.utc)

        async with self._lock:
            stale_ids = [
                conn_id
                for conn_id, conn in self._connections.items()
                if (now - conn.last_ping).total_seconds() > max_age_seconds
            ]

        for connection_id in stale_ids:
            await self.disconnect(connection_id)
            removed += 1

        if removed > 0:
            logger.info("Cleaned up %s stale WebSocket connections", removed)

        return removed


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
