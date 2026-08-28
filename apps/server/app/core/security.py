import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


class CryptographicVault:
    """AES-256-GCM Envelope Encryption Primitive for Sensitive At-Rest Data."""

    def __init__(self, raw_key_b64: str | None = None):
        key_str = raw_key_b64 or settings.VULMS_ENCRYPTION_KEY
        if not key_str:
            raise ValueError("VULMS_ENCRYPTION_KEY environment variable is missing.")

        # Ensure key decodes to exactly 32 bytes (256 bits)
        self.key = base64.b64decode(key_str)
        if len(self.key) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes (256 bits) after base64 decoding.")

        self.cipher = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypts string using AES-256-GCM.
        Returns base64-encoded string containing [12-byte Nonce + Ciphertext + 16-byte Tag].
        """
        if not plaintext:
            return ""

        # 96-bit (12-byte) nonce recommended for AES-GCM
        nonce = os.urandom(12)
        ciphertext = self.cipher.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)

        # Pack nonce + ciphertext (which includes GCM tag at end)
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
            if len(raw_payload) < 28:  # 12 bytes nonce + 16 bytes min GCM tag
                raise ValueError("Payload too short to be valid AES-GCM ciphertext.")

            nonce = raw_payload[:12]
            ciphertext = raw_payload[12:]

            decrypted_bytes = self.cipher.decrypt(nonce, ciphertext, associated_data=None)
            return decrypted_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError("Decryption failed: Ciphertext corrupted or invalid encryption key.") from exc


# Global Singleton Instance
vault = CryptographicVault()
