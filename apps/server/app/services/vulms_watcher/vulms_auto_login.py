from playwright.async_api import async_playwright

LOGIN_URL = "https://vulms.vu.edu.pk/"


# 1. Core Async Playwright Scraper
async def async_playwright_login(student_id: str, password: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(LOGIN_URL, wait_until="networkidle")

            await page.fill("#txtStudentID", student_id)
            await page.fill("#txtPassword", password)
            await page.click("#ibtnLogin")

            await page.wait_for_url("**/Home.aspx**", timeout=20000)

            cookies = await context.cookies()
            await browser.close()

            cookie_dict = {c['name']: c['value'] for c in cookies}
            return {
                "success": True,
                "asp_session_id": cookie_dict.get("ASP.NET_SessionId"),
            }

        except Exception as e:
            await browser.close()
            return {"success": False, "error": str(e)}

