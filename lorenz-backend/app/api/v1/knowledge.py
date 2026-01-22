"""
LORENZ SaaS - Knowledge Base (MNEME) API Routes
=================================================

Endpoints for managing the MNEME knowledge base.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.knowledge import MNEME, KnowledgeEntry, create_mneme

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


# ============================================================================
# SCHEMAS
# ============================================================================

class KnowledgeEntryCreate(BaseModel):
    """Create a knowledge entry"""
    category: str  # pattern, workflow, fact, preference, skill_memory
    title: str
    content: str
    context: Dict[str, Any] = {}
    confidence: float = 1.0
    source: str = ""
    tags: List[str] = []
    related_skills: List[str] = []


class KnowledgeEntryUpdate(BaseModel):
    """Update a knowledge entry"""
    title: Optional[str] = None
    content: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None


class KnowledgeEntryResponse(BaseModel):
    """Knowledge entry response"""
    id: str
    category: str
    title: str
    content: str
    context: Dict[str, Any]
    access_count: int
    confidence: float
    source: str
    tags: List[str]
    related_skills: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class KnowledgeSearchRequest(BaseModel):
    """Search request"""
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    semantic: bool = False
    limit: int = 50


class EmergentSkillCreate(BaseModel):
    """Create an emergent skill"""
    name: str
    description: str = ""
    description_it: str = ""
    trigger_patterns: List[str]
    workflow_steps: List[Dict[str, Any]]
    category: str = "custom"
    tags: List[str] = []


class EmergentSkillResponse(BaseModel):
    """Emergent skill response"""
    id: str
    name: str
    description: str
    description_it: str
    trigger_patterns: List[str]
    workflow_steps: List[Dict[str, Any]]
    category: str
    use_count: int
    success_rate: float
    enabled: bool
    tags: List[str]


class MNEMEStatsResponse(BaseModel):
    """MNEME statistics"""
    total_entries: int
    by_category: Dict[str, int]
    total_skills: int
    enabled_skills: int
    recent_activity: List[Dict[str, Any]]


# ============================================================================
# KNOWLEDGE ENDPOINTS
# ============================================================================

@router.post("/entries", response_model=KnowledgeEntryResponse)
async def create_knowledge_entry(
    entry: KnowledgeEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new knowledge entry

    Categories:
    - **pattern**: Learned interaction patterns
    - **workflow**: Discovered workflow combinations
    - **fact**: Facts about user/context
    - **preference**: User preferences
    - **skill_memory**: Memories from skill execution
    """
    mneme = create_mneme(db, current_user.id)

    knowledge = KnowledgeEntry(
        category=entry.category,
        title=entry.title,
        content=entry.content,
        context=entry.context,
        confidence=entry.confidence,
        source=entry.source,
        tags=entry.tags,
        related_skills=entry.related_skills
    )

    entry_id = await mneme.add_knowledge(knowledge)
    if not entry_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create knowledge entry"
        )

    # Fetch the created entry
    created = await mneme.get_knowledge(UUID(entry_id))
    return created.to_dict()


@router.get("/entries", response_model=List[KnowledgeEntryResponse])
async def list_knowledge_entries(
    category: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List knowledge entries"""
    mneme = create_mneme(db, current_user.id)
    entries = await mneme.search_knowledge(category=category, limit=limit)
    return [e.to_dict() for e in entries]


@router.post("/entries/search", response_model=List[KnowledgeEntryResponse])
async def search_knowledge(
    search: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search knowledge base

    Supports both keyword and semantic search.
    """
    mneme = create_mneme(db, current_user.id)

    entries = await mneme.search_knowledge(
        query=search.query,
        category=search.category,
        tags=search.tags,
        limit=search.limit,
        semantic=search.semantic
    )

    return [e.to_dict() for e in entries]


@router.get("/entries/{entry_id}", response_model=KnowledgeEntryResponse)
async def get_knowledge_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific knowledge entry"""
    mneme = create_mneme(db, current_user.id)
    entry = await mneme.get_knowledge(entry_id)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found"
        )

    return entry.to_dict()


@router.patch("/entries/{entry_id}", response_model=KnowledgeEntryResponse)
async def update_knowledge_entry(
    entry_id: UUID,
    updates: KnowledgeEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a knowledge entry"""
    mneme = create_mneme(db, current_user.id)

    # Build updates dict excluding None values
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )

    success = await mneme.update_knowledge(entry_id, update_dict)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update knowledge entry"
        )

    entry = await mneme.get_knowledge(entry_id)
    return entry.to_dict()


@router.delete("/entries/{entry_id}")
async def delete_knowledge_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge entry"""
    mneme = create_mneme(db, current_user.id)
    success = await mneme.delete_knowledge(entry_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete knowledge entry"
        )

    return {"status": "deleted", "id": str(entry_id)}


# ============================================================================
# EMERGENT SKILLS ENDPOINTS
# ============================================================================

@router.post("/skills", response_model=EmergentSkillResponse)
async def create_emergent_skill(
    skill: EmergentSkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new emergent skill

    Emergent skills are user-specific automations that LORENZ
    learns from repeated interactions.
    """
    from app.services.knowledge.mneme import EmergentSkill

    mneme = create_mneme(db, current_user.id)

    emergent_skill = EmergentSkill(
        name=skill.name,
        description=skill.description,
        description_it=skill.description_it,
        trigger_patterns=skill.trigger_patterns,
        workflow_steps=skill.workflow_steps,
        category=skill.category,
        tags=skill.tags,
        created_from="api"
    )

    skill_id = await mneme.add_emergent_skill(emergent_skill)
    if not skill_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create emergent skill"
        )

    # Return the created skill info
    emergent_skill.id = skill_id
    return emergent_skill.to_dict()


@router.get("/skills", response_model=List[EmergentSkillResponse])
async def list_emergent_skills(
    enabled_only: bool = True,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's emergent skills"""
    mneme = create_mneme(db, current_user.id)
    skills = await mneme.get_emergent_skills(enabled_only=enabled_only, category=category)
    return [s.to_dict() for s in skills]


# ============================================================================
# STATISTICS & HISTORY
# ============================================================================

@router.get("/stats", response_model=MNEMEStatsResponse)
async def get_mneme_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get MNEME statistics"""
    mneme = create_mneme(db, current_user.id)
    return await mneme.get_stats()


@router.get("/history")
async def get_learning_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get learning history"""
    mneme = create_mneme(db, current_user.id)
    history = await mneme.get_learning_history(limit=limit)
    return {"history": history, "total": len(history)}


# ============================================================================
# QUICK ACTIONS
# ============================================================================

@router.post("/remember")
async def quick_remember(
    title: str,
    content: str,
    category: str = "fact",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick action to remember something

    This is a shortcut for adding knowledge entries.
    """
    mneme = create_mneme(db, current_user.id)

    knowledge = KnowledgeEntry(
        category=category,
        title=title,
        content=content,
        source="quick_remember"
    )

    entry_id = await mneme.add_knowledge(knowledge)
    if entry_id:
        return {"status": "remembered", "id": entry_id, "title": title}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remember"
        )


@router.post("/learn-pattern")
async def learn_pattern(
    pattern_name: str,
    trigger_phrases: List[str],
    response_template: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Teach LORENZ a new pattern

    Example:
    - pattern_name: "morning_greeting"
    - trigger_phrases: ["buongiorno", "good morning"]
    - response_template: "Buongiorno! Come posso aiutarti oggi?"
    """
    mneme = create_mneme(db, current_user.id)

    knowledge = KnowledgeEntry(
        category="pattern",
        title=pattern_name,
        content=response_template,
        context={"trigger_phrases": trigger_phrases},
        source="learn_pattern"
    )

    entry_id = await mneme.add_knowledge(knowledge)
    if entry_id:
        return {
            "status": "learned",
            "id": entry_id,
            "pattern": pattern_name,
            "triggers": trigger_phrases
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to learn pattern"
        )
