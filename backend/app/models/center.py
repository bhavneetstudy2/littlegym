from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Center(BaseModel):
    """Center/Gym location model"""

    __tablename__ = "centers"

    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata")
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)

    # Relationships (will be added as we create more models)
    users = relationship("User", back_populates="center", foreign_keys="User.center_id")
