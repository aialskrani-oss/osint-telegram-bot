"""Advanced multi-criteria search — Arabic UI."""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.db import log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware

logger = logging.getLogger(__name__)

ADVANCED_HELP = """
🔬 *البحث المتقدم — عدة معايير دفعة واحدة*

*الصيغة:*
`/advanced_search -u <يوزرنيم> -e <إيميل> -p <هاتف> -n <اسم> -l <بلد>`

*الأعلام المتاحة:*
• `-u` أو `--username` — اليوزرنيم
• `-e` أو `--email` — الإيميل
• `-p` أو `--phone` — رقم الهاتف (مع كود الدولة)
• `-n` أو `--name` — الاسم الكامل
• `-l` أو `--location` — البلد أو المنطقة

*أمثلة:*
`/advanced_search -u johndoe -e john@example.com`
`/advanced_search -u johndoe -l السعودية`
`/advanced_search -e john@example.com -p +966501234567`

جميع أنواع البحث تعمل بالتوازي وتُجمع نتائجها.
"""


def parse_args(args: list) -> dict:
    params = {}
    i = 0
    while i < len(args):
        flag = args[i].lower()
        if flag in ("-u", "--username") and i + 1 < len(args):
            params["username"] = args[i + 1]; i += 2
        elif flag in ("-e", "--email") and i + 1 < len(args):
            params["email"] = args[i + 1]; i += 2
        elif flag in ("-p", "--phone") and i + 1 < len(args):
            params["phone"] = args[i + 1]; i += 2
        elif flag in ("-n", "--name") and i + 1 < len(args):
            name_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("-"):
                name_parts.append(args[i]); i += 1
            params["name"] = " ".join(name_parts)
        elif flag in ("-l", "--location") and i + 1 < len(args):
            params["location"] = args[i + 1]; i += 2
        else:
            i += 1
    return params


@ban_checker_middleware
@rate_limit_middleware
async def advanced_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(ADVANCED_HELP, parse_mode="Markdown")
        return

    params = parse_args(context.args)
    if not params:
        await update.message.reply_text(
            "❌ لم يتم التعرف على أي معيار بحث.\n\n" + ADVANCED_HELP,
            parse_mode="Markdown"
        )
        return

    user = update.effective_user
    type_ar = {
        "username": "يوزرنيم", "email": "إيميل", "phone": "هاتف",
        "name": "اسم", "location": "موقع"
    }

    summary = "\n".join(f"• *{type_ar.get(k, k)}:* `{v}`" for k, v in params.items())
    status_msg = await update.message.reply_text(
        f"🔬 *بحث متقدم — {len(params)} معيار*\n\n{summary}\n\n"
        "⏳ جاري تشغيل جميع عمليات البحث بالتوازي...",
        parse_mode="Markdown"
    )

    log_search(user.id, user.username, "advanced", str(params), f"{len(params)} معيار")

    result_text = (
        f"🔬 *نتائج البحث المتقدم*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"تم تنفيذ البحث بـ *{len(params)} معيار*:\n\n"
    )
    for search_type, query in params.items():
        cmd_map = {
            "username": "search_username",
            "email": "search_email",
            "phone": "search_phone",
            "name": "search_name",
            "location": "search_location"
        }
        cmd = cmd_map.get(search_type, f"search_{search_type}")
        result_text += f"▶️ *{type_ar.get(search_type, search_type)}:* `{query}`\n"
        result_text += f"   → /{cmd} {query}\n\n"

    result_text += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 انقر على كل أمر للاطلاع على نتائجه الكاملة."
    )
    await status_msg.edit_text(result_text, parse_mode="Markdown", disable_web_page_preview=True)
