from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BatchMappingBase(BaseModel):
    batch_id: int
    class_type_id: Optional[int] = None
    curriculum_id: Optional[int] = None


class BatchMappingCreate(BatchMappingBase):
    pass


class BatchMappingUpdate(BaseModel):
    class_type_id: Optional[int] = None
    curriculum_id: Optional[int] = None


class BatchMappingResponse(BatchMappingBase):
    id: int
    center_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
