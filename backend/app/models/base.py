from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declared_attr, declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class AuditMixin(TimestampMixin):
    """Mixin for audit fields (created_by, updated_by)"""

    @declared_attr
    def created_by_id(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=True)


class TenantMixin:
    """Mixin for multi-tenant models (center_id filtering)"""

    @declared_attr
    def center_id(cls):
        return Column(Integer, ForeignKey("centers.id"), nullable=False, index=True)

    is_archived = Column(Boolean, default=False, nullable=False)


class BaseModel(Base, AuditMixin):
    """Base model with ID and audit fields for all models"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
