import sqlite3
import asyncio
from typing import Callable, Dict, Any, Awaitable
from aiogram import Router, types, BaseMiddleware
from aiogram.filters import Command
from database import DB_CONFIG


ADMIN_IDS = {7963961151, 8880615460}

router = Router()


def _ensure_banned_table():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id   INTEGER PRIMARY KEY,
                banned_at TIMESTAMP DEFAULT datetime('now')
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[DB] banned_users table checked.")
    except Exception as e:
        print(f"[DB] Error creating banned_users table: {e}")

_ensure_banned_table()


def _is_banned_sync(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def _ban_user_sync(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO banned_users (user_id) VALUES (?) ON CONFLICT DO NOTHING",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

def _unban_user_sync(user_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM banned_users WHERE user_id = ?",
        (user_id,)
    )
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result is not None


@router.message(Command("ban"))
async def ban_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Aᴅᴍɪɴ Oɴʟʏ.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.reply("Usage: /ban [user_id]")
        return

    target_id = int(parts[1])
    if target_id in ADMIN_IDS:
        await message.reply("❌ Cannot ban the admin.")
        return

    await asyncio.to_thread(_ban_user_sync, target_id)
    await message.reply(
        f"🚫 User <code>{target_id}</code> has been <b>banned</b>.",
        parse_mode="HTML"
    )


@router.message(Command("unban"))
async def unban_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ Aᴅᴍɪɴ Oɴʟʏ.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.reply("Usage: /unban [user_id]")
        return

    target_id = int(parts[1])
    removed = await asyncio.to_thread(_unban_user_sync, target_id)

    if removed:
        await message.reply(
            f"✅ User <code>{target_id}</code> has been <b>unbanned</b>.",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            f"⚠️ User <code>{target_id}</code> is <b>not</b> in the ban list.",
            parse_mode="HTML"
        )


BAN_WARNING = (
    "🚫 <b>Yᴏᴜ Hᴀᴠᴇ Bᴇᴇɴ Bᴀɴɴᴇᴅ Fʀᴏᴍ Usɪɴɢ Tʜɪs Bᴏᴛ.</b>\n\n"
    "<b>Cᴏɴᴛᴀᴄᴛ Wɪᴛʜ Oᴡɴᴇʀ.</b>"
)

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        if not user or user.id in ADMIN_IDS:
            return await handler(event, data)

        banned = await asyncio.to_thread(_is_banned_sync, user.id)
        if banned:
            try:
                await event.reply(BAN_WARNING, parse_mode="HTML")
            except Exception:
                pass
            return

        return await handler(event, data)
