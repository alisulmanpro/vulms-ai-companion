import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.db import connect_db, disconnect_db, db
from app.services.notification.dispatcher import start_notification_dispatcher
from app.endpoints.api.v1.notifications.send import router as send_notification_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 1. Connect DB
    await connect_db()

    # 2. Start Dispatcher as Async Background Task
    dispatcher_task = asyncio.create_task(start_notification_dispatcher())

    yield

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

# ────── Notification Endpoint ───────────────────────────────────────────────────────────
app.include_router(send_notification_router, prefix="/api/v1", tags=["Notifications"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=800, reload=True)
