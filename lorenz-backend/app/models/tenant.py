"""
LORENZ SaaS - Tenant Model
"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """
    Tenant model - represents an organization/workspace.
    Each user belongs to a tenant for multi-tenant isolation.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    # Subscription
    plan = Column(String(50), default="free")  # free, pro, business
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)

    # Settings
    settings = Column(JSONB, default=dict)

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.slug}>"
