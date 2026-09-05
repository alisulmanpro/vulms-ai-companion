import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.vulms_types import (
    LoginPayload,
    AutoLoginResponse,
    ActiveStatusPayload,
    ActiveStatusResponse,
)
from app.services.vulms_watcher.vulms_auto_login import async_playwright_login
from app.services.credential_service import VulmsCredentialService

logger = logging.getLogger("VULMS_AuthAPI")

router = APIRouter(prefix="/vulms-watcher", tags=["VULMS Watcher Auth"])


@router.post("/auto-login", response_model=AutoLoginResponse)
async def auto_login_vulms(payload: LoginPayload):
    """
    Triggers automated login using Playwright to acquire session cookies.
    """
    try:
        response = await async_playwright_login(
            student_id=payload.student_id,
            password=payload.password
        )

        if not response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Auto-login failed: {response.get('error')}"
            )

        # Mark user active upon successful login
        await VulmsCredentialService.set_user_active_status(
            student_id=payload.student_id,
            is_active=True
        )

        return AutoLoginResponse(
            success=True,
            asp_session_id=response.get("asp_session_id", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"Auto-login exception for {payload.student_id}: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-login internal error: {error_msg}"
        )


@router.post("/active-status", response_model=ActiveStatusResponse)
async def update_user_active_status(payload: ActiveStatusPayload):
    """
    Heartbeat / status endpoint called by extension or web frontend.
    - is_active=True: Marks user active (browser open), halts server tracing, and purges pending notifications.
    - is_active=False: Marks user inactive (browser closed), allowing server to resume tracing.
    """
    try:
        updated = await VulmsCredentialService.set_user_active_status(
            student_id=payload.student_id,
            is_active=payload.is_active
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student record for '{payload.student_id}' not found."
            )
        msg = "User marked active (browser open). Tracing halted & pending queued notifications purged." if payload.is_active else "User marked inactive (browser closed). Server tracing enabled."
        return ActiveStatusResponse(
            success=True,
            message=msg,
            is_active=payload.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Active status update error for {payload.student_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Active status update error: {str(e)}"
        )

