"""
LORENZ SaaS - Skills Manager
=============================

Centralized manager for skill routing and execution.
Adapted from lorenz_skills.py SkillsManager.
"""

import logging
from typing import Dict, List, Optional, Type
from datetime import datetime
from uuid import UUID

from .base import Skill, SkillResult, SkillType, SkillCategory
from .god_skills import GOD_SKILLS, get_all_god_skills

logger = logging.getLogger(__name__)


class SkillsManager:
    """
    Centralized manager for LORENZ skills

    Features:
    - Skill registration and discovery
    - Smart routing based on user intent
    - Execution tracking and analytics
    - Multi-tenant isolation
    """

    def __init__(
        self,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        api_keys: Optional[Dict[str, str]] = None
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.api_keys = api_keys or {}

        # Initialize skill registry
        self._skills: Dict[str, Skill] = {}
        self._initialize_god_skills()

        # Execution stats
        self.stats = {
            "total_executions": 0,
            "by_skill": {},
            "by_category": {},
            "total_cost_usd": 0.0
        }

        logger.info(f"SkillsManager initialized with {len(self._skills)} skills")

    def _initialize_god_skills(self):
        """Initialize all GOD (built-in) skills"""
        for skill_class in GOD_SKILLS:
            try:
                skill = skill_class(self.api_keys)
                self._skills[skill.name] = skill
                logger.debug(f"Registered skill: {skill.name} (enabled={skill.enabled})")
            except Exception as e:
                logger.error(f"Failed to initialize skill {skill_class.name}: {e}")

    def register_skill(self, skill: Skill):
        """Register a new skill (for emergent skills)"""
        self._skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name}")

    def unregister_skill(self, skill_name: str) -> bool:
        """Unregister a skill"""
        if skill_name in self._skills:
            del self._skills[skill_name]
            logger.info(f"Unregistered skill: {skill_name}")
            return True
        return False

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self._skills.get(skill_name)

    def list_skills(
        self,
        enabled_only: bool = False,
        category: Optional[SkillCategory] = None,
        skill_type: Optional[SkillType] = None
    ) -> List[Dict]:
        """
        List available skills

        Args:
            enabled_only: Only return enabled skills
            category: Filter by category
            skill_type: Filter by GOD or EMERGENT

        Returns:
            List of skill info dictionaries
        """
        skills = []

        for skill in self._skills.values():
            if enabled_only and not skill.enabled:
                continue
            if category and skill.category != category:
                continue
            if skill_type and skill.skill_type != skill_type:
                continue

            skills.append(skill.get_info())

        # Sort by category, then by name
        skills.sort(key=lambda x: (x["category"], x["name"]))

        return skills

    def find_skill_for_query(
        self,
        query: str,
        threshold: float = 0.3
    ) -> Optional[Skill]:
        """
        Find the best matching skill for a user query

        Args:
            query: User input
            threshold: Minimum match score

        Returns:
            Best matching skill or None
        """
        best_skill = None
        best_score = 0.0

        for skill in self._skills.values():
            if not skill.enabled:
                continue

            score = skill.matches_query(query)
            if score > best_score and score >= threshold:
                best_score = score
                best_skill = skill

        if best_skill:
            logger.info(f"Matched query to skill: {best_skill.name} (score={best_score:.2f})")

        return best_skill

    async def execute_skill(
        self,
        skill_name: str,
        **kwargs
    ) -> SkillResult:
        """
        Execute a skill by name

        Args:
            skill_name: Name of the skill to execute
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult with execution outcome
        """
        skill = self.get_skill(skill_name)

        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill not found: {skill_name}",
                skill_name=skill_name
            )

        if not skill.enabled:
            return SkillResult(
                success=False,
                error=f"Skill is disabled: {skill_name}. Check API key configuration.",
                skill_name=skill_name
            )

        try:
            logger.info(f"Executing skill: {skill_name}")
            result = await skill.execute(**kwargs)

            # Update stats
            self.stats["total_executions"] += 1
            self.stats["by_skill"][skill_name] = \
                self.stats["by_skill"].get(skill_name, 0) + 1
            self.stats["by_category"][skill.category.value] = \
                self.stats["by_category"].get(skill.category.value, 0) + 1

            if result.success and skill.estimated_cost_usd > 0:
                self.stats["total_cost_usd"] += skill.estimated_cost_usd

            return result

        except Exception as e:
            logger.error(f"Skill execution failed: {skill_name} - {e}")
            return SkillResult(
                success=False,
                error=str(e),
                skill_name=skill_name
            )

    async def auto_execute(
        self,
        query: str,
        **kwargs
    ) -> SkillResult:
        """
        Automatically find and execute the best skill for a query

        Args:
            query: User input
            **kwargs: Additional parameters

        Returns:
            SkillResult with execution outcome
        """
        skill = self.find_skill_for_query(query)

        if not skill:
            return SkillResult(
                success=False,
                error="No matching skill found for this query",
                skill_name="auto"
            )

        # Pass the query as the main parameter
        return await self.execute_skill(skill.name, **kwargs)

    def get_stats(self) -> Dict:
        """Get execution statistics"""
        return {
            **self.stats,
            "skill_count": len(self._skills),
            "enabled_count": sum(1 for s in self._skills.values() if s.enabled),
            "by_type": {
                "god": sum(1 for s in self._skills.values() if s.skill_type == SkillType.GOD),
                "emergent": sum(1 for s in self._skills.values() if s.skill_type == SkillType.EMERGENT)
            }
        }

    def get_categories(self) -> List[Dict]:
        """Get skill categories with counts"""
        categories = {}

        for skill in self._skills.values():
            cat = skill.category.value
            if cat not in categories:
                categories[cat] = {
                    "name": cat,
                    "total": 0,
                    "enabled": 0,
                    "skills": []
                }

            categories[cat]["total"] += 1
            if skill.enabled:
                categories[cat]["enabled"] += 1
            categories[cat]["skills"].append(skill.name)

        return list(categories.values())


# ============================================================================
# SKILL ROUTER
# ============================================================================

class SkillRouter:
    """
    Routes user queries to appropriate skills

    Uses keyword matching and intent detection to select skills.
    """

    # Keyword to skill mapping
    SKILL_KEYWORDS = {
        "image_generation": [
            "genera immagine", "crea immagine", "disegna", "draw",
            "generate image", "create image", "illustra", "dall-e",
            "picture", "foto", "photo"
        ],
        "web_search": [
            "cerca", "search", "find", "google", "web",
            "trova", "notizie", "news", "latest", "current"
        ],
        "presentation": [
            "presentazione", "presentation", "slide", "powerpoint",
            "pptx", "deck", "pitch"
        ],
        "document_generation": [
            "documento", "document", "word", "docx", "report",
            "lettera", "letter", "pdf"
        ],
        "code_analysis": [
            "analizza codice", "analyze code", "review code",
            "debug", "security", "bug", "explain code"
        ],
        "email_draft": [
            "email", "mail", "scrivi email", "draft email",
            "reply", "rispondi", "bozza"
        ],
        "calendar": [
            "calendario", "calendar", "evento", "event",
            "meeting", "appuntamento", "schedule", "reminder"
        ]
    }

    @classmethod
    def route(cls, query: str) -> Optional[str]:
        """
        Route a query to the best skill

        Args:
            query: User input

        Returns:
            Skill name or None
        """
        query_lower = query.lower()
        scores = {}

        for skill_name, keywords in cls.SKILL_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1

            if score > 0:
                scores[skill_name] = score

        if not scores:
            return None

        # Return skill with highest score
        return max(scores, key=scores.get)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_skills_manager(
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    api_keys: Optional[Dict[str, str]] = None
) -> SkillsManager:
    """
    Factory function to create a SkillsManager instance

    Args:
        tenant_id: Tenant UUID for multi-tenant isolation
        user_id: User UUID for tracking
        api_keys: Optional custom API keys (BYOK)

    Returns:
        Configured SkillsManager instance
    """
    return SkillsManager(
        tenant_id=tenant_id,
        user_id=user_id,
        api_keys=api_keys
    )
