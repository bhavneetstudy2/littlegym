"""
Enhanced lead schemas for complete lifecycle management
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.utils.enums import (
    LeadStatus, LeadSource, IVOutcome,
    FollowUpStatus, FollowUpOutcome
)


# Enquiry Form / Discovery Form
class EnquiryFormCreate(BaseModel):
    """Complete enquiry/discovery form from frontend"""
    # Center
    center_id: Optional[int] = None  # Required for super admin

    # Child information
    child_first_name: str = Field(..., min_length=1, max_length=100)
    child_last_name: Optional[str] = Field(None, max_length=100)
    child_dob: Optional[date] = None
    age: Optional[int] = Field(None, ge=0, le=18)
    gender: Optional[str] = Field(None, pattern="^(Boy|Girl|Other)$")

    # Parent 1 information (required)
    parent_name: str = Field(..., min_length=1, max_length=200)
    contact_number: str = Field(..., pattern=r"^\+?[\d\s\-()]+$")
    email: Optional[str] = None

    # Parent 2 information (optional)
    parent2_name: Optional[str] = Field(None, max_length=200)
    parent2_contact_number: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-()]+$")
    parent2_email: Optional[str] = None

    # Discovery details
    school: Optional[str] = Field(None, max_length=200)
    source: Optional[LeadSource] = None
    parent_expectations: Optional[List[str]] = Field(
        None,
        description="List of expectations: child_development, socialization_skills, physical_activity, etc."
    )
    preferred_schedule: Optional[str] = Field(None, max_length=500)
    remarks: Optional[str] = None

    # Assignment
    assigned_to_user_id: Optional[int] = None


# Discovery Form Update (after initial enquiry)
class DiscoveryFormUpdate(BaseModel):
    school: Optional[str] = None
    preferred_schedule: Optional[str] = None
    parent_expectations: Optional[List[str]] = None
    discovery_notes: Optional[str] = None


# Lead responses
class LeadBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    child_id: int
    status: LeadStatus
    source: Optional[LeadSource]
    created_at: datetime
    updated_at: datetime


class LeadSummary(BaseModel):
    """Summary for list views with essential info"""
    model_config = ConfigDict(from_attributes=True)

    # Core lead info
    id: int
    center_id: int
    child_id: int
    status: LeadStatus
    source: Optional[LeadSource]
    created_at: datetime
    updated_at: datetime

    # Child info for display
    child_name: str
    child_age: Optional[int]
    school: Optional[str]
    enquiry_id: Optional[str]


class LeadDetail(LeadBase):
    """Detailed lead with all related data"""
    # Discovery form
    school: Optional[str]
    preferred_schedule: Optional[str]
    parent_expectations: Optional[List[str]]
    discovery_notes: Optional[str]
    discovery_completed_at: Optional[date]

    # Closure
    closed_reason: Optional[str]
    closed_at: Optional[date]

    # Conversion
    enrollment_id: Optional[int]
    converted_at: Optional[date]

    # Assignment
    assigned_to_user_id: Optional[int]

    # Related entities (populated by service layer)
    child: Optional[dict] = None
    parents: Optional[List[dict]] = None
    intro_visits: Optional[List[dict]] = None
    follow_ups: Optional[List[dict]] = None


# Intro Visit schemas
class IntroVisitCreate(BaseModel):
    lead_id: int
    scheduled_at: datetime
    batch_id: Optional[int] = None
    trainer_user_id: Optional[int] = None


class IntroVisitUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    batch_id: Optional[int] = None
    trainer_user_id: Optional[int] = None
    attended_at: Optional[datetime] = None
    outcome: Optional[IVOutcome] = None
    outcome_notes: Optional[str] = None


class IntroVisitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    scheduled_at: datetime
    attended_at: Optional[datetime]
    batch_id: Optional[int]
    trainer_user_id: Optional[int]
    outcome: Optional[IVOutcome]
    outcome_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# Follow-up schemas
class FollowUpCreate(BaseModel):
    lead_id: int
    scheduled_date: datetime
    notes: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class FollowUpUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[FollowUpStatus] = None
    outcome: Optional[FollowUpOutcome] = None
    notes: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    scheduled_date: datetime
    completed_at: Optional[datetime]
    status: FollowUpStatus
    outcome: Optional[FollowUpOutcome]
    notes: Optional[str]
    assigned_to_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# Lead action schemas
class LeadStatusUpdate(BaseModel):
    status: LeadStatus
    notes: Optional[str] = None


class LeadClose(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class LeadConvert(BaseModel):
    """Data needed to convert lead to enrollment"""
    enrollment_id: int  # The created enrollment ID


# Lead Activity schemas
class LeadActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    activity_type: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by_id: int
    performed_by_name: Optional[str] = None
    performed_at: datetime
    created_at: datetime


# Dashboard/List filters
class LeadFilter(BaseModel):
    status: Optional[List[LeadStatus]] = None
    source: Optional[List[LeadSource]] = None
    assigned_to_user_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    search: Optional[str] = None  # Search in child name, parent name, phone


# Pagination response
class PaginatedLeadsResponse(BaseModel):
    """Paginated response for leads list"""
    leads: List[LeadSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
