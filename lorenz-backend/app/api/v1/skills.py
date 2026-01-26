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
from app.models import User, Skill, SkillProposal, SkillType, SkillStatus
from sqlalchemy import select, update
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


# --- Unified Registry Schemas ---

class SkillProposalCreate(BaseModel):
    """Schema to propose a new emergent skill"""
    suggested_name: str
    reasoning: str
    confidence: float
    proposed_schema: Dict[str, Any]
    pattern_data: Optional[Dict[str, Any]] = None


class SkillProposalResponse(BaseModel):
    """Response for a skill proposal"""
    id: UUID
    suggested_name: str
    reasoning: str
    confidence: float
    status: str
    proposed_schema: Dict[str, Any]
    created_at: datetime


class SkillUnifiedResponse(BaseModel):
    """Response for a unified skill"""
    id: UUID
    name: str
    description: str
    skill_type: SkillType
    status: SkillStatus
    category: Optional[str]
    icon: Optional[str]
    version: str
    tool_schema: Dict[str, Any]
    use_count: float
    success_rate: float
    avg_latency_ms: float


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


# ============================================================================
# EMERGENT SKILLS REGISTRY (Management)
# ============================================================================

@router.post("/emergent/propose", response_model=SkillProposalResponse, status_code=status.HTTP_201_CREATED)
async def propose_emergent_skill(
    proposal: SkillProposalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Propose a new emergent skill (usually called by the RSI/Pattern Miner).
    """
    new_proposal = SkillProposal(
        tenant_id=current_user.tenant_id,
        suggested_name=proposal.suggested_name,
        reasoning=proposal.reasoning,
        confidence=proposal.confidence,
        proposed_schema=proposal.proposed_schema,
        pattern_data=proposal.pattern_data,
        status="pending"
    )
    db.add(new_proposal)
    await db.commit()
    await db.refresh(new_proposal)
    return new_proposal


@router.get("/emergent/proposals", response_model=List[SkillProposalResponse])
async def list_proposals(
    status: str = "pending",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List emergent skill proposals for review"""
    result = await db.execute(
        select(SkillProposal).where(
            SkillProposal.tenant_id == current_user.tenant_id,
            SkillProposal.status == status
        )
    )
    return result.scalars().all()


@router.post("/emergent/{proposal_id}/approve", response_model=SkillUnifiedResponse)
async def approve_skill_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a proposal and promote it to an active Skill.
    """
    # 1. Get proposal
    proposal_res = await db.execute(
        select(SkillProposal).where(
            SkillProposal.id == proposal_id,
            SkillProposal.tenant_id == current_user.tenant_id
        )
    )
    proposal = proposal_res.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.status}")

    # 2. Update proposal status
    proposal.status = "approved"
    proposal.reviewed_by = current_user.id

    # 3. Create actual Skill
    new_skill = Skill(
        tenant_id=current_user.tenant_id,
        name=proposal.suggested_name,
        description=f"Emergent skill learned from pattern: {proposal.suggested_name}",
        skill_type=SkillType.EMERGENT,
        status=SkillStatus.ACTIVE,
        tool_schema=proposal.proposed_schema,
        implementation={"pattern_data": proposal.pattern_data},
        category="emergent"
    )
    db.add(new_skill)
    
    await db.commit()
    await db.refresh(new_skill)
    return new_skill


@router.post("/emergent/{proposal_id}/reject")
async def reject_skill_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject an emergent skill proposal"""
    await db.execute(
        update(SkillProposal)
        .where(
            SkillProposal.id == proposal_id,
            SkillProposal.tenant_id == current_user.tenant_id
        )
        .values(status="rejected", reviewed_by=current_user.id)
    )
    await db.commit()
    return {"message": "Proposal rejected"}
