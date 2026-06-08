# 🚀 دليل النشر على PythonAnywhere (مجاني 100%)

## الخطوة 1: إنشاء حساب

انتقل إلى https://www.pythonanywhere.com/registration/register/beginner
أنشئ حساباً مجانياً (Beginner) — لا تحتاج بطاقة ائتمانية.

---

## الخطوة 2: فتح Bash Console

- من لوحة التحكم → **Consoles** → **Bash** → **New console**

---

## الخطوة 3: استنساخ الكود من GitHub

```bash
git clone https://github.com/aialskrani-oss/osint-telegram-bot.git
cd osint-telegram-bot
```

---

## الخطوة 4: تثبيت المكتبات

```bash
pip3.10 install -r requirements-pythonanywhere.txt --user
```

انتظر حتى يكتمل التثبيت (~2-3 دقائق).

---

## الخطوة 5: إعداد Web App

1. من لوحة التحكم → **Web** → **Add a new web app**
2. اختر: **Manual configuration**
3. اختر: **Python 3.10**
4. انقر **Next** حتى تصل إلى صفحة الإعدادات

---

## الخطوة 6: تعديل WSGI Config

في صفحة Web App، انقر على رابط **WSGI configuration file**
(يشبه: `/var/www/username_pythonanywhere_com_wsgi.py`)

**احذف كل المحتوى** واستبدله بما يلي:

```python
import sys
import os

project_home = '/home/YOUR_USERNAME/osint-telegram-bot'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['TELEGRAM_BOT_TOKEN'] = '8853331928:AAHvyA3cq722aAJpK6-q6Ei_x7-L6CclChc'
os.environ['WEBHOOK_SECRET'] = 'osint_secure_path'
os.environ['DB_PATH'] = f'{project_home}/osint_bot.db'

from bot_webhook import flask_app as application
```

> ⚠️ استبدل `YOUR_USERNAME` باسم مستخدمك على PythonAnywhere

احفظ الملف.

---

## الخطوة 7: تفعيل Web App

ارجع لصفحة **Web** وانقر **Reload** (الزر الأخضر).

---

## الخطوة 8: تسجيل Webhook مع Telegram

افتح هذا الرابط في المتصفح:
```
https://YOUR_USERNAME.pythonanywhere.com/set_webhook
```

يجب أن تظهر رسالة مثل:
```json
{
  "status": "ok",
  "webhook_url": "https://YOUR_USERNAME.pythonanywhere.com/webhook/osint_secure_path",
  "pending_update_count": 0
}
```

---

## ✅ الاختبار

افتح البوت على Telegram وأرسل:
```
/start
```

إذا رد، فالبوت يعمل بنجاح! 🎉

---

## 🔄 التحديثات المستقبلية

عند تحديث الكود:
```bash
# في Bash Console على PythonAnywhere
cd osint-telegram-bot
git pull origin main
```
ثم انقر **Reload** في صفحة Web App.

---

## ❓ مشاكل شائعة

| المشكلة | الحل |
|---------|------|
| Bot لا يرد | تأكد من تسجيل Webhook عبر /set_webhook |
| Import Error | أعد تشغيل `pip3.10 install -r requirements-pythonanywhere.txt --user` |
| 500 Error | تحقق من Error log في صفحة Web App |
| الـ DB لا يحفظ | تأكد من أن `DB_PATH` يشير لمجلد صحيح |
