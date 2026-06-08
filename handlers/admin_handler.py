"""Admin commands — Arabic UI."""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.db import ban_user_db, unban_user_db, get_banned_users

logger = logging.getLogger(__name__)

ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = set(int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit())


def is_admin(user_id: int) -> bool:
    return not ADMIN_IDS or user_id in ADMIN_IDS


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ *الاستخدام:* `/ban <معرّف المستخدم> [السبب]`", parse_mode="Markdown"
        )
        return
    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "انتهاك شروط الاستخدام"
        ban_user_db(target_id, reason, update.effective_user.id)
        await update.message.reply_text(
            f"🚫 تم حظر المستخدم `{target_id}`\n📋 السبب: {reason}",
            parse_mode="Markdown"
        )
        logger.warning("Admin %s banned %s: %s", update.effective_user.id, target_id, reason)
    except ValueError:
        await update.message.reply_text("❌ معرّف المستخدم يجب أن يكون رقماً.")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ *الاستخدام:* `/unban <معرّف المستخدم>`", parse_mode="Markdown"
        )
        return
    try:
        target_id = int(context.args[0])
        unban_user_db(target_id)
        await update.message.reply_text(
            f"✅ تم رفع الحظر عن المستخدم `{target_id}`", parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ معرّف المستخدم يجب أن يكون رقماً.")


async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية لاستخدام هذا الأمر.")
        return
    banned = get_banned_users()
    if not banned:
        await update.message.reply_text("✅ لا يوجد مستخدمون محظورون حالياً.")
        return
    lines = ["🚫 *قائمة المستخدمين المحظورين:*\n"]
    for b in banned:
        lines.append(f"• `{b['user_id']}` — {b['reason']} ({b['banned_at'][:10]})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
