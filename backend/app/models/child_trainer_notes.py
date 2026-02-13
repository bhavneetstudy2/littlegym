from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class ChildTrainerNotes(BaseModel, TenantMixin):
    """Trainer notes for a child: parent expectation and progress check"""

    __tablename__ = "child_trainer_notes"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=True, index=True)
    parent_expectation = Column(Text, nullable=True)
    progress_check = Column(Text, nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    child = relationship("Child")
    enrollment = relationship("Enrollment")
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])

    __table_args__ = (
        UniqueConstraint("child_id", "enrollment_id", name="uq_child_trainer_notes"),
    )
