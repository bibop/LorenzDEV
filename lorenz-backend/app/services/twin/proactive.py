"""
LORENZ - Proactive Engine for Human Digital Twin
Anticipates needs and takes proactive actions on behalf of the Twin's human
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime, timedelta, time
from enum import Enum
import asyncio
import logging
from abc import ABC, abstractmethod

from .profile import TwinProfile, Urgency
from .learning import TwinLearning, EventType, LearningEvent

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of proactive actions"""
    # Email actions
    EMAIL_FILTER = "email_filter"
    EMAIL_DRAFT_RESPONSE = "email_draft_response"
    EMAIL_AUTO_ARCHIVE = "email_auto_archive"
    EMAIL_PRIORITY_ALERT = "email_priority_alert"
    EMAIL_SUMMARY = "email_summary"

    # Calendar actions
    MEETING_REMINDER = "meeting_reminder"
    MEETING_PREPARATION = "meeting_preparation"
    MEETING_BRIEFING = "meeting_briefing"
    CALENDAR_CONFLICT_ALERT = "calendar_conflict_alert"
    TRAVEL_TIME_ALERT = "travel_time_alert"

    # Research actions
    PERSON_RESEARCH = "person_research"
    COMPANY_RESEARCH = "company_research"
    TOPIC_RESEARCH = "topic_research"
    NEWS_MONITORING = "news_monitoring"

    # Document actions
    PRESENTATION_NEEDED = "presentation_needed"
    DOCUMENT_PREPARATION = "document_preparation"
    SUMMARY_GENERATION = "summary_generation"

    # Alert actions
    DAILY_BRIEFING = "daily_briefing"
    WEEKLY_SUMMARY = "weekly_summary"
    DEADLINE_ALERT = "deadline_alert"
    FOLLOW_UP_REMINDER = "follow_up_reminder"

    # Intelligence actions
    INSIGHT_DETECTED = "insight_detected"
    PATTERN_ALERT = "pattern_alert"
    RECOMMENDATION = "recommendation"


class ActionPriority(Enum):
    """Priority levels for proactive actions"""
    CRITICAL = 1  # Execute immediately, interrupt if needed
    HIGH = 2      # Execute soon, notify user
    MEDIUM = 3    # Queue for next batch
    LOW = 4       # Execute when idle
    BACKGROUND = 5  # Execute silently


@dataclass
class ProactiveAction:
    """A proactive action to be taken by the Twin"""
    action_type: ActionType
    priority: ActionPriority
    title: str
    description: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, cancelled, failed
    result: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    user_notified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "status": self.status,
            "requires_approval": self.requires_approval,
        }


class ActionHandler(ABC):
    """Base class for action handlers"""

    @abstractmethod
    async def can_handle(self, action: ProactiveAction) -> bool:
        """Check if handler can process this action"""
        pass

    @abstractmethod
    async def execute(self, action: ProactiveAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action and return result"""
        pass


class EmailFilterHandler(ActionHandler):
    """Handles email filtering actions"""

    async def can_handle(self, action: ProactiveAction) -> bool:
        return action.action_type in [
            ActionType.EMAIL_FILTER,
            ActionType.EMAIL_AUTO_ARCHIVE,
            ActionType.EMAIL_PRIORITY_ALERT,
        ]

    async def execute(self, action: ProactiveAction, context: Dict[str, Any]) -> Dict[str, Any]:
        email_data = action.data.get("email", {})
        profile = context.get("profile")

        if action.action_type == ActionType.EMAIL_AUTO_ARCHIVE:
            # Mark email for archiving
            return {
                "action": "archive",
                "email_id": email_data.get("id"),
                "reason": action.data.get("reason", "Learned pattern: low priority"),
            }

        if action.action_type == ActionType.EMAIL_PRIORITY_ALERT:
            # Create priority notification
            return {
                "action": "notify",
                "message": f"High priority email from {email_data.get('from')}: {email_data.get('subject')}",
                "urgency": "high",
            }

        return {"action": "none"}


class MeetingPreparationHandler(ActionHandler):
    """Handles meeting preparation actions"""

    async def can_handle(self, action: ProactiveAction) -> bool:
        return action.action_type in [
            ActionType.MEETING_PREPARATION,
            ActionType.MEETING_BRIEFING,
            ActionType.MEETING_REMINDER,
        ]

    async def execute(self, action: ProactiveAction, context: Dict[str, Any]) -> Dict[str, Any]:
        meeting = action.data.get("meeting", {})

        if action.action_type == ActionType.MEETING_BRIEFING:
            attendees = meeting.get("attendees", [])
            return {
                "action": "generate_briefing",
                "attendees": attendees,
                "meeting_topic": meeting.get("title"),
                "research_needed": [a for a in attendees if a not in context.get("known_contacts", [])],
            }

        if action.action_type == ActionType.MEETING_REMINDER:
            return {
                "action": "remind",
                "message": f"Meeting in {action.data.get('minutes_until', 15)} minutes: {meeting.get('title')}",
                "meeting_details": meeting,
            }

        return {"action": "none"}


class ResearchHandler(ActionHandler):
    """Handles research actions"""

    async def can_handle(self, action: ProactiveAction) -> bool:
        return action.action_type in [
            ActionType.PERSON_RESEARCH,
            ActionType.COMPANY_RESEARCH,
            ActionType.TOPIC_RESEARCH,
        ]

    async def execute(self, action: ProactiveAction, context: Dict[str, Any]) -> Dict[str, Any]:
        if action.action_type == ActionType.PERSON_RESEARCH:
            person = action.data.get("person", {})
            return {
                "action": "research_person",
                "name": person.get("name"),
                "email": person.get("email"),
                "company": person.get("company"),
                "search_queries": [
                    f"{person.get('name')} LinkedIn",
                    f"{person.get('name')} {person.get('company', '')}",
                    f"{person.get('name')} news",
                ],
            }

        return {"action": "none"}


class ProactiveEngine:
    """
    Main engine for proactive actions.
    Monitors context, detects opportunities, and triggers appropriate actions.
    """

    def __init__(
        self,
        profile: TwinProfile,
        learning: TwinLearning,
    ):
        self.profile = profile
        self.learning = learning
        self.action_queue: List[ProactiveAction] = []
        self.completed_actions: List[ProactiveAction] = []
        self.running = False

        # Action handlers
        self.handlers: List[ActionHandler] = [
            EmailFilterHandler(),
            MeetingPreparationHandler(),
            ResearchHandler(),
        ]

        # Trigger conditions
        self.triggers: List[Dict[str, Any]] = []
        self._setup_default_triggers()

    def _setup_default_triggers(self):
        """Setup default proactive triggers"""
        # Email triggers
        self.triggers.append({
            "name": "vip_email_alert",
            "event_types": [EventType.EMAIL_RECEIVED],
            "condition": self._check_vip_email,
            "action_type": ActionType.EMAIL_PRIORITY_ALERT,
            "priority": ActionPriority.HIGH,
        })

        self.triggers.append({
            "name": "newsletter_auto_archive",
            "event_types": [EventType.EMAIL_RECEIVED],
            "condition": self._check_newsletter_email,
            "action_type": ActionType.EMAIL_AUTO_ARCHIVE,
            "priority": ActionPriority.LOW,
        })

        # Meeting triggers
        self.triggers.append({
            "name": "upcoming_meeting_prep",
            "scheduled": True,
            "check_interval_minutes": 30,
            "condition": self._check_upcoming_meetings,
            "action_type": ActionType.MEETING_BRIEFING,
            "priority": ActionPriority.MEDIUM,
        })

        # Research triggers
        self.triggers.append({
            "name": "unknown_attendee_research",
            "event_types": [EventType.MEETING_CREATED, EventType.MEETING_ACCEPTED],
            "condition": self._check_unknown_attendees,
            "action_type": ActionType.PERSON_RESEARCH,
            "priority": ActionPriority.MEDIUM,
        })

    async def process_event(self, event: LearningEvent) -> List[ProactiveAction]:
        """Process an event and trigger appropriate actions"""
        triggered_actions = []

        for trigger in self.triggers:
            if trigger.get("scheduled"):
                continue  # Skip scheduled triggers

            event_types = trigger.get("event_types", [])
            if event.event_type not in event_types:
                continue

            condition = trigger.get("condition")
            if condition and await condition(event):
                action = self._create_action_from_trigger(trigger, event)
                if action:
                    triggered_actions.append(action)
                    self.action_queue.append(action)

        return triggered_actions

    def _create_action_from_trigger(
        self,
        trigger: Dict[str, Any],
        event: LearningEvent
    ) -> Optional[ProactiveAction]:
        """Create a ProactiveAction from a trigger"""
        action_type = trigger.get("action_type")
        if not action_type:
            return None

        return ProactiveAction(
            action_type=action_type,
            priority=trigger.get("priority", ActionPriority.MEDIUM),
            title=trigger.get("name", "Proactive Action"),
            description=f"Triggered by {event.event_type.value}",
            data={
                "trigger": trigger.get("name"),
                "event": event.to_dict(),
            },
            requires_approval=trigger.get("requires_approval", False),
        )

    # =================
    # Trigger Conditions
    # =================

    async def _check_vip_email(self, event: LearningEvent) -> bool:
        """Check if email is from VIP sender"""
        sender = event.data.get("from", "")
        return self.profile.is_vip(sender)

    async def _check_newsletter_email(self, event: LearningEvent) -> bool:
        """Check if email appears to be a newsletter"""
        subject = event.data.get("subject", "").lower()
        sender = event.data.get("from", "").lower()

        newsletter_indicators = [
            "newsletter", "unsubscribe", "weekly digest", "monthly update",
            "noreply", "no-reply", "donotreply", "automated",
        ]

        for indicator in newsletter_indicators:
            if indicator in subject or indicator in sender:
                return True

        return self.profile.should_auto_archive(sender, subject)

    async def _check_upcoming_meetings(self, event: Optional[LearningEvent] = None) -> bool:
        """Check for meetings requiring preparation"""
        # This would integrate with calendar service
        # Return True if there are meetings in the next 2 hours without briefings
        return False  # Placeholder

    async def _check_unknown_attendees(self, event: LearningEvent) -> bool:
        """Check if meeting has unknown attendees"""
        attendees = event.data.get("attendees", [])
        for attendee in attendees:
            email = attendee.get("email", attendee) if isinstance(attendee, dict) else attendee
            if not self.profile.get_contact(email):
                return True
        return False

    # =================
    # Action Processing
    # =================

    async def execute_action(self, action: ProactiveAction) -> Dict[str, Any]:
        """Execute a single proactive action"""
        action.status = "executing"

        for handler in self.handlers:
            if await handler.can_handle(action):
                try:
                    context = {
                        "profile": self.profile,
                        "learning": self.learning,
                        "known_contacts": list(self.profile.contacts.keys()),
                    }
                    result = await handler.execute(action, context)
                    action.result = result
                    action.status = "completed"
                    action.executed_at = datetime.utcnow()
                    return result
                except Exception as e:
                    logger.error(f"Action execution failed: {e}")
                    action.status = "failed"
                    action.result = {"error": str(e)}
                    return {"error": str(e)}

        action.status = "failed"
        action.result = {"error": "No handler found"}
        return {"error": "No handler found"}

    async def process_queue(self, max_actions: int = 10) -> List[Dict[str, Any]]:
        """Process pending actions from the queue"""
        results = []

        # Sort by priority
        self.action_queue.sort(key=lambda a: a.priority.value)

        processed = 0
        while self.action_queue and processed < max_actions:
            action = self.action_queue[0]

            # Check if action requires approval and hasn't been approved
            if action.requires_approval and action.status == "pending":
                break

            # Check if action is scheduled for later
            if action.scheduled_for and action.scheduled_for > datetime.utcnow():
                continue

            self.action_queue.pop(0)
            result = await self.execute_action(action)
            results.append({
                "action": action.to_dict(),
                "result": result,
            })
            self.completed_actions.append(action)
            processed += 1

        return results

    # =================
    # Proactive Generators
    # =================

    async def generate_daily_briefing(self) -> ProactiveAction:
        """Generate daily briefing action"""
        briefing_data = self.learning.get_daily_briefing_data()

        return ProactiveAction(
            action_type=ActionType.DAILY_BRIEFING,
            priority=ActionPriority.MEDIUM,
            title="Daily Briefing",
            description=f"Your briefing for {datetime.now().strftime('%A, %B %d')}",
            data={
                "briefing": briefing_data,
                "date": datetime.now().date().isoformat(),
            },
            scheduled_for=self._get_briefing_time(),
        )

    def _get_briefing_time(self) -> datetime:
        """Get optimal time for daily briefing"""
        wake_time = self.profile.work_pattern.typical_wake_time
        hour, minute = map(int, wake_time.split(":"))

        today = datetime.now().replace(hour=hour, minute=minute + 30, second=0, microsecond=0)
        if today < datetime.now():
            today += timedelta(days=1)

        return today

    async def generate_meeting_briefings(
        self,
        meetings: List[Dict[str, Any]]
    ) -> List[ProactiveAction]:
        """Generate briefings for upcoming meetings"""
        actions = []

        for meeting in meetings:
            meeting_time = meeting.get("start_time")
            if isinstance(meeting_time, str):
                meeting_time = datetime.fromisoformat(meeting_time)

            # Schedule briefing 30 minutes before meeting
            briefing_time = meeting_time - timedelta(minutes=30)

            # Check for unknown attendees
            attendees = meeting.get("attendees", [])
            unknown_attendees = [
                a for a in attendees
                if not self.profile.get_contact(a.get("email", a) if isinstance(a, dict) else a)
            ]

            action = ProactiveAction(
                action_type=ActionType.MEETING_BRIEFING,
                priority=ActionPriority.MEDIUM,
                title=f"Briefing: {meeting.get('title', 'Meeting')}",
                description=f"Preparation for meeting with {len(attendees)} attendee(s)",
                data={
                    "meeting": meeting,
                    "unknown_attendees": unknown_attendees,
                    "research_needed": len(unknown_attendees) > 0,
                },
                scheduled_for=briefing_time,
            )
            actions.append(action)

        return actions

    async def detect_presentation_need(
        self,
        message_content: str
    ) -> Optional[ProactiveAction]:
        """Detect if a message indicates a presentation is needed"""
        presentation_keywords = [
            "presentation", "slides", "deck", "powerpoint", "keynote",
            "pitch", "demo", "showcase", "present to", "prepare for",
        ]

        content_lower = message_content.lower()

        for keyword in presentation_keywords:
            if keyword in content_lower:
                return ProactiveAction(
                    action_type=ActionType.PRESENTATION_NEEDED,
                    priority=ActionPriority.MEDIUM,
                    title="Presentation Detected",
                    description="A presentation may need to be prepared",
                    data={
                        "source_message": message_content[:500],
                        "detected_keyword": keyword,
                    },
                    requires_approval=True,
                )

        return None

    async def schedule_follow_up(
        self,
        context: Dict[str, Any],
        days_delay: int = 3
    ) -> ProactiveAction:
        """Schedule a follow-up reminder"""
        return ProactiveAction(
            action_type=ActionType.FOLLOW_UP_REMINDER,
            priority=ActionPriority.LOW,
            title="Follow-up Reminder",
            description=f"Follow up on: {context.get('subject', 'previous conversation')}",
            data={
                "context": context,
                "original_date": datetime.utcnow().isoformat(),
            },
            scheduled_for=datetime.utcnow() + timedelta(days=days_delay),
        )

    # =================
    # Email Intelligence
    # =================

    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an email and determine proactive actions"""
        analysis = {
            "priority": Urgency.MEDIUM.value,
            "actions": [],
            "insights": [],
        }

        sender = email_data.get("from", "")
        subject = email_data.get("subject", "")
        content = email_data.get("body", "")

        # Check priority
        priority = self.profile.get_email_priority(sender, subject)
        analysis["priority"] = priority.value

        # Check if VIP
        if self.profile.is_vip(sender):
            analysis["insights"].append("VIP sender - prioritize response")
            analysis["actions"].append({
                "type": ActionType.EMAIL_PRIORITY_ALERT.value,
                "priority": "high",
            })

        # Check for auto-archive
        if self.profile.should_auto_archive(sender, subject):
            analysis["actions"].append({
                "type": ActionType.EMAIL_AUTO_ARCHIVE.value,
                "reason": "Matches auto-archive pattern",
            })

        # Check for meeting mentions
        meeting_keywords = ["meeting", "call", "zoom", "teams", "calendario", "appuntamento"]
        if any(kw in content.lower() for kw in meeting_keywords):
            analysis["insights"].append("Meeting-related email detected")

        # Check for presentation need
        presentation_action = await self.detect_presentation_need(content)
        if presentation_action:
            analysis["actions"].append({
                "type": ActionType.PRESENTATION_NEEDED.value,
                "details": presentation_action.data,
            })

        # Check for deadline mentions
        deadline_keywords = ["deadline", "scadenza", "entro", "by tomorrow", "by friday", "asap", "urgente"]
        if any(kw in content.lower() for kw in deadline_keywords):
            analysis["insights"].append("Deadline or urgent request detected")
            analysis["priority"] = Urgency.HIGH.value

        # Get sender insights from learning
        sender_insights = self.learning.get_sender_insights(sender)
        if sender_insights.get("patterns"):
            analysis["sender_insights"] = sender_insights

        return analysis

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get list of pending actions"""
        return [a.to_dict() for a in self.action_queue if a.status == "pending"]

    def get_action_stats(self) -> Dict[str, Any]:
        """Get statistics about proactive actions"""
        return {
            "pending": len([a for a in self.action_queue if a.status == "pending"]),
            "completed_today": len([
                a for a in self.completed_actions
                if a.executed_at and a.executed_at.date() == datetime.now().date()
            ]),
            "total_completed": len(self.completed_actions),
            "by_type": {
                action_type.value: len([
                    a for a in self.completed_actions
                    if a.action_type == action_type
                ])
                for action_type in ActionType
            },
        }
