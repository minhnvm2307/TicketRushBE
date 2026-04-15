from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, event_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[event_id].append(websocket)

    def disconnect(self, event_id: str, websocket: WebSocket) -> None:
        if websocket in self.connections[event_id]:
            self.connections[event_id].remove(websocket)

    async def broadcast(self, event_id: str, payload: dict) -> None:
        for socket in list(self.connections[event_id]):
            await socket.send_json(payload)


connection_manager = ConnectionManager()
