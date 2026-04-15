from fastapi import APIRouter

from app.api.routes import admin, auth, checkout, events, queue, recommendations, seats, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(events.router)
api_router.include_router(seats.router)
api_router.include_router(checkout.router)
api_router.include_router(admin.router)
api_router.include_router(recommendations.router)
api_router.include_router(queue.router)
api_router.include_router(ws.router)
