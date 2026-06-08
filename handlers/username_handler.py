"""
Username search handler using Maigret / Sherlock-style search.
"""
import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_username_results

logger = logging.getLogger(__name__)

# Top 50 most popular sites for username checking (no API key required)
SITES = [
    {"name": "GitHub", "url": "https://github.com/{}", "check": "Not Found"},
    {"name": "Twitter/X", "url": "https://twitter.com/{}", "check": "This account doesn't exist"},
    {"name": "Instagram", "url": "https://www.instagram.com/{}/", "check": "Sorry, this page"},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "check": "page not found"},
    {"name": "TikTok", "url": "https://www.tiktok.com/@{}", "check": "Couldn't find this account"},
    {"name": "YouTube", "url": "https://www.youtube.com/@{}", "check": ""},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}/", "check": "The page you were looking for"},
    {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}", "check": ""},
    {"name": "Twitch", "url": "https://www.twitch.tv/{}", "check": ""},
    {"name": "Steam", "url": "https://steamcommunity.com/id/{}", "check": "The specified profile could not be found"},
    {"name": "Patreon", "url": "https://www.patreon.com/{}", "check": ""},
    {"name": "Flickr", "url": "https://www.flickr.com/people/{}", "check": "Page Not Found"},
    {"name": "Vimeo", "url": "https://vimeo.com/{}", "check": ""},
    {"name": "Soundcloud", "url": "https://soundcloud.com/{}", "check": ""},
    {"name": "Spotify", "url": "https://open.spotify.com/user/{}", "check": ""},
    {"name": "Behance", "url": "https://www.behance.net/{}", "check": ""},
    {"name": "Dribbble", "url": "https://dribbble.com/{}", "check": ""},
    {"name": "DeviantArt", "url": "https://www.deviantart.com/{}", "check": ""},
    {"name": "Medium", "url": "https://medium.com/@{}", "check": ""},
    {"name": "Quora", "url": "https://www.quora.com/profile/{}", "check": ""},
    {"name": "Hackerrank", "url": "https://www.hackerrank.com/{}", "check": ""},
    {"name": "Keybase", "url": "https://keybase.io/{}", "check": ""},
    {"name": "Gitlab", "url": "https://gitlab.com/{}", "check": "404"},
    {"name": "Bitbucket", "url": "https://bitbucket.org/{}", "check": ""},
    {"name": "npm", "url": "https://www.npmjs.com/~{}", "check": ""},
    {"name": "PyPI", "url": "https://pypi.org/user/{}/", "check": "404"},
    {"name": "DockerHub", "url": "https://hub.docker.com/u/{}", "check": ""},
    {"name": "Gravatar", "url": "https://en.gravatar.com/{}", "check": ""},
    {"name": "Replit", "url": "https://replit.com/@{}", "check": ""},
    {"name": "HackerNews", "url": "https://news.ycombinator.com/user?id={}", "check": "No such user"},
    {"name": "ProductHunt", "url": "https://www.producthunt.com/@{}", "check": ""},
    {"name": "AngelList", "url": "https://angel.co/{}", "check": ""},
    {"name": "Mastodon", "url": "https://mastodon.social/@{}", "check": ""},
    {"name": "Substack", "url": "https://{}.substack.com", "check": ""},
    {"name": "Ko-fi", "url": "https://ko-fi.com/{}", "check": ""},
    {"name": "BuyMeACoffee", "url": "https://buymeacoffee.com/{}", "check": ""},
    {"name": "Letterboxd", "url": "https://letterboxd.com/{}", "check": ""},
    {"name": "Goodreads", "url": "https://www.goodreads.com/{}", "check": ""},
    {"name": "About.me", "url": "https://about.me/{}", "check": ""},
    {"name": "Last.fm", "url": "https://www.last.fm/user/{}", "check": "Page not found"},
    {"name": "MySpace", "url": "https://myspace.com/{}", "check": ""},
    {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}", "check": ""},
    {"name": "Telegram", "url": "https://t.me/{}", "check": ""},
    {"name": "Discord", "url": "https://discord.com/users/{}", "check": ""},
    {"name": "Xbox", "url": "https://www.xbox.com/en-US/play/user/{}", "check": ""},
    {"name": "PSN", "url": "https://psnprofiles.com/{}", "check": ""},
    {"name": "Roblox", "url": "https://www.roblox.com/user.aspx?username={}", "check": ""},
    {"name": "Minecraft", "url": "https://namemc.com/profile/{}", "check": ""},
    {"name": "Fiverr", "url": "https://www.fiverr.com/{}", "check": ""},
    {"name": "Upwork", "url": "https://www.upwork.com/freelancers/~{}", "check": ""},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


async def check_site(session: aiohttp.ClientSession, site: dict, username: str) -> dict:
    url = site["url"].format(username)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
            if resp.status == 200:
                if site["check"]:
                    text = await resp.text()
                    if site["check"].lower() in text.lower():
                        return {"site": site["name"], "url": url, "found": False}
                return {"site": site["name"], "url": url, "found": True}
            elif resp.status == 404:
                return {"site": site["name"], "url": url, "found": False}
            else:
                return {"site": site["name"], "url": url, "found": False}
    except Exception as e:
        return {"site": site["name"], "url": url, "found": False, "error": str(e)}


@ban_checker_middleware
@rate_limit_middleware
async def search_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /search\\_username `<username>`\nExample: /search\\_username johndoe",
            parse_mode="Markdown"
        )
        return

    username = context.args[0].strip().lstrip("@")
    user = update.effective_user

    cached = get_cached("username", username)
    if cached:
        msg = format_username_results(cached)
        await update.message.reply_text(
            f"📦 *Cached result:*\n\n{msg}", parse_mode="Markdown",
            disable_web_page_preview=True
        )
        return

    status_msg = await update.message.reply_text(
        f"🔍 Searching for username `{username}` across {len(SITES)} sites...\n"
        "⏳ This may take up to 30 seconds.",
        parse_mode="Markdown"
    )

    found = []
    not_found = []
    errors = []

    connector = aiohttp.TCPConnector(limit=20, ssl=False)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = [check_site(session, site, username) for site in SITES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            errors.append(str(r))
        elif r.get("found"):
            found.append(r)
        elif r.get("error"):
            errors.append(r["error"])
        else:
            not_found.append(r)

    data = {
        "query": username,
        "found": found,
        "not_found": not_found,
        "errors": errors
    }
    set_cache("username", username, data)
    log_search(user.id, user.username, "username", username, f"Found on {len(found)} sites")

    msg = format_username_results(data)
    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
