from fastapi import APIRouter, HTTPException, status
from app.core.db import db
from app.schemas.notification import NotificationCreateSchema, BulkNotificationSchema
from app.schemas.notification import sanitize_phone_number
from typing import List

router = APIRouter(prefix="/notification")


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def create_single_notification(payload: NotificationCreateSchema):
    """
    Ingest a single notification into DB with PENDING status.
    The background dispatcher will process it automatically.
    """
    try:
        notification = await db.notification.create(
            data={
                "phoneNumber": payload.phoneNumber,
                "messageBody": payload.messageBody,
                "status": "PENDING"
            }
        )
        return {
            "success": True,
            "message": "Notification queued successfully",
            "data": {
                "id": notification.id,
                "phoneNumber": notification.phoneNumber,
                "status": notification.status
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue notification: {str(e)}"
        )


@router.post("/send-bulk", status_code=status.HTTP_201_CREATED)
async def create_bulk_notifications(payload: BulkNotificationSchema):
    """
    Ingest multiple notifications for broadcast broadcasts.
    """
    created_records = []
    for raw_phone in payload.phoneNumbers:
        try:
            clean_phone = sanitize_phone_number(raw_phone)
            created_records.append({
                "phoneNumber": clean_phone,
                "messageBody": payload.messageBody,
                "status": "PENDING"
            })
        except Exception:
            continue

    if not created_records:
        raise HTTPException(status_code=400, detail="No valid phone numbers provided")

    # Bulk create in Prisma
    await db.notification.create_many(data=created_records)

    return {
        "success": True,
        "message": f"Queued {len(created_records)} notifications successfully"
    }


@router.post("/send-batch", status_code=status.HTTP_201_CREATED)
async def create_batch_notifications(payload: List[NotificationCreateSchema]):
    """
    Ingest multiple distinct notifications with unique messages/numbers.
    Accepts: [{ "phoneNumber": "...", "messageBody": "..." }, ...]
    """
    created_records = []

    for item in payload:
        try:
            clean_phone = sanitize_phone_number(item.phoneNumber)
            if clean_phone and item.messageBody.strip():
                created_records.append({
                    "phoneNumber": clean_phone,
                    "messageBody": item.messageBody,
                    "status": "PENDING"
                })
        except Exception:
            continue

    if not created_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid notifications provided"
        )

    # Prisma Bulk Insert
    await db.notification.create_many(data=created_records)

    return {
        "success": True,
        "message": f"Queued {len(created_records)} notifications successfully"
    }
