"""
LORENZ SaaS - Social Graph Models
Unified contact management across all data sources (email, WhatsApp, LinkedIn, etc.)
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Integer, Float, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class DataSource(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    CALENDAR = "calendar"
    MANUAL = "manual"


class InteractionType(str, enum.Enum):
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    WHATSAPP_MESSAGE = "whatsapp_message"
    CALL = "call"
    MEETING = "meeting"
    LINKEDIN_CONNECTION = "linkedin_connection"
    LINKEDIN_MESSAGE = "linkedin_message"
    TWITTER_MENTION = "twitter_mention"
    TELEGRAM_MESSAGE = "telegram_message"
    OTHER = "other"


class RelationshipType(str, enum.Enum):
    INVESTOR = "investor"
    POTENTIAL_INVESTOR = "potential_investor"
    PARTNER = "partner"
    POTENTIAL_PARTNER = "potential_partner"
    CLIENT = "client"
    POTENTIAL_CLIENT = "potential_client"
    SUPPLIER = "supplier"
    POLITICAL_STAKEHOLDER = "political_stakeholder"
    MEDIA = "media"
    ACADEMIA = "academia"
    TEAM_INTERNAL = "team_internal"
    FAMILY = "family"
    FRIEND = "friend"
    ACQUAINTANCE = "acquaintance"
    OTHER = "other"


class OpportunityType(str, enum.Enum):
    INVESTMENT = "investment"
    PARTNERSHIP = "partnership"
    SALES = "sales"
    MEDIA_COVERAGE = "media_coverage"
    SPEAKING = "speaking"
    ADVISORY = "advisory"
    INTRODUCTION = "introduction"
    FOLLOW_UP = "follow_up"


class UnifiedContact(Base, TimestampMixin):
    """
    Unified Contact - aggregates data from all sources for a single person
    """
    __tablename__ = "unified_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core identity
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), index=True)  # Lowercase, no accents, for matching

    # Primary email (from most frequent interaction)
    primary_email = Column(String(255), index=True)
    all_emails = Column(ARRAY(String), default=list)  # All known emails

    # Phone numbers
    primary_phone = Column(String(50))
    all_phones = Column(ARRAY(String), default=list)

    # Professional info
    company = Column(String(255))
    job_title = Column(String(255))
    industry = Column(String(100))

    # Social profiles
    linkedin_url = Column(String(500))
    linkedin_id = Column(String(100))
    twitter_handle = Column(String(100))
    twitter_id = Column(String(100))
    instagram_handle = Column(String(100))
    facebook_id = Column(String(100))

    # Location
    city = Column(String(100))
    country = Column(String(100))
    timezone = Column(String(50))

    # Profile picture (best quality available)
    avatar_url = Column(String(500))

    # Relationship classification
    relationship_type = Column(SQLEnum(RelationshipType), default=RelationshipType.ACQUAINTANCE)
    relationship_strength = Column(Float, default=0.0)  # 0-1 based on interactions

    # Tags and notes
    tags = Column(ARRAY(String), default=list)
    notes = Column(Text)

    # Interaction stats (aggregated)
    total_interactions = Column(Integer, default=0)
    first_interaction = Column(DateTime(timezone=True))
    last_interaction = Column(DateTime(timezone=True))

    # Per-source interaction counts
    email_interactions = Column(Integer, default=0)
    whatsapp_interactions = Column(Integer, default=0)
    linkedin_interactions = Column(Integer, default=0)
    call_interactions = Column(Integer, default=0)
    meeting_interactions = Column(Integer, default=0)

    # Sentiment analysis
    overall_sentiment = Column(Float)  # -1 to 1

    # Graph positioning (for 3D visualization)
    graph_x = Column(Float, default=0.0)
    graph_y = Column(Float, default=0.0)
    graph_z = Column(Float, default=0.0)
    node_size = Column(Float, default=1.0)  # Based on importance
    node_color = Column(String(7))  # Hex color based on relationship type

    # Metadata from sources
    source_data = Column(JSONB, default=dict)  # Raw data from each source

    # AI analysis
    ai_summary = Column(Text)  # AI-generated summary of relationship
    ai_analyzed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="unified_contacts")
    interactions = relationship("ContactInteraction", back_populates="contact", cascade="all, delete-orphan")
    opportunities = relationship("ContactOpportunity", back_populates="contact", cascade="all, delete-orphan")
    source_links = relationship("ContactSourceLink", back_populates="contact", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UnifiedContact {self.name} ({self.primary_email})>"


class ContactSourceLink(Base, TimestampMixin):
    """
    Links a UnifiedContact to its source records (email contacts, WhatsApp, etc.)
    """
    __tablename__ = "contact_source_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("unified_contacts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Source identification
    source = Column(SQLEnum(DataSource), nullable=False)
    source_id = Column(String(255))  # ID in the source system
    source_email = Column(String(255), index=True)
    source_phone = Column(String(50))

    # Data from this source
    source_name = Column(String(255))
    source_data = Column(JSONB, default=dict)

    # Sync status
    last_synced_at = Column(DateTime(timezone=True))

    contact = relationship("UnifiedContact", back_populates="source_links")


class ContactInteraction(Base, TimestampMixin):
    """
    Individual interaction with a contact
    """
    __tablename__ = "contact_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("unified_contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Interaction details
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)
    source = Column(SQLEnum(DataSource), nullable=False)
    direction = Column(String(10))  # "inbound" or "outbound"

    # Content
    subject = Column(String(500))
    snippet = Column(Text)  # First 500 chars of content
    content_hash = Column(String(64))  # To avoid duplicates

    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Metadata
    source_id = Column(String(255))  # ID in source system
    extra_data = Column(JSONB, default=dict)  # Additional metadata

    # Sentiment
    sentiment_score = Column(Float)  # -1 to 1

    contact = relationship("UnifiedContact", back_populates="interactions")
    user = relationship("User")


class ContactOpportunity(Base, TimestampMixin):
    """
    AI-identified opportunities with contacts
    """
    __tablename__ = "contact_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("unified_contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Opportunity details
    opportunity_type = Column(SQLEnum(OpportunityType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Scoring
    confidence_score = Column(Float, default=0.5)  # 0-1 how confident the AI is
    priority = Column(Integer, default=5)  # 1-10
    potential_value = Column(String(50))  # "Low", "Medium", "High", "Very High"

    # Status
    status = Column(String(50), default="identified")  # identified, reviewing, pursuing, won, lost, dismissed

    # Action items
    suggested_action = Column(Text)
    action_deadline = Column(DateTime(timezone=True))

    # Evidence
    evidence = Column(JSONB, default=list)  # List of interaction IDs that support this opportunity

    # Tracking
    identified_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    actioned_at = Column(DateTime(timezone=True))

    contact = relationship("UnifiedContact", back_populates="opportunities")
    user = relationship("User")


class SocialGraphEdge(Base, TimestampMixin):
    """
    Edges between contacts (for network visualization)
    Represents relationships between contacts (not with the user)
    """
    __tablename__ = "social_graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Connected contacts
    source_contact_id = Column(UUID(as_uuid=True), ForeignKey("unified_contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    target_contact_id = Column(UUID(as_uuid=True), ForeignKey("unified_contacts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Edge properties
    connection_type = Column(String(50))  # "colleague", "same_company", "cc_together", etc.
    weight = Column(Float, default=1.0)  # Strength of connection

    # Evidence
    evidence = Column(JSONB, default=list)  # How we know they're connected

    # Relationships
    source_contact = relationship("UnifiedContact", foreign_keys=[source_contact_id])
    target_contact = relationship("UnifiedContact", foreign_keys=[target_contact_id])
