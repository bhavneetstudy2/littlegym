from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.utils.enums import MeasurementType


class ActivityCategory(BaseModel):
    """Activity category within a curriculum (e.g., Cartwheel, Push-ups)"""

    __tablename__ = "activity_categories"

    curriculum_id = Column(Integer, ForeignKey("curricula.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category_group = Column(String(100), nullable=True)  # e.g., "Floor Skills", "Beam Skills", "Strength"
    measurement_type = Column(
        SQLEnum(MeasurementType), default=MeasurementType.LEVEL, nullable=False
    )
    measurement_unit = Column(String(50), nullable=True)  # e.g., "reps", "seconds", "cm"
    display_order = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    curriculum = relationship("Curriculum", back_populates="activity_categories")
    progression_levels = relationship(
        "ProgressionLevel",
        back_populates="activity_category",
        cascade="all, delete-orphan",
        order_by="ProgressionLevel.level_number",
    )
