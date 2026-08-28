from typing import Dict
from bs4 import BeautifulSoup


class WebFormsStateError(Exception):
    """Raised when critical ASP.NET state tokens are missing from HTML response."""
    pass


def extract_webforms_state(html_content: str) -> Dict[str, str]:
    """
    Parses HTML DOM to extract ASP.NET WebForms state validation tokens.
    Defensively handles missing or altered hidden input structures.
    """
    if not html_content:
        raise WebFormsStateError("Cannot extract ASP.NET state from empty response.")

    soup = BeautifulSoup(html_content, "html.parser")

    viewstate = soup.find("input", {"id": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"id": "__EVENTVALIDATION"})

    if not viewstate or not viewstate.get("value"):
        raise WebFormsStateError(
            "__VIEWSTATE token not found. Session may have expired or VULMS DOM changed."
        )

    state_tokens: Dict[str, str] = {
        "__VIEWSTATE": viewstate.get("value", ""),
    }

    if viewstate_gen and viewstate_gen.get("value"):
        state_tokens["__VIEWSTATEGENERATOR"] = viewstate_gen.get("value", "")

    if event_validation and event_validation.get("value"):
        state_tokens["__EVENTVALIDATION"] = event_validation.get("value", "")

    return state_tokens
