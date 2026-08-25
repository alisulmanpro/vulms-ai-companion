from fastapi import HTTPException, APIRouter
from app.schemas.vulms_types import LoginPayload, AutoLoginResponse
from app.services.vulms_watcher.vulms_auto_login import async_playwright_login

router = APIRouter(prefix="/vulms-watcher")


@router.post("/auto-login", response_model=AutoLoginResponse)
async def auto_login_vulms(payload: LoginPayload):
    try:
        response = await async_playwright_login(
            student_id=payload.student_id,
            password=payload.password
        )

        return response
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        raise HTTPException(
            status_code=500,
            detail=f"Auto-login failed: {error_msg}"
        )
