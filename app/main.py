import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.responses import success_response
from app.core.telemetry import MetricsMiddleware, metrics_response
from app.db.session import Base, engine, SessionLocal
from app.services.bootstrap import BootstrapService
from app.workers.process_queue import process_queues_job


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        BootstrapService(db).seed_admin()
        BootstrapService(db).seed_user()
    finally:
        db.close()

    # Start the queue processing worker in the background
    worker_task = asyncio.create_task(process_queues_job())
    yield
    # Clean up the worker task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def healthcheck():
    return success_response({"status": "ok"})


@app.get("/metrics")
def metrics():
    return metrics_response()
