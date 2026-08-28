from typing import Optional, Tuple
from app.core.security import vault
from app.core import db


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
                },
                "update": {
                    "studentId": student_id,
                    "encryptedPassword": encrypted_pwd,
                    "isActive": True,
                },
            },
        )

    @staticmethod
    async def get_decrypted_credentials(account_id: str) -> Optional[Tuple[str, str]]:
        """
        Retrieves account and returns (student_id, raw_password).
        Decrypted password remains in ephemeral stack memory only.
        """
        account = await db.vulmsaccount.find_unique(where={"id": account_id})
        if not account or not account.isActive:
            return None

        # Decrypt password on the fly for worker usage
        raw_password = vault.decrypt(account.encryptedPassword)
        return account.studentId, raw_password
