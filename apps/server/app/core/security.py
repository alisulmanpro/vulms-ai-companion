import base64
import os
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings

logger = logging.getLogger("VULMS_Server")


class CryptographicVault:
    """AES-256-GCM Envelope Encryption Primitive for Sensitive At-Rest Data."""

    def __init__(self, raw_key_b64: str | None = None):
        key_str = raw_key_b64 or settings.VULMS_ENCRYPTION_KEY
        if not key_str:
            logger.warning(
                "VULMS_ENCRYPTION_KEY is missing in environment. Using a temporary dev key. "
                "Set VULMS_ENCRYPTION_KEY in .env for production!"
            )
            # Dev fallback: 32 bytes key base64 encoded
            key_str = base64.b64encode(b"0" * 32).decode("utf-8")

        try:
            self.key = base64.b64decode(key_str)
            if len(self.key) != 32:
                # If key length is not 32, derive/pad or raise
                self.key = self.key.ljust(32, b"\x00")[:32]
        except Exception:
            self.key = b"0" * 32

        self.cipher = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypts string using AES-256-GCM.
        Returns base64-encoded string containing [12-byte Nonce + Ciphertext + 16-byte Tag].
        """
        if not plaintext:
            return ""

        nonce = os.urandom(12)
        ciphertext = self.cipher.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
        encrypted_payload = nonce + ciphertext
        return base64.b64encode(encrypted_payload).decode("utf-8")

    def decrypt(self, encrypted_b64: str) -> str:
        """
        Decrypts base64-encoded GCM payload.
        Raises ValueError if payload is tampered or invalid key.
        """
        if not encrypted_b64:
            return ""

        try:
            raw_payload = base64.b64decode(encrypted_b64.encode("utf-8"))
            if len(raw_payload) < 28:
                raise ValueError("Payload too short for valid AES-GCM ciphertext.")

            nonce = raw_payload[:12]
            ciphertext = raw_payload[12:]

            decrypted_bytes = self.cipher.decrypt(nonce, ciphertext, associated_data=None)
            return decrypted_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError("Decryption failed: Ciphertext corrupted or invalid encryption key.") from exc


# Global Singleton Instance
vault = CryptographicVault()
