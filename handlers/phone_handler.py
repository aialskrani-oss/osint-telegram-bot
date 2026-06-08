"""
Phone number search handler using PhoneInfoga-style lookups.
"""
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


async def lookup_numverify(phone: str) -> dict:
    """Free phone lookup via open APIs."""
    info = {}
    try:
        # Use numverify-compatible open endpoint
        async with aiohttp.ClientSession() as session:
            url = f"https://phonevalidation.abstractapi.com/v1/?api_key=demo&phone={phone}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    info = {
                        "valid": data.get("valid", False),
                        "country": data.get("country", {}).get("name", ""),
                        "carrier": data.get("carrier", ""),
                        "line_type": data.get("type", ""),
                        "location": data.get("location", ""),
                        "timezone": ""
                    }
    except Exception as e:
        logger.debug("Abstract API failed: %s", e)
    return info


async def run_phoneinfoga(phone: str) -> dict:
    """Run PhoneInfoga if installed."""
    result = {}
    try:
        proc = await asyncio.create_subprocess_exec(
            "phoneinfoga", "scan", "-n", phone,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="ignore")
        result["raw"] = output[:2000]
        # Parse key fields
        for line in output.splitlines():
            if "Country" in line and ":" in line:
                result["country"] = line.split(":", 1)[1].strip()
            elif "Carrier" in line and ":" in line:
                result["carrier"] = line.split(":", 1)[1].strip()
            elif "Location" in line and ":" in line:
                result["location"] = line.split(":", 1)[1].strip()
    except Exception as e:
        logger.debug("PhoneInfoga not available: %s", e)
    return result


async def check_whatsapp(phone: str) -> bool:
    """Check if phone is on WhatsApp via wa.me redirect."""
    try:
        async with aiohttp.ClientSession() as session:
            clean = phone.replace("+", "").replace(" ", "").replace("-", "")
            url = f"https://wa.me/{clean}"
            async with session.get(url, allow_redirects=True,
                                   timeout=aiohttp.ClientTimeout(total=8)) as resp:
                text = await resp.text()
                return "WhatsApp" in text and "invalid" not in text.lower()
    except Exception:
        return False


async def check_telegram(phone: str) -> bool:
    """Basic Telegram phone check via t.me."""
    return False  # Requires Telegram API auth


@ban_checker_middleware
@rate_limit_middleware
async def search_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /search\\_phone `<number>`\nExample: /search\\_phone +1234567890",
            parse_mode="Markdown"
        )
        return

    phone = context.args[0].strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    user = update.effective_user
    cached = get_cached("phone", phone)
    if cached:
        msg = format_phone_results(cached)
        await update.message.reply_text(f"📦 *Cached result:*\n\n{msg}", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text(
        f"📞 Looking up phone number `{phone}`...\n⏳ Please wait...",
        parse_mode="Markdown"
    )

    phoneinfoga_data, numverify_data, whatsapp = await asyncio.gather(
        run_phoneinfoga(phone),
        lookup_numverify(phone),
        check_whatsapp(phone),
        return_exceptions=True
    )

    info = {}
    if isinstance(numverify_data, dict) and numverify_data:
        info.update(numverify_data)
    if isinstance(phoneinfoga_data, dict) and phoneinfoga_data:
        for k in ["country", "carrier", "location"]:
            if phoneinfoga_data.get(k) and not info.get(k):
                info[k] = phoneinfoga_data[k]

    data = {
        "query": phone,
        "info": info,
        "social": {
            "whatsapp": isinstance(whatsapp, bool) and whatsapp,
            "telegram": False
        }
    }
    set_cache("phone", phone, data)
    log_search(user.id, user.username, "phone", phone, f"Carrier: {info.get('carrier', 'Unknown')}")

    msg = format_phone_results(data)
    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
