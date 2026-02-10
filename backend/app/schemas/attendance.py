from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.utils.enums import SessionStatus, AttendanceStatus


# ClassSession schemas
class ClassSessionBase(BaseModel):
    batch_id: int
    session_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    trainer_user_id: Optional[int] = None
    status: SessionStatus = SessionStatus.SCHEDULED


class ClassSessionCreate(ClassSessionBase):
    pass


class ClassSessionUpdate(BaseModel):
    trainer_user_id: Optional[int] = None
    status: Optional[SessionStatus] = None


class ClassSessionResponse(ClassSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    created_at: datetime
    updated_at: datetime


# Attendance schemas
class AttendanceBase(BaseModel):
    child_id: int
    status: AttendanceStatus
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    class_session_id: int
    enrollment_id: Optional[int] = None


class AttendanceBulkCreate(BaseModel):
    class_session_id: int
    attendances: List[AttendanceBase]


class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    class_session_id: int
    enrollment_id: Optional[int] = None
    marked_by_user_id: Optional[int] = None
    marked_at: Optional[datetime] = None
    session_date: Optional[date] = None
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None
    visit_warning: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AttendanceWithChild(AttendanceResponse):
    model_config = ConfigDict(from_attributes=True)

    child: dict  # Will include child details


# Batch student with attendance summary
class BatchStudentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    child_id: int
    child_name: str
    enrollment_id: int
    batch_id: int
    batch_name: str
    classes_booked: int
    classes_attended: int
    classes_remaining: int
    last_attendance_date: Optional[date] = None
    enrollment_status: str


class QuickAttendanceCreate(BaseModel):
    batch_id: int
    session_date: date
    attendances: List[AttendanceBase]  # child_id, status, notes
