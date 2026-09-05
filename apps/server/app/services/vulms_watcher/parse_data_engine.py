import time
import asyncio
import logging
from typing import Any, Dict, Optional
from app.services.vulms_watcher.parse_assignments import parse_active_assignments
from app.services.vulms_watcher.parse_account import parse_account_summary
from app.services.vulms_watcher.parse_quizes import parse_active_quizzes
from app.services.vulms_watcher.parser_gdb import parse_active_gdbs
from app.services.vulms_watcher.vulms_auto_login import async_playwright_login
from app.core.cache import cache_manager
from prisma.models import VulmsAccount

logger = logging.getLogger("VULMS_ParseEngine")


class ParseDataEngine:
    def __init__(self, db_client: Any):
        """
        :param db_client: Prisma client instance
        """
        self.db = db_client

    async def get_db_user_credentials(self, student_id: str) -> Optional[Dict[str, str]]:
        """Fetch stored session and credentials from database."""
        account: VulmsAccount = await self.db.vulmsaccount.find_first(where={"studentId": student_id})
        if not account:
            return None

        return {
            "student_id": account.studentId,
            "password": account.encryptedPassword,
            "asp_session_id": account.aspSessionId or "",
        }

    async def update_db_cookies(self, student_id: str, asp_session_id: str) -> None:
        """Update fresh cookies in database after successful auto-login."""
        await self.db.vulmsaccount.update_many(
            where={"studentId": student_id},
            data={"aspSessionId": asp_session_id}
        )
        logger.info(f"Updated DB session cookies for {student_id}")

    async def _run_all_parsers(self, asp_session_id: str) -> Dict[str, Any]:
        """
        Executes all 4 scrapers concurrently using asyncio.gather for speed.
        """
        assignments_task = parse_active_assignments(asp_session_id=asp_session_id)
        quizzes_task = parse_active_quizzes(asp_session_id=asp_session_id)
        gdbs_task = parse_active_gdbs(asp_session_id=asp_session_id)
        account_task = parse_account_summary(asp_session_id=asp_session_id)

        assignments_res, quizzes_res, gdbs_res, account_res = await asyncio.gather(
            assignments_task,
            quizzes_task,
            gdbs_task,
            account_task,
            return_exceptions=False
        )

        return {
            "assignments": assignments_res,
            "quizzes": quizzes_res,
            "gdbs": gdbs_res,
            "account": account_res
        }

    async def run(self, student_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Main Engine Method: Speed optimized with caching, concurrent execution,
        and auto-login fallback.
        """
        start_time = time.perf_counter()
        cache_key = f"vulms_parsed_payload:{student_id}"

        # Step 0: Check L1/L2 Cache for speed optimization
        if use_cache:
            cached_payload = cache_manager.get(cache_key)
            if cached_payload:
                logger.info(f"Returning cached VULMS payload for student {student_id}")
                cached_payload["from_cache"] = True
                return cached_payload

        # Step 1: Fetch stored record from Database
        user_record = await self.get_db_user_credentials(student_id)
        if not user_record:
            return {
                "success": False,
                "error": f"User record for student '{student_id}' not found in database.",
                "execution_time_seconds": round(time.perf_counter() - start_time, 3)
            }

        asp_session_id = user_record.get("asp_session_id")
        password = user_record.get("password", "")

        parsed_data = None

        # Step 2: Try parsing with existing session cookies
        if asp_session_id:
            try:
                parsed_data = await self._run_all_parsers(asp_session_id)
            except Exception as e:
                logger.warning(f"Existing session expired for {student_id} ({str(e)}). Retrying auto-login...")
                parsed_data = None

        # Step 3: Auto-login fallback if cookies missing or parsing failed
        if parsed_data is None:
            # Note: Decrypt password before login
            from app.core.security import vault
            raw_password = vault.decrypt(password) if password else ""

            login_result = await async_playwright_login(student_id=student_id, password=raw_password)

            if not login_result.get("success"):
                execution_time = round(time.perf_counter() - start_time, 3)
                return {
                    "success": False,
                    "error": f"Auto-login failed: {login_result.get('error')}",
                    "execution_time_seconds": execution_time
                }

            asp_session_id = login_result.get("asp_session_id")
            await self.update_db_cookies(student_id, asp_session_id)

            try:
                parsed_data = await self._run_all_parsers(asp_session_id)
            except Exception as e:
                execution_time = round(time.perf_counter() - start_time, 3)
                return {
                    "success": False,
                    "error": f"Parsing failed even after auto-login: {str(e)}",
                    "execution_time_seconds": execution_time
                }

        # Step 4: Calculate items summary
        assignments_map = parsed_data.get("assignments", {})
        quizzes_map = parsed_data.get("quizzes", {})
        gdbs_map = parsed_data.get("gdbs", {})
        account_summary = parsed_data.get("account")

        total_assignments = sum(len(items) for items in assignments_map.values())
        total_quizzes = sum(len(items) for items in quizzes_map.values())
        total_gdbs = sum(len(items) for items in gdbs_map.values())
        total_unpaid_challans = account_summary.total_unpaid_challans if account_summary else 0

        total_active_items = total_assignments + total_quizzes + total_gdbs + total_unpaid_challans
        execution_time = round(time.perf_counter() - start_time, 3)

        response_payload = {}
        if total_assignments > 0:
            response_payload["assignments"] = {
                "total": total_assignments,
                "items": {k: [item.dict() if hasattr(item, "dict") else item for item in v] for k, v in assignments_map.items() if len(v) > 0}
            }

        if total_quizzes > 0:
            response_payload["quizzes"] = {
                "total": total_quizzes,
                "items": {k: [item.dict() if hasattr(item, "dict") else item for item in v] for k, v in quizzes_map.items() if len(v) > 0}
            }

        if total_gdbs > 0:
            response_payload["gdbs"] = {
                "total": total_gdbs,
                "items": {k: [item.dict() if hasattr(item, "dict") else item for item in v] for k, v in gdbs_map.items() if len(v) > 0}
            }

        if total_unpaid_challans > 0 and account_summary:
            response_payload["account"] = account_summary.dict() if hasattr(account_summary, "dict") else account_summary

        final_result = {
            "success": True,
            "execution_time_seconds": execution_time,
            "total_active_items": total_active_items,
            "data": response_payload,
            "from_cache": False
        }

        # Cache payload for 10 minutes (600s)
        cache_manager.set(cache_key, final_result, expire_seconds=600)
        return final_result
