from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.utils.enums import MeasurementType


# ── Activity Category ──

class ActivityCategoryBase(BaseModel):
    name: str
    category_group: Optional[str] = None
    measurement_type: MeasurementType = MeasurementType.LEVEL
    measurement_unit: Optional[str] = None
    display_order: int = 0
    description: Optional[str] = None


class ActivityCategoryCreate(ActivityCategoryBase):
    curriculum_id: int


class ProgressionLevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_category_id: int
    level_number: int
    name: str
    description: Optional[str] = None


class ActivityCategoryResponse(ActivityCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    curriculum_id: int
    progression_levels: List[ProgressionLevelResponse] = []
    created_at: datetime
    updated_at: datetime


# ── Progression Level ──

class ProgressionLevelCreate(BaseModel):
    activity_category_id: int
    level_number: int
    name: str
    description: Optional[str] = None


# ── Weekly Progress ──

class WeeklyProgressEntry(BaseModel):
    """Single activity entry within a weekly bulk update"""
    activity_category_id: int
    progression_level_id: Optional[int] = None  # For LEVEL type
    numeric_value: Optional[Decimal] = None      # For COUNT/TIME/MEASUREMENT
    notes: Optional[str] = None


class WeeklyProgressBulkUpdate(BaseModel):
    """Bulk update: one child, one week, multiple activities"""
    child_id: int
    enrollment_id: Optional[int] = None
    week_number: int
    week_start_date: date
    entries: List[WeeklyProgressEntry]


class WeeklyProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    child_id: int
    enrollment_id: Optional[int] = None
    activity_category_id: int
    week_number: int
    week_start_date: date
    progression_level_id: Optional[int] = None
    numeric_value: Optional[Decimal] = None
    notes: Optional[str] = None
    updated_by_user_id: Optional[int] = None
    last_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WeeklyProgressWithDetails(WeeklyProgressResponse):
    model_config = ConfigDict(from_attributes=True)

    activity_category: Optional[ActivityCategoryResponse] = None
    progression_level: Optional[ProgressionLevelResponse] = None


class WeeklyProgressWeekSummary(BaseModel):
    """Summary of a single week's progress"""
    week_number: int
    week_start_date: date
    total_activities: int
    completed_activities: int  # has a value set


# ── Child Trainer Notes ──

class ChildTrainerNotesCreate(BaseModel):
    child_id: int
    enrollment_id: Optional[int] = None
    parent_expectation: Optional[str] = None
    progress_check: Optional[str] = None


class ChildTrainerNotesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    child_id: int
    enrollment_id: Optional[int] = None
    parent_expectation: Optional[str] = None
    progress_check: Optional[str] = None
    updated_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Batch Student Progress Summary ──

class BatchStudentProgressSummary(BaseModel):
    child_id: int
    child_name: str
    enrollment_id: Optional[int] = None
    enrollment_start_date: Optional[date] = None
    current_week: int
    latest_recorded_week: Optional[int] = None
    total_activities: int
    completed_activities: int  # how many activities have values in the latest week
