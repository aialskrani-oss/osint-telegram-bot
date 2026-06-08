"""Cancel handler — stops any running search for the user."""
from telegram import Update
from telegram.ext import ContextTypes


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear any stored user data / conversation state
    context.user_data.clear()
    await update.message.reply_text(
        "✅ *تم الإلغاء*\n\n"
        "تم إلغاء العملية الجارية.\n"
        "يمكنك البدء ببحث جديد في أي وقت.",
        parse_mode="Markdown"
    )
