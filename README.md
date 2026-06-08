# 🔍 بوت OSINT للتيلغرام

بوت تيلغرام احترافي متخصص في استخبارات المصادر المفتوحة (OSINT) — يبحث عن البيانات المتاحة للعموم عبر آلاف المواقع والمصادر.

<div dir="rtl">

## ⚠️ تحذير قانوني وأخلاقي

- هذا البوت **للأغراض التعليمية والبحثية فقط**
- يبحث في البيانات **المتاحة للعموم فقط**
- لا يُسمح باستخدامه لمضايقة أو تتبع الأشخاص
- المخالفون سيتم حظرهم نهائياً

## ✨ الميزات

| الميزة | التفاصيل |
|--------|----------|
| بحث باليوزرنيم | 50+ موقع يتم فحصها بالتوازي |
| بحث بالإيميل | Holehe + Gravatar + GitHub |
| بحث برقم الهاتف | PhoneInfoga + فحص واتساب |
| بحث بالاسم | اكتشاف الملفات الشخصية العامة |
| بحث في منصات | GitHub، Reddit، إنستغرام، تيك توك، إلخ |
| بحث حسب البلد | دليل أدوات OSINT لـ 8+ دول |
| بحث متقدم | عدة معايير دفعة واحدة |
| تقارير | PDF، HTML، TXT |
| إحصائيات | أمر /status يعرض كل شيء |
| وضع Inline | بحث سريع من أي محادثة |
| تحديد معدل | 5 بحث/دقيقة لكل مستخدم |
| نظام الحظر | أوامر إدارية لحظر المسيئين |
| تخزين مؤقت | SQLite لمدة 24 ساعة |

## 🤖 الأوامر المتاحة

```
/start                          — رسالة الترحيب
/help                           — دليل الأوامر
/status                         — حالة البوت والإحصائيات
/cancel                         — إلغاء البحث الجاري

/search_username <يوزرنيم>      — بحث في 50+ موقع
/search_email <إيميل>           — حسابات مرتبطة وتسريبات
/search_phone <رقم>             — معلومات المشغّل والموقع
/search_name <الاسم الأول> <الأخير>  — بحث بالاسم الحقيقي
/search_social <منصة> <معرّف>   — بحث في منصة محددة
/search_location <بلد>          — أدوات OSINT حسب البلد
/advanced_search -u <u> -e <e>  — بحث متقدم بعدة معايير

/report txt|html|pdf            — تصدير سجل البحث
/ban <معرّف> [سبب]              — (مشرف) حظر مستخدم
/unban <معرّف>                  — (مشرف) رفع حظر
/banned                         — (مشرف) قائمة المحظورين
```

</div>

---

## 🚀 النشر على Render (مجاني)

### المتطلبات
- حساب GitHub (لديك بالفعل)
- حساب Render: https://render.com

### الخطوات

1. **سجّل دخول إلى Render:** https://dashboard.render.com

2. **أنشئ Web Service جديداً:**
   - **New → Web Service**
   - اربط مستودع GitHub: `aialskrani-oss/osint-telegram-bot`

3. **إعدادات الخدمة:**
   ```
   Runtime:       Python 3
   Build Command: pip install -r requirements-core.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 bot_webhook:flask_app
   Plan:          Free
   ```

4. **متغيرات البيئة:**
   | المتغير | القيمة |
   |---------|--------|
   | `TELEGRAM_BOT_TOKEN` | توكن البوت من BotFather |
   | `WEBHOOK_SECRET` | `osint_secure_path_2025` |
   | `DB_PATH` | `/tmp/osint_bot.db` |

5. **بعد النشر — فعّل الـ Webhook (مرة واحدة):**
   ```
   https://YOUR-APP.onrender.com/set_webhook
   ```

---

## 💻 التشغيل المحلي

```bash
git clone https://github.com/aialskrani-oss/osint-telegram-bot.git
cd osint-telegram-bot

pip install -r requirements-core.txt

# أنشئ ملف .env
echo "TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE" > .env

python bot.py
```

---

## 📁 هيكل المشروع

```
osint-telegram-bot/
├── bot.py                    # نقطة الدخول — وضع Polling (Replit)
├── bot_webhook.py            # وضع Webhook (Render / PythonAnywhere)
├── requirements-core.txt     # المكتبات الأساسية
├── requirements.txt          # المكتبات الكاملة (تشمل Holehe/Maigret)
├── render.yaml               # إعدادات النشر على Render
├── runtime.txt               # إصدار Python
├── Procfile                  # أمر التشغيل
├── .env.example              # قالب متغيرات البيئة
├── handlers/                 # معالج لكل نوع بحث
│   ├── start_handler.py
│   ├── username_handler.py
│   ├── email_handler.py
│   ├── phone_handler.py
│   ├── name_handler.py
│   ├── social_handler.py
│   ├── location_handler.py
│   ├── advanced_handler.py
│   ├── report_handler.py
│   ├── inline_handler.py
│   ├── admin_handler.py
│   ├── status_handler.py
│   └── cancel_handler.py
├── middleware/
│   ├── rate_limiter.py       # 5 طلبات/دقيقة
│   └── ban_checker.py        # فحص الحظر
├── database/
│   └── db.py                 # SQLite — تخزين مؤقت، سجل، حظر
└── utils/
    └── formatters.py         # تنسيق الرسائل بالعربية
```

---

## 📄 الترخيص

MIT License — استخدم بمسؤولية.
