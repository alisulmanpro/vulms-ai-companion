import logging
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

from app.schemas.vulms_types import GDBItem

logger = logging.getLogger("VULMS_GDB")

BASE_URL = "https://vulms.vu.edu.pk"
HOME_URL = f"{BASE_URL}/Home.aspx"
GDB_LIST_URL = f"{BASE_URL}/GDB/Default.aspx"


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parses date strings into date objects."""
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


def is_gdb_active(is_open: bool, status: str, due_date_str: str) -> bool:
    """
    Active GDB criteria:
    1. Status label must be 'Open'.
    2. Submission status must NOT be 'Submitted'.
    3. Due date must not be in the past.
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


async def parse_active_gdbs(asp_session_id: str) -> Dict[str, List[GDBItem]]:
    """
    Parses active GDBs per course for a student session.
    Handles ASP.NET WebForms 302 redirects gracefully on postbacks.
    """
    cookies = {
        "ASP.NET_SessionId": asp_session_id
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(
        cookies=cookies,
        headers=headers,
        follow_redirects=True,
        timeout=20.0
    ) as client:
        # Step 1: Scan Home Page
        home_res = await client.get(HOME_URL)
        if home_res.status_code not in (200, 302):
            raise Exception(f"Home page request failed with status {home_res.status_code}")

        soup = BeautifulSoup(home_res.text, "html.parser")

        view_state_el = soup.find("input", {"name": "__VIEWSTATE"})
        vs_gen_el = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        hf_course_el = soup.find("input", {"name": "ctl00$MainContent$hfCourseCode"})

        if not view_state_el:
            raise Exception("Session expired or invalid cookies: __VIEWSTATE not found on VULMS Home page.")

        view_state = view_state_el.get("value", "")
        vs_generator = vs_gen_el.get("value", "") if vs_gen_el else ""
        hf_course_code = hf_course_el.get("value", "") if hf_course_el else ""

        buttons = soup.select('input[type="image"][id^="MainContent_gvCourseList_ibtnGDB_"]')
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

        result: Dict[str, List[GDBItem]] = {}

        # Step 3: Fetch GDB Data per Course
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
                f"ctl00$MainContent$gvCourseList${ctl_id}$ibtnGDB.x": "6",
                f"ctl00$MainContent$gvCourseList${ctl_id}$ibtnGDB.y": "21",
            }

            post_res = await client.post(HOME_URL, data=payload)
            if post_res.status_code not in (200, 302):
                logger.warning(f"Unexpected status {post_res.status_code} during GDB course switch for {code}")

            post_soup = BeautifulSoup(post_res.text, "html.parser")
            new_vs = post_soup.find("input", {"name": "__VIEWSTATE"})
            new_vsg = post_soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            if new_vs and new_vs.get("value"):
                view_state = new_vs.get("value")
            if new_vsg and new_vsg.get("value"):
                vs_generator = new_vsg.get("value")

            # GET GDB List Page
            list_res = await client.get(GDB_LIST_URL)
            if list_res.status_code not in (200, 302):
                logger.warning(f"Failed to fetch GDB list view for course {code}")
                continue

            list_soup = BeautifulSoup(list_res.text, "html.parser")

            panels = list_soup.select('div[id^="MainContent_gvTileRepeaterGDB_pnl_"]')
            course_active_gdbs = []

            for panel in panels:
                def get_text(selector: str) -> str:
                    el = panel.select_one(selector)
                    return el.get_text(strip=True) if el else ""

                question = get_text('span[id*="lblTitle_"]')
                due_date = get_text('span[id*="Label3_"]')
                start_date = get_text('span[id*="Label4_"]')
                total_marks = get_text('span[id*="Label9_"]')

                status_el = panel.select_one('span[id*="lblSubmissionStatus_"] > span:first-child')
                status = status_el.get_text(strip=True) if status_el else "Not Submitted"

                score = get_text('span[id*="lblMarksObtained_"]')

                open_status_str = get_text('span[id*="lblStatus_"]').lower()
                is_open = open_status_str == "open"

                view_el = panel.select_one('a[id*="lbtnView_"]')
                view_url = f"{BASE_URL}/GDB/{view_el.get('href', '')}" if view_el and view_el.get("href") else ""

                sr_no_el = panel.select_one(".hideinMobileView.col-xs-9.col-sm-9.col-md-1.rightBorder")
                sr_no = sr_no_el.get_text(strip=True) if sr_no_el else ""

                if is_gdb_active(is_open=is_open, status=status, due_date_str=due_date):
                    item = GDBItem(
                        id=f"{code}_sr{sr_no}",
                        sr_no=sr_no,
                        question=question,
                        start_date=start_date,
                        due_date=due_date,
                        total_marks=total_marks,
                        status=status,
                        score=score,
                        is_open=is_open,
                        view_url=view_url
                    )
                    course_active_gdbs.append(item)

            result[code] = course_active_gdbs

        return result
