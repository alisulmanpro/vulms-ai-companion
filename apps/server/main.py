import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.db import connect_db, disconnect_db, db
from app.scheduler import start_background_scheduler, stop_background_scheduler
from app.services.notification.dispatcher import start_notification_dispatcher
from app.endpoints.api.v1.notifications.send import router as send_notification_router
from app.endpoints.api.v1.vulms_watcher.auth import router as vulms_watcher_router
from app.endpoints.api.v1.vulms_watcher.parser import router as vulms_watcher_parse_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Connect DB
    await connect_db()

    # Schedular Startup
    start_background_scheduler(interval_hours=0.0167)

    # Start Dispatcher as Async Background Task
    dispatcher_task = asyncio.create_task(start_notification_dispatcher())

    yield

    stop_background_scheduler()
    # Shutdown logic
    dispatcher_task.cancel()

    await disconnect_db()


app = FastAPI(
    title="VULMS AI Companion",
    version="1.0.0",
    lifespan=lifespan
)


# ────── Health Endpoint ───────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "database_connected": db.is_connected()
    }


# ────── Routers ───────────────────────────────────────────────────────────
app.include_router(send_notification_router, prefix="/api/v1", tags=["Notifications [Version 1]"])
app.include_router(vulms_watcher_router, prefix="/ap1/v1", tags=["Vulms Watcher [Version 1]"])
app.include_router(vulms_watcher_parse_router, prefix="/ap1/v1", tags=["Vulms Watcher Parser [Version 1]"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
