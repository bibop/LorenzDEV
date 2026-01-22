"""
LORENZ SaaS - Email Contact Parser
Imports contacts from email extraction JSON
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EmailContact:
    """Contact extracted from email"""
    name: str
    email: str
    company: Optional[str] = None
    role: Optional[str] = None
    interaction_type: str = "email"
    relationship_type: Optional[str] = None
    interaction_count: int = 0
    first_contact: Optional[datetime] = None
    last_contact: Optional[datetime] = None
    source_accounts: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


class EmailContactParser:
    """
    Parser for email contact extraction results

    Expects JSON with format:
    [
        {
            "nome": "Name",
            "email": "email@domain.com",
            "azienda": "Company",
            "ruolo": "Role",
            "tipo_interazione": "MAIL",
            "natura_relazione": "Partner Commerciale",
            "num_interazioni": 10,
            "primo_contatto": "2024-01-01T00:00:00",
            "ultimo_contatto": "2024-12-01T00:00:00",
            "account_origine": ["bibop@domain.com"],
            "argomenti": ["Topic 1", "Topic 2"]
        }
    ]
    """

    def parse_json_file(self, file_path: str) -> List[EmailContact]:
        """
        Parse email contacts from JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            List of EmailContact objects
        """
        contacts = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data:
                contact = self._parse_contact(item)
                if contact:
                    contacts.append(contact)

            logger.info(f"Parsed {len(contacts)} email contacts from {file_path}")
            return contacts

        except Exception as e:
            logger.error(f"Error parsing email contacts from {file_path}: {e}")
            raise

    def _parse_contact(self, item: Dict) -> Optional[EmailContact]:
        """Parse single contact from JSON item"""
        try:
            # Get required fields
            name = item.get('nome', item.get('name', '')).strip()
            email = item.get('email', '').strip().lower()

            if not email:
                return None

            # Parse optional fields
            company = item.get('azienda', item.get('company'))
            role = item.get('ruolo', item.get('role'))
            interaction_type = item.get('tipo_interazione', item.get('interaction_type', 'email'))
            relationship_type = item.get('natura_relazione', item.get('relationship_type'))
            interaction_count = item.get('num_interazioni', item.get('interaction_count', 0))

            # Parse dates
            first_contact = self._parse_date(
                item.get('primo_contatto', item.get('first_contact'))
            )
            last_contact = self._parse_date(
                item.get('ultimo_contatto', item.get('last_contact'))
            )

            # Get source accounts
            source_accounts = item.get('account_origine', item.get('source_accounts', []))
            if isinstance(source_accounts, str):
                source_accounts = [source_accounts]

            # Get topics
            topics = item.get('argomenti', item.get('topics', []))
            if isinstance(topics, str):
                topics = [topics]

            return EmailContact(
                name=name or self._name_from_email(email),
                email=email,
                company=company,
                role=role,
                interaction_type=interaction_type,
                relationship_type=relationship_type,
                interaction_count=interaction_count,
                first_contact=first_contact,
                last_contact=last_contact,
                source_accounts=source_accounts,
                topics=topics
            )

        except Exception as e:
            logger.warning(f"Error parsing contact item: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None

        # Try various formats
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _name_from_email(self, email: str) -> str:
        """Extract name from email address"""
        local = email.split('@')[0]
        # Replace separators with spaces
        name = local.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        # Remove numbers
        name = ''.join(c for c in name if not c.isdigit())
        # Title case
        return name.title().strip()

    def to_dict(self, contact: EmailContact) -> Dict:
        """Convert EmailContact to dictionary"""
        return {
            'name': contact.name,
            'email': contact.email,
            'company': contact.company,
            'role': contact.role,
            'interaction_type': contact.interaction_type,
            'relationship_type': contact.relationship_type,
            'interaction_count': contact.interaction_count,
            'first_contact': contact.first_contact.isoformat() if contact.first_contact else None,
            'last_contact': contact.last_contact.isoformat() if contact.last_contact else None,
            'source_accounts': contact.source_accounts,
            'topics': contact.topics
        }


def parse_email_contacts(file_path: str) -> List[Dict]:
    """
    Convenience function to parse email contacts

    Args:
        file_path: Path to JSON file

    Returns:
        List of contact dictionaries
    """
    parser = EmailContactParser()
    contacts = parser.parse_json_file(file_path)
    return [parser.to_dict(c) for c in contacts]
