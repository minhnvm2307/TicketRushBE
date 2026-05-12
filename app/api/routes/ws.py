from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from app.core.redis import RedisKey, get_redis_client, redis_is_enabled
from app.core.security import decode_access_token
from app.repositories.user import UserRepository
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.services.dashboard import DashboardService
from app.services.realtime import connection_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/events/{event_id}")
async def event_updates(websocket: WebSocket, event_id: str):
    await connection_manager.connect(event_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(event_id, websocket)


@router.websocket("/ws/admin/dashboard/{event_id}")
async def admin_dashboard_updates(websocket: WebSocket, event_id: str, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
    except ValueError:
        await websocket.close(code=1008)
        return
    session_id = payload.get("sid")
    if session_id and redis_is_enabled():
        session_user_id = get_redis_client().get(RedisKey.auth_session(session_id))
        if session_user_id != str(payload["sub"]):
            await websocket.close(code=1008)
            return

    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_id(payload["sub"])
        if not user or user.role != UserRole.ADMIN:
            await websocket.close(code=1008)
            return
        room = f"admin-dashboard:{event_id}"
        await connection_manager.connect(room, websocket)
        await websocket.send_json(
            jsonable_encoder({"type": "dashboard_update", **DashboardService(db).dashboard(event_id)})
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(f"admin-dashboard:{event_id}", websocket)
    finally:
        db.close()
