"""
LORENZ SaaS - Skills System
============================

Modular skill system adapted from lorenz_skills.py
for multi-tenant SaaS deployment.

Skill Types:
- GOD Skills: Built-in capabilities (image gen, web search, etc.)
- Emergent Skills: User-defined automations
- MNEME: Knowledge base integration

"""

from .base import Skill, SkillResult, SkillType, SkillCategory, SkillMetadata
from .manager import SkillsManager, create_skills_manager, SkillRouter
from .god_skills import (
    ImageGenerationSkill,
    WebSearchSkill,
    PresentationSkill,
    DocumentGenerationSkill,
    CodeAnalysisSkill,
    EmailDraftSkill,
    CalendarSkill,
)

__all__ = [
    # Base classes
    "Skill",
    "SkillResult",
    "SkillType",
    "SkillCategory",
    "SkillMetadata",
    # Manager
    "SkillsManager",
    "create_skills_manager",
    "SkillRouter",
    # GOD Skills
    "ImageGenerationSkill",
    "WebSearchSkill",
    "PresentationSkill",
    "DocumentGenerationSkill",
    "CodeAnalysisSkill",
    "EmailDraftSkill",
    "CalendarSkill",
]
