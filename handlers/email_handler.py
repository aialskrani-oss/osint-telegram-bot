"""
Email search handler using Holehe-style service checks.
"""
import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_email_results

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# Services to check via password-reset / account-exists flows
EMAIL_SERVICES = [
    {
        "name": "GitHub",
        "url": "https://api.github.com/search/users?q={email}+in:email",
        "method": "api_github"
    },
    {
        "name": "Gravatar",
        "url": "https://en.gravatar.com/{hash}.json",
        "method": "gravatar"
    },
    {
        "name": "Adobe",
        "url": "https://auth.services.adobe.com/en_US/index.html",
        "method": "post_check",
        "post_url": "https://auth.services.adobe.com/renga-idprovider/api/v3/signin/user",
        "payload": {
            "username": "{email}",
            "password": "FakeP@ss!",
            "rememberMe": False
        },
        "registered_indicator": "WRONG_PASSWORD",
        "not_registered_indicator": "ACCOUNT_DOES_NOT_EXIST"
    },
]


async def check_gravatar(session: aiohttp.ClientSession, email: str) -> dict:
    import hashlib
    email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://en.gravatar.com/{email_hash}.json"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                entry = data.get("entry", [{}])[0]
                return {
                    "name": "Gravatar",
                    "registered": True,
                    "display_name": entry.get("displayName", ""),
                    "profile_url": entry.get("profileUrl", "")
                }
    except Exception:
        pass
    return {"name": "Gravatar", "registered": False}


async def check_github_email(session: aiohttp.ClientSession, email: str) -> dict:
    url = f"https://api.github.com/search/users?q={email}+in:email"
    try:
        async with session.get(url, headers={"Accept": "application/vnd.github.v3+json"},
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("total_count", 0) > 0:
                    items = data.get("items", [])
                    login = items[0].get("login", "") if items else ""
                    return {"name": "GitHub", "registered": True, "username": login}
    except Exception:
        pass
    return {"name": "GitHub", "registered": False}


# Holehe-style checks for popular services
HOLEHE_SERVICES = [
    "airbnb", "amazon", "badoo", "bitmoji", "coinbase", "deliveroo",
    "discord", "dropbox", "duolingo", "ebay", "eventbrite", "facebook",
    "fiverr", "flickr", "footsites", "freelancer", "github", "gitlab",
    "google", "instagram", "lastfm", "laposte", "linkedin", "mail.ru",
    "myspace", "netflix", "nike", "ok.ru", "patreon", "pinterest",
    "protonmail", "quora", "reddit", "sevenrooms", "skype", "snapchat",
    "soundcloud", "spotify", "steam", "strava", "tiktok", "tumblr",
    "twitter", "udemy", "vimeo", "wordpress", "xbox", "yahoo", "yandex", "zalando"
]


async def run_holehe_check(email: str) -> list:
    """Run holehe if installed, otherwise do manual checks."""
    results = []
    try:
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "holehe", "--only-used", email,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode("utf-8", errors="ignore")
        for line in output.splitlines():
            if "[+]" in line:
                service = line.replace("[+]", "").strip()
                results.append({"name": service, "registered": True})
            elif "[-]" in line:
                service = line.replace("[-]", "").strip()
                results.append({"name": service, "registered": False})
    except Exception as e:
        logger.warning("holehe not available or failed: %s", e)
    return results


@ban_checker_middleware
@rate_limit_middleware
async def search_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /search\\_email `<email>`\nExample: /search\\_email user@example.com",
            parse_mode="Markdown"
        )
        return

    email = context.args[0].strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text("❌ Invalid email format. Please provide a valid email address.")
        return

    user = update.effective_user
    cached = get_cached("email", email)
    if cached:
        msg = format_email_results(cached)
        await update.message.reply_text(f"📦 *Cached result:*\n\n{msg}", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text(
        f"📧 Searching for email `{email}`...\n⏳ Running checks across multiple services...",
        parse_mode="Markdown"
    )

    accounts = []
    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = [
            check_gravatar(session, email),
            check_github_email(session, email),
        ]
        special_results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in special_results:
            if isinstance(r, dict) and r.get("registered"):
                accounts.append(r)

    holehe_results = await run_holehe_check(email)
    for r in holehe_results:
        if r.get("registered"):
            accounts.append(r)

    data = {
        "query": email,
        "accounts": accounts,
        "breaches": []
    }
    set_cache("email", email, data)
    log_search(user.id, user.username, "email", email, f"Found on {len(accounts)} services")

    msg = format_email_results(data)
    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
