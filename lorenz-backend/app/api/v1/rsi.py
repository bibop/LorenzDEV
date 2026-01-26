"""
LORENZ SaaS - RSI API Routes
==============================

Endpoints for Recursive Self Improvement (RSI) subsystem.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user, require_admin_role
from app.models import User
from app.services.rsi import run_pattern_mining

router = APIRouter(prefix="/rsi", tags=["RSI"])


class PatternMiningResponse(BaseModel):
    """Response from pattern mining"""
    proposals_created: int
    patterns_found: List[Dict[str, Any]]


class TelemetryEvent(BaseModel):
    """User feedback telemetry event"""
    skill_run_id: UUID
    score: int  # 1-5
    comment: str | None = None


@router.post("/mine-patterns", response_model=PatternMiningResponse)
async def trigger_pattern_mining(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger pattern mining for the current user.
    This analyzes recent skill usage to propose emergent skills.
    """
    proposals = await run_pattern_mining(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )
    
    return PatternMiningResponse(
        proposals_created=len(proposals),
        patterns_found=[
            p.pattern_data for p in proposals if p.pattern_data
        ]
    )


@router.post("/telemetry/feedback")
async def submit_feedback(
    event: TelemetryEvent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a skill run (used for RSI learning).
    """
    from sqlalchemy import select, update
    from app.models import SkillRun
    
    # Verify ownership
    query = select(SkillRun).where(
        SkillRun.id == event.skill_run_id,
        SkillRun.user_id == current_user.id
    )
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill run not found"
        )
    
    # Update feedback
    run.user_feedback = {
        "score": event.score,
        "comment": event.comment,
        "submitted_at": str(__import__("datetime").datetime.utcnow())
    }
    
    await db.commit()
    
    return {"message": "Feedback recorded"}


@router.get("/stats")
async def get_rsi_stats(
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get RSI statistics (admin only).
    """
    from sqlalchemy import select, func
    from app.models import SkillProposal, SkillRun
    
    # Count proposals
    proposals_query = select(func.count(SkillProposal.id)).where(
        SkillProposal.tenant_id == current_user.tenant_id
    )
    result = await db.execute(proposals_query)
    total_proposals = result.scalar() or 0
    
    # Count by status
    status_query = select(
        SkillProposal.status,
        func.count(SkillProposal.id)
    ).where(
        SkillProposal.tenant_id == current_user.tenant_id
    ).group_by(SkillProposal.status)
    
    result = await db.execute(status_query)
    by_status = {row[0]: row[1] for row in result.all()}
    
    # Count runs with feedback
    feedback_query = select(func.count(SkillRun.id)).where(
        SkillRun.tenant_id == current_user.tenant_id,
        SkillRun.user_feedback.isnot(None)
    )
    result = await db.execute(feedback_query)
    runs_with_feedback = result.scalar() or 0
    
    return {
        "total_proposals": total_proposals,
        "proposals_by_status": by_status,
        "runs_with_feedback": runs_with_feedback
    }
