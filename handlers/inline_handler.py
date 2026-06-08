"""Inline query handler — Arabic UI."""
import uuid
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    if not query:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔍 بحث باليوزرنيم",
                description="اكتب اليوزرنيم للبحث عنه",
                input_message_content=InputTextMessageContent("/search_username ")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📧 بحث بالإيميل",
                description="اكتب الإيميل للبحث عنه",
                input_message_content=InputTextMessageContent("/search_email ")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📞 بحث برقم الهاتف",
                description="اكتب رقم الهاتف مع كود الدولة",
                input_message_content=InputTextMessageContent("/search_phone ")
            ),
        ]
        await update.inline_query.answer(results, cache_time=0)
        return

    if "@" in query and "." in query.split("@")[-1]:
        results = [InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"📧 بحث عن الإيميل: {query}",
            description="اضغط للبحث عن هذا الإيميل",
            input_message_content=InputTextMessageContent(f"/search_email {query}")
        )]
    elif query.startswith("+") or (query.replace(" ", "").replace("-", "").isdigit() and len(query) >= 7):
        results = [InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"📞 بحث عن الرقم: {query}",
            description="اضغط للبحث عن هذا الرقم",
            input_message_content=InputTextMessageContent(f"/search_phone {query}")
        )]
    else:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"👤 بحث باليوزرنيم: {query}",
                description="بحث في 50+ موقع",
                input_message_content=InputTextMessageContent(f"/search_username {query}")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"👤 بحث بالاسم: {query}",
                description="بحث كاسم حقيقي",
                input_message_content=InputTextMessageContent(f"/search_name {query}")
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"🗺️ أدوات OSINT لـ {query}",
                description="أدوات OSINT حسب المنطقة",
                input_message_content=InputTextMessageContent(f"/search_location {query}")
            ),
        ]

    await update.inline_query.answer(results, cache_time=10)
