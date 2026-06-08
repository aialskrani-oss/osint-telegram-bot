"""
OSINT Telegram Bot — Webhook mode
Works on Render (free web service) and PythonAnywhere.

After deployment, visit:
  https://<your-app>.onrender.com/set_webhook
to register the webhook with Telegram.
"""
import os
import logging
import asyncio
from flask import Flask, request, abort, jsonify
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, InlineQueryHandler
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
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "osint_secure_path_2025")

flask_app = Flask(__name__)
_ptb_app = None
_loop = None


def get_loop():
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def get_ptb_app():
    global _ptb_app
    if _ptb_app is None:
        init_db()
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
        loop = get_loop()
        loop.run_until_complete(app.initialize())
        _ptb_app = app
        logger.info("PTB app initialized with token ending ...%s", TOKEN[-6:])
    return _ptb_app


# Initialize on startup
with flask_app.app_context():
    try:
        get_ptb_app()
    except Exception as e:
        logger.error("Startup init failed: %s", e)


@flask_app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.content_type != "application/json":
        abort(415)
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, get_ptb_app().bot)
        get_loop().run_until_complete(get_ptb_app().process_update(update))
        return "ok", 200
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return "error", 500


@flask_app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "bot": "OSINT Telegram Bot",
        "webhook": f"/webhook/{WEBHOOK_SECRET}"
    })


@flask_app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """Visit this URL once after deploying to activate the bot."""
    scheme = request.headers.get("X-Forwarded-Proto", "https")
    host = request.host
    webhook_url = f"{scheme}://{host}/webhook/{WEBHOOK_SECRET}"
    try:
        loop = get_loop()
        app = get_ptb_app()

        async def _set():
            await app.bot.delete_webhook()
            await app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "inline_query", "callback_query"]
            )
            return await app.bot.get_webhook_info()

        info = loop.run_until_complete(_set())
        return jsonify({
            "status": "✅ Webhook registered!",
            "webhook_url": webhook_url,
            "pending_updates": info.pending_update_count,
            "last_error": str(info.last_error_message) if info.last_error_message else None
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@flask_app.route("/delete_webhook", methods=["GET"])
def delete_webhook():
    try:
        get_loop().run_until_complete(get_ptb_app().bot.delete_webhook())
        return jsonify({"status": "Webhook deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Gunicorn / PythonAnywhere WSGI entry point
application = flask_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)
