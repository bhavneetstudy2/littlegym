from sqlalchemy import Column, String, Integer, Time, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class Batch(BaseModel, TenantMixin):
    """Age-based class group model"""

    __tablename__ = "batches"

    name = Column(String(255), nullable=False)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    days_of_week = Column(JSON, nullable=True)  # e.g., ["Mon", "Wed", "Fri"]
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    capacity = Column(Integer, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    center = relationship("Center", back_populates="batches")
    enrollments = relationship("Enrollment", back_populates="batch")
    intro_visits = relationship("IntroVisit", back_populates="batch")
    mappings = relationship("BatchMapping", back_populates="batch", cascade="all, delete-orphan")
