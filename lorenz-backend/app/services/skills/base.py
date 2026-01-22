"""
LORENZ SaaS - Skill Base Classes
=================================

Base classes for the modular skill system.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class SkillType(Enum):
    """Distinguishes between developer-created and learned skills"""
    GOD = "god"           # Built-in, created by developers
    EMERGENT = "emergent" # Learned by LORENZ through interactions


class SkillCategory(Enum):
    """Categories for organizing skills"""
    CREATIVE = "creative"       # Image, presentation, document generation
    RESEARCH = "research"       # Web search, web browse
    TECHNICAL = "technical"     # Code execution, server commands
    DATA = "data"               # File operations, data processing
    COMMUNICATION = "communication"  # Email, calendar
    WORKFLOW = "workflow"       # Emergent workflow combinations
    CUSTOM = "custom"           # User-defined emergent skills


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SkillResult:
    """Result from a skill execution"""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)  # File paths, URLs, etc.
    skill_name: str = ""
    execution_time_ms: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "artifacts": self.artifacts,
            "skill_name": self.skill_name,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class SkillMetadata:
    """Metadata for skill tracking and learning"""
    created_at: str = ""
    last_used: str = ""
    use_count: int = 0
    success_rate: float = 1.0
    avg_execution_time_ms: float = 0.0
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "created_at": self.created_at,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "success_rate": round(self.success_rate * 100, 1),
            "avg_execution_time_ms": round(self.avg_execution_time_ms, 0),
            "tags": self.tags,
            "version": self.version
        }


# ============================================================================
# BASE SKILL CLASS
# ============================================================================

class Skill(ABC):
    """
    Base class for all skills

    Attributes:
        name: Unique skill identifier
        description: English description
        description_it: Italian description
        examples: Example prompts that trigger this skill
        requires_api: List of required API keys
        skill_type: GOD or EMERGENT
        category: Skill category for organization
        icon: Emoji icon for UI
    """

    name: str = "base_skill"
    description: str = "Base skill"
    description_it: str = "Skill base"
    examples: List[str] = []
    requires_api: List[str] = []
    skill_type: SkillType = SkillType.GOD
    category: SkillCategory = SkillCategory.CUSTOM
    icon: str = "⚡"

    # Cost estimation (for billing)
    estimated_cost_usd: float = 0.0

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize skill with optional custom API keys

        Args:
            api_keys: Dict of API keys (e.g., {"OPENAI": "sk-..."})
        """
        self.api_keys = api_keys or {}
        self.enabled = self._check_requirements()
        self.metadata = SkillMetadata(
            created_at=datetime.now().isoformat(),
            last_used="",
            use_count=0
        )
        self.skill_id = str(uuid.uuid4())[:8]

    def _check_requirements(self) -> bool:
        """Check if required API keys are available"""
        for api in self.requires_api:
            key_name = f"{api.upper()}_API_KEY"
            # Check custom keys first, then environment
            if key_name not in self.api_keys and not os.getenv(key_name):
                logger.warning(f"Skill {self.name} disabled: missing {key_name}")
                return False
        return True

    def _get_api_key(self, api_name: str) -> Optional[str]:
        """Get API key from custom keys or environment"""
        key_name = f"{api_name.upper()}_API_KEY"
        return self.api_keys.get(key_name) or os.getenv(key_name)

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult with execution outcome
        """
        pass

    def _track_execution(self, result: SkillResult, execution_time_ms: float):
        """Track execution for analytics and learning"""
        self.metadata.use_count += 1
        self.metadata.last_used = datetime.now().isoformat()

        # Update success rate (rolling average)
        old_rate = self.metadata.success_rate
        old_count = self.metadata.use_count - 1
        success_val = 1.0 if result.success else 0.0

        if old_count > 0:
            self.metadata.success_rate = (old_rate * old_count + success_val) / self.metadata.use_count
        else:
            self.metadata.success_rate = success_val

        # Update average execution time
        self.metadata.avg_execution_time_ms = (
            (self.metadata.avg_execution_time_ms * old_count + execution_time_ms) /
            self.metadata.use_count
        )

    def get_info(self) -> Dict:
        """Get skill info for UI display"""
        return {
            "id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "description_it": self.description_it,
            "examples": self.examples,
            "enabled": self.enabled,
            "requires": self.requires_api,
            "type": self.skill_type.value,
            "category": self.category.value,
            "icon": self.icon,
            "estimated_cost": self.estimated_cost_usd,
            "metadata": self.metadata.to_dict()
        }

    def to_dict(self) -> Dict:
        """Serialize skill for storage"""
        return self.get_info()

    def matches_query(self, query: str) -> float:
        """
        Check if query matches this skill

        Args:
            query: User input

        Returns:
            Match score (0.0 to 1.0)
        """
        query_lower = query.lower()
        score = 0.0

        # Check examples
        for example in self.examples:
            example_lower = example.lower()
            # Check for keyword overlap
            example_words = set(example_lower.split())
            query_words = set(query_lower.split())
            overlap = len(example_words & query_words)
            if overlap > 0:
                score = max(score, overlap / len(example_words))

        return score

    def __repr__(self) -> str:
        return f"<Skill {self.name} ({self.skill_type.value})>"
