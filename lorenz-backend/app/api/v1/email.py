"""
LORENZ SaaS - Email Routes
With Human Digital Twin Integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.schemas.email import (
    EmailAccountCreate,
    EmailAccountUpdate,
    EmailAccountResponse,
    EmailMessageResponse,
    EmailSendRequest,
    EmailSendResponse,
    EmailSearchRequest,
    EmailStatsResponse,
)
from app.services.email import EmailService
from app.services.twin import get_twin_service
from app.api.deps import get_current_user
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


# Twin Integration Request/Response Models
class TwinAnalyzeEmailRequest(BaseModel):
    """Request to analyze email with Twin"""
    from_address: str = Field(..., alias="from")
    subject: str
    body: str
    message_id: Optional[str] = None

    class Config:
        populate_by_name = True


class TwinDraftRequest(BaseModel):
    """Request Twin to draft response"""
    original_from: str
    original_subject: str
    original_body: str
    intent: str = "professional"  # professional, friendly, formal, brief


class TwinSmartInboxRequest(BaseModel):
    """Request for smart inbox prioritization"""
    account_id: Optional[UUID] = None
    limit: int = 50


# Email Account Management

@router.get("/accounts", response_model=List[EmailAccountResponse])
async def list_email_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all email accounts for current user.
    """
    from sqlalchemy import select
    from app.models import EmailAccount

    query = select(EmailAccount).where(EmailAccount.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/accounts", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_email_account(
    account_data: EmailAccountCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new email account (IMAP).
    For Gmail/Outlook, use OAuth flow instead.
    """
    email_service = EmailService(db)
    try:
        account = await email_service.create_imap_account(
            user=current_user,
            **account_data.model_dump()
        )

        # Start background sync
        background_tasks.add_task(
            email_service.sync_account,
            account.id
        )

        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/accounts/{account_id}", response_model=EmailAccountResponse)
async def update_email_account(
    account_id: UUID,
    update_data: EmailAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an email account.
    """
    email_service = EmailService(db)
    try:
        account = await email_service.update_account(
            account_id=account_id,
            user_id=current_user.id,
            **update_data.model_dump(exclude_unset=True)
        )
        return account
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/accounts/{account_id}")
async def delete_email_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an email account.
    """
    email_service = EmailService(db)
    try:
        await email_service.delete_account(account_id, current_user.id)
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/accounts/{account_id}/sync")
async def sync_email_account(
    account_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger sync for an email account.
    """
    email_service = EmailService(db)

    # Verify account belongs to user
    account = await email_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Start background sync
    background_tasks.add_task(
        email_service.sync_account,
        account_id
    )

    return {"message": "Sync started", "account_id": str(account_id)}


# Email Messages

@router.get("/messages", response_model=List[EmailMessageResponse])
async def list_emails(
    account_id: Optional[UUID] = None,
    folder: str = "INBOX",
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List emails from one or all accounts.
    """
    email_service = EmailService(db)
    messages = await email_service.list_messages(
        user_id=current_user.id,
        account_id=account_id,
        folder=folder,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )
    return messages


@router.get("/messages/{account_id}/{message_id}", response_model=EmailMessageResponse)
async def get_email(
    account_id: UUID,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific email by ID.
    """
    email_service = EmailService(db)
    try:
        message = await email_service.get_message(
            user_id=current_user.id,
            account_id=account_id,
            message_id=message_id
        )
        return message
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    request: EmailSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send an email.
    """
    email_service = EmailService(db)
    try:
        result = await email_service.send_email(
            user_id=current_user.id,
            **request.model_dump()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/messages/{account_id}/{message_id}/mark-read")
async def mark_email_read(
    account_id: UUID,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an email as read.
    """
    email_service = EmailService(db)
    try:
        await email_service.mark_read(
            user_id=current_user.id,
            account_id=account_id,
            message_id=message_id
        )
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/search")
async def search_emails(
    request: EmailSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search emails across accounts.
    """
    email_service = EmailService(db)
    results = await email_service.search(
        user_id=current_user.id,
        **request.model_dump()
    )
    return {"results": results, "total": len(results)}


@router.get("/stats", response_model=EmailStatsResponse)
async def get_email_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get email statistics for current user.
    """
    email_service = EmailService(db)
    stats = await email_service.get_stats(current_user.id)
    return stats


# ===================
# Twin Integration Endpoints
# ===================

@router.post("/twin/analyze")
async def twin_analyze_email(
    request: TwinAnalyzeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze an email using the Human Digital Twin.

    Returns:
    - Priority level (critical, high, medium, low)
    - Recommended actions
    - Sender insights (if known contact)
    - Project relevance
    - Auto-response suggestion (if applicable)
    """
    try:
        twin = await get_twin_service(current_user, db)

        email_data = {
            "from": request.from_address,
            "subject": request.subject,
            "body": request.body,
            "message_id": request.message_id,
        }

        analysis = await twin.analyze_email(email_data)

        # Check if should auto-respond
        auto_response = await twin.should_auto_respond(email_data)

        return {
            "analysis": analysis,
            "auto_response_suggested": auto_response is not None,
            "auto_response_details": auto_response,
        }
    except Exception as e:
        logger.error(f"Twin email analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze email")


@router.post("/twin/draft")
async def twin_draft_response(
    request: TwinDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a draft email response using the Human Digital Twin.

    The Twin will:
    - Write in the user's communication style
    - Use appropriate tone based on sender relationship
    - Include relevant context from projects/history
    """
    try:
        twin = await get_twin_service(current_user, db)

        email_data = {
            "from": request.original_from,
            "subject": request.original_subject,
            "body": request.original_body,
        }

        draft = await twin.draft_email_response(email_data, request.intent)

        return {
            "draft": draft,
            "intent": request.intent,
            "suggested_subject": f"Re: {request.original_subject}",
        }
    except Exception as e:
        logger.error(f"Twin draft error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate draft")


@router.post("/twin/smart-inbox")
async def twin_smart_inbox(
    request: TwinSmartInboxRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a smart prioritized inbox view using the Human Digital Twin.

    Emails are categorized and prioritized based on:
    - VIP contacts (highest priority)
    - Active projects (high priority)
    - Learned patterns (medium priority)
    - Everything else (normal)
    """
    try:
        twin = await get_twin_service(current_user, db)
        email_service = EmailService(db)

        # Get raw emails
        messages = await email_service.list_messages(
            user_id=current_user.id,
            account_id=request.account_id,
            folder="INBOX",
            limit=request.limit,
            offset=0,
            unread_only=False
        )

        # Categorize emails using Twin
        categorized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        vip_contacts = twin.profile.vip_contacts
        project_keywords = []
        for project in twin.profile.projects:
            if project.status == "active":
                project_keywords.extend(project.related_emails_keywords)

        for msg in messages:
            sender = msg.get("from_address", msg.get("from", ""))
            subject = msg.get("subject", "")

            # Check VIP
            if any(vip.lower() in sender.lower() for vip in vip_contacts):
                categorized["critical"].append({
                    **msg,
                    "twin_category": "vip",
                    "twin_reason": "VIP contact",
                })
            # Check project relevance
            elif any(kw.lower() in subject.lower() for kw in project_keywords):
                categorized["high"].append({
                    **msg,
                    "twin_category": "project",
                    "twin_reason": "Project related",
                })
            # Check if unread
            elif not msg.get("is_read", True):
                categorized["medium"].append({
                    **msg,
                    "twin_category": "unread",
                    "twin_reason": "Unread message",
                })
            else:
                categorized["low"].append({
                    **msg,
                    "twin_category": "normal",
                    "twin_reason": "Normal priority",
                })

        return {
            "categorized": categorized,
            "stats": {
                "critical": len(categorized["critical"]),
                "high": len(categorized["high"]),
                "medium": len(categorized["medium"]),
                "low": len(categorized["low"]),
                "total": len(messages),
            },
            "vip_count": len(vip_contacts),
            "active_projects": len([p for p in twin.profile.projects if p.status == "active"]),
        }
    except Exception as e:
        logger.error(f"Twin smart inbox error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate smart inbox")


@router.post("/index-to-rag")
async def index_emails_to_rag(
    account_id: Optional[UUID] = None,
    limit: int = 50,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Index emails to RAG knowledge base for semantic search.

    This allows searching emails using natural language queries
    in the chat and document search interfaces.
    """
    from app.services.rag import RAGService

    try:
        email_service = EmailService(db)
        rag_service = RAGService(db)

        # Get emails to index
        messages = await email_service.list_messages(
            user_id=current_user.id,
            account_id=account_id,
            folder="INBOX",
            limit=limit,
            offset=0,
            unread_only=False
        )

        if not messages:
            return {
                "message": "No emails to index",
                "indexed": 0,
                "skipped": 0
            }

        # Prepare emails for indexing
        emails_to_index = []
        for msg in messages:
            emails_to_index.append({
                "message_id": msg.get("id", ""),
                "from_address": msg.get("from_address", msg.get("from", "")),
                "to_addresses": msg.get("to_addresses", msg.get("to", [])),
                "subject": msg.get("subject", ""),
                "body": msg.get("body", msg.get("snippet", ""))[:10000],
                "date": msg.get("date", msg.get("received_at")),
                "attachments": msg.get("attachments", [])
            })

        # Index to RAG
        result = await rag_service.index_emails_batch(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            emails=emails_to_index
        )

        return {
            "message": "Email indexing completed",
            "indexed": result["indexed"],
            "skipped": result["skipped"],
            "errors": len(result.get("errors", []))
        }

    except Exception as e:
        logger.error(f"Email RAG indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to index emails")


@router.post("/twin/batch-analyze")
async def twin_batch_analyze(
    account_id: Optional[UUID] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch analyze recent emails with the Twin.
    Useful for getting a quick overview of inbox state.
    """
    try:
        twin = await get_twin_service(current_user, db)
        email_service = EmailService(db)

        # Get recent unread emails
        messages = await email_service.list_messages(
            user_id=current_user.id,
            account_id=account_id,
            folder="INBOX",
            limit=limit,
            offset=0,
            unread_only=True
        )

        results = []
        for msg in messages:
            email_data = {
                "from": msg.get("from_address", msg.get("from", "")),
                "subject": msg.get("subject", ""),
                "body": msg.get("snippet", msg.get("body", ""))[:1000],  # Limit body for batch
            }

            # Quick analysis using proactive engine
            analysis = await twin.proactive.analyze_email(email_data)

            results.append({
                "message_id": msg.get("id"),
                "from": email_data["from"],
                "subject": email_data["subject"],
                "priority": analysis.get("priority", "medium"),
                "actions": analysis.get("actions", []),
                "is_vip": analysis.get("is_vip", False),
            })

        return {
            "analyzed": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Twin batch analyze error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to batch analyze")
