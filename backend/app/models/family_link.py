from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class FamilyLink(BaseModel, TenantMixin):
    """Many-to-many relationship between children and parents"""

    __tablename__ = "family_links"

    child_id = Column(Integer, ForeignKey("children.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False, index=True)
    relationship_type = Column(String(50), default="parent")  # mother, father, guardian, other
    is_primary_contact = Column(Boolean, default=False)

    # Relationships
    child = relationship("Child", back_populates="family_links")
    parent = relationship("Parent", back_populates="family_links")
