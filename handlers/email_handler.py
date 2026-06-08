"""Email search handler — Arabic UI."""
import asyncio
import hashlib
import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_email_results

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}


async def check_gravatar(session: aiohttp.ClientSession, email: str) -> dict:
    email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
    try:
        async with session.get(f"https://en.gravatar.com/{email_hash}.json",
                               timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                entry = data.get("entry", [{}])[0]
                return {"name": "Gravatar", "registered": True,
                        "display_name": entry.get("displayName", ""),
                        "profile_url": entry.get("profileUrl", "")}
    except Exception:
        pass
    return {"name": "Gravatar", "registered": False}


async def check_github_email(session: aiohttp.ClientSession, email: str) -> dict:
    try:
        async with session.get(
            f"https://api.github.com/search/users?q={email}+in:email",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("total_count", 0) > 0:
                    items = data.get("items", [])
                    login = items[0].get("login", "") if items else ""
                    return {"name": "GitHub", "registered": True, "username": login}
    except Exception:
        pass
    return {"name": "GitHub", "registered": False}


async def run_holehe(email: str) -> list:
    """Run holehe if installed."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "holehe", "--only-used", email,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        results = []
        for line in stdout.decode("utf-8", errors="ignore").splitlines():
            if "[+]" in line:
                results.append({"name": line.replace("[+]", "").strip(), "registered": True})
        return results
    except Exception as e:
        logger.debug("holehe unavailable: %s", e)
        return []


@ban_checker_middleware
@rate_limit_middleware
async def search_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ *الاستخدام الصحيح:*\n`/search_email <الإيميل>`\n\n"
            "*مثال:* `/search_email user@example.com`",
            parse_mode="Markdown"
        )
        return

    email = context.args[0].strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text("❌ صيغة الإيميل غير صحيحة. مثال: `user@example.com`",
                                        parse_mode="Markdown")
        return

    user = update.effective_user
    cached = get_cached("email", email)
    if cached:
        await update.message.reply_text(
            f"📦 *نتيجة محفوظة:*\n\n{format_email_results(cached)}",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text(
        f"📧 جاري البحث عن `{email}`...\n⏳ فحص عشرات الخدمات...",
        parse_mode="Markdown"
    )

    accounts = []
    try:
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
            results = await asyncio.gather(
                check_gravatar(session, email),
                check_github_email(session, email),
                return_exceptions=True
            )
        for r in results:
            if isinstance(r, dict) and r.get("registered"):
                accounts.append(r)
        holehe_results = await run_holehe(email)
        accounts.extend(holehe_results)
    except Exception as e:
        logger.error("Email search error: %s", e)

    data = {"query": email, "accounts": accounts, "breaches": []}
    set_cache("email", email, data)
    log_search(user.id, user.username, "email", email, f"موجود في {len(accounts)} خدمة")

    await status_msg.edit_text(format_email_results(data), parse_mode="Markdown",
                               disable_web_page_preview=True)
