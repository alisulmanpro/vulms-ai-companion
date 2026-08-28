from prisma import Prisma
from app.services.vulms_watcher.notification_engine import VULMSNotificationEngine
from app.services.vulms_watcher.parse_data_engine import ParseDataEngine


async def run_watcher_and_notify_pipeline(student_id: str, db: Prisma):
    # Step 1: Execute scraping engine
    watcher_engine = ParseDataEngine(db_client=db)
    parsed_result = await watcher_engine.run(student_id=student_id)

    if not parsed_result.get("success"):
        print(f"Scraper failed: {parsed_result.get('error')}")
        return

    account = await db.vulmsaccount.find_first(where={"studentId": student_id})

    # Step 2: Pass output to notification engine
    notifier = VULMSNotificationEngine(db_client=db)
    notification_result = await notifier.run(
        phone_number=account.whatsappNumber,
        parsed_payload=parsed_result
    )

    print(f"Pipeline finished. Total alerts queued: {notification_result['queued_notifications']}")
