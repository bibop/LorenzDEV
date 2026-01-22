"""
LORENZ - Human Digital Twin Learning System
Continuously learns from interactions to deeply understand the Twin's human
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of learning events"""
    # Email events
    EMAIL_RECEIVED = "email_received"
    EMAIL_READ = "email_read"
    EMAIL_REPLIED = "email_replied"
    EMAIL_ARCHIVED = "email_archived"
    EMAIL_DELETED = "email_deleted"
    EMAIL_STARRED = "email_starred"
    EMAIL_FORWARDED = "email_forwarded"

    # Calendar events
    MEETING_CREATED = "meeting_created"
    MEETING_ACCEPTED = "meeting_accepted"
    MEETING_DECLINED = "meeting_declined"
    MEETING_RESCHEDULED = "meeting_rescheduled"
    MEETING_CANCELLED = "meeting_cancelled"

    # Communication events
    MESSAGE_SENT = "message_sent"
    CALL_MADE = "call_made"
    CALL_RECEIVED = "call_received"

    # Behavior events
    SEARCH_PERFORMED = "search_performed"
    DOCUMENT_OPENED = "document_opened"
    TASK_COMPLETED = "task_completed"
    TASK_DELEGATED = "task_delegated"

    # Feedback events
    TWIN_APPROVED = "twin_approved"  # User approved Twin's action
    TWIN_REJECTED = "twin_rejected"  # User rejected Twin's action
    TWIN_MODIFIED = "twin_modified"  # User modified Twin's output

    # System events
    LOGIN = "login"
    PREFERENCE_CHANGED = "preference_changed"


@dataclass
class LearningEvent:
    """A single learning event"""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    session_id: str = ""

    # Computed insights
    sentiment: Optional[float] = None  # -1 to 1
    urgency: Optional[float] = None  # 0 to 1
    importance: Optional[float] = None  # 0 to 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "context": self.context,
            "user_id": self.user_id,
            "sentiment": self.sentiment,
            "urgency": self.urgency,
            "importance": self.importance,
        }


@dataclass
class Pattern:
    """A learned behavioral pattern"""
    name: str
    pattern_type: str  # "temporal", "relational", "semantic", "action"
    confidence: float  # 0 to 1
    occurrences: int
    last_seen: datetime
    data: Dict[str, Any]
    predictions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pattern_type": self.pattern_type,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "last_seen": self.last_seen.isoformat(),
            "data": self.data,
        }


class TwinLearning:
    """
    Learning engine for the Human Digital Twin.
    Continuously processes events to build a deep understanding of the user.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.events: List[LearningEvent] = []
        self.patterns: Dict[str, Pattern] = {}

        # Learning statistics
        self.stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "learning_started": datetime.utcnow(),
        }

        # Pattern detectors
        self._pattern_detectors: List[Callable] = [
            self._detect_email_patterns,
            self._detect_temporal_patterns,
            self._detect_communication_patterns,
            self._detect_priority_patterns,
        ]

    async def record_event(self, event: LearningEvent):
        """Record a learning event and trigger pattern analysis"""
        event.user_id = self.user_id
        event.timestamp = event.timestamp or datetime.utcnow()

        # Store event
        self.events.append(event)
        self.stats["total_events"] += 1
        self.stats["events_by_type"][event.event_type.value] += 1

        # Run pattern detection
        await self._analyze_patterns(event)

        logger.debug(f"Recorded event {event.event_type.value} for user {self.user_id}")

    async def _analyze_patterns(self, new_event: LearningEvent):
        """Analyze events to detect patterns"""
        for detector in self._pattern_detectors:
            try:
                patterns = detector(new_event, self.events[-100:])  # Last 100 events
                for pattern in patterns:
                    self._update_pattern(pattern)
            except Exception as e:
                logger.error(f"Pattern detection error: {e}")

    def _update_pattern(self, pattern: Pattern):
        """Update or create a pattern"""
        key = f"{pattern.pattern_type}:{pattern.name}"
        if key in self.patterns:
            existing = self.patterns[key]
            existing.occurrences += 1
            existing.last_seen = datetime.utcnow()
            # Increase confidence with repetition
            existing.confidence = min(0.99, existing.confidence + 0.05)
            # Merge predictions
            existing.predictions.extend(pattern.predictions)
        else:
            self.patterns[key] = pattern

    def _detect_email_patterns(
        self,
        event: LearningEvent,
        recent_events: List[LearningEvent]
    ) -> List[Pattern]:
        """Detect email behavior patterns"""
        patterns = []

        if event.event_type not in [
            EventType.EMAIL_RECEIVED,
            EventType.EMAIL_READ,
            EventType.EMAIL_REPLIED,
            EventType.EMAIL_ARCHIVED,
        ]:
            return patterns

        # Pattern: Response time to specific senders
        if event.event_type == EventType.EMAIL_REPLIED:
            sender = event.data.get("original_sender", "")
            if sender:
                # Find when email was received
                for prev_event in reversed(recent_events):
                    if (
                        prev_event.event_type == EventType.EMAIL_RECEIVED
                        and prev_event.data.get("from") == sender
                    ):
                        response_time = event.timestamp - prev_event.timestamp
                        patterns.append(Pattern(
                            name=f"response_time:{sender}",
                            pattern_type="temporal",
                            confidence=0.6,
                            occurrences=1,
                            last_seen=datetime.utcnow(),
                            data={
                                "sender": sender,
                                "avg_response_minutes": response_time.total_seconds() / 60,
                            },
                            predictions=[{
                                "type": "response_time",
                                "sender": sender,
                                "expected_minutes": response_time.total_seconds() / 60,
                            }]
                        ))
                        break

        # Pattern: Emails that get archived without reading
        if event.event_type == EventType.EMAIL_ARCHIVED:
            sender = event.data.get("from", "")
            subject = event.data.get("subject", "")

            # Check if it was read first
            was_read = any(
                e.event_type == EventType.EMAIL_READ
                and e.data.get("message_id") == event.data.get("message_id")
                for e in recent_events
            )

            if not was_read:
                patterns.append(Pattern(
                    name=f"auto_archive_candidate:{sender}",
                    pattern_type="action",
                    confidence=0.5,
                    occurrences=1,
                    last_seen=datetime.utcnow(),
                    data={
                        "sender": sender,
                        "subject_keywords": self._extract_keywords(subject),
                        "action": "archive_without_read",
                    },
                    predictions=[{
                        "type": "auto_archive",
                        "sender": sender,
                    }]
                ))

        return patterns

    def _detect_temporal_patterns(
        self,
        event: LearningEvent,
        recent_events: List[LearningEvent]
    ) -> List[Pattern]:
        """Detect time-based patterns"""
        patterns = []

        hour = event.timestamp.hour
        day_of_week = event.timestamp.strftime("%A")

        # Pattern: Activity by time of day
        patterns.append(Pattern(
            name=f"activity:{day_of_week}:{hour}",
            pattern_type="temporal",
            confidence=0.4,
            occurrences=1,
            last_seen=datetime.utcnow(),
            data={
                "day": day_of_week,
                "hour": hour,
                "event_type": event.event_type.value,
            },
            predictions=[]
        ))

        return patterns

    def _detect_communication_patterns(
        self,
        event: LearningEvent,
        recent_events: List[LearningEvent]
    ) -> List[Pattern]:
        """Detect communication style patterns"""
        patterns = []

        if event.event_type not in [EventType.EMAIL_REPLIED, EventType.MESSAGE_SENT]:
            return patterns

        # Analyze response length
        content = event.data.get("content", "")
        word_count = len(content.split())

        recipient = event.data.get("to", "")
        if recipient:
            patterns.append(Pattern(
                name=f"response_length:{recipient}",
                pattern_type="relational",
                confidence=0.5,
                occurrences=1,
                last_seen=datetime.utcnow(),
                data={
                    "recipient": recipient,
                    "avg_words": word_count,
                    "style": "brief" if word_count < 50 else "detailed" if word_count > 200 else "moderate",
                },
                predictions=[{
                    "type": "response_style",
                    "recipient": recipient,
                    "expected_words": word_count,
                }]
            ))

        return patterns

    def _detect_priority_patterns(
        self,
        event: LearningEvent,
        recent_events: List[LearningEvent]
    ) -> List[Pattern]:
        """Detect priority and urgency patterns"""
        patterns = []

        # Look for patterns in what gets immediate attention
        if event.event_type == EventType.EMAIL_READ:
            # Check time from receipt to read
            message_id = event.data.get("message_id")
            for prev_event in reversed(recent_events):
                if (
                    prev_event.event_type == EventType.EMAIL_RECEIVED
                    and prev_event.data.get("message_id") == message_id
                ):
                    read_delay = event.timestamp - prev_event.timestamp
                    sender = prev_event.data.get("from", "")

                    # Immediate reads (< 5 min) indicate high priority
                    if read_delay.total_seconds() < 300:
                        patterns.append(Pattern(
                            name=f"high_priority_sender:{sender}",
                            pattern_type="relational",
                            confidence=0.6,
                            occurrences=1,
                            last_seen=datetime.utcnow(),
                            data={
                                "sender": sender,
                                "avg_read_delay_seconds": read_delay.total_seconds(),
                            },
                            predictions=[{
                                "type": "sender_priority",
                                "sender": sender,
                                "priority": "high",
                            }]
                        ))
                    break

        return patterns

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did", "will",
                      "would", "could", "should", "may", "might", "must", "shall",
                      "re", "fw", "fwd"}

        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:10]

    def get_predictions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get predictions based on learned patterns"""
        predictions = []

        # Gather relevant predictions from all patterns
        for pattern in self.patterns.values():
            if pattern.confidence > 0.6:  # Only high-confidence patterns
                for pred in pattern.predictions:
                    pred["confidence"] = pattern.confidence
                    pred["pattern_name"] = pattern.name
                    predictions.append(pred)

        return predictions

    def get_sender_insights(self, sender_email: str) -> Dict[str, Any]:
        """Get learned insights about a specific sender"""
        insights = {
            "email": sender_email,
            "patterns": [],
            "expected_response_time": None,
            "priority_level": "normal",
            "typical_topics": [],
            "recommended_action": None,
        }

        sender_lower = sender_email.lower()

        for key, pattern in self.patterns.items():
            if sender_lower in key.lower() or sender_lower in str(pattern.data).lower():
                insights["patterns"].append(pattern.to_dict())

                if "response_time" in key:
                    insights["expected_response_time"] = pattern.data.get("avg_response_minutes")

                if "high_priority" in key:
                    insights["priority_level"] = "high"

                if "auto_archive" in key:
                    insights["recommended_action"] = "archive"

        return insights

    def should_auto_respond(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine if Twin should auto-respond based on learned patterns"""
        sender = email_data.get("from", "").lower()

        # Check for patterns that suggest auto-response
        for key, pattern in self.patterns.items():
            if pattern.pattern_type == "action" and pattern.confidence > 0.8:
                if sender in str(pattern.data).lower():
                    if pattern.data.get("action") == "always_respond":
                        return {
                            "should_respond": True,
                            "confidence": pattern.confidence,
                            "template_suggestion": pattern.data.get("template"),
                        }

        return None

    def get_daily_briefing_data(self) -> Dict[str, Any]:
        """Generate data for daily briefing based on learned patterns"""
        now = datetime.utcnow()
        today = now.strftime("%A")

        briefing = {
            "date": now.date().isoformat(),
            "day": today,
            "predicted_busy_hours": [],
            "expected_emails_from": [],
            "patterns_summary": [],
        }

        # Find temporal patterns for today
        for key, pattern in self.patterns.items():
            if pattern.pattern_type == "temporal" and today in key:
                briefing["predicted_busy_hours"].append(pattern.data.get("hour"))

            if pattern.pattern_type == "relational" and pattern.confidence > 0.7:
                if "high_priority" in key:
                    sender = pattern.data.get("sender")
                    if sender:
                        briefing["expected_emails_from"].append(sender)

        # Summarize top patterns
        sorted_patterns = sorted(
            self.patterns.values(),
            key=lambda p: (p.confidence, p.occurrences),
            reverse=True
        )
        briefing["patterns_summary"] = [p.to_dict() for p in sorted_patterns[:10]]

        return briefing

    def export_learning_data(self) -> Dict[str, Any]:
        """Export all learning data for backup or analysis"""
        return {
            "user_id": self.user_id,
            "stats": dict(self.stats),
            "patterns": {k: v.to_dict() for k, v in self.patterns.items()},
            "recent_events": [e.to_dict() for e in self.events[-1000:]],
            "exported_at": datetime.utcnow().isoformat(),
        }

    def import_learning_data(self, data: Dict[str, Any]):
        """Import learning data from backup"""
        self.stats = data.get("stats", self.stats)

        for key, pattern_data in data.get("patterns", {}).items():
            self.patterns[key] = Pattern(
                name=pattern_data["name"],
                pattern_type=pattern_data["pattern_type"],
                confidence=pattern_data["confidence"],
                occurrences=pattern_data["occurrences"],
                last_seen=datetime.fromisoformat(pattern_data["last_seen"]),
                data=pattern_data["data"],
            )

        logger.info(f"Imported {len(self.patterns)} patterns for user {self.user_id}")
