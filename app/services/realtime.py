from collections import defaultdict

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, event_id: str, websocket: WebSocket) -> None:
        event_id = str(event_id)
        await websocket.accept()
        self.connections[event_id].append(websocket)

    def disconnect(self, event_id: str, websocket: WebSocket) -> None:
        event_id = str(event_id)
        if websocket in self.connections[event_id]:
            self.connections[event_id].remove(websocket)

    async def broadcast(self, event_id: str, payload: dict) -> None:
        event_id = str(event_id)
        for socket in list(self.connections[event_id]):
            # Starlette's `send_json` uses `json.dumps` internally and does not
            # automatically handle non-JSON-native types (e.g. UUID, datetime).
            try:
                await socket.send_json(jsonable_encoder(payload))
            except Exception:
                self.disconnect(event_id, socket)


connection_manager = ConnectionManager()
