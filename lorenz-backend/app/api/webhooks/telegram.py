"""
LORENZ SaaS - Telegram Webhook Handler
"""

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json

from app.database import async_session
from app.models import User
from app.services.telegram import TelegramService
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram updates.
    This endpoint receives all messages sent to the LORENZ bot.
    """
    try:
        # Parse the update
        update = await request.json()
        logger.info(f"Received Telegram update: {json.dumps(update)[:200]}...")

        # Get message or callback query
        message = update.get("message")
        callback_query = update.get("callback_query")

        if message:
            await handle_message(message)
        elif callback_query:
            await handle_callback(callback_query)

        return {"ok": True}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        # Always return 200 to Telegram to prevent retries
        return {"ok": False, "error": str(e)}


async def handle_message(message: dict):
    """Handle incoming Telegram message"""
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    user_info = message.get("from", {})

    if not chat_id:
        return

    async with async_session() as db:
        telegram_service = TelegramService(db)

        # Check if this is a verification code
        if text and len(text) == 6 and text.isalnum():
            # Try to verify this code
            verified = await telegram_service.verify_code(chat_id, text)
            if verified:
                await telegram_service.send_message(
                    chat_id,
                    "Telegram account linked successfully! You can now use LORENZ from here."
                )
                return

        # Find user by chat_id
        query = select(User).where(User.telegram_chat_id == chat_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # Unknown user
            await telegram_service.send_message(
                chat_id,
                "Welcome to LORENZ! To link your account, please:\n\n"
                "1. Go to your LORENZ dashboard\n"
                "2. Click 'Connect Telegram'\n"
                "3. Send the verification code here\n\n"
                "If you don't have an account yet, visit: https://bibop.com/lorenz"
            )
            return

        # Process message for authenticated user
        await telegram_service.process_user_message(user, text, message)


async def handle_callback(callback_query: dict):
    """Handle Telegram callback query (button clicks)"""
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    callback_data = callback_query.get("data", "")
    callback_id = callback_query.get("id")

    if not chat_id or not callback_data:
        return

    async with async_session() as db:
        telegram_service = TelegramService(db)

        # Find user
        query = select(User).where(User.telegram_chat_id == chat_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            await telegram_service.handle_callback(user, callback_data, callback_id)
        else:
            await telegram_service.answer_callback(callback_id, "Please link your account first")


@router.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """
    Set the Telegram webhook URL.
    Only call this once during setup or when webhook URL changes.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    if not settings.TELEGRAM_WEBHOOK_URL:
        raise HTTPException(status_code=400, detail="Telegram webhook URL not configured")

    import aiohttp
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
        async with session.post(url, json={"url": settings.TELEGRAM_WEBHOOK_URL}) as resp:
            result = await resp.json()
            if result.get("ok"):
                return {"message": "Webhook set successfully", "result": result}
            else:
                raise HTTPException(status_code=400, detail=result)


@router.get("/telegram/webhook-info")
async def get_telegram_webhook_info():
    """
    Get current Telegram webhook info.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    import aiohttp
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
        async with session.get(url) as resp:
            result = await resp.json()
            return result
