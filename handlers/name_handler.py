"""
Real name search handler.
"""
import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_name_results

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


async def search_pipl_style(session: aiohttp.ClientSession, first: str, last: str) -> list:
    """Search via public name search engines."""
    results = []
    search_engines = [
        f"https://www.google.com/search?q=%22{first}+{last}%22+site:linkedin.com",
        f"https://www.google.com/search?q=%22{first}+{last}%22+profile",
    ]
    for url in search_engines:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Basic extraction of visible URLs
                    import re
                    urls = re.findall(r'href="(https?://[^"]+)"', text)
                    for u in urls[:5]:
                        if "google" not in u and "youtube" not in u:
                            results.append({"name": f"{first} {last}", "url": u, "location": "", "age": ""})
        except Exception as e:
            logger.debug("Name search engine error: %s", e)
    return results[:10]


async def search_social_profiles(session: aiohttp.ClientSession, first: str, last: str) -> list:
    """Search social platforms for real name profiles."""
    results = []
    platforms = [
        {
            "name": "LinkedIn",
            "url": f"https://www.linkedin.com/pub/dir/{first}/{last}/",
        },
        {
            "name": "Facebook",
            "url": f"https://www.facebook.com/search/people/?q={first}%20{last}",
        },
    ]
    for p in platforms:
        results.append({
            "name": f"{first} {last}",
            "url": p["url"],
            "location": "",
            "age": "",
            "platform": p["name"]
        })
    return results


@ban_checker_middleware
@rate_limit_middleware
async def search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /search\\_name `<first name> <last name>`\n"
            "Example: /search\\_name John Doe",
            parse_mode="Markdown"
        )
        return

    first = context.args[0].strip()
    last = " ".join(context.args[1:]).strip()
    full_name = f"{first} {last}"
    user = update.effective_user

    cached = get_cached("name", full_name)
    if cached:
        msg = format_name_results(cached)
        await update.message.reply_text(f"📦 *Cached result:*\n\n{msg}", parse_mode="Markdown",
                                        disable_web_page_preview=True)
        return

    status_msg = await update.message.reply_text(
        f"👤 Searching for *{full_name}*...\n⏳ Scanning public sources...",
        parse_mode="Markdown"
    )

    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        pipl_results, social_results = await asyncio.gather(
            search_pipl_style(session, first, last),
            search_social_profiles(session, first, last),
            return_exceptions=True
        )

    all_results = []
    if isinstance(pipl_results, list):
        all_results.extend(pipl_results)
    if isinstance(social_results, list):
        all_results.extend(social_results)

    data = {"query": full_name, "results": all_results}
    set_cache("name", full_name, data)
    log_search(user.id, user.username, "name", full_name, f"Found {len(all_results)} profiles")

    msg = format_name_results(data)
    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
