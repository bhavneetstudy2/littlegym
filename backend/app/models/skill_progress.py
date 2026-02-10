from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import SkillLevel


class SkillProgress(BaseModel, TenantMixin):
    """Track student progress on individual skills"""

    __tablename__ = "skill_progress"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    level = Column(SQLEnum(SkillLevel), default=SkillLevel.NOT_STARTED, nullable=False)
    last_updated_at = Column(DateTime, nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    child = relationship("Child", back_populates="skill_progress")
    skill = relationship("Skill", back_populates="skill_progress")
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])
