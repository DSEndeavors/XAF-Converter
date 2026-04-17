"""WebSocket endpoint for real-time progress updates."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.session_manager import session_manager
from ..utils.security import validate_uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for receiving progress updates during parsing/export."""
    if not validate_uuid(session_id):
        await websocket.close(code=4000, reason="Invalid session ID")
        return

    session = session_manager.get_session(session_id)
    if session is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    session.ws_connections.append(websocket)

    try:
        # Keep connection open; send initial status
        await websocket.send_json({
            "session_id": session_id,
            "stage": "connected",
            "percentage": 0,
            "message": "Connected to progress updates",
        })

        # Keep connection alive until client disconnects
        while True:
            # Wait for client messages (e.g., ping/pong, close)
            data = await websocket.receive_text()
            # Echo back as acknowledgement
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("WebSocket connection error for session %s", session_id)
    finally:
        if websocket in session.ws_connections:
            session.ws_connections.remove(websocket)


async def broadcast_progress(
    session_id: str, stage: str, percentage: int, message: str
) -> None:
    """Broadcast a progress update to all WebSocket connections for a session."""
    session = session_manager.get_session(session_id)
    if session is None:
        return

    payload = json.dumps({
        "session_id": session_id,
        "stage": stage,
        "percentage": percentage,
        "message": message,
    }, ensure_ascii=True)

    disconnected = []
    for ws in session.ws_connections:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        session.ws_connections.remove(ws)
