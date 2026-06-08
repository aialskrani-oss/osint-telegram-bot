"""
Location/Country-based OSINT resource search handler.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_cached, set_cache, log_search
from middleware.rate_limiter import rate_limit_middleware
from middleware.ban_checker import ban_checker_middleware
from utils.formatters import format_location_results

logger = logging.getLogger(__name__)

# Curated region-specific OSINT resources
LOCATION_RESOURCES = {
    "uk": [
        {"name": "Companies House", "url": "https://find-and-update.company-information.service.gov.uk/", "description": "UK company registrations"},
        {"name": "Electoral Roll Search", "url": "https://www.192.com/people/search/", "description": "UK electoral & address records"},
        {"name": "Land Registry", "url": "https://eservices.landregistry.gov.uk/eservices/FindAProperty/view/QuickEnquiryInit.do", "description": "UK property ownership"},
        {"name": "UK Court Records", "url": "https://www.find-court-tribunal.service.gov.uk/", "description": "Court records & tribunals"},
        {"name": "LinkedIn UK", "url": "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22101165590%22%5D", "description": "LinkedIn professionals in UK"},
    ],
    "germany": [
        {"name": "Handelsregister", "url": "https://www.handelsregister.de/", "description": "German commercial register"},
        {"name": "Bundesanzeiger", "url": "https://www.bundesanzeiger.de/", "description": "Federal Gazette"},
        {"name": "XING", "url": "https://www.xing.com/search/members", "description": "German professional network"},
        {"name": "German Phone Directory", "url": "https://www.dasoertliche.de/", "description": "German phonebook"},
    ],
    "usa": [
        {"name": "Whitepages", "url": "https://www.whitepages.com/", "description": "US people & address search"},
        {"name": "Spokeo", "url": "https://www.spokeo.com/", "description": "US people search engine"},
        {"name": "ZabaSearch", "url": "https://www.zabasearch.com/", "description": "Free US people search"},
        {"name": "SEC EDGAR", "url": "https://www.sec.gov/cgi-bin/browse-edgar", "description": "US company filings"},
        {"name": "Voter Records", "url": "https://www.voterrecords.com/", "description": "US voter registration data"},
        {"name": "Intelius", "url": "https://www.intelius.com/", "description": "US background checks"},
        {"name": "BeenVerified", "url": "https://www.beenverified.com/", "description": "US background reports"},
        {"name": "PACER", "url": "https://pacer.uscourts.gov/", "description": "US federal court records"},
    ],
    "france": [
        {"name": "Infogreffe", "url": "https://www.infogreffe.fr/", "description": "French company register"},
        {"name": "Journal Officiel", "url": "https://www.journal-officiel.gouv.fr/", "description": "Official French gazette"},
        {"name": "PagesJaunes", "url": "https://www.pagesjaunes.fr/", "description": "French yellow pages"},
        {"name": "LinkedIn France", "url": "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22105015875%22%5D", "description": "LinkedIn France"},
    ],
    "russia": [
        {"name": "VK", "url": "https://vk.com/search?c[section]=people", "description": "VKontakte people search"},
        {"name": "OK.ru", "url": "https://ok.ru/search", "description": "Odnoklassniki search"},
        {"name": "Russian Company Registry", "url": "https://egrul.nalog.ru/", "description": "FTS company registry"},
        {"name": "Rosreestr", "url": "https://rosreestr.gov.ru/", "description": "Russian property registry"},
    ],
    "china": [
        {"name": "Weibo Search", "url": "https://s.weibo.com/user", "description": "Weibo user search"},
        {"name": "Chinese Company", "url": "https://www.tianyancha.com/", "description": "Chinese company data"},
        {"name": "CNKI", "url": "https://www.cnki.net/", "description": "Chinese academic papers"},
    ],
    "australia": [
        {"name": "ABN Lookup", "url": "https://www.abn.business.gov.au/", "description": "Australian business numbers"},
        {"name": "ASIC Connect", "url": "https://connectonline.asic.gov.au/", "description": "Australian company registry"},
        {"name": "White Pages AU", "url": "https://www.whitepages.com.au/", "description": "Australian phone directory"},
        {"name": "Australian Electoral", "url": "https://www.aec.gov.au/", "description": "Electoral Commission"},
    ],
    "canada": [
        {"name": "Canada 411", "url": "https://www.canada411.ca/", "description": "Canadian phone directory"},
        {"name": "Corporations Canada", "url": "https://www.ic.gc.ca/app/scr/cc/CorporationsCanada/fdrlCrpSrch.html", "description": "Federal corporations"},
        {"name": "SEDAR", "url": "https://www.sedar.com/", "description": "Canadian securities filings"},
    ],
    "global": [
        {"name": "PeekYou", "url": "https://www.peekyou.com/", "description": "Global people search"},
        {"name": "Pipl", "url": "https://pipl.com/", "description": "Professional people search"},
        {"name": "Spokeo Global", "url": "https://www.spokeo.com/", "description": "Global people data"},
        {"name": "FullContact", "url": "https://www.fullcontact.com/", "description": "Identity resolution API"},
        {"name": "Hunter.io", "url": "https://hunter.io/", "description": "Email finder by domain"},
        {"name": "HaveIBeenPwned", "url": "https://haveibeenpwned.com/", "description": "Data breach checker"},
        {"name": "Shodan", "url": "https://www.shodan.io/", "description": "Internet device search"},
        {"name": "Censys", "url": "https://censys.io/", "description": "Internet scan data"},
        {"name": "IntelX", "url": "https://intelx.io/", "description": "Dark web & data search"},
        {"name": "TruthFinder", "url": "https://www.truthfinder.com/", "description": "Background checks"},
    ]
}


def find_location_resources(location: str) -> list:
    location_lower = location.lower()
    results = []
    # Try exact match first
    for key, sites in LOCATION_RESOURCES.items():
        if key in location_lower or location_lower in key:
            results.extend(sites)
    # Always add global resources
    if not results:
        results = LOCATION_RESOURCES.get("global", [])
    else:
        results.extend(LOCATION_RESOURCES.get("global", [])[:5])
    return results


@ban_checker_middleware
@rate_limit_middleware
async def search_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        countries = ", ".join(k for k in LOCATION_RESOURCES.keys() if k != "global")
        await update.message.reply_text(
            "Usage: /search\\_location `<country/region>`\n\n"
            f"Known regions: {countries}\n\n"
            "Example: /search\\_location USA",
            parse_mode="Markdown"
        )
        return

    location = " ".join(context.args).strip()
    user = update.effective_user

    cached = get_cached("location", location)
    if cached:
        msg = format_location_results(cached)
        await update.message.reply_text(f"📦 *Cached result:*\n\n{msg}", parse_mode="Markdown",
                                        disable_web_page_preview=True)
        return

    sites = find_location_resources(location)
    data = {"location": location, "sites": sites}
    set_cache("location", location, data)
    log_search(user.id, user.username, "location", location, f"Found {len(sites)} resources")

    msg = format_location_results(data)
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
