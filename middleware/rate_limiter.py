"""Rate limiting — max 5 requests/minute per user. Arabic messages."""
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
        count = get_rate_limit_count(user_id, func.__name__, WINDOW_SECONDS)
        if count >= MAX_REQUESTS:
            await update.message.reply_text(
                "⏳ *تجاوزت حد الاستخدام!*\n\n"
                f"الحد المسموح به: {MAX_REQUESTS} عمليات بحث في الدقيقة.\n"
                "انتظر لحظة ثم حاول مجدداً.",
                parse_mode="Markdown"
            )
            logger.warning("Rate limit: user %s on %s", user_id, func.__name__)
            return
        add_rate_limit_entry(user_id, func.__name__)
        return await func(update, context)
    return wrapper
