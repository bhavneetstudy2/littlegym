from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProgressionLevel(BaseModel):
    """Named progression level within an activity category (e.g., L1=Monkey Jump for Cartwheel)"""

    __tablename__ = "progression_levels"

    activity_category_id = Column(
        Integer, ForeignKey("activity_categories.id"), nullable=False, index=True
    )
    level_number = Column(Integer, nullable=False)  # 1, 2, 3...
    name = Column(String(255), nullable=False)  # "Monkey Jump", "1,2,3 Cartwheel"
    description = Column(Text, nullable=True)

    # Relationships
    activity_category = relationship("ActivityCategory", back_populates="progression_levels")

    __table_args__ = (
        UniqueConstraint(
            "activity_category_id", "level_number", name="uq_progression_level"
        ),
    )
