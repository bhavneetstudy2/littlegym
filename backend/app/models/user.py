from sqlalchemy import Column, String, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.utils.enums import UserRole, UserStatus


class User(BaseModel):
    """User model with role-based access control"""

    __tablename__ = "users"

    center_id = Column(Integer, ForeignKey("centers.id"), nullable=True)  # Nullable for super admin
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)

    # Relationships
    center = relationship("Center", back_populates="users", foreign_keys=[center_id])
