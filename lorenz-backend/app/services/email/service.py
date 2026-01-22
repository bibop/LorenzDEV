"""
LORENZ SaaS - Email Service Implementation
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
import logging

from app.models import User, EmailAccount, OAuthConnection
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_imap_account(
        self,
        user: User,
        email: str,
        provider: str,
        display_name: Optional[str] = None,
        imap_host: Optional[str] = None,
        imap_port: int = 993,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        password: Optional[str] = None,
        signature: Optional[str] = None,
        **kwargs
    ) -> EmailAccount:
        """Create an IMAP email account"""

        # Validate IMAP credentials
        if provider == "imap":
            if not all([imap_host, smtp_host, password]):
                raise ValueError("IMAP accounts require host and password")

        # Check if account already exists
        query = select(EmailAccount).where(
            EmailAccount.user_id == user.id,
            EmailAccount.email == email
        )
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Email account already exists")

        # Encrypt password
        from cryptography.fernet import Fernet
        fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted_password = fernet.encrypt(password.encode()).decode() if password else None

        # Check if this is the first account (make it primary)
        # Use database query instead of lazy-loaded relationship
        from sqlalchemy import func
        count_query = select(func.count(EmailAccount.id)).where(EmailAccount.user_id == user.id)
        count_result = await self.db.execute(count_query)
        account_count = count_result.scalar() or 0
        is_primary = account_count == 0

        account = EmailAccount(
            user_id=user.id,
            email=email,
            display_name=display_name or email,
            provider=provider,
            imap_host=imap_host or settings.DEFAULT_IMAP_HOST,
            imap_port=imap_port,
            smtp_host=smtp_host or settings.DEFAULT_SMTP_HOST,
            smtp_port=smtp_port,
            password_encrypted=encrypted_password,
            signature=signature,
            is_primary=is_primary,
            sync_status="pending"
        )

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        return account

    async def get_account(self, account_id: UUID, user_id: UUID) -> Optional[EmailAccount]:
        """Get an email account by ID"""
        query = select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_account(
        self,
        account_id: UUID,
        user_id: UUID,
        **kwargs
    ) -> EmailAccount:
        """Update an email account"""
        account = await self.get_account(account_id, user_id)
        if not account:
            raise ValueError("Account not found")

        for key, value in kwargs.items():
            if hasattr(account, key) and value is not None:
                setattr(account, key, value)

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        return account

    async def delete_account(self, account_id: UUID, user_id: UUID):
        """Delete an email account"""
        account = await self.get_account(account_id, user_id)
        if not account:
            raise ValueError("Account not found")

        await self.db.delete(account)
        await self.db.commit()

    async def sync_account(self, account_id: UUID):
        """Sync emails for an account (background task)"""
        query = select(EmailAccount).where(EmailAccount.id == account_id)
        result = await self.db.execute(query)
        account = result.scalar_one_or_none()

        if not account:
            logger.error(f"Account {account_id} not found for sync")
            return

        try:
            account.sync_status = "syncing"
            self.db.add(account)
            await self.db.commit()

            if account.provider == "gmail":
                await self._sync_gmail(account)
            elif account.provider == "outlook":
                await self._sync_outlook(account)
            else:
                await self._sync_imap(account)

            account.sync_status = "synced"
            account.sync_error = None

        except Exception as e:
            logger.error(f"Sync error for {account.email}: {e}")
            account.sync_status = "error"
            account.sync_error = str(e)

        finally:
            from datetime import datetime
            account.last_sync_at = datetime.utcnow()
            self.db.add(account)
            await self.db.commit()

    async def _sync_gmail(self, account: EmailAccount):
        """Sync via Gmail API"""
        # Get OAuth connection
        if not account.oauth_connection_id:
            raise ValueError("No OAuth connection for Gmail account")

        query = select(OAuthConnection).where(OAuthConnection.id == account.oauth_connection_id)
        result = await self.db.execute(query)
        oauth = result.scalar_one_or_none()

        if not oauth:
            raise ValueError("OAuth connection not found")

        # Use Gmail API to fetch emails
        # This is a placeholder - implement full Gmail API integration
        logger.info(f"Syncing Gmail account: {account.email}")

    async def _sync_outlook(self, account: EmailAccount):
        """Sync via Microsoft Graph API"""
        if not account.oauth_connection_id:
            raise ValueError("No OAuth connection for Outlook account")

        query = select(OAuthConnection).where(OAuthConnection.id == account.oauth_connection_id)
        result = await self.db.execute(query)
        oauth = result.scalar_one_or_none()

        if not oauth:
            raise ValueError("OAuth connection not found")

        # Use MS Graph API to fetch emails
        logger.info(f"Syncing Outlook account: {account.email}")

    async def _sync_imap(self, account: EmailAccount):
        """Sync via IMAP and index emails to RAG"""
        import imaplib
        import email
        from email.header import decode_header

        # Decrypt password
        from cryptography.fernet import Fernet
        fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        password = fernet.decrypt(account.password_encrypted.encode()).decode()

        # Get user's tenant_id for RAG indexing
        from sqlalchemy import select as sql_select
        query = sql_select(User).where(User.id == account.user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        tenant_id = user.tenant_id if user else None

        # Connect to IMAP
        imap = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
        emails_to_index = []

        try:
            imap.login(account.email, password)
            imap.select("INBOX")

            # Fetch recent emails
            _, message_numbers = imap.search(None, "ALL")
            email_ids = message_numbers[0].split()[-50:]  # Last 50 emails

            for email_id in email_ids:
                try:
                    _, msg_data = imap.fetch(email_id, "(RFC822)")
                    if not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Decode subject
                    subject = ""
                    if msg["Subject"]:
                        decoded = decode_header(msg["Subject"])
                        subject = "".join([
                            part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
                            for part, encoding in decoded
                        ])

                    # Get sender
                    from_address = msg.get("From", "")

                    # Get recipients
                    to_addresses = msg.get("To", "").split(",")

                    # Get date
                    date_str = msg.get("Date", "")

                    # Get body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                    break
                                except Exception:
                                    pass
                            elif content_type == "text/html" and not body:
                                try:
                                    html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                    # Simple HTML to text
                                    import re
                                    body = re.sub(r'<[^>]+>', ' ', html)
                                    body = re.sub(r'\s+', ' ', body).strip()
                                except Exception:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                        except Exception:
                            body = str(msg.get_payload())

                    # Get attachments
                    attachments = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_disposition() == "attachment":
                                filename = part.get_filename()
                                if filename:
                                    attachments.append(filename)

                    # Prepare email data for indexing
                    emails_to_index.append({
                        "message_id": msg.get("Message-ID", email_id.decode()),
                        "from_address": from_address,
                        "to_addresses": to_addresses,
                        "subject": subject,
                        "body": body[:10000],  # Limit body size
                        "date": date_str,
                        "attachments": attachments
                    })

                except Exception as e:
                    logger.warning(f"Failed to parse email {email_id}: {e}")
                    continue

            logger.info(f"Fetched {len(emails_to_index)} emails for {account.email}")

        finally:
            imap.logout()

        # Index emails to RAG if we have tenant_id
        if tenant_id and emails_to_index:
            try:
                from app.services.rag import RAGService
                rag_service = RAGService(self.db)
                result = await rag_service.index_emails_batch(
                    user_id=account.user_id,
                    tenant_id=tenant_id,
                    emails=emails_to_index
                )
                logger.info(f"Indexed {result['indexed']} emails to RAG for {account.email}")
            except Exception as e:
                logger.error(f"Failed to index emails to RAG: {e}")

    async def list_messages(
        self,
        user_id: UUID,
        account_id: Optional[UUID] = None,
        folder: str = "INBOX",
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[dict]:
        """List emails from accounts via IMAP"""
        import imaplib
        import email
        from email.header import decode_header
        from datetime import datetime
        import asyncio

        messages = []

        # Get accounts to fetch from
        if account_id:
            accounts = [await self.get_account(account_id, user_id)]
            accounts = [a for a in accounts if a]
        else:
            query = select(EmailAccount).where(EmailAccount.user_id == user_id)
            result = await self.db.execute(query)
            accounts = result.scalars().all()

        if not accounts:
            return []

        for account in accounts:
            if account.provider != "imap" or not account.password_encrypted:
                continue

            try:
                # Decrypt password
                from cryptography.fernet import Fernet
                fernet = Fernet(settings.ENCRYPTION_KEY.encode())
                password = fernet.decrypt(account.password_encrypted.encode()).decode()

                # Run IMAP fetch in thread pool to avoid blocking
                def fetch_emails():
                    emails = []
                    try:
                        imap = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
                        imap.login(account.email, password)
                        imap.select(folder)

                        # Search criteria
                        search_criteria = "UNSEEN" if unread_only else "ALL"
                        _, message_numbers = imap.search(None, search_criteria)
                        email_ids = message_numbers[0].split()

                        # Apply offset and limit (from newest)
                        email_ids = list(reversed(email_ids))
                        email_ids = email_ids[offset:offset + limit]

                        for email_id in email_ids:
                            try:
                                _, msg_data = imap.fetch(email_id, "(RFC822 FLAGS)")
                                if not msg_data or not msg_data[0]:
                                    continue

                                raw_email = msg_data[0][1]
                                flags = msg_data[0][0].decode() if msg_data[0][0] else ""
                                msg = email.message_from_bytes(raw_email)

                                # Decode subject
                                subject = ""
                                if msg["Subject"]:
                                    decoded = decode_header(msg["Subject"])
                                    subject = "".join([
                                        part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
                                        for part, encoding in decoded
                                    ])

                                # Get sender
                                from_address = msg.get("From", "")
                                from_name = ""
                                if "<" in from_address:
                                    from_name = from_address.split("<")[0].strip().strip('"')
                                    from_address = from_address.split("<")[1].rstrip(">")

                                # Get recipients
                                to_addresses = [a.strip() for a in msg.get("To", "").split(",")]

                                # Get date
                                date_str = msg.get("Date", "")
                                try:
                                    from email.utils import parsedate_to_datetime
                                    date = parsedate_to_datetime(date_str)
                                except:
                                    date = datetime.now()

                                # Get body snippet
                                body = ""
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == "text/plain":
                                            try:
                                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                                break
                                            except:
                                                pass
                                else:
                                    try:
                                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                                    except:
                                        body = str(msg.get_payload())

                                # Check flags
                                is_read = "\\Seen" in flags
                                is_starred = "\\Flagged" in flags

                                # Check attachments
                                has_attachments = False
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_disposition() == "attachment":
                                            has_attachments = True
                                            break

                                emails.append({
                                    "id": email_id.decode(),
                                    "account_id": str(account.id),
                                    "subject": subject,
                                    "from_address": from_address,
                                    "from_name": from_name,
                                    "to_addresses": to_addresses,
                                    "cc_addresses": [],
                                    "date": date.isoformat(),
                                    "snippet": body[:200] if body else "",
                                    "body_text": body[:5000] if body else "",
                                    "is_read": is_read,
                                    "is_starred": is_starred,
                                    "has_attachments": has_attachments,
                                    "attachments": [],
                                    "labels": [],
                                })
                            except Exception as e:
                                logger.warning(f"Failed to parse email: {e}")
                                continue

                        imap.logout()
                    except Exception as e:
                        logger.error(f"IMAP fetch error for {account.email}: {e}")
                    return emails

                # Run in thread pool
                loop = asyncio.get_event_loop()
                account_messages = await loop.run_in_executor(None, fetch_emails)
                messages.extend(account_messages)

            except Exception as e:
                logger.error(f"Failed to list messages for {account.email}: {e}")

        # Sort by date (newest first)
        messages.sort(key=lambda x: x.get("date", ""), reverse=True)
        return messages[:limit]

    async def get_message(
        self,
        user_id: UUID,
        account_id: UUID,
        message_id: str
    ) -> dict:
        """Get a specific email"""
        # Placeholder
        raise ValueError("Message not found")

    async def send_email(
        self,
        user_id: UUID,
        account_id: UUID,
        to: List[str],
        subject: str,
        body: str,
        **kwargs
    ) -> dict:
        """Send an email"""
        account = await self.get_account(account_id, user_id)
        if not account:
            raise ValueError("Account not found")

        # Implement SMTP sending
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = account.email
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        # Get password
        from cryptography.fernet import Fernet
        fernet = Fernet(settings.ENCRYPTION_KEY.encode())

        if account.password_encrypted:
            password = fernet.decrypt(account.password_encrypted.encode()).decode()
        else:
            # OAuth account - get token
            raise ValueError("OAuth email sending not implemented yet")

        with smtplib.SMTP(account.smtp_host, account.smtp_port) as server:
            server.starttls()
            server.login(account.email, password)
            server.send_message(msg)

        return {"success": True, "message_id": None}

    async def mark_read(
        self,
        user_id: UUID,
        account_id: UUID,
        message_id: str
    ):
        """Mark an email as read"""
        # Placeholder
        pass

    async def search(
        self,
        user_id: UUID,
        query: str,
        **kwargs
    ) -> List[dict]:
        """Search emails"""
        # Placeholder
        return []

    async def get_stats(self, user_id: UUID) -> dict:
        """Get email statistics"""
        query = select(EmailAccount).where(EmailAccount.user_id == user_id)
        result = await self.db.execute(query)
        accounts = result.scalars().all()

        return {
            "total_accounts": len(accounts),
            "total_emails": 0,  # Placeholder
            "unread_count": 0,
            "today_received": 0,
            "accounts": [
                {
                    "id": str(a.id),
                    "email": a.email,
                    "provider": a.provider,
                    "sync_status": a.sync_status,
                    "stats": a.stats
                }
                for a in accounts
            ]
        }
