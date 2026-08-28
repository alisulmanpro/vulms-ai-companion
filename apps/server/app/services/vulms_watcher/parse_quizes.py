from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

from app.schemas.vulms_types import QuizItem

BASE_URL = "https://vulms.vu.edu.pk"
HOME_URL = f"{BASE_URL}/Home.aspx"
QUIZ_LIST_URL = f"{BASE_URL}/Quiz/QuizList.aspx"


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parses VU LMS date formats such as 'Apr 30, 2026' or '30-Apr-2026'."""
    if not date_str:
        return None

    date_formats = (
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%b-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d"
    )

    clean_str = date_str.strip()
    for fmt in date_formats:
        try:
            return datetime.strptime(clean_str, fmt).date()
        except ValueError:
            continue

    return None


def is_quiz_active(is_open: bool, status: str, due_date_str: str) -> bool:
    """
    Filtering criteria:
    1. Must be marked as 'Open'.
    2. Must NOT be 'Submitted'.
    3. Due/End date must not be in the past.
    """
    if not is_open:
        return False

    status_lower = status.lower().strip()
    if "submitted" in status_lower and "not submitted" not in status_lower:
        return False

    parsed_due_date = parse_date(due_date_str)
    if parsed_due_date and parsed_due_date < datetime.now().date():
        return False

    return True


async def parse_active_quizzes(asp_session_id: str) -> Dict[str, List[QuizItem]]:
    cookies = {
        "ASP.NET_SessionId": asp_session_id,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(cookies=cookies, headers=headers, follow_redirects=True, timeout=20.0) as client:
        # Step 1: Scan Home Page for ViewState tokens & Courses
        home_res = await client.get(HOME_URL)
        if home_res.status_code != 200:
            raise Exception(f"Home page request failed with status {home_res.status_code}")

        soup = BeautifulSoup(home_res.text, "html.parser")

        view_state_el = soup.find("input", {"name": "__VIEWSTATE"})
        vs_gen_el = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        hf_course_el = soup.find("input", {"name": "ctl00$MainContent$hfCourseCode"})

        if not view_state_el:
            raise Exception("Session expired or invalid cookies: __VIEWSTATE not found")

        view_state = view_state_el.get("value", "")
        vs_generator = vs_gen_el.get("value", "") if vs_gen_el else ""
        hf_course_code = hf_course_el.get("value", "") if hf_course_el else ""

        # Find course buttons matching ibtnQuizzes
        buttons = soup.select('input[type="image"][id^="MainContent_gvCourseList_ibtnQuizzes_"]')
        courses = []

        for btn in buttons:
            btn_id = btn.get("id", "")
            btn_name = btn.get("name", "")
            id_parts = btn_id.split("_")
            name_parts = btn_name.split("$")

            if len(id_parts) > 0 and len(name_parts) >= 4:
                idx_str = id_parts[-1]
                ctl_id = name_parts[3]

                tracking_span = soup.select_one(f"#MainContent_gvCourseList_lblTracking_{idx_str}")
                if tracking_span:
                    parent_h3 = tracking_span.find_parent("h3")
                    title_text = parent_h3.get_text(strip=True) if parent_h3 else ""
                    course_code = title_text.split("-")[0].strip()

                    if course_code:
                        courses.append({"course_code": course_code, "ctl_id": ctl_id})

        result: Dict[str, List[QuizItem]] = {}

        # Step 2: Iterate through courses and fetch quizzes
        for course in courses:
            code = course["course_code"]
            ctl_id = course["ctl_id"]

            payload = {
                "__VIEWSTATE": view_state,
                "__VIEWSTATEGENERATOR": vs_generator,
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "ctl00$MainContent$hfCourseCode": hf_course_code,
                "ctl00$MainContent$hfCurSemester": "",
                "ctl00$MainContent$hfLessonNumber": "",
                f"ctl00$MainContent$gvCourseList${ctl_id}$ibtnQuizzes.x": "13",
                f"ctl00$MainContent$gvCourseList${ctl_id}$ibtnQuizzes.y": "23",
            }

            post_res = await client.post(HOME_URL, data=payload)
            post_soup = BeautifulSoup(post_res.text, "html.parser")

            new_vs = post_soup.find("input", {"name": "__VIEWSTATE"})
            new_vsg = post_soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            if new_vs and new_vs.get("value"):
                view_state = new_vs.get("value")
            if new_vsg and new_vsg.get("value"):
                vs_generator = new_vsg.get("value")

            # GET Quiz List Page
            list_res = await client.get(QUIZ_LIST_URL)
            list_soup = BeautifulSoup(list_res.text, "html.parser")

            panels = list_soup.select('div[id^="MainContent_gvTileRepeaterQuiz_pnl_"]')
            course_active_quizzes = []

            for panel in panels:
                def get_text(selector: str) -> str:
                    el = panel.select_one(selector)
                    return el.get_text(strip=True) if el else ""

                title = get_text('span[id*="lblTitle_"]')
                start_date = get_text('span[id*="lblStartDate_"]')
                due_date = get_text('span[id*="lblEndDate_"]')
                total_marks = get_text('span[id*="lblTotalMarks_"]')

                status_el = panel.select_one('span[id*="lblSubmitted_"] > span:first-child')
                status = status_el.get_text(strip=True) if status_el else "Not Submitted"

                score = get_text('span[id*="lblGetMarks_"]')

                open_status_str = get_text('span[id*="lblStatus_"]').lower()
                is_open = open_status_str == "open"

                sr_no_el = panel.select_one(".hideinMobileView.col-xs-9.col-sm-9.col-md-1.rightBorder")
                sr_no = sr_no_el.get_text(strip=True) if sr_no_el else ""

                if is_quiz_active(is_open=is_open, status=status, due_date_str=due_date):
                    item = QuizItem(
                        id=f"{code}_sr{sr_no}",
                        sr_no=sr_no,
                        title=title,
                        start_date=start_date,
                        due_date=due_date,
                        total_marks=total_marks,
                        status=status,
                        score=score,
                        is_open=is_open
                    )
                    course_active_quizzes.append(item)

            result[code] = course_active_quizzes

        return result