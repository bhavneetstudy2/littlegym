from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TenantMixin


class BatchMapping(BaseModel, TenantMixin):
    """Maps batch to class type and curriculum"""

    __tablename__ = "batch_mappings"

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)
    class_type_id = Column(Integer, ForeignKey("class_types.id"), nullable=True)
    curriculum_id = Column(Integer, ForeignKey("curricula.id"), nullable=True)

    # Relationships
    batch = relationship("Batch", back_populates="mappings")
    class_type = relationship("ClassType")
    curriculum = relationship("Curriculum")
