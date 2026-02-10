from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import FollowUpStatus, FollowUpOutcome


class FollowUp(BaseModel, TenantMixin):
    """Follow-up activity for leads"""

    __tablename__ = "follow_ups"

    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    scheduled_date = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(FollowUpStatus), default=FollowUpStatus.PENDING, nullable=False)
    outcome = Column(SQLEnum(FollowUpOutcome), nullable=True)
    notes = Column(Text, nullable=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="follow_ups")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
