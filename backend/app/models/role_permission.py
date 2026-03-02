from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum, UniqueConstraint
from app.models.base import BaseModel, TimestampMixin, Base
from app.utils.enums import UserRole


class RolePermission(Base, TimestampMixin):
    """
    Stores configurable role-based permissions per center.
    SUPER_ADMIN and CENTER_ADMIN always have full access (not stored here).
    Only CENTER_MANAGER, TRAINER, COUNSELOR permissions are configurable.
    """
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(Integer, ForeignKey("centers.id"), nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False)
    permission_key = Column(String(100), nullable=False)
    is_allowed = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('center_id', 'role', 'permission_key', name='uq_center_role_permission'),
    )
