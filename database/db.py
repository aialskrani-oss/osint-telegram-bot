"""
SQLite database for caching results, search history, and banned users.
"""
import sqlite3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_PATH", "osint_bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS search_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_type TEXT NOT NULL,
            query_value TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(query_type, query_value)
        );

        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            query_type TEXT NOT NULL,
            query_value TEXT NOT NULL,
            result_summary TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_at TEXT NOT NULL,
            banned_by INTEGER
        );

        CREATE TABLE IF NOT EXISTS rate_limits (
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_rate_limits_user ON rate_limits(user_id, action);
        CREATE INDEX IF NOT EXISTS idx_history_user ON search_history(user_id);
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)


def get_cached(query_type: str, query_value: str, max_age_hours: int = 24):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT result_json, created_at FROM search_cache
           WHERE query_type=? AND query_value=?""",
        (query_type, query_value.lower())
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    created = datetime.fromisoformat(row["created_at"])
    age = (datetime.utcnow() - created).total_seconds() / 3600
    if age > max_age_hours:
        return None
    return json.loads(row["result_json"])


def set_cache(query_type: str, query_value: str, result: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO search_cache
           (query_type, query_value, result_json, created_at)
           VALUES (?, ?, ?, ?)""",
        (query_type, query_value.lower(), json.dumps(result), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def log_search(user_id: int, username: str, query_type: str, query_value: str, summary: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO search_history
           (user_id, username, query_type, query_value, result_summary, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, username, query_type, query_value, summary, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def is_banned(user_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row is not None


def ban_user_db(user_id: int, reason: str, banned_by: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO banned_users (user_id, reason, banned_at, banned_by)
           VALUES (?, ?, ?, ?)""",
        (user_id, reason, datetime.utcnow().isoformat(), banned_by)
    )
    conn.commit()
    conn.close()


def unban_user_db(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_banned_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, reason, banned_at, banned_by FROM banned_users")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_rate_limit_count(user_id: int, action: str, window_seconds: int) -> int:
    conn = get_conn()
    c = conn.cursor()
    cutoff = datetime.utcnow().timestamp() - window_seconds
    c.execute(
        """SELECT COUNT(*) as cnt FROM rate_limits
           WHERE user_id=? AND action=? AND CAST(timestamp AS REAL) > ?""",
        (user_id, action, cutoff)
    )
    row = c.fetchone()
    conn.close()
    return row["cnt"] if row else 0


def add_rate_limit_entry(user_id: int, action: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO rate_limits (user_id, action, timestamp) VALUES (?, ?, ?)",
        (user_id, action, str(datetime.utcnow().timestamp()))
    )
    conn.commit()
    conn.close()


def get_user_history(user_id: int, limit: int = 20):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT query_type, query_value, result_summary, created_at
           FROM search_history WHERE user_id=?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
