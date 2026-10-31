import asyncio
import logging
import uuid
from html import escape
from typing import Any, Dict, List, Optional

from aiogram import types, Router, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument,
)


ADMIN_IDS = {7963961151, 8880615460}
FEEDBACK_CHANNEL = -1003744006874

router = Router()


_MEDIA_GROUPS: Dict[str, List[types.Message]] = {}

class MediaGroupCollectorMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: Dict[str, Any]):
        gid = getattr(event, "media_group_id", None)
        if gid:
            bucket = _MEDIA_GROUPS.setdefault(gid, [])

            existing_ids = {m.message_id for m in bucket}
            if event.message_id not in existing_ids:
                bucket.append(event)


            async def cleanup_group():
                await asyncio.sleep(3)
                _MEDIA_GROUPS.pop(gid, None)

            asyncio.create_task(cleanup_group())


        return await handler(event, data)

router.message.middleware(MediaGroupCollectorMiddleware())


_PENDING: dict = {}


def _detect_media(msg: types.Message) -> str:
    """Returns media type string for a single message."""
    if msg.photo:       return "photo"
    if msg.video:       return "video"
    if msg.animation:   return "animation"
    if msg.document:    return "document"
    return "text"

def _get_file_id(msg: types.Message) -> Optional[str]:
    """Returns the primary file_id from a message, or None."""
    if msg.photo:       return msg.photo[-1].file_id
    if msg.video:       return msg.video.file_id
    if msg.animation:   return msg.animation.file_id
    if msg.document:    return msg.document.file_id
    return None

def _get_caption_or_text(msg: types.Message) -> str:
    """Get caption or text from message."""
    return (msg.caption or msg.text or "").strip()


def _admin_info_text(user: types.User, media_type: str, count: int) -> str:
    """Create admin notification text with user info."""
    username_part = f"@{user.username}" if user.username else "N/A"
    user_link     = f'<a href="tg://user?id={user.id}">{escape(user.first_name)}</a>'


    if media_type == "photo_album":
        media_label = f"📸 Album ({count} photos)"
    elif count > 1:
        media_label = f"{count}× {media_type}"
    else:
        media_emoji = {
            "photo": "📷 Photo",
            "video": "🎥 Video",
            "animation": "🎬 GIF",
            "document": "📄 Document",
            "text": "📝 Text"
        }.get(media_type, media_type)
        media_label = media_emoji

    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><tg-emoji emoji-id=\"5465465194056525619\">👍</tg-emoji> NEW FEEDBACK</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>👤 User ➠</b> {user_link}\n"
        f"<b>🆔 User ID ➠</b> <code>{user.id}</code>\n"
        f"<b>📛 Username ➠</b> {username_part}\n"
        f"<b>🎯 Media:</b> {media_label}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def _admin_keyboard(pid: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for admin approval."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"fb_approve_{pid}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"fb_reject_{pid}"),
        ]
    ])

def _channel_caption(user: types.User, hit_text: str) -> str:
    """Create caption for channel post."""

    user_display = user.first_name or user.last_name or user.username or "User"
    user_link = f'<a href="tg://user?id={user.id}">{escape(user_display)}</a>'
    note_part = hit_text if hit_text else "—"

    return (
        f'<b><tg-emoji emoji-id=\"5956561749070057536\">👍</tg-emoji> Nᴇᴡ Fᴇᴇᴅʙᴀᴄᴋ</b>\n'
        f'<b>━━━━━━━━━━━━</b>\n'
        f'<b><tg-emoji emoji-id=\"5445174334031166029\">😵</tg-emoji> Usᴇʀ ➺</b> {user_link}\n'
        f'<b><tg-emoji emoji-id=\"5445358884480916784\">😎</tg-emoji> ID ➺</b> {user.id}\n'
        f'<b><tg-emoji emoji-id=\"5445344161333015312\">⭐️</tg-emoji> Mᴇssᴀɢᴇ ➺ {note_part}</b>\n'
    )

def _build_input_media(msg: types.Message, caption: str = "", parse_mode: str = "HTML") -> Optional[Any]:
    """Build an InputMedia* object for send_media_group."""
    fid = _get_file_id(msg)
    if not fid:
        return None

    mtype = _detect_media(msg)
    if mtype == "photo":
        return InputMediaPhoto(media=fid, caption=caption or None, parse_mode=parse_mode if caption else None)
    elif mtype == "video":
        return InputMediaVideo(media=fid, caption=caption or None, parse_mode=parse_mode if caption else None)
    elif mtype == "animation":

        return InputMediaDocument(media=fid, caption=caption or None, parse_mode=parse_mode if caption else None)
    elif mtype == "document":
        return InputMediaDocument(media=fid, caption=caption or None, parse_mode=parse_mode if caption else None)
    return None


async def cleanup_old_pending():
    """Clean up old pending feedbacks (older than 1 hour)."""
    while True:
        await asyncio.sleep(3600)
        current_time = asyncio.get_event_loop().time()
        expired = []
        for pid, data in _PENDING.items():
            if current_time - data.get("timestamp", 0) > 3600:
                expired.append(pid)
        for pid in expired:
            _PENDING.pop(pid, None)
            logging.info(f"[fb] Cleaned up expired pending feedback: {pid}")

async def start_cleanup_tasks():
    """Start all cleanup tasks (call this after bot is running)."""
    asyncio.create_task(cleanup_old_pending())
    logging.info("[fb] Cleanup tasks started")


@router.message(Command("fb"))
async def feedback_cmd(message: types.Message):
    """
    Reply to any hit message with /fb to submit it as feedback.
    Supports: single photo, video, GIF/animation, document, text, or photo albums (up to 10).
    """

    if not message.reply_to_message:
        await message.reply(
            "<b>❌ Usage:</b> <i>Reply to your hit message with /fb</i>",
            parse_mode="HTML"
        )
        return

    replied = message.reply_to_message
    user = message.from_user


    confirm_msg = await message.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>✅ Fᴇᴇᴅʙᴀᴄᴋ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>\n"
        "<i>Tʜᴀɴᴋ Yᴏᴜ Fᴏʀ Yᴏᴜʀ Fᴇᴇᴅʙᴀᴄᴋ! </i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )


    async def auto_delete():
        await asyncio.sleep(3)
        try:
            await confirm_msg.delete()
            await message.delete()
        except:
            pass

    asyncio.create_task(auto_delete())


    gid = getattr(replied, "media_group_id", None)
    if gid:

        await asyncio.sleep(0.5)
        group_msgs = list(_MEDIA_GROUPS.get(gid, [replied]))

        group_msgs.sort(key=lambda m: m.message_id)

        group_msgs = group_msgs[:10]


        is_photo_album = all(msg.photo for msg in group_msgs)
        media_type = "photo_album" if is_photo_album and len(group_msgs) > 1 else "mixed_album"
        hit_text = _get_caption_or_text(replied)
    else:
        group_msgs = [replied]
        media_type = _detect_media(replied)
        hit_text = _get_caption_or_text(replied)


    pid = uuid.uuid4().hex[:10]
    _PENDING[pid] = {
        "messages": group_msgs,
        "media_type": media_type,
        "hit_text": hit_text,
        "user": user,
        "timestamp": asyncio.get_event_loop().time(),
    }

    admin_text = _admin_info_text(user, media_type, len(group_msgs))


    async def forward_messages_to_admin():
        """Forward all messages to each admin with error handling."""
        for msg in group_msgs:
            for admin_id in sorted(ADMIN_IDS):
                try:
                    await message.bot.forward_message(
                        chat_id=admin_id,
                        from_chat_id=msg.chat.id,
                        message_id=msg.message_id
                    )
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logging.warning(f"[fb] Could not forward message {msg.message_id} to {admin_id}: {e}")
    async def send_admin_info():
        """Send admin notification with approval buttons to each admin."""
        for admin_id in sorted(ADMIN_IDS):
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode="HTML",
                    reply_markup=_admin_keyboard(pid),
                    disable_web_page_preview=True
                )
                logging.info(f"[fb] Pending {pid} sent to admin {admin_id} for user {user.id} ({media_type}, {len(group_msgs)} item(s))")
            except Exception as e:
                logging.error(f"[fb] Admin notify error for {admin_id}: {e}")
    await asyncio.gather(
        forward_messages_to_admin(),
        send_admin_info()
    )


@router.callback_query(F.data.startswith("fb_approve_"))
async def fb_approve(callback: types.CallbackQuery):
    """Handle admin approval of feedback."""

    await callback.answer("✅ Approving feedback...")


    try:
        await callback.message.edit_text(
            "<b>✅ Approved — Posting to channel...</b>",
            parse_mode="HTML"
        )
    except:
        pass

    pid = callback.data.replace("fb_approve_", "")
    entry = _PENDING.pop(pid, None)

    if not entry:
        await callback.message.edit_text(
            "<b>⚠️ Expired — Feedback already handled or bot restarted.</b>",
            parse_mode="HTML"
        )
        return

    user = entry["user"]
    msgs = entry["messages"]
    media_type = entry["media_type"]
    hit_text = entry["hit_text"]
    caption = _channel_caption(user, hit_text)

    try:

        if media_type == "photo_album" and len(msgs) > 1:

            media_items = []
            for i, msg in enumerate(msgs):
                inp = _build_input_media(msg, caption=caption if i == 0 else "")
                if inp:
                    media_items.append(inp)

            if media_items:
                await callback.bot.send_media_group(
                    chat_id=FEEDBACK_CHANNEL,
                    media=media_items
                )
            else:

                await callback.bot.forward_message(
                    chat_id=FEEDBACK_CHANNEL,
                    from_chat_id=msgs[0].chat.id,
                    message_id=msgs[0].message_id
                )

        elif media_type == "photo":
            file_id = _get_file_id(msgs[0])
            if file_id:
                await callback.bot.send_photo(
                    chat_id=FEEDBACK_CHANNEL,
                    photo=file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await callback.bot.send_message(
                    chat_id=FEEDBACK_CHANNEL,
                    text=caption,
                    parse_mode="HTML"
                )

        elif media_type == "video":
            file_id = _get_file_id(msgs[0])
            if file_id:
                await callback.bot.send_video(
                    chat_id=FEEDBACK_CHANNEL,
                    video=file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await callback.bot.send_message(
                    chat_id=FEEDBACK_CHANNEL,
                    text=caption,
                    parse_mode="HTML"
                )

        elif media_type == "animation":
            file_id = _get_file_id(msgs[0])
            if file_id:
                await callback.bot.send_animation(
                    chat_id=FEEDBACK_CHANNEL,
                    animation=file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await callback.bot.send_message(
                    chat_id=FEEDBACK_CHANNEL,
                    text=caption,
                    parse_mode="HTML"
                )

        elif media_type == "document":
            file_id = _get_file_id(msgs[0])
            if file_id:
                await callback.bot.send_document(
                    chat_id=FEEDBACK_CHANNEL,
                    document=file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await callback.bot.send_message(
                    chat_id=FEEDBACK_CHANNEL,
                    text=caption,
                    parse_mode="HTML"
                )

        elif media_type == "mixed_album":

            for i, msg in enumerate(msgs):
                file_id = _get_file_id(msg)
                if file_id:
                    msg_type = _detect_media(msg)
                    item_caption = caption if i == 0 else ""

                    if msg_type == "photo":
                        await callback.bot.send_photo(
                            chat_id=FEEDBACK_CHANNEL,
                            photo=file_id,
                            caption=item_caption,
                            parse_mode="HTML" if item_caption else None
                        )
                    elif msg_type == "video":
                        await callback.bot.send_video(
                            chat_id=FEEDBACK_CHANNEL,
                            video=file_id,
                            caption=item_caption,
                            parse_mode="HTML" if item_caption else None
                        )
                    elif msg_type == "animation":
                        await callback.bot.send_animation(
                            chat_id=FEEDBACK_CHANNEL,
                            animation=file_id,
                            caption=item_caption,
                            parse_mode="HTML" if item_caption else None
                        )
                    elif msg_type == "document":
                        await callback.bot.send_document(
                            chat_id=FEEDBACK_CHANNEL,
                            document=file_id,
                            caption=item_caption,
                            parse_mode="HTML" if item_caption else None
                        )
                    await asyncio.sleep(0.2)

        else:
            await callback.bot.send_message(
                chat_id=FEEDBACK_CHANNEL,
                text=caption,
                parse_mode="HTML",
                disable_web_page_preview=True
            )


        await callback.message.edit_text(
            "<b>✅ Approved — Posted to channel successfully!</b>",
            parse_mode="HTML"
        )

        logging.info(f"[fb] Approved and posted for user {user.id} ({media_type}, {len(msgs)} item(s))")

    except Exception as e:
        logging.error(f"[fb] Approve post error: {e}")
        try:
            await callback.message.edit_text(
                f"<b>❌ Approval failed:</b>\n<code>{str(e)[:200]}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("fb_reject_"))
async def fb_reject(callback: types.CallbackQuery):
    """Handle admin rejection of feedback."""
    await callback.answer("❌ Feedback rejected")

    pid = callback.data.replace("fb_reject_", "")
    entry = _PENDING.pop(pid, None)

    if entry:
        user = entry["user"]
        logging.info(f"[fb] Rejected feedback {pid} from user {user.id}")

    await callback.message.edit_text(
        "<b>❌ Rejected — Feedback declined</b>",
        parse_mode="HTML"
    )


def setup_feedback_handler(dispatcher):
    """Setup function for compatibility with existing code."""
    logging.info("[fb] Feedback handler router is ready")

    return router


__all__ = ['setup_feedback_handler', 'router', 'start_cleanup_tasks']
