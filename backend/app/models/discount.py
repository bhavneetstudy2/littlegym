from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import DiscountType


class Discount(BaseModel, TenantMixin):
    """Discount tracking model"""

    __tablename__ = "discounts"

    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False, index=True)
    type = Column(SQLEnum(DiscountType), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(500), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    applied_at = Column(DateTime, nullable=False)

    # Relationships
    enrollment = relationship("Enrollment", back_populates="discounts")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
