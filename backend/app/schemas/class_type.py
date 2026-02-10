from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClassTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    age_min: int = Field(..., ge=0, le=18)
    age_max: int = Field(..., ge=0, le=18)
    duration_minutes: int = Field(default=45, ge=15, le=180)
    active: bool = True


class ClassTypeCreate(ClassTypeBase):
    pass


class ClassTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    age_min: Optional[int] = Field(None, ge=0, le=18)
    age_max: Optional[int] = Field(None, ge=0, le=18)
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    active: Optional[bool] = None


class ClassTypeResponse(ClassTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
