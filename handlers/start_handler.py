"""Start and help handlers — Arabic/English bilingual."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DISCLAIMER = (
    "⚠️ *تحذير قانوني وأخلاقي*\n\n"
    "• هذا البوت يبحث في *البيانات المتاحة للعموم فقط*\n"
    "• لا تستخدمه لمضايقة أو تتبع أي شخص\n"
    "• جميع عمليات البحث مسجّلة لمنع الإساءة\n"
    "• المخالفون سيتم حظرهم نهائياً\n\n"
    "_باستخدامك لهذا البوت فأنت توافق على هذه الشروط_"
)

HELP_TEXT = """
🔍 *بوت OSINT — دليل الأوامر*

━━━━━━━━ *أوامر البحث* ━━━━━━━━
/search\_username `<اليوزرنيم>` — بحث في 50+ موقع
/search\_email `<الإيميل>` — حسابات مرتبطة وتسريبات
/search\_phone `<الرقم>` — معلومات المشغل والموقع
/search\_name `<الاسم الأول> <الأخير>` — بحث بالاسم الحقيقي
/search\_social `<المنصة> <المعرّف>` — بحث في منصة محددة
/search\_location `<البلد>` — أدوات OSINT حسب البلد
/advanced\_search — بحث متقدم بعدة معايير

━━━━━━━━ *أوامر التقارير* ━━━━━━━━
/report `txt` — تصدير التاريخ نصياً
/report `html` — تصدير بصيغة HTML
/report `pdf` — تصدير بصيغة PDF

━━━━━━━━ *أوامر عامة* ━━━━━━━━
/status — حالة البوت والإحصائيات
/cancel — إلغاء البحث الجاري
/help — عرض هذه القائمة

━━━━━━━━ *المنصات المدعومة* ━━━━━━━━
`github` `reddit` `instagram` `twitter`
`facebook` `telegram` `tiktok` `linkedin`

⚡ *حد الاستخدام:* 5 بحث/دقيقة لكل مستخدم
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📖 دليل الأوامر", callback_data="help"),
         InlineKeyboardButton("📊 الإحصائيات", callback_data="status")],
        [InlineKeyboardButton("🔍 بحث باليوزرنيم", switch_inline_query_current_chat="")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"👋 مرحباً *{user.first_name}*!\n\n"
        "🔍 أنا *بوت OSINT* متخصص في البحث عن المعلومات المتاحة للعموم "
        "عبر آلاف المواقع والمصادر المفتوحة.\n\n"
        f"{DISCLAIMER}\n\n"
        "اضغط على /help لعرض جميع الأوامر المتاحة."
    )
    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT, parse_mode="Markdown", disable_web_page_preview=True
    )
