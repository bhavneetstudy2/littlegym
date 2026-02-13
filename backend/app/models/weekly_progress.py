from sqlalchemy import (
    Column, Integer, Text, Date, DateTime, Numeric,
    ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class WeeklyProgress(BaseModel, TenantMixin):
    """Weekly progress entry for a child on a specific activity category"""

    __tablename__ = "weekly_progress"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=True, index=True)
    activity_category_id = Column(
        Integer, ForeignKey("activity_categories.id"), nullable=False, index=True
    )
    week_number = Column(Integer, nullable=False)
    week_start_date = Column(Date, nullable=False)

    # For LEVEL measurement type
    progression_level_id = Column(
        Integer, ForeignKey("progression_levels.id"), nullable=True
    )

    # For COUNT/TIME/MEASUREMENT types
    numeric_value = Column(Numeric(10, 2), nullable=True)

    notes = Column(Text, nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_updated_at = Column(DateTime, nullable=True)

    # Relationships
    child = relationship("Child")
    enrollment = relationship("Enrollment")
    activity_category = relationship("ActivityCategory")
    progression_level = relationship("ProgressionLevel")
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])

    __table_args__ = (
        UniqueConstraint(
            "child_id", "activity_category_id", "week_number", "enrollment_id",
            name="uq_weekly_progress_child_activity_week",
        ),
        Index("ix_weekly_progress_child_week", "child_id", "week_number"),
        Index("ix_weekly_progress_activity_week", "activity_category_id", "week_number"),
    )
