import logging
from prisma import Prisma
from app.services.vulms_watcher.notification_engine import VULMSNotificationEngine
from app.services.vulms_watcher.parse_data_engine import ParseDataEngine

logger = logging.getLogger("VULMS_Watcher")


async def run_watcher_and_notify_pipeline(student_id: str, db: Prisma) -> None:
    """
    Executes data extraction for a student and queues resulting alert notifications.
    """
    # Step 1: Execute scraping engine
    watcher_engine = ParseDataEngine(db_client=db)
    parsed_result = await watcher_engine.run(student_id=student_id)

    if not parsed_result.get("success"):
        logger.error(f"Scraper pipeline failed for {student_id}: {parsed_result.get('error')}")
        return

    # Step 2: Fetch student account with user relation included for phone number lookup
    account = await db.vulmsaccount.find_first(
        where={"studentId": student_id},
        include={"user": True}
    )

    if not account:
        logger.error(f"Pipeline error: No database account found for studentId={student_id}")
        return

    phone_number = (
        account.user.whatsappNumber if account.user and hasattr(account.user, "whatsappNumber") else None
    )

    if not phone_number:
        logger.warning(f"Skipping notifications for {student_id}: No phone number associated.")
        return

    # Step 3: Pass parsed output to notification engine
    notifier = VULMSNotificationEngine(db_client=db)
    notification_result = await notifier.run(
        phone_number=phone_number,
        parsed_payload=parsed_result
    )

    queued = notification_result.get("queued_notifications", 0)
    logger.info(f"Pipeline finished for {student_id}. Total alerts queued: {queued}")
