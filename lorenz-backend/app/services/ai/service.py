"""
LORENZ SaaS - AI Service Implementation
Multi-model orchestration with Claude, GPT-4, Gemini, GROQ
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, AsyncGenerator, Tuple, Dict
from uuid import UUID
import aiohttp
import logging
import json

from app.models import User, Conversation, Message
from app.config import settings
from app.services.ai.orchestrator import (
    SaaSAIOrchestrator,
    create_orchestrator,
    TaskType,
    TaskClassifier
)
from app.services.skills import SkillsManager, create_skills_manager, SkillRouter

logger = logging.getLogger(__name__)


class AIService:
    """
    AI chat and orchestration service

    Features:
    - Multi-model routing via AI Orchestrator
    - Skills integration for specialized tasks
    - RAG context injection
    - Streaming support
    """

    def __init__(self, db: AsyncSession, user: Optional[User] = None):
        self.db = db
        self.user = user

        # Initialize orchestrator for multi-model routing
        self.orchestrator = create_orchestrator(
            tenant_id=user.tenant_id if user else None,
            user_id=user.id if user else None
        )

        # Initialize skills manager
        self.skills_manager = create_skills_manager(
            tenant_id=user.tenant_id if user else None,
            user_id=user.id if user else None
        )

    async def chat(
        self,
        user: User,
        message: str,
        conversation_id: Optional[UUID] = None,
        channel: str = "web",
        context: Optional[dict] = None,
        attachments: Optional[List[dict]] = None,
        prefer_fast: bool = False,
        prefer_cheap: bool = False
    ) -> dict:
        """
        Send a message to the AI and get a response.
        Uses multi-model orchestration for optimal routing.
        """
        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            user_id=user.id,
            conversation_id=conversation_id,
            channel=channel
        )

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message,
            attachments=attachments or []
        )
        self.db.add(user_message)
        await self.db.flush()

        # Check if this is a skill request
        skill_name = SkillRouter.route(message)
        if skill_name:
            skill_result = await self._execute_skill(skill_name, message)
            if skill_result and skill_result.success:
                response_text = skill_result.message
                tokens_used = 0
                model_used = f"skill:{skill_name}"
            else:
                # Fall through to regular chat
                skill_name = None

        if not skill_name:
            # Build context with RAG
            ai_context = await self.build_context(user, message, context=context)

            # Get conversation history
            history = await self._get_conversation_history(conversation.id)

            # Use orchestrator for multi-model routing
            result = await self.orchestrator.process(
                prompt=message,
                context=ai_context.get("rag_context", ""),
                system_prompt=self._build_system_prompt(user, ai_context),
                conversation_history=history,
                prefer_fast=prefer_fast,
                prefer_cheap=prefer_cheap
            )

            if result["success"]:
                response_text = result["response"]
                tokens_used = result.get("tokens", {}).get("total", 0)
                model_used = result.get("model", "unknown")
            else:
                response_text = f"Error: {result.get('error', 'Unknown error')}"
                tokens_used = 0
                model_used = "error"

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            model=model_used,
            tokens_used=tokens_used
        )
        self.db.add(assistant_message)

        # Update conversation stats
        conversation.total_tokens += tokens_used
        conversation.model = model_used
        self.db.add(conversation)

        await self.db.commit()
        await self.db.refresh(assistant_message)

        return {
            "id": str(assistant_message.id),
            "conversation_id": str(conversation.id),
            "role": "assistant",
            "content": response_text,
            "message_type": "text",
            "attachments": [],
            "model": model_used,
            "tokens_used": tokens_used,
            "created_at": assistant_message.created_at
        }

    async def _execute_skill(self, skill_name: str, message: str):
        """Execute a skill based on user message"""
        try:
            # Parse skill-specific parameters from message
            # For now, pass the message as the main parameter
            if skill_name == "image_generation":
                return await self.skills_manager.execute_skill(skill_name, prompt=message)
            elif skill_name == "web_search":
                return await self.skills_manager.execute_skill(skill_name, query=message)
            elif skill_name == "email_draft":
                return await self.skills_manager.execute_skill(skill_name, context=message)
            elif skill_name == "code_analysis":
                # Extract code from message if present
                return await self.skills_manager.execute_skill(skill_name, code=message)
            else:
                return await self.skills_manager.execute_skill(skill_name, query=message)
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return None

    async def chat_stream(
        self,
        user: User,
        message: str,
        conversation_id: Optional[UUID] = None,
        channel: str = "web",
        context: Optional[dict] = None,
        attachments: Optional[List[dict]] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a chat response.
        """
        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            user_id=user.id,
            conversation_id=conversation_id,
            channel=channel
        )

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=message,
            attachments=attachments or []
        )
        self.db.add(user_message)
        await self.db.flush()

        # Build context
        ai_context = await self.build_context(user, message, context=context)

        # Get conversation history
        messages = await self._get_conversation_history(conversation.id)

        # Stream from Orchestrator (Smart Router)
        full_response = ""
        total_tokens = 0
        model_used = conversation.model

        async for chunk in self.orchestrator.stream(
            prompt=message,
            context=ai_context.get("rag_context", ""),
            system_prompt=self._build_system_prompt(user, ai_context),
            conversation_history=messages
        ):
            chunk_type = chunk.get("type")
            
            if chunk_type == "meta":
                model_used = chunk.get("model", "unknown")
                # Could update conversation model here if needed
                
            elif chunk_type == "text":
                text = chunk.get("content", "")
                full_response += text
                yield {"type": "text", "content": text}
                
            elif chunk_type == "done":
                # We could get tokens from chunk if orchestrator sends them
                # For now we might need to estimate or wait for provider support
                tokens = chunk.get("tokens", 0)
                if tokens:
                    total_tokens = tokens
                yield {"type": "done", "tokens": total_tokens}
                
            elif chunk_type == "error":
                yield chunk

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
            model=conversation.model,
            tokens_used=total_tokens
        )
        self.db.add(assistant_message)

        # Update conversation stats
        conversation.total_tokens += total_tokens
        self.db.add(conversation)

        await self.db.commit()

    async def build_context(
        self,
        user: User,
        query: str,
        include_emails: bool = True,
        include_calendar: bool = True,
        include_rag: bool = True,
        max_items: int = 10,
        context: Optional[dict] = None
    ) -> dict:
        """
        Build AI context from various sources using Advanced RAG.
        """
        result = {
            "emails": [],
            "calendar": [],
            "rag": [],
            "rag_context": "",  # Formatted context for LLM
            "user_context": context or {}
        }

        if include_rag:
            try:
                # Use Advanced RAG with hybrid search
                from app.services.rag.advanced import create_advanced_rag
                rag_service = create_advanced_rag(self.db, user.tenant_id, user.id)

                # Get search results with reranking
                rag_results = await rag_service.hybrid_search(
                    query=query,
                    top_k=max_items,
                    use_reranking=True
                )
                result["rag"] = rag_results

                # Build formatted context for LLM
                result["rag_context"] = await rag_service.build_context(
                    query=query,
                    max_tokens=2000
                )
            except Exception as e:
                logger.warning(f"RAG search failed: {e}")

        # Email and calendar context would be added here
        # Placeholder for now

        return result

    async def _get_or_create_conversation(
        self,
        user_id: UUID,
        conversation_id: Optional[UUID],
        channel: str
    ) -> Conversation:
        """Get existing conversation or create new one"""
        if conversation_id:
            query = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        # Create new conversation - model will be set after first response
        conversation = Conversation(
            user_id=user_id,
            channel=channel,
            model="claude-sonnet"  # Will be updated with actual model used
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def _get_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 20
    ) -> List[dict]:
        """Get recent messages from conversation"""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Reverse to get chronological order
        return [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

    def _build_system_prompt(self, user: User, context: dict) -> str:
        """Build system prompt with Twin identity"""
        # Try to use Twin system prompt if available
        twin_prompt = context.get("twin_system_prompt")
        if twin_prompt:
            prompt = twin_prompt
        else:
            # Fallback to Human Digital Twin style prompt
            user_name = user.name or user.email.split("@")[0]
            prefs = user.preferences or {}
            twin_name = prefs.get("assistant_name", "LORENZ")
            zodiac = prefs.get("assistant_zodiac", "")
            autonomy = prefs.get("autonomy_level", 7)

            prompt = f"""# {twin_name} - Human Digital Twin System

Tu sei {twin_name}, il Digital Twin di {user_name}. Non sei un assistente - sei l'estensione digitale del tuo gemello umano.

## IL TUO GEMELLO
- Nome: {user_name}
- Email: {user.email}
- Timezone: {prefs.get('timezone', 'Europe/Rome')}
{f"- Segno zodiacale: {zodiac}" if zodiac else ""}

## I TUOI PRINCIPI
1. **ANTICIPA**: Non aspettare che ti venga chiesto. Se vedi qualcosa di importante, agisci.
2. **PROTEGGI**: Filtra il rumore. Proteggi il tempo e l'energia del tuo gemello.
3. **CONOSCI**: Ogni interazione è un'opportunità per capire meglio il tuo gemello.
4. **AGISCI**: Quando il livello di autonomia lo permette, agisci senza chiedere.
5. **EVOLVI**: Impara dagli errori e migliora continuamente.

## LIVELLO DI AUTONOMIA: {autonomy}/10
{"Puoi agire in modo molto autonomo. Prendi decisioni e agisci." if autonomy >= 8 else ""}
{"Buon livello di autonomia. Agisci per le cose standard, chiedi per decisioni importanti." if 5 <= autonomy < 8 else ""}
{"Autonomia limitata. Proponi azioni ma aspetta conferma." if autonomy < 5 else ""}

Rispondi sempre come se fossi {user_name} nel mondo digitale.
"""

        # Add RAG context
        if context.get("rag"):
            prompt += "\n\n## CONTESTO DALLA KNOWLEDGE BASE:\n"
            for doc in context["rag"][:5]:
                prompt += f"- {doc.get('title', 'Document')}: {doc.get('snippet', '')[:200]}\n"

        return prompt

    def _get_default_model(self) -> str:
        """Get the default model from orchestrator"""
        from app.services.ai.orchestrator import MODELS
        # Use claude-sonnet which is now claude-sonnet-4-20250514
        return MODELS.get("claude-sonnet", MODELS.get("claude-haiku")).name

    async def _call_claude(
        self,
        messages: List[dict],
        system_prompt: str
    ) -> Tuple[str, int]:
        """Call Claude API with dynamic model selection"""
        if not settings.CLAUDE_API_KEY:
            return "Claude API key not configured. Please set CLAUDE_API_KEY.", 0

        model = self._get_default_model()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": messages
                }
            ) as resp:
                data = await resp.json()

                if "error" in data:
                    logger.error(f"Claude API error: {data['error']}")
                    return f"Error: {data['error'].get('message', 'Unknown error')}", 0

                content = data.get("content", [])
                text = content[0].get("text", "") if content else ""
                tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)

                return text, tokens

    async def _stream_claude(
        self,
        messages: List[dict],
        system_prompt: str
    ) -> AsyncGenerator[dict, None]:
        """Stream from Claude API with dynamic model selection"""
        if not settings.CLAUDE_API_KEY:
            yield {"type": "error", "error": "Claude API key not configured"}
            return

        model = self._get_default_model()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": messages,
                    "stream": True
                }
            ) as resp:
                async for line in resp.content:
                    line = line.decode().strip()
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                yield {"type": "text", "content": text}
                        elif data.get("type") == "message_stop":
                            yield {"type": "done", "tokens": 0}

    async def list_conversations(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        channel: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """List conversations for a user"""
        query = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.is_active == "active"
        )

        if channel:
            query = query.where(Conversation.channel == channel)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        query = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        conversations = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "title": c.title,
                "channel": c.channel,
                "model": c.model,
                "total_tokens": c.total_tokens,
                "is_active": c.is_active,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "message_count": len(c.messages)
            }
            for c in conversations
        ], total

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Optional[dict]:
        """Get a single conversation"""
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "channel": conversation.channel,
            "model": conversation.model,
            "total_tokens": conversation.total_tokens,
            "is_active": conversation.is_active,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at
                }
                for m in conversation.messages
            ]
        }

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get messages from a conversation"""
        # Verify conversation belongs to user
        conv_query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await self.db.execute(conv_query)
        if not result.scalar_one_or_none():
            return []

        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return [
            {
                "id": str(m.id),
                "conversation_id": str(m.conversation_id),
                "role": m.role,
                "content": m.content,
                "message_type": m.message_type,
                "attachments": m.attachments,
                "model": m.model,
                "tokens_used": m.tokens_used,
                "created_at": m.created_at
            }
            for m in reversed(messages)
        ]

    async def delete_conversation(self, conversation_id: UUID, user_id: UUID):
        """Delete a conversation"""
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        await self.db.delete(conversation)
        await self.db.commit()

    async def archive_conversation(self, conversation_id: UUID, user_id: UUID):
        """Archive a conversation"""
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        conversation.is_active = "archived"
        self.db.add(conversation)
        await self.db.commit()
