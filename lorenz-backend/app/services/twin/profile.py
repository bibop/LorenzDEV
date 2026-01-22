"""
LORENZ - Human Digital Twin Profile System
Manages the deep understanding of the Twin's human counterpart
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class PersonalityTrait(Enum):
    """Big Five personality traits"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class CommunicationStyle(Enum):
    """Communication preferences"""
    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    TECHNICAL = "technical"
    STORYTELLING = "storytelling"


class Urgency(Enum):
    """Message/task urgency levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass
class ContactProfile:
    """Profile of a known contact"""
    email: str
    name: str
    relationship: str  # colleague, friend, family, business, investor, media, etc.
    importance: int = 5  # 1-10 scale
    company: Optional[str] = None
    role: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    topics_discussed: List[str] = field(default_factory=list)
    sentiment_history: List[Dict[str, Any]] = field(default_factory=list)
    response_priority: Urgency = Urgency.MEDIUM
    preferred_language: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "email": self.email,
            "name": self.name,
            "relationship": self.relationship,
            "importance": self.importance,
            "company": self.company,
            "role": self.role,
            "notes": self.notes,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "interaction_count": self.interaction_count,
            "topics_discussed": self.topics_discussed,
            "response_priority": self.response_priority.value,
            "preferred_language": self.preferred_language,
        }


@dataclass
class WorkPattern:
    """User's work patterns and preferences"""
    typical_wake_time: str = "07:00"
    typical_sleep_time: str = "23:00"
    peak_productivity_hours: List[str] = field(default_factory=lambda: ["09:00-12:00", "15:00-18:00"])
    preferred_meeting_times: List[str] = field(default_factory=lambda: ["10:00-12:00", "14:00-16:00"])
    no_disturb_hours: List[str] = field(default_factory=lambda: ["22:00-08:00"])
    timezone: str = "Europe/Rome"
    work_days: List[str] = field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    travel_frequency: str = "frequent"  # rare, occasional, frequent, constant
    current_location: Optional[str] = None
    home_base: str = "Los Angeles"


@dataclass
class ProjectContext:
    """Active project information"""
    name: str
    description: str
    priority: int = 5  # 1-10
    stakeholders: List[str] = field(default_factory=list)
    deadlines: List[Dict[str, Any]] = field(default_factory=list)
    key_topics: List[str] = field(default_factory=list)
    status: str = "active"  # active, paused, completed
    related_emails_keywords: List[str] = field(default_factory=list)


@dataclass
class TwinProfile:
    """
    Complete profile of the Human Digital Twin's counterpart.
    This represents everything LORENZ knows about its human.
    """

    # Basic Identity
    user_id: str
    full_name: str
    preferred_name: str
    email_addresses: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)

    # Birth and Astrological Data
    birth_date: Optional[date] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    zodiac_sign: Optional[str] = None
    ascendant: Optional[str] = None
    moon_sign: Optional[str] = None

    # Professional Identity
    current_role: str = ""
    company: str = ""
    industry: str = ""
    professional_titles: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)

    # Personality & Communication
    personality_traits: Dict[str, float] = field(default_factory=dict)  # trait -> score (0-1)
    communication_style: CommunicationStyle = CommunicationStyle.DIRECT
    languages: List[str] = field(default_factory=lambda: ["English", "Italian"])
    preferred_language: str = "English"
    tone_preferences: Dict[str, str] = field(default_factory=dict)  # context -> tone

    # Work Patterns
    work_pattern: WorkPattern = field(default_factory=WorkPattern)

    # Active Projects
    projects: List[ProjectContext] = field(default_factory=list)

    # Contact Network
    contacts: Dict[str, ContactProfile] = field(default_factory=dict)  # email -> ContactProfile
    vip_contacts: List[str] = field(default_factory=list)  # emails that always get priority

    # Email Preferences
    email_signature_style: str = "professional"
    auto_archive_categories: List[str] = field(default_factory=lambda: ["newsletter", "promotional", "automated"])
    priority_senders: List[str] = field(default_factory=list)
    response_templates: Dict[str, str] = field(default_factory=dict)

    # Calendar Preferences
    meeting_buffer_minutes: int = 15
    max_meetings_per_day: int = 6
    preferred_meeting_duration: int = 30
    calendar_sync_accounts: List[str] = field(default_factory=list)

    # Learning Data
    learned_preferences: Dict[str, Any] = field(default_factory=dict)
    behavior_patterns: Dict[str, Any] = field(default_factory=dict)
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)

    # Twin Configuration
    twin_name: str = "LORENZ"
    twin_personality: str = "professional_proactive"
    autonomy_level: int = 7  # 1-10, how much LORENZ can do without asking
    notification_preferences: Dict[str, bool] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None

    def get_contact(self, email: str) -> Optional[ContactProfile]:
        """Get contact profile by email"""
        return self.contacts.get(email.lower())

    def add_contact(self, contact: ContactProfile):
        """Add or update a contact"""
        self.contacts[contact.email.lower()] = contact
        self.updated_at = datetime.utcnow()

    def is_vip(self, email: str) -> bool:
        """Check if email is from a VIP contact"""
        return email.lower() in [v.lower() for v in self.vip_contacts]

    def get_email_priority(self, sender_email: str, subject: str) -> Urgency:
        """Determine email priority based on sender and content"""
        # VIP always high priority
        if self.is_vip(sender_email):
            return Urgency.HIGH

        # Check contact profile
        contact = self.get_contact(sender_email)
        if contact:
            return contact.response_priority

        # Check for project-related keywords
        subject_lower = subject.lower()
        for project in self.projects:
            if project.status == "active":
                for keyword in project.related_emails_keywords:
                    if keyword.lower() in subject_lower:
                        return Urgency.HIGH if project.priority >= 8 else Urgency.MEDIUM

        return Urgency.MEDIUM

    def should_auto_archive(self, sender: str, subject: str) -> bool:
        """Determine if email should be auto-archived"""
        subject_lower = subject.lower()
        for category in self.auto_archive_categories:
            if category.lower() in subject_lower:
                return True
        return False

    def is_work_hours(self, dt: Optional[datetime] = None) -> bool:
        """Check if given time is within work hours"""
        if dt is None:
            dt = datetime.now()

        # Check day of week
        day_name = dt.strftime("%A")
        if day_name not in self.work_pattern.work_days:
            return False

        # Check time
        current_time = dt.strftime("%H:%M")
        for no_disturb in self.work_pattern.no_disturb_hours:
            start, end = no_disturb.split("-")
            if start <= current_time <= end:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "preferred_name": self.preferred_name,
            "email_addresses": self.email_addresses,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "zodiac_sign": self.zodiac_sign,
            "ascendant": self.ascendant,
            "current_role": self.current_role,
            "company": self.company,
            "communication_style": self.communication_style.value,
            "languages": self.languages,
            "preferred_language": self.preferred_language,
            "work_pattern": {
                "timezone": self.work_pattern.timezone,
                "peak_productivity_hours": self.work_pattern.peak_productivity_hours,
                "no_disturb_hours": self.work_pattern.no_disturb_hours,
            },
            "projects": [
                {"name": p.name, "priority": p.priority, "status": p.status}
                for p in self.projects
            ],
            "vip_contacts": self.vip_contacts,
            "twin_name": self.twin_name,
            "autonomy_level": self.autonomy_level,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TwinProfile":
        """Create profile from dictionary"""
        profile = cls(
            user_id=data.get("user_id", ""),
            full_name=data.get("full_name", ""),
            preferred_name=data.get("preferred_name", ""),
        )
        # Populate other fields from data
        for key, value in data.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        return profile


class TwinProfileManager:
    """
    Manages TwinProfile persistence and updates.
    Integrates with the database to store and retrieve profiles.
    """

    def __init__(self, db_session=None):
        self.db = db_session
        self._cache: Dict[str, TwinProfile] = {}

    async def get_profile(self, user_id: str) -> Optional[TwinProfile]:
        """Get or create user's twin profile"""
        if user_id in self._cache:
            return self._cache[user_id]

        # TODO: Load from database
        # For now, return None if not cached
        return None

    async def save_profile(self, profile: TwinProfile):
        """Save profile to database"""
        profile.updated_at = datetime.utcnow()
        self._cache[profile.user_id] = profile

        # TODO: Persist to database
        logger.info(f"Saved profile for user {profile.user_id}")

    async def update_from_interaction(
        self,
        user_id: str,
        interaction_type: str,
        data: Dict[str, Any]
    ):
        """Update profile based on user interaction"""
        profile = await self.get_profile(user_id)
        if not profile:
            logger.warning(f"No profile found for user {user_id}")
            return

        # Update based on interaction type
        if interaction_type == "email_sent":
            # Learn from sent emails
            self._learn_from_email(profile, data)
        elif interaction_type == "meeting_scheduled":
            # Learn from meeting patterns
            self._learn_from_meeting(profile, data)
        elif interaction_type == "feedback":
            # Direct feedback from user
            profile.feedback_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            })

        await self.save_profile(profile)

    def _learn_from_email(self, profile: TwinProfile, email_data: Dict[str, Any]):
        """Learn patterns from email interactions"""
        recipient = email_data.get("to")
        if recipient:
            contact = profile.get_contact(recipient)
            if contact:
                contact.interaction_count += 1
                contact.last_interaction = datetime.utcnow()

    def _learn_from_meeting(self, profile: TwinProfile, meeting_data: Dict[str, Any]):
        """Learn patterns from meeting scheduling"""
        # Update preferred meeting times based on actual scheduling
        pass

    async def create_initial_profile(
        self,
        user_id: str,
        user_data: Dict[str, Any]
    ) -> TwinProfile:
        """Create initial profile from onboarding data"""
        profile = TwinProfile(
            user_id=user_id,
            full_name=user_data.get("full_name", ""),
            preferred_name=user_data.get("preferred_name", user_data.get("full_name", "").split()[0]),
            email_addresses=[user_data.get("email", "")],
        )

        # Set astrological data if provided
        if "birth_date" in user_data:
            try:
                profile.birth_date = date.fromisoformat(user_data["birth_date"])
            except (ValueError, TypeError):
                pass

        profile.zodiac_sign = user_data.get("zodiac_sign")
        profile.ascendant = user_data.get("ascendant")

        # Set work preferences
        if "timezone" in user_data:
            profile.work_pattern.timezone = user_data["timezone"]

        # Set twin preferences
        if "twin_name" in user_data:
            profile.twin_name = user_data["twin_name"]

        await self.save_profile(profile)
        return profile
