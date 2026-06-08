"""Formatting utilities — Arabic UI."""
from typing import Any


def truncate(text: str, max_len: int = 4000) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def format_username_results(data: dict) -> str:
    username = data.get("query", "")
    found = data.get("found", [])
    not_found = data.get("not_found", [])

    lines = [
        "👤 *نتائج البحث باليوزرنيم*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🔎 اليوزرنيم: `{username}`",
        f"✅ موجود في: *{len(found)}* موقع",
        f"❌ غير موجود في: *{len(not_found)}* موقع",
        ""
    ]
    if found:
        lines.append("*📋 المواقع التي وُجد فيها:*")
        for item in found[:30]:
            lines.append(f"  ✅ [{item['site']}]({item['url']})")
        if len(found) > 30:
            lines.append(f"  _... و{len(found) - 30} مواقع أخرى_")
    else:
        lines.append("_لم يُعثر على هذا اليوزرنيم في أي موقع_")
    return truncate("\n".join(lines))


def format_email_results(data: dict) -> str:
    email = data.get("query", "")
    accounts = data.get("accounts", [])
    breaches = data.get("breaches", [])

    registered = [a for a in accounts if a.get("registered")]
    lines = [
        "📧 *نتائج البحث بالإيميل*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📨 الإيميل: `{email}`",
        f"✅ مسجّل في: *{len(registered)}* خدمة",
        ""
    ]
    if registered:
        lines.append("*📋 الخدمات المرتبطة:*")
        for acc in registered:
            name = acc.get("name", "")
            extra = ""
            if acc.get("username"):
                extra = f" — @{acc['username']}"
            if acc.get("display_name"):
                extra = f" — {acc['display_name']}"
            lines.append(f"  ✅ {name}{extra}")
    if breaches:
        lines.append(f"\n⚠️ *تسريبات بيانات ({len(breaches)}):*")
        for b in breaches[:10]:
            lines.append(f"  🔴 {b}")
    if not registered and not breaches:
        lines.append("_لم يُعثر على حسابات أو تسريبات مرتبطة بهذا الإيميل_")
    return truncate("\n".join(lines))


def format_phone_results(data: dict) -> str:
    phone = data.get("query", "")
    info = data.get("info", {})
    social = data.get("social", {})

    lines = [
        "📞 *نتائج البحث برقم الهاتف*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📱 الرقم: `{phone}`",
        ""
    ]
    if info:
        if info.get("valid"):
            lines.append("✅ رقم صالح ومفعّل")
        if info.get("country"):
            lines.append(f"🌍 *الدولة:* {info['country']}")
        if info.get("carrier"):
            lines.append(f"📡 *المشغّل:* {info['carrier']}")
        if info.get("line_type"):
            lines.append(f"📱 *النوع:* {info['line_type']}")
        if info.get("location"):
            lines.append(f"📍 *المنطقة:* {info['location']}")
        if info.get("timezone"):
            lines.append(f"🕐 *المنطقة الزمنية:* {info['timezone']}")
    if social:
        lines.append("\n*🌐 منصات التواصل:*")
        lines.append(f"  {'✅' if social.get('whatsapp') else '❌'} واتساب")
        lines.append(f"  {'✅' if social.get('telegram') else '❌'} تيلغرام")
    if not info and not social:
        lines.append("_لم يُعثر على معلومات لهذا الرقم_")
    return truncate("\n".join(lines))


def format_name_results(data: dict) -> str:
    name = data.get("query", "")
    results = data.get("results", [])

    lines = [
        "👤 *نتائج البحث بالاسم*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🔎 الاسم: `{name}`",
        f"📋 نتائج محتملة: *{len(results)}*",
        ""
    ]
    for i, r in enumerate(results[:15], 1):
        lines.append(f"*{i}.* {r.get('name', name)}")
        if r.get("location"):
            lines.append(f"   📍 {r['location']}")
        if r.get("platform"):
            lines.append(f"   🌐 {r['platform']}")
        if r.get("url"):
            lines.append(f"   🔗 [عرض الصفحة]({r['url']})")
        lines.append("")
    if not results:
        lines.append("_لم يُعثر على نتائج مطابقة_")
    return truncate("\n".join(lines))


def format_social_results(data: dict) -> str:
    platform = data.get("platform", "")
    query = data.get("query", "")
    profile = data.get("profile", {})

    platform_ar = {
        "github": "GitHub", "reddit": "Reddit", "instagram": "إنستغرام",
        "twitter": "تويتر/X", "facebook": "فيسبوك", "telegram": "تيلغرام",
        "tiktok": "تيك توك", "linkedin": "لينكدإن"
    }.get(platform, platform.title())

    lines = [
        f"🌐 *نتائج البحث في {platform_ar}*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🔎 المعرّف: `{query}`",
        ""
    ]
    if profile:
        if profile.get("status") == "found" or profile.get("name"):
            lines.append("✅ *الحساب موجود*\n")
            if profile.get("name"):
                lines.append(f"👤 *الاسم:* {profile['name']}")
            if profile.get("bio"):
                lines.append(f"📝 *النبذة:* {profile['bio'][:100]}")
            if profile.get("location"):
                lines.append(f"📍 *الموقع:* {profile['location']}")
            if profile.get("followers") is not None:
                lines.append(f"👥 *المتابعون:* {profile['followers']:,}")
            if profile.get("public_repos") is not None:
                lines.append(f"📦 *المستودعات:* {profile['public_repos']}")
            if profile.get("karma_post") is not None:
                lines.append(f"⬆️ *كارما المنشورات:* {profile['karma_post']:,}")
            if profile.get("profile_url"):
                lines.append(f"🔗 [عرض الصفحة]({profile['profile_url']})")
        else:
            lines.append("❌ *الحساب غير موجود أو خاص*")
    return truncate("\n".join(lines))


def format_location_results(data: dict) -> str:
    location = data.get("location", "")
    sites = data.get("sites", [])

    lines = [
        "🗺️ *أدوات OSINT حسب المنطقة*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📍 المنطقة: `{location}`",
        f"🔗 عدد الأدوات: *{len(sites)}*",
        ""
    ]
    for s in sites[:20]:
        name = s.get("name", "")
        url = s.get("url", "")
        desc = s.get("description", "")
        lines.append(f"• [{name}]({url})")
        if desc:
            lines.append(f"  _{desc}_")
    return truncate("\n".join(lines))
