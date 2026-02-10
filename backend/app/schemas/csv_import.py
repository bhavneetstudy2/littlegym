from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class CSVPreviewResponse(BaseModel):
    """Response for CSV preview endpoint"""
    headers: List[str]
    sample_rows: List[Dict[str, str]]
    total_rows: int


class ImportError(BaseModel):
    """Single import error with row reference"""
    row: int
    message: str


class ImportResult(BaseModel):
    """Result summary for any CSV import operation"""
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[ImportError] = []


class LeadsColumnMapping(BaseModel):
    """Column mapping for leads CSV import"""
    child_first_name: str
    child_last_name: Optional[str] = None
    child_dob: Optional[str] = None
    child_school: Optional[str] = None
    parent_name: str
    parent_phone: str
    parent_email: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class EnrollmentsColumnMapping(BaseModel):
    """Column mapping for enrollments CSV import"""
    child_name: Optional[str] = None
    enquiry_id: Optional[str] = None
    plan_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    batch_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AttendanceColumnMapping(BaseModel):
    """Column mapping for attendance CSV import"""
    child_name: Optional[str] = None
    enquiry_id: Optional[str] = None
    session_date: str
    status: str
    batch_name: Optional[str] = None


class ProgressColumnMapping(BaseModel):
    """Column mapping for skill progress CSV import"""
    child_name: Optional[str] = None
    enquiry_id: Optional[str] = None
    skill_name: str
    level: str
    notes: Optional[str] = None
