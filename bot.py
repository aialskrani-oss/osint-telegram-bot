"""
OSINT Telegram Bot - Main Entry Point
"""
import logging
import os
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    InlineQueryHandler, filters, CallbackQueryHandler
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
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from database.db import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('osint_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    init_db()
    logger.info("Database initialized")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("search_username", search_username))
    app.add_handler(CommandHandler("search_email", search_email))
    app.add_handler(CommandHandler("search_phone", search_phone))
    app.add_handler(CommandHandler("search_name", search_name))
    app.add_handler(CommandHandler("search_social", search_social))
    app.add_handler(CommandHandler("search_location", search_location))
    app.add_handler(CommandHandler("advanced_search", advanced_search))
    app.add_handler(CommandHandler("report", generate_report))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("banned", list_banned))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(lambda u, c: None))

    logger.info("OSINT Bot started successfully")
    app.run_polling(allowed_updates=["message", "inline_query", "callback_query"])


if __name__ == "__main__":
    main()
