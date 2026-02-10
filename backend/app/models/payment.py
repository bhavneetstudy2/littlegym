from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import PaymentMethod


class Payment(BaseModel, TenantMixin):
    """Payment tracking model"""

    __tablename__ = "payments"

    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    method = Column(SQLEnum(PaymentMethod), nullable=False)
    reference = Column(String(255), nullable=True)  # Transaction ID
    paid_at = Column(DateTime, nullable=False)
    discount_total = Column(Numeric(10, 2), default=0, nullable=True)
    net_amount = Column(Numeric(10, 2), nullable=False)

    # Relationships
    enrollment = relationship("Enrollment", back_populates="payments")
