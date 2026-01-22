"""
LORENZ SaaS - Calendar Service
================================

Multi-provider calendar integration for the Human Digital Twin.
Supports Google Calendar, Microsoft Outlook, and CalDAV.
"""

import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)


class CalendarProvider(str, Enum):
    """Supported calendar providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    CALDAV = "caldav"
    LOCAL = "local"  # For testing/development


@dataclass
class CalendarEvent:
    """Represents a calendar event"""
    id: str
    title: str
    start: datetime
    end: datetime
    description: str = ""
    location: str = ""
    attendees: List[str] = field(default_factory=list)
    organizer: str = ""
    is_all_day: bool = False
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    calendar_id: str = ""
    provider: CalendarProvider = CalendarProvider.LOCAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "description": self.description,
            "location": self.location,
            "attendees": self.attendees,
            "organizer": self.organizer,
            "is_all_day": self.is_all_day,
            "is_recurring": self.is_recurring,
            "recurrence_rule": self.recurrence_rule,
            "calendar_id": self.calendar_id,
            "provider": self.provider.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalendarEvent":
        """Create from dictionary"""
        start = data.get("start")
        end = data.get("end")

        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace("Z", "+00:00"))

        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            start=start or datetime.utcnow(),
            end=end or datetime.utcnow() + timedelta(hours=1),
            description=data.get("description", ""),
            location=data.get("location", ""),
            attendees=data.get("attendees", []),
            organizer=data.get("organizer", ""),
            is_all_day=data.get("is_all_day", False),
            is_recurring=data.get("is_recurring", False),
            recurrence_rule=data.get("recurrence_rule"),
            calendar_id=data.get("calendar_id", ""),
            provider=CalendarProvider(data.get("provider", "local")),
            metadata=data.get("metadata", {}),
        )


class CalendarService:
    """
    Multi-provider calendar service.

    Features:
    - Unified API for multiple calendar providers
    - Event retrieval and creation
    - Context building for AI (Twin)
    - Conflict detection
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None
    ):
        self.db = db
        self.user_id = user_id
        self._providers: Dict[CalendarProvider, Dict[str, Any]] = {}
        self._events_cache: List[CalendarEvent] = []
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes

    async def configure_provider(
        self,
        provider: CalendarProvider,
        credentials: Dict[str, Any]
    ):
        """
        Configure a calendar provider with OAuth credentials.

        Args:
            provider: The calendar provider
            credentials: OAuth tokens and configuration
        """
        self._providers[provider] = credentials
        logger.info(f"Configured calendar provider: {provider.value}")

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[CalendarProvider] = None,
        calendar_id: Optional[str] = None,
        max_results: int = 50
    ) -> List[CalendarEvent]:
        """
        Get calendar events from configured providers.

        Args:
            start_date: Start of date range (default: now)
            end_date: End of date range (default: 7 days from now)
            provider: Specific provider to query (default: all)
            calendar_id: Specific calendar ID
            max_results: Maximum events to return

        Returns:
            List of calendar events
        """
        if start_date is None:
            start_date = datetime.utcnow()
        if end_date is None:
            end_date = start_date + timedelta(days=7)

        events = []

        # Query each configured provider
        providers_to_query = [provider] if provider else list(self._providers.keys())

        for prov in providers_to_query:
            if prov not in self._providers:
                continue

            try:
                if prov == CalendarProvider.GOOGLE:
                    provider_events = await self._get_google_events(
                        start_date, end_date, calendar_id, max_results
                    )
                elif prov == CalendarProvider.MICROSOFT:
                    provider_events = await self._get_microsoft_events(
                        start_date, end_date, calendar_id, max_results
                    )
                elif prov == CalendarProvider.CALDAV:
                    provider_events = await self._get_caldav_events(
                        start_date, end_date, calendar_id, max_results
                    )
                else:
                    provider_events = []

                events.extend(provider_events)

            except Exception as e:
                logger.error(f"Failed to get events from {prov.value}: {e}")

        # Sort by start time
        events.sort(key=lambda e: e.start)

        # Cache results
        self._events_cache = events
        self._cache_timestamp = datetime.utcnow()

        return events[:max_results]

    async def get_today_events(self) -> List[CalendarEvent]:
        """Get events for today"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return await self.get_events(start_date=today, end_date=tomorrow)

    async def get_upcoming_events(
        self,
        hours: int = 24
    ) -> List[CalendarEvent]:
        """Get events in the next N hours"""
        now = datetime.utcnow()
        end = now + timedelta(hours=hours)
        return await self.get_events(start_date=now, end_date=end)

    async def get_events_with_attendee(
        self,
        attendee_email: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CalendarEvent]:
        """Get events where a specific person is an attendee"""
        events = await self.get_events(start_date, end_date)
        return [
            e for e in events
            if attendee_email.lower() in [a.lower() for a in e.attendees]
        ]

    async def create_event(
        self,
        event: CalendarEvent,
        provider: Optional[CalendarProvider] = None
    ) -> Optional[CalendarEvent]:
        """
        Create a calendar event.

        Args:
            event: The event to create
            provider: Provider to use (default: first configured)

        Returns:
            Created event with ID, or None if failed
        """
        if provider is None:
            # Use first configured provider
            if not self._providers:
                logger.error("No calendar provider configured")
                return None
            provider = list(self._providers.keys())[0]

        if provider not in self._providers:
            logger.error(f"Provider {provider.value} not configured")
            return None

        try:
            if provider == CalendarProvider.GOOGLE:
                return await self._create_google_event(event)
            elif provider == CalendarProvider.MICROSOFT:
                return await self._create_microsoft_event(event)
            elif provider == CalendarProvider.CALDAV:
                return await self._create_caldav_event(event)
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return None

        return None

    async def check_conflicts(
        self,
        start: datetime,
        end: datetime
    ) -> List[CalendarEvent]:
        """
        Check for conflicting events.

        Args:
            start: Proposed start time
            end: Proposed end time

        Returns:
            List of conflicting events
        """
        events = await self.get_events(
            start_date=start - timedelta(hours=1),
            end_date=end + timedelta(hours=1)
        )

        conflicts = []
        for event in events:
            # Check if times overlap
            if event.start < end and event.end > start:
                conflicts.append(event)

        return conflicts

    async def find_free_slots(
        self,
        date: datetime,
        duration_minutes: int = 60,
        work_start_hour: int = 9,
        work_end_hour: int = 18
    ) -> List[Dict[str, datetime]]:
        """
        Find free time slots on a given date.

        Args:
            date: Date to check
            duration_minutes: Required slot duration
            work_start_hour: Start of work hours
            work_end_hour: End of work hours

        Returns:
            List of available slots {"start": datetime, "end": datetime}
        """
        day_start = date.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)

        events = await self.get_events(start_date=day_start, end_date=day_end)

        # Sort events by start time
        events.sort(key=lambda e: e.start)

        free_slots = []
        current_time = day_start

        for event in events:
            # If there's a gap before this event
            if event.start > current_time:
                gap_minutes = (event.start - current_time).total_seconds() / 60
                if gap_minutes >= duration_minutes:
                    free_slots.append({
                        "start": current_time,
                        "end": event.start
                    })

            # Move current time to after this event
            if event.end > current_time:
                current_time = event.end

        # Check for time after last event
        if current_time < day_end:
            gap_minutes = (day_end - current_time).total_seconds() / 60
            if gap_minutes >= duration_minutes:
                free_slots.append({
                    "start": current_time,
                    "end": day_end
                })

        return free_slots

    def build_context_for_twin(
        self,
        events: List[CalendarEvent],
        include_attendees: bool = True
    ) -> str:
        """
        Build calendar context string for Twin AI.

        Args:
            events: List of events
            include_attendees: Whether to include attendee details

        Returns:
            Formatted context string
        """
        if not events:
            return "No upcoming calendar events."

        context_parts = ["## Upcoming Calendar Events:"]

        for event in events[:10]:  # Limit to 10 events
            start_str = event.start.strftime("%Y-%m-%d %H:%M")
            duration = (event.end - event.start).total_seconds() / 60

            parts = [f"- **{event.title}** ({start_str}, {int(duration)} min)"]

            if event.location:
                parts.append(f"  Location: {event.location}")

            if include_attendees and event.attendees:
                attendees_str = ", ".join(event.attendees[:5])
                if len(event.attendees) > 5:
                    attendees_str += f" +{len(event.attendees) - 5} more"
                parts.append(f"  Attendees: {attendees_str}")

            if event.description:
                desc_preview = event.description[:100]
                if len(event.description) > 100:
                    desc_preview += "..."
                parts.append(f"  Notes: {desc_preview}")

            context_parts.append("\n".join(parts))

        return "\n\n".join(context_parts)

    # =====================
    # Provider-specific implementations
    # =====================

    async def _get_google_events(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_id: Optional[str],
        max_results: int
    ) -> List[CalendarEvent]:
        """Get events from Google Calendar API"""
        creds = self._providers.get(CalendarProvider.GOOGLE, {})
        access_token = creds.get("access_token")

        if not access_token:
            logger.warning("Google Calendar: No access token")
            return []

        calendar_id = calendar_id or "primary"
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

        params = {
            "timeMin": start_date.isoformat() + "Z",
            "timeMax": end_date.isoformat() + "Z",
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime"
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        logger.error(f"Google Calendar API error: {resp.status}")
                        return []

                    data = await resp.json()
                    events = []

                    for item in data.get("items", []):
                        start = item.get("start", {})
                        end = item.get("end", {})

                        start_dt = start.get("dateTime") or start.get("date")
                        end_dt = end.get("dateTime") or end.get("date")

                        if isinstance(start_dt, str):
                            start_dt = datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
                        if isinstance(end_dt, str):
                            end_dt = datetime.fromisoformat(end_dt.replace("Z", "+00:00"))

                        events.append(CalendarEvent(
                            id=item.get("id", ""),
                            title=item.get("summary", ""),
                            start=start_dt,
                            end=end_dt,
                            description=item.get("description", ""),
                            location=item.get("location", ""),
                            attendees=[
                                a.get("email", "")
                                for a in item.get("attendees", [])
                            ],
                            organizer=item.get("organizer", {}).get("email", ""),
                            is_all_day="date" in start,
                            is_recurring="recurrence" in item,
                            recurrence_rule=item.get("recurrence", [None])[0],
                            calendar_id=calendar_id,
                            provider=CalendarProvider.GOOGLE,
                            metadata={"htmlLink": item.get("htmlLink")}
                        ))

                    return events

        except Exception as e:
            logger.error(f"Google Calendar fetch error: {e}")
            return []

    async def _get_microsoft_events(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_id: Optional[str],
        max_results: int
    ) -> List[CalendarEvent]:
        """Get events from Microsoft Graph API"""
        creds = self._providers.get(CalendarProvider.MICROSOFT, {})
        access_token = creds.get("access_token")

        if not access_token:
            logger.warning("Microsoft Calendar: No access token")
            return []

        url = "https://graph.microsoft.com/v1.0/me/calendarView"

        params = {
            "startDateTime": start_date.isoformat(),
            "endDateTime": end_date.isoformat(),
            "$top": max_results,
            "$orderby": "start/dateTime"
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        logger.error(f"Microsoft Graph API error: {resp.status}")
                        return []

                    data = await resp.json()
                    events = []

                    for item in data.get("value", []):
                        start = item.get("start", {})
                        end = item.get("end", {})

                        start_dt = datetime.fromisoformat(
                            start.get("dateTime", "").replace("Z", "+00:00")
                        )
                        end_dt = datetime.fromisoformat(
                            end.get("dateTime", "").replace("Z", "+00:00")
                        )

                        events.append(CalendarEvent(
                            id=item.get("id", ""),
                            title=item.get("subject", ""),
                            start=start_dt,
                            end=end_dt,
                            description=item.get("bodyPreview", ""),
                            location=item.get("location", {}).get("displayName", ""),
                            attendees=[
                                a.get("emailAddress", {}).get("address", "")
                                for a in item.get("attendees", [])
                            ],
                            organizer=item.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                            is_all_day=item.get("isAllDay", False),
                            is_recurring=item.get("recurrence") is not None,
                            calendar_id=calendar_id or "default",
                            provider=CalendarProvider.MICROSOFT,
                            metadata={"webLink": item.get("webLink")}
                        ))

                    return events

        except Exception as e:
            logger.error(f"Microsoft Graph fetch error: {e}")
            return []

    async def _get_caldav_events(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_id: Optional[str],
        max_results: int
    ) -> List[CalendarEvent]:
        """Get events from CalDAV server"""
        # CalDAV implementation would go here
        # For now, return empty list
        logger.info("CalDAV provider not fully implemented yet")
        return []

    async def _create_google_event(self, event: CalendarEvent) -> Optional[CalendarEvent]:
        """Create event in Google Calendar"""
        creds = self._providers.get(CalendarProvider.GOOGLE, {})
        access_token = creds.get("access_token")

        if not access_token:
            return None

        calendar_id = event.calendar_id or "primary"
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

        body = {
            "summary": event.title,
            "description": event.description,
            "location": event.location,
            "start": {"dateTime": event.start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": event.end.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": a} for a in event.attendees],
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, headers=headers) as resp:
                    if resp.status not in [200, 201]:
                        logger.error(f"Google Calendar create error: {resp.status}")
                        return None

                    data = await resp.json()
                    event.id = data.get("id", "")
                    event.provider = CalendarProvider.GOOGLE
                    return event

        except Exception as e:
            logger.error(f"Google Calendar create error: {e}")
            return None

    async def _create_microsoft_event(self, event: CalendarEvent) -> Optional[CalendarEvent]:
        """Create event in Microsoft Outlook"""
        creds = self._providers.get(CalendarProvider.MICROSOFT, {})
        access_token = creds.get("access_token")

        if not access_token:
            return None

        url = "https://graph.microsoft.com/v1.0/me/events"

        body = {
            "subject": event.title,
            "body": {"contentType": "text", "content": event.description},
            "location": {"displayName": event.location},
            "start": {"dateTime": event.start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": event.end.isoformat(), "timeZone": "UTC"},
            "attendees": [
                {"emailAddress": {"address": a}, "type": "required"}
                for a in event.attendees
            ],
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, headers=headers) as resp:
                    if resp.status not in [200, 201]:
                        logger.error(f"Microsoft Calendar create error: {resp.status}")
                        return None

                    data = await resp.json()
                    event.id = data.get("id", "")
                    event.provider = CalendarProvider.MICROSOFT
                    return event

        except Exception as e:
            logger.error(f"Microsoft Calendar create error: {e}")
            return None

    async def _create_caldav_event(self, event: CalendarEvent) -> Optional[CalendarEvent]:
        """Create event in CalDAV server"""
        logger.info("CalDAV event creation not fully implemented yet")
        return None


# Factory function
async def get_calendar_service(
    db: AsyncSession,
    user_id: Optional[str] = None,
    google_credentials: Optional[Dict[str, Any]] = None,
    microsoft_credentials: Optional[Dict[str, Any]] = None
) -> CalendarService:
    """
    Create and configure a CalendarService.

    Args:
        db: Database session
        user_id: User ID for context
        google_credentials: Google OAuth credentials
        microsoft_credentials: Microsoft OAuth credentials

    Returns:
        Configured CalendarService
    """
    service = CalendarService(db, user_id)

    if google_credentials:
        await service.configure_provider(CalendarProvider.GOOGLE, google_credentials)

    if microsoft_credentials:
        await service.configure_provider(CalendarProvider.MICROSOFT, microsoft_credentials)

    return service
