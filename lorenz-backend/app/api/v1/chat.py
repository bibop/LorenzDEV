"""
LORENZ SaaS - Chat Routes
Human Digital Twin Integration with RAG and MNEME
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging
import json

from app.database import get_db
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    ConversationListResponse,
)
from app.services.ai import AIService
from app.services.twin import get_twin_service, TwinService
from app.api.deps import get_current_user
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to LORENZ - Human Digital Twin.

    The Twin processes messages with full context awareness:
    - RAG context from hybrid search (vector + BM25 + reranking)
    - MNEME knowledge (facts, preferences, patterns)
    - User profile and preferences
    - Learned patterns and behaviors
    - Active projects and VIP contacts
    - Proactive insights and suggestions
    """
    from app.models import Conversation, Message
    from datetime import datetime

    try:
        # Initialize Twin for this user with full RAG/MNEME integration
        twin = await get_twin_service(current_user, db)

        # Build context from request
        context = request.context or {}
        if request.attachments:
            context["attachments"] = request.attachments
        context["channel"] = request.channel

        # Process message through Twin with full RAG/MNEME integration
        # This automatically:
        # - Fetches RAG context (hybrid search)
        # - Queries MNEME knowledge
        # - Applies user preferences
        # - Learns from conversation
        twin_response = await twin.process_message(
            message=request.message,
            context=context
        )

        # Get or create conversation
        conversation = None
        if request.conversation_id:
            from sqlalchemy import select
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == request.conversation_id,
                    Conversation.user_id == current_user.id
                )
            )
            conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(
                user_id=current_user.id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                channel=request.channel or "web",
                model="twin",
                metadata={"twin_processed": True}
            )
            db.add(conversation)
            await db.flush()

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            attachments=request.attachments or []
        )
        db.add(user_msg)

        # Save assistant (Twin) response
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=twin_response,
            model="twin_rag_mneme",
            metadata={
                "twin_processed": True,
                "rag_enabled": True,
                "mneme_enabled": True,
            }
        )
        db.add(assistant_msg)

        await db.commit()
        await db.refresh(assistant_msg)

        return {
            "id": str(assistant_msg.id),
            "conversation_id": str(conversation.id),
            "role": "assistant",
            "content": twin_response,
            "message_type": "text",
            "attachments": [],
            "model": "twin_rag_mneme",
            "tokens_used": assistant_msg.tokens_used or 0,
            "created_at": assistant_msg.created_at,
        }

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and stream the response from Human Digital Twin.

    Includes:
    - RAG context from hybrid search
    - MNEME knowledge integration
    - Real-time streaming with Twin personality
    """
    # Initialize Twin with full RAG/MNEME integration
    twin = None
    rag_context = ""
    mneme_context = ""

    try:
        twin = await get_twin_service(current_user, db)

        # Pre-fetch RAG and MNEME context for streaming
        rag_context = await twin._get_rag_context(
            request.message,
            source_types=["document", "email", "note"],
            top_k=5
        )

        mneme_results = await twin._search_mneme_knowledge(
            request.message,
            semantic=True,
            limit=5
        )
        if mneme_results:
            mneme_context = "\n".join([
                f"- {r.get('title', '')}: {r.get('content', '')[:200]}"
                for r in mneme_results
            ])

    except Exception as twin_err:
        logger.warning(f"Twin initialization failed, using fallback: {twin_err}")

    # Build enhanced context with RAG and MNEME
    enhanced_context = request.context or {}
    if twin:
        enhanced_context["twin_system_prompt"] = await twin.get_system_prompt()
        enhanced_context["twin_profile"] = {
            "name": twin.profile.preferred_name,
            "autonomy_level": twin.profile.autonomy_level,
        }
        enhanced_context["rag_context"] = rag_context
        enhanced_context["mneme_context"] = mneme_context

    ai_service = AIService(db)

    async def generate():
        full_response = ""
        try:
            # Send initial metadata
            yield f"data: {json.dumps({'type': 'meta', 'rag_enabled': bool(rag_context), 'mneme_enabled': bool(mneme_context)})}\n\n"

            async for chunk in ai_service.chat_stream(
                user=current_user,
                message=request.message,
                conversation_id=request.conversation_id,
                channel=request.channel,
                context=enhanced_context,
                attachments=request.attachments
            ):
                if chunk.get("type") == "text":
                    full_response += chunk.get("content", "")
                yield f"data: {json.dumps(chunk)}\n\n"

            # Learn from conversation after stream completes
            if twin:
                try:
                    await twin._learn_from_conversation(request.message, full_response)
                except Exception as learn_err:
                    logger.warning(f"Failed to learn from conversation: {learn_err}")

            # Send completion with metadata
            yield f"data: {json.dumps({'type': 'done', 'twin_processed': twin is not None})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    channel: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List conversations for current user.
    """
    ai_service = AIService(db)
    conversations, total = await ai_service.list_conversations(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        channel=channel
    )
    return ConversationListResponse(
        conversations=conversations,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific conversation with all messages.
    """
    ai_service = AIService(db)
    conversation = await ai_service.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages from a conversation.
    """
    ai_service = AIService(db)
    messages = await ai_service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    return messages


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    """
    ai_service = AIService(db)
    try:
        await ai_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        return {"message": "Conversation deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive a conversation.
    """
    ai_service = AIService(db)
    try:
        await ai_service.archive_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        return {"message": "Conversation archived"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/context")
async def get_ai_context(
    query: str,
    include_emails: bool = True,
    include_calendar: bool = True,
    include_rag: bool = True,
    max_items: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI context for a query without sending a full message.
    Useful for previewing what context will be used.
    """
    ai_service = AIService(db)
    context = await ai_service.build_context(
        user=current_user,
        query=query,
        include_emails=include_emails,
        include_calendar=include_calendar,
        include_rag=include_rag,
        max_items=max_items
    )
    return context
