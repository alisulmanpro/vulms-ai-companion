import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.core.db import db
from app.schemas.notification import NotificationCreateSchema, BulkNotificationSchema, sanitize_phone_number

logger = logging.getLogger("VULMS_NotificationAPI")

router = APIRouter(prefix="/notification", tags=["Notifications"])


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
        logger.error(f"Failed to queue notification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue notification: {str(e)}"
        )


@router.post("/send-bulk", status_code=status.HTTP_201_CREATED)
async def create_bulk_notifications(payload: BulkNotificationSchema):
    """
    Ingest multiple notifications for broadcast.
    """
    created_records = []
    for raw_phone in payload.phoneNumbers:
        try:
            clean_phone = sanitize_phone_number(raw_phone)
            if clean_phone:
                created_records.append({
                    "phoneNumber": clean_phone,
                    "messageBody": payload.messageBody,
                    "status": "PENDING"
                })
        except Exception:
            continue

    if not created_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid phone numbers provided"
        )

    await db.notification.create_many(data=created_records)

    return {
        "success": True,
        "message": f"Queued {len(created_records)} notifications successfully"
    }


@router.post("/send-batch", status_code=status.HTTP_201_CREATED)
async def create_batch_notifications(payload: List[NotificationCreateSchema]):
    """
    Ingest multiple distinct notifications with unique messages and numbers.
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

    await db.notification.create_many(data=created_records)

    return {
        "success": True,
        "message": f"Queued {len(created_records)} notifications successfully"
    }
