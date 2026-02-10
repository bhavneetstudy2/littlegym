from sqlalchemy import Column, String, Date, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class Child(BaseModel, TenantMixin):
    """Child/Student model"""

    __tablename__ = "children"

    enquiry_id = Column(String(50), nullable=True, unique=True, index=True)  # e.g., TLGC0002
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    dob = Column(Date, nullable=True)
    school = Column(String(255), nullable=True)
    interests = Column(JSON, nullable=True)  # Store as JSON array
    notes = Column(Text, nullable=True)

    # Relationships
    family_links = relationship("FamilyLink", back_populates="child")
    leads = relationship("Lead", back_populates="child")
    enrollments = relationship("Enrollment", back_populates="child")
    attendances = relationship("Attendance", back_populates="child")
    skill_progress = relationship("SkillProgress", back_populates="child")
