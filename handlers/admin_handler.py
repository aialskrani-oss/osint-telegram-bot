"""
Admin commands: ban/unban users.
"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.db import ban_user_db, unban_user_db, get_banned_users

logger = logging.getLogger(__name__)

ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = set(int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit())


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or not ADMIN_IDS  # If no admins set, first user can admin


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban `<user_id> [reason]`", parse_mode="Markdown")
        return

    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Policy violation"
        ban_user_db(target_id, reason, user.id)
        await update.message.reply_text(
            f"🚫 User `{target_id}` has been banned.\nReason: {reason}",
            parse_mode="Markdown"
        )
        logger.warning("User %s banned %s for: %s", user.id, target_id, reason)
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unban `<user_id>`", parse_mode="Markdown")
        return

    try:
        target_id = int(context.args[0])
        unban_user_db(target_id)
        await update.message.reply_text(f"✅ User `{target_id}` has been unbanned.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")


async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    banned = get_banned_users()
    if not banned:
        await update.message.reply_text("✅ No banned users.")
        return

    lines = ["🚫 *Banned Users:*\n"]
    for b in banned:
        lines.append(f"• ID: `{b['user_id']}` — {b['reason']} ({b['banned_at'][:10]})")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
