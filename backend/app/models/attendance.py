from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin
from app.utils.enums import AttendanceStatus


class Attendance(BaseModel, TenantMixin):
    """Attendance tracking model"""

    __tablename__ = "attendance"

    class_session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=True, index=True)
    status = Column(SQLEnum(AttendanceStatus), nullable=False)
    marked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    marked_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    class_session = relationship("ClassSession", foreign_keys=[class_session_id])
    child = relationship("Child", back_populates="attendances")
    enrollment = relationship("Enrollment", back_populates="attendances")
    marked_by = relationship("User", foreign_keys=[marked_by_user_id])

    @property
    def session_date(self):
        if self.class_session:
            return self.class_session.session_date
        return None

    @property
    def batch_id(self):
        if self.class_session:
            return self.class_session.batch_id
        return None

    @property
    def batch_name(self):
        if self.class_session and self.class_session.batch:
            return self.class_session.batch.name
        return None
