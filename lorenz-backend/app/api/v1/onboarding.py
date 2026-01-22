"""
LORENZ SaaS - Onboarding Routes
===============================

Handles user onboarding with automated setup features:
- Traditional step-by-step onboarding
- Auto-discovery of local files, cloud storage, social profiles
- Guided OAuth connection flow
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, List
from pydantic import BaseModel
import logging

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.discovery import (
    AutoSetupOrchestrator,
    LocalDiscoveryService,
    CloudStorageDiscovery,
    SocialHistoryIngestion,
)
from app.services.discovery.local import FileCategory
from app.services.discovery.cloud import CloudProvider
from app.services.discovery.social import SocialPlatform

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for setup sessions (use Redis in production)
_setup_sessions: Dict[str, AutoSetupOrchestrator] = {}


class OnboardingStepRequest(BaseModel):
    """Request to complete an onboarding step"""
    step_id: str
    data: Optional[dict] = None


class OnboardingStatusResponse(BaseModel):
    """Onboarding status response"""
    completed: bool
    current_step: str
    steps: list


ONBOARDING_STEPS = [
    {"id": "account", "title": "Create Account", "required": True},
    {"id": "email", "title": "Connect Email", "required": True},
    {"id": "calendar", "title": "Calendars", "required": False},
    {"id": "storage", "title": "Cloud Storage", "required": False},
    {"id": "social", "title": "Social Media", "required": False},
    {"id": "telegram", "title": "Telegram", "required": False},
    {"id": "knowledge", "title": "Knowledge Base", "required": True},
    {"id": "complete", "title": "Ready!", "required": True},
]


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current onboarding status.
    """
    # Calculate completed steps based on user's data
    completed_steps = ["account"]  # Account is always completed if user exists

    # Check email accounts
    if len(current_user.email_accounts) > 0:
        completed_steps.append("email")

    # Check OAuth connections for calendar/storage
    for conn in current_user.oauth_connections:
        if conn.provider in ["google", "microsoft"] and "calendar" not in completed_steps:
            if any(s.startswith("calendar") for s in conn.scopes):
                completed_steps.append("calendar")

    # Check cloud storage
    for conn in current_user.oauth_connections:
        if conn.provider in ["google", "microsoft", "dropbox"]:
            if any(s.startswith("drive") or s.startswith("files") for s in conn.scopes):
                if "storage" not in completed_steps:
                    completed_steps.append("storage")

    # Check social accounts
    if len(current_user.social_accounts) > 0:
        completed_steps.append("social")

    # Check Telegram
    if current_user.telegram_chat_id:
        completed_steps.append("telegram")

    # Check RAG documents
    if len(current_user.rag_documents) > 0:
        completed_steps.append("knowledge")

    # Determine current step
    current_step = current_user.onboarding_step

    # Build steps with completion status
    steps = []
    for step in ONBOARDING_STEPS:
        steps.append({
            **step,
            "completed": step["id"] in completed_steps
        })

    return OnboardingStatusResponse(
        completed=current_user.onboarding_completed,
        current_step=current_step,
        steps=steps
    )


@router.post("/step/{step_id}")
async def complete_onboarding_step(
    step_id: str,
    request: Optional[OnboardingStepRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an onboarding step as viewed/completed.
    """
    # Validate step exists
    valid_steps = [s["id"] for s in ONBOARDING_STEPS]
    if step_id not in valid_steps:
        raise HTTPException(status_code=400, detail=f"Invalid step: {step_id}")

    # Update user's current step
    current_user.onboarding_step = step_id

    # Check if onboarding is complete
    if step_id == "complete":
        current_user.onboarding_completed = True

    db.add(current_user)
    await db.commit()

    return {"message": f"Step {step_id} completed", "current_step": step_id}


@router.post("/skip")
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Skip remaining onboarding steps.
    """
    current_user.onboarding_completed = True
    current_user.onboarding_step = "complete"

    db.add(current_user)
    await db.commit()

    return {"message": "Onboarding skipped"}


@router.post("/reset")
async def reset_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset onboarding to start from beginning.
    """
    current_user.onboarding_completed = False
    current_user.onboarding_step = "email"  # Skip account step since user exists

    db.add(current_user)
    await db.commit()

    return {"message": "Onboarding reset"}


# ==============================================================================
# AUTOMATED SETUP ENDPOINTS
# ==============================================================================

class AutoSetupRequest(BaseModel):
    """Request to start automated setup"""
    include_local_scan: bool = True
    include_cloud: bool = True
    include_social: bool = True


class SetupStepExecuteRequest(BaseModel):
    """Request to execute a setup step"""
    step_id: str
    oauth_tokens: Optional[Dict[str, str]] = None


class LocalScanRequest(BaseModel):
    """Request for local file scan"""
    directories: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    max_files: int = 1000


class CloudDiscoveryRequest(BaseModel):
    """Request for cloud storage discovery"""
    provider: str  # google_drive, onedrive, dropbox
    access_token: str
    max_files: int = 500


class SocialIngestionRequest(BaseModel):
    """Request for social history ingestion"""
    platform: str  # linkedin, twitter, facebook, instagram
    access_token: str
    max_posts: int = 100


@router.post("/auto-setup/start")
async def start_auto_setup(
    request: AutoSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start the automated setup process.

    This initializes the setup orchestrator which:
    1. Scans local system for available data sources
    2. Creates a personalized setup plan
    3. Returns the plan for frontend to guide user through
    """
    user_id = str(current_user.id)
    tenant_id = str(current_user.tenant_id)

    # Create orchestrator
    orchestrator = AutoSetupOrchestrator(db, user_id, tenant_id)
    progress = await orchestrator.initialize_setup()

    # Store session
    _setup_sessions[user_id] = orchestrator

    logger.info(f"Started auto-setup for user {user_id}")

    return {
        "session_id": progress.session_id,
        "progress": progress.to_dict(),
        "next_step": orchestrator.get_next_step().to_dict() if orchestrator.get_next_step() else None,
        "required_oauth_providers": orchestrator.get_required_oauth_providers(),
    }


@router.get("/auto-setup/progress")
async def get_auto_setup_progress(
    current_user: User = Depends(get_current_user),
):
    """
    Get current auto-setup progress.
    """
    user_id = str(current_user.id)
    orchestrator = _setup_sessions.get(user_id)

    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail="No active setup session. Start with /auto-setup/start"
        )

    progress = orchestrator.get_progress()
    next_step = orchestrator.get_next_step()

    return {
        "progress": progress.to_dict() if progress else None,
        "next_step": next_step.to_dict() if next_step else None,
        "required_oauth_providers": orchestrator.get_required_oauth_providers(),
    }


@router.post("/auto-setup/execute-step")
async def execute_setup_step(
    request: SetupStepExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a specific setup step.

    For steps requiring OAuth, include the tokens in the request.
    """
    user_id = str(current_user.id)
    orchestrator = _setup_sessions.get(user_id)

    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail="No active setup session"
        )

    try:
        step = await orchestrator.execute_step(
            step_id=request.step_id,
            oauth_tokens=request.oauth_tokens
        )

        return {
            "step": step.to_dict(),
            "progress": orchestrator.get_progress().to_dict(),
            "next_step": orchestrator.get_next_step().to_dict() if orchestrator.get_next_step() else None,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Setup step execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-setup/skip-step/{step_id}")
async def skip_setup_step(
    step_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Skip a setup step.
    """
    user_id = str(current_user.id)
    orchestrator = _setup_sessions.get(user_id)

    if not orchestrator:
        raise HTTPException(status_code=404, detail="No active setup session")

    try:
        step = await orchestrator.skip_step(step_id)
        return {
            "step": step.to_dict(),
            "progress": orchestrator.get_progress().to_dict(),
            "next_step": orchestrator.get_next_step().to_dict() if orchestrator.get_next_step() else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auto-setup/complete")
async def complete_auto_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark the auto-setup as complete and update user's onboarding status.
    """
    user_id = str(current_user.id)
    orchestrator = _setup_sessions.get(user_id)

    if orchestrator:
        progress = orchestrator.get_progress()
        # Clean up session
        del _setup_sessions[user_id]
    else:
        progress = None

    # Update user's onboarding status
    current_user.onboarding_completed = True
    current_user.onboarding_step = "complete"

    db.add(current_user)
    await db.commit()

    return {
        "message": "Setup completed",
        "final_progress": progress.to_dict() if progress else None,
    }


# ==============================================================================
# DIRECT DISCOVERY ENDPOINTS (for manual/granular control)
# ==============================================================================

@router.post("/discovery/local-scan")
async def scan_local_files(
    request: LocalScanRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Scan local files on the user's computer.

    Note: This endpoint is called by the local agent running on user's machine.
    The results are then sent back to the server.
    """
    from pathlib import Path

    # Parse categories
    categories = None
    if request.categories:
        categories = {FileCategory(c) for c in request.categories}

    service = LocalDiscoveryService(
        max_file_size_mb=100,
        include_hidden=False,
        compute_hashes=False,
        categories_filter=categories,
    )

    # Add custom directories
    additional_dirs = None
    if request.directories:
        additional_dirs = [Path(d) for d in request.directories]

    result = await service.run_full_discovery(additional_directories=additional_dirs)

    return {
        "scan_id": result.scan_id,
        "files_found": result.files_found,
        "by_category": result.files_by_category,
        "total_size_mb": result.total_size_bytes / (1024 * 1024),
        "directories_scanned": result.directories_scanned,
        # Don't return full file list for large scans
        "files_preview": [f.to_dict() for f in result.files[:50]],
        "errors": result.errors,
    }


@router.post("/discovery/cloud")
async def discover_cloud_storage(
    request: CloudDiscoveryRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Discover files from cloud storage.
    """
    try:
        provider = CloudProvider(request.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Valid options: {[p.value for p in CloudProvider]}"
        )

    async with CloudStorageDiscovery(
        access_token=request.access_token,
        provider=provider,
        max_results=request.max_files,
    ) as discovery:
        result = await discovery.discover_all()

    return {
        "scan_id": result.scan_id,
        "provider": result.provider.value,
        "files_found": result.files_found,
        "folders_found": result.folders_found,
        "total_size_mb": result.total_size_bytes / (1024 * 1024),
        "files_preview": [f.to_dict() for f in result.files[:50]],
        "errors": result.errors,
    }


@router.post("/discovery/social")
async def ingest_social_history(
    request: SocialIngestionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Ingest social media history for profile building.
    """
    try:
        platform = SocialPlatform(request.platform)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Valid options: {[p.value for p in SocialPlatform]}"
        )

    async with SocialHistoryIngestion(
        access_token=request.access_token,
        platform=platform,
        max_posts=request.max_posts,
    ) as ingestion:
        result = await ingestion.ingest()

    return {
        "scan_id": result.scan_id,
        "platform": result.platform.value,
        "profile": result.profile.to_dict() if result.profile else None,
        "experiences_count": len(result.experiences),
        "education_count": len(result.education),
        "skills_count": len(result.skills),
        "content_count": len(result.content),
        "interests": result.interests[:20],
        "summary": result.summary,
        "errors": result.errors,
    }


@router.get("/discovery/quick-scan")
async def quick_system_scan(
    current_user: User = Depends(get_current_user),
):
    """
    Quick scan to see what data sources are available.
    Fast operation, returns immediately.
    """
    service = LocalDiscoveryService()
    result = await service.quick_scan()

    return {
        "platform": result.get("platform"),
        "home_dir": result.get("home_dir"),
        "directories_available": result.get("directories_available", []),
        "email_clients_detected": result.get("email_clients_detected", []),
        "calendar_sources_detected": result.get("calendar_sources_detected", []),
        "estimated_scan_dirs": result.get("estimated_scan_dirs", 0),
    }


# ==============================================================================
# IDENTITY DISCOVERY ENDPOINTS (Immersive Orb Onboarding)
# ==============================================================================

class NameConfirmationRequest(BaseModel):
    """Request to confirm user's name"""
    full_name: str


class IdentityDiscoveryRequest(BaseModel):
    """Request to discover identity from name"""
    full_name: str
    additional_context: Optional[Dict] = None


class DisambiguationRequest(BaseModel):
    """Request to resolve identity disambiguation"""
    selected_option: int
    additional_info: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """Request to update/correct profile information"""
    field: str
    value: str


class OnboardingCompleteRequest(BaseModel):
    """Request to complete onboarding"""
    profile_data: Dict
    assistant_name: str = "LORENZ"


@router.post("/identity/confirm-name")
async def confirm_name(
    request: NameConfirmationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1 of Orb Onboarding: Confirm the user's name.
    """
    full_name = request.full_name.strip().title()
    parts = full_name.split()

    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    current_user.name = full_name
    await db.commit()

    return {
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "message": f"Piacere di conoscerti, {first_name}!",
        "next_step": "identity_discovery"
    }


@router.post("/identity/discover")
async def discover_identity(
    request: IdentityDiscoveryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2 of Orb Onboarding: Discover information about the user from public sources.
    Uses web search and AI to find and analyze information.
    """
    from app.services.identity import create_identity_service

    logger.info(f"Starting identity discovery for: {request.full_name}")

    identity_service = create_identity_service()
    profile = await identity_service.discover_identity(
        full_name=request.full_name,
        additional_context=request.additional_context
    )

    # Generate introduction
    name = profile.first_name or request.full_name.split()[0]
    if profile.bio_summary:
        intro = profile.bio_summary
    else:
        intro_parts = [f"Piacere di conoscerti, {name}!"]
        if profile.profession and profile.company:
            intro_parts.append(f"Vedo che lavori come {profile.profession} presso {profile.company}.")
        elif profile.profession:
            intro_parts.append(f"Sei un/una {profile.profession}, interessante!")
        intro = " ".join(intro_parts)

    # Store discovered profile
    if not current_user.preferences:
        current_user.preferences = {}
    current_user.preferences["discovered_profile"] = profile.to_dict()
    current_user.preferences["onboarding_step"] = "profile_review"
    await db.commit()

    return {
        **profile.to_dict(),
        "lorenz_introduction": intro,
        "suggested_questions": [] if not profile.disambiguation_needed else [
            "Ho trovato più persone con questo nome.",
            *[f"{i+1}. {opt.get('description', '')[:100]}" for i, opt in enumerate(profile.disambiguation_options[:3])],
            "Quale di queste descrizioni corrisponde a te?"
        ],
    }


@router.post("/identity/resolve-disambiguation")
async def resolve_disambiguation(
    request: DisambiguationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2b: Resolve disambiguation when multiple identities are found.
    """
    from app.services.identity import create_identity_service

    prefs = current_user.preferences or {}
    stored_profile = prefs.get("discovered_profile")

    if not stored_profile:
        raise HTTPException(status_code=400, detail="No identity discovery in progress")

    options = stored_profile.get("disambiguation_options", [])
    if request.selected_option < 0 or request.selected_option >= len(options):
        raise HTTPException(status_code=400, detail="Invalid option selected")

    selected = options[request.selected_option]

    identity_service = create_identity_service()
    profile = await identity_service.discover_identity(
        full_name=stored_profile.get("full_name", ""),
        additional_context={
            "selected_context": selected.get("context", selected.get("description")),
            "additional_info": request.additional_info,
        }
    )

    current_user.preferences["discovered_profile"] = profile.to_dict()
    current_user.preferences["onboarding_step"] = "profile_review"
    await db.commit()

    return {
        **profile.to_dict(),
        "lorenz_introduction": profile.bio_summary or f"Ora ti riconosco, {profile.first_name}!",
    }


@router.post("/identity/update-field")
async def update_profile_field(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 3: Update/correct a specific profile field.
    """
    prefs = current_user.preferences or {}
    stored_profile = prefs.get("discovered_profile", {})

    if request.field in stored_profile:
        stored_profile[request.field] = request.value
        current_user.preferences["discovered_profile"] = stored_profile
        await db.commit()

        return {
            "success": True,
            "field": request.field,
            "value": request.value,
            "message": f"Ho aggiornato {request.field}"
        }

    raise HTTPException(status_code=400, detail=f"Unknown field: {request.field}")


@router.post("/identity/complete")
async def complete_identity_onboarding(
    request: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 4: Complete the identity-based onboarding.
    """
    if not current_user.preferences:
        current_user.preferences = {}

    current_user.preferences.update({
        "assistant_name": request.assistant_name,
        "profile_data": request.profile_data,
        "identity_onboarding_completed": True,
    })

    current_user.name = request.profile_data.get("full_name", current_user.name)
    await db.commit()

    return {
        "success": True,
        "message": f"Benvenuto, {current_user.name}! Sono {request.assistant_name}, il tuo assistente personale.",
        "redirect": "/setup",
    }
