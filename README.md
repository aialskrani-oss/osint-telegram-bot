# 🔍 OSINT Telegram Bot

A professional, fully-featured OSINT (Open Source Intelligence) Telegram bot that searches for publicly available information across thousands of sources. Supports 6 search types, report generation, rate limiting, and 24/7 deployment on Render.

---

## ⚠️ Legal & Ethical Notice

This bot is for **educational and research purposes only**.

- Only searches **publicly available** data sources
- Does **not** store sensitive data permanently
- Users can be banned for misuse
- Comply with the laws of your jurisdiction when using this tool

---

## ✨ Features

| Feature | Details |
|---|---|
| Username Search | 50+ sites checked in parallel |
| Email Search | Holehe-style service checks + Gravatar + GitHub |
| Phone Search | PhoneInfoga + carrier/location lookup |
| Name Search | Public profile discovery |
| Social Search | GitHub, Reddit, Instagram, Telegram, TikTok, etc. |
| Location Filter | Region-specific OSINT resource directory (8+ countries) |
| Advanced Search | Multi-criteria parallel search with flags |
| Reports | Export as TXT, HTML, or PDF |
| Inline Mode | Quick search directly from any chat |
| Rate Limiting | 5 searches/minute per user |
| Ban System | Admin commands to ban/unban abusers |
| Search Cache | 24-hour SQLite cache to avoid redundant lookups |
| Search History | Per-user history stored in SQLite |

---

## 🤖 Bot Commands

```
/start              — Welcome message & legal notice
/help               — Full command reference

/search_username <username>           — Search 50+ sites for username
/search_email <email>                 — Find linked accounts & data breaches
/search_phone <number>                — Carrier, region, WhatsApp check
/search_name <first> <last>           — Real name profile discovery
/search_social <platform> <id>        — Search specific social platform
/search_location <country>            — OSINT resources by country
/advanced_search -u <u> -e <e> ...    — Multi-criteria search

/report txt|html|pdf                  — Export your search history

/ban <user_id> [reason]               — (Admin) Ban a user
/unban <user_id>                      — (Admin) Unban a user
/banned                               — (Admin) List banned users
```

**Inline Mode:** Type `@YourBotUsername <query>` in any chat for quick search suggestions.

---

## 🚀 Deployment on Render

### Prerequisites
- Render account: https://render.com
- GitHub account (bot code pushed to a repo)
- Telegram Bot Token from @BotFather

### Step-by-step

1. **Push to GitHub** (already done via the agent's GitHub push)

2. **Create a new Render Worker:**
   - Go to https://dashboard.render.com
   - Click **New → Background Worker**
   - Connect your GitHub repository
   - Select the `osint-bot` folder as the root directory (or set **Root Directory** to `osint-bot`)

3. **Configure the service:**
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements-core.txt`
   - **Start Command:** `python bot.py`

4. **Set Environment Variables** in Render dashboard:
   | Key | Value |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
   | `ADMIN_IDS` | Your Telegram user ID (get it from @userinfobot) |
   | `DB_PATH` | `/opt/render/project/src/osint_bot.db` |

5. **Add a Disk** (for SQLite persistence):
   - In the service settings, add a disk
   - **Mount path:** `/opt/render/project/src`
   - **Size:** 1 GB (free tier)

6. **Deploy!** Click **Create Background Worker**

The bot will start polling automatically. Check the Render logs to confirm it's running.

---

## 🛠 Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/osint-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-core.txt

# Configure environment
cp .env.example .env
# Edit .env and set TELEGRAM_BOT_TOKEN

# Run the bot
python bot.py
```

---

## 📁 Project Structure

```
osint-bot/
├── bot.py                    # Main entry point
├── requirements.txt          # Full deps (includes optional OSINT tools)
├── requirements-core.txt     # Minimal deps for Render deployment
├── render.yaml               # Render deployment config
├── Procfile                  # Heroku-compatible start command
├── .env.example              # Environment variable template
├── .gitignore                # Excludes secrets & databases
│
├── handlers/                 # One file per search type
│   ├── start_handler.py      # /start, /help
│   ├── username_handler.py   # /search_username
│   ├── email_handler.py      # /search_email
│   ├── phone_handler.py      # /search_phone
│   ├── name_handler.py       # /search_name
│   ├── social_handler.py     # /search_social
│   ├── location_handler.py   # /search_location
│   ├── advanced_handler.py   # /advanced_search
│   ├── report_handler.py     # /report
│   ├── inline_handler.py     # Inline mode
│   └── admin_handler.py      # /ban, /unban, /banned
│
├── middleware/
│   ├── rate_limiter.py       # 5 requests/minute limit
│   └── ban_checker.py        # Blocks banned users
│
├── database/
│   └── db.py                 # SQLite: cache, history, bans, rate limits
│
└── utils/
    └── formatters.py         # Result formatting helpers
```

---

## 🔧 Optional Enhanced Tools

Install these for more powerful searches (may require additional setup):

```bash
# Holehe - email to accounts
pip install holehe

# Maigret - advanced username search (3000+ sites)
pip install maigret

# PhoneInfoga - advanced phone lookup
pip install phoneinfoga
```

---

## 📊 Architecture

```
User → Telegram → Bot (python-telegram-bot)
                    ├── Middleware (ban check → rate limit)
                    ├── Handler (search logic + aiohttp)
                    ├── Cache check (SQLite)
                    ├── External APIs / web scraping
                    └── Formatter → Telegram message
```

---

## 🔒 Security

- All tokens stored as environment variables (never in code)
- Rate limiting prevents abuse (5 req/min)
- Admin ban system for policy violators
- Search history for audit trail
- No permanent storage of sensitive personal data
- `.gitignore` excludes all `.env` and `.db` files

---

## 📝 License

MIT License — use responsibly.
