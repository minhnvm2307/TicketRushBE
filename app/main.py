from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.responses import success_response
from app.core.telemetry import MetricsMiddleware, metrics_response
from app.db.session import Base, engine, SessionLocal
from app.models import all_models  # noqa: F401
from app.services.bootstrap import BootstrapService
from app.workers.process_queue import scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        BootstrapService(db).seed_admin()
    finally:
        db.close()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(MetricsMiddleware)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def healthcheck():
    return success_response({"status": "ok"})


@app.get("/metrics")
def metrics():
    return metrics_response()
