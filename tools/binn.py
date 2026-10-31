from live_emoji import plan_badge, dev_badge
import sys
import os
import re
import asyncio
import logging
import aiohttp
from html import escape


from aiogram import Router, F, types


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from database import get_user_credits, update_credits, get_db_connection
from sub import get_premium_status


router = Router()


async def fetch_bin_from_api(bin_number: str) -> dict:
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    return {"error": "BIN not found."}
                elif resp.status == 429:
                    return {"error": "Rate limit exceeded."}
                else:
                    return {"error": f"API Error: HTTP {resp.status}"}
        except asyncio.TimeoutError:
            return {"error": "Request Timed Out."}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

async def get_plan_name_from_db(user_id) -> str:
    """Fetches the plan name from receipts DB (only called when user is premium)."""
    def _sync_fetch():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT plan FROM receipts WHERE user_id = ? ORDER BY purchased_on DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row['plan'].upper() if row else "PREMIUM"
    try:
        return await asyncio.to_thread(_sync_fetch)
    except Exception as e:
        logging.error(f"Error fetching plan name: {e}")
        return "PREMIUM"


@router.message(F.text.startswith("/binn"))
async def binn_command(message: types.Message):
    """
    Fetches and displays BIN info using the direct API.
    Works with Args or Reply to a message.
    Deducts 1 credit on successful lookup.
    """

    user = message.from_user
    user_id = user.id


    raw_text = ""

    parts = message.text.split()
    if len(parts) > 1:
        raw_text = " ".join(parts[1:])
    elif message.reply_to_message:
        replied_msg = message.reply_to_message
        if replied_msg.text:
            raw_text = replied_msg.text
        elif replied_msg.caption:
            raw_text = replied_msg.caption


    if not raw_text:
        await message.reply(
            "<b>Ꭼʀʀᴏʀ</b> ➵ <b>Mɪssɪɴɢ Aʀɢᴜᴍᴇɴᴛ</b> <tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> \n"
            "Usage: <code>/bin 456789</code>\n",
            parse_mode="HTML"
        )
        return


    digits_only = re.sub(r'\D', '', raw_text)

    if len(digits_only) < 6:
        await message.reply(
            "<b>Ꭼʀʀᴏʀ</b> ➵ <b>Iɴᴠᴀʟɪᴅ Iɴᴘᴜᴛ</b> <tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> \n"
            "Please provide at least 6 digits in the argument or replied message.",
            parse_mode="HTML"
        )
        return

    bin_6 = digits_only[:6]


    (is_premium, _), data = await asyncio.gather(
        asyncio.to_thread(get_premium_status, user_id),
        fetch_bin_from_api(bin_6)
    )


    current_credits = 0
    if not is_premium:
        current_credits = await asyncio.to_thread(get_user_credits, user_id)
        if current_credits <= 0:
            await message.reply(
                "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs</b>\n\n"
                "Yᴏᴜ Nᴇᴇᴅ Aᴛ Lᴇᴀsᴛ <b>1 Cʀᴇᴅɪᴛ</b> Tᴏ Usᴇ Tʜɪs Gᴀᴛᴇ.\n"
                "Usᴇ /plan Tᴏ Gᴇᴛ Mᴏʀᴇ.",
                parse_mode="HTML"
            )
            return


    if "error" not in data and not is_premium:
        await asyncio.to_thread(update_credits, user_id, current_credits - 1)


    plan_name = await get_plan_name_from_db(user_id) if is_premium else "FREE"
    user_link = f'<a href="tg://user?id={user.id}">{escape(user.first_name)}</a>'
    user_display = f"{user_link} {plan_badge(plan_name)}"

    dev_link = dev_badge()


    if "error" in data:
        final_text = (
            f"<b>Sᴛᴀᴛᴜs</b> ➵ <b>Ꭼʀʀᴏʀ</b>\n"
            f"<b>Mᴇssᴀɢᴇ</b> ➵ <code>{data['error']}</code>\n"
            f"<b>Dᴇᴠ ➵ {dev_link}</b>"
        )
    else:
        api_bin = data.get("bin", bin_6)
        brand = data.get("brand", "N/A")
        level = data.get("level", "N/A")
        bank = data.get("bank", "N/A")
        country = data.get("country_name", "N/A")
        flag = data.get("country_flag", "")
        card_type = data.get("type", "N/A")
        currencies = data.get("country_currencies", [])

        country_display = f"{flag} {country}" if flag else country
        currency_display = currencies[0] if currencies else "N/A"

        final_text = (
            f'<b><a href="https://t.me/Try_Low">[⌭]</a> BIN Iɴғᴏ</b> <tg-emoji emoji-id=\"6100515480735321747\">✅</tg-emoji>\n'
            f"━━━━━━━━━━━━━━\n"
            f'<b><a href="https://t.me/Try_Low">⬢</a> Bɪɴ</b> ➵ <code>{api_bin}</code>\n'
            f'<b><a href="https://t.me/Try_Low">⬡</a> Bʀᴀɴᴅ ➵ {brand}</b>\n'
            f'<b><a href="https://t.me/Try_Low">⬢</a> Lᴇᴠᴇʟ ➵ {level}</b>\n'
            f'<b><a href="https://t.me/Try_Low">⬡</a> Bᴀɴᴋ ➵ {bank}</b>\n'
            f'<b><a href="https://t.me/Try_Low">⬢</a> Cᴏᴜɴᴛʀʏ ➵ {country_display}</b>\n'
            f'<b><a href="https://t.me/Try_Low">⬡</a> Tʏᴘᴇ ➵ {card_type}</b>\n'
            f'<b><a href="https://t.me/Try_Low">⬢</a> Cᴜʀʀᴇɴᴄʏ ➵ {currency_display}</b>\n'
            f"━━━━━━━━━━━━━━\n"
            f'<b><a href="https://t.me/Try_Low">⎔</a> Usᴇʀ ➵ {user_display}</b>\n'
            f'<b><a href="https://t.me/Try_Low">⎔</a> Dᴇᴠ ➵ {dev_link}</b>'
        )


    await message.reply(
        text=final_text,
        parse_mode="HTML",

        disable_web_page_preview=True
    )
