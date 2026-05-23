# Thanatos\apps\api_server\routes\websocket.py

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.session_manager import SessionManager
from ..core.agent_loop import run_agent_loop
from ..schemas.websocket_models import HeartbeatMessage

logger = logging.getLogger(__name__)
router = APIRouter()

HEARTBEAT_INTERVAL = 15  # seconds


async def send_heartbeat(websocket: WebSocket, stop_event: asyncio.Event) -> None:
    """Periodically send a heartbeat message to keep the connection alive."""
    while not stop_event.is_set():
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        if not stop_event.is_set():
            try:
                await websocket.send_json(HeartbeatMessage().model_dump())
            except Exception:
                logger.exception("Heartbeat send failed, stopping.")
                stop_event.set()
                break


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint that manages a single conversation session.
    For each connection a SessionManager is created, a heartbeat is started,
    and the agent loop processes incoming user messages.
    """
    await websocket.accept()
    session_id = str(id(websocket))  # simple unique ID per connection
    session_manager = SessionManager(session_id=session_id)
    stop_heartbeat = asyncio.Event()

    heartbeat_task = asyncio.create_task(send_heartbeat(websocket, stop_heartbeat))

    try:
        await run_agent_loop(websocket, session_manager)
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", session_id)
    except Exception as exc:
        logger.exception("Unhandled error in WebSocket endpoint: %s", exc)
    finally:
        stop_heartbeat.set()
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await websocket.close()