"""
These classes define the exact shape of data going in and out of the API.
FastAPI uses them to auto-validate requests and auto-generate the API docs at /docs.
"""
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


class DirectiveOut(BaseModel):
    id: str
    raw_description: str
    source_page: Optional[int]
    source_snippet: Optional[str]
    ai_confidence: Optional[str]
    deadline_expression_raw: Optional[str]
    deadline_date_computed: Optional[date]
    suggested_department_id: Optional[str]
    verification_status: str
    rejection_reason: Optional[str]

    class Config:
        from_attributes = True


class CaseOut(BaseModel):
    id: str
    case_number: str
    court_name: Optional[str]
    order_date: Optional[date]
    parties: Optional[Dict]
    status: str
    directives: List[DirectiveOut] = []

    class Config:
        from_attributes = True


class ApproveDirectiveIn(BaseModel):
    pass


class EditApproveDirectiveIn(BaseModel):
    raw_description: Optional[str] = None
    suggested_department_id: Optional[str] = None
    deadline_date_computed: Optional[date] = None


class RejectDirectiveIn(BaseModel):
    reason: str


class ActionOut(BaseModel):
    id: str
    case_id: str
    description: str
    assigned_department_id: Optional[str]
    deadline_date: Optional[date]
    status: str

    class Config:
        from_attributes = True


class ActionStatusUpdateIn(BaseModel):
    status: str  # pending | in_progress | completed
    notes: Optional[str] = None


class LoginIn(BaseModel):
    email: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class SignupIn(BaseModel):
    full_name: str
    email: str
    password: str
    role: str
    department_id: Optional[str] = None
    # Required for any role other than department_officer — see auth.py.
    invite_code: Optional[str] = None


class GoogleAuthIn(BaseModel):
    # The ID token (JWT) returned by Google Identity Services on the frontend.
    credential: str


class UserOut(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    department_id: Optional[str] = None
    auth_provider: str

    class Config:
        from_attributes = True
