import sys
import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.db import connect_db, disconnect_db, db
from app.scheduler import start_background_scheduler, stop_background_scheduler
from app.services.notification.dispatcher import start_notification_dispatcher

from app.api.v1.endpoints.send import router as send_notification_router
from app.api.v1.endpoints.auth import router as vulms_watcher_router
from app.api.v1.endpoints.parser import router as vulms_watcher_parse_router

from app.middlewares.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

# Global Logging Configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("VULMS_Main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan context manager for managing async DB connection,
    background scheduler, and notification dispatcher task lifecycle.
    """
    logger.info("Initializing VULMS AI Companion Backend Services...")

    # 1. Database Connection Setup
    await connect_db()

    # 2. Start Background Scheduler (Interval Poller)
    start_background_scheduler(interval_hours=settings.WATCHER_INTERVAL_HOURS)

    # 3. Start Notification Dispatcher as Async Background Task
    dispatcher_task = asyncio.create_task(start_notification_dispatcher())

    logger.info("Application startup sequence completed.")

    yield

    # Shutdown Sequence
    logger.info("Shutting down VULMS AI Companion Backend Services...")

    stop_background_scheduler()

    if not dispatcher_task.done():
        dispatcher_task.cancel()
        try:
            await dispatcher_task
        except asyncio.CancelledError:
            logger.info("Notification Dispatcher background task cancelled.")

    await disconnect_db()
    logger.info("Shutdown sequence completed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise API engine for VULMS watcher, notifications, and AI automation.",
    lifespan=lifespan,
)

# ────── Global Exception Middlewares ─────────────────────────────────────────────
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# ────── Health & System Status Endpoint ─────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns database connection status and server health state."""
    db_connected = db.is_connected()
    return {
        "status": "online" if db_connected else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_connected,
    }


# ────── API Routers ─────────────────────────────────────────────────────────────
app.include_router(
    send_notification_router, prefix="/api/v1", tags=["Notifications [Version 1]"]
)
app.include_router(
    vulms_watcher_router, prefix="/api/v1", tags=["Vulms Watcher [Version 1]"]
)
app.include_router(
    vulms_watcher_parse_router,
    prefix="/api/v1",
    tags=["Vulms Watcher Parser [Version 1]"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
