import logging
from typing import Optional, Tuple
from app.core.security import vault
from app.core.db import db

logger = logging.getLogger("VULMS_Server")


class VulmsCredentialService:
    """Service handling transparent AES-256-GCM encryption/decryption for tenant credentials."""

    @staticmethod
    async def store_student_credentials(
        user_id: str, student_id: str, raw_password: str
    ) -> None:
        """Encrypts raw password at rest before persisting to PostgreSQL."""
        encrypted_pwd = vault.encrypt(raw_password)

        await db.vulmsaccount.upsert(
            where={"userId": user_id},
            data={
                "create": {
                    "userId": user_id,
                    "studentId": student_id,
                    "encryptedPassword": encrypted_pwd,
                    "aspSessionId": "",
                },
                "update": {
                    "studentId": student_id,
                    "encryptedPassword": encrypted_pwd,
                    "isActive": True,
                },
            },
        )
        logger.info(f"Stored encrypted credentials for student: {student_id}")

    @staticmethod
    async def get_decrypted_credentials(account_id: str) -> Optional[Tuple[str, str]]:
        """
        Retrieves account and returns (student_id, raw_password).
        Decrypted password remains in ephemeral stack memory only.
        """
        account = await db.vulmsaccount.find_unique(where={"id": account_id})
        if not account or not account.isActive:
            return None

        raw_password = vault.decrypt(account.encryptedPassword)
        return account.studentId, raw_password

    @staticmethod
    async def set_user_active_status(student_id: str, is_active: bool) -> bool:
        """
        Updates account isActive status.
        If is_active is True (user active / browser open):
          - Sets isActive = True and updates updatedAt.
          - Immediately purges all queued PENDING notifications in DB for that user's phone number.
        """
        account = await db.vulmsaccount.find_first(
            where={"studentId": student_id},
            include={"user": True}
        )
        if not account:
            logger.warning(f"set_user_active_status: Account for student_id '{student_id}' not found.")
            return False

        await db.vulmsaccount.update(
            where={"id": account.id},
            data={"isActive": is_active}
        )

        if is_active:
            phone_number = (
                account.user.whatsappNumber
                if account.user and hasattr(account.user, "whatsappNumber")
                else None
            )
            if phone_number:
                deleted_res = await db.notification.delete_many(
                    where={"phoneNumber": phone_number, "status": "PENDING"}
                )
                deleted_count = deleted_res if isinstance(deleted_res, int) else getattr(deleted_res, "count", 0)
                logger.info(
                    f"User {student_id} activated (isActive=True). "
                    f"Halted tracing & purged {deleted_count} queued PENDING notification(s)."
                )
            else:
                logger.info(f"User {student_id} activated (isActive=True). Halted tracing.")
        else:
            logger.info(f"User {student_id} marked inactive (isActive=False). Tracing resumed.")

        return True

