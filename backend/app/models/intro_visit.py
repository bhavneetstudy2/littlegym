from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import IVOutcome


class IntroVisit(BaseModel, TenantMixin):
    """Introductory visit/trial class model"""

    __tablename__ = "intro_visits"

    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    attended_at = Column(DateTime, nullable=True)
    trainer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    outcome = Column(SQLEnum(IVOutcome), nullable=True)
    outcome_notes = Column(Text, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="intro_visits")
    trainer = relationship("User", foreign_keys=[trainer_user_id])
    batch = relationship("Batch", foreign_keys=[batch_id])
