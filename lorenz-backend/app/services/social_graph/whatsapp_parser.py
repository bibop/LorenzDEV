"""
LORENZ SaaS - WhatsApp Chat Parser
Parses exported WhatsApp chat files (.txt)

To export: WhatsApp > Chat > More > Export Chat > Without Media
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessage:
    """Single WhatsApp message"""
    timestamp: datetime
    sender: str
    content: str
    is_media: bool = False
    media_type: Optional[str] = None


@dataclass
class WhatsAppContact:
    """Contact extracted from WhatsApp"""
    name: str
    phone: Optional[str] = None
    message_count: int = 0
    first_message: Optional[datetime] = None
    last_message: Optional[datetime] = None
    messages: List[WhatsAppMessage] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


class WhatsAppParser:
    """
    Parser for WhatsApp exported chat files

    Supports multiple date formats:
    - [DD/MM/YY, HH:MM:SS] (Italian/European)
    - [MM/DD/YY, HH:MM:SS] (US)
    - [DD/MM/YYYY, HH:MM:SS] (Extended year)
    - DD/MM/YY, HH:MM - Name: Message (without brackets)
    """

    # Regex patterns for different WhatsApp export formats
    PATTERNS = [
        # [DD/MM/YY, HH:MM:SS] Name: Message
        r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.+)',
        # DD/MM/YY, HH:MM - Name: Message
        r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*([^:]+):\s*(.+)',
        # MM/DD/YY, HH:MM AM/PM - Name: Message (US format)
        r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*-\s*([^:]+):\s*(.+)',
    ]

    # System messages to ignore
    SYSTEM_PATTERNS = [
        r'Messages and calls are end-to-end encrypted',
        r'I messaggi e le chiamate sono protetti',
        r'created group',
        r'ha creato il gruppo',
        r'added',
        r'aggiunto',
        r'left',
        r'ha abbandonato',
        r'changed the subject',
        r'ha modificato l\'oggetto',
        r'changed this group\'s icon',
        r'ha modificato l\'icona',
        r'security code changed',
        r'codice di sicurezza è cambiato',
        r'Missed voice call',
        r'Chiamata vocale persa',
        r'Missed video call',
        r'Videochiamata persa',
    ]

    # Media indicators
    MEDIA_PATTERNS = {
        'image': [r'<Media omitted>', r'<Allegato: immagine>', r'image omitted', r'\.jpg omitted', r'\.png omitted'],
        'video': [r'video omitted', r'<Allegato: video>', r'\.mp4 omitted'],
        'audio': [r'audio omitted', r'<Allegato: audio>', r'\.opus omitted', r'\.ogg omitted'],
        'document': [r'document omitted', r'<Allegato: documento>', r'\.pdf omitted', r'\.docx? omitted'],
        'sticker': [r'sticker omitted', r'<Allegato: sticker>'],
        'contact': [r'Contact card omitted', r'Scheda contatto omessa'],
        'location': [r'Location:', r'Posizione:'],
    }

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATTERNS]
        self.system_patterns = [re.compile(p, re.IGNORECASE) for p in self.SYSTEM_PATTERNS]

    def parse_file(self, file_path: str) -> Dict[str, WhatsAppContact]:
        """
        Parse a WhatsApp exported chat file

        Args:
            file_path: Path to the .txt export file

        Returns:
            Dictionary of contacts keyed by name
        """
        contacts: Dict[str, WhatsAppContact] = {}

        try:
            # Try different encodings
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                raise ValueError(f"Could not decode file with any supported encoding")

            # Split into lines, handling multi-line messages
            lines = content.split('\n')
            current_message = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Try to parse as new message
                parsed = self._parse_line(line)

                if parsed:
                    timestamp, sender, content = parsed

                    # Skip system messages
                    if self._is_system_message(content) or self._is_system_message(sender):
                        continue

                    # Detect media
                    is_media, media_type = self._detect_media(content)

                    message = WhatsAppMessage(
                        timestamp=timestamp,
                        sender=sender,
                        content=content,
                        is_media=is_media,
                        media_type=media_type
                    )

                    # Add to contact
                    if sender not in contacts:
                        contacts[sender] = WhatsAppContact(
                            name=sender,
                            first_message=timestamp
                        )

                    contact = contacts[sender]
                    contact.messages.append(message)
                    contact.message_count += 1
                    contact.last_message = timestamp

                    current_message = message

                elif current_message:
                    # This is a continuation of the previous message
                    current_message.content += f"\n{line}"

            logger.info(f"Parsed {len(contacts)} contacts from WhatsApp export")
            return contacts

        except Exception as e:
            logger.error(f"Error parsing WhatsApp file {file_path}: {e}")
            raise

    def _parse_line(self, line: str) -> Optional[Tuple[datetime, str, str]]:
        """Try to parse a line as a message"""
        for pattern in self.compiled_patterns:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                date_str = groups[0]
                time_str = groups[1]
                sender = groups[2].strip()
                content = groups[3].strip()

                # Parse timestamp
                timestamp = self._parse_timestamp(date_str, time_str)
                if timestamp:
                    return timestamp, sender, content

        return None

    def _parse_timestamp(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time strings into datetime"""
        # Try different date formats
        date_formats = [
            '%d/%m/%y',
            '%d/%m/%Y',
            '%m/%d/%y',
            '%m/%d/%Y',
        ]

        # Clean time string
        time_str = time_str.strip()
        has_seconds = time_str.count(':') == 2
        has_ampm = 'AM' in time_str.upper() or 'PM' in time_str.upper()

        for date_fmt in date_formats:
            for time_fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p']:
                if has_seconds and ':' not in time_fmt[-2:]:
                    continue
                if has_ampm and 'p' not in time_fmt.lower():
                    continue

                try:
                    dt_str = f"{date_str} {time_str}"
                    fmt = f"{date_fmt} {time_fmt}"
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue

        return None

    def _is_system_message(self, text: str) -> bool:
        """Check if text is a system message"""
        for pattern in self.system_patterns:
            if pattern.search(text):
                return True
        return False

    def _detect_media(self, content: str) -> Tuple[bool, Optional[str]]:
        """Detect if message contains media"""
        content_lower = content.lower()

        for media_type, patterns in self.MEDIA_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True, media_type

        return False, None

    def extract_phone_from_name(self, name: str) -> Optional[str]:
        """
        Extract phone number if the contact name is a phone number
        (happens when contact is not saved)
        """
        # Remove common prefixes
        clean = re.sub(r'^[\+\s]+', '', name)

        # Check if it looks like a phone number
        if re.match(r'^\d[\d\s\-]{8,}$', clean):
            # Normalize to digits only
            return re.sub(r'[^\d+]', '', name)

        return None

    def get_conversation_summary(self, contact: WhatsAppContact) -> Dict:
        """Get summary statistics for a conversation"""
        if not contact.messages:
            return {}

        total_chars = sum(len(m.content) for m in contact.messages)
        media_count = sum(1 for m in contact.messages if m.is_media)

        return {
            'name': contact.name,
            'phone': contact.phone or self.extract_phone_from_name(contact.name),
            'total_messages': contact.message_count,
            'media_messages': media_count,
            'text_messages': contact.message_count - media_count,
            'avg_message_length': total_chars / len(contact.messages) if contact.messages else 0,
            'first_message': contact.first_message.isoformat() if contact.first_message else None,
            'last_message': contact.last_message.isoformat() if contact.last_message else None,
            'days_active': (contact.last_message - contact.first_message).days if contact.first_message and contact.last_message else 0
        }


def parse_whatsapp_export(file_path: str) -> List[Dict]:
    """
    Convenience function to parse WhatsApp export and return contact list

    Args:
        file_path: Path to exported .txt file

    Returns:
        List of contact dictionaries with summary stats
    """
    parser = WhatsAppParser()
    contacts = parser.parse_file(file_path)

    return [parser.get_conversation_summary(c) for c in contacts.values()]
