"""
LORENZ SaaS - LinkedIn Data Export Parser
Parses LinkedIn data export files (GDPR data download)

To export: Settings > Data Privacy > Get a copy of your data
"""

import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path
import zipfile
import io

logger = logging.getLogger(__name__)


@dataclass
class LinkedInConnection:
    """LinkedIn connection"""
    first_name: str
    last_name: str
    email: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    connected_on: Optional[datetime] = None
    profile_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class LinkedInMessage:
    """LinkedIn message"""
    conversation_id: str
    sender: str
    content: str
    timestamp: datetime
    is_inmail: bool = False


@dataclass
class LinkedInContact:
    """Aggregated LinkedIn contact"""
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    connected_on: Optional[datetime] = None
    profile_url: Optional[str] = None
    messages: List[LinkedInMessage] = field(default_factory=list)
    message_count: int = 0
    first_message: Optional[datetime] = None
    last_message: Optional[datetime] = None


class LinkedInParser:
    """
    Parser for LinkedIn data export

    LinkedIn exports data as a ZIP file containing CSVs:
    - Connections.csv: Your connections
    - Messages.csv: Your messages
    - Invitations.csv: Sent/received invitations
    - Profile.csv: Your profile info
    - etc.
    """

    def __init__(self):
        self.connections: Dict[str, LinkedInConnection] = {}
        self.messages: List[LinkedInMessage] = []
        self.contacts: Dict[str, LinkedInContact] = {}

    def parse_export(self, export_path: str) -> Dict[str, LinkedInContact]:
        """
        Parse LinkedIn data export (ZIP file or directory)

        Args:
            export_path: Path to ZIP file or extracted directory

        Returns:
            Dictionary of contacts keyed by full name
        """
        path = Path(export_path)

        if path.suffix.lower() == '.zip':
            return self._parse_zip(export_path)
        elif path.is_dir():
            return self._parse_directory(export_path)
        else:
            raise ValueError(f"Invalid LinkedIn export path: {export_path}")

    def _parse_zip(self, zip_path: str) -> Dict[str, LinkedInContact]:
        """Parse LinkedIn export from ZIP file"""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Find and parse Connections.csv
            for name in zf.namelist():
                if 'Connections' in name and name.endswith('.csv'):
                    with zf.open(name) as f:
                        content = io.TextIOWrapper(f, encoding='utf-8')
                        self._parse_connections_csv(content)

            # Find and parse Messages.csv
            for name in zf.namelist():
                if 'messages' in name.lower() and name.endswith('.csv'):
                    with zf.open(name) as f:
                        content = io.TextIOWrapper(f, encoding='utf-8')
                        self._parse_messages_csv(content)

        return self._build_contacts()

    def _parse_directory(self, dir_path: str) -> Dict[str, LinkedInContact]:
        """Parse LinkedIn export from extracted directory"""
        path = Path(dir_path)

        # Find and parse Connections.csv
        for csv_file in path.rglob('*onnections*.csv'):
            with open(csv_file, 'r', encoding='utf-8') as f:
                self._parse_connections_csv(f)
            break

        # Find and parse Messages.csv
        for csv_file in path.rglob('*essages*.csv'):
            with open(csv_file, 'r', encoding='utf-8') as f:
                self._parse_messages_csv(f)
            break

        return self._build_contacts()

    def _parse_connections_csv(self, file_handle) -> None:
        """Parse Connections.csv"""
        reader = csv.DictReader(file_handle)

        for row in reader:
            try:
                # Handle different column name formats
                first_name = row.get('First Name', row.get('first_name', '')).strip()
                last_name = row.get('Last Name', row.get('last_name', '')).strip()
                email = row.get('Email Address', row.get('email', '')).strip() or None
                company = row.get('Company', row.get('company', '')).strip() or None
                position = row.get('Position', row.get('position', '')).strip() or None
                connected_on_str = row.get('Connected On', row.get('connected_on', ''))
                url = row.get('URL', row.get('url', '')).strip() or None

                if not first_name and not last_name:
                    continue

                # Parse connection date
                connected_on = None
                if connected_on_str:
                    for fmt in ['%d %b %Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            connected_on = datetime.strptime(connected_on_str.strip(), fmt)
                            break
                        except ValueError:
                            continue

                full_name = f"{first_name} {last_name}".strip()
                connection = LinkedInConnection(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    company=company,
                    position=position,
                    connected_on=connected_on,
                    profile_url=url
                )

                self.connections[full_name] = connection

            except Exception as e:
                logger.warning(f"Error parsing connection row: {e}")
                continue

        logger.info(f"Parsed {len(self.connections)} LinkedIn connections")

    def _parse_messages_csv(self, file_handle) -> None:
        """Parse Messages.csv"""
        reader = csv.DictReader(file_handle)

        for row in reader:
            try:
                # Handle different column name formats
                conv_id = row.get('CONVERSATION ID', row.get('conversation_id', ''))
                sender = row.get('FROM', row.get('sender', row.get('from', ''))).strip()
                content = row.get('CONTENT', row.get('content', row.get('message', ''))).strip()
                date_str = row.get('DATE', row.get('date', row.get('sent_at', '')))

                if not sender or not content:
                    continue

                # Parse timestamp
                timestamp = None
                if date_str:
                    for fmt in ['%Y-%m-%d %H:%M:%S UTC', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M']:
                        try:
                            timestamp = datetime.strptime(date_str.strip(), fmt)
                            break
                        except ValueError:
                            continue

                if not timestamp:
                    timestamp = datetime.now()

                message = LinkedInMessage(
                    conversation_id=conv_id,
                    sender=sender,
                    content=content,
                    timestamp=timestamp
                )

                self.messages.append(message)

            except Exception as e:
                logger.warning(f"Error parsing message row: {e}")
                continue

        logger.info(f"Parsed {len(self.messages)} LinkedIn messages")

    def _build_contacts(self) -> Dict[str, LinkedInContact]:
        """Build unified contact list from connections and messages"""

        # Start with connections
        for name, conn in self.connections.items():
            self.contacts[name] = LinkedInContact(
                first_name=conn.first_name,
                last_name=conn.last_name,
                full_name=name,
                email=conn.email,
                company=conn.company,
                position=conn.position,
                connected_on=conn.connected_on,
                profile_url=conn.profile_url
            )

        # Add messages
        for msg in self.messages:
            sender = msg.sender

            # Try to match sender to existing contact
            if sender not in self.contacts:
                # Create new contact from message
                name_parts = sender.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''

                self.contacts[sender] = LinkedInContact(
                    first_name=first_name,
                    last_name=last_name,
                    full_name=sender
                )

            contact = self.contacts[sender]
            contact.messages.append(msg)
            contact.message_count += 1

            if not contact.first_message or msg.timestamp < contact.first_message:
                contact.first_message = msg.timestamp
            if not contact.last_message or msg.timestamp > contact.last_message:
                contact.last_message = msg.timestamp

        logger.info(f"Built {len(self.contacts)} total LinkedIn contacts")
        return self.contacts

    def get_contact_summary(self, contact: LinkedInContact) -> Dict:
        """Get summary for a contact"""
        return {
            'name': contact.full_name,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'company': contact.company,
            'position': contact.position,
            'profile_url': contact.profile_url,
            'connected_on': contact.connected_on.isoformat() if contact.connected_on else None,
            'message_count': contact.message_count,
            'first_message': contact.first_message.isoformat() if contact.first_message else None,
            'last_message': contact.last_message.isoformat() if contact.last_message else None,
        }


def parse_linkedin_export(export_path: str) -> List[Dict]:
    """
    Convenience function to parse LinkedIn export

    Args:
        export_path: Path to LinkedIn export (ZIP or directory)

    Returns:
        List of contact dictionaries
    """
    parser = LinkedInParser()
    contacts = parser.parse_export(export_path)

    return [parser.get_contact_summary(c) for c in contacts.values()]
