"""
LORENZ SaaS - Social Graph Service
Main service for managing the unified social graph
"""

import logging
import math
import unicodedata
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.social_graph import (
    UnifiedContact, ContactSourceLink, ContactInteraction,
    ContactOpportunity, SocialGraphEdge,
    DataSource, InteractionType, RelationshipType, OpportunityType
)
from .whatsapp_parser import WhatsAppParser, WhatsAppContact
from .linkedin_parser import LinkedInParser, LinkedInContact
from .email_parser import EmailContactParser, EmailContact

logger = logging.getLogger(__name__)


# Color mapping for relationship types
RELATIONSHIP_COLORS = {
    RelationshipType.INVESTOR: "#FFD700",           # Gold
    RelationshipType.POTENTIAL_INVESTOR: "#FFA500", # Orange
    RelationshipType.PARTNER: "#4CAF50",            # Green
    RelationshipType.POTENTIAL_PARTNER: "#8BC34A",  # Light Green
    RelationshipType.CLIENT: "#2196F3",             # Blue
    RelationshipType.POTENTIAL_CLIENT: "#03A9F4",   # Light Blue
    RelationshipType.SUPPLIER: "#9C27B0",           # Purple
    RelationshipType.POLITICAL_STAKEHOLDER: "#F44336",  # Red
    RelationshipType.MEDIA: "#E91E63",              # Pink
    RelationshipType.ACADEMIA: "#00BCD4",           # Cyan
    RelationshipType.TEAM_INTERNAL: "#607D8B",      # Blue Grey
    RelationshipType.FAMILY: "#FF5722",             # Deep Orange
    RelationshipType.FRIEND: "#795548",             # Brown
    RelationshipType.ACQUAINTANCE: "#9E9E9E",       # Grey
    RelationshipType.OTHER: "#BDBDBD",              # Light Grey
}


class SocialGraphService:
    """
    Main service for Social Graph operations

    Features:
    - Import contacts from multiple sources
    - Merge and deduplicate contacts
    - Build relationship graph
    - Calculate graph positioning for 3D visualization
    - Identify opportunities
    """

    def __init__(self, db: Session):
        self.db = db
        self.whatsapp_parser = WhatsAppParser()
        self.linkedin_parser = LinkedInParser()
        self.email_parser = EmailContactParser()

    def normalize_name(self, name: str) -> str:
        """Normalize name for matching"""
        if not name:
            return ""
        # Remove accents
        nfkd = unicodedata.normalize('NFKD', name)
        name = ''.join(c for c in nfkd if not unicodedata.combining(c))
        # Lowercase and remove extra spaces
        name = ' '.join(name.lower().split())
        # Remove common prefixes/suffixes
        for prefix in ['dr.', 'prof.', 'ing.', 'mr.', 'mrs.', 'ms.']:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        return name

    def normalize_email(self, email: str) -> str:
        """Normalize email for matching"""
        if not email:
            return ""
        return email.lower().strip()

    # ==================== IMPORT METHODS ====================

    async def import_email_contacts(
        self,
        user_id: UUID,
        json_file_path: str
    ) -> Dict:
        """Import contacts from email extraction JSON"""
        contacts = self.email_parser.parse_json_file(json_file_path)

        stats = {'imported': 0, 'merged': 0, 'errors': 0}

        for email_contact in contacts:
            try:
                unified = await self._upsert_contact_from_email(user_id, email_contact)
                if unified:
                    stats['imported'] += 1
            except Exception as e:
                logger.error(f"Error importing email contact {email_contact.email}: {e}")
                stats['errors'] += 1

        self.db.commit()
        return stats

    async def import_whatsapp_chat(
        self,
        user_id: UUID,
        file_path: str
    ) -> Dict:
        """Import contacts from WhatsApp chat export"""
        contacts = self.whatsapp_parser.parse_file(file_path)

        stats = {'imported': 0, 'merged': 0, 'errors': 0}

        for name, wa_contact in contacts.items():
            try:
                unified = await self._upsert_contact_from_whatsapp(user_id, wa_contact)
                if unified:
                    stats['imported'] += 1
            except Exception as e:
                logger.error(f"Error importing WhatsApp contact {name}: {e}")
                stats['errors'] += 1

        self.db.commit()
        return stats

    async def import_linkedin_data(
        self,
        user_id: UUID,
        export_path: str
    ) -> Dict:
        """Import contacts from LinkedIn data export"""
        contacts = self.linkedin_parser.parse_export(export_path)

        stats = {'imported': 0, 'merged': 0, 'errors': 0}

        for name, li_contact in contacts.items():
            try:
                unified = await self._upsert_contact_from_linkedin(user_id, li_contact)
                if unified:
                    stats['imported'] += 1
            except Exception as e:
                logger.error(f"Error importing LinkedIn contact {name}: {e}")
                stats['errors'] += 1

        self.db.commit()
        return stats

    # ==================== UPSERT METHODS ====================

    async def _upsert_contact_from_email(
        self,
        user_id: UUID,
        email_contact: EmailContact
    ) -> Optional[UnifiedContact]:
        """Create or update contact from email source"""

        # Try to find existing contact
        existing = self._find_existing_contact(
            user_id,
            email=email_contact.email,
            name=email_contact.name
        )

        if existing:
            # Update existing
            self._merge_email_data(existing, email_contact)
            return existing
        else:
            # Create new
            unified = UnifiedContact(
                user_id=user_id,
                name=email_contact.name,
                normalized_name=self.normalize_name(email_contact.name),
                primary_email=email_contact.email,
                all_emails=[email_contact.email],
                company=email_contact.company,
                job_title=email_contact.role,
                relationship_type=self._map_relationship_type(email_contact.relationship_type),
                total_interactions=email_contact.interaction_count,
                email_interactions=email_contact.interaction_count,
                first_interaction=email_contact.first_contact,
                last_interaction=email_contact.last_contact,
                node_color=RELATIONSHIP_COLORS.get(
                    self._map_relationship_type(email_contact.relationship_type),
                    "#9E9E9E"
                )
            )
            self.db.add(unified)
            self.db.flush()

            # Add source link
            source_link = ContactSourceLink(
                contact_id=unified.id,
                source=DataSource.EMAIL,
                source_email=email_contact.email,
                source_name=email_contact.name,
                source_data={
                    'topics': email_contact.topics,
                    'source_accounts': email_contact.source_accounts
                }
            )
            self.db.add(source_link)

            return unified

    async def _upsert_contact_from_whatsapp(
        self,
        user_id: UUID,
        wa_contact: WhatsAppContact
    ) -> Optional[UnifiedContact]:
        """Create or update contact from WhatsApp source"""

        phone = self.whatsapp_parser.extract_phone_from_name(wa_contact.name)

        # Try to find existing contact
        existing = self._find_existing_contact(
            user_id,
            name=wa_contact.name,
            phone=phone
        )

        if existing:
            # Update existing
            self._merge_whatsapp_data(existing, wa_contact)
            return existing
        else:
            # Create new
            unified = UnifiedContact(
                user_id=user_id,
                name=wa_contact.name,
                normalized_name=self.normalize_name(wa_contact.name),
                primary_phone=phone,
                all_phones=[phone] if phone else [],
                total_interactions=wa_contact.message_count,
                whatsapp_interactions=wa_contact.message_count,
                first_interaction=wa_contact.first_message,
                last_interaction=wa_contact.last_message,
                node_color=RELATIONSHIP_COLORS.get(RelationshipType.ACQUAINTANCE, "#9E9E9E")
            )
            self.db.add(unified)
            self.db.flush()

            # Add source link
            source_link = ContactSourceLink(
                contact_id=unified.id,
                source=DataSource.WHATSAPP,
                source_phone=phone,
                source_name=wa_contact.name
            )
            self.db.add(source_link)

            return unified

    async def _upsert_contact_from_linkedin(
        self,
        user_id: UUID,
        li_contact: LinkedInContact
    ) -> Optional[UnifiedContact]:
        """Create or update contact from LinkedIn source"""

        # Try to find existing contact
        existing = self._find_existing_contact(
            user_id,
            email=li_contact.email,
            name=li_contact.full_name
        )

        if existing:
            # Update existing
            self._merge_linkedin_data(existing, li_contact)
            return existing
        else:
            # Create new
            unified = UnifiedContact(
                user_id=user_id,
                name=li_contact.full_name,
                normalized_name=self.normalize_name(li_contact.full_name),
                primary_email=li_contact.email,
                all_emails=[li_contact.email] if li_contact.email else [],
                company=li_contact.company,
                job_title=li_contact.position,
                linkedin_url=li_contact.profile_url,
                total_interactions=li_contact.message_count,
                linkedin_interactions=li_contact.message_count,
                first_interaction=li_contact.connected_on or li_contact.first_message,
                last_interaction=li_contact.last_message,
                node_color=RELATIONSHIP_COLORS.get(RelationshipType.ACQUAINTANCE, "#9E9E9E")
            )
            self.db.add(unified)
            self.db.flush()

            # Add source link
            source_link = ContactSourceLink(
                contact_id=unified.id,
                source=DataSource.LINKEDIN,
                source_email=li_contact.email,
                source_name=li_contact.full_name,
                source_data={
                    'company': li_contact.company,
                    'position': li_contact.position,
                    'profile_url': li_contact.profile_url
                }
            )
            self.db.add(source_link)

            return unified

    # ==================== FIND & MERGE ====================

    def _find_existing_contact(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[UnifiedContact]:
        """Find existing contact by email, name, or phone"""

        query = self.db.query(UnifiedContact).filter(
            UnifiedContact.user_id == user_id
        )

        # Try email first (most reliable)
        if email:
            normalized_email = self.normalize_email(email)
            contact = query.filter(
                or_(
                    UnifiedContact.primary_email == normalized_email,
                    UnifiedContact.all_emails.contains([normalized_email])
                )
            ).first()
            if contact:
                return contact

        # Try phone
        if phone:
            contact = query.filter(
                or_(
                    UnifiedContact.primary_phone == phone,
                    UnifiedContact.all_phones.contains([phone])
                )
            ).first()
            if contact:
                return contact

        # Try normalized name (fuzzy)
        if name:
            normalized = self.normalize_name(name)
            contact = query.filter(
                UnifiedContact.normalized_name == normalized
            ).first()
            if contact:
                return contact

        return None

    def _merge_email_data(self, contact: UnifiedContact, email_contact: EmailContact):
        """Merge email source data into existing contact"""
        # Add email if not present
        if email_contact.email and email_contact.email not in (contact.all_emails or []):
            contact.all_emails = (contact.all_emails or []) + [email_contact.email]

        # Update company/role if not set
        if not contact.company and email_contact.company:
            contact.company = email_contact.company
        if not contact.job_title and email_contact.role:
            contact.job_title = email_contact.role

        # Update interaction counts
        contact.email_interactions = (contact.email_interactions or 0) + email_contact.interaction_count
        contact.total_interactions = (contact.total_interactions or 0) + email_contact.interaction_count

        # Update dates
        if email_contact.first_contact:
            if not contact.first_interaction or email_contact.first_contact < contact.first_interaction:
                contact.first_interaction = email_contact.first_contact
        if email_contact.last_contact:
            if not contact.last_interaction or email_contact.last_contact > contact.last_interaction:
                contact.last_interaction = email_contact.last_contact

        # Update relationship type
        new_type = self._map_relationship_type(email_contact.relationship_type)
        if new_type != RelationshipType.OTHER:
            contact.relationship_type = new_type
            contact.node_color = RELATIONSHIP_COLORS.get(new_type, contact.node_color)

    def _merge_whatsapp_data(self, contact: UnifiedContact, wa_contact: WhatsAppContact):
        """Merge WhatsApp source data into existing contact"""
        phone = self.whatsapp_parser.extract_phone_from_name(wa_contact.name)

        if phone and phone not in (contact.all_phones or []):
            contact.all_phones = (contact.all_phones or []) + [phone]
            if not contact.primary_phone:
                contact.primary_phone = phone

        contact.whatsapp_interactions = (contact.whatsapp_interactions or 0) + wa_contact.message_count
        contact.total_interactions = (contact.total_interactions or 0) + wa_contact.message_count

        if wa_contact.first_message:
            if not contact.first_interaction or wa_contact.first_message < contact.first_interaction:
                contact.first_interaction = wa_contact.first_message
        if wa_contact.last_message:
            if not contact.last_interaction or wa_contact.last_message > contact.last_interaction:
                contact.last_interaction = wa_contact.last_message

    def _merge_linkedin_data(self, contact: UnifiedContact, li_contact: LinkedInContact):
        """Merge LinkedIn source data into existing contact"""
        if li_contact.email and li_contact.email not in (contact.all_emails or []):
            contact.all_emails = (contact.all_emails or []) + [li_contact.email]

        if not contact.linkedin_url and li_contact.profile_url:
            contact.linkedin_url = li_contact.profile_url

        if not contact.company and li_contact.company:
            contact.company = li_contact.company
        if not contact.job_title and li_contact.position:
            contact.job_title = li_contact.position

        contact.linkedin_interactions = (contact.linkedin_interactions or 0) + li_contact.message_count
        contact.total_interactions = (contact.total_interactions or 0) + li_contact.message_count

    def _map_relationship_type(self, rel_str: Optional[str]) -> RelationshipType:
        """Map string relationship type to enum"""
        if not rel_str:
            return RelationshipType.OTHER

        rel_lower = rel_str.lower()

        mapping = {
            'investor': RelationshipType.INVESTOR,
            'investitore': RelationshipType.INVESTOR,
            'possibile investitore': RelationshipType.POTENTIAL_INVESTOR,
            'potential investor': RelationshipType.POTENTIAL_INVESTOR,
            'partner': RelationshipType.PARTNER,
            'partner commerciale': RelationshipType.PARTNER,
            'possibile partner': RelationshipType.POTENTIAL_PARTNER,
            'cliente': RelationshipType.CLIENT,
            'client': RelationshipType.CLIENT,
            'possibile cliente': RelationshipType.POTENTIAL_CLIENT,
            'fornitore': RelationshipType.SUPPLIER,
            'supplier': RelationshipType.SUPPLIER,
            'stakeholder politico': RelationshipType.POLITICAL_STAKEHOLDER,
            'political': RelationshipType.POLITICAL_STAKEHOLDER,
            'media': RelationshipType.MEDIA,
            'giornalista': RelationshipType.MEDIA,
            'accademia': RelationshipType.ACADEMIA,
            'academia': RelationshipType.ACADEMIA,
            'team': RelationshipType.TEAM_INTERNAL,
            'interno': RelationshipType.TEAM_INTERNAL,
            'internal': RelationshipType.TEAM_INTERNAL,
            'famiglia': RelationshipType.FAMILY,
            'family': RelationshipType.FAMILY,
            'amico': RelationshipType.FRIEND,
            'friend': RelationshipType.FRIEND,
        }

        for key, value in mapping.items():
            if key in rel_lower:
                return value

        return RelationshipType.OTHER

    # ==================== GRAPH OPERATIONS ====================

    async def calculate_graph_positions(self, user_id: UUID) -> None:
        """
        Calculate 3D positions for all contacts using force-directed layout

        Uses a simplified force-directed algorithm:
        - User at center (0, 0, 0)
        - Contacts placed based on relationship type and interaction strength
        """
        contacts = self.db.query(UnifiedContact).filter(
            UnifiedContact.user_id == user_id
        ).all()

        if not contacts:
            return

        # Group contacts by relationship type
        groups: Dict[RelationshipType, List[UnifiedContact]] = {}
        for contact in contacts:
            rel_type = contact.relationship_type or RelationshipType.OTHER
            if rel_type not in groups:
                groups[rel_type] = []
            groups[rel_type].append(contact)

        # Assign positions by group
        group_angle = 0
        angle_step = 2 * math.pi / len(groups) if groups else 0

        for rel_type, group_contacts in groups.items():
            # Base radius for this group (further = less important relationship)
            importance_order = [
                RelationshipType.TEAM_INTERNAL,
                RelationshipType.FAMILY,
                RelationshipType.INVESTOR,
                RelationshipType.PARTNER,
                RelationshipType.CLIENT,
                RelationshipType.POTENTIAL_INVESTOR,
                RelationshipType.POTENTIAL_PARTNER,
                RelationshipType.POTENTIAL_CLIENT,
                RelationshipType.SUPPLIER,
                RelationshipType.POLITICAL_STAKEHOLDER,
                RelationshipType.MEDIA,
                RelationshipType.ACADEMIA,
                RelationshipType.FRIEND,
                RelationshipType.ACQUAINTANCE,
                RelationshipType.OTHER,
            ]

            try:
                base_radius = 5 + importance_order.index(rel_type) * 2
            except ValueError:
                base_radius = 20

            # Place contacts in this group
            contact_angle_step = 2 * math.pi / len(group_contacts) if group_contacts else 0

            for i, contact in enumerate(group_contacts):
                # Calculate position
                angle = group_angle + (i * contact_angle_step * 0.3)  # Spread within group
                radius = base_radius + (i % 3) * 1.5  # Vary radius slightly

                # Add vertical spread based on interactions
                z_offset = math.log10(contact.total_interactions + 1) * 2

                contact.graph_x = radius * math.cos(angle)
                contact.graph_y = radius * math.sin(angle)
                contact.graph_z = z_offset - 5

                # Calculate node size based on interactions
                contact.node_size = 0.5 + math.log10(contact.total_interactions + 1) * 0.3

                # Ensure color is set
                contact.node_color = RELATIONSHIP_COLORS.get(rel_type, "#9E9E9E")

            group_angle += angle_step

        self.db.commit()

    async def get_graph_data(self, user_id: UUID) -> Dict:
        """
        Get all data needed for 3D graph visualization

        Returns:
            {
                'nodes': [...],
                'edges': [...],
                'stats': {...}
            }
        """
        contacts = self.db.query(UnifiedContact).filter(
            UnifiedContact.user_id == user_id
        ).all()

        edges = self.db.query(SocialGraphEdge).filter(
            SocialGraphEdge.user_id == user_id
        ).all()

        # Build nodes list
        nodes = []
        for contact in contacts:
            nodes.append({
                'id': str(contact.id),
                'name': contact.name,
                'email': contact.primary_email,
                'company': contact.company,
                'role': contact.job_title,
                'relationship_type': contact.relationship_type.value if contact.relationship_type else 'other',
                'total_interactions': contact.total_interactions,
                'x': contact.graph_x or 0,
                'y': contact.graph_y or 0,
                'z': contact.graph_z or 0,
                'size': contact.node_size or 1,
                'color': contact.node_color or '#9E9E9E',
                'avatar': contact.avatar_url,
                'linkedin': contact.linkedin_url,
                'twitter': contact.twitter_handle,
            })

        # Build edges list
        edge_list = []
        for edge in edges:
            edge_list.append({
                'source': str(edge.source_contact_id),
                'target': str(edge.target_contact_id),
                'type': edge.connection_type,
                'weight': edge.weight
            })

        # Calculate stats
        rel_counts = {}
        for contact in contacts:
            rel_type = contact.relationship_type.value if contact.relationship_type else 'other'
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        stats = {
            'total_contacts': len(contacts),
            'total_edges': len(edges),
            'by_relationship': rel_counts,
            'total_interactions': sum(c.total_interactions or 0 for c in contacts),
        }

        return {
            'nodes': nodes,
            'edges': edge_list,
            'stats': stats
        }

    async def search_contacts(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """Search contacts by name, email, or company"""
        search_term = f"%{query.lower()}%"

        contacts = self.db.query(UnifiedContact).filter(
            UnifiedContact.user_id == user_id,
            or_(
                func.lower(UnifiedContact.name).like(search_term),
                func.lower(UnifiedContact.primary_email).like(search_term),
                func.lower(UnifiedContact.company).like(search_term),
            )
        ).limit(limit).all()

        return [{
            'id': str(c.id),
            'name': c.name,
            'email': c.primary_email,
            'company': c.company,
            'role': c.job_title,
            'relationship_type': c.relationship_type.value if c.relationship_type else 'other',
            'total_interactions': c.total_interactions,
        } for c in contacts]

    # ==================== APIFY IMPORT METHODS ====================

    async def import_from_apify_results(
        self,
        user_id: UUID,
        contacts: List[Dict],
        source: str
    ) -> Dict:
        """
        Import contacts from Apify scraping results

        Args:
            user_id: User ID
            contacts: List of parsed contact dicts from Apify service
            source: Source type ('whatsapp', 'linkedin', 'twitter')

        Returns:
            Import statistics
        """
        stats = {'imported': 0, 'merged': 0, 'errors': 0}

        for contact_data in contacts:
            try:
                if source == 'whatsapp':
                    unified = await self._upsert_contact_from_apify_whatsapp(user_id, contact_data)
                elif source in ('linkedin', 'linkedin_search'):
                    unified = await self._upsert_contact_from_apify_linkedin(user_id, contact_data)
                elif source == 'twitter':
                    unified = await self._upsert_contact_from_apify_twitter(user_id, contact_data)
                else:
                    logger.warning(f"Unknown source type: {source}")
                    continue

                if unified:
                    stats['imported'] += 1
            except Exception as e:
                logger.error(f"Error importing Apify {source} contact: {e}")
                stats['errors'] += 1

        self.db.commit()

        # Recalculate positions after import
        await self.calculate_graph_positions(user_id)

        return stats

    async def _upsert_contact_from_apify_whatsapp(
        self,
        user_id: UUID,
        data: Dict
    ) -> Optional[UnifiedContact]:
        """Import contact from Apify WhatsApp scraper results"""

        phone = data.get('phone_number')
        name = data.get('display_name') or phone

        if not name:
            return None

        # Skip groups for now
        if data.get('is_group'):
            return None

        existing = self._find_existing_contact(user_id, name=name, phone=phone)

        message_count = len(data.get('messages', []))

        if existing:
            # Merge data
            if phone and phone not in (existing.all_phones or []):
                existing.all_phones = (existing.all_phones or []) + [phone]
                if not existing.primary_phone:
                    existing.primary_phone = phone

            if data.get('profile_pic_url') and not existing.avatar_url:
                existing.avatar_url = data.get('profile_pic_url')

            existing.whatsapp_interactions = (existing.whatsapp_interactions or 0) + message_count
            existing.total_interactions = (existing.total_interactions or 0) + message_count

            return existing

        # Create new contact
        unified = UnifiedContact(
            user_id=user_id,
            name=name,
            normalized_name=self.normalize_name(name),
            primary_phone=phone,
            all_phones=[phone] if phone else [],
            avatar_url=data.get('profile_pic_url'),
            total_interactions=message_count,
            whatsapp_interactions=message_count,
            node_color=RELATIONSHIP_COLORS.get(RelationshipType.ACQUAINTANCE, "#9E9E9E"),
            source_data={'apify_whatsapp': data}
        )
        self.db.add(unified)
        self.db.flush()

        # Add source link
        source_link = ContactSourceLink(
            contact_id=unified.id,
            source=DataSource.WHATSAPP,
            source_phone=phone,
            source_name=name,
            source_data={'from_apify': True}
        )
        self.db.add(source_link)

        return unified

    async def _upsert_contact_from_apify_linkedin(
        self,
        user_id: UUID,
        data: Dict
    ) -> Optional[UnifiedContact]:
        """Import contact from Apify LinkedIn scraper results"""

        name = data.get('display_name')
        if not name:
            name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()

        if not name:
            return None

        linkedin_url = data.get('linkedin_url')

        # Try to find existing by LinkedIn URL or name
        existing = None
        if linkedin_url:
            existing = self.db.query(UnifiedContact).filter(
                UnifiedContact.user_id == user_id,
                UnifiedContact.linkedin_url == linkedin_url
            ).first()

        if not existing:
            existing = self._find_existing_contact(user_id, name=name)

        if existing:
            # Merge data
            if linkedin_url and not existing.linkedin_url:
                existing.linkedin_url = linkedin_url

            if data.get('profile_pic_url') and not existing.avatar_url:
                existing.avatar_url = data.get('profile_pic_url')

            if data.get('company') and not existing.company:
                existing.company = data.get('company')

            if data.get('job_title') and not existing.job_title:
                existing.job_title = data.get('job_title')

            if data.get('headline') and not existing.notes:
                existing.notes = data.get('headline')

            if data.get('location'):
                existing.city = data.get('location')

            # Store additional data
            existing.source_data = existing.source_data or {}
            existing.source_data['apify_linkedin'] = {
                'about': data.get('about'),
                'skills': data.get('skills', []),
                'experience': data.get('experience', []),
                'education': data.get('education', []),
                'connections': data.get('connections')
            }

            return existing

        # Create new contact
        unified = UnifiedContact(
            user_id=user_id,
            name=name,
            normalized_name=self.normalize_name(name),
            company=data.get('company'),
            job_title=data.get('job_title') or data.get('headline'),
            linkedin_url=linkedin_url,
            avatar_url=data.get('profile_pic_url'),
            city=data.get('location'),
            notes=data.get('about'),
            total_interactions=0,
            linkedin_interactions=0,
            node_color=RELATIONSHIP_COLORS.get(RelationshipType.ACQUAINTANCE, "#9E9E9E"),
            source_data={
                'apify_linkedin': {
                    'about': data.get('about'),
                    'skills': data.get('skills', []),
                    'experience': data.get('experience', []),
                    'education': data.get('education', []),
                    'connections': data.get('connections')
                }
            }
        )
        self.db.add(unified)
        self.db.flush()

        # Add source link
        source_link = ContactSourceLink(
            contact_id=unified.id,
            source=DataSource.LINKEDIN,
            source_name=name,
            source_data={
                'from_apify': True,
                'linkedin_url': linkedin_url
            }
        )
        self.db.add(source_link)

        return unified

    async def _upsert_contact_from_apify_twitter(
        self,
        user_id: UUID,
        data: Dict
    ) -> Optional[UnifiedContact]:
        """Import contact from Apify Twitter scraper results"""

        name = data.get('display_name')
        twitter_handle = data.get('twitter_handle')

        if not name and not twitter_handle:
            return None

        name = name or f"@{twitter_handle}"

        # Try to find existing by Twitter handle
        existing = None
        if twitter_handle:
            existing = self.db.query(UnifiedContact).filter(
                UnifiedContact.user_id == user_id,
                UnifiedContact.twitter_handle == twitter_handle
            ).first()

        if not existing:
            existing = self._find_existing_contact(user_id, name=name)

        if existing:
            # Merge data
            if twitter_handle and not existing.twitter_handle:
                existing.twitter_handle = twitter_handle

            if data.get('profile_pic_url') and not existing.avatar_url:
                existing.avatar_url = data.get('profile_pic_url')

            if data.get('location') and not existing.city:
                existing.city = data.get('location')

            if data.get('bio') and not existing.notes:
                existing.notes = data.get('bio')

            # Store additional data
            existing.source_data = existing.source_data or {}
            existing.source_data['apify_twitter'] = {
                'bio': data.get('bio'),
                'followers_count': data.get('followers_count'),
                'following_count': data.get('following_count'),
                'tweets_count': data.get('tweets_count'),
                'verified': data.get('verified'),
                'website': data.get('website'),
                'recent_tweets': data.get('recent_tweets', [])
            }

            return existing

        # Create new contact
        unified = UnifiedContact(
            user_id=user_id,
            name=name,
            normalized_name=self.normalize_name(name),
            twitter_handle=twitter_handle,
            avatar_url=data.get('profile_pic_url'),
            city=data.get('location'),
            notes=data.get('bio'),
            total_interactions=0,
            node_color=RELATIONSHIP_COLORS.get(RelationshipType.ACQUAINTANCE, "#9E9E9E"),
            source_data={
                'apify_twitter': {
                    'bio': data.get('bio'),
                    'followers_count': data.get('followers_count'),
                    'following_count': data.get('following_count'),
                    'tweets_count': data.get('tweets_count'),
                    'verified': data.get('verified'),
                    'website': data.get('website'),
                    'recent_tweets': data.get('recent_tweets', [])
                }
            }
        )
        self.db.add(unified)
        self.db.flush()

        # Add source link
        source_link = ContactSourceLink(
            contact_id=unified.id,
            source=DataSource.TWITTER,
            source_name=name,
            source_data={
                'from_apify': True,
                'twitter_handle': twitter_handle
            }
        )
        self.db.add(source_link)

        return unified
