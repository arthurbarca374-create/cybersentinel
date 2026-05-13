import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.auth import get_current_user
from backend.services.events import event_bus
from backend.core.security import decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ws", tags=["websocket"])


@router.websocket("/scan/{scan_id}")
async def scan_progress(websocket: WebSocket, scan_id: int, token: str = Query(...)):
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    channel = f"scan:{scan_id}"
    queue = event_bus.subscribe(channel)
    logger.info(f"WebSocket connected for scan {scan_id}")
    try:
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(data)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for scan {scan_id}")
    finally:
        event_bus.unsubscribe(channel, queue)
