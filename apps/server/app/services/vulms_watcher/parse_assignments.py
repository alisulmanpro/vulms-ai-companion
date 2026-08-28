from datetime import datetime
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import httpx

from app.schemas.vulms_types import AssignmentItem

BASE_URL = "https://vulms.vu.edu.pk"
HOME_URL = f"{BASE_URL}/Home.aspx"
LIST_VIEW_URL = f"{BASE_URL}/Assignments/StudentAssignmentListView.aspx"


def parse_date(date_str: str) -> Optional[datetime.date]:
    """
    Parses date strings into date objects.
    Supports formats like 'Apr 30, 2026', '25-Aug-2026', '2026-08-25'.
    """
    if not date_str:
        return None

    # %b %d, %Y handles 'Apr 30, 2026'
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
    1. Due Date must be today or in the future.
    2. Status must NOT be 'Submitted'.
    """
    if "submitted" in status.lower() and "expired" in status.lower() and "not submitted" not in status.lower():
        return False

    parsed_date = parse_date(due_date_str)
    if parsed_date and parsed_date < datetime.now().date():
        return False

    return True


async def parse_active_assignments(asp_session_id: str) -> Dict[str, List[AssignmentItem]]:
    cookies = {
        "ASP.NET_SessionId": asp_session_id,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(cookies=cookies, headers=headers, follow_redirects=True, timeout=20.0) as client:
        # Step 1: Fetch Home Page and extract tokens & courses
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

        # Extract courses matching assignment buttons[cite: 1]
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

            # POST to set active course session[cite: 1]
            post_res = await client.post(HOME_URL, data=payload)
            post_soup = BeautifulSoup(post_res.text, "html.parser")

            # Update ViewState tokens for subsequent request
            new_vs = post_soup.find("input", {"name": "__VIEWSTATE"})
            new_vsg = post_soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            if new_vs and new_vs.get("value"):
                view_state = new_vs.get("value")
            if new_vsg and new_vsg.get("value"):
                vs_generator = new_vsg.get("value")

            # GET assignment list view[cite: 1]
            list_res = await client.get(LIST_VIEW_URL)
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

                # Apply strict filtering criteria
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
