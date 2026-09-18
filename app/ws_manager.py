import json

from fastapi import WebSocket


class DisplayConnectionManager:
    """Tracks display screens connected over WebSocket and fans out new submissions to all of them."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast_submission(self, submission: dict) -> None:
        payload = json.dumps({"type": "submission", "data": submission})
        dead = []
        for connection in self._connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self._connections.discard(connection)


manager = DisplayConnectionManager()
