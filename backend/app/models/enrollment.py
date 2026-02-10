from sqlalchemy import Column, Integer, Date, JSON, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import PlanType, EnrollmentStatus


class Enrollment(BaseModel, TenantMixin):
    """Student enrollment model"""

    __tablename__ = "enrollments"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    visits_included = Column(Integer, nullable=True)  # For visit-based plans
    visits_used = Column(Integer, default=0, nullable=False)
    days_selected = Column(JSON, nullable=True)  # e.g., ["Mon", "Wed", "Fri"]
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    # Relationships
    child = relationship("Child", back_populates="enrollments")
    batch = relationship("Batch", back_populates="enrollments")
    payments = relationship("Payment", back_populates="enrollment")
    discounts = relationship("Discount", back_populates="enrollment")
    attendances = relationship("Attendance", back_populates="enrollment")
