"""
LORENZ SaaS - Skills API Routes
================================

Endpoints for skill management and execution.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.skills import (
    SkillsManager,
    create_skills_manager,
    SkillCategory,
    SkillType
)

router = APIRouter(prefix="/skills", tags=["Skills"])


# ============================================================================
# SCHEMAS
# ============================================================================

class SkillExecuteRequest(BaseModel):
    """Request to execute a skill"""
    skill_name: str
    parameters: Dict[str, Any] = {}


class SkillExecuteResponse(BaseModel):
    """Response from skill execution"""
    success: bool
    skill_name: str
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    artifacts: List[str] = []
    execution_time_ms: int = 0


class SkillInfo(BaseModel):
    """Skill information"""
    id: str
    name: str
    description: str
    description_it: str
    examples: List[str]
    enabled: bool
    requires: List[str]
    type: str
    category: str
    icon: str
    estimated_cost: float
    metadata: Dict[str, Any]


class SkillListResponse(BaseModel):
    """List of skills"""
    skills: List[SkillInfo]
    total: int
    enabled: int


class SkillCategoryInfo(BaseModel):
    """Category information"""
    name: str
    total: int
    enabled: int
    skills: List[str]


class SkillStatsResponse(BaseModel):
    """Skill execution statistics"""
    total_executions: int
    by_skill: Dict[str, int]
    by_category: Dict[str, int]
    total_cost_usd: float
    skill_count: int
    enabled_count: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=SkillListResponse)
async def list_skills(
    enabled_only: bool = False,
    category: Optional[str] = None,
    skill_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available skills

    - **enabled_only**: Only return enabled skills
    - **category**: Filter by category (creative, research, technical, etc.)
    - **skill_type**: Filter by type (god, emergent)
    """
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    # Convert string to enum if provided
    cat_enum = None
    if category:
        try:
            cat_enum = SkillCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}"
            )

    type_enum = None
    if skill_type:
        try:
            type_enum = SkillType(skill_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid skill type: {skill_type}"
            )

    skills = manager.list_skills(
        enabled_only=enabled_only,
        category=cat_enum,
        skill_type=type_enum
    )

    enabled_count = sum(1 for s in skills if s["enabled"])

    return SkillListResponse(
        skills=skills,
        total=len(skills),
        enabled=enabled_count
    )


@router.get("/categories", response_model=List[SkillCategoryInfo])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get skill categories with counts"""
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return manager.get_categories()


@router.get("/stats", response_model=SkillStatsResponse)
async def get_skill_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get skill execution statistics"""
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return manager.get_stats()


@router.get("/{skill_name}", response_model=SkillInfo)
async def get_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific skill"""
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    skill = manager.get_skill(skill_name)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {skill_name}"
        )

    return skill.get_info()


@router.post("/execute", response_model=SkillExecuteResponse)
async def execute_skill(
    request: SkillExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a skill

    Example request:
    ```json
    {
        "skill_name": "image_generation",
        "parameters": {
            "prompt": "A futuristic city at sunset",
            "size": "1024x1024"
        }
    }
    ```
    """
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    skill = manager.get_skill(request.skill_name)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {request.skill_name}"
        )

    if not skill.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill is disabled: {request.skill_name}. Check API key configuration."
        )

    result = await manager.execute_skill(
        skill_name=request.skill_name,
        **request.parameters
    )

    return SkillExecuteResponse(
        success=result.success,
        skill_name=result.skill_name,
        message=result.message,
        data=result.data,
        error=result.error,
        artifacts=result.artifacts,
        execution_time_ms=result.execution_time_ms
    )


@router.post("/auto-execute", response_model=SkillExecuteResponse)
async def auto_execute_skill(
    query: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Automatically find and execute the best skill for a query

    This endpoint analyzes the user's query and routes it to the
    most appropriate skill.

    Example: "Generate an image of a cat" would route to image_generation
    """
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    result = await manager.auto_execute(query)

    return SkillExecuteResponse(
        success=result.success,
        skill_name=result.skill_name,
        message=result.message,
        data=result.data,
        error=result.error,
        artifacts=result.artifacts,
        execution_time_ms=result.execution_time_ms
    )


# ============================================================================
# SPECIFIC SKILL SHORTCUTS
# ============================================================================

class ImageGenerationRequest(BaseModel):
    """Request for image generation"""
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"


@router.post("/generate-image", response_model=SkillExecuteResponse)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate an image using DALL-E 3"""
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    result = await manager.execute_skill(
        "image_generation",
        prompt=request.prompt,
        size=request.size,
        quality=request.quality,
        style=request.style
    )

    return SkillExecuteResponse(
        success=result.success,
        skill_name=result.skill_name,
        message=result.message,
        data=result.data,
        error=result.error,
        artifacts=result.artifacts,
        execution_time_ms=result.execution_time_ms
    )


class WebSearchRequest(BaseModel):
    """Request for web search"""
    query: str
    detailed: bool = False


@router.post("/web-search", response_model=SkillExecuteResponse)
async def web_search(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search the web using Perplexity"""
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    result = await manager.execute_skill(
        "web_search",
        query=request.query,
        detailed=request.detailed
    )

    return SkillExecuteResponse(
        success=result.success,
        skill_name=result.skill_name,
        message=result.message,
        data=result.data,
        error=result.error,
        artifacts=result.artifacts,
        execution_time_ms=result.execution_time_ms
    )


class EmailDraftRequest(BaseModel):
    """Request for email draft"""
    context: str
    tone: str = "professional"
    recipient: Optional[str] = None
    subject_hint: Optional[str] = None
    language: str = "en"


@router.post("/draft-email", response_model=SkillExecuteResponse)
async def draft_email(
    request: EmailDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Draft a professional email"""
    manager = create_skills_manager(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    result = await manager.execute_skill(
        "email_draft",
        context=request.context,
        tone=request.tone,
        recipient=request.recipient,
        subject_hint=request.subject_hint,
        language=request.language
    )

    return SkillExecuteResponse(
        success=result.success,
        skill_name=result.skill_name,
        message=result.message,
        data=result.data,
        error=result.error,
        artifacts=result.artifacts,
        execution_time_ms=result.execution_time_ms
    )
