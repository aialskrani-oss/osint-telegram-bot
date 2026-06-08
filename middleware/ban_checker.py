"""Ban checker middleware — Arabic messages."""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database.db import is_banned


def ban_checker_middleware(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return await func(update, context)
        if is_banned(update.effective_user.id):
            await update.message.reply_text(
                "🚫 *تم حظرك من استخدام هذا البوت* بسبب انتهاك شروط الاستخدام.\n"
                "إذا اعتقدت أن هذا خطأ، تواصل مع مشرف البوت.",
                parse_mode="Markdown"
            )
            return
        return await func(update, context)
    return wrapper
