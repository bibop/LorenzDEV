"""
LORENZ SaaS - Opportunity Detector
AI-powered opportunity identification from social graph
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.social_graph import (
    UnifiedContact, ContactInteraction, ContactOpportunity,
    RelationshipType, OpportunityType
)

logger = logging.getLogger(__name__)


class OpportunityDetector:
    """
    AI-powered opportunity detection from contact interactions

    Analyzes:
    - Interaction patterns (frequency, recency, sentiment)
    - Relationship strength trends
    - Network effects (mutual connections)
    - Content analysis (topics, intentions)
    """

    def __init__(self, db: Session, ai_client=None):
        self.db = db
        self.ai_client = ai_client  # Claude AI client for advanced analysis

    async def detect_opportunities(
        self,
        user_id: UUID,
        days_lookback: int = 90
    ) -> List[Dict]:
        """
        Detect opportunities across all contacts

        Returns list of identified opportunities
        """
        opportunities = []
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)

        contacts = self.db.query(UnifiedContact).filter(
            UnifiedContact.user_id == user_id
        ).all()

        for contact in contacts:
            contact_opps = await self._analyze_contact(contact, cutoff_date)
            opportunities.extend(contact_opps)

        # Sort by priority and confidence
        opportunities.sort(
            key=lambda x: (x['priority'], x['confidence_score']),
            reverse=True
        )

        return opportunities

    async def _analyze_contact(
        self,
        contact: UnifiedContact,
        cutoff_date: datetime
    ) -> List[Dict]:
        """Analyze single contact for opportunities"""
        opportunities = []

        # 1. Check for follow-up opportunities (inactive high-value contacts)
        follow_up = self._check_follow_up_opportunity(contact, cutoff_date)
        if follow_up:
            opportunities.append(follow_up)

        # 2. Check for relationship upgrade opportunities
        upgrade = self._check_relationship_upgrade(contact)
        if upgrade:
            opportunities.append(upgrade)

        # 3. Check for introduction opportunities
        intro = self._check_introduction_opportunity(contact)
        if intro:
            opportunities.append(intro)

        # 4. Check for investment opportunities
        investment = self._check_investment_opportunity(contact)
        if investment:
            opportunities.append(investment)

        # 5. Check for partnership opportunities
        partnership = self._check_partnership_opportunity(contact)
        if partnership:
            opportunities.append(partnership)

        return opportunities

    def _check_follow_up_opportunity(
        self,
        contact: UnifiedContact,
        cutoff_date: datetime
    ) -> Optional[Dict]:
        """Check if contact needs follow-up"""

        # Skip if no last interaction
        if not contact.last_interaction:
            return None

        # Important relationship types that warrant follow-up
        important_types = [
            RelationshipType.INVESTOR,
            RelationshipType.POTENTIAL_INVESTOR,
            RelationshipType.PARTNER,
            RelationshipType.POTENTIAL_PARTNER,
            RelationshipType.CLIENT,
            RelationshipType.POTENTIAL_CLIENT,
            RelationshipType.POLITICAL_STAKEHOLDER,
        ]

        if contact.relationship_type not in important_types:
            return None

        days_since_contact = (datetime.utcnow() - contact.last_interaction).days

        # Thresholds based on relationship type
        thresholds = {
            RelationshipType.INVESTOR: 30,
            RelationshipType.POTENTIAL_INVESTOR: 14,
            RelationshipType.PARTNER: 30,
            RelationshipType.POTENTIAL_PARTNER: 14,
            RelationshipType.CLIENT: 45,
            RelationshipType.POTENTIAL_CLIENT: 14,
            RelationshipType.POLITICAL_STAKEHOLDER: 60,
        }

        threshold = thresholds.get(contact.relationship_type, 30)

        if days_since_contact < threshold:
            return None

        # Calculate priority based on interaction history and time
        priority = min(10, 5 + (days_since_contact - threshold) // 7)
        confidence = 0.7 + (contact.total_interactions or 0) / 100

        return {
            'contact_id': str(contact.id),
            'contact_name': contact.name,
            'opportunity_type': OpportunityType.FOLLOW_UP.value,
            'title': f"Follow up with {contact.name}",
            'description': f"No contact in {days_since_contact} days. {contact.name} is a {contact.relationship_type.value.replace('_', ' ')} with {contact.total_interactions} previous interactions.",
            'confidence_score': min(1.0, confidence),
            'priority': priority,
            'potential_value': self._calculate_value(contact),
            'suggested_action': self._suggest_follow_up_action(contact, days_since_contact),
            'evidence': {
                'days_since_contact': days_since_contact,
                'total_interactions': contact.total_interactions,
                'relationship_type': contact.relationship_type.value
            }
        }

    def _check_relationship_upgrade(self, contact: UnifiedContact) -> Optional[Dict]:
        """Check if relationship can be upgraded"""

        # Map potential -> actual upgrades
        upgrade_map = {
            RelationshipType.POTENTIAL_INVESTOR: (RelationshipType.INVESTOR, OpportunityType.INVESTMENT),
            RelationshipType.POTENTIAL_PARTNER: (RelationshipType.PARTNER, OpportunityType.PARTNERSHIP),
            RelationshipType.POTENTIAL_CLIENT: (RelationshipType.CLIENT, OpportunityType.SALES),
            RelationshipType.ACQUAINTANCE: (RelationshipType.POTENTIAL_PARTNER, OpportunityType.PARTNERSHIP),
        }

        if contact.relationship_type not in upgrade_map:
            return None

        target_type, opp_type = upgrade_map[contact.relationship_type]

        # Check if interaction volume supports upgrade
        min_interactions = {
            RelationshipType.POTENTIAL_INVESTOR: 5,
            RelationshipType.POTENTIAL_PARTNER: 8,
            RelationshipType.POTENTIAL_CLIENT: 3,
            RelationshipType.ACQUAINTANCE: 10,
        }

        required = min_interactions.get(contact.relationship_type, 5)

        if (contact.total_interactions or 0) < required:
            return None

        # Check recency
        if contact.last_interaction:
            days_since = (datetime.utcnow() - contact.last_interaction).days
            if days_since > 60:
                return None

        confidence = min(1.0, 0.5 + (contact.total_interactions or 0) / 20)

        return {
            'contact_id': str(contact.id),
            'contact_name': contact.name,
            'opportunity_type': opp_type.value,
            'title': f"Upgrade relationship with {contact.name}",
            'description': f"Strong engagement ({contact.total_interactions} interactions) suggests {contact.name} may be ready to become a {target_type.value.replace('_', ' ')}.",
            'confidence_score': confidence,
            'priority': 7,
            'potential_value': self._calculate_value(contact, upgraded=True),
            'suggested_action': f"Schedule a call with {contact.name} to discuss deeper collaboration opportunities.",
            'evidence': {
                'current_type': contact.relationship_type.value,
                'target_type': target_type.value,
                'interactions': contact.total_interactions
            }
        }

    def _check_introduction_opportunity(self, contact: UnifiedContact) -> Optional[Dict]:
        """Check if contact can introduce to others"""

        # Only check well-connected relationship types
        connector_types = [
            RelationshipType.PARTNER,
            RelationshipType.INVESTOR,
            RelationshipType.POLITICAL_STAKEHOLDER,
            RelationshipType.MEDIA,
        ]

        if contact.relationship_type not in connector_types:
            return None

        # Need good relationship strength
        if (contact.total_interactions or 0) < 10:
            return None

        # Recent interaction required
        if contact.last_interaction:
            days_since = (datetime.utcnow() - contact.last_interaction).days
            if days_since > 90:
                return None
        else:
            return None

        confidence = 0.6

        return {
            'contact_id': str(contact.id),
            'contact_name': contact.name,
            'opportunity_type': OpportunityType.INTRODUCTION.value,
            'title': f"Request introductions from {contact.name}",
            'description': f"{contact.name} ({contact.company or 'N/A'}) may be able to introduce you to relevant contacts in their network.",
            'confidence_score': confidence,
            'priority': 5,
            'potential_value': "Medium",
            'suggested_action': f"Ask {contact.name} if they can introduce you to relevant investors or partners in their network.",
            'evidence': {
                'relationship_type': contact.relationship_type.value,
                'company': contact.company,
                'interactions': contact.total_interactions
            }
        }

    def _check_investment_opportunity(self, contact: UnifiedContact) -> Optional[Dict]:
        """Check for investment opportunities"""

        if contact.relationship_type != RelationshipType.POTENTIAL_INVESTOR:
            return None

        # Need recent engagement
        if contact.last_interaction:
            days_since = (datetime.utcnow() - contact.last_interaction).days
            if days_since > 30:
                return None
        else:
            return None

        # Look for high engagement
        if (contact.total_interactions or 0) < 3:
            return None

        confidence = min(1.0, 0.4 + (contact.total_interactions or 0) / 15)

        return {
            'contact_id': str(contact.id),
            'contact_name': contact.name,
            'opportunity_type': OpportunityType.INVESTMENT.value,
            'title': f"Investment opportunity with {contact.name}",
            'description': f"{contact.name} has shown strong engagement ({contact.total_interactions} interactions). Consider presenting investment opportunity.",
            'confidence_score': confidence,
            'priority': 9,
            'potential_value': "Very High",
            'suggested_action': f"Prepare pitch deck and schedule meeting with {contact.name} to discuss investment.",
            'evidence': {
                'interactions': contact.total_interactions,
                'company': contact.company,
                'last_contact_days': (datetime.utcnow() - contact.last_interaction).days if contact.last_interaction else None
            }
        }

    def _check_partnership_opportunity(self, contact: UnifiedContact) -> Optional[Dict]:
        """Check for partnership opportunities"""

        if contact.relationship_type not in [
            RelationshipType.POTENTIAL_PARTNER,
            RelationshipType.SUPPLIER
        ]:
            return None

        # Need company info for partnership
        if not contact.company:
            return None

        # Need engagement
        if (contact.total_interactions or 0) < 5:
            return None

        confidence = min(1.0, 0.5 + (contact.total_interactions or 0) / 20)

        return {
            'contact_id': str(contact.id),
            'contact_name': contact.name,
            'opportunity_type': OpportunityType.PARTNERSHIP.value,
            'title': f"Partnership opportunity with {contact.company}",
            'description': f"{contact.name} at {contact.company} could be a strategic partner based on interaction history.",
            'confidence_score': confidence,
            'priority': 7,
            'potential_value': "High",
            'suggested_action': f"Propose partnership discussion with {contact.name} from {contact.company}.",
            'evidence': {
                'company': contact.company,
                'role': contact.job_title,
                'interactions': contact.total_interactions
            }
        }

    def _calculate_value(self, contact: UnifiedContact, upgraded: bool = False) -> str:
        """Calculate potential value of opportunity"""

        base_values = {
            RelationshipType.INVESTOR: "Very High",
            RelationshipType.POTENTIAL_INVESTOR: "Very High" if upgraded else "High",
            RelationshipType.PARTNER: "High",
            RelationshipType.POTENTIAL_PARTNER: "High" if upgraded else "Medium",
            RelationshipType.CLIENT: "High",
            RelationshipType.POTENTIAL_CLIENT: "High" if upgraded else "Medium",
            RelationshipType.POLITICAL_STAKEHOLDER: "High",
            RelationshipType.MEDIA: "Medium",
        }

        return base_values.get(contact.relationship_type, "Low")

    def _suggest_follow_up_action(self, contact: UnifiedContact, days_since: int) -> str:
        """Suggest specific follow-up action"""

        templates = {
            RelationshipType.INVESTOR: f"Send update email to {contact.name} with latest traction metrics and news.",
            RelationshipType.POTENTIAL_INVESTOR: f"Schedule call with {contact.name} to re-engage on investment discussions.",
            RelationshipType.PARTNER: f"Check in with {contact.name} on partnership progress and upcoming opportunities.",
            RelationshipType.POTENTIAL_PARTNER: f"Reach out to {contact.name} with specific partnership proposal.",
            RelationshipType.CLIENT: f"Send satisfaction survey or check-in email to {contact.name}.",
            RelationshipType.POTENTIAL_CLIENT: f"Follow up with {contact.name} on their interest and decision timeline.",
            RelationshipType.POLITICAL_STAKEHOLDER: f"Schedule meeting with {contact.name} to maintain relationship.",
        }

        default = f"Send a brief check-in message to {contact.name} to maintain the relationship."

        return templates.get(contact.relationship_type, default)

    async def save_opportunities(
        self,
        user_id: UUID,
        opportunities: List[Dict]
    ) -> int:
        """Save detected opportunities to database"""
        saved = 0

        for opp in opportunities:
            # Check if similar opportunity already exists
            existing = self.db.query(ContactOpportunity).filter(
                ContactOpportunity.contact_id == opp['contact_id'],
                ContactOpportunity.opportunity_type == opp['opportunity_type'],
                ContactOpportunity.status.in_(['identified', 'reviewing'])
            ).first()

            if existing:
                # Update existing
                existing.confidence_score = opp['confidence_score']
                existing.priority = opp['priority']
                existing.description = opp['description']
                existing.suggested_action = opp['suggested_action']
            else:
                # Create new
                new_opp = ContactOpportunity(
                    contact_id=opp['contact_id'],
                    user_id=user_id,
                    opportunity_type=OpportunityType(opp['opportunity_type']),
                    title=opp['title'],
                    description=opp['description'],
                    confidence_score=opp['confidence_score'],
                    priority=opp['priority'],
                    potential_value=opp['potential_value'],
                    suggested_action=opp['suggested_action'],
                    evidence=opp.get('evidence', {}),
                    identified_at=datetime.utcnow()
                )
                self.db.add(new_opp)
                saved += 1

        self.db.commit()
        return saved

    async def get_opportunities(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get opportunities for user"""

        query = self.db.query(ContactOpportunity).filter(
            ContactOpportunity.user_id == user_id
        )

        if status:
            query = query.filter(ContactOpportunity.status == status)

        opportunities = query.order_by(
            ContactOpportunity.priority.desc(),
            ContactOpportunity.confidence_score.desc()
        ).limit(limit).all()

        return [{
            'id': str(opp.id),
            'contact_id': str(opp.contact_id),
            'opportunity_type': opp.opportunity_type.value,
            'title': opp.title,
            'description': opp.description,
            'confidence_score': opp.confidence_score,
            'priority': opp.priority,
            'potential_value': opp.potential_value,
            'status': opp.status,
            'suggested_action': opp.suggested_action,
            'identified_at': opp.identified_at.isoformat() if opp.identified_at else None,
        } for opp in opportunities]
