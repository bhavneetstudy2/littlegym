from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CenterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    active: bool = True


class CenterCreate(CenterBase):
    pass


class CenterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None


class CenterResponse(CenterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CenterStatsResponse(BaseModel):
    """Center statistics"""
    center_id: int
    center_name: str
    total_leads: int
    active_enrollments: int
    total_batches: int
    total_users: int
    todays_classes: int = 0
    pending_renewals: int = 0
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True
