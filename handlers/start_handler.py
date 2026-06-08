"""
Start and help command handlers.
"""
from telegram import Update
from telegram.ext import ContextTypes

LEGAL_DISCLAIMER = """
⚠️ *Legal & Ethical Notice*

This bot is for *educational and research purposes only*.
It only searches publicly available data sources.

• Do NOT use this bot to harass, stalk, or harm anyone
• Do NOT use results for illegal purposes
• All searches are logged for abuse prevention
• Users violating these terms will be permanently banned

By using this bot, you agree to these terms.
"""

HELP_TEXT = """
🔍 *OSINT Bot - Command Reference*

*Search Commands:*
/search\\_username `<username>` — Search across 3000+ sites
/search\\_email `<email>` — Find linked accounts & breaches  
/search\\_phone `<number>` — Carrier info & social accounts
/search\\_name `<first> <last>` — Search by real name
/search\\_social `<platform> <id>` — Search specific platform
/search\\_location `<country/region>` — Region-specific results
/advanced\\_search — Multi-criteria search mode

*Report Commands:*
/report `txt` — Export last results as text
/report `html` — Export last results as HTML
/report `pdf` — Export last results as PDF

*Platforms for search\\_social:*
`facebook`, `instagram`, `telegram`, `twitter`, `linkedin`

*Examples:*
`/search_username johndoe`
`/search_email user@example.com`
`/search_phone +1234567890`
`/search_name John Doe`
`/search_social instagram johndoe`
`/search_location Germany`

*Rate Limit:* 5 searches per minute per user
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Welcome, *{user.first_name}*!\n\n"
        "I'm an advanced *OSINT Bot* — I can search for publicly available "
        "information across thousands of sources.\n\n"
        f"{LEGAL_DISCLAIMER}\n\n"
        "Use /help to see all available commands."
    )
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
