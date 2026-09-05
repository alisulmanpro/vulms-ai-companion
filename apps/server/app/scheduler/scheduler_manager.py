import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.db import db
from app.services.vulms_watcher.notification_engine import VULMSNotificationEngine
from app.services.vulms_watcher.parse_data_engine import ParseDataEngine

logger = logging.getLogger("VULMS_Scheduler")

# Global instance of AsyncIOScheduler bound to FastAPI event loop
scheduler = AsyncIOScheduler()


async def observe_and_auto_inactivate_stale_accounts() -> None:
    """
    Observes isActive in database.
    If isActive == True but has not been updated for >30 minutes,
    automatically sets isActive = False so server tracing can resume.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        stale_accounts = await db.vulmsaccount.find_many(
            where={
                "isActive": True,
                "updatedAt": {"lte": cutoff}
            }
        )

        if stale_accounts:
            stale_ids = [acc.id for acc in stale_accounts]
            await db.vulmsaccount.update_many(
                where={"id": {"in": stale_ids}},
                data={"isActive": False}
            )
            for acc in stale_accounts:
                logger.info(
                    f"Scheduler: Auto-inactivated student {acc.studentId} "
                    f"(isActive was True but not updated for >30 mins)."
                )
    except Exception as err:
        logger.error(f"Scheduler: Error observing stale active accounts: {str(err)}", exc_info=True)


async def execute_watcher_cycle() -> None:
    """
    Main background task executed periodically by APScheduler.
    Auto-inactivates 30-min stale accounts, fetches inactive accounts (isActive == False),
    parses data engines, and queues alerts.
    """
    logger.info("Scheduler: Starting VULMS watcher cycle...")
    try:
        # Step 1: Auto-inactivate accounts with isActive=True if untouched for >30 minutes
        await observe_and_auto_inactivate_stale_accounts()

        parse_engine = ParseDataEngine(db_client=db)
        notification_engine = VULMSNotificationEngine(db_client=db)

        # Step 2: Retrieve registered INACTIVE VULMS accounts (isActive == False)
        # If isActive is True, server does NOT trace or send notifications to that user.
        accounts = await db.vulmsaccount.find_many(
            where={"isActive": False},
            include={"user": True}
        )

        if not accounts:
            logger.info("Scheduler: No inactive registered accounts found to trace.")
            return

        logger.info(f"Scheduler: Processing {len(accounts)} inactive account(s)...")

        for account in accounts:
            student_id = account.studentId
            phone_number = (
                account.user.whatsappNumber
                if account.user and hasattr(account.user, "whatsappNumber")
                else None
            )

            if not phone_number:
                logger.warning(f"Scheduler: Skipping student {student_id}: Missing phone number.")
                continue

            try:
                # Re-verify isActive status right before scraping
                current_acc = await db.vulmsaccount.find_unique(where={"id": account.id})
                if current_acc and current_acc.isActive:
                    logger.info(
                        f"Scheduler: Skipping student {student_id} - user opened browser (isActive=True). "
                        f"Purging queued PENDING notifications..."
                    )
                    await db.notification.delete_many(
                        where={"phoneNumber": phone_number, "status": "PENDING"}
                    )
                    continue

                # Trigger Data Extraction
                parsed_payload = await parse_engine.run(student_id=student_id, use_cache=False)
                if not parsed_payload.get("success"):
                    logger.error(f"Scheduler: Parsing failed for {student_id}: {parsed_payload.get('error')}")
                    continue

                # Re-verify isActive once more after Playwright/scraping finishes
                current_acc = await db.vulmsaccount.find_unique(where={"id": account.id})
                if current_acc and current_acc.isActive:
                    logger.info(
                        f"Scheduler: Aborting notification staging for student {student_id} - "
                        f"user became active mid-scrape (isActive=True). Purging PENDING notifications..."
                    )
                    await db.notification.delete_many(
                        where={"phoneNumber": phone_number, "status": "PENDING"}
                    )
                    continue

                # Stage Notifications
                notif_result = await notification_engine.run(
                    phone_number=phone_number,
                    parsed_payload=parsed_payload
                )
                queued_count = notif_result.get("queued_notifications", 0)
                logger.info(f"Scheduler: Processed {student_id}. Queued {queued_count} notification(s).")

            except Exception as user_err:
                logger.error(f"Scheduler: Error processing student {student_id}: {str(user_err)}", exc_info=True)

    except Exception as cycle_err:
        logger.critical(f"Scheduler: Watcher cycle failure: {str(cycle_err)}", exc_info=True)

    logger.info("Scheduler: Watcher cycle completed.")


def start_background_scheduler(interval_hours: float = 1.0) -> None:
    """Configures and starts the background interval scheduler."""
    if not scheduler.running:
        scheduler.add_job(
            execute_watcher_cycle,
            trigger="interval",
            hours=interval_hours,
            next_run_time=datetime.now(),
            id="vulms_watcher_interval_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(f"Background Scheduler started. Running every {interval_hours} hour(s).")


def stop_background_scheduler() -> None:
    """Shuts down the background scheduler cleanly."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background Scheduler terminated gracefully.")
