from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class Parent(BaseModel, TenantMixin):
    """Parent/Guardian model"""

    __tablename__ = "parents"

    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    family_links = relationship("FamilyLink", back_populates="parent")
