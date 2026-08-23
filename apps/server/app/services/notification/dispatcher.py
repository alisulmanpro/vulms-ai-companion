import asyncio
import random
from datetime import datetime, timezone
import httpx

from app.core.config import settings
from app.core.db import db


async def send_whatsapp_via_evolution(phone: str, text: str) -> dict:
    """Evolution API call helper function."""
    url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE}"
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": phone,
        "text": text
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        return {"success": False, "error": response.text}


async def start_notification_dispatcher():
    """Background loop that continuously checks and dispatches notifications."""
    print("WhatsApp Dispatcher engine started...")

    while True:
        try:
            # 1. Fetch Oldest PENDING notification
            notification = await db.notification.find_first(
                where={
                    "status": "PENDING",
                    "retryCount": {"lt": settings.MAX_RETRIES}
                },
                order={"createdAt": "asc"}
            )

            if not notification:
                await asyncio.sleep(2)
                continue

            # 2. Update status to PROCESSING
            await db.notification.update(
                where={"id": notification.id},
                data={"status": "PROCESSING"}
            )

            # 3. Attempt Evolution Call safely
            try:
                res = await send_whatsapp_via_evolution(
                    phone=notification.phoneNumber,
                    text=notification.messageBody
                )

                if res.get("success"):
                    msg_id = res["data"].get("key", {}).get("id")
                    await db.notification.update(
                        where={"id": notification.id},
                        data={
                            "status": "SENT",
                            "sentAt": datetime.now(timezone.utc),
                            "evolutionMsgId": msg_id,
                            "errorReason": None
                        }
                    )
                    print(f"Sent to {notification.phoneNumber}")
                else:
                    raise Exception(res.get("error", "Failed to send message via Evolution API"))

            except Exception as send_error:
                # Catch any HTTP/API failure and handle retries/failures properly
                new_retry_count = notification.retryCount + 1
                is_failed = new_retry_count >= settings.MAX_RETRIES

                await db.notification.update(
                    where={"id": notification.id},
                    data={
                        "status": "FAILED" if is_failed else "PENDING",
                        "retryCount": new_retry_count,
                        "errorReason": str(send_error)
                    }
                )
                print(f"Error sending to {notification.phoneNumber}: {send_error}")

            # 4. Anti-Ban Jitter Delay
            delay = random.uniform(3.0, 8.0)
            await asyncio.sleep(delay)

        except asyncio.CancelledError:
            print("Dispatcher stopped gracefully.")
            break
        except Exception as e:
            print(f"Dispatcher loop error: {str(e)}")
            await asyncio.sleep(5)
