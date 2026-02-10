from sqlalchemy import Column, Integer, Date, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class ReportCard(BaseModel, TenantMixin):
    """Report card snapshot for a child's progress"""

    __tablename__ = "report_cards"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    generated_at = Column(DateTime, nullable=False)
    generated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    summary_notes = Column(Text, nullable=True)
    skill_snapshot = Column(JSON, nullable=True)  # Frozen snapshot of skills at generation time

    # Relationships
    child = relationship("Child")
    generated_by = relationship("User", foreign_keys=[generated_by_user_id])
