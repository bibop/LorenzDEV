"""
LORENZ - Twin Service
Main orchestration service for the Human Digital Twin system

Integrates with:
- AdvancedRAGService: Semantic search and context building
- MNEME: Persistent knowledge and pattern storage
- SaaSAIOrchestrator: Multi-model AI routing
- Skills: Task execution capabilities
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.ai.orchestrator import SaaSAIOrchestrator, create_orchestrator
from app.services.rag.advanced import AdvancedRAGService
from app.services.knowledge.mneme import MNEME, KnowledgeEntry
from app.services.skills import SkillsManager, SkillRouter, SkillResult, create_skills_manager
from app.services.calendar import CalendarService, CalendarEvent, get_calendar_service
from app.services.email import EmailService
from .profile import TwinProfile, TwinProfileManager, ContactProfile, Urgency
from .learning import TwinLearning, LearningEvent, EventType
from .proactive import ProactiveEngine, ProactiveAction, ActionType, ActionPriority
from .prompts import TwinPrompts

logger = logging.getLogger(__name__)


class TwinService:
    """
    Main service that orchestrates all Human Digital Twin components.
    This is the brain of LORENZ.

    Integrates:
    - AdvancedRAGService: For semantic context retrieval
    - MNEMEService: For persistent knowledge storage
    - SaaSAIOrchestrator: For multi-model AI routing
    """

    def __init__(
        self,
        user: User,
        db: AsyncSession,
        ai_orchestrator: Optional[SaaSAIOrchestrator] = None,
        rag_service: Optional[AdvancedRAGService] = None,
        mneme_service: Optional[MNEME] = None,
        skills_manager: Optional[SkillsManager] = None,
        calendar_service: Optional[CalendarService] = None,
        email_service: Optional[EmailService] = None
    ):
        self.user = user
        self.db = db
        self.user_id = str(user.id) if user.id else None

        # AI Orchestrator for multi-model routing
        self.ai = ai_orchestrator or create_orchestrator(
            tenant_id=user.tenant_id if user.tenant_id else None,
            user_id=user.id if user.id else None
        )

        # Advanced RAG for semantic context
        self.rag = rag_service or AdvancedRAGService(db, user.tenant_id, user.id)

        # MNEME for persistent knowledge
        self.mneme = mneme_service or MNEME(db, self.user_id)

        # Skills Manager for task execution
        self.skills = skills_manager or create_skills_manager(
            tenant_id=user.tenant_id if user.tenant_id else None,
            user_id=user.id if user.id else None
        )

        # Calendar Service for schedule awareness
        self.calendar = calendar_service or CalendarService(db, self.user_id)

        # Email Service for email operations
        self.email_service = email_service or EmailService(db)

        # Initialize Twin components
        self.profile_manager = TwinProfileManager(db)
        self._profile: Optional[TwinProfile] = None
        self._learning: Optional[TwinLearning] = None
        self._proactive: Optional[ProactiveEngine] = None

        # Cache for performance
        self._initialized = False
        self._rag_context_cache: Dict[str, Any] = {}
        self._calendar_cache: List[CalendarEvent] = []
        self._context_cache_ttl = 300  # 5 minutes

    async def _ai_generate(
        self,
        prompt: str,
        system_prompt: str = None,
        response_format: str = None,
        use_rag: bool = True,
        rag_source_types: List[str] = None
    ) -> str:
        """
        Helper method to generate AI response using orchestrator with RAG context.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt override
            response_format: Optional response format
            use_rag: Whether to include RAG context (default True)
            rag_source_types: Filter RAG results by source type
        """
        # Build enhanced prompt with RAG context
        enhanced_prompt = prompt
        if use_rag:
            rag_context = await self._get_rag_context(prompt, rag_source_types)
            if rag_context:
                enhanced_prompt = f"""Context from knowledge base:
{rag_context}

User query: {prompt}"""

        result = await self.ai.process(
            prompt=enhanced_prompt,
            system_prompt=system_prompt or await self.get_system_prompt(),
        )
        if result.get("success"):
            return result.get("response", "")
        else:
            logger.error(f"AI processing failed: {result.get('error')}")
            return f"Error: {result.get('error', 'Unknown error')}"

    async def _get_rag_context(
        self,
        query: str,
        source_types: List[str] = None,
        top_k: int = 5
    ) -> str:
        """
        Retrieve relevant context from RAG using hybrid search.
        Uses AdvancedRAGService for semantic + keyword search with reranking.
        """
        try:
            # Use advanced hybrid search
            results = await self.rag.hybrid_search(
                query=query,
                source_types=source_types,
                top_k=top_k,
                use_reranking=True
            )

            if not results:
                return ""

            # Build context string
            context_parts = []
            for i, result in enumerate(results[:top_k], 1):
                source = result.get("source_type", "unknown")
                title = result.get("title", "Untitled")
                content = result.get("content", "")[:500]  # Limit content length
                score = result.get("score", 0)

                context_parts.append(
                    f"[{i}] ({source}) {title}\n{content}"
                )

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
            return ""

    async def _search_mneme_knowledge(
        self,
        query: str,
        category: str = None,
        semantic: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search MNEME knowledge base for relevant entries"""
        try:
            results = await self.mneme.search_knowledge(
                query=query,
                category=category,
                semantic=semantic,
                limit=limit
            )
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in results]
        except Exception as e:
            logger.warning(f"MNEME search failed: {e}")
            return []

    async def _store_knowledge(
        self,
        category: str,
        title: str,
        content: str,
        context: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Optional[str]:
        """Store knowledge in MNEME for future retrieval"""
        try:
            entry = KnowledgeEntry(
                category=category,
                title=title,
                content=content,
                context=context or {},
                tags=tags or [],
                source="twin_learning"
            )
            result = await self.mneme.add_knowledge(entry)
            return str(result.id) if result else None
        except Exception as e:
            logger.warning(f"MNEME storage failed: {e}")
            return None

    async def initialize(self) -> "TwinService":
        """Initialize all Twin components for this user"""
        if self._initialized:
            return self

        # Load or create profile
        self._profile = await self.profile_manager.get_profile(str(self.user.id))

        if not self._profile:
            # Create initial profile from user data
            self._profile = await self._create_initial_profile()

        # Initialize learning engine
        self._learning = TwinLearning(str(self.user.id))

        # Initialize proactive engine
        self._proactive = ProactiveEngine(self._profile, self._learning)

        self._initialized = True
        logger.info(f"Twin initialized for user {self.user.email}")

        return self

    async def _create_initial_profile(self) -> TwinProfile:
        """Create initial profile from user data"""
        user_data = {
            "user_id": str(self.user.id),
            "full_name": self.user.full_name or self.user.email.split("@")[0],
            "email": self.user.email,
        }

        # Extract preferences if available
        if self.user.preferences:
            prefs = self.user.preferences
            user_data.update({
                "twin_name": prefs.get("assistant_name", "LORENZ"),
                "birth_date": prefs.get("assistant_birth_date"),
                "zodiac_sign": prefs.get("assistant_zodiac"),
                "ascendant": prefs.get("assistant_ascendant"),
                "timezone": prefs.get("timezone", "Europe/Rome"),
            })

        return await self.profile_manager.create_initial_profile(
            str(self.user.id),
            user_data
        )

    @property
    def profile(self) -> TwinProfile:
        """Get the Twin profile"""
        if not self._profile:
            raise RuntimeError("TwinService not initialized. Call initialize() first.")
        return self._profile

    @property
    def learning(self) -> TwinLearning:
        """Get the learning engine"""
        if not self._learning:
            raise RuntimeError("TwinService not initialized. Call initialize() first.")
        return self._learning

    @property
    def proactive(self) -> ProactiveEngine:
        """Get the proactive engine"""
        if not self._proactive:
            raise RuntimeError("TwinService not initialized. Call initialize() first.")
        return self._proactive

    # =====================
    # Core Twin Operations
    # =====================

    async def get_system_prompt(self) -> str:
        """Get the core system prompt for AI interactions"""
        return TwinPrompts.get_core_identity_prompt(self.profile)

    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process an incoming message and generate Twin response.
        This is the main entry point for chat interactions.

        Uses:
        - Skills: For specialized task execution
        - RAG for semantic context retrieval
        - MNEME for knowledge base queries
        - AI Orchestrator for response generation
        """
        # Record the interaction
        await self.learning.record_event(LearningEvent(
            event_type=EventType.MESSAGE_SENT,
            timestamp=datetime.utcnow(),
            data={"content": message, "direction": "incoming"},
            context=context or {},
        ))

        # Check if this is an email request
        if self._is_email_request(message):
            logger.info("Detected email request, handling via EmailService")
            email_response = await self._handle_email_request(message, context)
            # Learn from this interaction
            asyncio.create_task(self._learn_from_conversation(message, email_response, context))
            return email_response

        # Check if this is a skill request
        skill_result = await self._try_execute_skill(message, context)
        if skill_result:
            # Skill was executed successfully
            return skill_result

        # Get system prompt
        system_prompt = await self.get_system_prompt()

        # Add context from profile, RAG, and MNEME
        enhanced_context = await self._build_conversation_context(message, context)

        # Build enhanced system prompt with context
        context_summary = self._format_context_for_prompt(enhanced_context)
        enhanced_system_prompt = f"""{system_prompt}

## Current Context:
{context_summary}"""

        # Generate response using AI with RAG context
        response = await self._ai_generate(
            prompt=message,
            system_prompt=enhanced_system_prompt,
            use_rag=True,  # Enable RAG for additional context
        )

        # Learn from this interaction (async, non-blocking)
        asyncio.create_task(self._learn_from_conversation(message, response, context))

        return response

    async def _try_execute_skill(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Try to match and execute a skill for the given message.

        Returns the skill result if a skill was executed, None otherwise.
        """
        try:
            # Check if message matches a skill
            skill_name = SkillRouter.route(message)

            if not skill_name:
                # Also try the skills manager's fuzzy matching
                skill = self.skills.find_skill_for_query(message)
                if skill:
                    skill_name = skill.name

            if not skill_name:
                return None

            logger.info(f"Detected skill request: {skill_name}")

            # Execute the skill
            result: SkillResult = await self.skills.execute_skill(
                skill_name,
                query=message,
                user_context=context,
                user_profile={
                    "name": self.profile.preferred_name,
                    "email": self.user.email,
                    "timezone": self.profile.work_pattern.timezone,
                }
            )

            if result.success:
                # Record skill execution
                await self.learning.record_event(LearningEvent(
                    event_type=EventType.TASK_COMPLETED,
                    timestamp=datetime.utcnow(),
                    data={
                        "skill_name": skill_name,
                        "query": message[:200],
                        "success": True,
                    },
                ))

                # Format skill response with Twin personality
                response = await self._format_skill_response(skill_name, result)
                return response
            else:
                logger.warning(f"Skill {skill_name} failed: {result.error}")
                return None

        except Exception as e:
            logger.error(f"Skill execution error: {e}")
            return None

    async def _format_skill_response(
        self,
        skill_name: str,
        result: SkillResult
    ) -> str:
        """
        Format skill result with Twin personality.
        Optionally uses AI to make the response more natural.
        """
        # Get raw skill message
        skill_message = result.message or "Task completed"

        # For simple acknowledgments, return directly
        if len(skill_message) < 100:
            return skill_message

        # For longer responses, optionally enhance with Twin personality
        try:
            enhanced = await self._ai_generate(
                prompt=f"""Summarize and present this {skill_name} result in your style:

{skill_message}

Keep your response concise but friendly.""",
                use_rag=False
            )
            return enhanced
        except Exception:
            return skill_message

    # =====================
    # Email Operations
    # =====================

    def _is_email_request(self, message: str) -> bool:
        """
        Detect if the message is requesting email operations.
        Supports Italian and English.
        """
        message_lower = message.lower()

        # Email keywords in multiple languages
        email_keywords = [
            # Italian
            "leggi", "leggere", "email", "mail", "posta", "messaggi",
            "inbox", "casella", "ricevute", "arrivate", "nuove email",
            "controlla email", "controlla la posta", "controllare",
            # English
            "read", "check", "emails", "inbox", "messages",
            "unread", "new mail", "fetch", "get emails"
        ]

        # Check for email-related request
        has_email_word = any(kw in message_lower for kw in ["email", "mail", "posta", "inbox", "messaggi"])
        has_action_word = any(kw in message_lower for kw in ["leggi", "leggere", "read", "check", "controlla", "controllare", "mostra", "show", "fetch", "get"])

        return has_email_word and has_action_word

    async def _handle_email_request(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle email-related requests by fetching and formatting emails.
        """
        try:
            # Determine how many emails to fetch
            limit = 10  # Default
            message_lower = message.lower()

            if "ultime" in message_lower or "last" in message_lower:
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', message)
                if numbers:
                    limit = min(int(numbers[0]), 50)  # Max 50
            elif "tutte" in message_lower or "all" in message_lower:
                limit = 20  # Reasonable limit for "all"

            # Fetch emails using EmailService
            logger.info(f"Fetching {limit} emails for user {self.user.id}")

            emails = await self.email_service.list_messages(
                user_id=self.user.id,
                limit=limit,
                unread_only=False
            )

            if not emails:
                return "Non ho trovato email configurate o la casella è vuota. Vuoi che ti aiuti a configurare un account email?"

            # Format emails for response
            response_parts = [f"Ecco le tue ultime {len(emails)} email:\n"]

            for i, email in enumerate(emails, 1):
                # Format each email
                subject = email.get("subject", "(Nessun oggetto)")
                # Get sender: prefer name, fallback to address
                from_name = email.get("from_name", "")
                from_address = email.get("from_address", "")
                sender = from_name if from_name else from_address if from_address else "Sconosciuto"
                date = email.get("date", "")
                is_unread = not email.get("is_read", True)  # is_read is the correct field
                snippet = email.get("snippet", "")[:100]

                status = "📩 " if is_unread else "📧 "
                response_parts.append(
                    f"{status}**{i}. {subject}**\n"
                    f"   Da: {sender}\n"
                    f"   Data: {date}\n"
                    f"   {snippet}{'...' if len(email.get('snippet', '')) > 100 else ''}\n"
                )

            # Add summary
            unread_count = sum(1 for e in emails if not e.get("is_read", True))
            if unread_count > 0:
                response_parts.append(f"\n📬 Hai {unread_count} email non lette.")

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error handling email request: {e}", exc_info=True)
            return f"Mi dispiace, c'è stato un errore nel recuperare le email: {str(e)}"

    async def execute_skill(
        self,
        skill_name: str,
        **kwargs
    ) -> SkillResult:
        """
        Directly execute a specific skill.

        Args:
            skill_name: Name of the skill to execute
            **kwargs: Skill-specific parameters
        """
        return await self.skills.execute_skill(skill_name, **kwargs)

    def list_available_skills(self, enabled_only: bool = True) -> List[Dict]:
        """Get list of available skills"""
        return self.skills.list_skills(enabled_only=enabled_only)

    def get_skill_categories(self) -> List[Dict]:
        """Get skill categories with counts"""
        return self.skills.get_categories()

    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for inclusion in system prompt"""
        parts = []

        # User profile
        if "user_profile" in context:
            profile = context["user_profile"]
            parts.append(f"User: {profile.get('name')} - {profile.get('role')} at {profile.get('company')}")

        # Active projects
        if context.get("active_projects"):
            projects = ", ".join([p["name"] for p in context["active_projects"][:3]])
            parts.append(f"Active projects: {projects}")

        # Knowledge from MNEME
        if context.get("knowledge_base"):
            kb_titles = ", ".join([k["title"] for k in context["knowledge_base"][:3]])
            parts.append(f"Relevant knowledge: {kb_titles}")

        # Semantic context from RAG
        if context.get("semantic_context"):
            sources = len(context["semantic_context"])
            parts.append(f"Found {sources} relevant documents in knowledge base")

        # Work context
        if context.get("is_work_hours") is not None:
            status = "during work hours" if context["is_work_hours"] else "outside work hours"
            parts.append(f"Current time: {status}")

        # Calendar context
        if context.get("calendar_events"):
            events = context["calendar_events"]
            parts.append(f"Upcoming events: {len(events)} in next 24h")
            for e in events[:3]:
                parts.append(f"  - {e.get('title', 'Event')} at {e.get('start', 'TBD')}")

        return "\n".join(parts) if parts else "No additional context available"

    async def _build_conversation_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build enhanced context for AI response using RAG and MNEME.
        Combines profile data, RAG results, and MNEME knowledge.
        """
        # Base context from profile
        base_context = {
            "user_profile": {
                "name": self.profile.preferred_name,
                "role": self.profile.current_role,
                "company": self.profile.company,
                "timezone": self.profile.work_pattern.timezone,
            },
            "active_projects": [
                {"name": p.name, "priority": p.priority}
                for p in self.profile.projects
                if p.status == "active"
            ][:5],
            "vip_contacts": self.profile.vip_contacts[:10],
            "autonomy_level": self.profile.autonomy_level,
            "learned_patterns": list(self.learning.patterns.keys())[:10],
            "current_time": datetime.utcnow().isoformat(),
            "is_work_hours": self.profile.is_work_hours(),
        }

        # Add MNEME knowledge context
        try:
            mneme_results = await self._search_mneme_knowledge(
                query=message,
                limit=5
            )
            if mneme_results:
                base_context["knowledge_base"] = [
                    {
                        "title": k.get("title", ""),
                        "content": k.get("content", "")[:200],
                        "category": k.get("category", ""),
                    }
                    for k in mneme_results
                ]
        except Exception as e:
            logger.debug(f"MNEME context retrieval skipped: {e}")

        # Add RAG semantic context
        try:
            rag_results = await self.rag.hybrid_search(
                query=message,
                top_k=3
            )
            if rag_results:
                base_context["semantic_context"] = [
                    {
                        "source": r.get("source_type", ""),
                        "title": r.get("title", ""),
                        "relevance": r.get("score", 0),
                    }
                    for r in rag_results
                ]
        except Exception as e:
            logger.debug(f"RAG context retrieval skipped: {e}")

        # Add Calendar context (upcoming events)
        try:
            upcoming_events = await self.calendar.get_upcoming_events(hours=24)
            if upcoming_events:
                base_context["calendar_events"] = [
                    {
                        "title": e.title,
                        "start": e.start.isoformat() if e.start else None,
                        "end": e.end.isoformat() if e.end else None,
                        "location": e.location,
                        "attendees": e.attendees[:5],  # Limit attendees
                    }
                    for e in upcoming_events[:5]  # Limit to 5 events
                ]
                base_context["calendar_context"] = self.calendar.build_context_for_twin(
                    upcoming_events[:5]
                )
        except Exception as e:
            logger.debug(f"Calendar context retrieval skipped: {e}")

        # Merge with provided context
        return {**base_context, **(context or {})}

    async def _learn_from_conversation(
        self,
        user_message: str,
        twin_response: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Extract learnings from conversation and store in MNEME.
        Uses AI to identify important facts, preferences, and patterns.
        """
        # Record the event in learning system
        await self.learning.record_event(LearningEvent(
            event_type=EventType.MESSAGE_SENT,
            timestamp=datetime.utcnow(),
            data={
                "user_message": user_message,
                "twin_response": twin_response[:500],
            },
        ))

        # Use AI to extract learnings (async, non-blocking)
        try:
            learning_prompt = TwinPrompts.get_learning_prompt(
                self.profile,
                {
                    "type": "conversation",
                    "content": f"User: {user_message}\n\nTwin: {twin_response}",
                    "context": context or {},
                }
            )

            # Ask AI to extract knowledge
            extraction_response = await self._ai_generate(
                prompt=f"""Analyze this conversation and extract any important information to remember.
Return JSON with: {{"facts": [], "preferences": [], "patterns": [], "should_store": boolean}}

Conversation:
User: {user_message}
Twin: {twin_response}""",
                use_rag=False  # Don't use RAG for extraction
            )

            # Parse and store in MNEME
            try:
                extracted = json.loads(extraction_response)
                if extracted.get("should_store", False):
                    # Store facts
                    for fact in extracted.get("facts", []):
                        await self._store_knowledge(
                            category="fact",
                            title=fact.get("title", "Learned fact"),
                            content=fact.get("content", str(fact)),
                            tags=["auto_learned", "conversation"]
                        )

                    # Store preferences
                    for pref in extracted.get("preferences", []):
                        await self._store_knowledge(
                            category="preference",
                            title=pref.get("title", "User preference"),
                            content=pref.get("content", str(pref)),
                            tags=["auto_learned", "preference"]
                        )

                    # Store patterns
                    for pattern in extracted.get("patterns", []):
                        await self._store_knowledge(
                            category="pattern",
                            title=pattern.get("title", "Behavior pattern"),
                            content=pattern.get("content", str(pattern)),
                            tags=["auto_learned", "pattern"]
                        )

                    logger.info(f"Stored {len(extracted.get('facts', []))} facts, "
                               f"{len(extracted.get('preferences', []))} preferences, "
                               f"{len(extracted.get('patterns', []))} patterns in MNEME")

            except json.JSONDecodeError:
                # Not valid JSON, skip MNEME storage
                pass

        except Exception as e:
            logger.debug(f"Learning extraction skipped: {e}")

    async def _get_relevant_insights(self, message: str) -> List[Dict[str, Any]]:
        """Get insights relevant to the current message"""
        insights = []

        # Check for mentions of known contacts
        for email, contact in self.profile.contacts.items():
            if contact.name.lower() in message.lower():
                insights.append({
                    "type": "contact_mentioned",
                    "contact": contact.name,
                    "importance": contact.importance,
                    "last_interaction": contact.last_interaction.isoformat() if contact.last_interaction else None,
                })

        # Check for project keywords
        for project in self.profile.projects:
            if any(kw.lower() in message.lower() for kw in project.key_topics):
                insights.append({
                    "type": "project_related",
                    "project": project.name,
                    "priority": project.priority,
                })

        return insights[:5]

    # =====================
    # Email Intelligence
    # =====================

    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an incoming email and determine actions.
        This is the core email intelligence function.

        Uses RAG to find related emails and conversations for context.
        Stores important email interactions in MNEME.
        """
        sender = email_data.get("from", "")
        subject = email_data.get("subject", "")

        # Record email received event
        await self.learning.record_event(LearningEvent(
            event_type=EventType.EMAIL_RECEIVED,
            timestamp=datetime.utcnow(),
            data=email_data,
        ))

        # Get proactive analysis
        analysis = await self.proactive.analyze_email(email_data)

        # Search RAG for related emails and context
        try:
            related_context = await self.rag.hybrid_search(
                query=f"{sender} {subject}",
                source_types=["email", "conversation"],
                top_k=3
            )
            if related_context:
                analysis["related_context"] = [
                    {"source": r.get("source_type"), "title": r.get("title")}
                    for r in related_context
                ]
        except Exception as e:
            logger.debug(f"RAG email context skipped: {e}")

        # Search MNEME for contact information
        try:
            contact_knowledge = await self._search_mneme_knowledge(
                query=sender,
                category="fact",
                limit=3
            )
            if contact_knowledge:
                analysis["contact_knowledge"] = contact_knowledge
        except Exception as e:
            logger.debug(f"MNEME contact lookup skipped: {e}")

        # Use AI for deeper analysis if needed
        if analysis["priority"] in ["high", "critical"]:
            ai_analysis = await self._ai_analyze_email(email_data)
            analysis["ai_insights"] = ai_analysis

            # Store important email interaction in MNEME
            await self._store_knowledge(
                category="fact",
                title=f"Important email from {sender}",
                content=f"Subject: {subject}\nPriority: {analysis['priority']}\nActions: {analysis.get('actions', [])}",
                tags=["email", "important", analysis["priority"]],
                context={"sender": sender, "subject": subject}
            )

        # Trigger proactive actions
        actions = await self.proactive.process_event(LearningEvent(
            event_type=EventType.EMAIL_RECEIVED,
            timestamp=datetime.utcnow(),
            data=email_data,
        ))

        analysis["triggered_actions"] = [a.to_dict() for a in actions]

        return analysis

    async def _ai_analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to deeply analyze an email with RAG context.
        Retrieves related emails and knowledge for comprehensive analysis.
        """
        sender = email_data.get("from", "")
        subject = email_data.get("subject", "")

        # Get RAG context for email analysis
        rag_context = await self._get_rag_context(
            query=f"email from {sender} about {subject}",
            source_types=["email", "conversation"],
            top_k=3
        )

        prompt = TwinPrompts.get_email_analysis_prompt(self.profile, email_data)

        # Include RAG context in prompt
        if rag_context:
            prompt = f"""Previous related communications:
{rag_context}

---

{prompt}"""

        response = await self._ai_generate(
            prompt=prompt,
            system_prompt=await self.get_system_prompt(),
            use_rag=False  # Already included RAG context above
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_analysis": response}

    async def draft_email_response(
        self,
        email_data: Dict[str, Any],
        intent: str = "professional"
    ) -> str:
        """Draft an email response as the Twin"""
        prompt = TwinPrompts.get_email_response_prompt(
            self.profile,
            email_data,
            intent
        )

        response = await self._ai_generate(
            prompt=prompt,
            system_prompt=await self.get_system_prompt(),
        )

        # Record that we drafted a response
        await self.learning.record_event(LearningEvent(
            event_type=EventType.EMAIL_REPLIED,
            timestamp=datetime.utcnow(),
            data={
                "original_sender": email_data.get("from"),
                "original_subject": email_data.get("subject"),
                "draft_intent": intent,
            },
        ))

        return response

    async def should_auto_respond(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine if Twin should auto-respond to this email"""
        # Check learned patterns
        auto_response = self.learning.should_auto_respond(email_data)
        if auto_response:
            return auto_response

        # Check if sender is VIP and autonomy is high enough
        sender = email_data.get("from", "")
        if self.profile.is_vip(sender) and self.profile.autonomy_level >= 9:
            return {
                "should_respond": True,
                "confidence": 0.8,
                "reason": "VIP sender with high autonomy level",
            }

        return None

    # =====================
    # Calendar & Meetings
    # =====================

    async def prepare_meeting_briefing(
        self,
        meeting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare a comprehensive briefing for an upcoming meeting"""
        attendees = meeting.get("attendees", [])

        # Gather information about attendees
        attendees_info = {}
        for attendee in attendees:
            email = attendee.get("email", attendee) if isinstance(attendee, dict) else attendee

            # Check if we know this person
            contact = self.profile.get_contact(email)
            if contact:
                attendees_info[email] = {
                    "name": contact.name,
                    "company": contact.company,
                    "role": contact.role,
                    "relationship": contact.relationship,
                    "importance": contact.importance,
                    "notes": contact.notes,
                    "interaction_count": contact.interaction_count,
                    "last_interaction": contact.last_interaction.isoformat() if contact.last_interaction else None,
                }
            else:
                # Unknown contact - mark for research
                attendees_info[email] = {
                    "name": email.split("@")[0],
                    "unknown": True,
                    "needs_research": True,
                }

        # Generate briefing using AI
        prompt = TwinPrompts.get_meeting_briefing_prompt(
            self.profile,
            meeting,
            attendees_info
        )

        briefing_content = await self._ai_generate(
            prompt=prompt,
            system_prompt=await self.get_system_prompt(),
        )

        # Create proactive actions for unknown attendees
        unknown_attendees = [
            email for email, info in attendees_info.items()
            if info.get("needs_research")
        ]

        research_actions = []
        for email in unknown_attendees:
            action = ProactiveAction(
                action_type=ActionType.PERSON_RESEARCH,
                priority=ActionPriority.MEDIUM,
                title=f"Research: {email}",
                description=f"Research attendee for {meeting.get('title', 'meeting')}",
                data={"email": email, "meeting_id": meeting.get("id")},
            )
            research_actions.append(action.to_dict())
            self.proactive.action_queue.append(action)

        return {
            "meeting": meeting,
            "attendees_info": attendees_info,
            "briefing": briefing_content,
            "research_needed": unknown_attendees,
            "research_actions": research_actions,
        }

    async def get_upcoming_meeting_alerts(
        self,
        meetings: List[Dict[str, Any]],
        alert_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Get alerts for upcoming meetings"""
        alerts = []
        now = datetime.utcnow()

        for meeting in meetings:
            start_time = meeting.get("start_time")
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

            time_until = start_time - now
            minutes_until = time_until.total_seconds() / 60

            if 0 < minutes_until <= alert_minutes:
                alerts.append({
                    "meeting": meeting,
                    "minutes_until": int(minutes_until),
                    "alert_type": "imminent" if minutes_until <= 10 else "upcoming",
                    "message": f"Meeting '{meeting.get('title', 'Untitled')}' starts in {int(minutes_until)} minutes",
                })

        return alerts

    # =====================
    # Research & Intelligence
    # =====================

    async def research_person(
        self,
        person: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """Research a person and generate a profile"""
        prompt = TwinPrompts.get_research_prompt(self.profile, person, context)

        research_content = await self._ai_generate(
            prompt=prompt,
            system_prompt=await self.get_system_prompt(),
        )

        # Create or update contact profile
        email = person.get("email", "")
        if email:
            existing = self.profile.get_contact(email)
            if existing:
                existing.notes.append(f"Research ({datetime.now().date()}): {research_content[:500]}")
            else:
                new_contact = ContactProfile(
                    email=email,
                    name=person.get("name", email.split("@")[0]),
                    relationship="unknown",
                    company=person.get("company"),
                    notes=[f"Initial research: {research_content[:500]}"],
                )
                self.profile.add_contact(new_contact)

            await self.profile_manager.save_profile(self.profile)

        return {
            "person": person,
            "research": research_content,
            "profile_updated": bool(email),
        }

    # =====================
    # Daily Operations
    # =====================

    async def generate_daily_briefing(
        self,
        calendar_events: List[Dict[str, Any]] = None,
        pending_emails: int = 0
    ) -> Dict[str, Any]:
        """Generate the daily briefing for the user"""
        # Gather learning insights
        learning_insights = self.learning.get_daily_briefing_data()

        # Get high priority items
        high_priority_items = []
        for action in self.proactive.action_queue:
            if action.priority in [ActionPriority.CRITICAL, ActionPriority.HIGH]:
                high_priority_items.append({
                    "type": action.action_type.value,
                    "description": action.description,
                })

        # Generate briefing content
        prompt = TwinPrompts.get_daily_briefing_prompt(
            self.profile,
            calendar_events or [],
            pending_emails,
            high_priority_items,
            learning_insights
        )

        briefing_content = await self._ai_generate(
            prompt=prompt,
            system_prompt=await self.get_system_prompt(),
        )

        return {
            "date": datetime.now().date().isoformat(),
            "content": briefing_content,
            "calendar_events": calendar_events or [],
            "pending_emails": pending_emails,
            "high_priority_items": high_priority_items,
            "patterns_summary": learning_insights.get("patterns_summary", [])[:5],
        }

    # =====================
    # Profile Management
    # =====================

    async def update_profile(self, updates: Dict[str, Any]) -> TwinProfile:
        """Update the Twin profile"""
        for key, value in updates.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)

        await self.profile_manager.save_profile(self.profile)
        return self.profile

    async def add_vip_contact(self, email: str) -> bool:
        """Add a contact to VIP list"""
        if email.lower() not in [v.lower() for v in self.profile.vip_contacts]:
            self.profile.vip_contacts.append(email)
            await self.profile_manager.save_profile(self.profile)
            return True
        return False

    async def add_project(
        self,
        name: str,
        description: str,
        priority: int = 5,
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Add a new active project"""
        from .profile import ProjectContext

        project = ProjectContext(
            name=name,
            description=description,
            priority=priority,
            related_emails_keywords=keywords or [],
        )

        self.profile.projects.append(project)
        await self.profile_manager.save_profile(self.profile)

        return {
            "name": project.name,
            "priority": project.priority,
            "status": project.status,
        }

    # =====================
    # Feedback & Learning
    # =====================

    async def record_feedback(
        self,
        feedback_type: str,
        data: Dict[str, Any]
    ):
        """Record user feedback on Twin actions"""
        event_type = {
            "approved": EventType.TWIN_APPROVED,
            "rejected": EventType.TWIN_REJECTED,
            "modified": EventType.TWIN_MODIFIED,
        }.get(feedback_type, EventType.TWIN_MODIFIED)

        await self.learning.record_event(LearningEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
        ))

        logger.info(f"Feedback recorded: {feedback_type} for user {self.user.id}")

    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the Twin's learning"""
        return {
            "total_events": self.learning.stats["total_events"],
            "events_by_type": dict(self.learning.stats["events_by_type"]),
            "patterns_count": len(self.learning.patterns),
            "top_patterns": [
                p.to_dict() for p in sorted(
                    self.learning.patterns.values(),
                    key=lambda x: x.confidence,
                    reverse=True
                )[:10]
            ],
            "learning_started": self.learning.stats["learning_started"].isoformat(),
        }

    # =====================
    # Proactive Processing
    # =====================

    async def process_proactive_queue(self) -> List[Dict[str, Any]]:
        """Process pending proactive actions"""
        results = await self.proactive.process_queue()

        # Record completed actions
        for result in results:
            if result.get("result", {}).get("action") != "none":
                await self.learning.record_event(LearningEvent(
                    event_type=EventType.TASK_COMPLETED,
                    timestamp=datetime.utcnow(),
                    data=result,
                ))

        return results

    async def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """Get proactive suggestions based on current context"""
        prompt = TwinPrompts.get_proactive_suggestion_prompt(
            self.profile,
            {
                "recent_events": [e.to_dict() for e in self.learning.events[-10:]],
            }
        )

        response = await self._ai_generate(
            prompt=prompt,
            system_prompt=await self.get_system_prompt(),
        )

        try:
            import json
            suggestions = json.loads(response)
            return suggestions.get("suggestions", [])
        except json.JSONDecodeError:
            return []


# Factory function for easy service creation
async def get_twin_service(
    user: User,
    db: AsyncSession,
    ai_orchestrator: Optional[SaaSAIOrchestrator] = None,
    rag_service: Optional[AdvancedRAGService] = None,
    mneme_service: Optional[MNEME] = None,
    skills_manager: Optional[SkillsManager] = None,
    calendar_service: Optional[CalendarService] = None
) -> TwinService:
    """
    Create and initialize a TwinService for a user with full integration.

    Integrates:
    - SaaSAIOrchestrator: Multi-model AI routing
    - AdvancedRAGService: Hybrid semantic search
    - MNEME: Persistent knowledge base
    - SkillsManager: Task execution capabilities
    - CalendarService: Schedule awareness and management

    Args:
        user: The user to create the Twin for
        db: Database session
        ai_orchestrator: Optional pre-configured AI orchestrator
        rag_service: Optional pre-configured RAG service
        mneme_service: Optional pre-configured MNEME service
        skills_manager: Optional pre-configured skills manager
        calendar_service: Optional pre-configured calendar service
    """
    service = TwinService(
        user=user,
        db=db,
        ai_orchestrator=ai_orchestrator,
        rag_service=rag_service,
        mneme_service=mneme_service,
        skills_manager=skills_manager,
        calendar_service=calendar_service
    )
    await service.initialize()
    return service


# Convenience function for quick Twin initialization with defaults
async def create_twin_with_defaults(
    user: User,
    db: AsyncSession
) -> TwinService:
    """Create Twin service with all default integrations"""
    user_id = str(user.id) if user.id else None
    tenant_id = user.tenant_id if user.tenant_id else None

    return await get_twin_service(
        user=user,
        db=db,
        ai_orchestrator=create_orchestrator(
            tenant_id=tenant_id,
            user_id=user.id if user.id else None
        ),
        rag_service=AdvancedRAGService(db, user_id),
        mneme_service=MNEME(db, user_id),
        skills_manager=create_skills_manager(
            tenant_id=tenant_id,
            user_id=user.id if user.id else None
        ),
        calendar_service=CalendarService(db, user_id)
    )
