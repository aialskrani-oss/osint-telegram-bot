"""
Rate limiting middleware — max 5 searches per minute per user.
"""
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_rate_limit_count, add_rate_limit_entry

logger = logging.getLogger(__name__)

MAX_REQUESTS = 5
WINDOW_SECONDS = 60


def rate_limit_middleware(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return await func(update, context)
        user_id = update.effective_user.id
        action = func.__name__
        count = get_rate_limit_count(user_id, action, WINDOW_SECONDS)
        if count >= MAX_REQUESTS:
            await update.message.reply_text(
                "⚠️ *Rate limit reached.* You can perform up to 5 searches per minute.\n"
                "Please wait a moment before trying again.",
                parse_mode="Markdown"
            )
            logger.warning("Rate limit hit for user %s on %s", user_id, action)
            return
        add_rate_limit_entry(user_id, action)
        return await func(update, context)
    return wrapper
