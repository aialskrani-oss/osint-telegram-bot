"""
Formatting utilities for bot responses.
"""
from typing import Any


def truncate(text: str, max_len: int = 4000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def format_username_results(data: dict) -> str:
    lines = ["🔍 *Username Search Results*", ""]
    query = data.get("query", "")
    found = data.get("found", [])
    not_found = data.get("not_found", [])
    errors = data.get("errors", [])

    lines.append(f"👤 Username: `{query}`")
    lines.append(f"✅ Found on {len(found)} sites | ❌ Not found on {len(not_found)} | ⚠️ Errors: {len(errors)}")
    lines.append("")

    if found:
        lines.append("*Found Profiles:*")
        for item in found[:30]:
            site = item.get("site", "Unknown")
            url = item.get("url", "")
            lines.append(f"• [{site}]({url})")
        if len(found) > 30:
            lines.append(f"_...and {len(found) - 30} more sites_")

    return truncate("\n".join(lines))


def format_email_results(data: dict) -> str:
    lines = ["📧 *Email Search Results*", ""]
    query = data.get("query", "")
    accounts = data.get("accounts", [])
    breaches = data.get("breaches", [])

    lines.append(f"Email: `{query}`")
    lines.append("")

    if accounts:
        lines.append(f"*Registered on {len(accounts)} services:*")
        for acc in accounts:
            name = acc.get("name", "Unknown")
            registered = acc.get("registered", False)
            status = "✅" if registered else "❌"
            lines.append(f"{status} {name}")
        lines.append("")

    if breaches:
        lines.append(f"⚠️ *Found in {len(breaches)} data breach(es):*")
        for b in breaches[:10]:
            lines.append(f"• {b}")

    if not accounts and not breaches:
        lines.append("No accounts or breaches found for this email.")

    return truncate("\n".join(lines))


def format_phone_results(data: dict) -> str:
    lines = ["📞 *Phone Number Search Results*", ""]
    query = data.get("query", "")
    info = data.get("info", {})
    
    lines.append(f"Number: `{query}`")
    lines.append("")

    if info:
        if info.get("valid"):
            lines.append(f"✅ Valid number")
        if info.get("country"):
            lines.append(f"🌍 Country: {info['country']}")
        if info.get("carrier"):
            lines.append(f"📡 Carrier: {info['carrier']}")
        if info.get("line_type"):
            lines.append(f"📱 Type: {info['line_type']}")
        if info.get("timezone"):
            lines.append(f"🕐 Timezone: {info['timezone']}")
        if info.get("location"):
            lines.append(f"📍 Region: {info['location']}")

    social = data.get("social", {})
    if social:
        lines.append("")
        lines.append("*Social Media:*")
        if social.get("whatsapp"):
            lines.append("✅ WhatsApp account found")
        if social.get("telegram"):
            lines.append("✅ Telegram account found")

    return truncate("\n".join(lines))


def format_name_results(data: dict) -> str:
    lines = ["👤 *Name Search Results*", ""]
    query = data.get("query", "")
    results = data.get("results", [])

    lines.append(f"Name: `{query}`")
    lines.append(f"Found {len(results)} potential profiles")
    lines.append("")

    for i, r in enumerate(results[:15], 1):
        lines.append(f"*{i}. {r.get('name', 'Unknown')}*")
        if r.get("location"):
            lines.append(f"   📍 {r['location']}")
        if r.get("age"):
            lines.append(f"   🎂 Age: {r['age']}")
        if r.get("url"):
            lines.append(f"   🔗 [Profile]({r['url']})")
        lines.append("")

    return truncate("\n".join(lines))


def format_social_results(data: dict) -> str:
    lines = ["🌐 *Social Media Search Results*", ""]
    platform = data.get("platform", "")
    query = data.get("query", "")
    profile = data.get("profile", {})
    posts = data.get("posts", [])

    lines.append(f"Platform: *{platform.title()}*")
    lines.append(f"Identifier: `{query}`")
    lines.append("")

    if profile:
        lines.append("*Profile Information:*")
        for key, val in profile.items():
            if val:
                label = key.replace("_", " ").title()
                lines.append(f"• {label}: {val}")
        lines.append("")

    if posts:
        lines.append(f"*Recent Activity ({len(posts)} items):*")
        for p in posts[:5]:
            lines.append(f"• {str(p)[:100]}")

    return truncate("\n".join(lines))


def format_location_results(data: dict) -> str:
    lines = ["🗺️ *Location-Based Search Results*", ""]
    location = data.get("location", "")
    sites = data.get("sites", [])

    lines.append(f"Location: `{location}`")
    lines.append(f"Found {len(sites)} region-specific results")
    lines.append("")

    for s in sites[:20]:
        name = s.get("name", "Unknown")
        url = s.get("url", "")
        desc = s.get("description", "")
        lines.append(f"• [{name}]({url})")
        if desc:
            lines.append(f"  _{desc}_")

    return truncate("\n".join(lines))
