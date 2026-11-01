"""
Daily SQLite database + stats-file backup.

Every 24 h (at 00:00 UTC):
  1. hot-copies the SQLite DB (via .backup API) and gzips it
  2. zips the stats .txt files (mshh.txt, sites.txt, …)
  3. saves both to ./backups/ and DMs them to the owner
  4. prunes copies older than RETENTION_DAYS

Catch-up backup on boot if the newest one is older than 20 h.
"""

import gzip
import shutil
import sqlite3
import zipfile
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

from aiogram.types import FSInputFile

from database import DB_CONFIG, DB_PATH


BACKUP_DIR      = Path(__file__).resolve().parent / "backups"
RETENTION_DAYS  = 7
CATCHUP_AFTER_H = 20

STATS_FILES = ["mshh.txt", "sites.txt"]


def _admin_id() -> int:
    try:
        from sub import PRIMARY_ADMIN_ID
        return PRIMARY_ADMIN_ID
    except Exception:
        return 7963961151


def _resolve_db_path() -> Path:
    candidate = DB_PATH or (DB_CONFIG.get("database") if isinstance(DB_CONFIG, dict) else "bot.db")
    p = Path(candidate)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent / p
    return p


def _dump_db_sql(dest_gz: Path) -> None:
    """Hot-copy the SQLite DB via .backup API, then gzip it."""
    db_path = _resolve_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found at {db_path}")

    tmp_copy = BACKUP_DIR / ".db_snapshot.tmp"
    try:
        src_conn = sqlite3.connect(str(db_path), timeout=30)
        dst_conn = sqlite3.connect(str(tmp_copy))
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

        with open(tmp_copy, "rb") as fin, gzip.open(dest_gz, "wb", compresslevel=9) as fout:
            shutil.copyfileobj(fin, fout)
    finally:
        try:
            if tmp_copy.exists():
                tmp_copy.unlink()
        except Exception:
            pass


def _make_txt_zip(dest: Path) -> list:
    included = []
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in STATS_FILES:
            p = Path(name)
            if p.exists() and p.is_file():
                zf.write(p, arcname=name)
                included.append(name)
    return included


def _prune(pattern_prefix: str) -> int:
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    removed = 0
    for f in BACKUP_DIR.glob(f"{pattern_prefix}_*"):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                removed += 1
        except Exception:
            pass
    return removed


def _latest_age_hours() -> float:
    newest = 0.0
    for f in BACKUP_DIR.glob("broken_db_*.sql.gz"):
        try:
            newest = max(newest, f.stat().st_mtime)
        except Exception:
            pass
    if not newest:
        return 1e9
    return (datetime.now() - datetime.fromtimestamp(newest)).total_seconds() / 3600


async def run_backup(bot, reason: str = "scheduled"):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp    = datetime.now().strftime("%Y-%m-%d")
    admin_id = _admin_id()

    db_gz   = BACKUP_DIR / f"broken_db_{stamp}.sql.gz"
    txt_zip = BACKUP_DIR / f"stats_txt_{stamp}.zip"

    logging.info(f"[Backup] Starting ({reason}) …")

    db_ok = False
    try:
        await asyncio.to_thread(_dump_db_sql, db_gz)
        db_ok = True
        size = db_gz.stat().st_size / 1024
        logging.info(f"[Backup] DB dump OK → {db_gz.name} ({size:.0f} KB)")
    except Exception as e:
        logging.error(f"[Backup] DB dump failed: {e}")

    txt_ok, included = False, []
    try:
        included = await asyncio.to_thread(_make_txt_zip, txt_zip)
        txt_ok = True
        logging.info(f"[Backup] TXT zip OK → {txt_zip.name} ({len(included)} files)")
    except Exception as e:
        logging.error(f"[Backup] TXT zip failed: {e}")

    now_str = datetime.now().strftime("%d %b %Y, %H:%M UTC")

    if db_ok:
        try:
            await bot.send_document(
                chat_id=admin_id,
                document=FSInputFile(str(db_gz)),
                caption=(
                    "<b>🗄 Database Backup</b>\n"
                    "━━━━━━━━━━━\n"
                    f"📅 Date : <b>{now_str}</b>\n"
                    f"🗂 File : <code>{db_gz.name}</code>\n"
                    "🔐 SQLite snapshot (restore: rename to bot.db)\n"
                    "━━━━━━━━━━━"
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logging.error(f"[Backup] Could not send DB backup: {e}")

    if txt_ok:
        try:
            file_list = "\n".join(f"• <code>{n}</code>" for n in included) or "• (none yet)"
            await bot.send_document(
                chat_id=admin_id,
                document=FSInputFile(str(txt_zip)),
                caption=(
                    "<b>📄 Stats Files Backup</b>\n"
                    "━━━━━━━━━━━\n"
                    f"📅 Date : <b>{now_str}</b>\n"
                    f"{file_list}\n"
                    "━━━━━━━━━━━"
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logging.error(f"[Backup] Could not send TXT backup: {e}")

    if not db_ok:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="⚠️ <b>Backup failed!</b>\nThe daily database dump did not complete. Check the bot logs.",
                parse_mode="HTML",
            )
        except Exception:
            pass

    removed  = await asyncio.to_thread(_prune, "broken_db")
    removed += await asyncio.to_thread(_prune, "stats_txt")
    if removed:
        logging.info(f"[Backup] Pruned {removed} old file(s)")
    logging.info("[Backup] Done ✅")


def _seconds_until_midnight() -> float:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(60.0, (tomorrow - now).total_seconds())


async def daily_backup_scheduler(bot):
    try:
        age = await asyncio.to_thread(_latest_age_hours)
        if age > CATCHUP_AFTER_H:
            logging.info(f"[Backup] Last backup {age:.0f}h old — running catch-up now.")
            await run_backup(bot, reason="catch-up")
    except Exception as e:
        logging.error(f"[Backup] catch-up error: {e}")

    while True:
        wait = _seconds_until_midnight()
        logging.info(f"[Backup] Next run in {wait/3600:.2f}h (00:00 UTC)")
        await asyncio.sleep(wait)
        try:
            await run_backup(bot, reason="scheduled")
        except Exception as e:
            logging.error(f"[Backup] scheduled run error: {e}")
