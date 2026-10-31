import asyncio
import os
import collections
import logging
from html import escape


from aiogram import types, F, Router


router = Router()


def get_leaderboard_data():
    """
    Reads the retained mass-gate hit log to count hits per user.
    Returns a sorted list of top users.
    """

    counts = collections.Counter()


    user_details = {}


    files_to_check = ["mshh.txt"]

    for filename in files_to_check:
        if not os.path.exists(filename):
            continue

        try:
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue


                    parts = line.split("|")
                    if len(parts) >= 3:
                        user_id = parts[0]
                        username = parts[1]
                        first_name = parts[2]


                        counts[user_id] += 1


                        if user_id not in user_details:

                            safe_username = username if username and username != "None" else None
                            safe_fname = first_name if first_name and first_name != "Unknown" else "Unknown"

                            user_details[user_id] = {
                                "username": safe_username,
                                "first_name": safe_fname
                            }
        except Exception as e:
            logging.error(f"Error reading {filename}: {e}")
            continue


    top_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return top_users, user_details


@router.message(F.text.startswith("/stats"))
async def stats_command(message: types.Message):
    """
    Displays the top 10 users ranked by total Charged cards.
    Pulls data from the retained mass-gate hit log.
    """


    status_msg = await message.answer("⏳ <b>Fᴇᴛᴄʜɪɴɢ Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ...</b>", parse_mode="HTML")

    try:

        top_users, user_details = await asyncio.to_thread(get_leaderboard_data)


        if not top_users:
            text = (
                '<tg-emoji emoji-id="5893376775781617954">🏆</tg-emoji><b> Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ (Cʜᴀʀɢᴇᴅ)</b>\n'
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "No charged cards found yet.\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Dᴇᴠ</b> ➺ <a href='https://t.me/Try_Low'>ＺＵＬＱＡＲ</a> <tg-emoji emoji-id=\"5260681660189408650\">🏆</tg-emoji>"
            )
        else:
            header = (
                '<tg-emoji emoji-id="5893376775781617954">🏆</tg-emoji><b> Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ (Cʜᴀʀɢᴇᴅ)</b>\n'
                "━━━━━━━━━━━━━━━━━━━━━\n"
            )


            bold_serif_numbers = {
                4: "𝟰.", 5: "𝟱.", 6: "𝟲.", 7: "𝟳.", 8: "𝟴.", 9: "𝟵.", 10: "𝟭𝟬."
            }

            list_text = ""
            for index, (user_id, count) in enumerate(top_users, 1):

                details = user_details.get(user_id, {})
                fname = details.get('first_name', 'Unknown')
                uname = details.get('username')


                if uname:
                    user_link = f'<a href="https://t.me/{escape(uname)}">{escape(fname)}</a>'
                else:
                    user_link = f'<a href="tg://user?id={user_id}">{escape(fname)}</a>'


                if index == 1:
                    medal = '<tg-emoji emoji-id="6269400956387987689">🥇</tg-emoji>'
                elif index == 2:
                    medal = '<tg-emoji emoji-id="5767304320114498155">🥈</tg-emoji>'
                elif index == 3:
                    medal = '<tg-emoji emoji-id="5764928223947267454">🥉</tg-emoji>'
                else:
                    medal = bold_serif_numbers.get(index, f"{index}.")

                list_text += f"{medal} {user_link} ➺ <b>{count} <tg-emoji emoji-id='5427168083074628963'>🏆</tg-emoji></b>\n"

            footer = (
                "━━━━━━━━━━━━━━━━━━━━━\n"
                '<tg-emoji emoji-id="5260681660189408650">🏆</tg-emoji> <b>Dᴇᴠ</b> ➺ ＺＵＬＱＡＲ'
            )

            text = header + list_text + footer


        await status_msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Error in /stats command: {e}")
        await status_msg.edit_text("❌ <b>Error fetching stats.</b>", parse_mode="HTML")
