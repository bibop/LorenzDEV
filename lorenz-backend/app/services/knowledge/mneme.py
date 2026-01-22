"""
LORENZ SaaS - MNEME Knowledge Base Service
===========================================

Multi-tenant persistent memory system adapted from lorenz_skills.py.

Features:
- Knowledge storage (patterns, workflows, facts, preferences)
- Emergent skill tracking
- Learning history
- Semantic search via Qdrant
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete

from .models import KnowledgeEntryModel, EmergentSkillModel, LearningHistoryModel

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

class KnowledgeCategory(Enum):
    """Categories for knowledge entries"""
    PATTERN = "pattern"       # Learned interaction patterns
    WORKFLOW = "workflow"     # Discovered workflow combinations
    FACT = "fact"            # Facts about user/context
    PREFERENCE = "preference" # User preferences
    SKILL_MEMORY = "skill_memory"  # Memories from skill execution


@dataclass
class KnowledgeEntry:
    """Single entry in the MNEME knowledge base"""
    category: str
    title: str
    content: str
    id: Optional[str] = None
    context: Dict = field(default_factory=dict)
    access_count: int = 0
    confidence: float = 1.0
    source: str = ""
    tags: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EmergentSkill:
    """User-learned skill definition"""
    name: str
    trigger_patterns: List[str]
    workflow_steps: List[Dict]
    id: Optional[str] = None
    description: str = ""
    description_it: str = ""
    category: str = "custom"
    use_count: int = 0
    success_rate: float = 1.0
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    created_from: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# MNEME SERVICE
# ============================================================================

class MNEME:
    """
    MNEME - Multi-tenant Knowledge Base for LORENZ

    Sistema di memoria persistente che archivia:
    - Patterns di successo nelle interazioni
    - Workflow emergenti scoperti
    - Fatti e preferenze dell'utente
    - Conoscenza appresa dalle conversazioni

    Ispezionabile e modificabile dal pannello di controllo.
    """

    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self._qdrant_client = None
        self._encoder = None

    # -------------------------------------------------------------------------
    # Knowledge Operations
    # -------------------------------------------------------------------------

    async def add_knowledge(self, entry: KnowledgeEntry) -> Optional[str]:
        """
        Add knowledge entry to MNEME

        Args:
            entry: Knowledge entry to add

        Returns:
            Entry ID or None on failure
        """
        try:
            model = KnowledgeEntryModel(
                user_id=self.user_id,
                category=entry.category,
                title=entry.title,
                content=entry.content,
                context=entry.context,
                confidence=entry.confidence,
                source=entry.source,
                tags=entry.tags,
                related_skills=entry.related_skills
            )

            self.db.add(model)
            await self.db.commit()
            await self.db.refresh(model)

            # Optionally add to Qdrant for semantic search
            await self._index_knowledge(model)

            logger.info(f"MNEME: Added knowledge '{entry.title}'")
            return str(model.id)

        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            await self.db.rollback()
            return None

    async def get_knowledge(self, entry_id: UUID) -> Optional[KnowledgeEntry]:
        """Get knowledge entry by ID"""
        try:
            query = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.id == entry_id,
                KnowledgeEntryModel.user_id == self.user_id
            )
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()

            if model:
                # Update access count
                model.access_count += 1
                self.db.add(model)
                await self.db.commit()

                return KnowledgeEntry(
                    id=str(model.id),
                    category=model.category,
                    title=model.title,
                    content=model.content,
                    context=model.context or {},
                    access_count=model.access_count,
                    confidence=model.confidence,
                    source=model.source,
                    tags=model.tags or [],
                    related_skills=model.related_skills or [],
                    created_at=model.created_at.isoformat() if model.created_at else None,
                    updated_at=model.updated_at.isoformat() if model.updated_at else None
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get knowledge: {e}")
            return None

    async def search_knowledge(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        semantic: bool = False
    ) -> List[KnowledgeEntry]:
        """
        Search knowledge base

        Args:
            query: Text query for search
            category: Filter by category
            tags: Filter by tags
            limit: Max results
            semantic: Use semantic search (Qdrant)

        Returns:
            List of matching entries
        """
        try:
            # Semantic search via Qdrant
            if semantic and query:
                return await self._semantic_search(query, category, limit)

            # SQL-based search
            sql_query = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.user_id == self.user_id
            )

            if query:
                sql_query = sql_query.where(
                    (KnowledgeEntryModel.title.ilike(f"%{query}%")) |
                    (KnowledgeEntryModel.content.ilike(f"%{query}%"))
                )

            if category:
                sql_query = sql_query.where(KnowledgeEntryModel.category == category)

            sql_query = sql_query.order_by(
                KnowledgeEntryModel.access_count.desc(),
                KnowledgeEntryModel.updated_at.desc()
            ).limit(limit)

            result = await self.db.execute(sql_query)
            models = result.scalars().all()

            return [
                KnowledgeEntry(
                    id=str(m.id),
                    category=m.category,
                    title=m.title,
                    content=m.content,
                    context=m.context or {},
                    access_count=m.access_count,
                    confidence=m.confidence,
                    source=m.source,
                    tags=m.tags or [],
                    related_skills=m.related_skills or [],
                    created_at=m.created_at.isoformat() if m.created_at else None,
                    updated_at=m.updated_at.isoformat() if m.updated_at else None
                )
                for m in models
            ]

        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []

    async def update_knowledge(self, entry_id: UUID, updates: Dict) -> bool:
        """Update knowledge entry"""
        try:
            query = update(KnowledgeEntryModel).where(
                KnowledgeEntryModel.id == entry_id,
                KnowledgeEntryModel.user_id == self.user_id
            ).values(**updates)

            await self.db.execute(query)
            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update knowledge: {e}")
            await self.db.rollback()
            return False

    async def delete_knowledge(self, entry_id: UUID) -> bool:
        """Delete knowledge entry"""
        try:
            query = delete(KnowledgeEntryModel).where(
                KnowledgeEntryModel.id == entry_id,
                KnowledgeEntryModel.user_id == self.user_id
            )

            await self.db.execute(query)
            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to delete knowledge: {e}")
            await self.db.rollback()
            return False

    # -------------------------------------------------------------------------
    # Emergent Skills
    # -------------------------------------------------------------------------

    async def add_emergent_skill(self, skill: EmergentSkill) -> Optional[str]:
        """Add a learned emergent skill"""
        try:
            model = EmergentSkillModel(
                user_id=self.user_id,
                name=skill.name,
                description=skill.description,
                description_it=skill.description_it,
                trigger_patterns=skill.trigger_patterns,
                workflow_steps=skill.workflow_steps,
                category=skill.category,
                tags=skill.tags,
                created_from=skill.created_from
            )

            self.db.add(model)
            await self.db.commit()
            await self.db.refresh(model)

            # Log learning event
            await self._log_learning(
                event_type="skill_created",
                skill_name=skill.name,
                learned_pattern=f"Created from: {skill.created_from}"
            )

            logger.info(f"MNEME: Added emergent skill '{skill.name}'")
            return str(model.id)

        except Exception as e:
            logger.error(f"Failed to add emergent skill: {e}")
            await self.db.rollback()
            return None

    async def get_emergent_skills(
        self,
        enabled_only: bool = True,
        category: Optional[str] = None
    ) -> List[EmergentSkill]:
        """Get user's emergent skills"""
        try:
            query = select(EmergentSkillModel).where(
                EmergentSkillModel.user_id == self.user_id
            )

            if enabled_only:
                query = query.where(EmergentSkillModel.enabled == True)

            if category:
                query = query.where(EmergentSkillModel.category == category)

            query = query.order_by(EmergentSkillModel.use_count.desc())

            result = await self.db.execute(query)
            models = result.scalars().all()

            return [
                EmergentSkill(
                    id=str(m.id),
                    name=m.name,
                    description=m.description,
                    description_it=m.description_it,
                    trigger_patterns=m.trigger_patterns or [],
                    workflow_steps=m.workflow_steps or [],
                    category=m.category,
                    use_count=m.use_count,
                    success_rate=m.success_rate,
                    enabled=m.enabled,
                    tags=m.tags or [],
                    created_from=m.created_from
                )
                for m in models
            ]

        except Exception as e:
            logger.error(f"Failed to get emergent skills: {e}")
            return []

    async def find_matching_skill(self, text: str) -> Optional[EmergentSkill]:
        """Find an emergent skill that matches the input text"""
        skills = await self.get_emergent_skills(enabled_only=True)

        for skill in skills:
            for pattern in skill.trigger_patterns:
                if pattern.lower() in text.lower():
                    return skill

        return None

    async def update_skill_usage(self, skill_id: UUID, success: bool):
        """Update skill usage statistics"""
        try:
            query = select(EmergentSkillModel).where(
                EmergentSkillModel.id == skill_id,
                EmergentSkillModel.user_id == self.user_id
            )
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()

            if model:
                model.use_count += 1
                # Update success rate (rolling average)
                old_rate = model.success_rate
                old_count = model.use_count - 1
                success_val = 1.0 if success else 0.0
                if old_count > 0:
                    model.success_rate = (old_rate * old_count + success_val) / model.use_count
                else:
                    model.success_rate = success_val

                self.db.add(model)
                await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update skill usage: {e}")

    # -------------------------------------------------------------------------
    # Learning History
    # -------------------------------------------------------------------------

    async def _log_learning(
        self,
        event_type: str,
        skill_name: Optional[str] = None,
        input_text: Optional[str] = None,
        result_success: bool = True,
        learned_pattern: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Log a learning event"""
        try:
            model = LearningHistoryModel(
                user_id=self.user_id,
                event_type=event_type,
                skill_name=skill_name,
                input_text=input_text,
                result_success=result_success,
                learned_pattern=learned_pattern,
                context=context or {}
            )

            self.db.add(model)
            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log learning: {e}")

    async def get_learning_history(self, limit: int = 50) -> List[Dict]:
        """Get recent learning history"""
        try:
            query = select(LearningHistoryModel).where(
                LearningHistoryModel.user_id == self.user_id
            ).order_by(
                LearningHistoryModel.timestamp.desc()
            ).limit(limit)

            result = await self.db.execute(query)
            models = result.scalars().all()

            return [m.to_dict() for m in models]

        except Exception as e:
            logger.error(f"Failed to get learning history: {e}")
            return []

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    async def get_stats(self) -> Dict:
        """Get MNEME statistics"""
        try:
            stats = {
                "total_entries": 0,
                "by_category": {},
                "total_skills": 0,
                "enabled_skills": 0,
                "recent_activity": []
            }

            # Total knowledge entries
            count_query = select(func.count(KnowledgeEntryModel.id)).where(
                KnowledgeEntryModel.user_id == self.user_id
            )
            result = await self.db.execute(count_query)
            stats["total_entries"] = result.scalar()

            # By category
            cat_query = select(
                KnowledgeEntryModel.category,
                func.count(KnowledgeEntryModel.id)
            ).where(
                KnowledgeEntryModel.user_id == self.user_id
            ).group_by(KnowledgeEntryModel.category)

            result = await self.db.execute(cat_query)
            for row in result.all():
                stats["by_category"][row[0]] = row[1]

            # Skills counts
            skills_query = select(func.count(EmergentSkillModel.id)).where(
                EmergentSkillModel.user_id == self.user_id
            )
            result = await self.db.execute(skills_query)
            stats["total_skills"] = result.scalar()

            enabled_query = select(func.count(EmergentSkillModel.id)).where(
                EmergentSkillModel.user_id == self.user_id,
                EmergentSkillModel.enabled == True
            )
            result = await self.db.execute(enabled_query)
            stats["enabled_skills"] = result.scalar()

            # Recent activity
            recent_query = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.user_id == self.user_id
            ).order_by(
                KnowledgeEntryModel.updated_at.desc()
            ).limit(10)

            result = await self.db.execute(recent_query)
            stats["recent_activity"] = [
                {
                    "title": m.title,
                    "category": m.category,
                    "date": m.updated_at.isoformat() if m.updated_at else None
                }
                for m in result.scalars().all()
            ]

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    # -------------------------------------------------------------------------
    # Semantic Search (Qdrant integration)
    # -------------------------------------------------------------------------

    async def _index_knowledge(self, model: KnowledgeEntryModel):
        """Index knowledge entry in Qdrant for semantic search"""
        # Optional - implement if Qdrant is available
        pass

    async def _semantic_search(
        self,
        query: str,
        category: Optional[str],
        limit: int
    ) -> List[KnowledgeEntry]:
        """Perform semantic search via Qdrant"""
        # Fallback to SQL search if Qdrant not available
        return await self.search_knowledge(
            query=query,
            category=category,
            limit=limit,
            semantic=False
        )


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_mneme(db: AsyncSession, user_id: UUID) -> MNEME:
    """
    Factory function to create a MNEME instance

    Args:
        db: Database session
        user_id: User UUID for data isolation

    Returns:
        Configured MNEME instance
    """
    return MNEME(db, user_id)
