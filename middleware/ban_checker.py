"""
Ban checker middleware — blocks banned users from using the bot.
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database.db import is_banned


def ban_checker_middleware(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return await func(update, context)
        user_id = update.effective_user.id
        if is_banned(user_id):
            await update.message.reply_text(
                "🚫 You have been banned from using this bot due to a policy violation."
            )
            return
        return await func(update, context)
    return wrapper
