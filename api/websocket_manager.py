"""WebSocket connection manager — broadcasts agent events to all GUI clients."""

import json
import logging
from typing import Any, Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug("[WS] Client connected — total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug("[WS] Client disconnected — total: %d", len(self.active_connections))

    async def broadcast(self, event: str, data: Dict[str, Any]) -> None:
        """Broadcast a typed event to all connected clients."""
        payload = json.dumps({"event": event, "data": data})
        dead: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for ws in dead:
            self.disconnect(ws)

    async def send_agent_status(
        self,
        agent: str,
        status: str,
        message: str = "",
        data: Dict[str, Any] | None = None,
    ) -> None:
        """
        Shorthand for broadcasting an agent status update.

        Parameters
        ----------
        agent   : "trend_master" | "analyse_master" | "trader_master"
        status  : "idle" | "analyzing" | "success" | "error"
        message : Human-readable description
        data    : Optional payload (e.g. TrendReport, TradeSignal)
        """
        await self.broadcast(
            "agent_status",
            {
                "agent": agent,
                "status": status,
                "message": message,
                "data": data or {},
            },
        )
