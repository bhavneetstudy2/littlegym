from sqlalchemy import Column, String, Text, Integer, Enum as SQLEnum, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import LeadStatus, LeadSource


class Lead(BaseModel, TenantMixin):
    """Lead/Prospect model with full lifecycle tracking"""

    __tablename__ = "leads"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.ENQUIRY_RECEIVED, nullable=False, index=True)
    source = Column(SQLEnum(LeadSource), nullable=True)

    # Discovery form fields
    school = Column(String(200), nullable=True)
    preferred_schedule = Column(Text, nullable=True)  # Days/timings preference
    parent_expectations = Column(JSON, nullable=True)  # Array of expectations
    discovery_notes = Column(Text, nullable=True)
    discovery_completed_at = Column(Date, nullable=True)

    # Closure tracking
    closed_reason = Column(String(500), nullable=True)
    closed_at = Column(Date, nullable=True)

    # Conversion tracking
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=True)
    converted_at = Column(Date, nullable=True)

    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    child = relationship("Child", back_populates="leads")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    intro_visits = relationship("IntroVisit", back_populates="lead", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan", order_by="LeadActivity.performed_at.desc()")
    enrollment = relationship("Enrollment", foreign_keys=[enrollment_id], post_update=True)
