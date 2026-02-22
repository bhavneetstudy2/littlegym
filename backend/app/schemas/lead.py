from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.utils.enums import LeadStatus, LeadSource


# Parent schemas
class ParentBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None


class ParentCreate(ParentBase):
    pass


class ParentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ParentResponse(ParentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    created_at: datetime
    updated_at: datetime


# Child schemas
class ChildBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    dob: Optional[date] = None
    school: Optional[str] = None
    interests: Optional[List[str]] = None
    notes: Optional[str] = None


class ChildCreate(ChildBase):
    pass


class ChildUpdate(BaseModel):
    enquiry_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    age_years: Optional[int] = None
    school: Optional[str] = None
    interests: Optional[List[str]] = None
    notes: Optional[str] = None


class ChildResponse(ChildBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    age: Optional[int] = None  # Calculated from DOB
    created_at: datetime
    updated_at: datetime


# FamilyLink schemas
class FamilyLinkCreate(BaseModel):
    parent_id: int
    relationship_type: str = "parent"
    is_primary_contact: bool = False


class FamilyLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    parent_id: int
    relationship_type: str
    is_primary_contact: bool
    parent: ParentResponse


# Lead schemas
class LeadBase(BaseModel):
    source: Optional[LeadSource] = None
    discovery_notes: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class LeadCreate(LeadBase):
    # Center ID (required for super admin, optional for others)
    center_id: Optional[int] = None

    # Child information
    child_first_name: str
    child_last_name: Optional[str] = None
    child_dob: Optional[date] = None
    child_age_years: Optional[int] = None
    child_school: Optional[str] = None
    child_interests: Optional[List[str]] = None
    child_notes: Optional[str] = None

    # Parent information (can have multiple parents)
    parents: List[ParentCreate]


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    discovery_notes: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class LeadMarkDead(BaseModel):
    reason: str


class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    child_id: int
    status: LeadStatus
    dead_lead_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Include child data
    child: ChildResponse


class LeadDetailResponse(LeadResponse):
    # Include family links with parent data
    class Config:
        from_attributes = True


# IntroVisit schemas
class IntroVisitBase(BaseModel):
    scheduled_at: datetime
    batch_id: Optional[int] = None
    trainer_user_id: Optional[int] = None
    outcome_notes: Optional[str] = None


class IntroVisitCreate(IntroVisitBase):
    lead_id: int


class IntroVisitMarkAttended(BaseModel):
    attended_at: datetime
    outcome_notes: Optional[str] = None


class IntroVisitResponse(IntroVisitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    lead_id: int
    attended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
