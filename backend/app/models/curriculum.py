from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Curriculum(BaseModel):
    """Curriculum template model - can be global or center-specific"""

    __tablename__ = "curricula"

    name = Column(String(255), nullable=False, index=True)
    level = Column(String(50), nullable=True)  # e.g., "Level 1", "Beginner", "Advanced"
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    center_id = Column(Integer, ForeignKey("centers.id"), nullable=True)  # Null = global curriculum
    is_global = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    skills = relationship("Skill", back_populates="curriculum", cascade="all, delete-orphan")
    center = relationship("Center", foreign_keys=[center_id])
