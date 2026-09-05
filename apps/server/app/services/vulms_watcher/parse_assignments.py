import logging
from datetime import datetime
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import httpx

from app.schemas.vulms_types import AssignmentItem

logger = logging.getLogger("VULMS_Assignments")

BASE_URL = "https://vulms.vu.edu.pk"
HOME_URL = f"{BASE_URL}/Home.aspx"
LIST_VIEW_URL = f"{BASE_URL}/Assignments/StudentAssignmentListView.aspx"


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


def is_assignment_active(due_date_str: str, status: str) -> bool:
    """
    Filtering Rule:
    1. Status must NOT be 'Submitted'.
    2. Due Date must be today or in the future.
    """
    status_lower = status.lower().strip()
    if "submitted" in status_lower and "not submitted" not in status_lower:
        return False

    parsed_date = parse_date(due_date_str)
    if parsed_date and parsed_date < datetime.now().date():
        return False

    return True


async def parse_active_assignments(asp_session_id: str) -> Dict[str, List[AssignmentItem]]:
    """
    Parses active assignments per course for a student session.
    Handles ASP.NET WebForms 302 redirects gracefully on postbacks.
    """
    cookies = {
        "ASP.NET_SessionId": asp_session_id,
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
        # Step 1: Fetch Home Page and extract tokens & courses
        home_res = await client.get(HOME_URL)
        if home_res.status_code not in (200, 302):
            raise Exception(f"Home page request failed with HTTP status {home_res.status_code}")

        soup = BeautifulSoup(home_res.text, "html.parser")

        view_state_el = soup.find("input", {"name": "__VIEWSTATE"})
        vs_gen_el = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        hf_course_el = soup.find("input", {"name": "ctl00$MainContent$hfCourseCode"})

        if not view_state_el:
            raise Exception("Session expired or invalid cookies: __VIEWSTATE not found on VULMS Home page.")

        view_state = view_state_el.get("value", "")
        vs_generator = vs_gen_el.get("value", "") if vs_gen_el else ""
        hf_course_code = hf_course_el.get("value", "") if hf_course_el else ""

        buttons = soup.select('input[type="image"][id^="MainContent_gvCourseList_ibtnAssignments_"]')
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

        result: Dict[str, List[AssignmentItem]] = {}

        # Step 2: Iterate through courses and fetch assignments
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
                f"ctl00$MainContent$gvCourseList${ctl_id}$ibtnAssignments.x": "17",
                f"ctl00$MainContent$gvCourseList${ctl_id}$ibtnAssignments.y": "13",
            }

            # POST postback to switch active course context (302 redirect is expected & followed)
            post_res = await client.post(HOME_URL, data=payload)
            if post_res.status_code not in (200, 302):
                logger.warning(f"Unexpected status {post_res.status_code} during course switch for {code}")

            post_soup = BeautifulSoup(post_res.text, "html.parser")
            new_vs = post_soup.find("input", {"name": "__VIEWSTATE"})
            new_vsg = post_soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            if new_vs and new_vs.get("value"):
                view_state = new_vs.get("value")
            if new_vsg and new_vsg.get("value"):
                vs_generator = new_vsg.get("value")

            # GET assignment list view
            list_res = await client.get(LIST_VIEW_URL)
            if list_res.status_code not in (200, 302):
                logger.warning(f"Failed to fetch assignment list view for course {code}")
                continue

            list_soup = BeautifulSoup(list_res.text, "html.parser")

            panels = list_soup.select('div[id^="MainContent_gvTileRepeaterAssignment_pnl_"]')
            course_active_assignments = []

            for panel in panels:
                def get_text(selector: str) -> str:
                    el = panel.select_one(selector)
                    return el.get_text(strip=True) if el else ""

                title = get_text('span[id*="Label3_"]')
                due_date = get_text('span[id*="lblDueDate_"]')
                total_marks = get_text('span[id*="lblTotalMarks_"]')
                status = get_text('span[id*="lblsubmitted_"]') or get_text('span[id*="lblExpired_"]') or "Not Submitted"
                score = get_text('span[id*="lblScore_"]')

                download_el = panel.select_one('a[id*="lbtnViewSubmittedFile_"]')
                download_url = download_el.get("href", "") if download_el else ""

                comments_el = panel.select_one('a[href*="InstructorComments.aspx"]')
                comments_url = f"{BASE_URL}/Assignments/{comments_el.get('href', '')}" if comments_el else ""

                sr_no_el = panel.select_one(".hideinMobileView.col-xs-9.col-sm-9.col-md-1.rightBorder")
                sr_no = sr_no_el.get_text(strip=True) if sr_no_el else ""

                if is_assignment_active(due_date_str=due_date, status=status):
                    item = AssignmentItem(
                        id=f"{code}_sr{sr_no}",
                        sr_no=sr_no,
                        title=title,
                        due_date=due_date,
                        total_marks=total_marks,
                        status=status,
                        score=score,
                        download_url=download_url,
                        comments_url=comments_url
                    )
                    course_active_assignments.append(item)

            result[code] = course_active_assignments

        return result
