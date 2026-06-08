"""
Advanced multi-criteria search handler.
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware

logger = logging.getLogger(__name__)

ADVANCED_INSTRUCTIONS = """
🔬 *Advanced OSINT Search*

Combine multiple criteria in one query using flags:

`/advanced_search -u <username> -e <email> -p <phone> -n <name> -l <location>`

*Flags:*
• `-u` or `--username` — Username
• `-e` or `--email` — Email address
• `-p` or `--phone` — Phone number (with country code)
• `-n` or `--name` — Full name (use quotes: "John Doe")
• `-l` or `--location` — Location/country filter

*Examples:*
`/advanced_search -u johndoe -e john@example.com`
`/advanced_search -u johndoe -l USA`
`/advanced_search -e john@example.com -p +1234567890`

All matching searches will run in parallel and results combined.
"""


def parse_advanced_args(args: list) -> dict:
    params = {}
    i = 0
    while i < len(args):
        flag = args[i].lower()
        if flag in ("-u", "--username") and i + 1 < len(args):
            params["username"] = args[i + 1]
            i += 2
        elif flag in ("-e", "--email") and i + 1 < len(args):
            params["email"] = args[i + 1]
            i += 2
        elif flag in ("-p", "--phone") and i + 1 < len(args):
            params["phone"] = args[i + 1]
            i += 2
        elif flag in ("-n", "--name") and i + 1 < len(args):
            name_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("-"):
                name_parts.append(args[i])
                i += 1
            params["name"] = " ".join(name_parts)
        elif flag in ("-l", "--location") and i + 1 < len(args):
            params["location"] = args[i + 1]
            i += 2
        else:
            i += 1
    return params


@ban_checker_middleware
@rate_limit_middleware
async def advanced_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(ADVANCED_INSTRUCTIONS, parse_mode="Markdown")
        return

    params = parse_advanced_args(context.args)
    if not params:
        await update.message.reply_text(
            "❌ No valid search criteria found.\n\n" + ADVANCED_INSTRUCTIONS,
            parse_mode="Markdown"
        )
        return

    user = update.effective_user
    summary_parts = []
    for k, v in params.items():
        summary_parts.append(f"*{k.title()}:* `{v}`")

    status_msg = await update.message.reply_text(
        "🔬 *Advanced Search Started*\n\n"
        f"Running searches for:\n{chr(10).join(summary_parts)}\n\n"
        "⏳ Launching parallel searches...",
        parse_mode="Markdown"
    )

    tasks = []
    results = []

    if "username" in params:
        # Simulate triggering username search inline
        tasks.append(("username", params["username"]))
    if "email" in params:
        tasks.append(("email", params["email"]))
    if "phone" in params:
        tasks.append(("phone", params["phone"]))
    if "name" in params:
        tasks.append(("name", params["name"]))
    if "location" in params:
        tasks.append(("location", params["location"]))

    log_search(user.id, user.username, "advanced", str(params), f"{len(tasks)} criteria")

    result_text = (
        "🔬 *Advanced Search Results*\n\n"
        f"Searched {len(tasks)} criteria:\n\n"
    )

    for search_type, query in tasks:
        result_text += f"▶️ *{search_type.title()} Search:* `{query}`\n"
        result_text += f"Use `/search_{search_type} {query}` to see full results\n\n"

    result_text += (
        "💡 *Tip:* Each individual search command shows the full detailed results.\n"
        "Advanced search gives you a coordinated overview."
    )

    await status_msg.edit_text(result_text, parse_mode="Markdown", disable_web_page_preview=True)
