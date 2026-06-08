"""
Inline mode handler for quick searches.
"""
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
import uuid

logger = logging.getLogger(__name__)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔍 Username Search",
                description="Type: @username to search",
                input_message_content=InputTextMessageContent("/search_username ")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📧 Email Search",
                description="Type: email@domain.com",
                input_message_content=InputTextMessageContent("/search_email ")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📞 Phone Search",
                description="Type: +1234567890",
                input_message_content=InputTextMessageContent("/search_phone ")
            ),
        ]
        await update.inline_query.answer(results, cache_time=0)
        return

    # Detect query type from content
    if "@" in query and "." in query.split("@")[-1]:
        # Looks like email
        results = [InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"📧 Search email: {query}",
            description="Click to search this email address",
            input_message_content=InputTextMessageContent(f"/search_email {query}")
        )]
    elif query.startswith("+") or (query.replace("-", "").replace(" ", "").isdigit() and len(query) >= 7):
        # Looks like phone
        results = [InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"📞 Search phone: {query}",
            description="Click to search this phone number",
            input_message_content=InputTextMessageContent(f"/search_phone {query}")
        )]
    else:
        # Default: username search
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"👤 Search username: {query}",
                description="Search this username across 50+ sites",
                input_message_content=InputTextMessageContent(f"/search_username {query}")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"👤 Search name: {query}",
                description="Search this as a real name",
                input_message_content=InputTextMessageContent(f"/search_name {query}")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"🗺️ Search location: {query}",
                description="Get OSINT resources for this country/region",
                input_message_content=InputTextMessageContent(f"/search_location {query}")
            ),
        ]

    await update.inline_query.answer(results, cache_time=10)
