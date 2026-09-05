import logging
from prisma import Prisma

logger = logging.getLogger("VULMS_Server")

# Single global instance of Prisma client
db = Prisma()


async def connect_db() -> None:
    """Connects Prisma client to PostgreSQL if not connected."""
    if not db.is_connected():
        logger.info("Connecting to database via Prisma...")
        await db.connect()
        logger.info("Database connection successfully established.")


async def disconnect_db() -> None:
    """Disconnects Prisma client gracefully on application shutdown."""
    if db.is_connected():
        logger.info("Disconnecting from database...")
        await db.disconnect()
        logger.info("Database disconnected.")