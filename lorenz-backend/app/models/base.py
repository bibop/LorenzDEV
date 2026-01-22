"""
LORENZ SaaS - Base Model Classes
"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantMixin:
    """Mixin for tenant_id column (for RLS)"""
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
