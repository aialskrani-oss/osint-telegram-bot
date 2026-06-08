"""
OSINT Telegram Bot — Main entry point (polling mode for Replit).
For Render deployment use bot_webhook.py instead.
"""
import logging
import os
from telegram.ext import (
    Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler
)
from handlers.username_handler import search_username
from handlers.email_handler import search_email
from handlers.phone_handler import search_phone
from handlers.name_handler import search_name
from handlers.social_handler import search_social
from handlers.location_handler import search_location
from handlers.advanced_handler import advanced_search
from handlers.report_handler import generate_report
from handlers.inline_handler import inline_query
from handlers.admin_handler import ban_user, unban_user, list_banned
from handlers.start_handler import start, help_command
from handlers.status_handler import status_command
from handlers.cancel_handler import cancel_command
from database.db import init_db

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('osint_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN غير مضبوط في متغيرات البيئة")

    init_db()
    logger.info("✅ قاعدة البيانات جاهزة")

    app = Application.builder().token(token).build()

    # General commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Search commands
    app.add_handler(CommandHandler("search_username", search_username))
    app.add_handler(CommandHandler("search_email", search_email))
    app.add_handler(CommandHandler("search_phone", search_phone))
    app.add_handler(CommandHandler("search_name", search_name))
    app.add_handler(CommandHandler("search_social", search_social))
    app.add_handler(CommandHandler("search_location", search_location))
    app.add_handler(CommandHandler("advanced_search", advanced_search))

    # Report commands
    app.add_handler(CommandHandler("report", generate_report))

    # Admin commands
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("banned", list_banned))

    # Inline mode
    app.add_handler(InlineQueryHandler(inline_query))

    logger.info("🚀 بوت OSINT يعمل الآن...")
    app.run_polling(allowed_updates=["message", "inline_query", "callback_query"])


if __name__ == "__main__":
    main()
