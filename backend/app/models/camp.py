from sqlalchemy import Column, String, Text, Date, Integer, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class Camp(BaseModel, TenantMixin):
    """A short-term camp (e.g. Spring Camp, Summer Camp)"""

    __tablename__ = "camps"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    capacity = Column(Integer, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    enrollments = relationship("CampEnrollment", back_populates="camp", cascade="all, delete-orphan")
