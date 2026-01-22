"""
LORENZ SaaS - Twin Database Models
Persistent storage for Human Digital Twin data
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class TwinProfileModel(Base, TimestampMixin):
    """
    Persistent storage for Twin profile data.
    Stores the complete knowledge about a user's digital twin.
    """
    __tablename__ = "twin_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # Basic Identity
    full_name = Column(String(255))
    preferred_name = Column(String(100))
    email_addresses = Column(ARRAY(String), default=[])
    phone_numbers = Column(ARRAY(String), default=[])

    # Birth and Astrological Data
    birth_date = Column(Date)
    birth_time = Column(String(10))
    birth_place = Column(String(255))
    zodiac_sign = Column(String(50))
    ascendant = Column(String(50))
    moon_sign = Column(String(50))

    # Professional Identity
    current_role = Column(String(255))
    company = Column(String(255))
    industry = Column(String(100))
    professional_titles = Column(ARRAY(String), default=[])
    expertise_areas = Column(ARRAY(String), default=[])

    # Personality & Communication
    personality_traits = Column(JSONB, default={})  # trait -> score (0-1)
    communication_style = Column(String(50), default="direct")
    languages = Column(ARRAY(String), default=["English"])
    preferred_language = Column(String(50), default="English")
    tone_preferences = Column(JSONB, default={})  # context -> tone

    # Work Patterns
    work_pattern = Column(JSONB, default={
        "typical_wake_time": "07:00",
        "typical_sleep_time": "23:00",
        "peak_productivity_hours": ["09:00-12:00", "15:00-18:00"],
        "no_disturb_hours": ["22:00-08:00"],
        "timezone": "Europe/Rome",
        "work_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    })

    # Email Preferences
    email_signature_style = Column(String(50), default="professional")
    auto_archive_categories = Column(ARRAY(String), default=["newsletter", "promotional"])
    priority_senders = Column(ARRAY(String), default=[])
    response_templates = Column(JSONB, default={})

    # Calendar Preferences
    meeting_buffer_minutes = Column(Integer, default=15)
    max_meetings_per_day = Column(Integer, default=6)
    preferred_meeting_duration = Column(Integer, default=30)

    # Twin Configuration
    twin_name = Column(String(100), default="LORENZ")
    twin_personality = Column(String(50), default="professional_proactive")
    autonomy_level = Column(Integer, default=7)  # 1-10
    notification_preferences = Column(JSONB, default={})

    # Learning Data (summary - detailed in TwinLearningModel)
    learned_preferences = Column(JSONB, default={})
    behavior_patterns = Column(JSONB, default={})

    # Relationships
    user = relationship("User", back_populates="twin_profile")
    contacts = relationship("TwinContactModel", back_populates="twin_profile", cascade="all, delete-orphan")
    projects = relationship("TwinProjectModel", back_populates="twin_profile", cascade="all, delete-orphan")
    learning_events = relationship("TwinLearningModel", back_populates="twin_profile", cascade="all, delete-orphan")


class TwinContactModel(Base, TimestampMixin):
    """
    Known contacts for the Twin.
    Stores relationship and interaction data for each contact.
    """
    __tablename__ = "twin_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_profile_id = Column(UUID(as_uuid=True), ForeignKey("twin_profiles.id"), nullable=False)

    # Contact Info
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    relationship_type = Column(String(50))  # colleague, friend, family, business, investor, media
    importance = Column(Integer, default=5)  # 1-10 scale
    is_vip = Column(Boolean, default=False)

    # Professional Info
    company = Column(String(255))
    role = Column(String(255))

    # Interaction Data
    notes = Column(ARRAY(String), default=[])
    interaction_count = Column(Integer, default=0)
    topics_discussed = Column(ARRAY(String), default=[])
    sentiment_history = Column(JSONB, default=[])

    # Communication Preferences
    response_priority = Column(String(20), default="medium")  # critical, high, medium, low
    preferred_language = Column(String(50), default="auto")
    communication_style = Column(String(50))  # how this person communicates

    # Research Data
    research_notes = Column(Text)
    linkedin_url = Column(String(500))
    social_profiles = Column(JSONB, default={})

    # Relationship
    twin_profile = relationship("TwinProfileModel", back_populates="contacts")


class TwinProjectModel(Base, TimestampMixin):
    """
    Active projects tracked by the Twin.
    Used for email filtering and prioritization.
    """
    __tablename__ = "twin_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_profile_id = Column(UUID(as_uuid=True), ForeignKey("twin_profiles.id"), nullable=False)

    # Project Info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=5)  # 1-10
    status = Column(String(20), default="active")  # active, paused, completed

    # Related Data
    stakeholders = Column(ARRAY(String), default=[])
    deadlines = Column(JSONB, default=[])
    key_topics = Column(ARRAY(String), default=[])
    related_emails_keywords = Column(ARRAY(String), default=[])

    # Relationship
    twin_profile = relationship("TwinProfileModel", back_populates="projects")


class TwinLearningModel(Base, TimestampMixin):
    """
    Learning events and patterns detected by the Twin.
    Stores the continuous learning data.
    """
    __tablename__ = "twin_learning_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_profile_id = Column(UUID(as_uuid=True), ForeignKey("twin_profiles.id"), nullable=False)

    # Event Info
    event_type = Column(String(50), nullable=False)  # email_received, email_replied, meeting_created, etc.
    event_data = Column(JSONB, default={})
    context = Column(JSONB, default={})

    # Computed Insights
    sentiment = Column(Integer)  # -100 to 100
    urgency = Column(Integer)  # 0 to 100
    importance = Column(Integer)  # 0 to 100

    # Pattern Detection
    patterns_detected = Column(ARRAY(String), default=[])
    learnings_extracted = Column(JSONB, default={})

    # Relationship
    twin_profile = relationship("TwinProfileModel", back_populates="learning_events")


class TwinPatternModel(Base, TimestampMixin):
    """
    Detected behavioral patterns.
    Used for predictions and proactive actions.
    """
    __tablename__ = "twin_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_profile_id = Column(UUID(as_uuid=True), ForeignKey("twin_profiles.id"), nullable=False)

    # Pattern Info
    name = Column(String(255), nullable=False)
    pattern_type = Column(String(50))  # temporal, relational, semantic, action
    confidence = Column(Integer, default=50)  # 0-100
    occurrences = Column(Integer, default=1)

    # Pattern Data
    data = Column(JSONB, default={})
    predictions = Column(JSONB, default=[])

    # Status
    is_active = Column(Boolean, default=True)


class TwinActionModel(Base, TimestampMixin):
    """
    Proactive actions taken or pending.
    Tracks what the Twin has done or plans to do.
    """
    __tablename__ = "twin_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_profile_id = Column(UUID(as_uuid=True), ForeignKey("twin_profiles.id"), nullable=False)

    # Action Info
    action_type = Column(String(50), nullable=False)  # email_filter, meeting_briefing, research, etc.
    priority = Column(Integer, default=3)  # 1-5 (1=critical)
    title = Column(String(255))
    description = Column(Text)
    data = Column(JSONB, default={})

    # Scheduling
    scheduled_for = Column(String(50))  # ISO datetime or null for immediate
    executed_at = Column(String(50))

    # Status
    status = Column(String(20), default="pending")  # pending, executing, completed, cancelled, failed
    result = Column(JSONB)

    # Approval
    requires_approval = Column(Boolean, default=False)
    user_notified = Column(Boolean, default=False)
    approved_at = Column(String(50))
    rejected_at = Column(String(50))
