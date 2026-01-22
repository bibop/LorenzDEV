"""
LORENZ - Human Digital Twin System
The most advanced personal AI twin technology
"""

from .profile import TwinProfile, TwinProfileManager, ContactProfile, WorkPattern, ProjectContext
from .learning import TwinLearning, LearningEvent, EventType, Pattern
from .proactive import ProactiveEngine, ProactiveAction, ActionType, ActionPriority
from .prompts import TwinPrompts
from .service import TwinService, get_twin_service, create_twin_with_defaults

__all__ = [
    # Profile
    "TwinProfile",
    "TwinProfileManager",
    "ContactProfile",
    "WorkPattern",
    "ProjectContext",
    # Learning
    "TwinLearning",
    "LearningEvent",
    "EventType",
    "Pattern",
    # Proactive
    "ProactiveEngine",
    "ProactiveAction",
    "ActionType",
    "ActionPriority",
    # Prompts
    "TwinPrompts",
    # Service
    "TwinService",
    "get_twin_service",
    "create_twin_with_defaults",
]
