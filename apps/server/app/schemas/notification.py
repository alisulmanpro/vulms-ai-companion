import re
from pydantic import BaseModel, Field, field_validator


def sanitize_phone_number(phone: str) -> str:
    """Clean and convert Pakistani numbers to standard 92XXXXXXXXXX format."""
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("03"):
        digits = "92" + digits[1:]
    elif digits.startswith("3") and len(digits) == 10:
        digits = "92" + digits

    return digits


class NotificationCreateSchema(BaseModel):
    phoneNumber: str = Field(..., json_schema_extra={"example": "03001234567"}, description="Recipient phone number")
    messageBody: str = Field(..., json_schema_extra={"example": "Your VULMS assignment deadline is tomorrow!"},
                             description="Message text")

    @field_validator("phoneNumber")
    @classmethod
    def validate_and_clean_phone(cls, v: str) -> str:
        cleaned = sanitize_phone_number(v)
        if len(cleaned) < 10 or len(cleaned) > 12:
            raise ValueError("Invalid phone number format")
        return cleaned


class BulkNotificationSchema(BaseModel):
    phoneNumbers: list[str]
    messageBody: str
