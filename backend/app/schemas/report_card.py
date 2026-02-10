from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


# ReportCard schemas
class ReportCardBase(BaseModel):
    period_start: date
    period_end: date
    summary_notes: Optional[str] = None


class ReportCardCreate(ReportCardBase):
    child_id: int


class ReportCardResponse(ReportCardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    child_id: int
    generated_at: datetime
    generated_by_user_id: Optional[int] = None
    skill_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ReportCardWithChild(ReportCardResponse):
    model_config = ConfigDict(from_attributes=True)

    child: dict  # Will include child details
