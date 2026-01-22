"""
LORENZ SaaS - Twin API Routes
Endpoints for Human Digital Twin operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.twin import TwinService, get_twin_service

router = APIRouter()
logger = logging.getLogger(__name__)


# =====================
# Request/Response Models
# =====================

class TwinProfileResponse(BaseModel):
    """Twin profile information"""
    user_id: str
    full_name: str
    preferred_name: str
    twin_name: str
    autonomy_level: int
    zodiac_sign: Optional[str] = None
    ascendant: Optional[str] = None
    communication_style: str
    languages: List[str]
    vip_contacts_count: int
    active_projects_count: int


class UpdateProfileRequest(BaseModel):
    """Request to update Twin profile"""
    preferred_name: Optional[str] = None
    twin_name: Optional[str] = None
    autonomy_level: Optional[int] = Field(None, ge=1, le=10)
    communication_style: Optional[str] = None
    languages: Optional[List[str]] = None


class AddVIPRequest(BaseModel):
    """Request to add VIP contact"""
    email: str


class AddProjectRequest(BaseModel):
    """Request to add a project"""
    name: str
    description: str
    priority: int = Field(5, ge=1, le=10)
    keywords: Optional[List[str]] = None


class EmailAnalysisRequest(BaseModel):
    """Request to analyze an email"""
    from_address: str = Field(..., alias="from")
    subject: str
    body: str
    message_id: Optional[str] = None

    class Config:
        populate_by_name = True


class EmailAnalysisResponse(BaseModel):
    """Email analysis result"""
    priority: str
    actions: List[Dict[str, Any]]
    insights: List[str]
    sender_insights: Optional[Dict[str, Any]] = None
    triggered_actions: List[Dict[str, Any]]


class DraftEmailRequest(BaseModel):
    """Request to draft email response"""
    original_from: str
    original_subject: str
    original_body: str
    intent: str = "professional"


class MeetingBriefingRequest(BaseModel):
    """Request for meeting briefing"""
    title: str
    start_time: str
    attendees: List[str]
    description: Optional[str] = None
    location: Optional[str] = None


class ResearchRequest(BaseModel):
    """Request to research a person"""
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    context: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Request to record feedback"""
    feedback_type: str = Field(..., pattern="^(approved|rejected|modified)$")
    action_id: Optional[str] = None
    data: Dict[str, Any] = {}


class LearningStatsResponse(BaseModel):
    """Learning statistics"""
    total_events: int
    events_by_type: Dict[str, int]
    patterns_count: int
    top_patterns: List[Dict[str, Any]]
    learning_started: str


# =====================
# Helper Functions
# =====================

async def get_initialized_twin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TwinService:
    """Get initialized TwinService for current user"""
    return await get_twin_service(current_user, db)


# =====================
# Profile Endpoints
# =====================

@router.get("/profile", response_model=TwinProfileResponse)
async def get_twin_profile(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get the current user's Twin profile.
    """
    profile = twin.profile
    return TwinProfileResponse(
        user_id=profile.user_id,
        full_name=profile.full_name,
        preferred_name=profile.preferred_name,
        twin_name=profile.twin_name,
        autonomy_level=profile.autonomy_level,
        zodiac_sign=profile.zodiac_sign,
        ascendant=profile.ascendant,
        communication_style=profile.communication_style.value,
        languages=profile.languages,
        vip_contacts_count=len(profile.vip_contacts),
        active_projects_count=len([p for p in profile.projects if p.status == "active"]),
    )


@router.patch("/profile")
async def update_twin_profile(
    request: UpdateProfileRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Update Twin profile settings.
    """
    updates = request.model_dump(exclude_unset=True, exclude_none=True)
    profile = await twin.update_profile(updates)

    return {
        "message": "Profile updated",
        "updated_fields": list(updates.keys()),
    }


@router.post("/profile/vip")
async def add_vip_contact(
    request: AddVIPRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Add a contact to VIP list for priority handling.
    """
    added = await twin.add_vip_contact(request.email)

    if added:
        return {"message": f"Added {request.email} to VIP contacts"}
    else:
        return {"message": f"{request.email} is already a VIP contact"}


@router.delete("/profile/vip/{email}")
async def remove_vip_contact(
    email: str,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Remove a contact from VIP list.
    """
    vip_list = twin.profile.vip_contacts
    email_lower = email.lower()

    for i, vip in enumerate(vip_list):
        if vip.lower() == email_lower:
            vip_list.pop(i)
            await twin.profile_manager.save_profile(twin.profile)
            return {"message": f"Removed {email} from VIP contacts"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{email} is not in VIP contacts"
    )


@router.get("/profile/vip")
async def list_vip_contacts(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    List all VIP contacts.
    """
    return {
        "vip_contacts": twin.profile.vip_contacts,
        "count": len(twin.profile.vip_contacts),
    }


# =====================
# Project Endpoints
# =====================

@router.post("/projects")
async def add_project(
    request: AddProjectRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Add a new project to track.
    """
    project = await twin.add_project(
        name=request.name,
        description=request.description,
        priority=request.priority,
        keywords=request.keywords,
    )

    return {
        "message": "Project added",
        "project": project,
    }


@router.get("/projects")
async def list_projects(
    status: Optional[str] = None,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    List all projects.
    """
    projects = twin.profile.projects

    if status:
        projects = [p for p in projects if p.status == status]

    return {
        "projects": [
            {
                "name": p.name,
                "description": p.description,
                "priority": p.priority,
                "status": p.status,
                "keywords": p.related_emails_keywords,
            }
            for p in projects
        ],
        "count": len(projects),
    }


# =====================
# Email Intelligence Endpoints
# =====================

@router.post("/email/analyze", response_model=EmailAnalysisResponse)
async def analyze_email(
    request: EmailAnalysisRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Analyze an incoming email and get Twin recommendations.
    """
    email_data = {
        "from": request.from_address,
        "subject": request.subject,
        "body": request.body,
        "message_id": request.message_id,
    }

    analysis = await twin.analyze_email(email_data)

    return EmailAnalysisResponse(
        priority=analysis.get("priority", "medium"),
        actions=analysis.get("actions", []),
        insights=analysis.get("insights", []),
        sender_insights=analysis.get("sender_insights"),
        triggered_actions=analysis.get("triggered_actions", []),
    )


@router.post("/email/draft")
async def draft_email_response(
    request: DraftEmailRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Generate a draft email response written as the Twin.
    """
    email_data = {
        "from": request.original_from,
        "subject": request.original_subject,
        "body": request.original_body,
    }

    draft = await twin.draft_email_response(email_data, request.intent)

    return {
        "draft": draft,
        "intent": request.intent,
        "original_subject": request.original_subject,
    }


@router.post("/email/should-auto-respond")
async def check_auto_respond(
    request: EmailAnalysisRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Check if Twin should auto-respond to this email.
    """
    email_data = {
        "from": request.from_address,
        "subject": request.subject,
        "body": request.body,
    }

    result = await twin.should_auto_respond(email_data)

    return {
        "should_auto_respond": result is not None,
        "details": result,
    }


# =====================
# Meeting & Calendar Endpoints
# =====================

@router.post("/meeting/briefing")
async def generate_meeting_briefing(
    request: MeetingBriefingRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Generate a comprehensive briefing for an upcoming meeting.
    """
    meeting = {
        "title": request.title,
        "start_time": request.start_time,
        "attendees": [{"email": a} for a in request.attendees],
        "description": request.description,
        "location": request.location,
    }

    briefing = await twin.prepare_meeting_briefing(meeting)

    return briefing


@router.post("/meeting/alerts")
async def get_meeting_alerts(
    meetings: List[MeetingBriefingRequest],
    alert_minutes: int = 30,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get alerts for upcoming meetings.
    """
    meetings_data = [
        {
            "title": m.title,
            "start_time": m.start_time,
            "attendees": m.attendees,
        }
        for m in meetings
    ]

    alerts = await twin.get_upcoming_meeting_alerts(meetings_data, alert_minutes)

    return {
        "alerts": alerts,
        "count": len(alerts),
    }


# =====================
# Research & Intelligence Endpoints
# =====================

@router.post("/research/person")
async def research_person(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Research a person and generate intelligence.
    """
    person = {
        "name": request.name,
        "email": request.email,
        "company": request.company,
    }

    result = await twin.research_person(person, request.context or "")

    return result


# =====================
# Daily Operations Endpoints
# =====================

@router.post("/briefing/daily")
async def generate_daily_briefing(
    calendar_events: Optional[List[Dict[str, Any]]] = None,
    pending_emails: int = 0,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Generate the daily briefing for the user.
    """
    briefing = await twin.generate_daily_briefing(
        calendar_events=calendar_events,
        pending_emails=pending_emails,
    )

    return briefing


@router.get("/suggestions")
async def get_proactive_suggestions(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get proactive suggestions from the Twin.
    """
    suggestions = await twin.get_proactive_suggestions()

    return {
        "suggestions": suggestions,
        "count": len(suggestions),
    }


# =====================
# Proactive Actions Endpoints
# =====================

@router.get("/actions/pending")
async def get_pending_actions(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get pending proactive actions.
    """
    actions = twin.proactive.get_pending_actions()

    return {
        "actions": actions,
        "count": len(actions),
    }


@router.post("/actions/process")
async def process_proactive_actions(
    max_actions: int = 10,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Process pending proactive actions.
    """
    results = await twin.process_proactive_queue()

    return {
        "processed": results,
        "count": len(results),
    }


@router.get("/actions/stats")
async def get_action_stats(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get statistics about proactive actions.
    """
    return twin.proactive.get_action_stats()


# =====================
# Learning & Feedback Endpoints
# =====================

@router.post("/feedback")
async def record_feedback(
    request: FeedbackRequest,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Record user feedback on Twin actions.
    """
    await twin.record_feedback(
        feedback_type=request.feedback_type,
        data={
            "action_id": request.action_id,
            **request.data,
        }
    )

    return {"message": "Feedback recorded"}


@router.get("/learning/stats", response_model=LearningStatsResponse)
async def get_learning_stats(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get statistics about the Twin's learning.
    """
    stats = await twin.get_learning_stats()

    return LearningStatsResponse(
        total_events=stats["total_events"],
        events_by_type=stats["events_by_type"],
        patterns_count=stats["patterns_count"],
        top_patterns=stats["top_patterns"],
        learning_started=stats["learning_started"],
    )


@router.get("/learning/patterns")
async def get_learned_patterns(
    limit: int = 20,
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get learned behavioral patterns.
    """
    patterns = sorted(
        twin.learning.patterns.values(),
        key=lambda p: p.confidence,
        reverse=True
    )[:limit]

    return {
        "patterns": [p.to_dict() for p in patterns],
        "count": len(patterns),
    }


# =====================
# System Prompt Endpoint
# =====================

@router.get("/system-prompt")
async def get_system_prompt(
    twin: TwinService = Depends(get_initialized_twin)
):
    """
    Get the current Twin system prompt (for debugging/admin).
    """
    prompt = await twin.get_system_prompt()

    return {
        "system_prompt": prompt,
        "length": len(prompt),
    }
