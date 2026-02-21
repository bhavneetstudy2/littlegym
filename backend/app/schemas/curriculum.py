from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.utils.enums import SkillLevel


# Curriculum schemas
class CurriculumBase(BaseModel):
    name: str
    level: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    description: Optional[str] = None
    is_global: bool = False
    active: bool = True
    curriculum_type: str = "GYMNASTICS"


class CurriculumCreate(CurriculumBase):
    pass


class CurriculumUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class CurriculumResponse(CurriculumBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Skill schemas
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0


class SkillCreate(SkillBase):
    curriculum_id: int


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class SkillResponse(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    curriculum_id: int
    created_at: datetime
    updated_at: datetime


class CurriculumWithSkills(CurriculumResponse):
    model_config = ConfigDict(from_attributes=True)

    skills: List[SkillResponse] = []


# SkillProgress schemas
class SkillProgressBase(BaseModel):
    skill_id: int
    level: SkillLevel
    notes: Optional[str] = None


class SkillProgressCreate(SkillProgressBase):
    child_id: int


class SkillProgressBulkUpdate(BaseModel):
    """Update multiple skills at once for a child"""
    child_id: int
    progress: List[SkillProgressBase]


class SkillProgressUpdate(BaseModel):
    level: Optional[SkillLevel] = None
    notes: Optional[str] = None


class SkillProgressResponse(SkillProgressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    center_id: int
    child_id: int
    last_updated_at: Optional[datetime] = None
    updated_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class SkillProgressWithDetails(SkillProgressResponse):
    model_config = ConfigDict(from_attributes=True)

    skill: SkillResponse
