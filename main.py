import sqlite3
import logging
import asyncio
import time
import html
from datetime import datetime
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, types, F, Router, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from database import get_user, create_user, get_user_credits, update_credits, set_first_name, DB_CONFIG
from live_emoji import _ALIASES as _PLAN_ALIASES, _LOOKUP as _PLAN_LOOKUP
import privacy
import gifs
from gate import (
    on_command, off_command, onall_command, offall_command,
    gates_command, gif_command, offgif_command,
)
from fb import router as fb_router, setup_feedback_handler, feedback_cmd
from stats import stats_command
from tools.binn import binn_command
from tools.gen import gen_command, regenerate_cards_callback
from cmds import router as cmds_router, cmds_command
from broad import broad_command, router as broad_router
from ban import ban_command, unban_command, BanMiddleware, router as ban_router
from status import status_command, router as status_router
from sub import (
    auth_command, rc_command, authall_command, gen_code_command,
    claim_command, info_command, rauth_command, plan_command,
    adcr_command, get_premium_status, key_command,
    premium_expiry_worker,
    me_command, all_command,
)
from proxy import (
    proxy_command, checkproxy_command, clearproxy_command, myproxy_command,
    gproxyadd_command, gproxyclear_command, gproxyreload_command,
    gproxyinfo_command, gproxyexport_command,
    global_proxy_manager,
)

from gates.st import st_command
from gates.sp import sp_command
from gates.vbv import vbv_command
from gates.ch import ch_command
from gates.b3 import b3_command
from autohitters.stco import stco_command, stco_callback_handler
from autohitters.whop import router as whop_router, whop_command, whop_callback_handler
from autohitters.jio import router as jio_router, jio_command, jio_callback_handler
from autohitters.mpin import router as mpin_router

from mass_gates.msh import (
    router as msh_router, MshStopCallback, MshResultCallback,
    handle_stop_callback as msh_stop_handler,
    handle_result_callback as msh_result_handler,
)
from mass_gates.sitechk import (
    checksite_command, seturl_command, siteall_command,
    removeall_command, dedupe_command, proxyinfo_command, resetproxy_command
)

import payments as pay_sys

from backup import daily_backup_scheduler




from split import (
    router as split_router,
)


BOT_TOKEN = "9076243583:AAHYaxMKukLL9dRFXkBAKszeR8771EK9bnE"

START_IMAGE_URL     = "https://ibb.co/nM7VhBZy"

LOG_CHANNEL_ID      = 5359329585
BOT_LINK            = "https://t.me/Try_Low"
REQUIRED_CHANNEL_ID = -1003744006874
REQUIRED_GROUP_ID   = -1003706505883
REQUIRED_GROUP2_ID  = 5359329585
CHANNEL_LINK        = "https://t.me/+gKR64Mqqdp41MTBk"
GROUP_LINK          = "https://t.me/+qbfZLvrw5qgzMzVh"
GROUP2_LINK         = "https://t.me/+YfwzO7RQWgM2YThl"
OWNER_LINK = "https://t.me/Try_Low"
JOIN_TEXT = (
    '<tg-emoji emoji-id="5445033158456145975">📲</tg-emoji> '
    '<b>𝗔𝗰𝗰𝗲𝘀𝘀 𝗥𝗲𝘀𝘁𝗿𝗶𝗰𝘁𝗲𝗱</b> '
    '<tg-emoji emoji-id="5445362436418859744">↩️</tg-emoji>\n\n'

    '<tg-emoji emoji-id="5447453226498552490">💳</tg-emoji> '
    '<b>𝗧𝗼 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀 𝗕𝗼𝘁 𝗬𝗼𝘂 𝗠𝘂𝘀𝘁 𝗕𝗲 𝗡𝗲𝗲𝗱 𝘁𝗼 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 & 𝗚𝗿𝗼𝘂𝗽 𝗖𝗵𝗮𝘁</b> '
    '<tg-emoji emoji-id="5445146408153806223">📊</tg-emoji>\n\n'

    '<tg-emoji emoji-id="5445027583588593750">🌐</tg-emoji> '
    '<b>𝗖𝗹𝗶𝗰𝗸 𝗩𝗲𝗿𝗶𝗳𝘆 𝗔𝗳𝘁𝗲𝗿 𝗝𝗼𝗶𝗻𝗶𝗻𝗴</b> '
    '<tg-emoji emoji-id="5879883461711367869">⬇️</tg-emoji>'
)

PRICING_TEXT = (
    '[⌯] <b>𝗣𝗹𝗮𝗻𝘀</b> ⌁ 𝙶𝚎𝚝 𝙿𝚕𝚊𝚗𝚜 '
    '<tg-emoji emoji-id="5039644681583985437">🔥</tg-emoji>\n'
    '─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n'
    '[⌯] <b>𝗦𝗪𝗜𝗙𝗧</b> ⌁ $𝟹 '
    '<tg-emoji emoji-id="5893368370530621889">🔜</tg-emoji>\n'
    '[⌯] <b>𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻</b> ⌁ 𝟸 𝙳𝚊𝚢𝚜 '
    '<tg-emoji emoji-id="5195410032874769208">🌏</tg-emoji>\n'
    '─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n'
    '[⌯] <b>𝗧𝗨𝗥𝗕𝗢</b> ⌁ $𝟽 '
    '<tg-emoji emoji-id="5893368370530621889">🔜</tg-emoji>\n'
    '[⌯] <b>𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻</b> ⌁ 𝟽 𝙳𝚊𝚢𝚜 '
    '<tg-emoji emoji-id="5195410032874769208">🌏</tg-emoji>\n'
    '─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n'
    '[⌯] <b>𝗡𝗜𝗧𝗥𝗢</b> ⌁ $𝟷𝟺 '
    '<tg-emoji emoji-id="5893368370530621889">🔜</tg-emoji>\n'
    '[⌯] <b>𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻</b> ⌁ 𝟷𝟻 𝙳𝚊𝚢𝚜 '
    '<tg-emoji emoji-id="5195410032874769208">🌏</tg-emoji>\n'
    '─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n'
    '[⌯] <b>𝗔𝗣𝗘𝗫</b> ⌁ $𝟸𝟻 '
    '<tg-emoji emoji-id="5893368370530621889">🔜</tg-emoji>\n'
    '[⌯] <b>𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻</b> ⌁ 𝟹𝟶 𝙳𝚊𝚢𝚜 '
    '<tg-emoji emoji-id="5195410032874769208">🌏</tg-emoji>\n'
    '─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n'
    '[⌯] <b>𝗖𝗼𝗻𝘁𝗮𝗰𝘁</b> ⌁ '
    '<a href="https://t.me/Try_Low">𝒁𝑼𝑳𝑸𝑨𝑹</a> '
    '<tg-emoji emoji-id="5454096630372379732">☑️</tg-emoji>'
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


bot = Bot(
    token=BOT_TOKEN,
    session=gifs.build_session(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp  = Dispatcher(storage=MemoryStorage())


dp.include_router(msh_router)
dp.include_router(cmds_router)
dp.include_router(fb_router)
dp.include_router(ban_router)
dp.include_router(broad_router)
dp.include_router(status_router)
dp.include_router(split_router)
dp.include_router(whop_router)
dp.include_router(jio_router)
dp.include_router(mpin_router)

router = Router()
dp.include_router(router)


EMOJI_LIGHTNING = "5085022089103016925"
EMOJI_BAT       = "6136246765369694911"
EMOJI_STAR      = "6136275172283391020"
EMOJI_TOP       = "5463071033256848094"
EMOJI_DIAMOND   = "5359719332542718652"
EMOJI_APPROVED  = "6100515480735321747"
EMOJI_DECLINED  = "6100541628496219252"

ADMIN_IDS = {7963961151, 8880615460}


def colored_button(
    text: str,
    callback_data: str = None,
    url: str = None,
    style: str = "primary",
    icon_custom_emoji_id: str = None,
) -> InlineKeyboardButton:
    kwargs: dict = {"text": text, "style": style}
    if url:
        kwargs["url"] = url
    else:
        kwargs["callback_data"] = callback_data
    if icon_custom_emoji_id:
        kwargs["icon_custom_emoji_id"] = str(icon_custom_emoji_id)
    return InlineKeyboardButton(**kwargs)


def colored_back_button(target: str, style: str = "danger") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [colored_button(text="𝗕𝗮𝗰𝗸", callback_data=target, style=style)]
    ])


_MEMBERSHIP_CACHE: Dict[int, tuple]       = {}
_MEMBERSHIP_CACHE_TTL                     = 60
_MEMBERSHIP_LOCK: Dict[int, asyncio.Lock] = {}
_VALID_STATUSES                           = {"member", "administrator", "creator"}
_MEMBERSHIP_LOCK_MAP_LOCK: Optional[asyncio.Lock] = None


def _get_lock_map_lock() -> asyncio.Lock:
    global _MEMBERSHIP_LOCK_MAP_LOCK
    if _MEMBERSHIP_LOCK_MAP_LOCK is None:
        _MEMBERSHIP_LOCK_MAP_LOCK = asyncio.Lock()
    return _MEMBERSHIP_LOCK_MAP_LOCK


async def _get_user_lock(user_id: int) -> asyncio.Lock:
    async with _get_lock_map_lock():
        if user_id not in _MEMBERSHIP_LOCK:
            _MEMBERSHIP_LOCK[user_id] = asyncio.Lock()
        return _MEMBERSHIP_LOCK[user_id]


async def check_membership(user_id: int, bot_instance: Bot) -> bool:
    now    = time.monotonic()
    cached = _MEMBERSHIP_CACHE.get(user_id)
    if cached is not None:
        is_member, expires_at = cached
        if now < expires_at:
            return is_member

    lock = await _get_user_lock(user_id)
    async with lock:
        now    = time.monotonic()
        cached = _MEMBERSHIP_CACHE.get(user_id)
        if cached is not None:
            is_member, expires_at = cached
            if now < expires_at:
                return is_member
        try:
            ch, gr, gr2 = await asyncio.gather(
                bot_instance.get_chat_member(REQUIRED_CHANNEL_ID, user_id),
                bot_instance.get_chat_member(REQUIRED_GROUP_ID,   user_id),
                bot_instance.get_chat_member(REQUIRED_GROUP2_ID,  user_id),
            )
            is_member = (ch.status in _VALID_STATUSES
                         and gr.status in _VALID_STATUSES
                         and gr2.status in _VALID_STATUSES)
        except Exception as e:
            logging.warning(f"Membership check failed for {user_id}: {e}")
            is_member = False
        ttl = _MEMBERSHIP_CACHE_TTL if is_member else 15
        _MEMBERSHIP_CACHE[user_id] = (is_member, now + ttl)
        return is_member


def invalidate_membership_cache(user_id: int):
    _MEMBERSHIP_CACHE.pop(user_id, None)


_JOIN_KB = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            text="𝗖𝗛𝗔𝗡𝗡𝗘𝗟",
            url=CHANNEL_LINK,
            icon_custom_emoji_id="5258318251355545562"
        ),
        colored_button(
            text="𝗚𝗥𝗢𝗨𝗣",
            url=GROUP_LINK,
            icon_custom_emoji_id="5258330865674494479"
        ),
    ],
    [
        colored_button(
            text="𝗛𝗜𝗧 𝗟𝗢𝗚𝗦",
            url=GROUP2_LINK,
            icon_custom_emoji_id="5258334872878980409",
        ),
    ],
    [
        colored_button(
            text="𝗩𝗘𝗥𝗜𝗙𝗬",
            callback_data="verify_membership",
            icon_custom_emoji_id="5357069174512303778",
        )
    ],
])


class MembershipMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: Dict[str, Any]):
        user = event.from_user
        if not user:
            return await handler(event, data)
        if user.id in ADMIN_IDS:
            return await handler(event, data)
        if not await check_membership(user.id, data["bot"]):
            await event.answer(
                text=JOIN_TEXT,
                parse_mode="HTML",
                reply_markup=_JOIN_KB,
                disable_web_page_preview=True,
            )
            return
        return await handler(event, data)


dp.message.middleware(MembershipMiddleware())
dp.message.middleware(BanMiddleware())


@router.callback_query(F.data == "verify_membership")
async def verify_membership_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    invalidate_membership_cache(user_id)
    joined = await check_membership(user_id, callback.bot)

    if joined:
        try:
            await callback.answer(
                "𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱 𝗡𝗼𝘄 𝗬𝗼𝘂 𝗛𝗮𝘃𝗲 𝗙𝘂𝗹𝗹 𝗔𝗰𝗰𝗲𝘀𝘀 𝗧𝗼 𝗕𝗼𝘁",
                show_alert=True,
            )
        except Exception:
            pass

        try:
            await callback.message.delete()
        except Exception:
            pass

        user = callback.from_user
        asyncio.create_task(
            ensure_user_and_credits(user.id, user.username, user.first_name)
        )
        asyncio.create_task(
            _show_start(callback.message.chat.id, callback.bot, user)
        )
    else:
        try:
            await callback.answer(
                "𝗬𝗼𝘂 𝗛𝗮𝘃𝗲𝗻'𝘁 𝗝𝗼𝗶𝗻𝗲𝗱 𝗬𝗲𝘁 𝗣𝗹𝗲𝗮𝘀𝗲 𝗝𝗼𝗶𝗻 "
                "𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗚𝗿𝗼𝘂𝗽 𝗔𝗻𝗱 𝗟𝗼𝗴𝘀 𝗧𝗵𝗲𝗻 𝗥𝗲𝘁𝗿𝘆",
                show_alert=True,
            )
        except Exception:
            pass


def _db_conn():
    return get_db_connection()


def _ensure_user_sync(user_id, username, first_name=None):
    try:
        if not get_user(user_id):
            create_user(user_id, username or "unknown", first_name)
        if first_name:
            set_first_name(user_id, first_name)
        cr = get_user_credits(user_id)
        if not cr:
            update_credits(user_id, 150)
    except Exception as e:
        logging.error(f"ensure_user {user_id}: {e}")


async def ensure_user_and_credits(user_id, username="unknown", first_name=None):
    await asyncio.to_thread(_ensure_user_sync, user_id, username, first_name)


def _status_sync(user_id):
    conn = _db_conn()
    cur  = conn.cursor()
    plan, credits_str, joined_str = "FREE", "0", "N/A"
    try:
        cur.execute(
            "SELECT is_premium, premium_expiry, joined_at FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cur.fetchone()
        if row:
            if row['joined_at']:
                joined_str = row['joined_at'].strftime('%Y-%m-%d')
            if (
                row['is_premium'] == 1
                and row['premium_expiry']
                and datetime.datetime('now') < row['premium_expiry']
            ):
                cur.execute(
                    "SELECT plan FROM receipts WHERE user_id = ? ORDER BY purchased_on DESC LIMIT 1",
                    (user_id,)
                )
                r    = cur.fetchone()
                plan = r['plan'] if r else "Premium"
        cr          = get_user_credits(user_id)
        credits_str = str(cr if cr is not None else 0)
    except Exception as e:
        logging.error(f"status {user_id}: {e}")
        cr          = get_user_credits(user_id)
        credits_str = str(cr if cr is not None else 0)
    finally:
        conn.close()
    return credits_str, plan, joined_str


BOT_VERSION = "𝟲𝟵"

EMOJI_PHONE = "5246734896356936944"
EMOJI_PLATE = "6152176648746702128"


_MATH_ITALIC_BASE = 0x1D63C


PLAN_DISPLAY = {}
for _alias, _key in _PLAN_ALIASES.items():
    _cur = PLAN_DISPLAY.get(_key)
    if _cur is None or (_cur.isascii() and not _alias.isascii()):
        PLAN_DISPLAY[_key] = _alias


def _lnk(symbol: str) -> str:
    """Wrap a decorative symbol so it opens the dev channel when tapped."""
    return f'<a href="https://t.me/Try_Low">{symbol}</a>'


def _b(text: str) -> str:
    """Bold a whole caption line."""
    return f"<b>{text}</b>"


def _math_italic(text: str) -> str:
    """Render ASCII letters as MATHEMATICAL SANS-SERIF BOLD ITALIC capitals."""
    out = []
    for ch in text.upper():
        if "A" <= ch <= "Z":
            out.append(chr(_MATH_ITALIC_BASE + (ord(ch) - ord("A"))))
        else:
            out.append(ch)
    return "".join(out)


async def _get_profile_caption(user) -> str:
    credits_str, access_str, joined_str = await asyncio.to_thread(
        _status_sync, user.id
    )

    first_name = html.escape(str(user.first_name or "User"))

    if user.username:
        username = html.escape(user.username)
        name_link = f'<a href="https://t.me/{username}">{first_name}</a>'
    else:
        name_link = f'<a href="tg://user?id={user.id}">{first_name}</a>'

    credits_text = html.escape(str(credits_str or "0"))
    joined_text = html.escape(str(joined_str or ""))
    plan_text = html.escape(str(access_str or "FREE").strip().upper())
    dev_link = 'ＺＵＬＱＡＲ'
    divider = "━━━━━━━━━━━━━━━━━━"

    return "\n".join([
        _b('<tg-emoji emoji-id="5447381715293074599">⚠️</tg-emoji> 𝗧𝗵𝗮𝗻𝗸𝘀 𝗙𝗼𝗿 𝗖𝗼𝗺𝗶𝗻𝗴 <tg-emoji emoji-id="5447153029759397673">👍</tg-emoji>'),
        _b(divider),
        _b(f'<tg-emoji emoji-id="5447602197439218445">🌐</tg-emoji> 𝗡𝗔𝗠𝗘 ➵ {name_link}'),
        _b(f'<tg-emoji emoji-id="5444862970377040012">❤️</tg-emoji> 𝗖𝗛𝗔𝗧 ➵ <code>{user.id}</code>'),
        _b(f'<tg-emoji emoji-id="5444860552310457690">💰</tg-emoji> 𝗣𝗟𝗔𝗡 ➵ {plan_text}'),
        _b(f'<tg-emoji emoji-id="5445388803223091254">⚡️</tg-emoji> 𝗝𝗢𝗜𝗡𝗘𝗗 ➵ {joined_text}'),
        _b(f'<tg-emoji emoji-id="5445260044398524944">📋</tg-emoji> 𝗖𝗥𝗘𝗗𝗜𝗧 ➵ {credits_text}'),
        _b(divider),
        _b(f'<tg-emoji emoji-id="5280962371207077415">💎</tg-emoji> 𝗩𝗘𝗥𝗦𝗜𝗢𝗡 ➵ 𝘃{BOT_VERSION}'),
        _b(f'<tg-emoji emoji-id="5258096772776991776">⚙</tg-emoji> 𝗗𝗘𝗩 ➵ {dev_link}'),
        _b(divider),
        _b('<tg-emoji emoji-id="5447453226498552490">💳</tg-emoji> 𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗡 𝗢𝗣𝗧𝗜𝗢𝗡 <tg-emoji emoji-id="5447651546613449378">◀️</tg-emoji>'),
    ])


def mask_receipt_id(receipt_id):
    parts = receipt_id.split('-')
    if len(parts) == 3:
        m = parts[1]
        if len(m) >= 2:
            return f"{parts[0]}-{m[:2]}XX{m[4:]}-{parts[2]}"
    return receipt_id


# ══════════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════════

_MAIN_KB = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗚𝗮𝘁𝗲𝘀",
            callback_data="menu_gates",
            icon_custom_emoji_id="5445146945024720188",
        ),
        colored_button(
            "𝗣𝗹𝗮𝗻𝘀",
            callback_data="menu_price",
            icon_custom_emoji_id="5445260044398524944",
        ),
    ],
    [
        colored_button(
            "𝗦𝘂𝗽𝗽𝗼𝗿𝘁",
            url=OWNER_LINK,
            icon_custom_emoji_id="5256143829672672750",
        ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# GATES MENU
# ══════════════════════════════════════════════════════════════════

_KB_GATES = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗔𝘂𝘁𝗵",
            callback_data="menu_auth_section",
            icon_custom_emoji_id="5364021841801262907",
        ),
        colored_button(
            "𝗖𝗵𝗮𝗿𝗴𝗲",
            callback_data="menu_charge_section",
            icon_custom_emoji_id="5363858809137677324",
        ),
    ],
    [
        colored_button(
            "𝗠𝗮𝘀𝘀",
            callback_data="menu_mass",
            icon_custom_emoji_id="5363938558090425835",
        ),
        colored_button(
            "𝗛𝗶𝘁𝘁𝗲𝗿",
            callback_data="menu_hitter",
            icon_custom_emoji_id="5363839335755953463",
        ),
    ],
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="back_main",
            icon_custom_emoji_id="5271656293768118134",
        ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# AUTH SECTION
# ══════════════════════════════════════════════════════════════════

_KB_AUTH_SECTION = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗕𝗿𝗮𝗶𝗻𝘁𝗿𝗲𝗲",
            callback_data="menu_auth_braintree",
            icon_custom_emoji_id="5364021841801262907",
        ),
        colored_button(
            "𝗖𝗵𝗮𝘀𝗲",
            callback_data="menu_auth_chase",
            icon_custom_emoji_id="5363858809137677324",
        ),
    ],
    [
        colored_button(
            "𝟯𝗱𝘀 𝗟𝗼𝗼𝗸𝘂𝗽",
            callback_data="info_3ds_vbv",
            icon_custom_emoji_id="5363938558090425835",
        ),
    ],
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="menu_gates",
            icon_custom_emoji_id="5271656293768118134",
        ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# CHARGE SECTION
# ══════════════════════════════════════════════════════════════════

_KB_CHARGE_SECTION = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗦𝗵𝗼𝗽𝗶𝗳𝘆",
            callback_data="info_charge_shopify",
            icon_custom_emoji_id="5364021841801262907",
        ),
        colored_button(
            "𝗦𝘁𝗿𝗶𝗽𝗲",
            callback_data="info_charge_stripe",
            icon_custom_emoji_id="5363858809137677324",
        ),
    ],
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="menu_gates",
            icon_custom_emoji_id="5271656293768118134",
        ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# 3DS SECTION
# ══════════════════════════════════════════════════════════════════

_KB_3DS_SECTION = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="menu_auth_section",
            icon_custom_emoji_id="5271656293768118134",       # ← fill later
            ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# MASS SECTION
# ══════════════════════════════════════════════════════════════════

_KB_MASS = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗦𝗵𝗼𝗽𝗶𝗳𝘆",
            callback_data="info_mass_shopify",
            icon_custom_emoji_id="5364021841801262907",       # ← fill later
        ),
    ],
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="menu_gates",
            icon_custom_emoji_id="5271656293768118134",       # ← fill later
            ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# HITTER SECTION
# ══════════════════════════════════════════════════════════════════

_KB_HITTER = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗠𝗮𝗴𝗶𝗰𝗽𝗶𝗻",
            callback_data="info_hitter_mpin",
            icon_custom_emoji_id="5364021841801262907",       # ← fill later
        ),
        colored_button(
            "𝗦𝘁𝗿𝗶𝗽𝗲",
            callback_data="info_hitter_stripe",
            icon_custom_emoji_id="5363858809137677324",       # ← fill later
        ),
    ],
    [
        colored_button(
            "𝗪𝗵𝗼𝗽",
            callback_data="info_hitter_whop",
            icon_custom_emoji_id="5363938558090425835",       # ← fill later
        ),
        colored_button(
            "𝗝𝗶𝗼",
            callback_data="info_hitter_jio",
            icon_custom_emoji_id="5363839335755953463",       # ← fill later
        ),
    ],
    [
        InlineKeyboardButton(
            text="𝗦𝘁𝗼𝗽",
            callback_data="hitters_stop_all",
            icon_custom_emoji_id="5974083768233760323",       # ← fill later
        ),
    ],
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="menu_gates",
            icon_custom_emoji_id="5271656293768118134",       # ← fill later
            ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# PRICE WITH BUY
# ══════════════════════════════════════════════════════════════════

_KB_PRICE_WITH_BUY = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            "𝗕𝘂𝘆 𝗡𝗼𝘄",
            callback_data="menu_buy",
            icon_custom_emoji_id="5796205953913196373",       # ← fill later
        ),
    ],
    [
        colored_button(
            "𝗕𝗮𝗰𝗸",
            callback_data="back_main",
            icon_custom_emoji_id="5271656293768118134",       # ← fill later
            ),
    ],
])


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

_SEP = "━━━━━━━━━━━━━━━━"


def _back(t):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            colored_button(
                text="𝗕𝗮𝗰𝗸",
                callback_data=t,
                icon_custom_emoji_id="5271656293768118134",   # ← fill later
            ),
        ],
    ])


_KB_BACK_MASS_LOCAL = InlineKeyboardMarkup(inline_keyboard=[
    [
        colored_button(
            text="𝗕𝗮𝗰𝗸",
            callback_data="menu_mass",
            icon_custom_emoji_id="5271656293768118134",       # ← fill later
        ),
    ],
])


STATIC_MENU_MAP: dict = {
    "menu_gates"          : (
        '<tg-emoji emoji-id="5447319442562251569">🛒</tg-emoji> '
        '<b>𝗖𝗛𝗢𝗢𝗦𝗘 𝗚𝗔𝗧𝗘𝗪𝗔𝗬</b> '
        '<tg-emoji emoji-id="5260681660189408650">💎</tg-emoji>',
        _KB_GATES
    ),
    "menu_auth_section"   : (
        '<tg-emoji emoji-id="5208880351690112495">✅</tg-emoji> '
        '<b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗡 𝗔𝗨𝗧𝗛 𝗚𝗔𝗧𝗘</b> '
        '<tg-emoji emoji-id="5211182849297762045">🟢</tg-emoji>',
        _KB_AUTH_SECTION
    ),
    "menu_charge_section" : (
        '<tg-emoji emoji-id="5208514867153091900">✅</tg-emoji> '
        '<b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔 𝗖𝗛𝗔𝗥𝗚𝗘 𝗚𝗔𝗧𝗘</b> '
        '<tg-emoji emoji-id="5208942800514596941">🩷</tg-emoji>',
        _KB_CHARGE_SECTION
    ),
    "menu_3ds_section"    : ("<b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔 𝗟𝗢𝗢𝗞𝗨𝗣 𝗚𝗔𝗧𝗘</b>", _KB_3DS_SECTION),
    "menu_mass"           : (
        '<tg-emoji emoji-id="5210974045167697028">✅</tg-emoji> '
        '<b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔 𝗠𝗔𝗦𝗦 𝗚𝗔𝗧𝗘</b> '
        '<tg-emoji emoji-id="5210847498251287496">🟤</tg-emoji>',
        _KB_MASS
    ),
    "menu_hitter"         : (
        '<tg-emoji emoji-id="5208838553068387559">✅</tg-emoji> '
        '<b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗬𝗢𝗨𝗥 𝗛𝗜𝗧𝗧𝗘𝗥</b> '
        '<tg-emoji emoji-id="5208429100951159058">🔴</tg-emoji>',
        _KB_HITTER
    ),
    "menu_buy"     : (
        '<tg-emoji emoji-id="5427168083074628963">💎</tg-emoji> <b>Select Your Plan</b>\n\n'
        "<b>Pick a Plan Below, Pay Through a Secure Hosted Crypto Checkout Page.</b>",
        pay_sys.get_plan_selection_keyboard(),
    ),
    "menu_auth_braintree" : (f"{_SEP}\n<b><i>Gate ➵ Braintree Premium Auth</i></b>\n<b><i>Command ➵ /b3</i></b>\n<b><i>Sites ➵ 1</i></b>\n<b><i>Health ➵ 100%</i></b>\n{_SEP}", _back("menu_auth_section")),
    "menu_auth_chase"     : (f"{_SEP}\n<b><i>Gate ➵ Chase Auth</i></b>\n<b><i>Command ➵ /ch</i></b>\n<b><i>Sites ➵ 1</i></b>\n<b><i>Health ➵ 100%</i></b>\n{_SEP}", _back("menu_auth_section")),
    "info_3ds_vbv"        : (f"{_SEP}\n<b><i>Gate ➵ VBV Lookup</i></b>\n<b><i>Command ➵ /vbv</i></b>\n<b><i>Sites ➵ 1</i></b>\n<b><i>Health ➵ 100%</i></b>\n{_SEP}", _back("menu_auth_section")),
    "info_charge_stripe"   : (f"{_SEP}\n<b><i>Gate ➵ Stripe 1$</i></b>\n<b><i>Command ➵ /st</i></b>\n<b><i>Sites ➵ 1</i></b>\n<b><i>Health ➵ 100%</i></b>\n{_SEP}", _back("menu_charge_section")),
    "info_charge_shopify"  : (f"{_SEP}\n<b><i>Gate ➵ Shopify 1$</i></b>\n<b><i>Command ➵ /sp</i></b>\n<b><i>Health ➵ 100%</i></b>\n{_SEP}", _back("menu_charge_section")),
    "info_hitter_stripe"   : (f"{_SEP}\n<b><i>Gate ➵ Stripe Auto Hitter</i></b>\n<b><i>Command ➵ /stco</i></b>\n<b><i>Mode ➵ Automated Stripe Checking</i></b>\n<b><i>Status ➵ Available</i></b>\n{_SEP}", _back("menu_hitter")),
    "info_hitter_whop"     : (f"{_SEP}\n<b><i>Gate ➵ Whop Auto Hitter</i></b>\n<b><i>Command ➵ /hit</i></b>\n<b><i>Mode ➵ Automated Whop Checking</i></b>\n<b><i>Status ➵ Available</i></b>\n{_SEP}", _back("menu_hitter")),
    "info_hitter_jio"      : (
        f"{_SEP}\n"
        "<b><i>Gate ➵ Jio Auto Hitter</i></b>\n"
        "<b><i>Command ➵ /jio &lt;phone&gt; &lt;amount&gt; &lt;card&gt;</i></b>\n"
        "<b><i>Mode ➵ Automated Jio Checking</i></b>\n"
        "<b><i>Status ➵ Available</i></b>\n"
        f"{_SEP}\n",
        _back("menu_hitter"),
    ),
    "info_hitter_mpin"     : (
        f"{_SEP}\n"
        "<b><i>Gate ➵ Magicpin Auto Hitter</i></b>\n"
        "<b><i>Login ➵ /mpsession &lt;phone&gt; ➵ /motp &lt;otp&gt;</i></b>\n"
        "<b><i>Commands ➵ /mpl (Play 50₹) • /mzm (Zomato 500₹)</i></b>\n"
        "<b><i>Blinkit ➵ /mbl (500₹) • /mbl1 (1000₹)</i></b>\n"
        "<b><i>Mode ➵ Automated Magicpin Checking</i></b>\n"
        "<b><i>Status ➵ Available</i></b>\n"
        f"{_SEP}\n",
        _back("menu_hitter"),
    ),
    "info_mass_shopify"    : (f"{_SEP}\n<b><i>Gate ➵ Mass Shopify</i></b>\n"
                               f"<b><i>Mode ➵ Shopify Mass Checker</i></b>\n"
                               f"<b><i>Command ➵ /msp</i></b>\n"
                               f"<b><i>Status ➵ Available</i></b>\n{_SEP}",
                               _back("menu_mass")),

    "menu_price": (PRICING_TEXT, _KB_PRICE_WITH_BUY),
}


for _i in range(12, 17):
    STATIC_MENU_MAP[f"info_charge_gate{_i}"] = (
        f"{_SEP}\n<b><i>Gate ➵ Coming Soon</i></b>\n"
        f"<b><i>Status ➵ 🚧 Under Development</i></b>\n{_SEP}",
        _back("menu_charge_section")
    )


async def _edit(msg: types.Message, text: str, kb: InlineKeyboardMarkup):
    try:
        if msg.caption is not None:
            await msg.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
        else:
            await msg.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TypeError:
        pass
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            logging.warning(f"_edit: {e}")


async def _safe_answer(cb: types.CallbackQuery, text: str = "", **kw):
    try:
        await cb.answer(text, **kw)
    except Exception:
        pass


async def _start_caption(user) -> str:
    return await _get_profile_caption(user)


async def _show_start(chat_id: int, bot_instance: Bot, user=None):
    if user is None:
        return
    caption = await _start_caption(user)


    await bot_instance.send_message(
        chat_id      = chat_id,
        text         = caption,
        reply_markup = _MAIN_KB,
        parse_mode   = "HTML",
    )


@router.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    asyncio.create_task(ensure_user_and_credits(user.id, user.username, user.first_name))
    parts = (message.text or "").split(maxsplit=1)
    args = parts[1] if len(parts) > 1 else ""
    if args and "plan" in args.lower():
        from sub import _PLAN_TEXT
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="💎 Bᴜʏ Pʟᴀɴ", callback_data="menu_buy"),
        ]])
        await message.answer(text=_PLAN_TEXT, parse_mode="HTML", reply_markup=kb)
        return
    await _show_start(message.chat.id, message.bot, user)


_TRACK_USAGE = (
    "ℹ️ <b>Uꜱᴀɢᴇ</b>\n"
    "<code>/track &lt;track_id&gt;</code>\n\n"
    "Your <b>Track ID</b> is shown on your payment invoice.\n"
    "Example: <code>/track 6aab8a7cb4b72aa7f2042ff8</code>"
)


@router.message(Command("track"))
async def track_command(message: types.Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer(
            "❌ <b>This command is for the owner only.</b>",
            parse_mode="HTML",
        )
        return
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(_TRACK_USAGE, parse_mode="HTML")
        return
    info = await asyncio.to_thread(pay_sys.track_payment_info, parts[1].strip())
    if not info:
        await message.answer(
            "❌ <b>Pᴀʏᴍᴇɴᴛ ʀᴇᴄᴏʀᴅ ɴᴏᴛ ғᴏᴜɴᴅ.</b>\n\n"
            "Check the Track ID and try again.",
            parse_mode="HTML",
        )
        return

    if info.get("user_id"):
        try:
            chat = await message.bot.get_chat(info["user_id"])
            real_name = chat.first_name or chat.username
            if real_name:
                info["order_for"] = real_name
                set_first_name(info["user_id"], real_name)
        except Exception:
            pass
    await message.answer(
        pay_sys.format_track_caption(info),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


DOT_COMMAND_MAP = {
    "ch": ch_command, "st": st_command, "sp": sp_command,
    "vbv": vbv_command,
    "b3": b3_command,
    "stco": stco_command,
    "bin": binn_command, "binn": binn_command,
    "auth": auth_command, "rc": rc_command, "authall": authall_command,
    "gen_code": gen_code_command, "claim": claim_command, "info": info_command,
    "rauth": rauth_command, "plan": plan_command, "adcr": adcr_command,
    "key": key_command,
    "me": me_command, "all": all_command,
    "on": on_command, "off": off_command,
    "onall": onall_command, "offall": offall_command, "gates": gates_command,
    "gif": gif_command, "offgif": offgif_command,
    "stats": stats_command,
    "proxy": proxy_command, "checkproxy": checkproxy_command,
    "clearproxy": clearproxy_command, "myproxy": myproxy_command,
    "gproxyadd": gproxyadd_command, "gproxyclear": gproxyclear_command,
    "gproxyreload": gproxyreload_command, "gproxyinfo": gproxyinfo_command,
    "gproxyexport": gproxyexport_command,
    "checksite": checksite_command, "seturl": seturl_command,
    "siteall": siteall_command, "removeall": removeall_command,
    "dedupe": dedupe_command, "proxyinfo": proxyinfo_command,
    "resetproxy": resetproxy_command, "cmds": cmds_command,
    "fb": feedback_cmd, "broad": broad_command,
    "ban": ban_command, "unban": unban_command, "status": status_command,
    "gen": gen_command,

    "whop": whop_command, "hit": whop_command, "jio": jio_command,
    "track": track_command,

}


@router.message(F.text.regexp(r'^\.\w+'))
async def dot_command_handler(message: types.Message):
    cmd = message.text.strip().split()[0][1:].lower()
    h   = DOT_COMMAND_MAP.get(cmd)
    if h:
        await h(message)


def _setting_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Hide",
                callback_data="setting_hide",
                icon_custom_emoji_id=EMOJI_APPROVED,
            ),
            InlineKeyboardButton(
                text="Unhide",
                callback_data="setting_show",
                icon_custom_emoji_id=EMOJI_DECLINED,
            ),
        ],
        [
            InlineKeyboardButton(
                text="Close",
                callback_data="setting_close",
                icon_custom_emoji_id=EMOJI_DECLINED,
            ),
        ],
    ])


def _setting_text() -> str:
    if privacy.names_hidden():
        status = f'<tg-emoji emoji-id="{EMOJI_APPROVED}">✅</tg-emoji> Hidden'
    else:
        status = f'<tg-emoji emoji-id="{EMOJI_DECLINED}">❌</tg-emoji> Visible'
    return (
        '<b><a href="https://t.me/Try_Low">[⌭]</a> Hide Setting</b>\n'
        '━━━━━━━━━━━\n'
        f'<b>Name is ➵ {status}</b>'
    )


@router.message(Command("setting"))
async def setting_command(message: types.Message):
    is_paid, _ = get_premium_status(message.from_user.id)
    if not is_paid and message.from_user.id not in ADMIN_IDS:
        await message.reply("❌ <b>Only paid plan users can access this.</b>\n\nBuy a plan to unlock this feature.")
        return
    await message.reply(
        text=_setting_text(),
        parse_mode="HTML",
        reply_markup=_setting_kb(),
    )


@router.callback_query(F.data.in_({"setting_hide", "setting_show"}))
async def setting_callback(callback: types.CallbackQuery):
    is_paid, _ = get_premium_status(callback.from_user.id)
    if not is_paid and callback.from_user.id not in ADMIN_IDS:
        await _safe_answer(callback, "❌ Only paid plan users can access this.", show_alert=True)
        return
    hide = callback.data == "setting_hide"
    privacy.set_names_hidden(hide)
    await _safe_answer(
        callback,
        "🔒 Names are now HIDDEN in log groups." if hide else "👁 Names are now VISIBLE in log groups.",
        show_alert=True,
    )
    await _edit(callback.message, _setting_text(), _setting_kb())


@router.callback_query(F.data == "setting_close")
async def setting_close_callback(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _safe_answer(callback)


_HIT_CODE_DIRS = ("autohitters", "mass_gates", "gates")


def _stop_all_hittings() -> int:
    """Cancel every in-flight hitter/check task across all gates. Returns count."""
    current = asyncio.current_task()
    cancelled = 0
    for task in asyncio.all_tasks():
        if task is current or task.done():
            continue
        coro = task.get_coro()
        code = getattr(coro, "cr_code", None)
        if code is None:
            code = getattr(getattr(coro, "__func__", None), "__code__", None)
        filename = getattr(code, "co_filename", "") if code else ""
        if not filename:
            continue
        parts = filename.replace("\\", "/").split("/")
        if len(parts) >= 2 and parts[-2] in _HIT_CODE_DIRS:
            task.cancel()
            cancelled += 1
    return cancelled


@router.callback_query(F.data == "hitters_stop_all")
async def hitters_stop_all_callback(callback: types.CallbackQuery):
    n = _stop_all_hittings()
    logging.info(f"🛑 [STOP-ALL] cancelled {n} tasks")
    await _safe_answer(
        callback,
        f"🛑 Stopped {n} running check(s)." if n else "ℹ️ Nothing is running.",
        show_alert=True,
    )


_MASS_PREFIXES = ("mshs_", "mshr_", "stco_", "fb_", "cmds_", "mppr_", "mpps_")


@router.callback_query(lambda cb: not (cb.data or "").startswith(("pay_plan_", "pay_check_", "pay_back_plans_")))
async def button_handler(callback: types.CallbackQuery):
    data = callback.data or ""

    if data.startswith(_MASS_PREFIXES):
        return

    msg = callback.message
    if not isinstance(msg, types.Message):
        await _safe_answer(callback, "❌ Message expired. Please use /start again.", show_alert=True)
        return


    static = STATIC_MENU_MAP.get(data)
    if static is not None:
        text, kb = static
        asyncio.create_task(_safe_answer(callback))
        asyncio.create_task(_edit(msg, text, kb))
        return


    if data == "back_main":
        asyncio.create_task(_safe_answer(callback))
        try:
            caption = await _start_caption(callback.from_user)
            if msg.text is not None:
                await msg.edit_text(text=caption, reply_markup=_MAIN_KB, parse_mode="HTML")
            else:
                try:
                    await msg.delete()
                except Exception:
                    pass


                await callback.bot.send_message(
                    chat_id=msg.chat.id,
                    text=caption,
                    reply_markup=_MAIN_KB, parse_mode="HTML",
                )
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                logging.warning(f"back_main: {e}")
        return


@router.callback_query(F.data.startswith("pay_plan_"))
async def pay_plan_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    plan    = callback.data[len("pay_plan_"):]
    if plan not in pay_sys.PLANS:
        await _safe_answer(callback, "Invalid plan selected.", show_alert=True)
        return

    pay_sys.cancel_user_active_payment(user_id)
    await _safe_answer(callback, "⏳ Creating your payment page… please wait.", show_alert=True)

    payment = await asyncio.to_thread(pay_sys.create_payment, user_id, plan)
    if not payment:
        await _edit(
            callback.message,
            "❌ <b>Fᴀɪʟᴇᴅ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴘᴀʏᴍᴇɴᴛ.</b>\n"
            "Please try again or contact support.",
            pay_sys.get_plan_selection_keyboard(),
        )
        return

    pay_sys.register_payment(payment["track_id"], user_id, plan)
    pay_sys.set_user_session(user_id, plan)

    kb      = pay_sys.get_paid_button_keyboard(payment["track_id"], user_id, payment["invoice_url"])
    caption = pay_sys.format_payment_caption(payment, plan)

    await _edit(callback.message, caption, kb)

    pay_sys.start_payment_monitor(
        payment["track_id"], callback.message.chat.id,
        callback.message.message_id, False, caption,
        payment_data=payment, plan=plan, user_id=user_id,
    )


@router.callback_query(F.data.startswith("pay_check_"))
async def pay_check_callback(callback: types.CallbackQuery):
    track_id = callback.data[len("pay_check_"):]
    status = await pay_sys.manual_check_payment(track_id)
    if status in ("Paid", "Expired"):
        await _safe_answer(callback)
    else:
        await _safe_answer(
            callback,
            "⏳ Payment not detected yet.\n\n"
            "Please send the exact crypto amount to the payment page address first, "
            "then tap 'I Have Paid' again.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("pay_back_plans_"))
async def pay_back_plans_callback(callback: types.CallbackQuery):
    pay_sys.clear_user_session(callback.from_user.id)
    await _safe_answer(callback)
    await _edit(
        callback.message,
        "💎 <b>Sᴇʟᴇᴄᴛ Yᴏᴜʀ Pʟᴀɴ</b>",
        pay_sys.get_plan_selection_keyboard(),
    )


dp.callback_query.register(msh_stop_handler,         MshStopCallback.filter())
dp.callback_query.register(msh_result_handler,        MshResultCallback.filter())
dp.callback_query.register(stco_callback_handler,     F.data.startswith("stco_"))
dp.callback_query.register(whop_callback_handler,     F.data.startswith("whop_"))
dp.callback_query.register(jio_callback_handler,      F.data.startswith("jio_"))
dp.callback_query.register(regenerate_cards_callback, F.data.startswith("gen_reg"))


for _cmd, _fn in [
    ("b3", b3_command), ("ch", ch_command), ("st", st_command),
    ("sp", sp_command), ("stco", stco_command), ("vbv", vbv_command),
    ("auth", auth_command), ("rc", rc_command),
    ("authall", authall_command), ("gen_code", gen_code_command), ("claim", claim_command),
    ("info", info_command), ("rauth", rauth_command), ("plan", plan_command),
    ("adcr", adcr_command), ("key", key_command),
    ("me", me_command), ("all", all_command),
    ("on", on_command), ("off", off_command),
    ("onall", onall_command), ("offall", offall_command), ("gates", gates_command),
    ("gif", gif_command), ("offgif", offgif_command),
    ("hit", whop_command), ("jio", jio_command), ("checksite", checksite_command), ("seturl", seturl_command),
    ("siteall", siteall_command), ("removeall", removeall_command), ("dedupe", dedupe_command),
    ("proxyinfo", proxyinfo_command), ("myproxy", myproxy_command),
    ("resetproxy", resetproxy_command), ("stats", stats_command),
    ("proxy", proxy_command), ("checkproxy", checkproxy_command),
    ("clearproxy", clearproxy_command), ("myproxy", myproxy_command),
    ("gproxyadd", gproxyadd_command), ("gproxyclear", gproxyclear_command),
    ("gproxyreload", gproxyreload_command), ("gproxyinfo", gproxyinfo_command),
    ("gproxyexport", gproxyexport_command),
    ("bin", binn_command), ("binn", binn_command),
    ("gen", gen_command),
    ("whop", whop_command),
    ("track", track_command),

]:
    dp.message.register(_fn, Command(_cmd))

setup_feedback_handler(dp)


async def main():
    logging.info("Bot starting...")


    pay_sys.set_bot(bot)
    logging.info("Payment gateway: READY ✅")


    asyncio.create_task(pay_sys.apply_maintenance_compensation(bot))
    asyncio.create_task(pay_sys._maintenance_heartbeat())
    logging.info("Maintenance compensation: ARMED ✅")


    asyncio.create_task(pay_sys.resume_payments())
    logging.info("Payment recovery: STARTED ✅")


    asyncio.create_task(daily_backup_scheduler(bot))
    logging.info("Daily backup scheduler: STARTED ✅")



    asyncio.create_task(premium_expiry_worker(bot))
    logging.info("Premium expiry worker: STARTED ✅")

    await global_proxy_manager.reload()
    logging.info(f"Global proxy pool: LOADED ✅ ({global_proxy_manager.get_count()} proxies)")

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        logging.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass