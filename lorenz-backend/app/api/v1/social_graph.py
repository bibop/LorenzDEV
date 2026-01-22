"""
LORENZ SaaS - Social Graph API Endpoints
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.social_graph import (
    SocialGraphService,
    OpportunityDetector
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/social-graph", tags=["social-graph"])


# ==================== SCHEMAS ====================

class ContactResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    company: Optional[str]
    role: Optional[str]
    relationship_type: str
    total_interactions: int
    x: float = 0
    y: float = 0
    z: float = 0
    size: float = 1
    color: str = "#9E9E9E"
    avatar: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None

    class Config:
        from_attributes = True


class GraphDataResponse(BaseModel):
    nodes: List[dict]
    edges: List[dict]
    stats: dict


class ImportResponse(BaseModel):
    imported: int
    merged: int
    errors: int


class OpportunityResponse(BaseModel):
    id: str
    contact_id: str
    contact_name: Optional[str] = None
    opportunity_type: str
    title: str
    description: Optional[str]
    confidence_score: float
    priority: int
    potential_value: Optional[str]
    status: str
    suggested_action: Optional[str]
    identified_at: Optional[str]


class SearchQuery(BaseModel):
    query: str
    limit: int = 20


# ==================== ENDPOINTS ====================

@router.get("/data", response_model=GraphDataResponse)
async def get_graph_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete graph data for 3D visualization"""
    service = SocialGraphService(db)
    data = await service.get_graph_data(current_user.id)
    return data


@router.post("/calculate-positions")
async def calculate_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recalculate 3D positions for all contacts"""
    service = SocialGraphService(db)
    await service.calculate_graph_positions(current_user.id)
    return {"status": "success", "message": "Positions recalculated"}


@router.get("/contacts", response_model=List[ContactResponse])
async def search_contacts(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search contacts by name, email, or company"""
    service = SocialGraphService(db)
    results = await service.search_contacts(current_user.id, q, limit)
    return results


@router.get("/contacts/{contact_id}")
async def get_contact(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed contact information"""
    from app.models.social_graph import UnifiedContact

    contact = db.query(UnifiedContact).filter(
        UnifiedContact.id == contact_id,
        UnifiedContact.user_id == current_user.id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return {
        'id': str(contact.id),
        'name': contact.name,
        'email': contact.primary_email,
        'all_emails': contact.all_emails,
        'phone': contact.primary_phone,
        'all_phones': contact.all_phones,
        'company': contact.company,
        'role': contact.job_title,
        'industry': contact.industry,
        'linkedin_url': contact.linkedin_url,
        'twitter_handle': contact.twitter_handle,
        'city': contact.city,
        'country': contact.country,
        'avatar_url': contact.avatar_url,
        'relationship_type': contact.relationship_type.value if contact.relationship_type else 'other',
        'relationship_strength': contact.relationship_strength,
        'tags': contact.tags,
        'notes': contact.notes,
        'total_interactions': contact.total_interactions,
        'email_interactions': contact.email_interactions,
        'whatsapp_interactions': contact.whatsapp_interactions,
        'linkedin_interactions': contact.linkedin_interactions,
        'call_interactions': contact.call_interactions,
        'meeting_interactions': contact.meeting_interactions,
        'first_interaction': contact.first_interaction.isoformat() if contact.first_interaction else None,
        'last_interaction': contact.last_interaction.isoformat() if contact.last_interaction else None,
        'ai_summary': contact.ai_summary,
        'source_data': contact.source_data,
    }


@router.patch("/contacts/{contact_id}")
async def update_contact(
    contact_id: UUID,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update contact information"""
    from app.models.social_graph import UnifiedContact, RelationshipType

    contact = db.query(UnifiedContact).filter(
        UnifiedContact.id == contact_id,
        UnifiedContact.user_id == current_user.id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Update allowed fields
    allowed_fields = [
        'name', 'company', 'job_title', 'industry',
        'city', 'country', 'tags', 'notes'
    ]

    for field in allowed_fields:
        if field in updates:
            setattr(contact, field, updates[field])

    # Handle relationship_type separately
    if 'relationship_type' in updates:
        try:
            contact.relationship_type = RelationshipType(updates['relationship_type'])
        except ValueError:
            pass

    db.commit()
    return {"status": "success", "message": "Contact updated"}


# ==================== IMPORT ENDPOINTS ====================

@router.post("/import/email", response_model=ImportResponse)
async def import_email_contacts(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import contacts from email extraction JSON file"""
    import tempfile
    import os

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = SocialGraphService(db)
        stats = await service.import_email_contacts(current_user.id, tmp_path)

        # Recalculate positions after import
        await service.calculate_graph_positions(current_user.id)

        return stats
    finally:
        os.unlink(tmp_path)


@router.post("/import/whatsapp", response_model=ImportResponse)
async def import_whatsapp_chat(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import contacts from WhatsApp chat export (.txt file)"""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = SocialGraphService(db)
        stats = await service.import_whatsapp_chat(current_user.id, tmp_path)

        # Recalculate positions after import
        await service.calculate_graph_positions(current_user.id)

        return stats
    finally:
        os.unlink(tmp_path)


@router.post("/import/linkedin", response_model=ImportResponse)
async def import_linkedin_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import contacts from LinkedIn data export (ZIP file)"""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = SocialGraphService(db)
        stats = await service.import_linkedin_data(current_user.id, tmp_path)

        # Recalculate positions after import
        await service.calculate_graph_positions(current_user.id)

        return stats
    finally:
        os.unlink(tmp_path)


# ==================== OPPORTUNITY ENDPOINTS ====================

@router.post("/opportunities/detect")
async def detect_opportunities(
    days_lookback: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect opportunities from contact interactions"""
    detector = OpportunityDetector(db)

    opportunities = await detector.detect_opportunities(
        current_user.id,
        days_lookback=days_lookback
    )

    # Save to database
    saved = await detector.save_opportunities(current_user.id, opportunities)

    return {
        "detected": len(opportunities),
        "saved": saved,
        "opportunities": opportunities[:20]  # Return top 20
    }


@router.get("/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detected opportunities"""
    detector = OpportunityDetector(db)
    opportunities = await detector.get_opportunities(
        current_user.id,
        status=status,
        limit=limit
    )

    # Add contact names
    from app.models.social_graph import UnifiedContact

    for opp in opportunities:
        contact = db.query(UnifiedContact).filter(
            UnifiedContact.id == opp['contact_id']
        ).first()
        if contact:
            opp['contact_name'] = contact.name

    return opportunities


@router.patch("/opportunities/{opportunity_id}")
async def update_opportunity(
    opportunity_id: UUID,
    status: str = Query(..., regex="^(identified|reviewing|pursuing|won|lost|dismissed)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update opportunity status"""
    from app.models.social_graph import ContactOpportunity
    from datetime import datetime

    opp = db.query(ContactOpportunity).filter(
        ContactOpportunity.id == opportunity_id,
        ContactOpportunity.user_id == current_user.id
    ).first()

    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp.status = status

    if status == 'reviewing':
        opp.reviewed_at = datetime.utcnow()
    elif status in ['pursuing', 'won', 'lost']:
        opp.actioned_at = datetime.utcnow()

    db.commit()
    return {"status": "success", "message": f"Opportunity status updated to {status}"}


# ==================== STATS ENDPOINTS ====================

# ==================== APIFY IMPORT ENDPOINTS ====================

class ApifyWhatsAppImportRequest(BaseModel):
    phone_numbers: Optional[List[str]] = None
    group_names: Optional[List[str]] = None
    max_messages: int = 100


class ApifyLinkedInImportRequest(BaseModel):
    profile_urls: List[str]


class ApifyLinkedInSearchRequest(BaseModel):
    query: str
    max_results: int = 50
    location: Optional[str] = None


class ApifyTwitterImportRequest(BaseModel):
    usernames: List[str]
    include_tweets: bool = True


class ApifyRunStatusResponse(BaseModel):
    run_id: str
    status: str
    message: str


class ApifyImportResult(BaseModel):
    success: bool
    source: str
    contacts_imported: int
    run_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/import/apify/whatsapp", response_model=ApifyImportResult)
async def import_whatsapp_via_apify(
    request: ApifyWhatsAppImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import WhatsApp contacts and messages via Apify scraper.

    NOTE: First run requires WhatsApp Web QR code authentication in Apify console.
    The actor will prompt for QR scan if not already authenticated.
    """
    from app.services.social_graph.apify_service import SocialGraphApifyImporter
    from app.config import settings

    if not settings.APIFY_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Apify API key not configured. Set APIFY_API_KEY in environment."
        )

    try:
        importer = SocialGraphApifyImporter()
        result = await importer.import_whatsapp_chats(
            phone_numbers=request.phone_numbers,
            group_names=request.group_names,
            max_messages=request.max_messages
        )

        if result["success"]:
            # Save contacts to database
            service = SocialGraphService(db)
            stats = await service.import_from_apify_results(
                user_id=current_user.id,
                contacts=result["contacts"],
                source="whatsapp"
            )

            return ApifyImportResult(
                success=True,
                source="whatsapp",
                contacts_imported=stats.get("imported", 0)
            )
        else:
            return ApifyImportResult(
                success=False,
                source="whatsapp",
                contacts_imported=0,
                run_id=result.get("run_id"),
                error=result.get("error")
            )

    except Exception as e:
        logger.error(f"Apify WhatsApp import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/apify/linkedin", response_model=ApifyImportResult)
async def import_linkedin_via_apify(
    request: ApifyLinkedInImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import LinkedIn profiles via Apify scraper.

    Provide a list of LinkedIn profile URLs to scrape.
    """
    from app.services.social_graph.apify_service import SocialGraphApifyImporter
    from app.config import settings

    if not settings.APIFY_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Apify API key not configured. Set APIFY_API_KEY in environment."
        )

    if not request.profile_urls:
        raise HTTPException(status_code=400, detail="No profile URLs provided")

    try:
        importer = SocialGraphApifyImporter()
        result = await importer.import_linkedin_connections(
            profile_urls=request.profile_urls
        )

        if result["success"]:
            # Save contacts to database
            service = SocialGraphService(db)
            stats = await service.import_from_apify_results(
                user_id=current_user.id,
                contacts=result["contacts"],
                source="linkedin"
            )

            return ApifyImportResult(
                success=True,
                source="linkedin",
                contacts_imported=stats.get("imported", 0)
            )
        else:
            return ApifyImportResult(
                success=False,
                source="linkedin",
                contacts_imported=0,
                run_id=result.get("run_id"),
                error=result.get("error")
            )

    except Exception as e:
        logger.error(f"Apify LinkedIn import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/apify/linkedin/search", response_model=ApifyImportResult)
async def search_and_import_linkedin_via_apify(
    request: ApifyLinkedInSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search LinkedIn by keywords and import matching profiles.

    Example queries: "CEO tech startup", "VP Engineering AI", "Investor cleantech"
    """
    from app.services.social_graph.apify_service import SocialGraphApifyImporter
    from app.config import settings

    if not settings.APIFY_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Apify API key not configured. Set APIFY_API_KEY in environment."
        )

    try:
        importer = SocialGraphApifyImporter()
        result = await importer.search_and_import_linkedin(
            search_query=request.query,
            max_results=request.max_results,
            location=request.location
        )

        if result["success"]:
            # Save contacts to database
            service = SocialGraphService(db)
            stats = await service.import_from_apify_results(
                user_id=current_user.id,
                contacts=result["contacts"],
                source="linkedin"
            )

            return ApifyImportResult(
                success=True,
                source="linkedin_search",
                contacts_imported=stats.get("imported", 0)
            )
        else:
            return ApifyImportResult(
                success=False,
                source="linkedin_search",
                contacts_imported=0,
                run_id=result.get("run_id"),
                error=result.get("error")
            )

    except Exception as e:
        logger.error(f"Apify LinkedIn search import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/apify/twitter", response_model=ApifyImportResult)
async def import_twitter_via_apify(
    request: ApifyTwitterImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import Twitter/X profiles via Apify scraper.

    Provide a list of Twitter usernames (without @).
    """
    from app.services.social_graph.apify_service import SocialGraphApifyImporter
    from app.config import settings

    if not settings.APIFY_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Apify API key not configured. Set APIFY_API_KEY in environment."
        )

    if not request.usernames:
        raise HTTPException(status_code=400, detail="No usernames provided")

    try:
        importer = SocialGraphApifyImporter()
        result = await importer.import_twitter_profiles(
            usernames=request.usernames,
            include_tweets=request.include_tweets
        )

        if result["success"]:
            # Save contacts to database
            service = SocialGraphService(db)
            stats = await service.import_from_apify_results(
                user_id=current_user.id,
                contacts=result["contacts"],
                source="twitter"
            )

            return ApifyImportResult(
                success=True,
                source="twitter",
                contacts_imported=stats.get("imported", 0)
            )
        else:
            return ApifyImportResult(
                success=False,
                source="twitter",
                contacts_imported=0,
                run_id=result.get("run_id"),
                error=result.get("error")
            )

    except Exception as e:
        logger.error(f"Apify Twitter import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apify/status")
async def get_apify_status(
    current_user: User = Depends(get_current_user)
):
    """Check if Apify is configured and available"""
    from app.config import settings

    return {
        "configured": bool(settings.APIFY_API_KEY),
        "whatsapp_actor": settings.APIFY_WHATSAPP_ACTOR_ID,
        "linkedin_actor": settings.APIFY_LINKEDIN_ACTOR_ID,
        "linkedin_bulk_actor": settings.APIFY_LINKEDIN_BULK_ACTOR_ID
    }


# ==================== STATS ENDPOINTS ====================

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get social graph statistics"""
    from app.models.social_graph import UnifiedContact, ContactOpportunity
    from sqlalchemy import func

    # Contact stats
    total_contacts = db.query(func.count(UnifiedContact.id)).filter(
        UnifiedContact.user_id == current_user.id
    ).scalar()

    total_interactions = db.query(func.sum(UnifiedContact.total_interactions)).filter(
        UnifiedContact.user_id == current_user.id
    ).scalar() or 0

    # Relationship type distribution
    rel_distribution = db.query(
        UnifiedContact.relationship_type,
        func.count(UnifiedContact.id)
    ).filter(
        UnifiedContact.user_id == current_user.id
    ).group_by(UnifiedContact.relationship_type).all()

    # Opportunity stats
    open_opportunities = db.query(func.count(ContactOpportunity.id)).filter(
        ContactOpportunity.user_id == current_user.id,
        ContactOpportunity.status.in_(['identified', 'reviewing', 'pursuing'])
    ).scalar()

    return {
        'total_contacts': total_contacts,
        'total_interactions': total_interactions,
        'relationship_distribution': {
            (r.value if r else 'other'): count
            for r, count in rel_distribution
        },
        'open_opportunities': open_opportunities
    }
