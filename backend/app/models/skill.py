from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Skill(BaseModel):
    """Individual skill within a curriculum"""

    __tablename__ = "skills"

    curriculum_id = Column(Integer, ForeignKey("curricula.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "Balance", "Strength", "Flexibility"
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    curriculum = relationship("Curriculum", back_populates="skills")
    skill_progress = relationship("SkillProgress", back_populates="skill", cascade="all, delete-orphan")
