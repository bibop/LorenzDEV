"""
LORENZ SaaS - Auto Setup Orchestrator
=====================================

Orchestrates the automated first-time setup process:
1. Detects available data sources (local, cloud, social)
2. Guides user through OAuth connections
3. Discovers and indexes documents
4. Builds initial user profile from social history
5. Creates the Human Digital Twin foundation

This is the "magic" that makes Lorenz feel intelligent from the first interaction.
"""

import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from .local import LocalDiscoveryService, DiscoveryResult, FileCategory
from .cloud import CloudStorageDiscovery, CloudProvider, CloudDiscoveryResult
from .social import SocialHistoryIngestion, SocialPlatform, SocialHistoryResult

logger = logging.getLogger(__name__)


class SetupPhase(str, Enum):
    """Phases of the automated setup"""
    INITIALIZING = "initializing"
    DETECTING_LOCAL = "detecting_local"
    CONNECTING_EMAIL = "connecting_email"
    CONNECTING_CALENDAR = "connecting_calendar"
    DISCOVERING_CLOUD = "discovering_cloud"
    CONNECTING_SOCIAL = "connecting_social"
    ANALYZING_HISTORY = "analyzing_history"
    BUILDING_PROFILE = "building_profile"
    INDEXING_DOCUMENTS = "indexing_documents"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class SetupPriority(str, Enum):
    """Priority levels for setup steps"""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass
class SetupStep:
    """A step in the setup process"""
    id: str
    phase: SetupPhase
    title: str
    description: str
    priority: SetupPriority
    requires_oauth: bool = False
    oauth_provider: Optional[str] = None
    oauth_scopes: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, skipped, failed
    result: Optional[Dict] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "phase": self.phase.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "requires_oauth": self.requires_oauth,
            "oauth_provider": self.oauth_provider,
            "oauth_scopes": self.oauth_scopes,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class SetupProgress:
    """Current progress of the setup"""
    session_id: str
    user_id: str
    current_phase: SetupPhase
    current_step_id: Optional[str]
    steps: List[SetupStep]
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    percent_complete: int
    discoveries: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_phase": self.current_phase.value,
            "current_step_id": self.current_step_id,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "percent_complete": self.percent_complete,
            "discoveries": self.discoveries,
        }


class AutoSetupOrchestrator:
    """
    Orchestrates the automated setup process for new users.

    The setup process:
    1. Quick scan of local system to understand what's available
    2. Guide user to connect email (required)
    3. Optional: Connect calendars
    4. Discover cloud storage (if OAuth available)
    5. Connect social media for profile understanding
    6. Analyze social history to build initial profile
    7. Index important documents
    8. Generate initial Twin profile

    Design principles:
    - Be fast and non-intrusive
    - Show progress to build trust
    - Allow skipping any step
    - Learn from what user chooses to share
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: str,
        tenant_id: str,
    ):
        """
        Initialize setup orchestrator.

        Args:
            db: Database session
            user_id: User ID
            tenant_id: Tenant ID
        """
        self.db = db
        self.user_id = user_id
        self.tenant_id = tenant_id

        self._progress: Optional[SetupProgress] = None
        self._progress_callback: Optional[Callable] = None
        self._cancelled = False

    def set_progress_callback(self, callback: Callable[[SetupProgress], None]):
        """Set callback for progress updates"""
        self._progress_callback = callback

    def cancel(self):
        """Cancel the setup process"""
        self._cancelled = True

    async def initialize_setup(self) -> SetupProgress:
        """
        Initialize the setup process and return initial progress.
        Creates the setup plan based on quick system scan.
        """
        session_id = str(uuid4())

        # Create setup steps
        steps = self._create_setup_steps()

        self._progress = SetupProgress(
            session_id=session_id,
            user_id=self.user_id,
            current_phase=SetupPhase.INITIALIZING,
            current_step_id=None,
            steps=steps,
            started_at=datetime.now(),
            updated_at=datetime.now(),
            completed_at=None,
            percent_complete=0,
            discoveries={},
        )

        # Quick scan to see what's available
        await self._quick_system_scan()

        return self._progress

    def _create_setup_steps(self) -> List[SetupStep]:
        """Create the list of setup steps"""
        return [
            # Local Discovery
            SetupStep(
                id="local_scan",
                phase=SetupPhase.DETECTING_LOCAL,
                title="Scan Local Files",
                description="Discover documents on your computer",
                priority=SetupPriority.RECOMMENDED,
            ),

            # Email Connection
            SetupStep(
                id="email_google",
                phase=SetupPhase.CONNECTING_EMAIL,
                title="Connect Gmail",
                description="Access your Gmail inbox",
                priority=SetupPriority.REQUIRED,
                requires_oauth=True,
                oauth_provider="google",
                oauth_scopes=["gmail.readonly", "gmail.send"],
            ),
            SetupStep(
                id="email_microsoft",
                phase=SetupPhase.CONNECTING_EMAIL,
                title="Connect Outlook",
                description="Access your Outlook inbox",
                priority=SetupPriority.OPTIONAL,
                requires_oauth=True,
                oauth_provider="microsoft",
                oauth_scopes=["Mail.Read", "Mail.Send"],
            ),

            # Calendar
            SetupStep(
                id="calendar_google",
                phase=SetupPhase.CONNECTING_CALENDAR,
                title="Connect Google Calendar",
                description="Access your calendar events",
                priority=SetupPriority.RECOMMENDED,
                requires_oauth=True,
                oauth_provider="google",
                oauth_scopes=["calendar.readonly", "calendar.events"],
            ),
            SetupStep(
                id="calendar_microsoft",
                phase=SetupPhase.CONNECTING_CALENDAR,
                title="Connect Outlook Calendar",
                description="Access your Outlook calendar",
                priority=SetupPriority.OPTIONAL,
                requires_oauth=True,
                oauth_provider="microsoft",
                oauth_scopes=["Calendars.Read", "Calendars.ReadWrite"],
            ),

            # Cloud Storage
            SetupStep(
                id="cloud_google_drive",
                phase=SetupPhase.DISCOVERING_CLOUD,
                title="Connect Google Drive",
                description="Discover files in your Google Drive",
                priority=SetupPriority.RECOMMENDED,
                requires_oauth=True,
                oauth_provider="google",
                oauth_scopes=["drive.readonly"],
            ),
            SetupStep(
                id="cloud_onedrive",
                phase=SetupPhase.DISCOVERING_CLOUD,
                title="Connect OneDrive",
                description="Discover files in your OneDrive",
                priority=SetupPriority.OPTIONAL,
                requires_oauth=True,
                oauth_provider="microsoft",
                oauth_scopes=["Files.Read"],
            ),
            SetupStep(
                id="cloud_dropbox",
                phase=SetupPhase.DISCOVERING_CLOUD,
                title="Connect Dropbox",
                description="Discover files in your Dropbox",
                priority=SetupPriority.OPTIONAL,
                requires_oauth=True,
                oauth_provider="dropbox",
                oauth_scopes=["files.content.read"],
            ),

            # Social Media
            SetupStep(
                id="social_linkedin",
                phase=SetupPhase.CONNECTING_SOCIAL,
                title="Connect LinkedIn",
                description="Import your professional profile",
                priority=SetupPriority.RECOMMENDED,
                requires_oauth=True,
                oauth_provider="linkedin",
                oauth_scopes=["openid", "profile", "email"],
            ),
            SetupStep(
                id="social_twitter",
                phase=SetupPhase.CONNECTING_SOCIAL,
                title="Connect Twitter/X",
                description="Understand your interests from tweets",
                priority=SetupPriority.OPTIONAL,
                requires_oauth=True,
                oauth_provider="twitter",
                oauth_scopes=["tweet.read", "users.read"],
            ),
            SetupStep(
                id="social_meta",
                phase=SetupPhase.CONNECTING_SOCIAL,
                title="Connect Facebook/Instagram",
                description="Import your social presence",
                priority=SetupPriority.OPTIONAL,
                requires_oauth=True,
                oauth_provider="meta",
                oauth_scopes=["email", "public_profile"],
            ),

            # Document Indexing
            SetupStep(
                id="index_documents",
                phase=SetupPhase.INDEXING_DOCUMENTS,
                title="Index Documents",
                description="Process and index your documents for search",
                priority=SetupPriority.RECOMMENDED,
            ),

            # Profile Building
            SetupStep(
                id="build_profile",
                phase=SetupPhase.BUILDING_PROFILE,
                title="Build Your Profile",
                description="Create your Digital Twin foundation",
                priority=SetupPriority.REQUIRED,
            ),
        ]

    async def _quick_system_scan(self):
        """Quick scan to see what data sources are available"""
        discovery = LocalDiscoveryService(
            max_file_size_mb=50,
            include_hidden=False,
            compute_hashes=False,
        )

        quick_result = await discovery.quick_scan()

        self._progress.discoveries["local"] = {
            "available": True,
            "directories": quick_result.get("directories_available", []),
            "email_clients": quick_result.get("email_clients_detected", []),
            "calendar_sources": quick_result.get("calendar_sources_detected", []),
            "platform": quick_result.get("platform"),
        }

        self._update_progress()

    async def execute_step(
        self,
        step_id: str,
        oauth_tokens: Optional[Dict[str, str]] = None
    ) -> SetupStep:
        """
        Execute a specific setup step.

        Args:
            step_id: The step ID to execute
            oauth_tokens: OAuth tokens if step requires OAuth

        Returns:
            Updated step with results
        """
        step = next((s for s in self._progress.steps if s.id == step_id), None)
        if not step:
            raise ValueError(f"Step not found: {step_id}")

        step.status = "in_progress"
        self._progress.current_step_id = step_id
        self._progress.current_phase = step.phase
        self._update_progress()

        try:
            # Execute based on step type
            if step_id == "local_scan":
                result = await self._execute_local_scan()
            elif step_id.startswith("email_"):
                result = await self._execute_email_connection(step, oauth_tokens)
            elif step_id.startswith("calendar_"):
                result = await self._execute_calendar_connection(step, oauth_tokens)
            elif step_id.startswith("cloud_"):
                result = await self._execute_cloud_discovery(step, oauth_tokens)
            elif step_id.startswith("social_"):
                result = await self._execute_social_ingestion(step, oauth_tokens)
            elif step_id == "index_documents":
                result = await self._execute_document_indexing()
            elif step_id == "build_profile":
                result = await self._execute_profile_building()
            else:
                result = {"status": "unknown_step"}

            step.status = "completed"
            step.result = result

        except Exception as e:
            logger.error(f"Step {step_id} failed: {e}", exc_info=True)
            step.status = "failed"
            step.error = str(e)

        self._update_progress()
        return step

    async def skip_step(self, step_id: str) -> SetupStep:
        """Skip a step"""
        step = next((s for s in self._progress.steps if s.id == step_id), None)
        if not step:
            raise ValueError(f"Step not found: {step_id}")

        step.status = "skipped"
        self._update_progress()
        return step

    async def _execute_local_scan(self) -> Dict:
        """Execute local file discovery"""
        discovery = LocalDiscoveryService(
            max_file_size_mb=100,
            include_hidden=False,
            compute_hashes=False,
            categories_filter={
                FileCategory.DOCUMENT,
                FileCategory.PDF,
                FileCategory.SPREADSHEET,
                FileCategory.PRESENTATION,
                FileCategory.NOTE,
            }
        )

        result = await discovery.run_full_discovery()

        self._progress.discoveries["local_files"] = {
            "files_found": result.files_found,
            "by_category": result.files_by_category,
            "total_size_bytes": result.total_size_bytes,
            "directories_scanned": result.directories_scanned,
        }

        return result.to_dict()

    async def _execute_email_connection(
        self,
        step: SetupStep,
        oauth_tokens: Optional[Dict]
    ) -> Dict:
        """Connect email account"""
        if not oauth_tokens or "access_token" not in oauth_tokens:
            raise ValueError("OAuth token required for email connection")

        provider = step.oauth_provider

        # Store the OAuth connection (this would typically update the database)
        # For now, return success
        return {
            "provider": provider,
            "connected": True,
            "email": oauth_tokens.get("email", "unknown"),
        }

    async def _execute_calendar_connection(
        self,
        step: SetupStep,
        oauth_tokens: Optional[Dict]
    ) -> Dict:
        """Connect calendar"""
        if not oauth_tokens or "access_token" not in oauth_tokens:
            raise ValueError("OAuth token required for calendar connection")

        provider = step.oauth_provider

        return {
            "provider": provider,
            "connected": True,
        }

    async def _execute_cloud_discovery(
        self,
        step: SetupStep,
        oauth_tokens: Optional[Dict]
    ) -> Dict:
        """Discover cloud storage files"""
        if not oauth_tokens or "access_token" not in oauth_tokens:
            raise ValueError("OAuth token required for cloud discovery")

        provider_map = {
            "google": CloudProvider.GOOGLE_DRIVE,
            "microsoft": CloudProvider.ONEDRIVE,
            "dropbox": CloudProvider.DROPBOX,
        }

        provider = provider_map.get(step.oauth_provider)
        if not provider:
            raise ValueError(f"Unknown cloud provider: {step.oauth_provider}")

        async with CloudStorageDiscovery(
            access_token=oauth_tokens["access_token"],
            provider=provider,
            max_results=500,
        ) as discovery:
            result = await discovery.discover_all()

        self._progress.discoveries[f"cloud_{step.oauth_provider}"] = {
            "files_found": result.files_found,
            "folders_found": result.folders_found,
            "total_size_bytes": result.total_size_bytes,
        }

        return result.to_dict()

    async def _execute_social_ingestion(
        self,
        step: SetupStep,
        oauth_tokens: Optional[Dict]
    ) -> Dict:
        """Ingest social media history"""
        if not oauth_tokens or "access_token" not in oauth_tokens:
            raise ValueError("OAuth token required for social ingestion")

        platform_map = {
            "linkedin": SocialPlatform.LINKEDIN,
            "twitter": SocialPlatform.TWITTER,
            "meta": SocialPlatform.FACEBOOK,
        }

        platform = platform_map.get(step.oauth_provider)
        if not platform:
            raise ValueError(f"Unknown social platform: {step.oauth_provider}")

        async with SocialHistoryIngestion(
            access_token=oauth_tokens["access_token"],
            platform=platform,
            max_posts=100,
        ) as ingestion:
            result = await ingestion.ingest()

        self._progress.discoveries[f"social_{step.oauth_provider}"] = result.summary

        return result.to_dict()

    async def _execute_document_indexing(self) -> Dict:
        """Index discovered documents for RAG"""
        # This would integrate with the DocumentProcessor and RAG service
        # For now, return a placeholder

        total_indexed = 0

        # Count files from local discovery
        if "local_files" in self._progress.discoveries:
            total_indexed += self._progress.discoveries["local_files"].get("files_found", 0)

        # Count files from cloud discovery
        for key, value in self._progress.discoveries.items():
            if key.startswith("cloud_") and isinstance(value, dict):
                total_indexed += value.get("files_found", 0)

        return {
            "documents_indexed": total_indexed,
            "status": "completed",
        }

    async def _execute_profile_building(self) -> Dict:
        """Build the initial Digital Twin profile"""
        # Aggregate all discoveries into a profile summary

        profile_data = {
            "sources_connected": [],
            "documents_discovered": 0,
            "social_profiles": [],
            "generated_at": datetime.now().isoformat(),
        }

        # Local files
        if "local_files" in self._progress.discoveries:
            local = self._progress.discoveries["local_files"]
            profile_data["documents_discovered"] += local.get("files_found", 0)
            profile_data["sources_connected"].append("local_files")

        # Cloud storage
        for key in ["cloud_google", "cloud_microsoft", "cloud_dropbox"]:
            if key in self._progress.discoveries:
                cloud = self._progress.discoveries[key]
                profile_data["documents_discovered"] += cloud.get("files_found", 0)
                profile_data["sources_connected"].append(key)

        # Social profiles
        for key in ["social_linkedin", "social_twitter", "social_meta"]:
            if key in self._progress.discoveries:
                social = self._progress.discoveries[key]
                profile_data["social_profiles"].append({
                    "platform": key.replace("social_", ""),
                    "summary": social,
                })
                profile_data["sources_connected"].append(key)

        return profile_data

    def _update_progress(self):
        """Update progress and notify callback"""
        if not self._progress:
            return

        # Calculate percent complete
        total_steps = len(self._progress.steps)
        completed_steps = sum(1 for s in self._progress.steps if s.status in ["completed", "skipped"])
        self._progress.percent_complete = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

        self._progress.updated_at = datetime.now()

        # Check if all required steps are done
        required_incomplete = [
            s for s in self._progress.steps
            if s.priority == SetupPriority.REQUIRED and s.status not in ["completed", "skipped"]
        ]

        if not required_incomplete and self._progress.percent_complete >= 50:
            self._progress.current_phase = SetupPhase.COMPLETED
            self._progress.completed_at = datetime.now()

        # Notify callback
        if self._progress_callback:
            try:
                self._progress_callback(self._progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def get_progress(self) -> Optional[SetupProgress]:
        """Get current progress"""
        return self._progress

    def get_required_oauth_providers(self) -> List[str]:
        """Get list of OAuth providers that still need connection"""
        providers = set()
        for step in self._progress.steps if self._progress else []:
            if step.requires_oauth and step.status == "pending":
                providers.add(step.oauth_provider)
        return list(providers)

    def get_next_step(self) -> Optional[SetupStep]:
        """Get the next pending step"""
        if not self._progress:
            return None

        # Prioritize required steps
        for step in self._progress.steps:
            if step.status == "pending" and step.priority == SetupPriority.REQUIRED:
                return step

        # Then recommended
        for step in self._progress.steps:
            if step.status == "pending" and step.priority == SetupPriority.RECOMMENDED:
                return step

        # Then optional
        for step in self._progress.steps:
            if step.status == "pending":
                return step

        return None


# Factory function
async def create_setup_session(
    db: AsyncSession,
    user_id: str,
    tenant_id: str
) -> AutoSetupOrchestrator:
    """
    Create a new setup session for a user.

    Args:
        db: Database session
        user_id: User ID
        tenant_id: Tenant ID

    Returns:
        Initialized AutoSetupOrchestrator
    """
    orchestrator = AutoSetupOrchestrator(db, user_id, tenant_id)
    await orchestrator.initialize_setup()
    return orchestrator
