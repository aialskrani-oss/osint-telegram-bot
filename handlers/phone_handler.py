"""Phone number search handler — Arabic UI."""
import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_phone_results

logger = logging.getLogger(__name__)


async def run_phoneinfoga(phone: str) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "phoneinfoga", "scan", "-n", phone,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        result = {}
        for line in stdout.decode("utf-8", errors="ignore").splitlines():
            if "Country" in line and ":" in line:
                result["country"] = line.split(":", 1)[1].strip()
            elif "Carrier" in line and ":" in line:
                result["carrier"] = line.split(":", 1)[1].strip()
            elif "Location" in line and ":" in line:
                result["location"] = line.split(":", 1)[1].strip()
        return result
    except Exception as e:
        logger.debug("phoneinfoga unavailable: %s", e)
        return {}


async def check_whatsapp(phone: str) -> bool:
    try:
        clean = phone.replace("+", "").replace(" ", "").replace("-", "")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wa.me/{clean}",
                                   allow_redirects=True,
                                   timeout=aiohttp.ClientTimeout(total=8)) as resp:
                text = await resp.text()
                return resp.status == 200 and "invalid" not in text.lower()
    except Exception:
        return False


@ban_checker_middleware
@rate_limit_middleware
async def search_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ *الاستخدام الصحيح:*\n`/search_phone <رقم الهاتف>`\n\n"
            "*مثال:* `/search_phone +966501234567`",
            parse_mode="Markdown"
        )
        return

    phone = context.args[0].strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    user = update.effective_user
    cached = get_cached("phone", phone)
    if cached:
        await update.message.reply_text(
            f"📦 *نتيجة محفوظة:*\n\n{format_phone_results(cached)}",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text(
        f"📞 جاري البحث عن الرقم `{phone}`...\n⏳ يرجى الانتظار...",
        parse_mode="Markdown"
    )

    info = {}
    whatsapp = False
    try:
        phoneinfoga_data, whatsapp_result = await asyncio.gather(
            run_phoneinfoga(phone), check_whatsapp(phone), return_exceptions=True
        )
        if isinstance(phoneinfoga_data, dict):
            info.update(phoneinfoga_data)
        if isinstance(whatsapp_result, bool):
            whatsapp = whatsapp_result
    except Exception as e:
        logger.error("Phone search error: %s", e)

    data = {"query": phone, "info": info, "social": {"whatsapp": whatsapp, "telegram": False}}
    set_cache("phone", phone, data)
    log_search(user.id, user.username, "phone", phone,
               f"المشغّل: {info.get('carrier', 'غير معروف')}")

    await status_msg.edit_text(format_phone_results(data), parse_mode="Markdown",
                               disable_web_page_preview=True)
