# database.py — SQLite drop-in replacement (no PostgreSQL needed)
import sqlite3
import threading
import time
import logging
from datetime import datetime

DB_PATH = "bot.db"
_lock   = threading.Lock()

OWNER_IDS = {8801932812, 8801932812}

def is_owner_user(user_id) -> bool:
    try:    return int(user_id) in OWNER_IDS
    except: return False

# ── row handling ────────────────────────────────────────────────────

# Columns that hold timestamps. SQLite returns them as text, so we parse them
# back into datetime objects here. Works for both new and old tables.
_TS_COLS = {
    "premium_expiry", "joined_at", "purchased_on", "expires_on",
    "created_at", "paid_at", "claimed_at", "expires_at", "updated_at",
    "banned_at", "added_at", "cooldown_until", "last_used",
}


def _to_dt(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    return value


class _Row(dict):
    """Dict-style row that also supports integer indexing (row[0]) and .get()."""

    def __init__(self, cols, vals):
        super().__init__(zip(cols, vals))
        self._vals = tuple(vals)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return super().__getitem__(key)


def _row_factory(cursor, row):
    cols = [d[0] for d in cursor.description]
    vals = [_to_dt(v) if c in _TS_COLS else v for c, v in zip(cols, row)]
    return _Row(cols, vals)


# ── connection ──────────────────────────────────────────────────────

def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    c.row_factory = _row_factory
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

class PooledConn:
    def __enter__(self):
        self._c = _conn(); return self._c
    def __exit__(self, exc, *_):
        if exc: self._c.rollback()
        else:   self._c.commit()
        self._c.close()

def get_db_connection():
    return _conn()

# ── caches ──────────────────────────────────────────────────────────

_gate_cache         = {}
_gate_cache_ttl     = 30
_credits_cache      = {}
_credits_cache_ttl  = 5
_premium_cache      = {}
_premium_cache_ttl  = 60

# ── schema helpers ──────────────────────────────────────────────────

def ensure_users_table():
    with PooledConn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id              INTEGER PRIMARY KEY,
                username             TEXT,
                first_name           TEXT,
                credits              INTEGER DEFAULT 0,
                cc_checked           INTEGER DEFAULT 0,
                cc_charged           INTEGER DEFAULT 0,
                cc_charged_lifetime  INTEGER DEFAULT 0,
                cc_approved_lifetime INTEGER DEFAULT 0,
                cc_declined_lifetime INTEGER DEFAULT 0,
                is_premium           INTEGER DEFAULT 0,
                premium_expiry       TEXT,
                joined_at            TEXT
            )
        """)
    logging.info("[DB] users table ready")

def ensure_stats_columns():
    # SQLite doesn't support IF NOT EXISTS on ALTER — safely ignore errors
    for col in ("cc_checked INTEGER DEFAULT 0", "cc_charged INTEGER DEFAULT 0"):
        try:
            with PooledConn() as c:
                c.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except Exception: pass

def ensure_lifetime_stats_columns():
    for col in (
        "cc_charged_lifetime  INTEGER DEFAULT 0",
        "cc_approved_lifetime INTEGER DEFAULT 0",
        "cc_declined_lifetime INTEGER DEFAULT 0",
    ):
        try:
            with PooledConn() as c:
                c.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except Exception: pass

def ensure_proxy_table():
    with PooledConn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                proxy    TEXT NOT NULL,
                added_at TEXT DEFAULT (datetime('now'))
            )
        """)

def ensure_gate_table():
    with PooledConn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS gate_status (
                gate       TEXT PRIMARY KEY,
                is_enabled INTEGER DEFAULT 1,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

def ensure_keys_columns():
    for col in (
        "plan_name        TEXT",
        "duration_seconds INTEGER",
        "created_by       INTEGER",
        "expires_at       TEXT",
    ):
        try:
            with PooledConn() as c:
                c.execute(f"ALTER TABLE codes ADD COLUMN {col}")
        except Exception: pass

def ensure_codes_table():
    with PooledConn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS codes (
                code             TEXT PRIMARY KEY,
                credits          INTEGER DEFAULT 0,
                used             INTEGER DEFAULT 0,
                used_by          INTEGER,
                plan_name        TEXT,
                duration_seconds INTEGER,
                created_by       INTEGER,
                expires_at       TEXT,
                claimed_by       INTEGER,
                claimed_at       TIMESTAMP
            )
        """)

def ensure_receipts_table():
    with PooledConn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id   TEXT,
                user_id      INTEGER,
                plan         TEXT,
                amount_paid  REAL,
                purchased_on TEXT DEFAULT (datetime('now')),
                expires_on   TIMESTAMP,
                track_id     TEXT
            )
        """)

def _column_names(table: str) -> set:
    with PooledConn() as c:
        return {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}

def _add_column(table: str, name: str, decl: str) -> bool:
    try:
        with PooledConn() as c:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
        return True
    except Exception:
        return False

def ensure_migrations():
    """Bring tables created by older versions up to the columns sub.py and payments.py use."""
    # receipts
    existing = _column_names("receipts")
    for name, decl in (
        ("receipt_id",  "TEXT"),
        ("amount_paid", "REAL"),
        ("expires_on",  "TIMESTAMP"),
    ):
        if name not in existing:
            _add_column("receipts", name, decl)
    try:
        with PooledConn() as c:
            c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_receipts_receipt_id ON receipts(receipt_id)")
    except Exception as e:
        logging.warning(f"[DB] receipt_id index: {e}")

    # codes
    existing = _column_names("codes")
    claimed_just_added = False
    for name, decl in (
        ("claimed_by",       "INTEGER"),
        ("claimed_at",       "TIMESTAMP"),
        ("plan_name",        "TEXT"),
        ("duration_seconds", "INTEGER"),
        ("created_by",       "INTEGER"),
        ("expires_at",       "TIMESTAMP"),
    ):
        if name not in existing:
            if _add_column("codes", name, decl) and name == "claimed_by":
                claimed_just_added = True
    if claimed_just_added:
        # Carry over codes the old schema marked as used
        try:
            with PooledConn() as c:
                c.execute("""
                    UPDATE codes
                       SET claimed_by = used_by,
                           claimed_at = datetime('now')
                     WHERE used = 1 AND claimed_by IS NULL
                """)
        except Exception as e:
            logging.warning(f"[DB] codes backfill: {e}")

def create_global_proxy_table():
    with PooledConn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS global_proxies (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                proxy          TEXT UNIQUE NOT NULL,
                status         TEXT DEFAULT 'active',
                fail_count     INTEGER DEFAULT 0,
                success_count  INTEGER DEFAULT 0,
                cooldown_until TEXT,
                last_used      TEXT,
                created_at     TEXT DEFAULT (datetime('now'))
            )
        """)

# ── user ops ────────────────────────────────────────────────────────

def get_user(user_id: int):
    with PooledConn() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

def create_user(user_id: int, username: str, first_name: str = None):
    with PooledConn() as c:
        c.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, credits, joined_at)
            VALUES (?,?,?,?,?)
        """, (user_id, username, first_name, 150, datetime.now().isoformat()))

def set_first_name(user_id: int, first_name: str):
    name = str(first_name or "").strip()[:64]
    if not name: return
    with PooledConn() as c:
        c.execute("UPDATE users SET first_name=? WHERE user_id=?", (name, user_id))

def get_user_credits(user_id: int) -> int:
    now    = time.monotonic()
    cached = _credits_cache.get(user_id)
    if cached and now < cached[1]: return cached[0]
    with PooledConn() as c:
        row = c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,)).fetchone()
        credits = row[0] if row else 0
    _credits_cache[user_id] = (credits, now + _credits_cache_ttl)
    return credits

def update_credits(user_id: int, new_credits: int):
    with PooledConn() as c:
        c.execute("UPDATE users SET credits=? WHERE user_id=?", (new_credits, user_id))
    _credits_cache[user_id] = (new_credits, time.monotonic() + _credits_cache_ttl)

def deduct_credits_atomic(user_id: int, amount: int) -> int:
    with _lock:
        with PooledConn() as c:
            c.execute("""
                UPDATE users SET credits = MAX(credits - ?, 0) WHERE user_id=?
            """, (amount, user_id))
            row = c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,)).fetchone()
            new_credits = row[0] if row else 0
    _credits_cache[user_id] = (new_credits, time.monotonic() + _credits_cache_ttl)
    return new_credits

def update_user_stats(user_id: int, is_charged: bool):
    with PooledConn() as c:
        if is_charged:
            c.execute("UPDATE users SET cc_checked=cc_checked+1, cc_charged=cc_charged+1 WHERE user_id=?", (user_id,))
        else:
            c.execute("UPDATE users SET cc_checked=cc_checked+1 WHERE user_id=?", (user_id,))

def increment_lifetime_stats(user_id: int, charged=0, approved=0, declined=0):
    if charged == 0 and approved == 0 and declined == 0: return
    with PooledConn() as c:
        c.execute("""
            UPDATE users SET
                cc_charged_lifetime  = cc_charged_lifetime  + ?,
                cc_approved_lifetime = cc_approved_lifetime + ?,
                cc_declined_lifetime = cc_declined_lifetime + ?
            WHERE user_id=?
        """, (charged, approved, declined, user_id))

def get_user_lifetime_stats(user_id: int) -> dict:
    with PooledConn() as c:
        row = c.execute("""
            SELECT cc_charged_lifetime, cc_approved_lifetime, cc_declined_lifetime
            FROM users WHERE user_id=?
        """, (user_id,)).fetchone()
    if row:
        return {"cc_charged_lifetime": row[0] or 0,
                "cc_approved_lifetime": row[1] or 0,
                "cc_declined_lifetime": row[2] or 0}
    return {"cc_charged_lifetime": 0, "cc_approved_lifetime": 0, "cc_declined_lifetime": 0}

def get_all_lifetime_stats_totals() -> dict:
    with PooledConn() as c:
        row = c.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(cc_charged_lifetime),0),
                   COALESCE(SUM(cc_approved_lifetime),0),
                   COALESCE(SUM(cc_declined_lifetime),0)
            FROM users
        """).fetchone()
    if row:
        return {"total_users": row[0], "total_charged": row[1],
                "total_approved": row[2], "total_declined": row[3]}
    return {"total_users": 0, "total_charged": 0, "total_approved": 0, "total_declined": 0}

# ── gate ops ────────────────────────────────────────────────────────

ALL_GATES = ("st","sp","vbv","b3","ch","msh","scr","clean")

def is_known_gate(gate: str) -> bool:
    return gate in ALL_GATES

def is_gate_enabled(gate: str) -> bool:
    now    = time.monotonic()
    cached = _gate_cache.get(gate)
    if cached and now < cached[1]: return cached[0]
    with PooledConn() as c:
        c.execute("INSERT OR IGNORE INTO gate_status (gate, is_enabled) VALUES (?,1)", (gate,))
        row    = c.execute("SELECT is_enabled FROM gate_status WHERE gate=?", (gate,)).fetchone()
        status = bool(row[0]) if row else True
    _gate_cache[gate] = (status, now + _gate_cache_ttl)
    return status

def set_gate_status(gate: str, enabled: bool):
    with PooledConn() as c:
        c.execute("""
            INSERT INTO gate_status (gate, is_enabled) VALUES (?,?)
            ON CONFLICT(gate) DO UPDATE SET is_enabled=excluded.is_enabled,
            updated_at=datetime('now')
        """, (gate, int(enabled)))
    _gate_cache[gate] = (enabled, time.monotonic() + _gate_cache_ttl)

def get_all_gate_status() -> dict:
    status = {g: True for g in ALL_GATES}
    with PooledConn() as c:
        rows = c.execute("SELECT gate, is_enabled FROM gate_status").fetchall()
    now = time.monotonic()
    for row in rows:
        enabled = bool(row[0])
        status[row[0]] = enabled
        _gate_cache[row[0]] = (enabled, now + _gate_cache_ttl)
    return status

def set_gate_status_bulk(enabled: bool, gates=None) -> list:
    targets = list(ALL_GATES if gates is None else gates)
    if not targets: return []
    with PooledConn() as c:
        for g in targets:
            c.execute("""
                INSERT INTO gate_status (gate, is_enabled) VALUES (?,?)
                ON CONFLICT(gate) DO UPDATE SET is_enabled=excluded.is_enabled,
                updated_at=datetime('now')
            """, (g, int(enabled)))
    now = time.monotonic()
    for g in targets:
        _gate_cache[g] = (enabled, now + _gate_cache_ttl)
    return targets

def clear_gate_cache(gate: str = None):
    if gate is None: _gate_cache.clear()
    else:            _gate_cache.pop(gate, None)

# ── global proxy ops ────────────────────────────────────────────────

def add_global_proxy(proxy: str) -> str:
    try:
        with PooledConn() as c:
            c.execute("INSERT OR IGNORE INTO global_proxies (proxy) VALUES (?)", (proxy,))
            return 'added' if c.execute("SELECT changes()").fetchone()[0] else 'exists'
    except Exception as e:
        logging.error(f"[DB] add_global_proxy: {e}"); return 'error'

def remove_global_proxy(proxy: str) -> bool:
    try:
        with PooledConn() as c:
            c.execute("DELETE FROM global_proxies WHERE proxy=?", (proxy,))
            return c.execute("SELECT changes()").fetchone()[0] > 0
    except Exception as e:
        logging.error(f"[DB] remove_global_proxy: {e}"); return False

def clear_global_proxies() -> int:
    try:
        with PooledConn() as c:
            count = c.execute("SELECT COUNT(*) FROM global_proxies").fetchone()[0]
            c.execute("DELETE FROM global_proxies")
            return count
    except Exception as e:
        logging.error(f"[DB] clear_global_proxies: {e}"); return 0

def get_global_proxies() -> list:
    try:
        with PooledConn() as c:
            rows = c.execute("""
                SELECT proxy FROM global_proxies
                WHERE status='active'
                   OR cooldown_until IS NULL
                   OR cooldown_until <= datetime('now')
                ORDER BY id
            """).fetchall()
            return [r[0] for r in rows]
    except Exception as e:
        logging.error(f"[DB] get_global_proxies: {e}"); return []

def get_global_proxy_count() -> int:
    try:
        with PooledConn() as c:
            return c.execute("SELECT COUNT(*) FROM global_proxies").fetchone()[0]
    except: return 0

def mark_proxy_success(proxy: str):
    try:
        with PooledConn() as c:
            c.execute("""
                UPDATE global_proxies SET success_count=success_count+1,
                status='active', cooldown_until=NULL, last_used=datetime('now')
                WHERE proxy=?
            """, (proxy,))
    except Exception as e: logging.error(f"[DB] mark_proxy_success: {e}")

def mark_proxy_failed(proxy: str, cooldown_seconds: int = 300):
    try:
        with PooledConn() as c:
            c.execute("""
                UPDATE global_proxies SET fail_count=fail_count+1,
                status='cooldown',
                cooldown_until=datetime('now',?||' seconds'),
                last_used=datetime('now')
                WHERE proxy=?
            """, (str(cooldown_seconds), proxy))
    except Exception as e: logging.error(f"[DB] mark_proxy_failed: {e}")

def reset_failed_proxies():
    try:
        with PooledConn() as c:
            c.execute("""
                UPDATE global_proxies SET status='active', cooldown_until=NULL
                WHERE status='cooldown' AND cooldown_until <= datetime('now')
            """)
            return c.execute("SELECT changes()").fetchone()[0]
    except Exception as e:
        logging.error(f"[DB] reset_failed_proxies: {e}"); return 0

def proxy_statistics() -> dict:
    try:
        with PooledConn() as c:
            row = c.execute("""
                SELECT COUNT(*),
                       SUM(CASE WHEN status='active' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN status='cooldown' AND cooldown_until > datetime('now') THEN 1 ELSE 0 END),
                       AVG(fail_count)
                FROM global_proxies
            """).fetchone()
        if row:
            return {"total": row[0] or 0, "active": row[1] or 0,
                    "on_cooldown": row[2] or 0, "avg_fail_count": float(row[3] or 0)}
        return {}
    except Exception as e:
        logging.error(f"[DB] proxy_statistics: {e}"); return {}

# ── DB_CONFIG shim (for main.py which imports it) ───────────────────
DB_CONFIG = {"database": DB_PATH}

# ── boot ────────────────────────────────────────────────────────────
ensure_users_table()
ensure_stats_columns()
ensure_lifetime_stats_columns()
ensure_proxy_table()
ensure_gate_table()
ensure_codes_table()
ensure_receipts_table()
ensure_keys_columns()
ensure_migrations()
create_global_proxy_table()
logging.info("[DB] SQLite ready → bot.db")