from sqlalchemy import Column, Integer, Date, Time, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import SessionStatus


class ClassSession(BaseModel, TenantMixin):
    """Individual class session model"""

    __tablename__ = "class_sessions"

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    trainer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False)

    # Relationships
    batch = relationship("Batch", foreign_keys=[batch_id])
    trainer = relationship("User", foreign_keys=[trainer_user_id])
