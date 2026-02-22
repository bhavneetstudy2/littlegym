from datetime import datetime, date, time
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.utils.enums import PlanType, EnrollmentStatus, PaymentMethod, DiscountType


# Batch schemas
class BatchBase(BaseModel):
    name: str
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    days_of_week: Optional[List[str]] = None  # ["Mon", "Wed", "Fri"]
    start_time: Optional[time] = None  # Python time object
    end_time: Optional[time] = None
    capacity: Optional[int] = None
    active: bool = True


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    days_of_week: Optional[List[str]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    capacity: Optional[int] = None
    active: Optional[bool] = None


class BatchResponse(BatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    created_at: datetime
    updated_at: datetime


# Discount schemas
class DiscountCreate(BaseModel):
    type: DiscountType
    value: Decimal
    reason: Optional[str] = None


class DiscountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    enrollment_id: int
    type: DiscountType
    value: Decimal
    reason: Optional[str] = None
    approved_by_user_id: Optional[int] = None
    applied_at: datetime
    created_at: datetime


# Payment schemas
class PaymentCreate(BaseModel):
    amount: Decimal
    method: PaymentMethod
    reference: Optional[str] = None
    paid_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    enrollment_id: int
    amount: Decimal
    currency: str
    method: PaymentMethod
    reference: Optional[str] = None
    paid_at: datetime
    discount_total: Optional[Decimal] = None
    net_amount: Decimal
    created_at: datetime


# Enrollment schemas
class EnrollmentBase(BaseModel):
    child_id: int
    batch_id: Optional[int] = None
    plan_type: PlanType
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    visits_included: Optional[int] = None
    days_selected: Optional[List[str]] = None  # ["Mon", "Wed", "Fri"]
    notes: Optional[str] = None


class EnrollmentCreate(EnrollmentBase):
    # Payment information
    payment: PaymentCreate
    # Optional discount
    discount: Optional[DiscountCreate] = None


class EnrollmentUpdate(BaseModel):
    batch_id: Optional[int] = None
    status: Optional[EnrollmentStatus] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class EnrollmentResponse(EnrollmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    visits_used: int
    status: EnrollmentStatus
    created_at: datetime
    updated_at: datetime


class EnrollmentDetailResponse(EnrollmentResponse):
    model_config = ConfigDict(from_attributes=True)

    payments: List[PaymentResponse]
    discounts: List[DiscountResponse]


# Child info for enrolled student response
class ChildInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enquiry_id: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    dob: Optional[date] = None
    age_years: Optional[int] = None
    school: Optional[str] = None
    interests: Optional[List[str]] = None
    notes: Optional[str] = None


class ParentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    email: Optional[str] = None
    relationship_type: Optional[str] = None
    is_primary_contact: bool = False


class BatchInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    days_of_week: Optional[List[str]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class EnrolledStudentResponse(BaseModel):
    """Complete enrolled student response with all details"""
    model_config = ConfigDict(from_attributes=True)

    # Enrollment info
    enrollment_id: int
    plan_type: PlanType
    status: EnrollmentStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    visits_included: Optional[int] = None
    visits_used: int = 0
    days_selected: Optional[List[str]] = None
    enrollment_notes: Optional[str] = None
    enrolled_at: datetime

    # Child info
    child: ChildInfo

    # Parent info
    parents: List[ParentInfo] = []

    # Batch info (optional)
    batch: Optional[BatchInfo] = None

    # Payment summary
    total_paid: Decimal
    total_discount: Decimal


# Master Students schemas
class MasterStudentResponse(BaseModel):
    """Child-centric view: one row per child with aggregated enrollment data"""
    # Child info
    child: ChildInfo
    parents: List[ParentInfo] = []

    # Enrollment summary
    enrollment_count: int
    is_renewal: bool  # enrollment_count > 1

    # Latest enrollment details
    latest_enrollment_id: int
    latest_plan_type: str
    latest_status: str
    latest_start_date: Optional[date] = None
    latest_end_date: Optional[date] = None
    latest_visits_included: Optional[int] = None
    latest_visits_used: int = 0
    latest_batch: Optional[BatchInfo] = None
    latest_enrolled_at: Optional[datetime] = None

    # Aggregates
    total_paid: float = 0
    lead_source: Optional[str] = None
    converted_at: Optional[date] = None


class MasterStudentsStatsResponse(BaseModel):
    total: int
    new_count: int
    renewal_count: int
    by_status: dict  # { "ACTIVE": N, "EXPIRED": N, ... }
