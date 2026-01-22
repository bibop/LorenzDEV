"""
LORENZ SaaS - Telegram Service Implementation
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import aiohttp
import logging

from app.models import User
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Telegram bot service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_base = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: dict = None
    ):
        """Send a message to a Telegram chat"""
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured")
            return

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/sendMessage",
                json=payload
            ) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    logger.error(f"Telegram send failed: {result}")
                return result

    async def answer_callback(self, callback_id: str, text: str = None):
        """Answer a callback query"""
        if not settings.TELEGRAM_BOT_TOKEN:
            return

        payload = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/answerCallbackQuery",
                json=payload
            ) as resp:
                return await resp.json()

    async def verify_code(self, chat_id: int, code: str) -> bool:
        """
        Verify a code sent to the bot.
        Links the Telegram chat to a user account.
        """
        # Find user with this verification code
        query = select(User).where(
            User.telegram_verification_code == code
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Check expiry
        if user.telegram_verification_expires:
            expires = datetime.fromisoformat(user.telegram_verification_expires)
            if datetime.utcnow() > expires:
                return False

        # Link account
        user.telegram_chat_id = chat_id
        user.telegram_verification_code = None
        user.telegram_verification_expires = None

        self.db.add(user)
        await self.db.commit()

        logger.info(f"Linked Telegram {chat_id} to user {user.email}")
        return True

    async def process_user_message(
        self,
        user: User,
        text: str,
        message: dict
    ):
        """Process a message from an authenticated user"""
        # Import AI service
        from app.services.ai import AIService

        ai_service = AIService(self.db)

        # Handle commands
        if text.startswith("/"):
            await self._handle_command(user, text, message)
            return

        # Regular message - send to AI
        try:
            response = await ai_service.chat(
                user=user,
                message=text,
                channel="telegram"
            )

            # Send response
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text=response["content"]
            )
        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}")
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text="Sorry, I encountered an error processing your message. Please try again."
            )

    async def _handle_command(self, user: User, text: str, message: dict):
        """Handle Telegram commands"""
        command = text.split()[0].lower()
        args = text.split()[1:] if len(text.split()) > 1 else []

        if command == "/start":
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text=f"""Welcome to LORENZ, {user.name or 'there'}!

I'm your AI personal assistant. I can help you with:
- 📧 Email management
- 📅 Calendar
- 📝 Notes and documents
- 🔍 Knowledge search
- 💬 General questions

Just send me a message to get started!

Commands:
/status - Check your account status
/email - Check recent emails
/help - Show this help message
"""
            )

        elif command == "/help":
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text="""LORENZ Commands:

/status - Your account status
/email - Check recent emails
/calendar - Today's events
/search <query> - Search knowledge base
/help - This help message

Or just type naturally and I'll assist you!
"""
            )

        elif command == "/status":
            # Get user stats
            email_count = len(user.email_accounts)
            rag_count = len(user.rag_documents)

            await self.send_message(
                chat_id=user.telegram_chat_id,
                text=f"""📊 Account Status

👤 Name: {user.name or 'Not set'}
📧 Email: {user.email}
📬 Connected accounts: {email_count}
📚 Documents indexed: {rag_count}
✅ Account active: Yes
"""
            )

        elif command == "/email":
            # Placeholder - implement email checking
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text="Email checking not yet implemented. Coming soon!"
            )

        else:
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text=f"Unknown command: {command}\n\nUse /help to see available commands."
            )

    async def handle_callback(
        self,
        user: User,
        callback_data: str,
        callback_id: str
    ):
        """Handle callback queries from inline buttons"""
        await self.answer_callback(callback_id, "Processing...")

        # Parse callback data and handle accordingly
        # Format: action:param1:param2
        parts = callback_data.split(":")
        action = parts[0]

        if action == "email_read":
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text="Email read functionality coming soon!"
            )
        else:
            await self.send_message(
                chat_id=user.telegram_chat_id,
                text=f"Unknown action: {action}"
            )
