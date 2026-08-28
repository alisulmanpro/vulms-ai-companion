import time
from typing import Any, Dict, Optional
from app.services.vulms_watcher.parse_assignments import parse_active_assignments
from app.services.vulms_watcher.parse_account import parse_account_summary
from app.services.vulms_watcher.parse_quizes import parse_active_quizzes
from app.services.vulms_watcher.parser_gdb import parse_active_gdbs
from app.services.vulms_watcher.vulms_auto_login import async_playwright_login
from prisma.models import VulmsAccount


class ParseDataEngine:
    def __init__(self, db_client: Any):
        """
        :param db_client: Your database instance or session (Prisma / SQLAlchemy)
        """
        self.db = db_client

    async def get_db_user_credentials(self, student_id: str) -> Optional[Dict[str, str]]:
        """
        Fetch stored cookies and credentials from DB table 'vulms_account'.
        """

        account: VulmsAccount = await self.db.vulmsaccount.find_first(where={"studentId": student_id})
        if not account:
            return None

        return {
            "student_id": account.studentId,
            "password": account.encryptedPassword,
            "asp_session_id": account.aspSessionId or "",
        }

    async def update_db_cookies(self, student_id: str, asp_session_id: str) -> None:
        """
        Update fresh cookies in the database after successful auto-login.
        """
        await self.db.vulmsaccount.update_many(
            where={"studentId": student_id},
            data={"aspSessionId": asp_session_id}
        )
        print(f"[Engine] Updated DB cookies for {student_id}")

    async def _run_all_parsers(self, asp_session_id: str) -> Dict[str, Any]:
        """
        Executes all 4 scrapers concurrently using asyncio.gather.
        """
        # Step 1: Parse Active Assignments
        assignments_res = await parse_active_assignments(
            asp_session_id=asp_session_id,
        )

        # Step 2: Parse Active Quizzes
        quizzes_res = await parse_active_quizzes(
            asp_session_id=asp_session_id,
        )

        # Step 3: Parse Active GDBs
        gdbs_res = await parse_active_gdbs(
            asp_session_id=asp_session_id,
        )

        # Step 4: Parse Account Summary (Single GET, no course switching)
        account_res = await parse_account_summary(
            asp_session_id=asp_session_id,
        )

        return {
            "assignments": assignments_res,
            "quizzes": quizzes_res,
            "gdbs": gdbs_res,
            "account": account_res
        }

    async def run(self, student_id: str) -> Dict[str, Any]:
        """
        Main Engine Method: Tracks execution time, validates sessions,
        handles auto-login fallback, and builds output JSON.
        """
        start_time = time.perf_counter()

        # Step 1: Fetch stored record from Database
        user_record = await self.get_db_user_credentials(student_id)
        if not user_record:
            return {
                "success": False,
                "error": "User record not found in database",
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
                print(f"[Engine] Existing session expired/failed ({str(e)}). Retrying with auto-login...")
                parsed_data = None

        # Step 3: Auto-login fallback if cookies missing or parsing failed
        if parsed_data is None:
            login_result = await async_playwright_login(student_id=student_id, password=password)

            if not login_result.get("success"):
                execution_time = round(time.perf_counter() - start_time, 3)
                return {
                    "success": False,
                    "error": f"Auto-login failed: {login_result.get('error')}",
                    "execution_time_seconds": execution_time
                }

            asp_session_id = login_result.get("asp_session_id")

            # Update fresh session cookies in Database
            await self.update_db_cookies(student_id, asp_session_id)

            # Re-run parsers with fresh cookies
            try:
                parsed_data = await self._run_all_parsers(asp_session_id)
            except Exception as e:
                execution_time = round(time.perf_counter() - start_time, 3)
                return {
                    "success": False,
                    "error": f"Parsing failed even after auto-login: {str(e)}",
                    "execution_time_seconds": execution_time
                }

        # Step 4: Calculate total active items count across all categories
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

        # Step 5: If total items across all parsers is 0, return {}
        if total_active_items == 0:
            return {
                "success": True,
                "execution_time_seconds": execution_time,
                "data": {}
            }

        # Step 6: Construct response dictionary containing only categories with items > 0
        response_payload = {}

        if total_assignments > 0:
            response_payload["assignments"] = {
                "total": total_assignments,
                "items": {k: v for k, v in assignments_map.items() if len(v) > 0}
            }

        if total_quizzes > 0:
            response_payload["quizzes"] = {
                "total": total_quizzes,
                "items": {k: v for k, v in quizzes_map.items() if len(v) > 0}
            }

        if total_gdbs > 0:
            response_payload["gdbs"] = {
                "total": total_gdbs,
                "items": {k: v for k, v in gdbs_map.items() if len(v) > 0}
            }

        if total_unpaid_challans > 0 and account_summary:
            response_payload["account"] = account_summary.dict()

        return {
            "success": True,
            "execution_time_seconds": execution_time,
            "data": response_payload
        }
