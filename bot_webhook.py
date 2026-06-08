"""
OSINT Telegram Bot — Webhook mode (for PythonAnywhere free hosting).
PythonAnywhere serves this as a WSGI Flask app.
Telegram sends updates to: https://<username>.pythonanywhere.com/webhook/<TOKEN>
"""
import os
import logging
import asyncio
from flask import Flask, request, abort
from telegram import Update
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

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "osint_secure_path")

flask_app = Flask(__name__)
ptb_app: Application = None


def build_ptb_app() -> Application:
    app = Application.builder().token(TOKEN).updater(None).build()
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
    return app


def get_or_create_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@flask_app.before_request
def init_app():
    global ptb_app
    if ptb_app is None:
        init_db()
        ptb_app = build_ptb_app()
        loop = get_or_create_event_loop()
        loop.run_until_complete(ptb_app.initialize())
        logger.info("PTB app initialized")


@flask_app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.headers.get("Content-Type") != "application/json":
        abort(403)
    data = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    loop = get_or_create_event_loop()
    loop.run_until_complete(ptb_app.process_update(update))
    return "ok", 200


@flask_app.route("/", methods=["GET"])
def health():
    return "OSINT Bot is running ✅", 200


@flask_app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """
    Visit this URL once after deploying to register the webhook with Telegram.
    Example: https://yourusername.pythonanywhere.com/set_webhook
    """
    host = request.host_url.rstrip("/")
    webhook_url = f"{host}/webhook/{WEBHOOK_SECRET}"
    loop = get_or_create_event_loop()

    async def _set():
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "inline_query", "callback_query"]
        )
        info = await ptb_app.bot.get_webhook_info()
        return info

    info = loop.run_until_complete(_set())
    return {
        "status": "ok",
        "webhook_url": webhook_url,
        "pending_update_count": info.pending_update_count,
        "last_error": str(info.last_error_message) if info.last_error_message else None
    }, 200


@flask_app.route("/delete_webhook", methods=["GET"])
def delete_webhook():
    loop = get_or_create_event_loop()
    loop.run_until_complete(ptb_app.bot.delete_webhook())
    return {"status": "webhook deleted"}, 200


# WSGI entry point for PythonAnywhere
application = flask_app

if __name__ == "__main__":
    # Local dev: use polling instead
    import sys
    sys.path.insert(0, ".")
    init_db()
    from bot import main
    main()
