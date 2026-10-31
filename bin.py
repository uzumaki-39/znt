import aiohttp


BINLIST_URL = "https://bins.antipublic.cc/bins/{}"

async def get_bin_info(bin_number: str) -> dict:
    """
    Fetch BIN information from the antipublic.cc API.
    """
    if not bin_number.isdigit() or len(bin_number) < 6:
        return {"error": "Invalid BIN. Must be at least 6 digits."}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BINLIST_URL.format(bin_number)) as resp:
                if resp.status == 429:
                    return {"error": "Rate limit exceeded. Try again later."}
                if resp.status == 404:
                    return {"error": "BIN not found."}
                if resp.status != 200:
                    return {"error": f"API request failed (status {resp.status})"}

                data = await resp.json()


                return {
                    "bin": data.get("bin"),
                    "length": "N/A",
                    "luhn": "N/A",
                    "scheme": data.get("brand"),
                    "type": data.get("type"),
                    "brand": data.get("level"),
                    "bank": data.get("bank"),
                    "bank_phone": "N/A",
                    "bank_url": "N/A",
                    "country": data.get("country_name"),
                    "country_emoji": data.get("country_flag"),
                }
        except Exception as e:
            return {"error": f"Exception: {str(e)}"}
