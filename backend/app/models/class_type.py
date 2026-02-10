from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import BaseModel


class ClassType(BaseModel):
    """Global class type definition (Birds, Bugs, Beasts, etc.)"""

    __tablename__ = "class_types"

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    age_min = Column(Integer, nullable=False)
    age_max = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=45, nullable=False)
    active = Column(Boolean, default=True, nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False)
