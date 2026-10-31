from live_emoji import plan_badge, dev_badge


import asyncio
import logging
from faker import Faker
from html import escape


from database import get_user_credits, update_credits, PooledConn
from sub import get_premium_status


user_last_command_time = {}


SUPPORTED_LOCALES = {
    'us': ('en_US', 'United States 🇺🇸'),
    'gb': ('en_GB', 'United Kingdom 🇬🇧'),
    'fr': ('fr_FR', 'France 🇫🇷'),
    'de': ('de_DE', 'Germany 🇩🇪'),
    'es': ('es_ES', 'Spain 🇪🇸'),
    'it': ('it_IT', 'Italy 🇮🇹'),
    'jp': ('ja_JP', 'Japan 🇯🇵'),
    'in': ('en_IN', 'India 🇮🇳'),
    'au': ('en_AU', 'Australia 🇦🇺'),
    'ca': ('en_CA', 'Canada 🇨🇦'),
    'mx': ('es_MX', 'Mexico 🇲🇽'),
    'br': ('pt_BR', 'Brazil 🇧🇷'),
    'ru': ('ru_RU', 'Russia 🇷🇺'),
    'cn': ('zh_CN', 'China 🇨🇳'),
    'za': ('en_ZA', 'South Africa 🇿🇦'),
    'nl': ('nl_NL', 'Netherlands 🇳🇱'),
    'pl': ('pl_PL', 'Poland 🇵🇱'),
    'se': ('sv_SE', 'Sweden 🇸🇪'),
    'no': ('no_NO', 'Norway 🇳🇴'),
    'fi': ('fi_FI', 'Finland 🇫🇮'),
    'dk': ('da_DK', 'Denmark 🇩🇰'),
    'kr': ('ko_KR', 'South Korea 🇰🇷'),
    'tr': ('tr_TR', 'Turkey 🇹🇷'),
    'id': ('id_ID', 'Indonesia 🇮🇩'),
    'th': ('th_TH', 'Thailand 🇹🇭'),
    'vn': ('vi_VN', 'Vietnam 🇻🇳'),
    'gr': ('el_GR', 'Greece 🇬🇷'),
    'cz': ('cs_CZ', 'Czech Republic 🇨🇿'),
    'hu': ('hu_HU', 'Hungary 🇭🇺'),
    'ro': ('ro_RO', 'Romania 🇷🇴'),
    'ar': ('ar_SA', 'Saudi Arabia 🇸🇦'),
    'il': ('he_IL', 'Israel 🇮🇱'),
    'pt': ('pt_PT', 'Portugal 🇵🇹'),
    'bg': ('bg_BG', 'Bulgaria 🇧🇬'),
    'ua': ('uk_UA', 'Ukraine 🇺🇦'),
    'pk': ('en_PK', 'Pakistan 🇵🇰'),
    'ph': ('tl_PH', 'Philippines 🇵🇭'),
    'eg': ('ar_EG', 'Egypt 🇪🇬'),
    'cl': ('es_CL', 'Chile 🇨🇱'),
    'tw': ('zh_TW', 'Taiwan 🇹🇼'),
    'sa': ('ar_SA', 'Saudi Arabia 🇸🇦'),
    'np': ('ne_NP', 'Nepal 🇳🇵'),
    'bd': ('bn_BD', 'Bangladesh 🇧🇩'),
    'ae': ('ar_AE', 'United Arab Emirates 🇦🇪'),
    'bh': ('ar_BH', 'Bahrain 🇧🇭'),
    'jo': ('ar_JO', 'Jordan 🇯🇴'),
    'iq': ('ar_IQ', 'Iraq 🇮🇶'),
    'ps': ('ar_PS', 'Palestine 🇵🇸')
}


def ensure_fake_stats_columns():
    """Ensures fake stats columns exist in users table."""
    try:
        with PooledConn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN fake_generated INTEGER DEFAULT 0")
            except Exception:
                pass
            conn.commit()
        logging.info("[FAKE] Stats columns checked.")
    except Exception as e:
        logging.error(f"[FAKE] Error checking stats columns: {e}")


ensure_fake_stats_columns()


async def update_fake_stats(user_id: int):
    """Increment fake_generated counter for user."""
    def _sync_update():
        try:
            with PooledConn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET fake_generated = fake_generated + 1 WHERE user_id = %s",
                    (user_id,)
                )
                conn.commit()
        except Exception as e:
            logging.error(f"[FAKE] Error updating fake stats: {e}")

    await asyncio.to_thread(_sync_update)


async def get_user_plan_name(user_id: int) -> str:
    """Fetches the specific plan name from receipts if premium, else Trial."""
    premium_result = await asyncio.to_thread(get_premium_status, user_id)
    is_premium = premium_result[0] if isinstance(premium_result, tuple) else False

    if is_premium:
        try:
            def _sync_fetch():
                with PooledConn() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT plan FROM receipts WHERE user_id = %s ORDER BY purchased_on DESC LIMIT 1",
                        (user_id,)
                    )
                    row = cursor.fetchone()
                    return row[0].upper() if row else "PREMIUM"

            return await asyncio.to_thread(_sync_fetch)
        except Exception as e:
            logging.error(f"[FAKE] Error fetching plan name: {e}")
        return "PREMIUM"
    else:
        return "FREE"


def generate_fake_identity(country_code: str):
    """Generate fake identity details for given country code."""
    locale, country_name = SUPPORTED_LOCALES.get(country_code, ('en_US', 'United States 🇺🇸'))

    fake = Faker(locale)


    fake_name = fake.name()
    fake_gender = fake.random_element(elements=("Male", "Female"))
    fake_address = fake.street_address() if hasattr(fake, "street_address") else "N/A"
    fake_city = fake.city() if hasattr(fake, "city") else "N/A"
    fake_state = fake.state() if hasattr(fake, "state") else "N/A"
    fake_zipcode = fake.postcode() if hasattr(fake, "postcode") else "N/A"
    fake_phone = fake.phone_number() if hasattr(fake, "phone_number") else "N/A"


    fake_email = fake.email() if hasattr(fake, "email") else f"{fake_name.lower().replace(' ', '.')}@example.com"


    fake_dob = fake.date_of_birth(minimum_age=18, maximum_age=80) if hasattr(fake, "date_of_birth") else "N/A"

    return {
        "name": fake_name,
        "gender": fake_gender,
        "address": fake_address,
        "city": fake_city,
        "state": fake_state,
        "zipcode": fake_zipcode,
        "phone": fake_phone,
        "email": fake_email,
        "dob": fake_dob.strftime("%Y-%m-%d") if fake_dob != "N/A" else "N/A",
        "country": country_name
    }


async def process_fake_generation(message, proc_msg, user, user_id, country_code, plan_name):
    """Generate fake identity, deduct credits, update stats, and send results."""


    try:
        identity = await asyncio.to_thread(generate_fake_identity, country_code)
        logging.info(f"[FAKE] Identity generated for {user_id} with country {country_code}")
    except Exception as e:
        logging.error(f"[FAKE] Generation error: {e}")
        identity = {
            "name": "Error",
            "gender": "N/A",
            "address": "N/A",
            "city": "N/A",
            "state": "N/A",
            "zipcode": "N/A",
            "phone": "N/A",
            "email": "N/A",
            "dob": "N/A",
            "country": "N/A"
        }


    current_balance = await asyncio.to_thread(get_user_credits, user_id)
    new_balance = max(0, current_balance - 1)
    await asyncio.to_thread(update_credits, user_id, new_balance)


    await update_fake_stats(user_id)


    user_link = f'<a href="tg://user?id={user.id}">{escape(user.first_name)}</a>'
    dev_link = dev_badge()
    user_display = f"{user_link} {plan_badge(plan_name)}"


    country_display = SUPPORTED_LOCALES.get(country_code, ('en_US', 'United States 🇺🇸'))[1]

    final_caption = (
        f"<b>𝐅𝐚𝐤𝐞 𝐈𝐝𝐞𝐧𝐭𝐢𝐭𝐲 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>𝐅𝐮𝐥𝐥 𝐍𝐚𝐦𝐞</b> ➺ <code>{identity['name']}</code>\n"
        f"<b>𝐆𝐞𝐧𝐝𝐞𝐫</b> ➺ <code>{identity['gender']}</code>\n"
        f"<b>𝐃𝐚𝐭𝐞 𝐨𝐟 𝐁𝐢𝐫𝐭𝐡</b> ➺ <code>{identity['dob']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>𝐒𝐭𝐫𝐞𝐞𝐭 𝐀𝐝𝐝𝐫𝐞𝐬𝐬</b> ➺ <code>{identity['address']}</code>\n"
        f"<b>𝐂𝐢𝐭𝐲/𝐓𝐨𝐰𝐧</b> ➺ <code>{identity['city']}</code>\n"
        f"<b>𝐒𝐭𝐚𝐭𝐞/𝐏𝐫𝐨𝐯𝐢𝐧𝐜𝐞</b> ➺ <code>{identity['state']}</code>\n"
        f"<b>𝐏𝐨𝐬𝐭𝐚𝐥 𝐂𝐨𝐝𝐞</b> ➺ <code>{identity['zipcode']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>𝐏𝐡𝐨𝐧𝐞 𝐍𝐮𝐦𝐛𝐞𝐫</b> ➺ <code>{identity['phone']}</code>\n"
        f"<b>𝐄𝐦𝐚𝐢𝐥 𝐀𝐝𝐝𝐫𝐞𝐬𝐬</b> ➺ <code>{identity['email']}</code>\n"
        f"<b>𝐂𝐨𝐮𝐧𝐭𝐫𝐲</b> ➺ <code>{country_display}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>𝐔𝐬𝐞𝐫</b> ➺ {user_display}\n"
        f"<b>𝐃𝐞𝐯</b> ➺ {dev_link}"
    )


    try:
        await proc_msg.edit_text(
            text=final_caption,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"[FAKE] Error editing message: {e}")
        await message.reply(
            text=final_caption,
            parse_mode="HTML",
            disable_web_page_preview=True
        )


    await message.reply(final_caption, parse_mode="HTML", disable_web_page_preview=True)
