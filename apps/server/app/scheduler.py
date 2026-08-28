import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.db import db
from app.services.vulms_watcher.notification_engine import VULMSNotificationEngine
from app.services.vulms_watcher.parse_data_engine import ParseDataEngine

logger = logging.getLogger("VULMS_Watcher")

# Global instance of AsyncIOScheduler bound to FastAPI's event loop
scheduler = AsyncIOScheduler()


async def execute_watcher_cycle():
    """
    Main background task executed periodically by APScheduler.
    Fetches accounts, executes parsing engines, and queues alert notifications.
    """
    logger.info("Scheduler:\t\t\tWatcher cycle started.")
    try:
        parse_engine = ParseDataEngine(db_client=db)
        notification_engine = VULMSNotificationEngine(db_client=db)

        # Retrieve registered VULMS accounts
        accounts = await db.vulmsaccount.find_many(include={"user": True})
        if not accounts:
            logger.info("Scheduler:\t\t\tNo registered accounts found to process.")
            return

        logger.info(f"Scheduler:\t\t\tProcessing {len(accounts)} account(s)...")

        for account in accounts:
            student_id = account.studentId
            phone_number = getattr(account, "whatsappNumber", None) or (
                account.user.whatsappNumber if hasattr(account, "user") and account.user else None
            )

            if not phone_number:
                logger.warning(f"Scheduler:\t\t\tSkipping {student_id}: Missing phone number.")
                continue

            try:
                # Trigger Data Extraction
                parsed_payload = await parse_engine.run(student_id=student_id)
                if not parsed_payload.get("success"):
                    logger.error(f"Scheduler:\tParsing failed for {student_id}: {parsed_payload.get('error')}")
                    continue

                # Stage Notifications
                notif_result = await notification_engine.run(
                    phone_number=phone_number,
                    parsed_payload=parsed_payload
                )
                queued_count = notif_result.get("queued_notifications", 0)
                logger.info(f"Scheduler:\tProcessed {student_id}. Queued {queued_count} notification(s).")

            except Exception as user_err:
                logger.error(f"Scheduler:\tError processing student {student_id}: {str(user_err)}", exc_info=True)

    except Exception as cycle_err:
        logger.critical(f"Scheduler:\tWatcher cycle failure: {str(cycle_err)}", exc_info=True)

    logger.info("Scheduler:\tWatcher cycle completed.")


def start_background_scheduler(interval_hours: float = 1.0):
    """
    Configures and starts the background interval scheduler.

    :param interval_hours: Frequency of watcher cycles in hours (e.g., 1.0 = every hour, 0.00833 = ~30s for testing)
    """
    if not scheduler.running:
        scheduler.add_job(
            execute_watcher_cycle,
            trigger="interval",
            hours=interval_hours,
            next_run_time=datetime.now(),  # Triggers an immediate first run on startup
            id="vulms_watcher_interval_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Scheduler:\tBackground Scheduler initialized. Running every {interval_hours} hour(s).")


def stop_background_scheduler():
    """
    Shuts down the background scheduler cleanly.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler:\tBackground Scheduler terminated gracefully.")
