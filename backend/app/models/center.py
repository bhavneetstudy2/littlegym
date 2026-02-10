from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Center(BaseModel):
    """Center/Gym location model"""

    __tablename__ = "centers"

    name = Column(String(255), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=True, index=True)  # e.g., "MUM", "CHD", "BLR"
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata")
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    users = relationship("User", back_populates="center", foreign_keys="User.center_id")
    batches = relationship("Batch", back_populates="center")
