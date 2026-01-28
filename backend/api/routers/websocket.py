"""
WebSocket Router for Real-Time Features

Provides WebSocket endpoints for real-time job updates, notifications, and more.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import (APIRouter, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import HTMLResponse

from api.middleware.auth import get_current_user_from_websocket
from api.websocket_manager import ConnectionType, websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/connect")
async def websocket_connect(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    connection_types: Optional[str] = Query("notifications"),
):
    """
    WebSocket connection endpoint

    Args:
        websocket: WebSocket connection
        token: JWT token for authentication (optional)
        connection_types: Comma-separated list of connection types
                         (notifications, job_updates, application_status, matches)
    """
    user_id = None

    # Authenticate if token provided
    if token:
        try:
            user_id = await get_current_user_from_websocket(websocket, token)
        except Exception as e:
            logger.warning("WebSocket auth failed: %s", e)
            # Allow anonymous connections for now
            pass

    # Parse connection types
    types = set()
    for ct in connection_types.split(","):
        ct = ct.strip()
        try:
            types.add(ConnectionType(ct))
        except ValueError:
            logger.warning("Unknown connection type: %s", ct)

    if not types:
        types = {ConnectionType.NOTIFICATIONS}

    # Accept connection
    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=user_id,
        connection_types=types,
        metadata={
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "client_ip": websocket.client.host if websocket.client else None,
        },
    )

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "connection_id": connection_id,
                "user_id": user_id,
                "connection_types": [ct.value for ct in types],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_websocket_message(connection_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket message error: %s", e)
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(e),
                    }
                )

    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(connection_id)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Dedicated WebSocket endpoint for notifications

    Args:
        websocket: WebSocket connection
        token: JWT token for authentication
    """
    user_id = await get_current_user_from_websocket(websocket, token)

    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=user_id,
        connection_types={ConnectionType.NOTIFICATIONS},
    )

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "connection_id": connection_id,
                "channel": "notifications",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_websocket_message(connection_id, data)
            except WebSocketDisconnect:
                break

    finally:
        await websocket_manager.disconnect(connection_id)


@router.websocket("/jobs")
async def websocket_jobs(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Dedicated WebSocket endpoint for job updates

    Args:
        websocket: WebSocket connection
        token: JWT token (optional)
    """
    user_id = None
    if token:
        try:
            user_id = await get_current_user_from_websocket(websocket, token)
        except Exception:
            pass

    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=user_id,
        connection_types={ConnectionType.JOB_UPDATES, ConnectionType.MATCHES},
    )

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "connection_id": connection_id,
                "channel": "jobs",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        while True:
            try:
                data = await websocket.receive_json()
                await handle_websocket_message(connection_id, data)
            except WebSocketDisconnect:
                break

    finally:
        await websocket_manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, data: dict) -> None:
    """
    Handle incoming WebSocket messages

    Args:
        connection_id: Connection ID
        data: Message data
    """
    message_type = data.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        await websocket_manager._send_message(
            connection_id,
            {
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    elif message_type == "subscribe":
        # Subscribe to additional connection types
        new_types = data.get("connection_types", [])
        async with websocket_manager._lock:
            conn = websocket_manager._connections.get(connection_id)
            if conn:
                for ct in new_types:
                    try:
                        conn.connection_types.add(ConnectionType(ct))
                        if ct not in websocket_manager._type_connections:
                            websocket_manager._type_connections[ct] = set()
                        websocket_manager._type_connections[ct].add(connection_id)
                    except ValueError:
                        pass

    elif message_type == "unsubscribe":
        # Unsubscribe from connection types
        remove_types = data.get("connection_types", [])
        async with websocket_manager._lock:
            conn = websocket_manager._connections.get(connection_id)
            if conn:
                for ct in remove_types:
                    try:
                        conn.connection_types.discard(ConnectionType(ct))
                    except ValueError:
                        pass

    elif message_type == "job_preference":
        # Update job preferences for real-time filtering
        preferences = data.get("preferences", {})
        async with websocket_manager._lock:
            conn = websocket_manager._connections.get(connection_id)
            if conn:
                conn.metadata["job_preferences"] = preferences

    else:
        logger.warning("Unknown WebSocket message type: %s", message_type)


@router.get("/stats")
async def get_websocket_stats() -> dict:
    """
    Get WebSocket connection statistics (for monitoring)

    Returns:
        Dictionary with connection statistics
    """
    return {
        "total_connections": websocket_manager.get_connection_count(),
        "connections_by_type": {
            ct.value: websocket_manager.get_type_connection_count(ct)
            for ct in ConnectionType
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Simple HTML page for WebSocket testing
WEBSOCKET_TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JobSwipe WebSocket Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
        #messages { height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
        .message { margin: 5px 0; padding: 5px; background: #f0f0f0; }
        .sent { background: #e0f7fa; }
        .received { background: #f3e5f5; }
        .error { background: #ffebee; }
        #status { font-weight: bold; margin: 10px 0; }
        .connected { color: green; }
        .disconnected { color: red; }
    </style>
</head>
<body>
    <h1>JobSwipe WebSocket Test</h1>
    
    <div id="status" class="disconnected">Disconnected</div>
    
    <div>
        <label>Token (optional): <input type="text" id="token" size="50"></label>
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    
    <div>
        <button onclick="sendPing()">Send Ping</button>
        <button onclick="sendSubscribe()">Subscribe to Jobs</button>
    </div>
    
    <h3>Messages</h3>
    <div id="messages"></div>
    
    <script>
        let ws = null;
        
        function log(message, type = 'received') {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = `${new Date().toLocaleTimeString()}: ${JSON.stringify(message)}`;
            document.getElementById('messages').appendChild(div);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
        
        function updateStatus(connected) {
            const status = document.getElementById('status');
            status.textContent = connected ? 'Connected' : 'Disconnected';
            status.className = connected ? 'connected' : 'disconnected';
        }
        
        function connect() {
            const token = document.getElementById('token').value;
            const url = `ws://${window.location.host}/api/v1/ws/connect${token ? '?token=' + token : ''}`;
            
            ws = new WebSocket(url);
            
            ws.onopen = () => {
                log({ type: 'connected' }, 'sent');
                updateStatus(true);
            };
            
            ws.onclose = () => {
                log({ type: 'disconnected' }, 'error');
                updateStatus(false);
            };
            
            ws.onerror = (error) => {
                log({ type: 'error', error }, 'error');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                log(data, 'received');
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }
        
        function sendPing() {
            if (ws) {
                ws.send(JSON.stringify({ type: 'ping' }));
                log({ type: 'ping' }, 'sent');
            }
        }
        
        function sendSubscribe() {
            if (ws) {
                ws.send(JSON.stringify({ 
                    type: 'subscribe',
                    connection_types: ['job_updates', 'matches']
                }));
                log({ type: 'subscribe', connection_types: ['job_updates', 'matches'] }, 'sent');
            }
        }
    </script>
</body>
</html>
"""


@router.get("/test")
async def websocket_test() -> HTMLResponse:
    """WebSocket test page"""
    return HTMLResponse(WEBSOCKET_TEST_HTML)
