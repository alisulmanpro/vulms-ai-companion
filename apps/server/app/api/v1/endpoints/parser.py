import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.vulms_types import (
    ActiveAssignmentResponse,
    AuthPayload,
    ActiveQuizzesResponse,
    ActiveGDBResponse,
    AccountSummaryResponse
)
from app.services.vulms_watcher.parse_account import parse_account_summary
from app.services.vulms_watcher.parse_assignments import parse_active_assignments
from app.services.vulms_watcher.parse_quizes import parse_active_quizzes
from app.services.vulms_watcher.parser_gdb import parse_active_gdbs

logger = logging.getLogger("VULMS_ParserAPI")

router = APIRouter(prefix="/vulms-watcher-parser", tags=["VULMS Watcher Parser"])


@router.post("/active-assignments", response_model=ActiveAssignmentResponse)
async def get_active_assignments(payload: AuthPayload):
    """Fetches active assignment activities using ASP.NET session ID."""
    try:
        assignments_map = await parse_active_assignments(
            asp_session_id=payload.asp_session_id,
        )

        total_assignments_count = sum(len(items) for items in assignments_map.values())

        return ActiveAssignmentResponse(
            success=True,
            total_courses=len(assignments_map),
            total_assignments=total_assignments_count,
            assignments_by_course=assignments_map
        )
    except Exception as e:
        logger.error(f"Failed to fetch assignments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch assignments: {str(e)}"
        )


@router.post("/active-quiz", response_model=ActiveQuizzesResponse)
async def get_active_quizzes(payload: AuthPayload):
    """Fetches active quiz activities using ASP.NET session ID."""
    try:
        quizzes_map = await parse_active_quizzes(
            asp_session_id=payload.asp_session_id,
        )

        total_quizzes_count = sum(len(items) for items in quizzes_map.values())

        return ActiveQuizzesResponse(
            success=True,
            total_courses=len(quizzes_map),
            total_quizzes=total_quizzes_count,
            quizzes_by_course=quizzes_map
        )
    except Exception as e:
        logger.error(f"Failed to fetch quizzes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch quizzes: {str(e)}"
        )


@router.post("/active-gdbs", response_model=ActiveGDBResponse)
async def get_active_gdbs(payload: AuthPayload):
    """Fetches active Graded Discussion Boards (GDBs) using ASP.NET session ID."""
    try:
        gdbs_map = await parse_active_gdbs(
            asp_session_id=payload.asp_session_id,
        )

        total_gdbs_count = sum(len(items) for items in gdbs_map.values())

        return ActiveGDBResponse(
            success=True,
            total_courses=len(gdbs_map),
            total_gdbs=total_gdbs_count,
            gdbs_by_course=gdbs_map
        )
    except Exception as e:
        logger.error(f"Failed to fetch GDBs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch GDBs: {str(e)}"
        )


@router.post("/account-summary", response_model=AccountSummaryResponse)
async def get_account_summary(payload: AuthPayload):
    """Fetches fee challans and account summary using ASP.NET session ID."""
    try:
        summary = await parse_account_summary(
            asp_session_id=payload.asp_session_id,
        )
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account record found for this session."
            )

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch account summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch account summary: {str(e)}"
        )
