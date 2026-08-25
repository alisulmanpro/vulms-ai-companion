import re
from datetime import datetime
from typing import Optional, List
from bs4 import BeautifulSoup
import httpx

from app.schemas.vulms_types import AccountSummaryResponse, ChallanItem

BASE_URL = "https://vulms.vu.edu.pk"
ACCOUNT_BOOK_URL = f"{BASE_URL}/AccountBook/AccountBook.aspx"


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parses VU LMS date formats into date objects."""
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


async def parse_account_summary(asp_session_id: str) -> Optional[AccountSummaryResponse]:
    cookies = {
        "ASP.NET_SessionId": asp_session_id
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html"
    }

    async with httpx.AsyncClient(cookies=cookies, headers=headers, timeout=20.0) as client:
        # Step 1: Fetch Account Book Page
        res = await client.get(ACCOUNT_BOOK_URL)
        if res.status_code != 200:
            raise Exception(f"Account Book request failed with status {res.status_code}")

        soup = BeautifulSoup(res.text, "html.parser")

        # Step 2: Validate grid presence
        account_grid = soup.select_one('[id*="grdaccountbook"]')
        if not account_grid:
            raise Exception("Account grid not found or session expired")

        challans: List[ChallanItem] = []
        panels = soup.select('[id^="MainContent_grdaccountbook_pnl_"]')

        # Step 3: Parse Challan panels
        for pnl in panels:
            pnl_id = pnl.get("id", "")
            id_suffix = pnl_id.split("_")[-1] if pnl_id else ""
            if not id_suffix:
                continue

            # Paid Date Check
            paid_date_el = pnl.select_one(f"#MainContent_grdaccountbook_lblpaiddate_{id_suffix}")
            paid_date_text = paid_date_el.get_text(strip=True) if paid_date_el else ""

            # Filter only "UnPaid" challans
            if paid_date_text.lower() != "unpaid":
                continue

            # Challan Number
            challan_no_el = pnl.select_one(f"#MainContent_grdaccountbook_lbl_{id_suffix}")
            if not challan_no_el:
                continue
            challan_no = challan_no_el.get_text(strip=True)

            # Payable Amount
            payable_amount_el = pnl.select_one(f"#MainContent_grdaccountbook_lblPayableAmount_{id_suffix}")
            payable_amount_str = payable_amount_el.get_text(strip=True) if payable_amount_el else "0"

            try:
                payable_fee = int(payable_amount_str)
            except ValueError:
                payable_fee = 0

            # Due Date
            due_date_el = pnl.select_one(f"#MainContent_grdaccountbook_lblduedate_{id_suffix}")
            due_date_text = due_date_el.get_text(strip=True) if due_date_el else ""

            # Late Fee Calculation (+200 PKR if current date > due date)
            extra_charges = 0
            parsed_due_date = parse_date(due_date_text)

            if parsed_due_date and datetime.now().date() > parsed_due_date:
                payable_fee += 200
                extra_charges = 200

            # Dynamic Print URL Extraction via regex matching on onclick attribute
            print_url = f"{BASE_URL}/AccountBook/PrintChallan.aspx?ChallanNo={challan_no}"
            print_btn = pnl.select_one(f"#MainContent_grdaccountbook_hlPrint_{id_suffix}")

            if print_btn:
                onclick_attr = print_btn.get("onclick", "")
                url_match = re.search(r"['\"](ChallanPrintPreview\.aspx\?[^'\"]+)['\"]", onclick_attr)
                if url_match:
                    print_url = f"{BASE_URL}/AccountBook/{url_match.group(1)}"

            challans.append(
                ChallanItem(
                    challan_no=challan_no,
                    original_payable_fee=payable_fee - extra_charges,
                    late_fee_applied=extra_charges > 0,
                    payable_fee=payable_fee,
                    due_date=due_date_text,
                    paid_date=paid_date_text,
                    print_url=print_url
                )
            )

        grand_total_fees = sum(item.payable_fee for item in challans)

        return AccountSummaryResponse(
            success=True,
            total_fees=grand_total_fees,
            total_unpaid_challans=len(challans),
            challans_list=challans,
            page_url=ACCOUNT_BOOK_URL
        )
