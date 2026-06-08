"""Bot status and statistics command."""
import os
import sys
import platform
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_conn
from middleware.ban_checker import ban_checker_middleware

logger = logging.getLogger(__name__)
BOT_START_TIME = datetime.utcnow()


def get_stats() -> dict:
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM search_history")
        total_searches = c.fetchone()["cnt"]

        c.execute("SELECT COUNT(DISTINCT user_id) as cnt FROM search_history")
        unique_users = c.fetchone()["cnt"]

        c.execute("""SELECT query_type, COUNT(*) as cnt FROM search_history
                     GROUP BY query_type ORDER BY cnt DESC LIMIT 5""")
        top_types = c.fetchall()

        c.execute("SELECT COUNT(*) as cnt FROM search_cache")
        cached_results = c.fetchone()["cnt"]

        c.execute("SELECT COUNT(*) as cnt FROM banned_users")
        banned_count = c.fetchone()["cnt"]

        conn.close()
        return {
            "total_searches": total_searches,
            "unique_users": unique_users,
            "top_types": [(r["query_type"], r["cnt"]) for r in top_types],
            "cached_results": cached_results,
            "banned_count": banned_count,
        }
    except Exception as e:
        logger.error("Stats error: %s", e)
        return {}


@ban_checker_middleware
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = datetime.utcnow() - BOT_START_TIME
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{hours}س {minutes}د {seconds}ث"

    stats = get_stats()

    top_types_text = ""
    for search_type, count in stats.get("top_types", []):
        type_ar = {
            "username": "يوزرنيم", "email": "إيميل", "phone": "هاتف",
            "name": "اسم", "social": "منصة", "location": "موقع", "advanced": "متقدم"
        }.get(search_type, search_type)
        top_types_text += f"   • {type_ar}: {count} بحث\n"

    text = (
        "📊 *حالة البوت والإحصائيات*\n\n"
        f"🟢 *الحالة:* يعمل بشكل طبيعي\n"
        f"⏱ *وقت التشغيل:* {uptime_str}\n"
        f"🐍 *Python:* {platform.python_version()}\n\n"
        "━━━━━━━━ *إحصائيات البحث* ━━━━━━━━\n"
        f"🔍 *إجمالي عمليات البحث:* {stats.get('total_searches', 0)}\n"
        f"👥 *مستخدمون فريدون:* {stats.get('unique_users', 0)}\n"
        f"📦 *نتائج مخزّنة:* {stats.get('cached_results', 0)}\n"
        f"🚫 *مستخدمون محظورون:* {stats.get('banned_count', 0)}\n\n"
        "━━━━━━━━ *أكثر أنواع البحث* ━━━━━━━━\n"
        f"{top_types_text or '   لا توجد بيانات بعد'}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *GitHub:* [osint-telegram-bot](https://github.com/aialskrani-oss/osint-telegram-bot)"
    )
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
