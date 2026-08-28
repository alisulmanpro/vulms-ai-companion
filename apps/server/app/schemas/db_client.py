from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==========================================
# 1. ENUMS
# ==========================================
class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"


class Role(str, Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


# Base Config for Prisma ORM compatibility
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


# ==========================================
# 2. NOTIFICATION SCHEMAS
# ==========================================
class NotificationBase(BaseSchema):
    phone_number: str = Field(..., alias="phoneNumber")
    message_body: str = Field(..., alias="messageBody")
    status: NotificationStatus = NotificationStatus.PENDING
    evolution_msg_id: Optional[str] = Field(None, alias="evolutionMsgId")
    retry_count: int = Field(0, alias="retryCount")
    error_reason: Optional[str] = Field(None, alias="errorReason")


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    created_at: datetime = Field(..., alias="createdAt")
    sent_at: Optional[datetime] = Field(None, alias="sentAt")


# ==========================================
# 3. VULMS ACCOUNT SCHEMAS
# ==========================================
class VulmsAccountBase(BaseSchema):
    student_id: str = Field(..., alias="studentId")
    asp_session_id: Optional[str] = Field(None, alias="aspSessionId")
    is_browser_open: bool = Field(False, alias="isBrowserOpen")
    is_active: bool = Field(True, alias="isActive")


class VulmsAccountCreate(VulmsAccountBase):
    user_id: str = Field(..., alias="userId")
    password: str


class VulmsAccountResponse(VulmsAccountBase):
    id: str
    user_id: str = Field(..., alias="userId")
    last_synced_at: Optional[datetime] = Field(None, alias="lastSyncedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# ==========================================
# 4. USER SCHEMAS
# ==========================================
class UserBase(BaseSchema):
    name: str
    email: EmailStr
    email_verified: bool = Field(False, alias="emailVerified")
    image: Optional[str] = None
    role: Role = Role.STUDENT


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    vulms_accounts: Optional[List[VulmsAccountResponse]] = Field(default=[], alias="vulmsAccounts")


# ==========================================
# 5. SESSION SCHEMAS
# ==========================================
class SessionSchema(BaseSchema):
    id: str
    user_id: str = Field(..., alias="userId")
    token: str
    expires_at: datetime = Field(..., alias="expiresAt")
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# ==========================================
# 6. ACCOUNT SCHEMAS
# ==========================================
class AccountSchema(BaseSchema):
    id: str
    user_id: str = Field(..., alias="userId")
    account_id: str = Field(..., alias="accountId")
    provider_id: str = Field(..., alias="providerId")
    access_token: Optional[str] = Field(None, alias="accessToken")
    refresh_token: Optional[str] = Field(None, alias="refreshToken")
    id_token: Optional[str] = Field(None, alias="idToken")
    access_token_expires_at: Optional[datetime] = Field(None, alias="accessTokenExpiresAt")
    refresh_token_expires_at: Optional[datetime] = Field(None, alias="refreshTokenExpiresAt")
    scope: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# ==========================================
# 7. VERIFICATION SCHEMAS
# ==========================================
class VerificationSchema(BaseSchema):
    id: str
    identifier: str
    value: str
    expires_at: datetime = Field(..., alias="expiresAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
