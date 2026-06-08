"""
Social media profile search handler.
"""
import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_social_results

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

SUPPORTED_PLATFORMS = {
    "instagram": "https://www.instagram.com/{}/",
    "twitter": "https://twitter.com/{}",
    "facebook": "https://www.facebook.com/{}",
    "telegram": "https://t.me/{}",
    "linkedin": "https://www.linkedin.com/in/{}",
    "tiktok": "https://www.tiktok.com/@{}",
    "github": "https://api.github.com/users/{}",
    "reddit": "https://www.reddit.com/user/{}/about.json",
    "youtube": "https://www.youtube.com/@{}",
    "twitch": "https://api.twitch.tv/helix/users?login={}",
}


async def fetch_github_profile(session: aiohttp.ClientSession, identifier: str) -> dict:
    url = f"https://api.github.com/users/{identifier}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "name": data.get("name", ""),
                    "bio": data.get("bio", ""),
                    "location": data.get("location", ""),
                    "public_repos": data.get("public_repos", 0),
                    "followers": data.get("followers", 0),
                    "following": data.get("following", 0),
                    "created_at": data.get("created_at", ""),
                    "profile_url": data.get("html_url", ""),
                    "avatar": data.get("avatar_url", ""),
                    "blog": data.get("blog", ""),
                    "company": data.get("company", ""),
                }
    except Exception as e:
        logger.debug("GitHub fetch error: %s", e)
    return {}


async def fetch_reddit_profile(session: aiohttp.ClientSession, identifier: str) -> dict:
    url = f"https://www.reddit.com/user/{identifier}/about.json"
    try:
        async with session.get(url, headers={"User-Agent": "OSINT-Bot/1.0"},
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                d = data.get("data", {})
                return {
                    "name": d.get("name", ""),
                    "karma_post": d.get("link_karma", 0),
                    "karma_comment": d.get("comment_karma", 0),
                    "is_verified": d.get("verified", False),
                    "has_premium": d.get("is_gold", False),
                    "account_age_days": d.get("created_utc", 0),
                    "profile_url": f"https://www.reddit.com/user/{identifier}",
                }
    except Exception as e:
        logger.debug("Reddit fetch error: %s", e)
    return {}


async def fetch_generic_profile(session: aiohttp.ClientSession, platform: str, identifier: str) -> dict:
    url_template = SUPPORTED_PLATFORMS.get(platform, "https://www.{}.com/{}")
    url = url_template.format(identifier)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10),
                               allow_redirects=True) as resp:
            exists = resp.status == 200
            return {
                "profile_url": url,
                "status": "found" if exists else "not_found",
                "http_status": resp.status,
            }
    except Exception as e:
        logger.debug("Generic fetch error for %s: %s", platform, e)
    return {"profile_url": url, "status": "error"}


@ban_checker_middleware
@rate_limit_middleware
async def search_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /search\\_social `<platform> <identifier>`\n\n"
            f"Supported platforms: {', '.join(SUPPORTED_PLATFORMS.keys())}\n\n"
            "Examples:\n"
            "`/search_social github torvalds`\n"
            "`/search_social reddit spez`\n"
            "`/search_social instagram natgeo`",
            parse_mode="Markdown"
        )
        return

    platform = context.args[0].strip().lower()
    identifier = context.args[1].strip().lstrip("@")
    user = update.effective_user

    if platform not in SUPPORTED_PLATFORMS:
        await update.message.reply_text(
            f"❌ Unsupported platform: `{platform}`\n"
            f"Supported: {', '.join(SUPPORTED_PLATFORMS.keys())}",
            parse_mode="Markdown"
        )
        return

    cache_key = f"{platform}:{identifier}"
    cached = get_cached("social", cache_key)
    if cached:
        msg = format_social_results(cached)
        await update.message.reply_text(f"📦 *Cached result:*\n\n{msg}", parse_mode="Markdown",
                                        disable_web_page_preview=True)
        return

    status_msg = await update.message.reply_text(
        f"🌐 Searching *{platform.title()}* for `{identifier}`...\n⏳ Please wait...",
        parse_mode="Markdown"
    )

    connector = aiohttp.TCPConnector(limit=5, ssl=False)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        if platform == "github":
            profile = await fetch_github_profile(session, identifier)
        elif platform == "reddit":
            profile = await fetch_reddit_profile(session, identifier)
        else:
            profile = await fetch_generic_profile(session, platform, identifier)

    data = {
        "platform": platform,
        "query": identifier,
        "profile": profile,
        "posts": []
    }
    set_cache("social", cache_key, data)
    log_search(user.id, user.username, "social", cache_key, f"Platform: {platform}")

    msg = format_social_results(data)
    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
