from sqlalchemy import Column, String, Text, Date, Integer, Numeric, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TenantMixin


class CampEnrollmentStatus(str, enum.Enum):
    ENROLLED = "ENROLLED"
    CANCELLED = "CANCELLED"
    WAITLISTED = "WAITLISTED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIAL = "PARTIAL"


class CampEnrollment(BaseModel, TenantMixin):
    """Enrollment of a child (existing or new) into a camp"""

    __tablename__ = "camp_enrollments"

    camp_id = Column(Integer, ForeignKey("camps.id"), nullable=False, index=True)

    # Existing student path
    is_existing_student = Column(Boolean, nullable=False, default=False)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=True, index=True)

    # New student path (captured inline)
    child_name = Column(String(255), nullable=True)
    child_dob = Column(Date, nullable=True)
    parent_name = Column(String(255), nullable=True)
    parent_phone = Column(String(50), nullable=True)
    parent_email = Column(String(255), nullable=True)

    # Common
    notes = Column(Text, nullable=True)
    status = Column(
        SQLEnum(CampEnrollmentStatus),
        default=CampEnrollmentStatus.ENROLLED,
        nullable=False,
    )
    payment_status = Column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    payment_amount = Column(Numeric(10, 2), nullable=True)
    amount_paid = Column(Numeric(10, 2), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    payment_date = Column(Date, nullable=True)

    # Per-enrollment period (e.g. week 1 of a 3-week camp)
    enrollment_start_date = Column(Date, nullable=True)
    enrollment_end_date = Column(Date, nullable=True)

    camp = relationship("Camp", back_populates="enrollments")
    child = relationship("Child")
