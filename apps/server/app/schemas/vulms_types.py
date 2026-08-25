from typing import Optional, Dict, List

from pydantic import BaseModel, Field


class LoginPayload(BaseModel):
    student_id: str = Field(..., example="bc240431077")
    password: str = Field(..., example="!r!3[qP::rwe2")


class AuthPayload(BaseModel):
    asp_session_id: str = Field(..., example="aspnet_cookie_value")


class AssignmentItem(BaseModel):
    id: str
    sr_no: str
    title: str
    due_date: str
    total_marks: str
    status: str
    score: str
    download_url: Optional[str] = None
    comments_url: Optional[str] = None


class AutoLoginResponse(BaseModel):
    success: bool
    asp_session_id: str


class ActiveAssignmentResponse(BaseModel):
    success: bool
    total_courses: int
    total_assignments: int
    assignments_by_course: Dict[str, List[AssignmentItem]]


class QuizItem(BaseModel):
    id: str
    sr_no: str
    title: str
    start_date: str
    due_date: str
    total_marks: str
    status: str
    score: str
    is_open: bool


class ActiveQuizzesResponse(BaseModel):
    success: bool
    total_courses: int
    total_quizzes: int
    quizzes_by_course: Dict[str, List[QuizItem]]


class GDBItem(BaseModel):
    id: str
    sr_no: str
    question: str
    start_date: str
    due_date: str
    total_marks: str
    status: str
    score: str
    is_open: bool
    view_url: Optional[str] = None


class ActiveGDBResponse(BaseModel):
    success: bool
    total_courses: int
    total_gdbs: int
    gdbs_by_course: Dict[str, List[GDBItem]]


class ChallanItem(BaseModel):
    challan_no: str
    original_payable_fee: int
    late_fee_applied: bool
    payable_fee: int
    due_date: str
    paid_date: str
    print_url: str


class AccountSummaryResponse(BaseModel):
    success: bool
    total_fees: int
    total_unpaid_challans: int
    challans_list: List[ChallanItem]
    page_url: str
