import logging
from typing import Dict, Any
from playwright.async_api import async_playwright

logger = logging.getLogger("VULMS_AutoLogin")

LOGIN_URL = "https://vulms.vu.edu.pk/"


async def async_playwright_login(student_id: str, password: str) -> Dict[str, Any]:
    """
    Automated Playwright chromium login to VULMS to capture ASP.NET_SessionId cookie.
    Guarantees browser process closure via try/finally block to prevent memory leaks.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            logger.info(f"Initiating Playwright auto-login for student ID: {student_id}")
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)

            await page.fill("#txtStudentID", student_id)
            await page.fill("#txtPassword", password)
            await page.click("#ibtnLogin")

            # Wait for successful redirect to Home.aspx (handles 302 redirects)
            await page.wait_for_url("**/Home.aspx**", timeout=25000)

            cookies = await context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            asp_session_id = cookie_dict.get("ASP.NET_SessionId")

            if not asp_session_id:
                return {
                    "success": False,
                    "error": "Login seemed to succeed, but ASP.NET_SessionId cookie was not set."
                }

            logger.info(f"Auto-login successful for {student_id}. Session ID retrieved.")
            return {
                "success": True,
                "asp_session_id": asp_session_id,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Auto-login failed for student {student_id}: {error_msg}")
            return {"success": False, "error": error_msg}

        finally:
            # Guarantees browser closure to prevent process/memory leaks
            await context.close()
            await browser.close()
