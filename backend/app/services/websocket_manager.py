"""Real-time WebSocket manager for live conversation updates."""

import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter

logger = logging.getLogger("swiftreply.ws")
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per organisation."""

    def __init__(self):
        # org_id -> set of WebSocket connections
        self.active: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: str):
        await websocket.accept()
        if org_id not in self.active:
            self.active[org_id] = set()
        self.active[org_id].add(websocket)
        logger.info(f"WS connected for org {org_id}. Total: {len(self.active[org_id])}")

    def disconnect(self, websocket: WebSocket, org_id: str):
        if org_id in self.active:
            self.active[org_id].discard(websocket)
            if not self.active[org_id]:
                del self.active[org_id]

    async def broadcast_to_org(self, org_id: str, data: dict):
        """Send JSON message to all connections for an org."""
        if org_id not in self.active:
            return
        dead = set()
        for ws in self.active[org_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active[org_id].discard(ws)


manager = ConnectionManager()


@router.websocket("/ws/{org_id}")
async def websocket_endpoint(websocket: WebSocket, org_id: str):
    """WebSocket endpoint for real-time conversation updates."""
    await manager.connect(websocket, org_id)
    try:
        while True:
            # Keep alive — client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, org_id)
        logger.info(f"WS disconnected for org {org_id}")
