# -*- coding: utf-8 -*-
"""
🌍 ربات «جنگ جهانی ✦ امپراتوری» — نسخه‌ی تلگرام (آپدیت بزرگ)
════════════════════════════════════════════════════════════
بازی استراتژیک چندنفره: هر بازیکن رهبر یک کشور واقعیه (~۱۹۶ کشور).

✦ تجهیزات واقعی هر کشور: هر کشور تجهیزات ساخت خودش رو آزاد می‌خره؛ برای تجهیزات کشورهای دیگه
  باید «مجوز» بگیره: 🔓 دائمی | 💰 در ازای پول (زمان‌دار) | 🔢 عددی (مثلاً ۱۰۰ عدد) — یا بازار سیاه با ریسک.
✦ پک‌های ویژه (تومانی) با فعال‌سازی ادمین برای هر کشور + گزارش خودکار توی کانال
✦ حقوق/درآمد چند برابر، صنایع و معادن (کارخانه، نفت، طلا، ...)، منابع و بازار منابع
✦ ساخت‌وساز: شهر، کافه، پارک، موزه، دانشگاه، فرودگاه ...، ابرپروژه‌ها (شگفتی‌های جهان)
✦ بانک (سپرده و وام)، ارز دیجیتال (خرید/فروش + ماینر)، سیاست‌های داخلی، ماموریت‌های روزانه
✦ اتحادها (ائتلاف بزرگ): خزانه، سطح، افسر، جنگ اتحادی، کمک دفاعی | تحریم | عملیات سایبری و جاسوسی
✦ هر گزارش توی کانال با عکس مربوطه؛ بیانیه‌ی عکس‌دار؛ ادمین برای هر نوع گزارش عکس تنظیم می‌کنه
✦ پنل ادمین: تغییر پول/منابع هر کشور، فعال‌سازی پک، مجوزها، عکس‌ها، بازار و بانک، قوانین

راه‌اندازی:
  1) pip install requests pillow                 (pillow برای ساخت خودکار عکس گزارش‌هاست؛ اختیاری)
  2) توی تلگرام به @BotFather پیام بده، بات بساز و توکن بگیر
  3) BOT_TOKEN="توکن" python main.py
  4) بات رو «ادمین کانال» کن (دسترسی ارسال پیام).
"""
import io
import json
import hmac
import base64
import zlib
from collections import defaultdict, deque
import math
import os
import queue
import random
import re
import socket
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

try:  # برای ساخت خودکار عکس گزارش‌ها (اختیاری)
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except Exception:  # noqa: BLE001
    Image = ImageDraw = ImageFont = ImageFilter = None

# ═════════════ تنظیمات (فقط همین بخش رو عوض کن) ═════════════
TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")  # توکن از @BotFather تلگرام
ADMIN_IDS = ["6015642359", "8043789696", "7497407553"]  # ادمین‌های اصلی
CHANNEL = "@WorldWar_Empire"         # کانال (ربات باید ادمین کانال باشه)
CHANNEL_USERNAME = CHANNEL.lstrip("@")
ADMIN_USERNAME = ""                  # (اختیاری) آیدی تلگرام ادمین برای نمایش، بدون @
API_HOST = os.environ.get("API_HOST", "https://api.telegram.org")
ADMIN_CODE = "EMPIRE-1352-ADMIN"  # کد ورود ادمین؛ برای امنیت، مخزن را خصوصی نگه دار
DATA_FILE = os.environ.get("WW_DATA", "ww_tg_data.json")
# محدودیت‌های محافظه‌کارانه برای کاهش فشار API و جلوگیری از Flood Limit تلگرام
API_GLOBAL_GAP = max(0.05, min(1.0, float(os.environ.get("WW_API_GLOBAL_GAP", "0.06"))))
API_PRIVATE_GAP = max(1.0, min(5.0, float(os.environ.get("WW_API_PRIVATE_GAP", "1.10"))))
API_GROUP_GAP = max(3.0, min(10.0, float(os.environ.get("WW_API_GROUP_GAP", "3.20"))))
USER_BURST_COUNT = max(3, min(20, int(os.environ.get("WW_USER_BURST_COUNT", "8"))))
USER_BURST_WINDOW = max(5, min(60, int(os.environ.get("WW_USER_BURST_WINDOW", "10"))))
USER_MINUTE_LIMIT = max(USER_BURST_COUNT, min(120, int(os.environ.get("WW_USER_MINUTE_LIMIT", "40"))))
ATTACK_COOLDOWN = int(os.environ.get("WW_COOLDOWN", "180"))  # ثانیه بین دو حمله
STATEMENT_COOLDOWN = 180                                      # ثانیه بین دو بیانیه
IMG_DIR = os.environ.get("WW_IMAGES", "ww_images")            # (اختیاری) پوشه‌ی عکس گزارش‌ها: war.jpg, peace.png ...
INCOME_MULT = float(os.environ.get("WW_INCOME", "10"))      # ضریب حقوق/درآمد (۱۰ = ده برابر نسخه‌ی قبل)
# ═════════════════════════════════════════════════════════════

try:  # فقط IPv4؛ روی بعضی شبکه‌ها IPv6 باعث تأخیر چند ده ثانیه‌ای می‌شه
    import urllib3.util.connection as _u3c
    _u3c.allowed_gai_family = lambda: socket.AF_INET
except Exception:  # noqa: BLE001
    pass
_TL = threading.local()


# ═════════════ ابزارها ═════════════
FA2EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def en_digits(s):
    return str(s).translate(FA2EN)


def squash(s):
    s = en_digits(s).lower().replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"[\W_]+", "", s)


def num(s):
    s = en_digits(s).replace(",", "").replace("٬", "").replace("،", "").strip()
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def m(n):
    n = float(n)
    if abs(n) >= 100 or n == int(n):
        return "{:,}".format(int(round(n)))
    if abs(n) < 1:
        return "{:.3g}".format(n)
    return "{:,.1f}".format(n)


def flag(iso):
    if len(iso) == 2 and iso.isascii() and iso.isalpha():
        return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in iso.upper())
    return "🏳️"


def dur(sec):
    sec = max(0, int(sec))
    h, r = divmod(sec, 3600)
    mi = r // 60
    if h:
        return "%d ساعت و %d دقیقه" % (h, mi)
    return ("%d دقیقه" % mi) if mi else ("%d ثانیه" % sec)


def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def now():
    return time.time()


def split_text(text, n=3800):
    parts, cur = [], ""
    for line in text.split("\n"):
        while len(line) > n:
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:n])
            line = line[n:]
        if cur and len(cur) + len(line) + 1 > n:
            parts.append(cur)
            cur = line
        else:
            cur = (cur + "\n" + line) if cur else line
    if cur or not parts:
        parts.append(cur or "…")
    return parts


# ═════════════ داده‌های بازی ═════════════
CAT_LABEL = {
    "gnd": "🪖 زمینی", "fighter": "✈️ جنگنده", "bomber": "🛩 بمب‌افکن", "heli": "🚁 بالگرد",
    "drone": "🛸 پهپاد", "aa": "🛡 پدافند", "navy": "🚢 ناوگان", "missile": "🚀 موشک",
    "bomb": "💣 بمب", "nuke": "☢️ هسته‌ای", "cyber": "💻 سایبری",
}
SHOP = {
    "🪖 زمینی": ["gnd"],
    "✈️ هوایی": ["fighter", "bomber", "heli", "drone"],
    "🛡 پدافند": ["aa"],
    "🚢 دریایی": ["navy"],
    "🚀 موشک و بمب": ["missile", "bomb"],
    "☢️ هسته‌ای": ["nuke"],
    "💻 سایبری": ["cyber"],
}

# (کلید، دسته، نام، قیمت میلیون‌دلار، سطح تکنولوژی لازم، سهم حمله از قدرت، کشور(های) سازنده)
# سازنده "*" = تجهیز عمومی که همه آزادانه می‌خرن. هر کشور تجهیزات ساخت خودش رو آزاد می‌خره؛
# تجهیزات سازنده‌های دیگه فقط با «مجوز» (دائمی / در ازای پول / عددی) یا بازار سیاه.
UNITS = [
    # ───── زمینی ─────
    ("inf", "gnd", "پیاده‌نظام (تیپ)", 15, 1, .35, "*"),
    ("sof", "gnd", "نیروی ویژه (SOF)", 35, 2, .6, "*"),
    ("soldier", "gnd", "سرباز (Soldier)", 0.01, 1, .35, "*"),
    ("t72", "gnd", "تانک T-72B3", 4, 1, .55, "RU"),
    ("t80", "gnd", "تانک T-80BVM", 5, 2, .55, "RU"),
    ("t90", "gnd", "تانک T-90M", 6, 2, .55, "RU"),
    ("t14", "gnd", "تانک T-14 Armata", 12, 5, .6, "RU"),
    ("bmp3", "gnd", "نفربر BMP-3", 3.5, 2, .5, "RU"),
    ("btr82", "gnd", "نفربر BTR-82A", 1.5, 1, .4, "RU"),
    ("msta", "gnd", "توپخانه 2S19 Msta-S", 5, 2, .75, "RU"),
    ("tos1", "gnd", "توپخانه موشکی TOS-1A", 6, 3, .8, "RU"),
    ("ztz99", "gnd", "تانک Type 99A", 4, 3, .55, "CN"),
    ("ztq15", "gnd", "تانک سبک Type 15", 5, 3, .55, "CN"),
    ("plz05", "gnd", "توپخانه PLZ-05", 7, 3, .75, "CN"),
    ("phl16", "gnd", "توپخانه موشکی PHL-16", 9, 4, .8, "CN"),
    ("merk", "gnd", "تانک Merkava Mk.4", 8, 3, .5, "IL"),
    ("namer", "gnd", "نفربر Namer", 5, 3, .45, "IL"),
    ("k2", "gnd", "تانک K2 Black Panther", 9, 3, .55, "KR"),
    ("k9", "gnd", "توپخانه K9 Thunder", 5, 3, .75, "KR"),
    ("k21", "gnd", "نفربر K21 IFV", 4, 3, .5, "KR"),
    ("abr", "gnd", "تانک M1A2 Abrams", 11, 3, .55, "US"),
    ("bradley", "gnd", "نفربر M2A3 Bradley", 4, 2, .5, "US"),
    ("stryker", "gnd", "نفربر Stryker", 3, 2, .45, "US"),
    ("m109", "gnd", "توپخانه M109A7 Paladin", 6, 3, .75, "US"),
    ("himars", "gnd", "توپخانه موشکی HIMARS", 8, 3, .8, "US"),
    ("m270", "gnd", "توپخانه موشکی M270 MLRS", 9, 3, .8, "US"),
    ("leo", "gnd", "تانک Leopard 2A7+", 14, 4, .55, "DE"),
    ("puma", "gnd", "نفربر Puma", 6, 4, .5, "DE"),
    ("boxer", "gnd", "نفربر Boxer", 4, 3, .45, "DE NL"),
    ("pzh", "gnd", "توپخانه PzH 2000", 10, 3, .75, "DE"),
    ("rch155", "gnd", "توپخانه RCH 155", 8, 4, .75, "DE"),
    ("ch3", "gnd", "تانک Challenger 3", 13, 4, .55, "GB"),
    ("ajax", "gnd", "نفربر Ajax", 8, 4, .5, "GB"),
    ("leclerc", "gnd", "تانک Leclerc", 10, 4, .55, "FR"),
    ("vbci", "gnd", "نفربر VBCI", 3.5, 3, .45, "FR"),
    ("caesar", "gnd", "توپخانه CAESAR", 6, 3, .75, "FR"),
    ("ariete", "gnd", "تانک Ariete", 6, 3, .5, "IT"),
    ("centauro", "gnd", "خودروی رزمی Centauro II", 5, 3, .55, "IT"),
    ("leo2e", "gnd", "تانک Leopard 2E", 9, 3, .55, "ES"),
    ("cv90", "gnd", "نفربر CV90", 5, 3, .5, "SE"),
    ("archer", "gnd", "توپخانه Archer", 8, 4, .8, "SE"),
    ("patria", "gnd", "نفربر Patria AMV", 3, 3, .45, "FI"),
    ("krab", "gnd", "توپخانه Krab", 7, 3, .75, "PL"),
    ("pt91", "gnd", "تانک PT-91 Twardy", 4, 2, .5, "PL"),
    ("borsuk", "gnd", "نفربر Borsuk", 4, 3, .5, "PL"),
    ("pandur", "gnd", "نفربر Pandur II", 3, 2, .4, "AT CZ"),
    ("ulan", "gnd", "نفربر Ulan", 3.5, 2, .45, "AT"),
    ("piranha", "gnd", "نفربر Piranha IV", 3, 2, .45, "CH"),
    ("arjun", "gnd", "تانک Arjun Mk.1A", 8, 3, .55, "IN"),
    ("pinaka", "gnd", "توپخانه موشکی Pinaka", 6, 3, .8, "IN"),
    ("dhanush", "gnd", "توپخانه Dhanush", 4, 2, .75, "IN"),
    ("type10", "gnd", "تانک Type 10", 11, 4, .55, "JP"),
    ("type99", "gnd", "توپخانه Type 99", 7, 3, .75, "JP"),
    ("altay", "gnd", "تانک Altay", 9, 4, .55, "TR"),
    ("firtina", "gnd", "توپخانه T-155 Fırtına", 6, 3, .75, "TR"),
    ("karrar", "gnd", "تانک Karrar", 4, 2, .55, "IR"),
    ("zulfiq", "gnd", "تانک Zulfiqar-3", 3, 2, .5, "IR"),
    ("khalid", "gnd", "تانک Al-Khalid", 4, 3, .55, "PK CN"),
    ("chonma", "gnd", "تانک Chonma-ho", 2.5, 1, .55, "KP"),
    ("koksan", "gnd", "توپخانه Koksan 170mm", 3, 1, .75, "KP"),
    ("bulat", "gnd", "تانک T-64BM Bulat", 3, 2, .55, "UA"),
    ("oplot", "gnd", "تانک Oplot-M", 4, 3, .55, "UA"),
    ("bohdana", "gnd", "توپخانه Bohdana", 5, 3, .75, "UA"),
    ("rooikat", "gnd", "خودروی رزمی Rooikat", 3, 2, .5, "ZA"),
    ("g6", "gnd", "توپخانه G6", 4, 2, .75, "ZA"),
    ("ramses", "gnd", "تانک Ramses II", 2, 1, .5, "EG"),
    ("harimau", "gnd", "تانک Harimau", 4, 2, .55, "ID TR"),
    ("anoa", "gnd", "نفربر Anoa", 1.5, 1, .4, "ID"),
    ("gempita", "gnd", "نفربر AV8 Gempita", 3, 2, .45, "MY"),
    ("guarani", "gnd", "نفربر Guarani", 2.5, 2, .45, "BR"),
    ("astros", "gnd", "توپخانه موشکی ASTROS II", 6, 3, .8, "BR"),
    ("tam", "gnd", "تانک TAM", 2.5, 1, .5, "AR"),
    ("lav3", "gnd", "نفربر LAV III", 3, 2, .45, "CA"),
    ("bushmaster", "gnd", "نفربر Bushmaster", 1.5, 2, .4, "AU"),
    ("bionix", "gnd", "نفربر Bionix II", 3, 3, .45, "SG"),
    ("hunter", "gnd", "نفربر Hunter AFV", 4, 3, .5, "SG"),
    ("cm11", "gnd", "تانک CM-11 Brave Tiger", 3, 2, .5, "TW"),
    ("nora", "gnd", "توپخانه Nora B-52", 4, 2, .75, "RS"),
    ("rabdan", "gnd", "نفربر Rabdan", 1.5, 2, .45, "AE"),
    # ───── جنگنده ─────
    ("mig29", "fighter", "جنگنده MiG-29", 30, 1, .6, "RU"),
    ("mig31", "fighter", "جنگنده MiG-31BM", 70, 4, .5, "RU"),
    ("mig35", "fighter", "جنگنده MiG-35", 40, 3, .6, "RU"),
    ("su25", "fighter", "جنگنده Su-25SM3", 15, 2, .65, "RU"),
    ("su30", "fighter", "جنگنده Su-30SM", 55, 3, .6, "RU"),
    ("su34", "fighter", "جنگنده Su-34 Fullback", 55, 4, .65, "RU"),
    ("su35", "fighter", "جنگنده Su-35S", 80, 4, .6, "RU"),
    ("su57", "fighter", "جنگنده Su-57 Felon", 95, 5, .6, "RU"),
    ("f16", "fighter", "جنگنده F-16V Viper", 65, 3, .6, "US"),
    ("a10", "fighter", "جنگنده A-10C Thunderbolt II", 20, 3, .65, "US"),
    ("fa18", "fighter", "جنگنده F/A-18E/F Super Hornet", 70, 4, .6, "US"),
    ("f15ex", "fighter", "جنگنده F-15EX Eagle II", 90, 4, .6, "US"),
    ("f35", "fighter", "جنگنده F-35A Lightning II", 110, 5, .6, "US"),
    ("f22", "fighter", "جنگنده F-22 Raptor", 150, 6, .6, "US"),
    ("rafale", "fighter", "جنگنده Rafale F4", 115, 4, .6, "FR"),
    ("m2000", "fighter", "جنگنده Mirage 2000-5", 45, 3, .55, "FR"),
    ("typhoon", "fighter", "جنگنده Eurofighter Typhoon", 115, 4, .6, "GB DE IT ES"),
    ("m346", "fighter", "جنگنده M-346FA", 30, 3, .5, "IT"),
    ("gripen", "fighter", "جنگنده JAS-39E Gripen", 85, 4, .6, "SE"),
    ("j10c", "fighter", "جنگنده J-10C", 50, 4, .6, "CN"),
    ("j16", "fighter", "جنگنده J-16", 85, 4, .6, "CN"),
    ("j20", "fighter", "جنگنده J-20 Mighty Dragon", 105, 5, .6, "CN"),
    ("j35", "fighter", "جنگنده J-35", 100, 5, .6, "CN"),
    ("jf17", "fighter", "جنگنده JF-17 Thunder", 28, 3, .55, "PK CN"),
    ("tejas", "fighter", "جنگنده Tejas Mk1A", 45, 3, .6, "IN"),
    ("f2", "fighter", "جنگنده Mitsubishi F-2", 80, 4, .6, "JP"),
    ("kf21", "fighter", "جنگنده KF-21 Boramae", 65, 4, .6, "KR"),
    ("fa50", "fighter", "جنگنده FA-50", 30, 3, .55, "KR"),
    ("kaan", "fighter", "جنگنده KAAN", 100, 5, .6, "TR"),
    ("hurjet", "fighter", "جنگنده Hürjet", 25, 3, .5, "TR"),
    ("kowsar", "fighter", "جنگنده Kowsar", 15, 2, .5, "IR"),
    ("ching", "fighter", "جنگنده F-CK-1 Ching-kuo", 25, 2, .55, "TW"),
    ("pampa", "fighter", "جنگنده IA-63 Pampa III", 18, 2, .5, "AR"),
    ("tucano", "fighter", "جنگنده A-29 Super Tucano", 15, 2, .5, "BR"),
    ("l159", "fighter", "جنگنده L-159 ALCA", 15, 2, .55, "CZ"),
    ("pc21", "fighter", "جنگنده Pilatus PC-21", 15, 2, .4, "CH"),
    # ───── بمب‌افکن ─────
    ("tu95", "bomber", "بمب‌افکن Tu-95MS", 100, 3, .9, "RU"),
    ("tu22", "bomber", "بمب‌افکن Tu-22M3", 90, 3, .9, "RU"),
    ("tu160", "bomber", "بمب‌افکن Tu-160M", 300, 5, .9, "RU"),
    ("b52", "bomber", "بمب‌افکن B-52H Stratofortress", 100, 4, .9, "US"),
    ("b1", "bomber", "بمب‌افکن B-1B Lancer", 280, 4, .9, "US"),
    ("b21", "bomber", "بمب‌افکن B-21 Raider", 700, 6, .9, "US"),
    ("b2", "bomber", "بمب‌افکن B-2 Spirit", 2100, 6, .9, "US"),
    ("h6k", "bomber", "بمب‌افکن H-6K", 120, 3, .9, "CN"),
    ("h20", "bomber", "بمب‌افکن H-20", 600, 6, .9, "CN"),
    ("vulcan", "bomber", "بمب‌افکن Avro Vulcan", 60, 3, .9, "GB"),
    # ───── بالگرد ─────
    ("ah64", "heli", "بالگرد AH-64E Apache", 35, 3, .8, "US"),
    ("uh60", "heli", "بالگرد UH-60M Black Hawk", 18, 3, .5, "US"),
    ("ka52", "heli", "بالگرد Ka-52 Alligator", 30, 3, .8, "RU"),
    ("mi28", "heli", "بالگرد Mi-28N Havoc", 28, 3, .8, "RU"),
    ("z10", "heli", "بالگرد Z-10", 25, 3, .8, "CN"),
    ("tigre", "heli", "بالگرد Tiger HAD", 40, 4, .8, "FR DE"),
    ("prachand", "heli", "بالگرد LCH Prachand", 22, 3, .8, "IN"),
    ("rooivalk", "heli", "بالگرد Rooivalk", 22, 3, .8, "ZA"),
    ("t129", "heli", "بالگرد T129 ATAK", 25, 3, .8, "TR"),
    # ───── پهپاد ─────
    ("tb2", "drone", "پهپاد Bayraktar TB2", 5, 2, .8, "TR"),
    ("akinci", "drone", "پهپاد Bayraktar Akıncı", 18, 4, .8, "TR"),
    ("kizil", "drone", "پهپاد Bayraktar Kızılelma", 30, 5, .7, "TR"),
    ("kargu", "drone", "پهپاد انتحاری Kargu", 0.05, 2, 1, "TR"),
    ("mq9", "drone", "پهپاد MQ-9 Reaper", 32, 3, .8, "US"),
    ("seaguard", "drone", "پهپاد MQ-9B SeaGuardian", 28, 4, .8, "US"),
    ("protector", "drone", "پهپاد Protector RG Mk1 (MQ-9B)", 25, 4, .8, "GB US"),
    ("rq4", "drone", "پهپاد RQ-4 Global Hawk", 120, 4, .2, "US"),
    ("shahed191", "drone", "پهپاد Shahed 191", 3, 2, .8, "IR"),
    ("shahed129", "drone", "پهپاد Shahed 129", 6, 3, .8, "IR"),
    ("mohajer6", "drone", "پهپاد Mohajer-6", 3, 2, .8, "IR"),
    ("lancet", "drone", "پهپاد انتحاری Lancet", 0.05, 2, 1, "RU"),
    ("orion", "drone", "پهپاد Orion", 12, 3, .7, "RU"),
    ("wl2", "drone", "پهپاد CAIG Wing Loong II", 12, 3, .8, "CN"),
    ("ch5", "drone", "پهپاد CH-5 Rainbow", 14, 3, .8, "CN"),
    ("gj11", "drone", "پهپاد GJ-11 Sharp Sword", 35, 5, .8, "CN"),
    ("patroller", "drone", "پهپاد SDT Patroller", 15, 3, .7, "FR"),
    ("heron", "drone", "پهپاد Heron TP", 25, 3, .6, "IL"),
    ("harop", "drone", "پهپاد انتحاری Harop", 1, 3, 1, "IL"),
    ("rustom", "drone", "پهپاد Rustom-II", 12, 3, .7, "IN"),
    ("burraq", "drone", "پهپاد Burraq", 4, 2, .8, "PK"),
    # ───── پدافند ─────
    ("s300", "aa", "پدافند S-300PMU2", 150, 2, 0, "RU"),
    ("s350", "aa", "پدافند S-350 Vityaz", 250, 4, 0, "RU"),
    ("s400", "aa", "پدافند S-400", 500, 4, 0, "RU"),
    ("s500", "aa", "پدافند S-500 Prometey", 1500, 6, 0, "RU"),
    ("pantsir", "aa", "پدافند Pantsir-S1", 15, 2, 0, "RU"),
    ("tor", "aa", "پدافند Tor-M2", 25, 3, 0, "RU"),
    ("bukm3", "aa", "پدافند Buk-M3 Viking", 200, 3, 0, "RU"),
    ("hq9", "aa", "پدافند HQ-9", 250, 3, 0, "CN"),
    ("hq16", "aa", "پدافند HQ-16", 90, 3, 0, "CN"),
    ("hq22", "aa", "پدافند HQ-22", 180, 3, 0, "CN"),
    ("irondome", "aa", "پدافند Iron Dome", 120, 3, 0, "IL"),
    ("davids", "aa", "پدافند David's Sling", 600, 4, 0, "IL"),
    ("arrow3", "aa", "پدافند Arrow 3", 900, 5, 0, "IL"),
    ("patriot", "aa", "پدافند Patriot PAC-3", 450, 4, 0, "US"),
    ("pac3mse", "aa", "پدافند Patriot PAC-3 MSE", 550, 5, 0, "US"),
    ("thaad", "aa", "پدافند THAAD", 900, 5, 0, "US"),
    ("nasams", "aa", "پدافند NASAMS", 180, 3, 0, "NO US"),
    ("sampt", "aa", "پدافند SAMP/T", 400, 4, 0, "FR IT"),
    ("iris", "aa", "پدافند IRIS-T SLM", 180, 3, 0, "DE"),
    ("skyranger", "aa", "پدافند Skyranger 30", 22, 3, 0, "DE"),
    ("camm", "aa", "پدافند Sky Sabre (CAMM)", 60, 4, 0, "GB"),
    ("akash", "aa", "پدافند Akash", 40, 2, 0, "IN"),
    ("type03", "aa", "پدافند Type 03 Chu-SAM", 80, 3, 0, "JP"),
    ("kmsam", "aa", "پدافند KM-SAM Cheongung", 90, 3, 0, "KR"),
    ("siper", "aa", "پدافند Siper", 150, 4, 0, "TR"),
    ("hisar", "aa", "پدافند Hisar-A", 12, 3, 0, "TR"),
    ("bavar", "aa", "پدافند Bavar-373", 220, 4, 0, "IR"),
    ("khordad", "aa", "پدافند Khordad-15", 100, 3, 0, "IR"),
    ("tk3", "aa", "پدافند Tien Kung III", 70, 3, 0, "TW"),
    # ───── ناوگان ─────
    ("corv", "navy", "ناوچه موشک‌انداز (Corvette)", 150, 2, .5, "*"),
    ("fremm", "navy", "ناو فریگیت FREMM", 600, 3, .5, "FR IT"),
    ("horizon", "navy", "ناوشکن Horizon", 1100, 4, .5, "FR IT"),
    ("kilo", "navy", "زیردریایی Kilo-class", 400, 3, .55, "RU"),
    ("karakurt", "navy", "ناوچه Karakurt", 250, 3, .5, "RU"),
    ("gorshkov", "navy", "ناو فریگیت Admiral Gorshkov", 900, 4, .5, "RU"),
    ("kirov", "navy", "رزم‌ناو Pyotr Velikiy (Kirov)", 2800, 4, .5, "RU"),
    ("yasen", "navy", "زیردریایی Yasen-M", 3500, 5, .55, "RU"),
    ("kuznetsov", "navy", "ناو هواپیمابر Admiral Kuznetsov", 4000, 3, .5, "RU"),
    ("borei", "navy", "زیردریایی Borei (SSBN)", 4500, 6, .5, "RU"),
    ("d052", "navy", "ناوشکن Type 052D", 1100, 4, .5, "CN"),
    ("t055", "navy", "ناوشکن Type 055", 1800, 5, .5, "CN"),
    ("t075", "navy", "ناو هلی‌بر Type 075", 1500, 4, .5, "CN"),
    ("fujian", "navy", "ناو هواپیمابر Fujian", 9000, 5, .5, "CN"),
    ("t094", "navy", "زیردریایی Type 094 (SSBN)", 3500, 5, .5, "CN"),
    ("ddg51", "navy", "ناوشکن Arleigh Burke", 1800, 5, .5, "US"),
    ("cg47", "navy", "رزم‌ناو Ticonderoga", 1500, 4, .5, "US"),
    ("ddg1000", "navy", "ناوشکن Zumwalt", 4000, 5, .5, "US"),
    ("la", "navy", "زیردریایی Los Angeles-class", 1800, 4, .55, "US"),
    ("vir", "navy", "زیردریایی Virginia-class", 3000, 5, .55, "US"),
    ("ohio", "navy", "زیردریایی Ohio (SSBN)", 5000, 6, .5, "US"),
    ("cvn", "navy", "ناو هواپیمابر Gerald R. Ford", 13000, 6, .5, "US"),
    ("cvn72", "navy", "ناو هواپیمابر USS Abraham Lincoln", 12000, 6, .5, "US"),
    ("t45", "navy", "ناوشکن Type 45", 1500, 4, .5, "GB"),
    ("qe", "navy", "ناو هواپیمابر Queen Elizabeth", 6000, 5, .5, "GB"),
    ("astute", "navy", "زیردریایی Astute-class", 2500, 5, .55, "GB"),
    ("cdg", "navy", "ناو هواپیمابر Charles de Gaulle", 4500, 5, .5, "FR"),
    ("barracuda", "navy", "زیردریایی Barracuda", 2000, 5, .55, "FR"),
    ("triomphant", "navy", "زیردریایی Triomphant (SSBN)", 4000, 5, .5, "FR"),
    ("cavour", "navy", "ناو هواپیمابر Cavour", 3000, 4, .5, "IT"),
    ("f100", "navy", "ناو فریگیت Álvaro de Bazán", 1000, 4, .5, "ES"),
    ("jc1", "navy", "ناو هلی‌بر Juan Carlos I", 1500, 3, .5, "ES"),
    ("s80", "navy", "زیردریایی S-80 Plus", 800, 4, .55, "ES"),
    ("visby", "navy", "ناوچه Visby", 400, 4, .5, "SE"),
    ("a26", "navy", "زیردریایی A26", 500, 4, .55, "SE"),
    ("t212", "navy", "زیردریایی Type 212A", 700, 4, .55, "DE"),
    ("f125", "navy", "ناو فریگیت F125", 900, 4, .5, "DE"),
    ("doorman", "navy", "ناو فریگیت De Zeven Provinciën", 800, 4, .5, "NL"),
    ("atago", "navy", "ناوشکن Atago-class", 1700, 5, .5, "JP"),
    ("maya", "navy", "ناوشکن Maya-class", 1800, 5, .5, "JP"),
    ("mogami", "navy", "ناو فریگیت Mogami", 600, 4, .5, "JP"),
    ("soryu", "navy", "زیردریایی Soryu/Taigei", 700, 4, .55, "JP"),
    ("izumo", "navy", "ناو هلی‌بر Izumo", 3000, 4, .5, "JP"),
    ("visakh", "navy", "ناوشکن Visakhapatnam", 1000, 4, .5, "IN"),
    ("vikrant", "navy", "ناو هواپیمابر INS Vikrant", 3500, 4, .5, "IN"),
    ("arihant", "navy", "زیردریایی Arihant (SSBN)", 3200, 5, .55, "IN"),
    ("sejong", "navy", "ناوشکن Sejong the Great", 1700, 4, .5, "KR"),
    ("kss3", "navy", "زیردریایی KSS-III", 800, 4, .55, "KR"),
    ("istif", "navy", "ناو فریگیت İstif", 800, 4, .5, "TR"),
    ("anadolu", "navy", "ناو هلی‌بر TCG Anadolu", 1500, 4, .5, "TR"),
    ("moudge", "navy", "ناو فریگیت Moudge", 250, 2, .45, "IR"),
    ("fatehsub", "navy", "زیردریایی Fateh", 120, 2, .5, "IR"),
    ("saar6", "navy", "ناوچه Sa'ar 6", 450, 4, .5, "IL"),
    ("dolphin", "navy", "زیردریایی Dolphin", 650, 4, .55, "IL"),
    ("hangor", "navy", "زیردریایی Hangor", 500, 3, .55, "CN PK"),
    ("hobart", "navy", "ناوشکن Hobart-class", 1400, 4, .5, "AU"),
    ("collins", "navy", "زیردریایی Collins", 600, 3, .55, "AU"),
    ("halifax", "navy", "ناو فریگیت Halifax", 550, 3, .5, "CA"),
    ("riachuelo", "navy", "زیردریایی Riachuelo", 500, 3, .55, "BR FR"),
    ("haikun", "navy", "زیردریایی Hai Kun", 500, 3, .55, "TW"),
    ("formidable", "navy", "ناو فریگیت Formidable", 650, 4, .5, "SG"),
    ("baynunah", "navy", "ناوچه Baynunah", 250, 3, .5, "AE"),
    # ───── موشک ─────
    ("scud", "missile", "موشک بالستیک Scud-B", 1, 1, 1, "RU KP"),
    ("shahed", "missile", "پهپاد انتحاری Shahed-136 (بسته ۱۰تایی)", 1.5, 2, 1, "IR"),
    ("shahab3", "missile", "موشک Shahab-3", 3, 2, 1, "IR"),
    ("fateh", "missile", "موشک Fateh-110", 1.5, 2, 1, "IR"),
    ("zolfaghar", "missile", "موشک Zolfaghar", 2, 3, 1, "IR"),
    ("sejjil", "missile", "موشک Sejjil", 4, 3, 1, "IR"),
    ("khorram", "missile", "موشک Khorramshahr", 5, 4, 1, "IR"),
    ("fattah", "missile", "موشک هایپرسونیک Fattah", 8, 5, 1, "IR"),
    ("atacms", "missile", "موشک ATACMS", 2, 3, 1, "US"),
    ("tomahawk", "missile", "موشک کروز Tomahawk", 2.5, 4, 1, "US"),
    ("jassm", "missile", "موشک کروز JASSM-ER", 3.5, 4, 1, "US"),
    ("trident", "missile", "موشک Trident II D5", 60, 6, 1, "US GB"),
    ("isk", "missile", "موشک Iskander-M", 4, 3, 1, "RU"),
    ("kalibr", "missile", "موشک کروز Kalibr", 6, 4, 1, "RU"),
    ("kh101", "missile", "موشک کروز Kh-101", 4, 4, 1, "RU"),
    ("kinzhal", "missile", "موشک هایپرسونیک Kinzhal", 10, 5, 1, "RU"),
    ("zircon", "missile", "موشک هایپرسونیک Zircon", 9, 5, 1, "RU"),
    ("oreshnik", "missile", "موشک بالستیک Oreshnik", 25, 6, 1, "RU"),
    ("avangard", "missile", "سامانه هایپرسونیک Avangard", 40, 6, 1, "RU"),
    ("sarmat", "missile", "موشک RS-28 Sarmat (Satan II)", 90, 6, 1, "RU"),
    ("r36", "missile", "موشک R-36M2 Voevoda (SS-18 Satan)", 70, 6, 1, "RU"),
    ("df17", "missile", "موشک هایپرسونیک DF-17", 12, 5, 1, "CN"),
    ("df21", "missile", "موشک DF-21D", 6, 4, 1, "CN"),
    ("df26", "missile", "موشک DF-26", 9, 5, 1, "CN"),
    ("yj18", "missile", "موشک کروز YJ-18", 3, 4, 1, "CN"),
    ("gl2", "missile", "موشک GL-2", 15, 5, 1, "CN"),
    ("brahmos", "missile", "موشک کروز BrahMos", 3.5, 4, 1, "IN RU"),
    ("agni5", "missile", "موشک Agni-V", 18, 5, 1, "IN"),
    ("prithvi", "missile", "موشک Prithvi-II", 2, 2, 1, "IN"),
    ("stormshadow", "missile", "موشک کروز Storm Shadow/SCALP", 3, 4, 1, "GB FR"),
    ("exocet", "missile", "موشک ضدکشتی Exocet", 1.2, 3, 1, "FR"),
    ("taurus", "missile", "موشک کروز Taurus KEPD 350", 3, 4, 1, "DE SE"),
    ("nsm", "missile", "موشک ضدکشتی NSM", 2.2, 4, 1, "NO"),
    ("type12", "missile", "موشک Type 12 SSM", 2.5, 4, 1, "JP"),
    ("hyunmoo", "missile", "موشک Hyunmoo-4", 5, 4, 1, "KR"),
    ("tayfun", "missile", "موشک Tayfun", 6, 4, 1, "TR"),
    ("bora", "missile", "موشک Bora", 3, 3, 1, "TR"),
    ("atmaca", "missile", "موشک ضدکشتی Atmaca", 1.5, 3, 1, "TR"),
    ("neptune", "missile", "موشک کروز Neptune", 1.5, 3, 1, "UA"),
    ("babur", "missile", "موشک کروز Babur", 2, 3, 1, "PK"),
    ("shaheen", "missile", "موشک Shaheen-III", 8, 4, 1, "PK"),
    ("ghauri", "missile", "موشک Ghauri", 4, 3, 1, "PK"),
    ("hs15", "missile", "موشک Hwasong-15", 10, 4, 1, "KP"),
    ("hs17", "missile", "موشک Hwasong-17", 14, 5, 1, "KP"),
    ("kn23", "missile", "موشک KN-23", 3, 3, 1, "KP"),
    ("spike", "missile", "موشک Spike NLOS", 0.8, 3, 1, "IL"),
    ("hf3", "missile", "موشک Hsiung Feng III", 2, 3, 1, "TW"),
    # ───── بمب ─────
    ("jdam", "bomb", "بمب JDAM GBU-31 (بسته ۱۰۰تایی)", 3, 2, 1, "US"),
    ("sdb", "bomb", "بمب GBU-39 SDB (بسته ۱۰۰تایی)", 5, 3, 1, "US"),
    ("moab", "bomb", "بمب GBU-43 MOAB", 16, 4, 1, "US"),
    ("mop", "bomb", "بمب سنگرشکن GBU-57 MOP", 4, 5, 1, "US"),
    ("kab", "bomb", "بمب هدایت‌شونده KAB-500 (بسته ۱۰۰تایی)", 2.5, 2, 1, "RU"),
    ("fab3000", "bomb", "بمب سنگین FAB-3000", 8, 3, 1, "RU"),
    ("ls6", "bomb", "بمب لیزری LS-6 (بسته ۱۰۰تایی)", 2, 2, 1, "CN"),
    ("aasm", "bomb", "بمب AASM Hammer (بسته ۱۰۰تایی)", 4, 3, 1, "FR"),
    # ───── هسته‌ای (فقط کشورهای هسته‌ای؛ مجوز‌پذیر نیست) ─────
    ("tnuke", "nuke", "کلاهک هسته‌ای تاکتیکی", 3500, 6, 0, "US RU CN GB FR IN PK IL KP"),
    ("icbm", "nuke", "موشک قاره‌پیمای هسته‌ای (ICBM)", 9000, 6, 0, "US RU CN GB FR IN PK KP"),
    # ───── سایبری (عمومی) ─────
    ("redhat", "cyber", "هکر کلاه‌قرمز (Red Hat)", 8, 3, 0, "*"),
    ("whitehat", "cyber", "هکر کلاه‌سفید (White Hat)", 8, 3, 0, "*"),
    ("fin", "cyber", "هکر مالی (Financial)", 12, 3, 0, "*"),
    ("spy", "cyber", "جاسوس (Spy)", 5, 2, 0, "*"),
]
U = {}
for _k, _cat, _name, _cost, _tech, _share, _org in UNITS:
    _burst = 3.0 if _cat in ("missile", "bomb") else 1.0
    _pw = 0.0 if _cat in ("nuke", "cyber") else _cost * (0.9 + 0.1 * _tech) * _burst
    U[_k] = {"key": _k, "cat": _cat, "name": _name, "cost": _cost, "tech": _tech,
             "pw": _pw, "atk": _pw * _share, "dfn": _pw * (1 - _share),
             "org": frozenset(_org.split()) - {"*"}}
ORG_INDEX = {}      # کشور سازنده ← کلیدهای تجهیزاتش
for _k, _u in U.items():
    for _o in _u["org"]:
        ORG_INDEX.setdefault(_o, []).append(_k)

AIRBORNE = {"fighter", "bomber", "heli", "drone", "bomb", "missile"}
# کلاهک: (تلفات ارتش، تلفات خزانه، استان از دست رفته، افت ثبات)
NUKE = {"tnuke": (0.35, 0.25, 0, 30), "icbm": (0.6, 0.45, 1, 45)}

TIER_NAME = {5: "👑 ابرقدرت", 4: "🥇 قدرت بزرگ", 3: "🥈 قدرت منطقه‌ای",
             2: "🥉 قدرت متوسط", 1: "🌱 کشور کوچک"}
START_MONEY = {5: 12000, 4: 6000, 3: 3500, 2: 1800, 1: 1000}
START_PROV = {5: 10, 4: 7, 3: 5, 2: 4, 1: 3}
PER_PROV = {5: 15, 4: 11, 3: 9, 2: 6, 1: 5}
TECH_COST = {2: 800, 3: 2000, 4: 4500, 5: 9000, 6: 18000}

BASE_KIT = {
    5: {"inf": 300, "sof": 30, "himars": 40, "patriot": 4, "corv": 10},
    4: {"inf": 200, "sof": 15, "himars": 20, "s300": 6, "corv": 6},
    3: {"inf": 120, "t72": 80, "s300": 3, "mig29": 10, "corv": 3},
    2: {"inf": 80, "t72": 40, "mig29": 12, "tb2": 5},
    1: {"inf": 40, "t72": 15, "mig29": 5},
}
SIG = {  # تجهیزات شاخص هر کشور (به کیت پایه اضافه می‌شه)
    "US": {"abr": 400, "f35": 120, "f22": 40, "f16": 100, "b2": 15, "b52": 40, "b1": 30,
           "tomahawk": 400, "thaad": 4, "patriot": 8, "ddg51": 20, "vir": 14, "cvn": 4,
           "jdam": 60, "mop": 8, "icbm": 10, "tnuke": 20, "mq9": 100},
    "RU": {"t90": 500, "t72": 800, "su57": 30, "su35": 120, "su30": 80, "tu160": 16, "tu95": 50,
           "s400": 25, "kalibr": 300, "isk": 150, "kinzhal": 40, "shahed": 200, "icbm": 12,
           "tnuke": 30, "ka52": 100, "kilo": 20},
    "CN": {"ztz99": 700, "j20": 120, "su35": 24, "hq9": 30, "d052": 30, "df17": 60, "kilo": 40,
           "tu95": 30, "icbm": 6, "tnuke": 10},
    "GB": {"ch3": 150, "typhoon": 90, "f35": 30, "tomahawk": 60, "fremm": 8, "icbm": 3},
    "FR": {"leo": 200, "rafale": 100, "fremm": 8, "icbm": 3},
    "DE": {"leo": 300, "typhoon": 90, "pzh": 120, "patriot": 8},
    "IN": {"t90": 450, "su30": 200, "rafale": 36, "brahmos": 120, "s400": 3, "kilo": 8,
           "tnuke": 15, "icbm": 2},
    "JP": {"f35": 40, "f15ex": 80, "patriot": 10, "ddg51": 8},
    "KR": {"k2": 200, "f35": 40, "f16": 150, "ddg51": 3},
    "TR": {"leo": 120, "f16": 200, "tb2": 150, "s400": 2, "fremm": 8},
    "IR": {"t72": 450, "mig29": 24, "shahed": 400, "scud": 300, "s300": 8, "kilo": 3},
    "IL": {"merk": 450, "f35": 40, "f16": 150, "irondome": 10, "jdam": 40},
    "SA": {"abr": 400, "f15ex": 90, "typhoon": 70, "patriot": 12, "thaad": 2},
    "PK": {"t90": 300, "f16": 75, "scud": 100, "tnuke": 8},
    "KP": {"t72": 500, "scud": 400, "mig29": 40, "tnuke": 8, "icbm": 2},
    "UA": {"t72": 400, "mig29": 40, "himars": 30, "s300": 6, "tb2": 40, "atacms": 50},
    "PL": {"k2": 120, "abr": 116, "f35": 32, "f16": 48, "patriot": 4},
    "EG": {"abr": 400, "rafale": 54, "f16": 200, "s300": 8},
    "AU": {"abr": 59, "f35": 72, "ddg51": 3},
    "CA": {"leo": 80, "f35": 10},
    "IT": {"typhoon": 90, "f35": 40, "fremm": 8},
    "ES": {"leo": 100, "typhoon": 70, "fremm": 5},
}
COUNTRIES = [
    ("US", "آمریکا", "United States", 5), ("CN", "چین", "China", 5), ("RU", "روسیه", "Russia", 5),
    ("GB", "انگلیس", "United Kingdom", 4), ("FR", "فرانسه", "France", 4),
    ("DE", "آلمان", "Germany", 4), ("IN", "هند", "India", 4), ("JP", "ژاپن", "Japan", 4),
    ("TR", "ترکیه", "Turkey", 4), ("IR", "ایران", "Iran", 4), ("IL", "اسرائیل", "Israel", 4),
    ("KR", "کره جنوبی", "South Korea", 4), ("SA", "عربستان", "Saudi Arabia", 4),
    ("IT", "ایتالیا", "Italy", 3), ("ES", "اسپانیا", "Spain", 3), ("PL", "لهستان", "Poland", 3),
    ("UA", "اوکراین", "Ukraine", 3), ("PK", "پاکستان", "Pakistan", 3), ("EG", "مصر", "Egypt", 3),
    ("BR", "برزیل", "Brazil", 3), ("AU", "استرالیا", "Australia", 3), ("CA", "کانادا", "Canada", 3),
    ("KP", "کره شمالی", "North Korea", 3), ("ID", "اندونزی", "Indonesia", 3),
    ("MX", "مکزیک", "Mexico", 3),
    ("ZA", "آفریقای جنوبی", "South Africa", 2), ("IQ", "عراق", "Iraq", 2),
    ("AZ", "آذربایجان", "Azerbaijan", 2), ("GR", "یونان", "Greece", 2), ("SE", "سوئد", "Sweden", 2),
    ("AE", "امارات", "UAE", 2), ("AR", "آرژانتین", "Argentina", 2), ("TH", "تایلند", "Thailand", 2),
    ("VN", "ویتنام", "Vietnam", 2), ("NG", "نیجریه", "Nigeria", 2),
    ("CU", "کوبا", "Cuba", 1), ("VE", "ونزوئلا", "Venezuela", 1), ("AM", "ارمنستان", "Armenia", 1),
    ("BY", "بلاروس", "Belarus", 1),
]
# رویدادهای جهانی (ادمین فعال می‌کنه یا خودکار)
EVENTS = [
    {"name": "🌋 زلزله‌ی ویرانگر", "text": "زمین‌لرزه‌ای شدید زیرساخت‌ها را نابود کرد!", "money": -0.15, "stab": -10},
    {"name": "🌊 سیل ویرانگر", "text": "سیل بی‌سابقه مناطق وسیعی را زیر آب برد!", "money": -0.12, "stab": -8},
    {"name": "📉 بحران اقتصادی", "text": "بازارها سقوط کردند و ارزش پول ملی افت کرد!", "money": -0.25, "stab": -8},
    {"name": "📈 جهش اقتصادی", "text": "صادرات رکورد زد و اقتصاد جهش کرد!", "money": 0.2, "stab": 5},
    {"name": "🛢 کشف میدان نفتی", "text": "یک میدان عظیم نفتی کشف شد!", "bonus": 24},
    {"name": "🧨 کودتای نافرجام", "text": "کودتا سرکوب شد اما بخشی از ارتش از دست رفت.", "units": 0.15, "stab": -25},
    {"name": "🦠 همه‌گیری", "text": "بیماری واگیردار کشور را فلج کرد!", "money": -0.1, "stab": -15},
    {"name": "🎉 وحدت ملی", "text": "مردم متحد شدند و روحیه‌ی ملی اوج گرفت!", "stab": 20},
    {"name": "💣 حمله تروریستی", "text": "حمله‌ی تروریستی به مراکز حساس رخ داد!", "units": 0.03, "stab": -10},
]


# ═════════════ کشورهای بیشتر (جمعاً ~۱۹۶ کشور) ═════════════
COUNTRIES += [
    # اروپا
    ("AL", "آلبانی", "Albania", 1), ("AD", "آندورا", "Andorra", 1), ("AT", "اتریش", "Austria", 3),
    ("BE", "بلژیک", "Belgium", 3), ("BA", "بوسنی و هرزگوین", "Bosnia", 1), ("BG", "بلغارستان", "Bulgaria", 2),
    ("HR", "کرواسی", "Croatia", 2), ("CY", "قبرس", "Cyprus", 1), ("CZ", "چک", "Czechia", 3),
    ("DK", "دانمارک", "Denmark", 3), ("EE", "استونی", "Estonia", 2), ("FI", "فنلاند", "Finland", 3),
    ("HU", "مجارستان", "Hungary", 2), ("IS", "ایسلند", "Iceland", 1), ("IE", "ایرلند", "Ireland", 2),
    ("LV", "لتونی", "Latvia", 2), ("LI", "لیختن‌اشتاین", "Liechtenstein", 1), ("LT", "لیتوانی", "Lithuania", 2),
    ("LU", "لوکزامبورگ", "Luxembourg", 1), ("MT", "مالت", "Malta", 1), ("MD", "مولداوی", "Moldova", 1),
    ("MC", "موناکو", "Monaco", 1), ("ME", "مونته‌نگرو", "Montenegro", 1), ("NL", "هلند", "Netherlands", 3),
    ("MK", "مقدونیه شمالی", "North Macedonia", 1), ("NO", "نروژ", "Norway", 3), ("PT", "پرتغال", "Portugal", 3),
    ("RO", "رومانی", "Romania", 3), ("SM", "سن مارینو", "San Marino", 1), ("RS", "صربستان", "Serbia", 2),
    ("SK", "اسلواکی", "Slovakia", 2), ("SI", "اسلوونی", "Slovenia", 2), ("CH", "سوئیس", "Switzerland", 3),
    ("VA", "واتیکان", "Vatican", 1), ("GE", "گرجستان", "Georgia", 2),
    # آسیا
    ("AF", "افغانستان", "Afghanistan", 2), ("BH", "بحرین", "Bahrain", 2), ("BD", "بنگلادش", "Bangladesh", 3),
    ("BT", "بوتان", "Bhutan", 1), ("BN", "برونئی", "Brunei", 1), ("KH", "کامبوج", "Cambodia", 2),
    ("JO", "اردن", "Jordan", 2), ("KZ", "قزاقستان", "Kazakhstan", 3), ("KW", "کویت", "Kuwait", 2),
    ("KG", "قرقیزستان", "Kyrgyzstan", 1), ("LA", "لائوس", "Laos", 1), ("LB", "لبنان", "Lebanon", 2),
    ("MY", "مالزی", "Malaysia", 3), ("MV", "مالدیو", "Maldives", 1), ("MN", "مغولستان", "Mongolia", 2),
    ("MM", "میانمار", "Myanmar", 2), ("NP", "نپال", "Nepal", 2), ("OM", "عمان", "Oman", 2),
    ("PH", "فیلیپین", "Philippines", 3), ("QA", "قطر", "Qatar", 3), ("SG", "سنگاپور", "Singapore", 3),
    ("LK", "سریلانکا", "Sri Lanka", 2), ("SY", "سوریه", "Syria", 2), ("TJ", "تاجیکستان", "Tajikistan", 1),
    ("TL", "تیمور شرقی", "Timor-Leste", 1), ("TM", "ترکمنستان", "Turkmenistan", 2),
    ("UZ", "ازبکستان", "Uzbekistan", 2), ("YE", "یمن", "Yemen", 2), ("PS", "فلسطین", "Palestine", 1),
    ("TW", "تایوان", "Taiwan", 3),
    # آفریقا
    ("DZ", "الجزایر", "Algeria", 3), ("AO", "آنگولا", "Angola", 2), ("BJ", "بنین", "Benin", 1),
    ("BW", "بوتسوانا", "Botswana", 1), ("BF", "بورکینافاسو", "Burkina Faso", 1), ("BI", "بوروندی", "Burundi", 1),
    ("CV", "کیپ‌ورد", "Cape Verde", 1), ("CM", "کامرون", "Cameroon", 2), ("CF", "آفریقای مرکزی", "Central African Republic", 1),
    ("TD", "چاد", "Chad", 1), ("KM", "کومور", "Comoros", 1), ("CG", "کنگو", "Congo", 1),
    ("CD", "کنگوی دموکراتیک", "DR Congo", 2), ("CI", "ساحل عاج", "Ivory Coast", 2), ("DJ", "جیبوتی", "Djibouti", 1),
    ("GQ", "گینه استوایی", "Equatorial Guinea", 1), ("ER", "اریتره", "Eritrea", 1), ("SZ", "اسواتینی", "Eswatini", 1),
    ("ET", "اتیوپی", "Ethiopia", 3), ("GA", "گابن", "Gabon", 1), ("GM", "گامبیا", "Gambia", 1),
    ("GH", "غنا", "Ghana", 2), ("GN", "گینه", "Guinea", 1), ("GW", "گینه بیسائو", "Guinea-Bissau", 1),
    ("KE", "کنیا", "Kenya", 2), ("LS", "لسوتو", "Lesotho", 1), ("LR", "لیبریا", "Liberia", 1),
    ("LY", "لیبی", "Libya", 2), ("MG", "ماداگاسکار", "Madagascar", 1), ("MW", "مالاوی", "Malawi", 1),
    ("ML", "مالی", "Mali", 1), ("MR", "موریتانی", "Mauritania", 1), ("MU", "موریس", "Mauritius", 1),
    ("MA", "مراکش", "Morocco", 3), ("MZ", "موزامبیک", "Mozambique", 1), ("NA", "نامیبیا", "Namibia", 1),
    ("NE", "نیجر", "Niger", 1), ("RW", "رواندا", "Rwanda", 1), ("ST", "سائوتومه و پرنسیپ", "Sao Tome", 1),
    ("SN", "سنگال", "Senegal", 1), ("SC", "سیشل", "Seychelles", 1), ("SL", "سیرالئون", "Sierra Leone", 1),
    ("SO", "سومالی", "Somalia", 1), ("SS", "سودان جنوبی", "South Sudan", 1), ("SD", "سودان", "Sudan", 2),
    ("TZ", "تانزانیا", "Tanzania", 2), ("TG", "توگو", "Togo", 1), ("TN", "تونس", "Tunisia", 2),
    ("UG", "اوگاندا", "Uganda", 2), ("ZM", "زامبیا", "Zambia", 1), ("ZW", "زیمبابوه", "Zimbabwe", 2),
    # آمریکا
    ("AG", "آنتیگوا و باربودا", "Antigua", 1), ("BS", "باهاما", "Bahamas", 1), ("BB", "باربادوس", "Barbados", 1),
    ("BZ", "بلیز", "Belize", 1), ("BO", "بولیوی", "Bolivia", 2), ("CL", "شیلی", "Chile", 3),
    ("CO", "کلمبیا", "Colombia", 3), ("CR", "کاستاریکا", "Costa Rica", 2), ("DM", "دومینیکا", "Dominica", 1),
    ("DO", "جمهوری دومینیکن", "Dominican Republic", 2), ("EC", "اکوادور", "Ecuador", 2),
    ("SV", "السالوادور", "El Salvador", 2), ("GD", "گرنادا", "Grenada", 1), ("GT", "گواتمالا", "Guatemala", 2),
    ("GY", "گویان", "Guyana", 1), ("HT", "هائیتی", "Haiti", 1), ("HN", "هندوراس", "Honduras", 2),
    ("JM", "جامائیکا", "Jamaica", 1), ("NI", "نیکاراگوئه", "Nicaragua", 1), ("PA", "پاناما", "Panama", 2),
    ("PY", "پاراگوئه", "Paraguay", 2), ("PE", "پرو", "Peru", 2), ("KN", "سنت کیتس و نویس", "Saint Kitts", 1),
    ("LC", "سنت لوسیا", "Saint Lucia", 1), ("VC", "سنت وینسنت", "Saint Vincent", 1), ("SR", "سورینام", "Suriname", 1),
    ("TT", "ترینیداد و توباگو", "Trinidad", 1), ("UY", "اروگوئه", "Uruguay", 2),
    # اقیانوسیه
    ("FJ", "فیجی", "Fiji", 1), ("KI", "کیریباتی", "Kiribati", 1), ("MH", "جزایر مارشال", "Marshall Islands", 1),
    ("FM", "میکرونزی", "Micronesia", 1), ("NR", "نائورو", "Nauru", 1), ("NZ", "نیوزیلند", "New Zealand", 2),
    ("PW", "پالائو", "Palau", 1), ("PG", "پاپوآ گینه نو", "Papua New Guinea", 1), ("WS", "ساموآ", "Samoa", 1),
    ("SB", "جزایر سلیمان", "Solomon Islands", 1), ("TO", "تونگا", "Tonga", 1), ("TV", "تووالو", "Tuvalu", 1),
    ("VU", "وانواتو", "Vanuatu", 1),
]
SEED_V = 2   # با بالا بردنش، کشورهای جدیدِ لیست به بازی‌های قدیمی هم اضافه می‌شن

EVENTS += [
    {"name": "🏆 میزبانی رویداد جهانی", "text": "میزبانی یک رویداد بزرگ جهانی، گردشگری و درآمد آورد!", "bonus": 12, "stab": 8},
    {"name": "🛰 هک گسترده‌ی ملی", "text": "حمله‌ی سایبری گسترده به زیرساخت‌ها رخ داد!", "money": -0.08, "stab": -6},
    {"name": "🔌 خاموشی سراسری", "text": "شبکه‌ی برق فروپاشید و ذخایر برق آسیب دید!", "res_elec": -0.5, "stab": -8},
    {"name": "💎 کشف رگه‌ی طلا", "text": "رگه‌ی عظیم طلا کشف شد!", "res_gold": 0.5, "stab": 4},
]

# ═════════════ منابع ═════════════
RES = {"oil": ("🛢", "نفت"), "iron": ("⛓", "آهن"), "alu": ("🔩", "آلومینیوم"), "gold": ("🥇", "طلا"),
       "uranium": ("☢️", "اورانیوم"), "elec": ("⚡", "برق")}
RES_PRICE = {"oil": 1.2, "iron": 0.8, "alu": 3.0, "gold": 40.0, "uranium": 300.0, "elec": 0.5}  # M$ برای هر ۱۰۰۰ واحد
_RES_BASE = {"oil": 300000, "iron": 300000, "alu": 15000, "gold": 20000, "uranium": 1500, "elec": 100000}
_RES_F = {5: 1.0, 4: 0.5, 3: 0.25, 2: 0.1, 1: 0.04}
START_RES = {t: {k: float(v * f) for k, v in _RES_BASE.items()} for t, f in _RES_F.items()}
START_POP = {5: 150_000_000, 4: 80_000_000, 3: 40_000_000, 2: 15_000_000, 1: 5_000_000}
INCOME_BASE = {"core": "پایه", "fac": "صنایع و معادن", "bld": "ساخت‌وساز", "tax": "مالیات جمعیت"}

# (کلید، نام، هزینه‌ی سطح۱، تکنولوژی لازم، درآمد پولی هر سطح در ساعت، (منبع، تولید هر سطح در ساعت)، معدن؟، توضیح)
_FAC = [
    ("cement", "🧱 کارخانه سیمان", 400, 1, 14, None, False, "هزینه ساخت‌وساز −۲٪ در هر سطح"),
    ("car", "🚗 کارخانه خودروسازی", 650, 2, 36, None, False, "صادرات خودرو و درآمد پایدار"),
    ("steel", "🏭 ذوب‌آهن و فولاد", 700, 2, 10, ("iron", 6000), False, "تولید آهن"),
    ("alu", "🔩 کارخانه آلومینیوم", 900, 3, 12, ("alu", 1200), False, "تولید آلومینیوم"),
    ("holding", "🏢 هلدینگ اقتصادی", 1500, 2, 70, None, False, "گروه شرکت‌های بزرگ؛ درآمد بالا"),
    ("refinery", "⛽ پالایشگاه و پتروشیمی", 1800, 3, 90, None, False, "فرآوری نفت؛ درآمد بالا"),
    ("tech", "💻 پارک فناوری", 3000, 4, 140, None, False, "استارتاپ‌ها و صادرات فناوری"),
    ("arms", "🔫 صنایع نظامی", 2000, 3, 0, None, False, "قیمت تجهیزات −۲٪ در هر سطح (حداکثر ۲۰٪)"),
    ("space", "🛰 برنامه‌ی فضایی", 5000, 5, 160, None, False, "ماهواره: حمله‌ی هوایی/موشکی +۳٪ در هر سطح"),
    ("agri", "🌾 کشاورزی و صنایع غذایی", 300, 1, 8, None, False, "رشد سریع‌تر جمعیت"),
    ("oil", "🛢 میدان نفتی", 800, 1, 8, ("oil", 15000), True, "استخراج نفت"),
    ("ironm", "⛏ معدن آهن", 500, 1, 5, ("iron", 12000), True, "استخراج آهن"),
    ("gold", "🥇 معدن طلا", 1200, 2, 10, ("gold", 600), True, "استخراج طلا"),
    ("uran", "☢️ معدن اورانیوم", 2500, 4, 0, ("uranium", 120), True, "استخراج اورانیوم"),
    ("power", "⚡ نیروگاه برق", 700, 1, 6, ("elec", 12000), False, "تولید برق (سوخت ماینرها و صنایع)"),
]
FD = {f[0]: {"key": f[0], "name": f[1], "cost": f[2], "tech": f[3], "money": f[4], "res": f[5],
             "mine": f[6], "desc": f[7]} for f in _FAC}
FAC_MAX = 10

# (کلید، نام، هزینه، درآمد ساعتی، تکنولوژی، تعداد اسلات، توضیح)
_BLD = [
    ("cafe", "☕ کافه", 40, 4.5, 1, 1, ""),
    ("rest", "🍽 رستوران", 90, 10, 1, 1, ""),
    ("park", "🌳 پارک", 120, 12, 1, 1, "ثبات +"),
    ("house", "🏘 مجتمع مسکونی", 150, 15, 1, 1, "ظرفیت جمعیت +۲M"),
    ("cinema", "🎬 سینما", 220, 24, 1, 1, ""),
    ("museum", "🏛 موزه", 320, 35, 2, 1, "گردشگری"),
    ("mall", "🛍 مرکز خرید", 650, 72, 2, 2, ""),
    ("hospital", "🏥 بیمارستان", 900, 70, 2, 2, "رشد جمعیت +"),
    ("hotel", "🏨 هتل", 900, 100, 2, 2, ""),
    ("theater", "🎭 تئاتر و اپرا", 1000, 110, 2, 2, "ثبات +"),
    ("theme", "🎡 شهربازی", 1400, 155, 3, 3, ""),
    ("uni", "🎓 دانشگاه", 2200, 240, 3, 3, "هزینه تحقیقات −۱٪"),
    ("stadium", "🏟 ورزشگاه", 2800, 310, 3, 3, "ثبات +"),
    ("port", "⚓ بندر تجاری", 4200, 470, 3, 3, ""),
    ("airport", "✈️ فرودگاه بین‌المللی", 5500, 610, 4, 3, ""),
    ("tower", "🏙 برج تجاری", 9000, 1000, 4, 3, ""),
]
BD = {b[0]: {"key": b[0], "name": b[1], "cost": b[2], "inc": b[3], "tech": b[4], "slots": b[5], "note": b[6]}
      for b in _BLD}
CITY_PRESETS = ["🏛 پایتخت", "⚓ شهر بندری", "⛰ شهر کوهستانی", "🏭 شهر صنعتی", "🌆 کلان‌شهر", "🏝 شهر ساحلی"]

# شگفتی‌ها: هر کدوم فقط یک کشور تو کل بازی می‌تونه داشته باشه
WONDERS = [
    ("pyramid", "🔺 اهرام جاودان", 15000, 2, "درآمد کل +۱۵٪"),
    ("wall", "🧱 دیوار بزرگ", 20000, 2, "قدرت دفاع +۲۵٪"),
    ("suez", "🚢 کانال بزرگ تجاری", 25000, 3, "درآمد کل +۲۰٪"),
    ("dam", "⚡ سد عظیم", 18000, 3, "تولید برق +۴۰,۰۰۰ در ساعت"),
    ("silicon", "💻 دره‌ی سیلیکون", 30000, 4, "تولید ماینرها +۳۰٪ و درآمد صنایع +۱۵٪"),
    ("oilcity", "🛢 ابرشهر نفتی", 28000, 3, "تولید نفت و طلا +۳۰٪"),
    ("library", "📚 کتابخانه‌ی جهانی", 22000, 3, "هزینه تحقیقات −۲۵٪"),
    ("manhattan", "☢️ پروژه‌ی منهتن", 40000, 5, "سقف کلاهک هسته‌ای +۱۰"),
    ("elevator", "🛰 آسانسور فضایی", 60000, 6, "حمله‌ی هوایی/موشکی +۳۰٪ و درآمد +۱۰٪"),
]
WD = {w[0]: {"key": w[0], "name": w[1], "cost": w[2], "tech": w[3], "desc": w[4]} for w in WONDERS}

# ═════════════ ارز دیجیتال، ماینر و بانک ═════════════
COINS = {
    "BTC": {"name": "بیت‌کوین", "sym": "₿", "p": 60.0, "vol": 0.004},
    "ETH": {"name": "اتریوم", "sym": "Ξ", "p": 3.2, "vol": 0.005},
    "SOL": {"name": "سولانا", "sym": "◎", "p": 0.16, "vol": 0.007},
    "DOGE": {"name": "دوج‌کوین", "sym": "Ð", "p": 0.0012, "vol": 0.010},
}
CRYPTO_FEE = 0.005
# (کلید، نام، قیمت M$، تولید BTC در ساعت، مصرف برق در ساعت، تکنولوژی)
_MINERS = [
    ("asic1", "⛏ ماینر Antminer S19", 6, 0.0045, 30, 1),
    ("asic2", "⛏ ماینر Antminer S21 Pro", 22, 0.0185, 90, 2),
    ("rack", "🗄 رک ماینینگ (۱۰۰ دستگاه)", 450, 0.50, 2600, 3),
    ("farm", "🏭 مزرعه‌ی ماینینگ صنعتی", 6000, 7.5, 32000, 4),
    ("dc", "🛰 دیتاسنتر ماینینگ غول‌پیکر", 60000, 85.0, 320000, 5),
]
MD = {x[0]: {"key": x[0], "name": x[1], "cost": x[2], "btc": x[3], "elec": x[4], "tech": x[5]} for x in _MINERS}

BANK_KINDS = {
    "flex": {"name": "🟢 سپرده‌ی انعطاف‌پذیر", "rate": 0.0025, "lock": 0},
    "d1": {"name": "🟡 سپرده‌ی ۲۴ ساعته", "rate": 0.0050, "lock": 24},
    "d3": {"name": "🔴 سپرده‌ی ۷۲ ساعته", "rate": 0.0080, "lock": 72},
}
LOAN_RATE = 0.005        # سود وام در ساعت
LOAN_GRACE_H = 48        # بعد از این مدت جریمه شروع می‌شه
LOAN_FORCE_H = 96        # بعد از این مدت بانک از خزانه برداشت می‌کنه
EARLY_PENALTY = 0.05

# ═════════════ سیاست‌های داخلی ═════════════
TAX_LEVELS = [("🟢 کم", 0.90, 1.0), ("🟡 متوسط", 1.00, 0.0), ("🟠 زیاد", 1.20, -1.0), ("🔴 سنگین", 1.40, -3.0)]
# نام: (درآمد, دفاع, حمله, ثبات/ساعت, هزینه تحقیقات, توضیح)
GOVS = {
    "dem": ("🗳 دموکراسی", 1.08, 1.0, 0.95, 0.5, 1.0, "درآمد +۸٪، ثبات بیشتر، حمله −۵٪"),
    "mon": ("👑 سلطنت", 1.00, 1.05, 1.0, 0.3, 1.0, "دفاع +۵٪، ثبات بیشتر"),
    "mil": ("🪖 حکومت نظامی", 0.92, 1.08, 1.10, 0.0, 1.0, "حمله +۱۰٪، دفاع +۸٪، درآمد −۸٪"),
    "soc": ("☭ سوسیالیسم", 1.05, 1.05, 1.0, 0.0, 0.92, "درآمد +۵٪، دفاع +۵٪، تحقیقات −۸٪"),
}
GOV_COST = 3000
RANKS = ["🔰 سرباز", "🎖 سرجوخه", "🎖 گروهبان", "⭐ ستوان", "⭐⭐ سروان", "⭐⭐⭐ سرگرد", "🦅 سرهنگ",
         "🦅🦅 سرتیپ", "🦅🦅🦅 سرلشکر", "👑 سپهبد", "👑👑 مارشال"]

# ماموریت‌های روزانه: (نوع، توضیح، تعداد)
QUESTS = [
    ("build", "🏗 {n} ساختمان بساز", (3, 8)),
    ("buy", "🛒 {n} تجهیز نظامی بخر", (20, 200)),
    ("attack", "💥 {n} حمله انجام بده", (1, 2)),
    ("fac", "🏭 {n} بار صنایع و معادن رو ارتقا بده", (1, 2)),
    ("deposit", "🏦 {n} بار پول به سپرده‌ی بانکی واریز کن", (1, 2)),
    ("market", "🛢 {n} بار توی بازار منابع یا ارز دیجیتال معامله کن", (1, 3)),
    ("cyber", "💻 {n} عملیات سایبری یا جاسوسی انجام بده", (1, 2)),
    ("deal", "🤝 {n} معامله یا مجوز با کشورهای دیگه ببند", (1, 1)),
]

# ═════════════ پک‌های ویژه (پرداخت به تومان؛ ادمین فعال‌سازی می‌کنه) ═════════════
# آیتم: (برچسب نمایش، نوع [u=تجهیز, r=منبع, p=جمعیت], کلید, مقدار)
PACKS = [
    {"key": "nuke", "name": "پک کلاهک هسته ای☢", "price": 100000, "limit": 0, "items": [
        ("Nuclear warhead", "u", "tnuke", 2)]},
    {"key": "eco", "name": "پک اقتصادی قاتل ابر قدرت💀", "price": 50000, "limit": 0, "items": [
        ("oil", "r", "oil", 500000), ("iron", "r", "iron", 500000), ("Aluminum", "r", "alu", 20000),
        ("gold", "r", "gold", 70000), ("uranium", "r", "uranium", 5000), ("electricity", "r", "elec", 70000),
        ("جمعیت", "p", "pop", 80000000)]},
    {"key": "ground", "name": "پک جهنم زمینی🚛", "price": 35000, "limit": 0, "items": [
        ("oil", "r", "oil", 40000), ("iron", "r", "iron", 50000), ("Soldier", "u", "soldier", 500000),
        ("Leopard 2A7+ Tank", "u", "leo", 20000)]},
    {"key": "vip", "name": "پک اشتراک پرمیوم(VIP)", "price": 30000, "limit": 1, "vip": True,
     "note": "این پک فقط یک بار فعال میشه و شامل افزایش جمعیت افزایش ساخت و ساز افزایش ارتقا بیشتر معادن و مقداری برق",
     "items": [("جمعیت", "p", "pop", 10000000), ("برق", "r", "elec", 50000)]},
    {"key": "drone", "name": "⚠️یورش پهپادی ⚠️", "price": 20000, "limit": 0, "items": [
        ("Shahed 191", "u", "shahed191", 20000), ("Protector RG Mk1 (MQ-9B)", "u", "protector", 4500),
        ("MQ-9B SeaGuardian", "u", "seaguard", 7500), ("MQ-9 Reaper", "u", "mq9", 18000),
        ("CAIG Wing Loong II", "u", "wl2", 10000), ("SDT Patroller", "u", "patroller", 14000)]},
    {"key": "cyber", "name": "یورش سایبری💻", "price": 15000, "limit": 0, "items": [
        ("جمعیت", "p", "pop", 50000000), ("Red_hat", "u", "redhat", 2000), ("white_hat", "u", "whitehat", 2000),
        ("financial", "u", "fin", 1250), ("spy", "u", "spy", 2450), ("electricity", "r", "elec", 24000)]},
    {"key": "def", "name": "دفاع پولادین🛡", "price": 55000, "limit": 0, "items": [
        ("S-500 Prometey", "u", "s500", 850), ("David’s Sling", "u", "davids", 500),
        ("Patriot PAC-3 MSE", "u", "pac3mse", 1200), ("SAMP/T", "u", "sampt", 3000),
        ("Buk-M3 Viking", "u", "bukm3", 9000), ("HQ-9", "u", "hq9", 5000), ("IRIS-T SLM", "u", "iris", 10000)]},
    {"key": "navy", "name": "🚢بمباران دریایی🚢", "price": 45000, "limit": 0, "items": [
        ("USS Abraham Lincoln", "u", "cvn72", 500), ("Atago-class destroyer", "u", "atago", 1000),
        ("Maya-class", "u", "maya", 1500), ("Visakhapatnam", "u", "visakh", 3000)]},
    {"key": "missile", "name": "پک بارش موشکی☄", "price": 50000, "limit": 0, "items": [
        ("GL-2", "u", "gl2", 5000), ("RS-28 Sarmat (Satan II)", "u", "sarmat", 17000),
        ("R-36M2 Voevoda (SS-18 Satan)", "u", "r36", 13500), ("Trident II D5", "u", "trident", 50000),
        ("Iskander-M", "u", "isk", 200000)]},
    {"key": "bomber", "name": "پک بمب افکن💥", "price": 30000, "limit": 0, "items": [
        ("B-2", "u", "b2", 60), ("Tupolev Tu-160", "u", "tu160", 200), ("B-1", "u", "b1", 70),
        ("Avro Vulcan", "u", "vulcan", 100)]},
]
PK = {p["key"]: p for p in PACKS}

# ═════════════ عکس گزارش‌ها ═════════════
IMG_CATS = {
    "war": "⚔️ اعلام جنگ", "battle": "💥 نبرد", "nuke": "☢️ حمله هسته‌ای", "peace": "🕊 صلح",
    "alliance": "🛡 ائتلاف", "union": "🛡 اتحاد", "diplomacy": "🤝 دیپلماسی", "trade": "💱 تجارت",
    "arms": "🛒 خرید تسلیحات", "tech": "🔬 فناوری", "statement": "📜 بیانیه", "event": "🎲 رویداد",
    "newleader": "🏛 رهبر جدید", "pack": "🛍 پک ویژه", "crypto": "₿ ارز دیجیتال", "cyber": "💻 سایبری",
    "build": "🏗 ساخت‌وساز", "bank": "🏦 بانک", "license": "🎫 مجوز تسلیحاتی", "sanction": "🚫 تحریم",
    "wonder": "🏛 شگفتی جهان", "black": "🕶 بازار سیاه", "admin": "📢 اعلامیه ادمین", "general": "📰 عمومی",
}
# هشتگ ← دسته‌ی عکس (بعد از squash)
TAG_CAT = {"اعلامجنگ": "war", "جنگ": "battle", "هستهای": "nuke", "صلح": "peace", "ائتلاف": "alliance",
           "اتحاد": "union", "دیپلماسی": "diplomacy", "تجارت": "trade", "تسلیحات": "arms", "تکنولوژی": "tech",
           "بیانیه": "statement", "رویداد": "event", "کشورجدید": "newleader", "پکویژه": "pack",
           "کریپتو": "crypto", "سایبری": "cyber", "ساختوساز": "build", "بانک": "bank", "مجوز": "license",
           "تحریم": "sanction", "شگفتی": "wonder", "بازارسیاه": "black", "احیا": "newleader",
           "شروعدوباره": "event"}
# عنوان انگلیسی و دو رنگ برای کارت‌های خودکار
CARD_STYLE = {
    "war": ("WAR DECLARED", (120, 10, 20), (30, 5, 10)), "battle": ("BATTLE REPORT", (150, 70, 10), (40, 15, 5)),
    "nuke": ("NUCLEAR STRIKE", (160, 120, 0), (30, 10, 10)), "peace": ("PEACE TREATY", (20, 110, 90), (10, 40, 60)),
    "alliance": ("ALLIANCE FORMED", (20, 70, 150), (8, 20, 60)), "union": ("UNION", (30, 60, 140), (10, 15, 50)),
    "diplomacy": ("DIPLOMACY", (20, 100, 120), (8, 30, 50)), "trade": ("TRADE DEAL", (150, 110, 20), (45, 30, 8)),
    "arms": ("ARMS PURCHASE", (60, 90, 50), (15, 25, 15)), "tech": ("TECH BREAKTHROUGH", (80, 40, 150), (20, 10, 60)),
    "statement": ("OFFICIAL STATEMENT", (25, 45, 90), (8, 12, 30)), "event": ("WORLD EVENT", (110, 40, 130), (30, 10, 45)),
    "newleader": ("NEW LEADER", (150, 120, 20), (40, 30, 8)), "pack": ("SPECIAL PACK", (170, 40, 120), (50, 10, 40)),
    "crypto": ("CRYPTO MARKET", (200, 120, 10), (20, 20, 20)), "cyber": ("CYBER OPERATION", (10, 120, 50), (5, 20, 15)),
    "build": ("CONSTRUCTION", (120, 80, 40), (35, 25, 15)), "bank": ("BANKING", (20, 110, 60), (8, 35, 25)),
    "license": ("ARMS LICENSE", (60, 80, 110), (15, 20, 35)), "sanction": ("SANCTIONS", (130, 30, 30), (35, 10, 10)),
    "wonder": ("WORLD WONDER", (170, 130, 30), (45, 30, 10)), "black": ("BLACK MARKET", (60, 60, 60), (10, 10, 10)),
    "admin": ("ANNOUNCEMENT", (70, 70, 90), (20, 20, 30)), "general": ("WORLD WAR · EMPIRE", (50, 60, 80), (15, 18, 28)),
}


# ═════════════ دیتابیس ═════════════
DB = {}
CTX = {}          # حالت منتظر پاسخ برای هر کاربر
PHOTO = {}        # کالبک منتظر عکس برای هر کاربر
IDENT = set()
SEEN = []
LAST_ROWS = {}   # آخرین دکمه‌های هر کاربر (با هر پیام دوباره فرستاده می‌شن)
LAG = {}         # تأخیر رسیدن آخرین پیام هر کاربر به بات
IMPORT_WAIT = set()  # ادمین‌هایی که منتظر دریافت فایل بازیابی هستند
TICK = {"t": 0.0}
ROUTES = {}
ROUTE_N = {}
REGEX_ROUTES = []


def ensure(c):
    """فیلدهای جدید رو برای کشورهای قدیمی هم می‌سازه (سازگاری با دیتای قبلی)."""
    t = c.get("tier", 1)
    c.setdefault("res", dict(START_RES.get(t, START_RES[1])))
    for k in RES:
        c["res"].setdefault(k, 0.0)
    c.setdefault("pop", float(START_POP.get(t, 5_000_000)))
    c.setdefault("fac", {})
    c.setdefault("cities", [])
    c.setdefault("crypto", {})
    c.setdefault("miners", {})
    c.setdefault("bank", {"deps": [], "loan": 0.0, "loan_t": 0, "warned": 0})
    c.setdefault("union", None)
    c.setdefault("vip", False)
    c.setdefault("stmt_photo", None)
    c.setdefault("packs", {})
    c.setdefault("daily", 0)
    c.setdefault("cd_cy", 0)
    c.setdefault("tax", 1)
    c.setdefault("gov", "")
    c.setdefault("gov_t", 0)
    c.setdefault("xp", 0)
    c.setdefault("quest", {"day": 0, "q": [], "bonus": False})
    c.setdefault("draft_t", 0)
    c.setdefault("propa_t", 0)
    c.setdefault("un_msg_t", 0)
    c.setdefault("sanc_t", 0)
    return c


def make_country(iso, fa, en, tier):
    units = dict(BASE_KIT[tier])
    for k, v in SIG.get(iso, {}).items():
        units[k] = units.get(k, 0) + v
    return ensure({"iso": iso, "fa": fa, "en": en, "tier": tier, "owner": None, "leader": "",
                   "money": float(START_MONEY[tier]), "tech": tier, "eco": 0, "fort": 0,
                   "prov": START_PROV[tier], "stab": 100.0, "units": units, "last": now(),
                   "prot": 0, "cd": 0, "stmt": 0, "alive": True})


def new_db():
    return {"settings": {"channel": None, "paused": False, "speed": 1.0, "protect_h": 12,
                         "admins": [], "auto_events": False, "last_event": 0, "warned": False,
                         "imgs": {}, "bank_dep_mult": 1.0, "bank_loan_mult": 1.0, "lic_on": True,
                         "auto_lic": True, "black_on": True, "black_mult": 2.2, "export_pct": 0.10,
                         "seed_v": 0, "img_on": True},
            "users": {}, "countries": {}, "wars": [], "allies": [], "props": [],
            "requests": [], "log": [], "ctr": 0, "offset": None, "admin_code": None,
            "unions": {}, "market": {}, "licenses": [], "sanctions": [], "wonders": {}, "pack_log": []}


def seed_countries():
    DB["countries"] = {}
    for iso, fa, en, tier in COUNTRIES:
        DB["countries"][iso] = make_country(iso, fa, en, tier)
    DB["settings"]["seed_v"] = SEED_V


def init_market():
    mk = DB.setdefault("market", {})
    mk.setdefault("t", 0)
    mk.setdefault("res", {})
    for k in RES:
        mk["res"].setdefault(k, 1.0)
    co = mk.setdefault("coins", {})
    for sym, d in COINS.items():
        co.setdefault(sym, {"p": d["p"], "hist": [d["p"]]})


def load():
    global DB
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            DB = json.load(f)
        base = new_db()
        for k, v in base.items():
            DB.setdefault(k, v)
        for k, v in base["settings"].items():
            DB["settings"].setdefault(k, v)
        if isinstance(DB.get("wonders"), list):
            DB["wonders"] = {}
    else:
        DB = new_db()
        seed_countries()
    if not isinstance(DB.get("wonders"), dict):
        DB["wonders"] = {}
    if DB["settings"].get("seed_v", 0) < SEED_V:      # کشورهای جدید رو به بازی قدیمی اضافه کن
        for iso, fa, en, tier in COUNTRIES:
            if iso not in DB["countries"]:
                DB["countries"][iso] = make_country(iso, fa, en, tier)
        DB["settings"]["seed_v"] = SEED_V
    for c in DB["countries"].values():
        ensure(c)
    init_market()
    for a in ADMIN_IDS:
        if a not in DB["settings"]["admins"]:
            DB["settings"]["admins"].append(a)
    DB["settings"]["admins"] = list(dict.fromkeys(DB["settings"]["admins"]))
    DB["settings"]["channel"] = DB["settings"].get("channel") or CHANNEL
    if not DB.get("admin_code"):
        DB["admin_code"] = "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(8))
    save()


def save():
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False)
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, DATA_FILE)


def nid():
    DB["ctr"] += 1
    return DB["ctr"]


def admin_code():
    return ADMIN_CODE or DB["admin_code"]


def C(iso):
    return DB["countries"].get(iso)


def cname(c):
    return "%s %s" % (flag(c["iso"]), c["fa"])


def user(uid, chat=None):
    u = DB["users"].get(uid)
    if u is None:
        u = {"country": None, "banned": False, "chat": chat or uid, "name": "", "uname": "", "seen": now()}
        DB["users"][uid] = u
    if chat:
        u["chat"] = chat
    return u


def ulabel(uid):
    u = DB["users"].get(uid, {})
    base = u.get("name") or ("کاربر " + str(uid)[-5:])
    return base + ((" @" + u["uname"]) if u.get("uname") else "")


def mine(uid):
    iso = DB["users"].get(uid, {}).get("country")
    c = C(iso) if iso else None
    return c if c and c["alive"] and c["owner"] == uid else None


def is_admin(uid):
    return uid in DB["settings"]["admins"]


def at_war(a, b):
    return any({a, b} == {w[0], w[1]} for w in DB["wars"])


def enemies(iso):
    return [w[1] if w[0] == iso else w[0] for w in DB["wars"] if iso in (w[0], w[1])]


def add_war(a, b):
    if not at_war(a, b):
        DB["wars"].append([a, b, now()])


def end_war(a, b):
    DB["wars"] = [w for w in DB["wars"] if {a, b} != {w[0], w[1]}]


def pact_allies(iso):
    return [x[1] if x[0] == iso else x[0] for x in DB["allies"] if iso in (x[0], x[1])]


def is_ally(a, b):
    return b in allies_of(a)


def allies_of(iso):
    """متحدان = پیمان‌های دوجانبه + اعضای هم‌اتحادی."""
    out = list(pact_allies(iso))
    c = DB["countries"].get(iso)
    un = un_get(c) if c else None
    if un:
        for i in un["members"]:
            if i != iso and i not in out and DB["countries"].get(i, {}).get("alive"):
                out.append(i)
    return out


# ───── اتحادها ─────
def un_get(c):
    uid = c.get("union") if c else None
    return DB["unions"].get(str(uid)) if uid else None


def un_members(un):
    return [i for i in un["members"] if DB["countries"].get(i) and DB["countries"][i]["alive"]]


def un_cap(un):
    return int(un.get("capx") or (4 + 2 * un["lvl"]))


def un_up_cost(un):
    return int(8000 * un["lvl"] ** 1.8)


def un_power(un):
    return sum(power(DB["countries"][i]) for i in un_members(un))


def un_role(un, iso):
    return "leader" if un["leader"] == iso else ("officer" if iso in un["officers"] else "member")


def un_log(un, text):
    un["log"].append([now(), text])
    del un["log"][:-30]


def un_tell(un, text, skip=None):
    for i in un_members(un):
        if i != skip:
            notify_country(i, text)


def union_lvl(c):
    un = un_get(c)
    return un["lvl"] if un else 0


def un_label(un):
    return "%s %s" % (un["emoji"], un["name"])


def un_remove(iso, why=""):
    c = DB["countries"].get(iso)
    if not c:
        return
    un = un_get(c)
    c["union"] = None
    if not un:
        return
    if iso in un["members"]:
        un["members"].remove(iso)
    if iso in un["officers"]:
        un["officers"].remove(iso)
    left = un_members(un)
    if not left:
        DB["unions"].pop(str(un["id"]), None)
        announce("💥 اتحاد «%s» منحل شد.\n#اتحاد" % un_label(un), cat="union")
        return
    if un["leader"] == iso:
        succ = next((i for i in un["officers"] if i in left), left[0])
        un["leader"] = succ
        if succ in un["officers"]:
            un["officers"].remove(succ)
        un_tell(un, "👑 رهبر جدید اتحاد «%s»: %s" % (un_label(un), cname(DB["countries"][succ])))
    un_log(un, "%s از اتحاد خارج شد%s" % (cname(c), (" (%s)" % why) if why else ""))


def union_help(de, att):
    """کمک دفاعی هم‌اتحادی‌ها: بخشی از دفاعشون به مدافع اضافه می‌شه."""
    un = un_get(de)
    if not un:
        return 0.0
    share = 0.15 + 0.02 * un["lvl"]
    s = 0.0
    for i in un_members(un):
        if i in (de["iso"], att["iso"]):
            continue
        s += defense(DB["countries"][i]) * share
    return s


# ───── مجوزهای تسلیحاتی ─────
def lic_valid(l):
    if l["kind"] == "count" and l.get("qty", 0) <= 0:
        return False
    if l.get("exp") and l["exp"] < now():
        return False
    return True


def lic_covers(l, key):
    u = U[key]
    if l["from"] not in u["org"] or u["cat"] == "nuke":
        return False
    sc = l["scope"]
    if sc["t"] == "all":
        return True
    if sc["t"] == "cat":
        return u["cat"] in SHOP.get(sc.get("c"), [])
    return sc.get("k") == key


def sanc_active():
    t = now()
    return [s for s in DB["sanctions"] if s["until"] > t]


def sanctioned_between(a, b):
    return any({s["by"], s["on"]} == {a, b} for s in sanc_active())


def sanc_count(iso):
    return sum(1 for s in sanc_active() if s["on"] == iso)


def sanc_mult(c):
    return 1.0 - 0.06 * min(5, sanc_count(c["iso"]))


def my_licenses(iso, key=None):
    out = []
    for l in DB["licenses"]:
        if l["to"] == iso and lic_valid(l) and (key is None or lic_covers(l, key)):
            if not sanctioned_between(l["from"], iso):
                out.append(l)
    return out


def unit_access(c, key):
    """چطور می‌تونه این تجهیز رو بخره؟ own=ساخت خودش | generic=عمومی | lic=با مجوز | none=قفل"""
    u = U[key]
    iso = c["iso"]
    if not DB["settings"].get("lic_on", True):
        return {"how": "own", "cap": None}
    if not u["org"]:
        return {"how": "generic", "cap": None}
    if iso in u["org"]:
        return {"how": "own", "cap": None}
    if u["cat"] == "nuke":
        return {"how": "none", "cap": 0}
    ls = my_licenses(iso, key)
    if not ls:
        return {"how": "none", "cap": 0}
    free = [l for l in ls if l["kind"] in ("perm", "paid")]
    if free:
        return {"how": "lic", "cap": None, "lic": free[0], "lics": free}
    return {"how": "lic", "cap": sum(l["qty"] for l in ls), "lic": ls[0], "lics": ls}


def lic_consume(c, key, n):
    """بعد از خرید: از مجوزهای عددی کم می‌کنه و کشور صادرکننده رو برمی‌گردونه."""
    acc = unit_access(c, key)
    if acc["how"] != "lic":
        return None
    if acc["cap"] is None:
        l = acc["lic"]
        l["used"] = l.get("used", 0) + n
        return l["from"]
    left = n
    for l in acc["lics"]:
        take = min(left, l["qty"])
        l["qty"] -= take
        l["used"] = l.get("used", 0) + take
        left -= take
        if left <= 0:
            break
    return acc["lic"]["from"]


def lic_new(frm, to, scope, kind, qty=0, hours=0, price=0.0):
    l = {"id": nid(), "from": frm, "to": to, "scope": scope, "kind": kind,
         "qty": int(qty) if kind == "count" else 0, "tot": int(qty) if kind == "count" else 0,
         "exp": (now() + hours * 3600) if (kind == "paid" and hours) else 0,
         "hours": hours, "price": float(price), "t": now(), "used": 0}
    DB["licenses"].append(l)
    return l


def lic_std_price(key, kind, qty=0, hours=0):
    cost = U[key]["cost"]
    if kind == "perm":
        return max(50.0, cost * 30)
    if kind == "paid":
        return max(25.0, cost * 2.0 * hours / 24.0)
    return max(20.0, cost * qty * 0.08)


def scope_text(sc):
    if sc["t"] == "all":
        return "🔰 همه‌ی تجهیزات"
    if sc["t"] == "cat":
        return "📂 " + str(sc.get("c"))
    k = sc.get("k")
    return "🎯 " + (U[k]["name"] if k in U else str(k))


def kind_text(l):
    if l["kind"] == "perm":
        return "🔓 دائمی"
    if l["kind"] == "paid":
        left = (l["exp"] - now()) if l.get("exp") else 0
        return "💰 زمان‌دار (%s مانده)" % dur(left) if l.get("exp") else "💰 در ازای پول"
    return "🔢 عددی (%s از %s باقی)" % (m(l.get("qty", 0)), m(l.get("tot", 0)))


def lic_text(l):
    a, b = DB["countries"].get(l["from"]), DB["countries"].get(l["to"])
    return "🎫 #%d  از %s برای %s\n    %s | %s%s" % (
        l["id"], cname(a) if a else l["from"], cname(b) if b else l["to"], scope_text(l["scope"]), kind_text(l),
        (" | 💵 %s M$" % m(l["price"])) if l.get("price") else "")


def terms_text(t):
    s = {"perm": "🔓 دائمی", "paid": "💰 در ازای پول — %s ساعت" % m(t.get("hours", 0)),
         "count": "🔢 عددی — %s عدد" % m(t.get("qty", 0))}[t["kind"]]
    return "%s | 💵 قیمت مجوز: %s M$" % (s, m(t.get("price", 0)))


# ───── شگفتی‌ها ─────
def wonder_has(c, key):
    return DB["wonders"].get(key) == c["iso"]


def wonders_of(c):
    return [k for k in WD if DB["wonders"].get(k) == c["iso"]]


def wonder_release(iso):
    for k in [k for k, v in DB["wonders"].items() if v == iso]:
        del DB["wonders"][k]


# ───── بازار ─────
def res_price(k):
    return RES_PRICE[k] * DB["market"]["res"].get(k, 1.0) * strait_mult(k)


def coin_price(sym):
    return DB["market"]["coins"][sym]["p"]


def crypto_value(c):
    return sum(a * coin_price(s) for s, a in c["crypto"].items() if s in COINS)


def fp(x):
    x = float(x)
    if x >= 100:
        return "{:,.0f}".format(x)
    if x >= 1:
        return "{:,.2f}".format(x)
    if x >= 0.01:
        return "{:.4f}".format(x)
    return "{:.6f}".format(x)


SPARK = "▁▂▃▄▅▆▇█"


def spark(vals, n=24):
    vals = list(vals)[-n:]
    if len(vals) < 2:
        return "▁" * len(vals)
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return SPARK[3] * len(vals)
    return "".join(SPARK[min(7, int((v - lo) / (hi - lo) * 7.999))] for v in vals)




# ═════════════ ارتباط با تلگرام ═════════════
class ApiError(Exception):
    pass


def _session():
    s = getattr(_TL, "s", None)
    if s is None:
        s = _TL.s = requests.Session()
    return s


# زمان‌بندی سراسری درخواست‌های خروجی؛ getUpdates از این صف عبور نمی‌کند.
_API_RATE_LOCK = threading.Lock()
_API_LAST_GLOBAL = 0.0
_API_LAST_CHAT = {}
_API_SEND_METHODS = {"sendMessage", "sendPhoto", "sendDocument", "sendVideo", "sendAudio", "sendMediaGroup"}


def _wait_api_slot(method, params):
    global _API_LAST_GLOBAL
    if method not in _API_SEND_METHODS:
        return
    chat = str((params or {}).get("chat_id") or "")
    if not chat:
        return
    # برای کانال/گروه فاصله بیشتر از چت خصوصی در نظر گرفته می‌شود.
    gap = API_GROUP_GAP if chat.startswith("-") or chat.startswith("@") else API_PRIVATE_GAP
    with _API_RATE_LOCK:
        t = time.monotonic()
        wait_global = API_GLOBAL_GAP - (t - _API_LAST_GLOBAL)
        wait_chat = gap - (t - _API_LAST_CHAT.get(chat, 0.0))
        wait_for = max(0.0, wait_global, wait_chat)
        if wait_for:
            time.sleep(wait_for)
        sent_at = time.monotonic()
        _API_LAST_GLOBAL = sent_at
        _API_LAST_CHAT[chat] = sent_at
        # جلوگیری از رشد نامحدود حافظه در بات‌های پرترافیک
        if len(_API_LAST_CHAT) > 5000:
            cutoff = sent_at - 600
            for key, value in list(_API_LAST_CHAT.items()):
                if value < cutoff:
                    _API_LAST_CHAT.pop(key, None)


def api(method, params=None, read_timeout=20):
    url = "%s/bot%s/%s" % (API_HOST, TOKEN, method)
    last = None
    attempts = 5 if method == "getUpdates" else 4
    for attempt in range(attempts):
        _wait_api_slot(method, params)
        t0 = time.time()
        try:
            r = _session().post(url, json=params or {}, timeout=(8, read_timeout))
            js = r.json()
        except (requests.RequestException, ValueError) as e:
            last = e
            _TL.s = None
            # backoff افزایشی + jitter برای جلوگیری از موج درخواست هم‌زمان
            if attempt + 1 < attempts:
                time.sleep(min(12.0, 1.0 * (2 ** attempt)) + random.uniform(0.1, 0.6))
            continue
        dt = time.time() - t0
        if dt > 4 and method != "getUpdates":
            print("⏱ %s کند بود: %.1f ثانیه" % (method, dt))
        if js.get("ok"):
            return js
        code = js.get("error_code")
        if code == 429:
            retry_after = (js.get("parameters") or {}).get("retry_after", 5)
            try:
                retry_after = max(1.0, min(3600.0, float(retry_after)))
            except (TypeError, ValueError):
                retry_after = 5.0
            print("⚠️ محدودیت نرخ تلگرام؛ توقف %.1f ثانیه‌ای" % retry_after)
            time.sleep(retry_after + random.uniform(0.2, 0.8))
            continue
        raise ApiError("%s: %s %s" % (method, code, js.get("description")))
    raise last if last else ApiError("%s: ناموفق" % method)


def reply_markup(rows):
    return {"keyboard": [[{"text": b} for b in row] for row in rows if row],
            "resize_keyboard": True, "is_persistent": True}


def send(chat, text, rows=None):
    ok = True
    parts = split_text(text)
    for i, part in enumerate(parts):
        body = {"chat_id": chat, "text": part}
        if rows and i == len(parts) - 1:
            body["reply_markup"] = reply_markup(rows)
        try:
            api("sendMessage", body)
        except Exception as e:  # noqa: BLE001
            ok = False
            print("send error:", e)
    return ok


SENT_KP = {}   # آخرین دکمه‌هایی که واقعاً برای هر کاربر فرستاده شد


def tell(uid, text, rows=None, force=False):
    """دکمه‌ها فقط وقتی فرستاده می‌شن که عوض شده باشن."""
    chat = DB["users"].get(uid, {}).get("chat") or uid
    if DB["users"].get(uid, {}).get("lang") == "en":
        try:
            text, rows = en_ui(uid, text, rows)
        except Exception as e:  # noqa: BLE001
            print("en_ui error:", repr(e)[:150])
    if rows:
        LAST_ROWS[uid] = rows
    else:
        rows = LAST_ROWS.get(uid)
    sig = json.dumps(rows, ensure_ascii=False) if rows else None
    attach = rows if (rows and (force or SENT_KP.get(uid) != sig)) else None
    ok = send(chat, text, attach)
    if attach and ok:
        SENT_KP[uid] = sig


def notify_country(iso, text):
    c = C(iso)
    if c and c["owner"]:
        tell(c["owner"], text)


def notify_admins(text, rows=None):
    for a in DB["settings"]["admins"]:
        tell(a, text, rows)
    if not DB["settings"]["admins"]:
        print("[ADMIN]", text)


def api_form(method, data, files, read_timeout=40):
    """ارسال multipart (برای آپلود عکس)؛ مثل api() با پروکسی و تلاش مجدد."""
    url = "%s/bot%s/%s" % (API_HOST, TOKEN, method)
    last = None
    for attempt in range(4):
        _wait_api_slot(method, data)
        try:
            r = _session().post(url, data=data, files=files, timeout=(8, read_timeout))
            js = r.json()
        except (requests.RequestException, ValueError) as e:
            last = e
            _TL.s = None
            if attempt + 1 < 4:
                time.sleep(min(12.0, 1.0 * (2 ** attempt)) + random.uniform(0.1, 0.6))
            continue
        if js.get("ok"):
            return js
        if js.get("error_code") == 429:
            retry_after = (js.get("parameters") or {}).get("retry_after", 5)
            try:
                retry_after = max(1.0, min(3600.0, float(retry_after)))
            except (TypeError, ValueError):
                retry_after = 5.0
            print("⚠️ محدودیت نرخ تلگرام در آپلود؛ توقف %.1f ثانیه‌ای" % retry_after)
            time.sleep(retry_after + random.uniform(0.2, 0.8))
            continue
        raise ApiError("%s: %s %s" % (method, js.get("error_code"), js.get("description")))
    raise last if last else ApiError("%s: ناموفق" % method)


# ───── کارت‌های تصویری خودکار برای گزارش‌ها ─────
_FONTS = {}


def _font(size):
    f = _FONTS.get(size)
    if f:
        return f
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try:
            f = ImageFont.truetype(name, size)
            break
        except Exception:  # noqa: BLE001
            f = None
    if f is None:
        try:
            f = ImageFont.load_default(size)
        except Exception:  # noqa: BLE001
            f = ImageFont.load_default()
    _FONTS[size] = f
    return f


def _fit(d, text, maxw, size):
    while size > 18:
        f = _font(size)
        try:
            w = d.textlength(text, font=f)
        except Exception:  # noqa: BLE001
            w = len(text) * size * 0.6
        if w <= maxw:
            return f
        size -= 4
    return _font(18)


def _orn(d, cat, cx, cy, r, col):
    fill = col + (185,)
    w = 16
    if cat == "nuke":
        box = [cx - r, cy - r, cx + r, cy + r]
        for a in (-90, 30, 150):
            d.pieslice(box, a - 30, a + 30, fill=fill)
        rr = r // 5
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fill)
    elif cat in ("war", "battle"):
        pts = []
        for i in range(24):
            ang = math.pi * 2 * i / 24
            rad = r if i % 2 == 0 else r * 0.55
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        d.polygon(pts, fill=fill)
    elif cat == "peace":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fill, width=w)
        d.line([cx, cy - r, cx, cy + r], fill=fill, width=w)
        d.line([cx, cy, cx - int(r * .7), cy + int(r * .7)], fill=fill, width=w)
        d.line([cx, cy, cx + int(r * .7), cy + int(r * .7)], fill=fill, width=w)
    elif cat in ("alliance", "union", "diplomacy"):
        rr = int(r * .65)
        d.ellipse([cx - rr - rr // 2, cy - rr, cx + rr // 2 - rr // 2 + 0, cy + rr], outline=fill, width=w)
        d.ellipse([cx - rr // 2 + rr // 2, cy - rr, cx + rr + rr // 2, cy + rr], outline=fill, width=w)
    elif cat in ("trade", "bank", "pack", "crypto", "license", "black", "admin", "general"):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
        d.ellipse([cx - int(r * .82), cy - int(r * .82), cx + int(r * .82), cy + int(r * .82)], outline=(0, 0, 0, 120), width=8)
        sym = {"trade": "$", "bank": "$", "pack": "★", "crypto": "B", "license": "✓", "black": "?", "admin": "!"}.get(cat, "W")
        d.text((cx, cy), sym, font=_font(int(r * 1.2)), fill=(0, 0, 0, 170), anchor="mm")
    elif cat == "cyber":
        rnd = random.Random(7)
        for x in range(cx - r - 40, cx + r + 40, 34):
            for y in range(cy - r - 20, cy + r + 20, 38):
                d.text((x, y), rnd.choice("01"), font=_font(26), fill=(0, 255, 120, rnd.randint(40, 170)))
    elif cat == "build":
        base = cy + r
        for i in range(7):
            h = 90 + (i * 53) % 190
            x0 = cx - r + i * int(r * 2 / 7)
            d.rectangle([x0, base - h, x0 + int(r * 2 / 7) - 8, base], fill=fill)
    elif cat == "tech":
        for k, rad in enumerate((r, int(r * .62))):
            pts = [(cx + rad * math.cos(math.pi / 3 * i), cy + rad * math.sin(math.pi / 3 * i)) for i in range(6)]
            d.polygon(pts, outline=fill, width=w) if k == 0 else d.polygon(pts, fill=fill)
    elif cat == "event":
        d.polygon([(cx - 40, cy - r), (cx + 70, cy - 10), (cx + 10, cy - 10), (cx + 60, cy + r),
                   (cx - 70, cy + 40), (cx - 5, cy + 40)], fill=fill)
    elif cat == "statement":
        d.rounded_rectangle([cx - r // 1.4, cy - r, cx + r // 1.4, cy + r], radius=24, fill=fill)
        for i in range(5):
            y = cy - r + 60 + i * 70
            d.line([cx - r // 2, y, cx + r // 2, y], fill=(0, 0, 0, 110), width=10)
    elif cat in ("arms", "sanction"):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fill, width=w)
        if cat == "arms":
            d.line([cx - r - 30, cy, cx + r + 30, cy], fill=fill, width=10)
            d.line([cx, cy - r - 30, cx, cy + r + 30], fill=fill, width=10)
        else:
            d.line([cx - int(r * .7), cy + int(r * .7), cx + int(r * .7), cy - int(r * .7)], fill=fill, width=w)
    else:  # newleader / wonder / ...
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + math.pi * i / 5
            rad = r if i % 2 == 0 else r * .42
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        d.polygon(pts, fill=fill)


def make_card(cat, isos=()):
    """عکس گزارش بدون نیاز به اینترنت/فایل؛ نیاز: pip install pillow (اختیاری)."""
    if Image is None:
        return None
    try:
        title, c1, c2 = CARD_STYLE.get(cat) or CARD_STYLE["general"]
        W, H = 1280, 720
        img = Image.new("RGB", (W, H), c1)
        g = ImageDraw.Draw(img)
        for y in range(H):
            t = y / (H - 1)
            g.line([(0, y), (W, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for x in range(-H, W, 90):
            od.polygon([(x, H), (x + 40, H), (x + 40 + H, 0), (x + H, 0)], fill=(255, 255, 255, 9))
        acc = tuple(min(255, int(v * 1.7 + 70)) for v in c1)
        od.ellipse([W - 640, -140, W + 160, 660], fill=acc + (34,))
        try:
            _orn(od, cat, 960, 330, 175, acc)
        except Exception as e:  # noqa: BLE001
            print("ornament error:", e)
        img = Image.alpha_composite(img.convert("RGBA"), ov)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 20, H], fill=acc + (255,))
        d.text((84, 120), "WORLD WAR · EMPIRE", font=_font(30), fill=acc + (255,))
        d.text((84, 190), title, font=_fit(d, title, 760, 88), fill=(255, 255, 255, 255))
        isos = [i for i in isos if i][:2]
        sep = "VS" if cat in ("war", "battle", "nuke") else "&"
        x = 84
        for n, iso in enumerate(isos):
            if n:
                d.text((x + 14, 470), sep, font=_font(48), fill=acc + (255,), anchor="lm")
                x += 100
            d.rounded_rectangle([x, 410, x + 230, 530], radius=26, fill=(0, 0, 0, 120), outline=acc + (255,), width=4)
            d.text((x + 115, 470), iso.upper(), font=_font(72), fill=(255, 255, 255, 255), anchor="mm")
            x += 250
        d.text((84, 640), "@" + CHANNEL_USERNAME, font=_font(32), fill=(255, 255, 255, 200))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "PNG", optimize=True)
        return buf.getvalue()
    except Exception as e:  # noqa: BLE001
        print("make_card error:", e)
        return None


# ═════════════ تصویرسازی گزارش‌ها (صحنه‌های واقعی‌تر؛ بدون نیاز به اینترنت) ═════════════
SW, SH = 1280, 720


def _canvas(top, bot):
    img = Image.new("RGBA", (SW, SH), tuple(top) + (255,))
    g = ImageDraw.Draw(img)
    for y in range(SH):
        t = y / (SH - 1)
        g.line([(0, y), (SW, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,))
    return img, ImageDraw.Draw(img, "RGBA")


def _glow(img, x, y, r, col, alpha=140):
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([x - r, y - r, x + r, y + r], fill=tuple(col) + (alpha,))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(max(4, r / 2.2))))


def _bx(a, b, c, e):
    return [min(a, c), min(b, e), max(a, c), max(b, e)]


def _stars(d, n=80, seed=1, ymax=320):
    r = random.Random(seed)
    for _ in range(n):
        x, y, s = r.randint(0, SW), r.randint(0, ymax), r.choice((1, 1, 2, 3))
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, r.randint(90, 230)))


def _cloud(d, x, y, s=1.0, col=(255, 255, 255, 190)):
    for dx, dy, rr in ((0, 0, 40), (45, -15, 50), (95, 0, 40), (45, 12, 45)):
        d.ellipse([x + (dx - rr) * s, y + (dy - rr) * s, x + (dx + rr) * s, y + (dy + rr) * s], fill=col)


def _hills(d, y, col, seed=3, amp=70, step=110):
    r = random.Random(seed)
    pts = [(0, SH)] + [(x, y - r.randint(0, amp)) for x in range(0, SW + step, step)] + [(SW, SH)]
    d.polygon(pts, fill=col)


def _skyline(d, y, col, seed=5, wmin=40, wmax=95, hmin=60, hmax=260, lit=(255, 220, 120, 140)):
    r = random.Random(seed)
    x = -10
    while x < SW:
        w, h = r.randint(wmin, wmax), r.randint(hmin, hmax)
        d.rectangle([x, y - h, x + w, y], fill=col)
        for wy in range(y - h + 12, y - 8, 22):
            for wx in range(x + 8, x + w - 8, 16):
                if r.random() < .33:
                    d.rectangle([wx, wy, wx + 6, wy + 9], fill=lit)
        x += w + r.randint(0, 8)


def _tree(d, x, y, s=1.0, col=(40, 130, 60, 255)):
    d.rectangle([x - 6 * s, y - 50 * s, x + 6 * s, y], fill=(90, 60, 40, 255))
    for dx, dy, rr in ((0, -85, 42), (-28, -60, 32), (28, -60, 32)):
        d.ellipse([x + (dx - rr) * s, y + (dy - rr) * s, x + (dx + rr) * s, y + (dy + rr) * s], fill=col)


def _wins(d, x, y, w, h, cols, rows, on=(255, 225, 130, 255), off=(60, 70, 95, 255), seed=2):
    r = random.Random(seed)
    cw, ch = w / cols, h / rows
    for i in range(cols):
        for j in range(rows):
            d.rectangle([x + i * cw + cw * .2, y + j * ch + ch * .2, x + (i + 1) * cw - cw * .2, y + (j + 1) * ch - ch * .2],
                        fill=on if r.random() < .6 else off)


def _boom(img, d, x, y, r):
    _glow(img, x, y, r * 1.7, (255, 140, 30), 170)
    for k, (rad, col) in enumerate(((1.0, (190, 35, 20, 255)), (0.76, (255, 110, 20, 255)), (0.5, (255, 205, 60, 255)), (0.24, (255, 250, 210, 255)))):
        pts = []
        for i in range(18):
            ang = math.pi * 2 * i / 18 + k * 0.25
            rr = r * rad * (1.0 if i % 2 == 0 else 0.6)
            pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
        d.polygon(pts, fill=col)


def _smoke(d, x, y, n=7, s=1.0, col=(40, 40, 45)):
    r = random.Random(int(x + y))
    for i in range(n):
        rr = (26 + i * 9) * s
        d.ellipse([x + r.randint(-18, 18) * s - rr, y - i * 38 * s - rr, x + r.randint(-18, 18) * s + rr, y - i * 38 * s + rr],
                  fill=col + (max(40, 190 - i * 22),))


def _tank(d, x, y, s=1.0, col=(74, 90, 62, 255), face=1):
    dk = tuple(max(0, v - 30) for v in col[:3]) + (255,)
    d.rounded_rectangle([x - 92 * s, y - 28 * s, x + 92 * s, y], radius=14 * s, fill=(38, 38, 40, 255))
    for i in range(-3, 4):
        d.ellipse([x + i * 24 * s - 10 * s, y - 24 * s, x + i * 24 * s + 10 * s, y - 4 * s], fill=(95, 95, 98, 255))
    d.polygon([(x - 82 * s, y - 28 * s), (x + 82 * s, y - 28 * s), (x + 62 * s, y - 56 * s), (x - 62 * s, y - 56 * s)], fill=col)
    d.rounded_rectangle([x - 38 * s, y - 86 * s, x + 38 * s, y - 54 * s], radius=10 * s, fill=dk)
    bx = x + face * 38 * s
    d.rectangle(_bx(bx, y - 76 * s, bx + face * 100 * s, y - 66 * s), fill=dk)
    d.ellipse(_bx(bx + face * 94 * s, y - 80 * s, bx + face * 112 * s, y - 62 * s), fill=dk)


def _jet(d, x, y, s=1.0, col=(205, 210, 220, 255), face=1, tilt=0.0):
    ca, sa = math.cos(tilt), math.sin(tilt)

    def P(px, py):
        px, py = px * face, py
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)

    d.polygon([P(-90, 0), P(-60, -11), P(40, -11), P(105, 0), P(40, 11), P(-60, 11)], fill=col)
    d.polygon([P(-5, -4), P(-55, -64), P(-30, -64), P(35, -4)], fill=tuple(max(0, v - 25) for v in col[:3]) + (255,))
    d.polygon([P(-5, 4), P(-55, 64), P(-30, 64), P(35, 4)], fill=tuple(max(0, v - 25) for v in col[:3]) + (255,))
    d.polygon([P(-84, -6), P(-104, -38), P(-86, -38), P(-62, -6)], fill=col)
    a, b = P(28, -10), P(62, 4)
    d.ellipse(_bx(a[0], a[1], b[0], b[1]), fill=(90, 160, 220, 255))
    a, b = P(-100, -4), P(-150, 4)
    d.polygon([P(-92, -5), P(-150, 0), P(-92, 5)], fill=(255, 170, 50, 220))


def _ship(d, x, y, s=1.0, col=(112, 122, 138, 255), face=1):
    d.polygon([(x - 150 * s, y - 30 * s), (x + 150 * s, y - 30 * s), (x + face * 175 * s, y - 38 * s), (x + 118 * s, y + 6 * s), (x - 118 * s, y + 6 * s)], fill=col)
    d.rectangle([x - 70 * s, y - 62 * s, x + 50 * s, y - 30 * s], fill=tuple(min(255, v + 25) for v in col[:3]) + (255,))
    d.rectangle([x - 30 * s, y - 92 * s, x + 20 * s, y - 62 * s], fill=tuple(min(255, v + 45) for v in col[:3]) + (255,))
    d.line([(x - 5 * s, y - 92 * s), (x - 5 * s, y - 128 * s)], fill=(60, 60, 66, 255), width=max(2, int(4 * s)))
    d.rectangle(_bx(x + face * 90 * s, y - 52 * s, x + face * 140 * s, y - 44 * s), fill=(70, 74, 82, 255))
    d.rectangle(_bx(x + face * 120 * s, y - 56 * s, x + face * 160 * s, y - 50 * s), fill=(70, 74, 82, 255))


def _missile(d, x, y, ang, s=1.0, col=(232, 232, 238, 255), trail=420):
    ca, sa = math.cos(ang), math.sin(ang)

    def T(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)

    for i in range(8):                                    # دنباله‌ی دود
        a, b = T(-80 - i * trail / 8, 0), T(-80 - (i + 1) * trail / 8, 0)
        rr = (10 + i * 3) * s
        d.ellipse([a[0] - rr, a[1] - rr, a[0] + rr, a[1] + rr], fill=(235, 235, 240, max(30, 150 - i * 18)))
    d.polygon([T(-70, -9), T(40, -9), T(80, 0), T(40, 9), T(-70, 9)], fill=col)
    d.polygon([T(-70, -9), T(-96, -27), T(-52, -9)], fill=(200, 48, 48, 255))
    d.polygon([T(-70, 9), T(-96, 27), T(-52, 9)], fill=(200, 48, 48, 255))
    d.polygon([T(-72, -6), T(-122, 0), T(-72, 6)], fill=(255, 175, 45, 235))


def _mushroom(img, d, x, y, s=1.0):
    _glow(img, x, y - 200 * s, 290 * s, (255, 150, 40), 150)
    d.polygon([(x - 30 * s, y), (x + 30 * s, y), (x + 20 * s, y - 170 * s), (x - 20 * s, y - 170 * s)], fill=(125, 92, 70, 255))
    for dx, dy, rr, col in ((0, -240, 118, (225, 105, 38, 255)), (-86, -205, 74, (190, 78, 30, 255)), (86, -205, 74, (190, 78, 30, 255)),
                            (-48, -275, 66, (255, 165, 58, 255)), (48, -275, 66, (255, 165, 58, 255)), (0, -300, 70, (255, 200, 90, 255))):
        d.ellipse([x + (dx - rr) * s, y + (dy - rr) * s, x + (dx + rr) * s, y + (dy + rr) * s], fill=col)


def _coin(d, x, y, r, sym="$", col=(245, 190, 40, 255)):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    d.ellipse([x - r * .8, y - r * .8, x + r * .8, y + r * .8], outline=(190, 130, 10, 255), width=max(3, int(r / 9)))
    d.text((x, y), sym, font=_font(int(r * 1.25)), fill=(150, 95, 5, 255), anchor="mm")


def _dove(d, x, y, s=1.0, col=(250, 250, 255, 255)):
    d.ellipse([x - 60 * s, y - 22 * s, x + 50 * s, y + 26 * s], fill=col)
    d.ellipse([x + 30 * s, y - 42 * s, x + 74 * s, y - 2 * s], fill=col)
    d.polygon([(x + 72 * s, y - 24 * s), (x + 98 * s, y - 18 * s), (x + 72 * s, y - 12 * s)], fill=(250, 170, 60, 255))
    d.polygon([(x - 20 * s, y - 12 * s), (x - 90 * s, y - 100 * s), (x - 10 * s, y - 70 * s), (x + 30 * s, y - 14 * s)], fill=(235, 238, 248, 255))
    d.polygon([(x - 50 * s, y), (x - 130 * s, y + 8 * s), (x - 60 * s, y + 24 * s)], fill=(225, 230, 242, 255))
    d.ellipse([x + 52 * s, y - 30 * s, x + 60 * s, y - 22 * s], fill=(30, 30, 40, 255))
    d.arc([x + 40 * s, y + 10 * s, x + 200 * s, y + 80 * s], 200, 330, fill=(80, 150, 70, 255), width=max(3, int(6 * s)))
    for i in range(5):
        ex, ey = x + (70 + i * 26) * s, y + (50 - abs(i - 2) * 6 + i * 2) * s
        d.ellipse([ex - 9 * s, ey - 5 * s, ex + 9 * s, ey + 5 * s], fill=(90, 170, 80, 255))


def _flag(d, x, y, s=1.0, cols=((200, 40, 40), (250, 250, 250), (40, 70, 170)), h=120):
    d.rectangle([x - 4 * s, y - h * s - 20 * s, x + 4 * s, y], fill=(170, 170, 175, 255))
    d.ellipse([x - 8 * s, y - h * s - 30 * s, x + 8 * s, y - h * s - 14 * s], fill=(235, 190, 60, 255))
    fh = 70 * s / len(cols)
    for i, c in enumerate(cols):
        d.polygon([(x + 4 * s, y - h * s + i * fh), (x + 130 * s, y - h * s + i * fh + 8 * s), (x + 130 * s, y - h * s + (i + 1) * fh + 8 * s), (x + 4 * s, y - h * s + (i + 1) * fh)], fill=tuple(c) + (255,))


def _shield(d, x, y, s=1.0, col=(40, 90, 190, 255), star=True):
    pts = [(x - 90 * s, y - 100 * s), (x + 90 * s, y - 100 * s), (x + 90 * s, y + 10 * s), (x, y + 110 * s), (x - 90 * s, y + 10 * s)]
    d.polygon(pts, fill=(235, 235, 245, 255))
    d.polygon([(x - 74 * s, y - 86 * s), (x + 74 * s, y - 86 * s), (x + 74 * s, y + 4 * s), (x, y + 92 * s), (x - 74 * s, y + 4 * s)], fill=col)
    if star:
        st = []
        for i in range(10):
            a = -math.pi / 2 + math.pi * i / 5
            rr = 46 * s if i % 2 == 0 else 19 * s
            st.append((x + rr * math.cos(a), y - 10 * s + rr * math.sin(a)))
        d.polygon(st, fill=(255, 215, 80, 255))


def _gift(d, x, y, s=1.0, col=(200, 40, 120, 255)):
    d.rectangle([x - 100 * s, y - 90 * s, x + 100 * s, y + 80 * s], fill=col)
    d.rectangle([x - 112 * s, y - 130 * s, x + 112 * s, y - 80 * s], fill=tuple(min(255, v + 30) for v in col[:3]) + (255,))
    d.rectangle([x - 14 * s, y - 130 * s, x + 14 * s, y + 80 * s], fill=(255, 215, 80, 255))
    d.ellipse([x - 60 * s, y - 190 * s, x - 4 * s, y - 126 * s], outline=(255, 215, 80, 255), width=int(12 * s))
    d.ellipse([x + 4 * s, y - 190 * s, x + 60 * s, y - 126 * s], outline=(255, 215, 80, 255), width=int(12 * s))


def _crown(d, x, y, s=1.0):
    pts = [(x - 90 * s, y), (x - 90 * s, y - 80 * s), (x - 45 * s, y - 35 * s), (x, y - 100 * s), (x + 45 * s, y - 35 * s), (x + 90 * s, y - 80 * s), (x + 90 * s, y)]
    d.polygon(pts, fill=(250, 200, 50, 255))
    d.rectangle([x - 90 * s, y - 14 * s, x + 90 * s, y + 18 * s], fill=(225, 165, 30, 255))
    for dx in (-60, 0, 60):
        d.ellipse([x + (dx - 9) * s, y - 8 * s, x + (dx + 9) * s, y + 10 * s], fill=(220, 40, 60, 255))


def _globe(d, x, y, r, col=(40, 110, 190, 255)):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for k in (-0.5, 0, 0.5):
        d.ellipse([x - r * abs(1 - abs(k)) - 2, y - r, x + r * abs(1 - abs(k)) + 2, y + r], outline=(255, 255, 255, 120), width=3)
        d.line([(x - r, y + r * k), (x + r, y + r * k)], fill=(255, 255, 255, 90), width=3)
    r2 = random.Random(9)
    for _ in range(7):
        a, b = r2.randint(-60, 60), r2.randint(-60, 60)
        d.ellipse([x + a * r / 80 - 22, y + b * r / 80 - 14, x + a * r / 80 + 22, y + b * r / 80 + 14], fill=(70, 160, 80, 230))


def _factory(d, x, y, w=300, h=150, col=(110, 112, 122, 255), chim=2, smoke=True):
    d.rectangle([x, y - h, x + w, y], fill=col)
    for i in range(0, w - 30, 60):
        d.polygon([(x + i, y - h), (x + i + 60, y - h), (x + i + 60, y - h - 36), (x + i, y - h)], fill=tuple(max(0, v - 15) for v in col[:3]) + (255,))
    _wins(d, x + 14, y - h + 30, w - 28, h - 60, max(3, w // 40), 3, seed=4)
    for i in range(chim):
        cx = x + w - 40 - i * 62
        d.rectangle([cx, y - h - 130, cx + 34, y - h], fill=(150, 90, 70, 255))
        d.rectangle([cx - 4, y - h - 140, cx + 38, y - h - 124], fill=(90, 55, 45, 255))
        if smoke:
            _smoke(d, cx + 17, y - h - 150, 5, .8, (90, 90, 98))


def _text(d, xy, s, size, col=(255, 255, 255, 255), anchor="la"):
    d.text(xy, s, font=_font(size), fill=col, anchor=anchor)


def _sign(d, cx, cy, s, w=300, col=(60, 40, 30, 255), tc=(255, 235, 200, 255), size=40):
    d.rounded_rectangle([cx - w / 2, cy - 30, cx + w / 2, cy + 30], radius=10, fill=col, outline=(255, 255, 255, 120), width=3)
    _text(d, (cx, cy), s, size, tc, "mm")


# ───────── ساختمان‌ها ─────────
BLD_EN = {"cafe": "CAFE", "rest": "RESTAURANT", "park": "CITY PARK", "house": "APARTMENTS", "cinema": "CINEMA", "museum": "MUSEUM",
          "mall": "SHOPPING MALL", "hospital": "HOSPITAL", "hotel": "HOTEL", "theater": "THEATRE", "theme": "THEME PARK",
          "uni": "UNIVERSITY", "stadium": "STADIUM", "port": "SEA PORT", "airport": "AIRPORT", "tower": "BUSINESS TOWER"}


def sc_building(key):
    night = key in ("cinema", "stadium", "theater", "hotel", "tower")
    img, d = _canvas((20, 24, 60), (120, 70, 110)) if night else _canvas((255, 170, 90), (255, 224, 170))
    if night:
        _stars(d, 90, 4, 280)
        d.ellipse([1040, 70, 1110, 140], fill=(250, 245, 220, 255))
    else:
        _glow(img, 1030, 150, 150, (255, 230, 150), 200)
        d.ellipse([990, 110, 1070, 190], fill=(255, 245, 190, 255))
        _cloud(d, 180, 130, 1.1)
        _cloud(d, 640, 90, .8)
    _skyline(d, 520, (60, 50, 80, 255) if night else (160, 120, 120, 255), 11, 40, 80, 50, 190)
    d.rectangle([0, 520, SW, SH], fill=(66, 68, 80, 255))
    d.rectangle([0, 520, SW, 540], fill=(120, 122, 132, 255))
    for x in range(30, SW, 150):
        d.rectangle([x, 640, x + 70, 650], fill=(230, 230, 120, 200))
    cx = 560
    if key == "cafe":
        d.rectangle([cx - 190, 300, cx + 190, 520], fill=(236, 205, 160, 255))
        for i in range(10):
            d.polygon([(cx - 200 + i * 40, 300), (cx - 160 + i * 40, 300), (cx - 160 + i * 40, 372), (cx - 180 + i * 40, 392), (cx - 200 + i * 40, 372)],
                      fill=(205, 45, 50, 255) if i % 2 == 0 else (250, 245, 240, 255))
        d.rectangle([cx - 150, 410, cx - 40, 510], fill=(255, 220, 130, 255))
        d.rectangle([cx + 20, 410, cx + 150, 510], fill=(255, 220, 130, 255))
        d.rectangle([cx - 30, 420, cx + 14, 520], fill=(110, 70, 45, 255))
        _sign(d, cx, 262, "CAFE", 220)
        for tx in (cx - 300, cx + 300):
            d.line([(tx, 470), (tx, 540)], fill=(90, 60, 40, 255), width=6)
            d.pieslice([tx - 70, 410, tx + 70, 520], 180, 360, fill=(220, 70, 60, 255))
            d.ellipse([tx - 40, 535, tx + 40, 555], fill=(80, 55, 40, 255))
        cup = (1040, 460)                                   # فنجان قهوه
        _glow(img, cup[0], cup[1] - 40, 150, (255, 190, 90), 110)
        d.rounded_rectangle([cup[0] - 70, cup[1] - 80, cup[0] + 70, cup[1] + 40], radius=26, fill=(250, 245, 240, 255))
        d.arc([cup[0] + 40, cup[1] - 60, cup[0] + 120, cup[1] + 10], 270, 90, fill=(250, 245, 240, 255), width=14)
        d.ellipse([cup[0] - 62, cup[1] - 84, cup[0] + 62, cup[1] - 56], fill=(110, 65, 40, 255))
        d.ellipse([cup[0] - 130, cup[1] + 36, cup[0] + 130, cup[1] + 66], fill=(240, 235, 230, 255))
        for i, dx in enumerate((-26, 0, 26)):
            d.arc([cup[0] + dx - 14, cup[1] - 170 + i * 8, cup[0] + dx + 14, cup[1] - 100 + i * 8], 90, 270, fill=(255, 255, 255, 170), width=6)
    elif key == "rest":
        d.rectangle([cx - 210, 320, cx + 210, 520], fill=(52, 92, 74, 255))
        d.polygon([(cx - 230, 320), (cx + 230, 320), (cx + 190, 270), (cx - 190, 270)], fill=(140, 60, 50, 255))
        for i in range(4):
            d.rectangle([cx - 180 + i * 100, 360, cx - 110 + i * 100, 450], fill=(255, 215, 120, 255))
        d.rectangle([cx - 28, 430, cx + 28, 520], fill=(90, 55, 40, 255))
        _sign(d, cx, 295, "RESTAURANT", 330, (35, 35, 40, 255), (255, 215, 120, 255), 38)
        pl = (1030, 440)
        _glow(img, pl[0], pl[1], 150, (255, 220, 140), 110)
        d.ellipse([pl[0] - 100, pl[1] - 100, pl[0] + 100, pl[1] + 100], fill=(250, 250, 252, 255))
        d.ellipse([pl[0] - 70, pl[1] - 70, pl[0] + 70, pl[1] + 70], outline=(200, 200, 210, 255), width=5)
        d.rectangle([pl[0] - 170, pl[1] - 100, pl[0] - 150, pl[1] + 100], fill=(215, 215, 222, 255))
        d.rectangle([pl[0] + 150, pl[1] - 100, pl[0] + 170, pl[1] + 100], fill=(215, 215, 222, 255))
    elif key == "park":
        d.rectangle([0, 520, SW, SH], fill=(70, 150, 80, 255))
        d.ellipse([300, 560, 780, 690], fill=(70, 150, 210, 255))
        d.ellipse([340, 575, 700, 640], fill=(120, 190, 235, 200))
        for tx, ty, s in ((120, 540, 1.3), (260, 545, 1.0), (880, 540, 1.4), (1030, 548, 1.1), (1170, 540, 1.3), (540, 520, .8)):
            _tree(d, tx, ty, s, (40, 120 + int(s * 20), 55, 255))
        d.rectangle([880, 600, 1010, 612], fill=(120, 80, 50, 255))
        d.rectangle([880, 580, 1010, 590], fill=(120, 80, 50, 255))
        d.rectangle([890, 612, 898, 640], fill=(70, 50, 40, 255))
        d.rectangle([992, 612, 1000, 640], fill=(70, 50, 40, 255))
        d.rectangle([600, 330, 612, 540], fill=(60, 60, 66, 255))
        _glow(img, 606, 330, 60, (255, 240, 170), 160)
        _sign(d, 640, 250, "CITY PARK", 300, (30, 90, 50, 255), (255, 255, 255, 255))
    elif key in ("house", "hotel", "tower", "hospital", "mall"):
        w = {"house": 150, "hotel": 150, "tower": 160, "hospital": 330, "mall": 460}[key]
        h = {"house": 280, "hotel": 340, "tower": 380, "hospital": 250, "mall": 190}[key]
        col = {"house": (170, 120, 100, 255), "hotel": (110, 90, 150, 255), "tower": (70, 130, 170, 255),
               "hospital": (240, 242, 248, 255), "mall": (150, 170, 200, 255)}[key]
        xs = [cx - w // 2] if key in ("hospital", "mall") else [cx - w - 20, cx + 20]
        for x0 in xs:
            d.rectangle([x0, 520 - h, x0 + w, 520], fill=col)
            _wins(d, x0 + 12, 520 - h + 14, w - 24, h - 40, max(3, w // 36), max(3, h // 46),
                  on=(255, 230, 140, 255) if key != "hospital" else (160, 205, 245, 255), off=(70, 85, 110, 255) if key != "hospital" else (200, 210, 225, 255))
        if key == "hospital":
            d.rectangle([cx - 20, 520 - h - 60, cx + 20, 520 - h], fill=(220, 40, 50, 255))
            d.rectangle([cx - 50, 520 - h - 40, cx + 50, 520 - h - 20], fill=(220, 40, 50, 255))
            d.rounded_rectangle([880, 470, 1060, 540], radius=14, fill=(250, 250, 252, 255))
            d.rectangle([940, 482, 960, 520], fill=(220, 40, 50, 255))
            d.rectangle([925, 492, 975, 510], fill=(220, 40, 50, 255))
        if key == "hotel":
            for i in range(5):
                a = -math.pi / 2 + math.pi * 2 * i / 5
                st = [(cx + 100 + (40 if j % 2 == 0 else 17) * math.cos(a + j * math.pi / 5 - math.pi / 5), 140 + (40 if j % 2 == 0 else 17) * math.sin(a + j * math.pi / 5 - math.pi / 5)) for j in range(10)]
            for k2, sx in enumerate(range(cx - 90, cx + 91, 45)):
                pts = []
                for j in range(10):
                    aa = -math.pi / 2 + math.pi * j / 5
                    rr = 19 if j % 2 == 0 else 8
                    pts.append((sx + rr * math.cos(aa), 520 - h - 40 + rr * math.sin(aa)))
                d.polygon(pts, fill=(255, 215, 80, 255))
        if key == "mall":
            d.rectangle([cx - 60, 450, cx + 60, 520], fill=(40, 60, 90, 255))
            for bx2, bc in ((960, (220, 60, 90)), (1040, (60, 150, 220)), (1120, (240, 190, 50))):
                d.polygon([(bx2 - 40, 470), (bx2 + 40, 470), (bx2 + 48, 540), (bx2 - 48, 540)], fill=bc + (255,))
                d.arc([bx2 - 24, 430, bx2 + 24, 490], 180, 360, fill=(250, 250, 250, 255), width=6)
        _sign(d, cx, 520 - h - (100 if key in ("hospital",) else 40), BLD_EN[key], 340 if key in ("hospital", "mall", "tower") else 300,
              (25, 30, 45, 255), (255, 235, 180, 255), 36)
    elif key == "cinema":
        d.rectangle([cx - 230, 330, cx + 230, 520], fill=(70, 40, 80, 255))
        d.rounded_rectangle([cx - 260, 290, cx + 260, 370], radius=12, fill=(30, 20, 40, 255), outline=(255, 215, 90, 255), width=5)
        for i in range(14):
            d.ellipse([cx - 245 + i * 38, 296, cx - 231 + i * 38, 310], fill=(255, 230, 120, 255))
            d.ellipse([cx - 245 + i * 38, 350, cx - 231 + i * 38, 364], fill=(255, 230, 120, 255))
        _text(d, (cx, 330), "CINEMA", 52, (255, 225, 110, 255), "mm")
        for i in range(3):
            d.rectangle([cx - 160 + i * 120, 410, cx - 90 + i * 120, 500], fill=(240, 90, 90, 255) if i % 2 == 0 else (90, 140, 240, 255))
        for bx2 in (cx - 330, cx + 330):
            lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
            ImageDraw.Draw(lay).polygon([(bx2, 520), (bx2 - 40, 0), (bx2 + 40, 0)], fill=(255, 255, 220, 60))
            img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
        fr = (1040, 420)
        d.ellipse([fr[0] - 90, fr[1] - 90, fr[0] + 90, fr[1] + 90], fill=(40, 40, 50, 255), outline=(220, 220, 230, 255), width=8)
        for k2 in range(6):
            a = math.pi * 2 * k2 / 6
            d.ellipse([fr[0] + 50 * math.cos(a) - 16, fr[1] + 50 * math.sin(a) - 16, fr[0] + 50 * math.cos(a) + 16, fr[1] + 50 * math.sin(a) + 16], fill=(220, 220, 230, 255))
    elif key in ("museum", "uni", "theater"):
        col = {"museum": (232, 224, 205, 255), "uni": (170, 90, 80, 255), "theater": (190, 170, 130, 255)}[key]
        d.polygon([(cx - 270, 330), (cx + 270, 330), (cx, 220)], fill=col)
        d.rectangle([cx - 270, 330, cx + 270, 352], fill=tuple(max(0, v - 25) for v in col[:3]) + (255,))
        for i in range(7):
            d.rectangle([cx - 240 + i * 80, 352, cx - 214 + i * 80, 500], fill=tuple(min(255, v + 10) for v in col[:3]) + (255,))
        for k2 in range(3):
            d.rectangle([cx - 290 + k2 * 12, 500 + k2 * 7, cx + 290 - k2 * 12, 507 + k2 * 7], fill=(200, 200, 205, 255))
        if key == "uni":
            d.pieslice([cx - 80, 150, cx + 80, 290], 180, 360, fill=(220, 190, 90, 255))
            d.rectangle([cx - 80, 220, cx + 80, 226], fill=(220, 190, 90, 255))
            d.polygon([(1040, 380), (1130, 410), (1040, 440), (950, 410)], fill=(30, 30, 40, 255))
            d.rectangle([1000, 430, 1080, 470], fill=(40, 40, 52, 255))
            d.line([(1130, 410), (1130, 470)], fill=(240, 200, 60, 255), width=5)
        if key == "theater":
            d.rectangle([cx - 60, 380, cx + 60, 500], fill=(150, 30, 40, 255))
            for k2 in range(5):
                d.polygon([(cx - 60 + k2 * 24, 380), (cx - 36 + k2 * 24, 380), (cx - 48 + k2 * 24, 500)], fill=(185, 40, 55, 255))
            d.ellipse([950, 400, 1030, 480], fill=(250, 240, 220, 255))
            d.ellipse([1050, 420, 1130, 500], fill=(240, 200, 90, 255))
            for mx, my in ((990, 440), (1090, 460)):
                d.ellipse([mx - 20, my - 12, mx - 8, my], fill=(40, 30, 30, 255))
                d.ellipse([mx + 8, my - 12, mx + 20, my], fill=(40, 30, 30, 255))
                d.arc([mx - 22, my + 4, mx + 22, my + 30], 0 if mx < 1000 else 180, 180 if mx < 1000 else 360, fill=(40, 30, 30, 255), width=5)
        _sign(d, cx, 188 if key != "uni" else 130, BLD_EN[key], 300, (35, 30, 30, 255), (250, 235, 190, 255), 38)
    elif key == "theme":
        wx, wy = 560, 380
        d.ellipse([wx - 190, wy - 190, wx + 190, wy + 190], outline=(250, 250, 255, 255), width=10)
        d.ellipse([wx - 110, wy - 110, wx + 110, wy + 110], outline=(250, 250, 255, 160), width=5)
        for k2 in range(12):
            a = math.pi * 2 * k2 / 12
            d.line([(wx, wy), (wx + 190 * math.cos(a), wy + 190 * math.sin(a))], fill=(240, 240, 250, 255), width=5)
            gx, gy = wx + 190 * math.cos(a), wy + 190 * math.sin(a)
            d.rounded_rectangle([gx - 22, gy - 10, gx + 22, gy + 30], radius=8, fill=[(235, 70, 80), (70, 160, 235), (250, 200, 60)][k2 % 3] + (255,))
        d.polygon([(wx, wy), (wx - 90, 540), (wx + 90, 540)], outline=(240, 240, 250, 255), width=8)
        for k2 in range(14):
            d.ellipse([wx + 220 + k2 * 6, 330 + abs(k2 - 7) * 20 - 40, wx + 232 + k2 * 6, 342 + abs(k2 - 7) * 20 - 40], fill=(255, 230, 100, 255))
        d.arc([wx + 200, 330, wx + 460, 560], 180, 360, fill=(240, 90, 90, 255), width=10)
        d.arc([wx + 420, 400, wx + 660, 560], 180, 360, fill=(240, 90, 90, 255), width=10)
        _sign(d, 640, 150, "THEME PARK", 360, (120, 30, 120, 255), (255, 235, 130, 255), 40)
    elif key == "stadium":
        d.ellipse([cx - 330, 360, cx + 330, 560], fill=(150, 150, 165, 255))
        d.ellipse([cx - 270, 380, cx + 270, 540], fill=(60, 150, 70, 255))
        d.ellipse([cx - 160, 410, cx + 160, 510], outline=(255, 255, 255, 180), width=4)
        d.line([(cx, 392), (cx, 528)], fill=(255, 255, 255, 180), width=4)
        for tx in (cx - 340, cx + 340):
            d.rectangle([tx - 6, 220, tx + 6, 520], fill=(90, 90, 100, 255))
            d.rectangle([tx - 40, 200, tx + 40, 240], fill=(235, 235, 245, 255))
            _glow(img, tx, 220, 120, (255, 255, 220), 180)
        _sign(d, cx, 300, "STADIUM", 300, (20, 40, 90, 255), (255, 255, 255, 255), 42)
    elif key == "port":
        d.rectangle([0, 520, SW, SH], fill=(40, 100, 160, 255))
        for k2 in range(8):
            d.arc([k2 * 170 - 40, 560, k2 * 170 + 130, 600], 0, 180, fill=(120, 175, 220, 255), width=4)
        d.rectangle([0, 470, 640, 520], fill=(120, 122, 130, 255))
        for i, cc in enumerate(((200, 70, 60), (60, 120, 190), (240, 180, 50), (70, 150, 90), (200, 70, 60), (60, 120, 190))):
            d.rectangle([40 + (i % 3) * 120, 470 - (i // 3 + 1) * 56, 150 + (i % 3) * 120, 470 - (i // 3) * 56], fill=cc + (255,))
        d.rectangle([700, 180, 724, 520], fill=(230, 160, 50, 255))
        d.rectangle([700, 180, 1000, 204], fill=(230, 160, 50, 255))
        d.line([(960, 204), (960, 400)], fill=(60, 60, 66, 255), width=4)
        d.rectangle([940, 400, 980, 430], fill=(200, 70, 60, 255))
        _ship(d, 900, 540, 1.3, (160, 60, 60, 255))
        _sign(d, 640, 120, "SEA PORT", 280, (20, 50, 90, 255), (255, 255, 255, 255), 40)
    elif key == "airport":
        d.rectangle([0, 470, SW, SH], fill=(70, 72, 82, 255))
        for x in range(0, SW, 120):
            d.rectangle([x, 560, x + 70, 570], fill=(240, 240, 240, 230))
        d.rectangle([180, 300, 260, 470], fill=(210, 215, 225, 255))
        d.rectangle([160, 260, 280, 310], fill=(100, 170, 220, 255))
        d.rectangle([250, 380, 800, 470], fill=(190, 200, 215, 255))
        _wins(d, 262, 392, 520, 60, 14, 2, on=(130, 190, 240, 255), off=(100, 130, 170, 255))
        _jet(d, 930, 400, 1.4, (240, 242, 250, 255), 1, -0.12)
        _sign(d, 640, 170, "AIRPORT", 280, (20, 50, 100, 255), (255, 255, 255, 255), 42)
    return img, d


def sc_factory(key):
    img, d = _canvas((70, 85, 120), (240, 160, 110)) if key not in ("tech", "space") else _canvas((15, 18, 45), (60, 40, 100))
    d.rectangle([0, 560, SW, SH], fill=(50, 52, 60, 255))
    if key in ("oil", "oilcity"):
        _glow(img, 900, 520, 240, (255, 150, 60), 150)
        d.ellipse([820, 440, 980, 600], fill=(255, 215, 120, 255))
        d.rectangle([0, 540, SW, SH], fill=(110, 80, 50, 255))
        for ox, s in ((330, 1.4), (640, 1.0), (1000, 1.2)):
            d.polygon([(ox - 50 * s, 540), (ox + 50 * s, 540), (ox + 12 * s, 240 * s + 300 - 240), (ox - 12 * s, 300)], fill=(40, 40, 46, 255))
            for k2 in range(5):
                yy = 540 - k2 * 50 * s
                d.line([(ox - 45 * s + k2 * 7, yy), (ox + 45 * s - k2 * 7, yy - 40 * s)], fill=(70, 70, 78, 255), width=4)
            d.rectangle([ox - 14 * s, 280, ox + 14 * s, 330], fill=(200, 60, 50, 255))
        d.polygon([(130, 540), (260, 540), (230, 470), (160, 470)], fill=(30, 30, 36, 255))
        d.polygon([(110, 460), (280, 430), (284, 444), (110, 476)], fill=(200, 60, 50, 255))
        if key == "oilcity":
            _skyline(d, 540, (35, 40, 58, 255), 21, 40, 80, 60, 200)
    elif key in ("ironm", "gold", "uran"):
        d.polygon([(0, 560), (300, 260), (520, 420), (780, 200), (1100, 430), (1280, 330), (1280, 560)], fill=(88, 84, 92, 255))
        d.polygon([(780, 200), (840, 250), (800, 300), (740, 250)], fill=(230, 232, 240, 255))
        d.polygon([(430, 560), (440, 420), (560, 420), (570, 560)], fill=(30, 28, 34, 255))
        d.rectangle([420, 405, 580, 425], fill=(120, 80, 50, 255))
        col = {"ironm": (120, 130, 150), "gold": (250, 200, 50), "uran": (110, 240, 90)}[key]
        _glow(img, 500, 500, 140, col, 150 if key != "ironm" else 40)
        for k2 in range(6):
            d.ellipse([700 + k2 * 55, 520 - (k2 % 2) * 30, 750 + k2 * 55, 570 - (k2 % 2) * 30], fill=col + (255,))
        d.rectangle([640, 560, 900, 590], fill=(40, 40, 46, 255))
        d.polygon([(660, 520), (880, 520), (860, 566), (680, 566)], fill=(120, 80, 50, 255))
        if key == "uran":
            d.ellipse([950, 400, 1110, 560], fill=(250, 220, 40, 255), outline=(30, 30, 30, 255), width=8)
            for a in (-90, 30, 150):
                d.pieslice([960, 410, 1100, 550], a - 30, a + 30, fill=(30, 30, 30, 255))
            d.ellipse([1015, 465, 1045, 495], fill=(30, 30, 30, 255))
        if key == "gold":
            for k2, (gx, gy) in enumerate(((980, 560), (1060, 560), (1020, 520))):
                d.polygon([(gx - 50, gy), (gx + 50, gy), (gx + 36, gy - 36), (gx - 36, gy - 36)], fill=(250, 205, 60, 255), outline=(190, 140, 20, 255))
    elif key == "power":
        for cx2, s in ((330, 1.3), (640, 1.0)):
            d.polygon([(cx2 - 90 * s, 560), (cx2 + 90 * s, 560), (cx2 + 55 * s, 330), (cx2 - 55 * s, 330)], fill=(205, 205, 212, 255))
            d.ellipse([cx2 - 55 * s, 316, cx2 + 55 * s, 346], fill=(170, 170, 180, 255))
            _smoke(d, cx2, 310, 5, s, (235, 235, 242))
        for px in (880, 1010, 1140):
            d.line([(px, 560), (px, 300)], fill=(60, 60, 68, 255), width=7)
            d.line([(px - 70, 340), (px + 70, 340)], fill=(60, 60, 68, 255), width=6)
            d.line([(px - 55, 400), (px + 55, 400)], fill=(60, 60, 68, 255), width=5)
        for k2 in range(3):
            d.line([(880, 340 + k2 * 4), (1140, 340 + k2 * 4)], fill=(60, 60, 68, 255), width=2)
        d.polygon([(1000, 380), (1020, 380), (1008, 430), (1026, 430), (996, 500), (1006, 444), (990, 444)], fill=(255, 225, 60, 255))
    elif key == "tech":
        _stars(d, 60, 2, 250)
        d.rounded_rectangle([320, 160, 960, 500], radius=24, fill=(20, 24, 40, 255), outline=(120, 140, 220, 255), width=8)
        d.rectangle([590, 500, 690, 560], fill=(70, 74, 90, 255))
        d.rounded_rectangle([500, 556, 780, 580], radius=10, fill=(70, 74, 90, 255))
        rr = random.Random(5)
        for _ in range(26):
            x1, y1 = rr.randint(350, 900), rr.randint(190, 470)
            x2 = x1 + rr.choice((-120, 0, 120))
            d.line([(x1, y1), (x2, y1), (x2, y1 + rr.choice((-70, 70)))], fill=(90, 230, 220, 200), width=4)
            d.ellipse([x1 - 6, y1 - 6, x1 + 6, y1 + 6], fill=(120, 255, 240, 255))
        d.rounded_rectangle([540, 270, 740, 390], radius=14, fill=(60, 70, 150, 255), outline=(150, 170, 255, 255), width=5)
        _text(d, (640, 330), "AI", 70, (255, 255, 255, 255), "mm")
        _glow(img, 640, 330, 220, (90, 120, 255), 120)
    elif key == "space":
        _stars(d, 120, 6, 560)
        _glow(img, 640, 610, 260, (255, 150, 50), 200)
        d.polygon([(560, 610), (720, 610), (700, 720), (580, 720)], fill=(255, 190, 60, 200))
        d.ellipse([600, 560, 680, 720], fill=(255, 240, 180, 230))
        d.rounded_rectangle([590, 200, 690, 560], radius=40, fill=(238, 240, 246, 255))
        d.polygon([(590, 200), (640, 90), (690, 200)], fill=(220, 50, 55, 255))
        d.ellipse([618, 280, 662, 324], fill=(70, 140, 220, 255), outline=(60, 70, 90, 255), width=6)
        d.polygon([(590, 470), (530, 570), (590, 540)], fill=(220, 50, 55, 255))
        d.polygon([(690, 470), (750, 570), (690, 540)], fill=(220, 50, 55, 255))
        d.rectangle([800, 330, 812, 600], fill=(80, 80, 90, 255))
        d.rectangle([440, 330, 452, 600], fill=(80, 80, 90, 255))
    elif key == "arms":
        d.rectangle([0, 540, SW, SH], fill=(46, 50, 46, 255))
        _tank(d, 360, 560, 1.6, (82, 98, 66, 255), 1)
        _jet(d, 860, 360, 1.7, (190, 196, 206, 255), 1, -0.05)
        for k2 in range(3):
            _missile(d, 1040 + k2 * 70, 540, -math.pi / 2, 0.7, trail=0)
    elif key == "agri":
        img2, d = _canvas((120, 190, 240), (250, 235, 170))
        img.paste(img2)
        d = ImageDraw.Draw(img, "RGBA")
        _glow(img, 1000, 160, 150, (255, 240, 160), 220)
        d.ellipse([960, 120, 1040, 200], fill=(255, 245, 190, 255))
        _hills(d, 430, (110, 170, 90, 255), 8)
        d.rectangle([0, 470, SW, SH], fill=(210, 170, 70, 255))
        for k2 in range(14):
            d.line([(k2 * 100 - 200, SH), (300 + k2 * 55, 470)], fill=(180, 140, 50, 255), width=6)
        d.rectangle([700, 400, 860, 480], fill=(60, 140, 60, 255))
        d.rectangle([830, 360, 880, 420], fill=(60, 140, 60, 255))
        d.ellipse([690, 450, 790, 550], fill=(35, 35, 38, 255))
        d.ellipse([820, 480, 880, 540], fill=(35, 35, 38, 255))
        d.ellipse([715, 475, 765, 525], fill=(220, 190, 60, 255))
    else:                                              # صنایع عمومی (کارخانه)
        _hills(d, 520, (60, 62, 80, 255), 4)
        _factory(d, 200, 560, 420, 170, (118, 120, 132, 255), 3)
        _factory(d, 700, 560, 330, 130, (100, 104, 118, 255), 2)
        if key == "car":
            d.rounded_rectangle([880, 470, 1180, 550], radius=30, fill=(210, 40, 50, 255))
            d.polygon([(930, 470), (1000, 420), (1100, 420), (1150, 470)], fill=(190, 36, 46, 255))
            d.polygon([(950, 468), (1005, 430), (1060, 430), (1060, 468)], fill=(150, 200, 235, 255))
            d.polygon([(1070, 468), (1070, 430), (1100, 430), (1135, 468)], fill=(150, 200, 235, 255))
            for wx in (950, 1110):
                d.ellipse([wx - 34, 520, wx + 34, 588], fill=(30, 30, 34, 255))
                d.ellipse([wx - 16, 538, wx + 16, 570], fill=(190, 190, 200, 255))
        if key in ("steel", "alu", "refinery"):
            _glow(img, 400, 470, 180, (255, 120, 40) if key != "alu" else (200, 220, 255), 150)
        if key == "refinery":
            d.line([(1100, 560), (1100, 300)], fill=(60, 60, 66, 255), width=8)
            d.polygon([(1100, 300), (1130, 240), (1070, 240)], fill=(255, 150, 40, 255))
        if key == "holding":
            _skyline(d, 560, (40, 46, 70, 255), 17, 60, 100, 160, 330)
    return img, d


def sc_war(sub):
    if sub in ("ground", "conquest", "war"):
        img, d = _canvas((70, 28, 40), (255, 140, 60)) if sub != "conquest" else _canvas((40, 25, 45), (230, 100, 50))
        _glow(img, 640, 480, 300, (255, 130, 40), 130)
        d.ellipse([560, 330, 720, 490], fill=(255, 210, 120, 255))
        _hills(d, 520, (50, 30, 40, 255), 6, 60)
        d.rectangle([0, 520, SW, SH], fill=(40, 28, 30, 255))
        if sub == "conquest":
            _skyline(d, 530, (30, 22, 32, 255), 31, 50, 100, 100, 320, (255, 150, 60, 150))
            for sx in (200, 480, 900, 1100):
                _smoke(d, sx, 440, 6, 1.0, (30, 30, 34))
            _boom(img, d, 330, 430, 70)
            _boom(img, d, 980, 400, 80)
            _flag(d, 640, 500, 1.7, ((200, 40, 40), (250, 250, 250), (40, 70, 170)), 200)
            for k2 in range(5):
                x0 = 420 + k2 * 100
                d.rectangle([x0, 464, x0 + 14, 504], fill=(15, 15, 20, 255))
                d.ellipse([x0 - 2, 450, x0 + 16, 468], fill=(15, 15, 20, 255))
        else:
            _tank(d, 280, 545, 1.5, (84, 100, 64, 255), 1)
            _tank(d, 1000, 545, 1.5, (110, 96, 70, 255), -1)
            _boom(img, d, 640, 470, 100)
            for sx in (520, 760):
                _smoke(d, sx, 470, 6, 1.1, (30, 30, 34))
            _boom(img, d, 470, 480, 34)
            _boom(img, d, 800, 486, 38)
        return img, d
    if sub == "air":
        img, d = _canvas((30, 60, 130), (250, 170, 110))
        _glow(img, 1000, 280, 200, (255, 230, 150), 160)
        for cx2, cy in ((150, 120), (500, 200), (820, 90), (1100, 190)):
            _cloud(d, cx2, cy, 1.3)
        for x0, y0, f, t in ((250, 250, 1, 0.08), (520, 400, 1, -0.06), (900, 220, -1, 0.1), (760, 470, -1, -0.07)):
            for k2 in range(6):
                d.line([(x0 - f * (110 + k2 * 70), y0 + k2 * 4), (x0 - f * (110 + (k2 + 1) * 70), y0 + (k2 + 1) * 4)], fill=(255, 255, 255, max(30, 190 - k2 * 30)), width=14 - k2)
            _jet(d, x0, y0, 1.2, (200, 206, 216, 255), f, t)
        _boom(img, d, 640, 330, 70)
        d.rectangle([0, 600, SW, SH], fill=(35, 60, 70, 255))
        return img, d
    if sub == "naval":
        img, d = _canvas((60, 90, 150), (240, 170, 120))
        _glow(img, 640, 380, 260, (255, 210, 130), 150)
        d.rectangle([0, 420, SW, SH], fill=(24, 70, 120, 255))
        for k2 in range(12):
            d.arc([k2 * 120 - 60, 440 + (k2 % 3) * 40, k2 * 120 + 100, 480 + (k2 % 3) * 40], 0, 180, fill=(110, 170, 220, 220), width=4)
        _ship(d, 330, 470, 1.4, (118, 128, 144, 255), 1)
        _ship(d, 960, 500, 1.3, (140, 120, 112, 255), -1)
        _boom(img, d, 760, 450, 60)
        _smoke(d, 960, 400, 5, 1.0, (50, 50, 56))
        for sx in (560, 640, 700):
            d.polygon([(sx - 20, 480), (sx, 400 - (sx % 7) * 6), (sx + 20, 480)], fill=(220, 235, 250, 200))
        return img, d
    img, d = _canvas((8, 10, 30), (40, 20, 60))        # موشکی
    _stars(d, 100, 3, 420)
    _skyline(d, 600, (20, 22, 40, 255), 12, 50, 100, 90, 250, (255, 200, 90, 150))
    d.rectangle([0, 600, SW, SH], fill=(14, 14, 24, 255))
    for k2, (mx, my) in enumerate(((250, 160), (520, 120), (800, 150), (1060, 110))):
        ang = math.atan2(520 - my, 640 + (k2 - 1.5) * 90 - mx)
        _missile(d, mx, my, ang, 1.0, trail=380)
    for bx2 in (520, 640, 760):
        _boom(img, d, bx2, 590, 55)
    return img, d


def sc_misc(cat, sub=None):
    if cat == "nuke":
        img, d = _canvas((250, 160, 60), (90, 30, 30))
        _glow(img, 640, 380, 420, (255, 230, 120), 190)
        _skyline(d, 600, (30, 20, 25, 255), 8, 50, 100, 80, 220, (255, 160, 60, 120))
        d.rectangle([0, 600, SW, SH], fill=(25, 15, 18, 255))
        _mushroom(img, d, 640, 600, 1.35)
        return img, d
    if cat == "peace":
        img, d = _canvas((255, 190, 120), (170, 220, 250))
        _glow(img, 640, 480, 320, (255, 240, 170), 190)
        d.ellipse([560, 420, 720, 580], fill=(255, 245, 190, 255))
        _hills(d, 600, (90, 160, 90, 255), 5, 50)
        _hills(d, 650, (60, 130, 70, 255), 9, 40)
        _dove(d, 560, 300, 2.0)
        return img, d
    if cat in ("alliance", "diplomacy", "union"):
        img, d = _canvas((20, 40, 100), (60, 110, 190))
        _stars(d, 60, 3, 300)
        _glow(img, 640, 330, 260, (120, 170, 255), 130)
        if cat == "union":
            _shield(d, 640, 340, 2.2, (40, 90, 190, 255))
            _flag(d, 260, 600, 1.3, ((200, 40, 40), (250, 250, 250), (40, 70, 170)))
            _flag(d, 1010, 600, 1.3, ((30, 130, 60), (250, 250, 250), (200, 40, 40)))
        else:
            _globe(d, 640, 340, 190)
            _flag(d, 330, 600, 1.5, ((200, 40, 40), (250, 250, 250), (40, 70, 170)))
            _flag(d, 860, 600, 1.5, ((30, 130, 60), (250, 250, 250), (230, 190, 40)))
        d.rectangle([0, 600, SW, SH], fill=(20, 30, 70, 255))
        return img, d
    if cat == "trade":
        img, d = _canvas((255, 190, 110), (250, 225, 170))
        _glow(img, 1000, 180, 160, (255, 235, 160), 200)
        d.rectangle([0, 470, SW, SH], fill=(30, 100, 160, 255))
        for k2 in range(10):
            d.arc([k2 * 140 - 50, 500 + (k2 % 2) * 40, k2 * 140 + 110, 540 + (k2 % 2) * 40], 0, 180, fill=(120, 180, 225, 255), width=4)
        d.polygon([(220, 470), (1060, 470), (990, 560), (290, 560)], fill=(50, 60, 90, 255))
        for i in range(8):
            for j in range(3):
                d.rectangle([300 + i * 88, 470 - (j + 1) * 46, 380 + i * 88, 470 - j * 46], fill=[(210, 70, 60), (70, 130, 200), (240, 185, 55), (70, 160, 100)][(i + j) % 4] + (255,))
        d.rectangle([900, 330, 1000, 470], fill=(235, 235, 240, 255))
        _coin(d, 1140, 250, 55, "$")
        _coin(d, 130, 300, 45, "$")
        return img, d
    if cat in ("crypto", "bank"):
        img, d = _canvas((14, 16, 30), (30, 24, 60)) if cat == "crypto" else _canvas((30, 90, 70), (210, 230, 200))
        if cat == "crypto":
            _stars(d, 50, 8, 300)
            rr = random.Random(11)
            y0 = 520
            for k2 in range(18):
                up = rr.random() < .6
                h = rr.randint(40, 140)
                x0 = 80 + k2 * 62
                col = (60, 200, 110, 255) if up else (230, 70, 80, 255)
                d.line([(x0 + 18, y0 - h - 40), (x0 + 18, y0 + 20)], fill=col, width=4)
                d.rectangle([x0, y0 - h, x0 + 36, y0], fill=col)
                y0 += -22 if up else 16
            _glow(img, 1000, 250, 230, (255, 170, 30), 180)
            _coin(d, 1000, 250, 150, "B", (250, 160, 20, 255))
        else:
            _glow(img, 640, 300, 280, (255, 255, 220), 150)
            d.polygon([(250, 300), (1030, 300), (640, 160)], fill=(240, 236, 220, 255))
            d.rectangle([250, 300, 1030, 322], fill=(205, 200, 185, 255))
            for i in range(8):
                d.rectangle([290 + i * 96, 322, 322 + i * 96, 520], fill=(250, 246, 232, 255))
            d.rectangle([220, 520, 1060, 560], fill=(200, 196, 182, 255))
            _text(d, (640, 250), "BANK", 60, (150, 120, 40, 255), "mm")
            for k2 in range(5):
                _coin(d, 150 + (k2 % 2) * 30, 600 - k2 * 24, 52, "$")
            for k2 in range(4):
                _coin(d, 1130 - (k2 % 2) * 30, 610 - k2 * 24, 52, "$")
        return img, d
    if cat == "statement":
        img, d = _canvas((25, 40, 85), (60, 80, 150))
        _glow(img, 640, 300, 300, (170, 190, 255), 110)
        for k2 in range(9):
            d.polygon([(100 + k2 * 130, 0), (150 + k2 * 130, 0), (130 + k2 * 130, 520), (80 + k2 * 130, 520)], fill=(30, 50, 110, 140))
        _flag(d, 250, 540, 1.6, ((200, 40, 40), (250, 250, 250), (40, 70, 170)))
        _flag(d, 900, 540, 1.6, ((30, 130, 60), (250, 250, 250), (200, 40, 40)))
        d.rectangle([0, 540, SW, SH], fill=(35, 28, 30, 255))
        d.polygon([(470, 540), (810, 540), (780, 330), (500, 330)], fill=(110, 70, 45, 255))
        d.rectangle([490, 320, 790, 340], fill=(140, 92, 60, 255))
        d.line([(640, 320), (640, 230)], fill=(60, 60, 66, 255), width=8)
        d.ellipse([616, 190, 664, 238], fill=(40, 40, 46, 255))
        d.ellipse([600, 410, 680, 490], fill=(235, 190, 60, 255))
        return img, d
    if cat == "pack":
        img, d = _canvas((60, 20, 90), (170, 50, 110))
        _glow(img, 640, 380, 300, (255, 150, 220), 140)
        rr = random.Random(4)
        for _ in range(60):
            x, y = rr.randint(0, SW), rr.randint(0, SH)
            s = rr.randint(3, 9)
            d.polygon([(x, y - s * 2), (x + s, y), (x, y + s * 2), (x - s, y)], fill=(255, 235, 140, rr.randint(120, 255)))
        _gift(d, 640, 420, 2.0, (210, 40, 120, 255))
        d.rectangle([0, 640, SW, SH], fill=(40, 12, 60, 255))
        return img, d
    if cat == "license":
        img, d = _canvas((30, 44, 70), (80, 100, 140))
        d.rounded_rectangle([380, 90, 900, 640], radius=20, fill=(248, 246, 236, 255))
        for k2 in range(8):
            d.line([(430, 190 + k2 * 44), (850 - (k2 % 3) * 70, 190 + k2 * 44)], fill=(170, 170, 180, 255), width=8)
        _text(d, (640, 140), "LICENSE", 46, (40, 60, 120, 255), "mm")
        d.ellipse([700, 450, 860, 610], fill=(200, 40, 50, 230))
        d.ellipse([715, 465, 845, 595], outline=(255, 220, 220, 255), width=5)
        _text(d, (780, 530), "OK", 54, (255, 235, 235, 255), "mm")
        return img, d
    if cat == "sanction":
        img, d = _canvas((70, 20, 24), (30, 20, 40))
        _globe(d, 640, 360, 220, (50, 90, 140, 255))
        d.ellipse([400, 120, 880, 600], outline=(230, 40, 50, 255), width=30)
        d.line([(440, 160), (840, 560)], fill=(230, 40, 50, 255), width=30)
        return img, d
    if cat == "cyber":
        img, d = _canvas((2, 14, 8), (4, 36, 20))
        rr = random.Random(2)
        for x in range(0, SW, 26):
            for y in range(rr.randint(0, 300), SH, 30):
                d.text((x, y), rr.choice("01"), font=_font(24), fill=(40, 255, 120, rr.randint(40, 200)))
        _glow(img, 640, 380, 280, (40, 255, 120), 110)
        d.polygon([(480, 640), (480, 400), (560, 300), (720, 300), (800, 400), (800, 640)], fill=(10, 16, 14, 255), outline=(40, 255, 120, 255))
        d.ellipse([570, 340, 710, 470], fill=(2, 6, 4, 255))
        d.ellipse([600, 395, 630, 415], fill=(40, 255, 120, 255))
        d.ellipse([650, 395, 680, 415], fill=(40, 255, 120, 255))
        d.rounded_rectangle([520, 560, 760, 640], radius=10, fill=(30, 40, 38, 255), outline=(40, 255, 120, 255), width=3)
        return img, d
    if cat == "black":
        img, d = _canvas((6, 6, 14), (30, 24, 40))
        d.ellipse([980, 90, 1070, 180], fill=(240, 236, 210, 255))
        _skyline(d, 560, (14, 12, 22, 255), 3, 60, 110, 120, 340, (240, 200, 90, 70))
        d.rectangle([0, 560, SW, SH], fill=(12, 10, 16, 255))
        for k2, (cx2, cy2) in enumerate(((300, 600), (420, 610), (360, 560), (980, 610))):
            d.rectangle([cx2 - 50, cy2 - 50, cx2 + 50, cy2 + 10], fill=(90, 62, 40, 255), outline=(40, 28, 20, 255), width=4)
        d.polygon([(660, 640), (660, 480), (700, 420), (760, 420), (800, 480), (800, 640)], fill=(4, 4, 8, 255))
        d.ellipse([690, 360, 770, 440], fill=(4, 4, 8, 255))
        _glow(img, 1030, 120, 120, (240, 230, 190), 80)
        return img, d
    if cat == "event":
        img, d = _canvas((30, 24, 56), (90, 60, 110))
        for cx2, cy in ((200, 120), (520, 80), (860, 130), (1100, 90)):
            _cloud(d, cx2, cy, 1.6, (60, 58, 80, 255))
        d.polygon([(600, 150), (720, 150), (660, 290), (740, 290), (560, 560), (620, 340), (550, 340)], fill=(255, 235, 90, 255))
        _glow(img, 640, 350, 200, (255, 235, 120), 130)
        d.rectangle([0, 600, SW, SH], fill=(24, 20, 36, 255))
        return img, d
    if cat == "newleader":
        img, d = _canvas((70, 50, 20), (230, 190, 90))
        for k2 in range(7):
            lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
            ImageDraw.Draw(lay).polygon([(640, 700), (640 - 520 + k2 * 170, 0), (640 - 520 + k2 * 170 + 60, 0)], fill=(255, 245, 190, 55))
            img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5)))
        _glow(img, 640, 330, 240, (255, 225, 120), 190)
        _crown(d, 640, 380, 2.3)
        d.rectangle([0, 620, SW, SH], fill=(60, 40, 20, 255))
        return img, d
    if cat == "wonder":
        img, d = _canvas((255, 160, 80), (255, 225, 160))
        _glow(img, 900, 200, 200, (255, 240, 170), 200)
        d.ellipse([860, 160, 940, 240], fill=(255, 245, 190, 255))
        if sub == "wall":
            _hills(d, 450, (120, 140, 90, 255), 12, 110, 140)
            d.polygon([(0, 560), (0, 470), (350, 400), (700, 350), (1050, 280), (1280, 240), (1280, 300), (1050, 340), (700, 410), (350, 460), (0, 540)], fill=(150, 130, 110, 255))
            for k2 in range(14):
                d.rectangle([k2 * 90 + 10, 460 - k2 * 15, k2 * 90 + 40, 480 - k2 * 15], fill=(120, 100, 85, 255))
        elif sub == "dam":
            d.rectangle([0, 480, SW, SH], fill=(40, 110, 180, 255))
            d.polygon([(260, 480), (1020, 480), (940, 250), (340, 250)], fill=(180, 182, 190, 255))
            for k2 in range(5):
                d.polygon([(480 + k2 * 70, 480), (500 + k2 * 70, 480), (495 + k2 * 70, 640), (485 + k2 * 70, 640)], fill=(200, 230, 250, 200))
        elif sub == "elevator":
            img, d = _canvas((6, 10, 40), (40, 70, 140))
            _stars(d, 160, 5, 600)
            d.polygon([(620, 720), (660, 720), (648, 0), (632, 0)], fill=(220, 225, 240, 255))
            d.ellipse([560, 80, 720, 150], fill=(160, 170, 200, 255))
            _glow(img, 640, 120, 120, (150, 200, 255), 120)
        else:
            _hills(d, 560, (230, 195, 120, 255), 6, 40, 200)
            d.polygon([(250, 600), (640, 190), (1030, 600)], fill=(222, 182, 100, 255))
            d.polygon([(640, 190), (1030, 600), (760, 600)], fill=(190, 150, 80, 255))
            d.polygon([(100, 600), (330, 400), (560, 600)], fill=(225, 188, 108, 255))
            d.rectangle([0, 600, SW, SH], fill=(220, 185, 110, 255))
        return img, d
    img, d = _canvas((20, 30, 70), (60, 90, 150))     # عمومی
    _stars(d, 100, 1, 400)
    _glow(img, 640, 360, 300, (100, 160, 255), 120)
    _globe(d, 640, 360, 230)
    return img, d


SCENE_TITLE = {"conquest": "PROVINCE CAPTURED", "ground": "GROUND BATTLE", "air": "AIR STRIKE", "naval": "NAVAL BATTLE",
               "missile": "MISSILE STRIKE"}


def make_scene(cat, sub=None, isos=()):
    """تصویر صحنه‌ای مرتبط با گزارش (کافه، نبرد، پک، ...)؛ در صورت خطا None."""
    if Image is None:
        return None
    try:
        title = None
        if cat == "build" and sub in BLD_EN:
            img, d = sc_building(sub)
            title = "NEW " + BLD_EN[sub]
        elif cat == "build" and sub and sub.startswith("fac:"):
            img, d = sc_factory(sub[4:])
            title = FAC_EN.get(sub[4:], "INDUSTRY")
        elif cat == "battle":
            img, d = sc_war(sub or "ground")
            title = SCENE_TITLE.get(sub or "ground", "BATTLE REPORT")
        elif cat == "war":
            img, d = sc_war("war")
            title = "WAR DECLARED"
        elif cat == "wonder":
            img, d = sc_misc("wonder", sub)
            title = "WORLD WONDER"
        elif cat == "pack":
            pk = {"nuke": ("nuke", None), "ground": ("battle", "ground"), "drone": ("battle", "air"), "def": ("battle", "missile"),
                  "navy": ("battle", "naval"), "missile": ("battle", "missile"), "bomber": ("battle", "air"), "cyber": ("cyber", None),
                  "eco": ("build", "fac:oil"), "vip": ("newleader", None)}.get(sub)
            if pk and pk[0] == "battle":
                img, d = sc_war(pk[1])
            elif pk and pk[0] == "build":
                img, d = sc_factory("oil")
            elif pk:
                img, d = sc_misc(pk[0], pk[1])
            else:
                img, d = sc_misc("pack")
            title = "SPECIAL PACK"
        else:
            img, d = sc_misc(cat if cat not in ("tech", "arms", "admin", "general") else "general", sub)
            if cat == "tech":
                img, d = sc_factory("space")
            elif cat == "arms":
                if sub == "gnd":
                    img, d = sc_war("ground")
                elif sub in ("fighter", "bomber", "heli", "drone"):
                    img, d = sc_war("air")
                elif sub == "navy":
                    img, d = sc_war("naval")
                elif sub in ("missile", "bomb", "aa"):
                    img, d = sc_war("missile")
                elif sub == "cyber":
                    img, d = sc_misc("cyber")
                else:
                    img, d = sc_factory("arms")
            title = CARD_STYLE.get(cat, CARD_STYLE["general"])[0]
        # نوار پایین + عنوان + نشان کشورها
        lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for y in range(SH - 190, SH):
            ld.line([(0, y), (SW, y)], fill=(0, 0, 0, int(215 * (y - (SH - 190)) / 190)))
        for y in range(0, 110):
            ld.line([(0, y), (SW, y)], fill=(0, 0, 0, int(120 * (1 - y / 110))))
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img, "RGBA")
        d.text((56, 38), "WORLD WAR · EMPIRE", font=_font(28), fill=(255, 255, 255, 235))
        d.text((56, 618), title or "REPORT", font=_fit(d, title or "REPORT", 760, 64), fill=(255, 255, 255, 255))
        isos = [i for i in isos if i][:2]
        x = SW - 56
        for iso in reversed(isos):
            d.rounded_rectangle([x - 150, 610, x, 690], radius=18, fill=(0, 0, 0, 150), outline=(255, 255, 255, 230), width=3)
            d.text((x - 75, 650), iso.upper(), font=_font(50), fill=(255, 255, 255, 255), anchor="mm")
            x -= 170
        d.text((SW - 56, 40), "@" + CHANNEL_USERNAME, font=_font(26), fill=(255, 255, 255, 220), anchor="ra")
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=90)
        return buf.getvalue()
    except Exception as e:  # noqa: BLE001
        print("make_scene error:", cat, sub, repr(e)[:160])
        return None


FAC_EN = {"cement": "CEMENT FACTORY", "car": "CAR FACTORY", "steel": "STEEL MILL", "alu": "ALUMINIUM PLANT", "holding": "ECONOMIC HOLDING",
          "refinery": "REFINERY", "tech": "TECH PARK", "arms": "DEFENSE INDUSTRY", "space": "SPACE PROGRAM", "agri": "AGRICULTURE",
          "oil": "OIL FIELD", "ironm": "IRON MINE", "gold": "GOLD MINE", "uran": "URANIUM MINE", "power": "POWER PLANT"}


def infer_cat(text):
    for tag in re.findall(r"#(\S+)", text or ""):
        k = squash(tag)
        if k in TAG_CAT:
            return TAG_CAT[k]
    return "general"


def resolve_photo(cat, isos=(), photo=None, sub=None):
    """اولویت: عکس مخصوص ← عکسی که ادمین برای دسته گذاشته ← فایل پوشه‌ی ww_images ← کارت خودکار."""
    s = DB["settings"]
    if photo:
        return ("id", photo)
    if not s.get("img_on", True):
        return None
    fid = (s.get("imgs") or {}).get(cat)
    if fid:
        return ("id", fid)
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(IMG_DIR, "%s.%s" % (cat, ext))
        if os.path.isfile(p):
            try:
                with open(p, "rb") as f:
                    return ("bytes", f.read(), os.path.basename(p))
            except OSError:
                pass
    if cat.startswith("atk_"):
        sub = {"naval": "naval", "missile": "missile", "drone": "air", "air": "air", "bomber": "air", "ground": "ground"}.get(cat[4:], "ground")
        b = make_scene("battle", sub, isos)
    else:
        b = make_scene(cat, sub, isos)
    if b:
        return ("bytes", b, "report.jpg")
    b = make_card(cat, isos)
    return ("bytes", b, "report.png") if b else None


def send_photo(chat, spec, caption=None, html=False):
    body = {"chat_id": chat}
    if caption:
        body["caption"] = caption[:1000]
        if html:
            body["parse_mode"] = "HTML"
    if spec[0] == "id":
        body["photo"] = spec[1]
        return api("sendPhoto", body)
    name = spec[2] if len(spec) > 2 else "img.png"
    mime = "image/png" if name.lower().endswith("png") else "image/jpeg"
    return api_form("sendPhoto", body, {"photo": (name, spec[1], mime)})


def post_channel(text, cat=None, isos=(), photo=None, sub=None, pin=False, tag=None):
    """گزارش رو (فارسی بالا، ترجمه‌ی انگلیسی پایین) با عکس مربوطه توی کانال می‌ذاره؛ pin=True سنجاق هم می‌کنه."""
    ch = DB["settings"].get("channel")
    if not ch:
        return False, "کانال هنوز ثبت نشده"
    cat = cat or infer_cat(text)
    en = None
    try:
        en = english_of(text)
    except Exception as e:  # noqa: BLE001
        print("bilingual error:", repr(e)[:150])
    spec = None
    try:
        spec = resolve_photo(cat, isos, photo, sub)
    except Exception as e:  # noqa: BLE001
        print("photo resolve error:", e)
    plain = strip_q(text)
    mid = None

    def msg(tx):
        """یک پیام متنی (با نقل‌قول HTML در صورت وجود)؛ شناسه‌ی پیام رو برمی‌گردونه."""
        if tx != strip_q(tx) and len(tx) < 3800:
            try:
                r = api("sendMessage", {"chat_id": ch, "text": to_html(tx), "parse_mode": "HTML"})
                return ((r or {}).get("result") or {}).get("message_id")
            except Exception as e:  # noqa: BLE001
                print("html send error:", str(e)[:150])
        got = None
        for part in split_text(strip_q(tx)):
            r = api("sendMessage", {"chat_id": ch, "text": part})
            got = got or ((r or {}).get("result") or {}).get("message_id")
        return got

    try:
        sent = False
        if spec and len(plain) <= 1000:
            for tx, hf in ((text, True), (plain, False)) if plain != text else ((plain, False),):
                try:
                    r = send_photo(ch, spec, to_html(tx) if hf else tx, hf)
                    mid = ((r or {}).get("result") or {}).get("message_id")
                    sent = True
                    break
                except Exception as e:  # noqa: BLE001
                    print("sendPhoto error:", str(e)[:200])
            if sent and en:
                msg("🇬🇧 ENGLISH\n" + en)
        elif spec:
            try:
                r = send_photo(ch, spec, plain.split("\n")[0][:900])      # عنوان روی عکس، متن کامل بعدش
                mid = ((r or {}).get("result") or {}).get("message_id")
            except Exception as e:  # noqa: BLE001
                print("sendPhoto error:", str(e)[:200])
        if not sent:
            m2 = msg(text + (("\n\n━━━━━━━━━━━━━━━━━━━━\n🇬🇧 ENGLISH\n" + en) if en else ""))
            mid = mid or m2
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:200]
    if pin and mid:
        try:
            api("pinChatMessage", {"chat_id": ch, "message_id": mid, "disable_notification": False})
        except Exception as e:  # noqa: BLE001
            print("pin error:", str(e)[:150])
    LAST_POST["mid"] = mid
    if tag and mid:
        POST_MID[tag] = mid
    return True, ""


LAST_POST = {"mid": None}
POST_MID = {}


CH_Q = queue.Queue(maxsize=300)  # صف محدود برای جلوگیری از انباشته‌شدن حافظه
CH_ASYNC = {"on": False}


def warn_channel(err):
    s = DB["settings"]
    if not s.get("warned"):
        s["warned"] = True
        notify_admins("⚠️ پیام در کانال ارسال نشد: %s\nاز «⚙️ تنظیمات ← 📣 تنظیم کانال» راهنما رو ببین." % err)


def channel_worker():
    while True:
        job = CH_Q.get()
        try:
            ok, err = post_channel(*job)
            if not ok:
                warn_channel(err)
        except Exception as e:  # noqa: BLE001
            print("channel worker error:", e)


def announce(text, cat=None, iso=None, photo=None, sub=None, pin=False, tag=None):
    """گزارش رو توی کانال می‌ذاره (همراه عکس مربوطه). iso = کشور(های) درگیر برای کارت."""
    DB["log"].append({"t": now(), "text": strip_q(text)})
    del DB["log"][:-300]
    isos = tuple(iso) if isinstance(iso, (list, tuple)) else ((iso,) if iso else ())
    job = (text, cat, isos, photo, sub, pin, tag)
    if CH_ASYNC["on"] and DB["settings"].get("channel"):
        try:
            CH_Q.put_nowait(job)
            return True
        except queue.Full:
            print("⚠️ صف گزارش کانال پر است؛ گزارش جدید برای محافظت از سرویس حذف شد.")
            return False
    ok, err = post_channel(*job)
    if not ok:
        warn_channel(err)
    return ok


# ═════════════ منطق بازی ═════════════
def base_income_raw(c):
    return c["prov"] * PER_PROV[c["tier"]]


def base_income(c):
    return base_income_raw(c) * INCOME_MULT          # حقوق/درآمد پایه (چند برابر نسخه‌ی قبل)


def stab_f(c):
    return 0.5 + 0.5 * c["stab"] / 100.0


def gov_of(c):
    return GOVS.get(c.get("gov") or "")


def policy_mult(c):
    k = TAX_LEVELS[c.get("tax", 1)][1]
    g = gov_of(c)
    if g:
        k *= g[1]
    if wonder_has(c, "pyramid"):
        k *= 1.15
    if wonder_has(c, "suez"):
        k *= 1.20
    if wonder_has(c, "elevator"):
        k *= 1.10
    return k * sanc_mult(c)


def fac_lvl(c, k):
    return c["fac"].get(k, 0)


def fac_income(c):
    k = 1.15 if wonder_has(c, "silicon") else 1.0
    return k * sum(FD[x]["money"] * lv for x, lv in c["fac"].items() if x in FD)


def city_mult(city):
    k = 1 + 0.08 * (city["lvl"] - 1)
    if city.get("fest", 0) > now():
        k *= 1.5
    return k


def city_income(c, city):
    base = sum(BD[x]["inc"] * n for x, n in city["b"].items() if x in BD)
    return base * city_mult(city) * (1.25 if c["vip"] else 1.0)


def build_income(c):
    return sum(city_income(c, ct) for ct in c["cities"])


def pop_tax(c):
    return c["pop"] / 1e6 * 0.4


def income_parts(c):
    st = stab_f(c) * policy_mult(c)
    allies = min(4, len(allies_of(c["iso"])))
    core = base_income(c) * (1 + 0.3 * c["eco"]) * (1 + 0.05 * allies) * (1 + 0.03 * union_lvl(c))
    return {"core": core * st, "fac": fac_income(c) * st, "bld": build_income(c) * st, "tax": pop_tax(c) * st}


def income(c):
    return sum(income_parts(c).values())


def cost_eco(c):
    return base_income_raw(c) * 15 * (c["eco"] + 1)


def cost_fort(c):
    return base_income_raw(c) * 8 * (c["fort"] + 1)


def uni_count(c):
    return sum(ct["b"].get("uni", 0) for ct in c["cities"])


def tech_disc(c):
    k = 1 - min(0.3, 0.01 * uni_count(c))
    if wonder_has(c, "library"):
        k *= 0.75
    g = gov_of(c)
    if g:
        k *= g[5]
    return k


def cost_tech(c):
    base = TECH_COST.get(c["tech"] + 1)
    return base * tech_disc(c) if base else None


def arms_disc(c):
    return 1 - min(0.2, 0.02 * fac_lvl(c, "arms"))


def ucost(c, u):
    return u["cost"] * arms_disc(c)


def bdisc(c):
    return max(0.5, 1 - 0.02 * fac_lvl(c, "cement") - (0.2 if c["vip"] else 0))


def fac_cost(c, k):
    return FD[k]["cost"] * 1.55 ** fac_lvl(c, k)


def fac_max(c, k):
    return FAC_MAX + (5 if (c["vip"] and FD[k]["mine"]) else 0)


def rank_idx(c):
    return min(len(RANKS) - 1, int((c.get("xp", 0) / 25.0) ** 0.5))


def xp_add(c, n):
    c["xp"] = c.get("xp", 0) + n


def atk_mult(c):
    k = 1 + 0.005 * rank_idx(c)
    g = gov_of(c)
    return k * (g[3] if g else 1.0)


def air_bonus(c):
    k = 1 + 0.03 * fac_lvl(c, "space")
    return k * (1.3 if wonder_has(c, "elevator") else 1.0)


def def_mult(c):
    k = 1 + 0.02 * union_lvl(c)
    if wonder_has(c, "wall"):
        k *= 1.25
    g = gov_of(c)
    return k * (g[2] if g else 1.0)


def nuke_cap(c):
    return 10 + (10 if wonder_has(c, "manhattan") else 0)


def pop_cap(c):
    housing = sum(ct["b"].get("house", 0) for ct in c["cities"])
    lv = sum(ct["lvl"] for ct in c["cities"])
    return START_POP.get(c["tier"], 5e6) * 3 + housing * 2e6 + lv * 3e6


def stab_regen(c):
    nice = sum(ct["b"].get("park", 0) + ct["b"].get("theater", 0) + ct["b"].get("stadium", 0) for ct in c["cities"])
    g = gov_of(c)
    return 2.0 + min(3.0, 0.05 * nice) + TAX_LEVELS[c.get("tax", 1)][2] + (g[4] if g else 0.0)


def mine_tick(c, h):
    need = sum(MD[k]["elec"] * n for k, n in c["miners"].items() if k in MD)
    if need <= 0:
        return
    use = need * h
    have = c["res"]["elec"]
    ratio = 1.0 if have >= use else (have / use if use > 0 else 0.0)
    c["res"]["elec"] = max(0.0, have - use * ratio)
    prod = sum(MD[k]["btc"] * n for k, n in c["miners"].items() if k in MD) * h * ratio
    if wonder_has(c, "silicon"):
        prod *= 1.3
    c["crypto"]["BTC"] = c["crypto"].get("BTC", 0.0) + prod


def bank_tick(c, h, t):
    b = c["bank"]
    s = DB["settings"]
    dm, lm = s.get("bank_dep_mult", 1.0), s.get("bank_loan_mult", 1.0)
    for d in b["deps"]:
        d["amt"] *= (1 + BANK_KINDS[d["kind"]]["rate"] * dm) ** h
    if b["loan"] > 0:
        age = (t - b["loan_t"]) / 3600.0
        b["loan"] *= (1 + LOAN_RATE * lm * (2 if age > LOAN_GRACE_H else 1)) ** h
        if age > LOAN_GRACE_H:
            c["stab"] = max(0.0, c["stab"] - 1.0 * h)
            if not b["warned"]:
                b["warned"] = 1
                notify_country(c["iso"], "⚠️ وام بانکیت از %d ساعت گذشته! سودش دو برابر شد و ثباتت افت می‌کنه.\n"
                                         "هرچه زودتر «🏦 بانک ← 💸 بازپرداخت وام» رو بزن." % LOAN_GRACE_H)
        if age > LOAN_FORCE_H:
            pay = min(c["money"], b["loan"])
            c["money"] -= pay
            b["loan"] -= pay
            c["stab"] = max(0.0, c["stab"] - 15)
            notify_country(c["iso"], "🏦 بانک مرکزی %s M$ از خزانه‌ات برداشت کرد (وام معوق)!" % m(pay))
            if b["loan"] < 1:
                b["loan"], b["warned"] = 0.0, 0
            else:
                b["loan_t"] = t - (LOAN_GRACE_H + 2) * 3600


def econ_tick(c, dt, spd, t):
    h = dt * spd
    c["money"] += income(c) * h
    c["stab"] = max(0.0, min(100.0, c["stab"] + stab_regen(c) * h))
    vip = c["vip"]
    for k, lv in c["fac"].items():
        f = FD.get(k)
        if not f or not f["res"]:
            continue
        rk, per = f["res"]
        km = 1.5 if (vip and f["mine"]) else 1.0
        if wonder_has(c, "oilcity") and rk in ("oil", "gold"):
            km *= 1.3
        c["res"][rk] += per * lv * km * h
    if wonder_has(c, "dam"):
        c["res"]["elec"] += 40000 * h
    hosp = sum(ct["b"].get("hospital", 0) for ct in c["cities"])
    g = min(0.01, 0.002 + 0.0006 * hosp) + 0.0004 * fac_lvl(c, "agri") * (1.25 if vip else 1.0)
    cap = pop_cap(c)
    if c["pop"] < cap:
        c["pop"] = min(cap, c["pop"] * (1 + g * h))
    mine_tick(c, h)
    bank_tick(c, h, t)


def crypto_shock(sym, frac):
    cc, d = DB["market"]["coins"][sym], COINS[sym]
    old = cc["p"]
    cc["p"] = min(d["p"] * 20, max(d["p"] * 0.05, old * (1 + frac)))
    cc["hist"].append(round(cc["p"], 8))
    up = cc["p"] >= old
    announce("%s %s %s %s\n💱 از %s به %s M$ (%+.0f٪)\n%s\n#کریپتو" % (
        "🚀" if up else "📉", "جهش بزرگ" if up else "سقوط شدید", d["sym"], d["name"], fp(old), fp(cc["p"]),
        (cc["p"] / old - 1) * 100, "خریداران جشن گرفتن!" if up else "بازار قرمز شد!"), cat="crypto")


def market_tick(t):
    mk = DB["market"]
    if t - mk["t"] < 60:
        return
    steps = max(1, min(5, int((t - mk["t"]) // 60)))
    mk["t"] = t
    for _ in range(steps):
        for sym, d in COINS.items():
            cc = mk["coins"][sym]
            drift = 0.012 * (math.log(d["p"]) - math.log(cc["p"]))
            cc["p"] = min(d["p"] * 20, max(d["p"] * 0.05, cc["p"] * math.exp(drift + random.gauss(0, d["vol"]))))
            cc["hist"].append(round(cc["p"], 8))
            del cc["hist"][:-180]
        for k in RES:
            v = mk["res"][k]
            mk["res"][k] = min(2.0, max(0.5, v * math.exp(random.gauss(0, 0.005) - 0.02 * math.log(v))))
    if random.random() < steps / 150.0:
        crypto_shock(random.choice(list(COINS)), random.choice([-1, 1]) * random.uniform(0.08, 0.2))


def tick_all():
    t = now()
    if t - TICK["t"] < 20:
        return
    TICK["t"] = t
    s = DB["settings"]
    if not s["paused"]:
        market_tick(t)
    for c in DB["countries"].values():
        dt = min(t - c.get("last", t), 48 * 3600) / 3600.0
        c["last"] = t
        if c["owner"] and c["alive"] and not s["paused"]:
            econ_tick(c, dt, s["speed"], t)
    ext_tick(t)
    DB["props"] = [p for p in DB["props"] if t - p["t"] < 86400]
    DB["sanctions"] = [x for x in DB["sanctions"] if x["until"] > t - 3600]
    if len(DB["licenses"]) > 300:
        DB["licenses"] = [l for l in DB["licenses"] if lic_valid(l)][-300:]
    if s["auto_events"] and not s["paused"] and t - s["last_event"] > 6 * 3600:
        s["last_event"] = t
        owned = [c for c in DB["countries"].values() if c["owner"] and c["alive"]]
        if owned:
            fire_event(random.choice(owned), random.choice(EVENTS))


def power(c):
    return sum(U[k]["pw"] * n for k, n in c["units"].items() if k in U)


def nuke_count(c):
    return sum(n for k, n in c["units"].items() if k in U and U[k]["cat"] == "nuke")


def score(c):
    return power(c) + c["prov"] * 500 + c["money"] * 0.3 + crypto_value(c) * 0.3


DEF_W = {"gnd": 1.0, "heli": 0.5, "fighter": 0.5, "navy": 0.4, "bomber": 0.1, "drone": 0.2, "aa": 0.3}


def defense(c):
    s = 0.0
    for k, n in c["units"].items():
        u = U.get(k)
        if u and u["cat"] in DEF_W:
            s += u["dfn"] * n * DEF_W[u["cat"]]
    return s * (1 + 0.08 * c["fort"]) * 1.15 * (0.7 + 0.3 * c["stab"] / 100.0) * def_mult(c)


def aa_power(c):
    s = 0.0
    for k, n in c["units"].items():
        u = U.get(k)
        if not u:
            continue
        if u["cat"] == "aa":
            s += u["dfn"] * n
        elif u["cat"] == "fighter":
            s += 0.5 * u["dfn"] * n
    return s


def lose_count(n, frac):
    return min(n, int(n * frac + random.random()))


MODES = {"ground": ["gnd", "heli", "fighter", "navy"],
         "air": ["fighter", "bomber", "heli", "drone", "bomb"],
         "missile": ["missile"]}


def plan_force(c, mode, pct):
    cats = MODES[mode]
    sent = {}
    for k, n in c["units"].items():
        u = U.get(k)
        if u and u["cat"] in cats and n > 0:
            sent[k] = min(n, max(1, int(n * pct / 100.0)))
    if mode == "air":
        planes = sum(q for k, q in sent.items() if U[k]["cat"] in ("fighter", "bomber", "heli", "drone"))
        bombs = [k for k in sent if U[k]["cat"] == "bomb"]
        cap = planes * 8
        tot = sum(sent[k] for k in bombs)
        if tot > cap:
            for k in bombs:
                sent[k] = int(sent[k] * cap / tot) if tot else 0
    return {k: q for k, q in sent.items() if q > 0}


def sent_atk(sent):
    return sum(U[k]["atk"] * q for k, q in sent.items())


def resolve_attack(att, de, mode, sent):
    ground = sum(U[k]["atk"] * q for k, q in sent.items() if U[k]["cat"] not in AIRBORNE)
    air = sum(U[k]["atk"] * q for k, q in sent.items() if U[k]["cat"] in AIRBORNE)
    aa = aa_power(de)
    inter = min(0.75, aa / (aa + air + 1.0)) if air > 0 else 0.0
    A = ((ground + air * (1 - inter) * air_bonus(att)) * atk_mult(att) * random.uniform(0.9, 1.1)
         * (0.7 + 0.3 * att["stab"] / 100.0))
    D = defense(de) * (1 + 0.1 * min(3, len(pact_allies(de["iso"])))) + union_help(de, att)
    res = {"A": A, "D": D, "inter": inter, "win": False, "captured": 0, "R": 0.0, "dmg": 0.0}
    att_frac = {}
    def_frac = 0.0
    money_loss = 0.0
    if mode == "ground":
        R = A / max(D, 1.0)
        res["R"] = R
        if R >= 1.1:
            res["win"] = True
            al = min(0.25, max(0.04, 0.18 / R))
            def_frac = min(0.6, max(0.15, 0.1 + 0.15 * R))
            res["captured"] = 3 if R >= 4 else (2 if R >= 2.5 else 1)
            de["stab"] = max(0.0, de["stab"] - 10)
        elif R <= 0.9:
            al = min(0.5, max(0.2, 0.2 / max(R, 0.01)))
            def_frac = min(0.2, max(0.05, 0.06 + 0.1 * R))
            att["stab"] = max(0.0, att["stab"] - 3)
        else:
            al = 0.12
            def_frac = 0.1
        for k in sent:
            att_frac[k] = 1.0 if U[k]["cat"] in ("missile", "bomb") else al
    else:
        dmg = A / (A + D + 1.0)
        res["dmg"] = dmg
        def_frac = min(0.5, dmg * 0.6)
        money_loss = dmg * 0.25
        res["win"] = dmg >= 0.35
        de["stab"] = max(0.0, de["stab"] - dmg * 12)
        for k in sent:
            c_ = U[k]["cat"]
            att_frac[k] = 1.0 if c_ in ("missile", "bomb") else (inter * 0.35 if c_ in AIRBORNE else 0.04 + 0.18 * (1 - dmg))
    lost_a, lost_d = {}, {}
    for k, q in sent.items():
        n = lose_count(q, att_frac.get(k, 0))
        if n:
            att["units"][k] -= n
            lost_a[k] = n
    for k, n in list(de["units"].items()):
        u = U.get(k)
        if not u or u["cat"] == "nuke" or n <= 0:
            continue
        lo = lose_count(n, def_frac)
        if lo:
            de["units"][k] = n - lo
            lost_d[k] = lo
    if money_loss:
        de["money"] *= (1 - money_loss)
    return res, lost_a, lost_d


def eliminate(de, by=None):
    owner = de["owner"]
    un_remove(de["iso"], "سقوط")
    wonder_release(de["iso"])
    if by:
        for k, n in list(de["units"].items()):
            u = U.get(k)
            if u and u["cat"] != "nuke":
                by["units"][k] = by["units"].get(k, 0) + int(n * 0.3)
        by["money"] += de["money"] * 0.5
    de.update(alive=False, units={}, money=0.0, owner=None, leader="", prov=0)
    DB["wars"] = [w for w in DB["wars"] if de["iso"] not in (w[0], w[1])]
    DB["allies"] = [a for a in DB["allies"] if de["iso"] not in a]
    if owner:
        u = DB["users"].get(owner)
        if u:
            u["country"] = None
        clear(owner)
        tell(owner, "💀 کشورت به‌طور کامل سقوط کرد!\nمی‌تونی دوباره «🌍 درخواست کشور» بدی.", main_rows(owner))


def capture(att, de, n):
    n = min(n, de["prov"])
    de["prov"] -= n
    att["prov"] += n
    loot = de["money"] * 0.12
    de["money"] -= loot
    att["money"] += loot
    fell = de["prov"] <= 0
    if fell:
        eliminate(de, att)
    return n, loot, fell


def launch_nuke(att, de, key):
    n = att["units"].get(key, 0)
    if n <= 0:
        return None
    att["units"][key] = n - 1
    ul, ml, pv, st = NUKE[key]
    aa = sum(U[k]["dfn"] * q for k, q in de["units"].items() if k in U and U[k]["cat"] == "aa")
    p = min(0.6, aa / (aa + 4000.0))
    att["stab"] = max(0.0, att["stab"] - 30)
    if random.random() < p:
        return {"hit": False, "p": p}
    lost = {}
    for k, q in list(de["units"].items()):
        u = U.get(k)
        if u and u["cat"] != "nuke" and q > 0:
            lo = lose_count(q, ul)
            if lo:
                de["units"][k] = q - lo
                lost[k] = lo
    mloss = de["money"] * ml
    de["money"] *= (1 - ml)
    de["stab"] = max(0.0, de["stab"] - st)
    cap = None
    if pv:
        cap = capture(att, de, pv)
    return {"hit": True, "p": p, "lost": lost, "cap": cap, "mloss": mloss, "pop": de["pop"] * (0.02 if key == "tnuke" else 0.05)}


def fire_event(c, e):
    c["money"] = max(0.0, c["money"] * (1 + e.get("money", 0)) + e.get("bonus", 0) * income(c))
    c["stab"] = min(100.0, max(0.0, c["stab"] + e.get("stab", 0)))
    for ek, ev in e.items():
        if ek.startswith("res_") and ek[4:] in c["res"]:
            c["res"][ek[4:]] = max(0.0, c["res"][ek[4:]] * (1 + ev))
    fr = e.get("units", 0)
    if fr:
        for k, n in list(c["units"].items()):
            if k in U and U[k]["cat"] != "nuke":
                c["units"][k] = n - lose_count(n, fr)
    announce("🎲 رویداد جهانی\n%s\n%s: %s\n#رویداد" % (e["name"], cname(c), e["text"]), cat="event", iso=c["iso"])
    notify_country(c["iso"], "🎲 %s\n%s" % (e["name"], e["text"]))


def assign(tuid, iso, leader):
    c = C(iso)
    u = user(tuid)
    old = C(u["country"]) if u.get("country") else None
    if old and old["owner"] == tuid:
        old["owner"] = None
        old["leader"] = ""
    h = DB["settings"]["protect_h"]
    c.update(owner=tuid, leader=leader[:40], last=now(), prot=now() + h * 3600)
    u["country"] = iso
    clear(tuid)
    announce("🏛 رهبر جدید!\n%s اکنون توسط «%s» اداره می‌شود.\n#کشور_جدید" % (cname(c), c["leader"]))
    tell(tuid, "🎉 تبریک! %s به تو واگذار شد.\n🛡 تا %d ساعت تحت حفاظت هستی.\nاز منوی زیر شروع کن 👇" % (cname(c), h),
         main_rows(tuid))


def free_country(iso):
    c = C(iso)
    owner = c["owner"]
    un_remove(iso, "آزاد شد")
    wonder_release(iso)
    if owner:
        u = DB["users"].get(owner)
        if u and u.get("country") == iso:
            u["country"] = None
    c["owner"] = None
    c["leader"] = ""
    DB["wars"] = [w for w in DB["wars"] if iso not in (w[0], w[1])]
    if owner:
        clear(owner)
        tell(owner, "🔓 کشورت توسط ادمین آزاد شد.", main_rows(owner))


def remove_links(iso):
    un_remove(iso, "حذف")
    wonder_release(iso)
    DB["licenses"] = [l for l in DB["licenses"] if iso not in (l["from"], l["to"])]
    DB["sanctions"] = [x for x in DB["sanctions"] if iso not in (x["by"], x["on"])]
    DB["wars"] = [w for w in DB["wars"] if iso not in (w[0], w[1])]
    DB["allies"] = [a for a in DB["allies"] if iso not in a]
    DB["props"] = [p for p in DB["props"] if iso not in (p["a"], p["b"])]
    DB["requests"] = [r for r in DB["requests"]
                      if not (r["type"] == "country" and r["iso"] == iso)
                      and not (r["type"] == "nuke" and iso in (r["att"], r["de"]))]


# ═════════════ هسته‌ی رابط کاربری ═════════════
def route(*labels, admin=False):
    def deco(fn):
        for lab in labels:
            ROUTES[lab] = (fn, admin)
            ROUTE_N[squash(lab)] = lab
        return fn
    return deco


def rx_route(pattern, admin=False):
    def deco(fn):
        REGEX_ROUTES.append((re.compile(pattern), fn, admin))
        return fn
    return deco


def clear(uid):
    CTX.pop(uid, None)
    PHOTO.pop(uid, None)


def ask(uid, prompt, fn, rows=None, back=True):
    CTX[uid] = fn
    rows = [list(r) for r in (rows or [])]
    if back:
        rows.append([B_BACK])
    tell(uid, prompt, rows)


def back_to(uid, text, rows):
    clear(uid)
    tell(uid, text, rows)


def menu(uid, text="🏠 منوی اصلی"):
    clear(uid)
    tell(uid, text, main_rows(uid))


CUSTOM_BTN = "✍️ نوشتن دلخواه"
LEADER_TITLES = ["رئیس‌جمهور", "مارشال", "فرمانده کل", "سردار", "ژنرال", "امپراتور", "سلطان", "پادشاه"]
DECL_PRESETS = ["🔥 تجاوز شما بی‌پاسخ نمی‌مونه", "🛡 برای دفاع از منافع ملی",
                "⚔️ زمان حساب‌کشیدنه", "🚫 بدون متن"]
STMT_PRESETS = ["🕊 ما خواهان صلح و ثبات هستیم", "⚠️ هشدار نهایی به همه‌ی دشمنان",
                "🤝 درهای مذاکره باز است", "💪 ارتش ما آماده‌ی دفاع از مرزهاست",
                "🌍 جهان باید پاسخگو باشد"]
ANN_PRESETS = ["🚀 بازی رسمی شروع شد! همین حالا کشورت رو بگیر.", "🎉 به همه‌ی بازیکنان خوش آمدید!",
               "🔧 بات برای مدتی در حال به‌روزرسانیه."]


def ask_text(uid, prompt, presets, cb, custom_prompt="✍️ متنت رو بنویس:", per_row=1):
    """متن آماده با دکمه؛ یا با دکمه‌ی «نوشتن دلخواه» (یا تایپ مستقیم) متن دلخواه."""
    def h(t):
        if squash(t) == squash(CUSTOM_BTN):
            return ask(uid, custom_prompt, cb)
        cb(t)

    ask(uid, prompt, h, chunk(list(presets), per_row) + [[CUSTOM_BTN]])


def leader_name(uid, t):
    t = t.strip()
    nm = (DB["users"].get(uid, {}).get("name") or "").split(" ")[0]
    return ("%s %s" % (t, nm)).strip() if (t in LEADER_TITLES and nm) else t


# انتخاب «پول یا تجهیزات + مقدار» فقط با دکمه (برای معامله)
def pick_item(uid, prompt, cb, owner=None):
    ask(uid, prompt + "\n(💵 انتقال پول فقط از «🏦 بانک ← 💳 کارت به کارت» ممکنه)", lambda t: item_kind(uid, prompt, cb, owner, t), [["🎖 تجهیزات"]])


def item_kind(uid, prompt, cb, owner, t):
    if "پول" in t:
        pres = [p for p in (100, 500, 1000, 5000, 10000, 50000) if not owner or p <= owner["money"]]
        ask(uid, "💵 چه مبلغی (M$)؟ دکمه بزن یا عدد بنویس.", lambda a: item_money(uid, prompt, cb, owner, a),
            chunk([str(p) for p in pres], 3))
    elif "تجهیزات" in t:
        ask(uid, "🎖 کدوم بخش؟", lambda c: item_cat(uid, prompt, cb, owner, c),
            chunk([k for k in SHOP if k != "☢️ هسته‌ای"], 2))
    else:
        pick_item(uid, prompt, cb, owner)


def item_money(uid, prompt, cb, owner, a):
    v = num(a)
    if not v or v <= 0 or (owner and v > owner["money"]):
        tell(uid, "❌ مبلغ نامعتبر یا بیشتر از موجودیه.")
        return item_kind(uid, prompt, cb, owner, "پول")
    cb(("money", v))


def no_country(uid):
    menu(uid, "🌍 هنوز کشوری نداری! اول «%s» رو بزن." % B_REQ)


def frozen(uid):
    if DB["settings"]["paused"] and not is_admin(uid):
        menu(uid, "⏸ بازی موقتاً توسط ادمین متوقف شده.")
        return True
    return False


def find_country(text, opts):
    s = squash(text)
    if not s:
        return None
    for c in opts:
        if s in (squash(c["fa"]), squash(c["en"]), c["iso"].lower()):
            return c
    hits = [c for c in opts if s in squash(c["fa"]) or s in squash(c["en"])]
    return hits[0] if len(hits) == 1 else None


def pick_user(uid, prompt, fn, flt=None):
    us = [(i, x) for i, x in DB["users"].items() if flt is None or flt(i, x)]
    us.sort(key=lambda p: -p[1].get("seen", 0))
    us = us[:40]
    if not us:
        return back_to(uid, "👤 هنوز بازیکنی ثبت نشده.", main_rows(uid))
    labels = {}
    for i, x in us:
        lab = ulabel(i)
        if x.get("country") and C(x["country"]):
            lab += " · " + flag(x["country"])
        while lab in labels:
            lab += "'"
        labels[lab] = i

    def h(t):
        i = labels.get(t)
        if not i:
            return pick_user(uid, prompt, fn, flt)
        fn(i)

    ask(uid, prompt, h, chunk(list(labels), 2))


def find_units(q):
    s = squash(q)
    if not s:
        return []
    exact = [k for k, u in U.items() if s == k or s == squash(u["name"])]
    if exact:
        return exact
    return [k for k, u in U.items() if s in squash(u["name"])]


def parse_item(text, signed=False, allow_nuke=False):
    t = en_digits(text).strip()
    pat = r"^(.+?)\s+[xX×*]?\s*([-+]?[\d.,]+)\s*$" if signed else r"^(.+?)\s+[xX×*]?\s*([\d.,]+)\s*$"
    mt = re.match(pat, t)
    if not mt:
        return None, "فرمت درست نیست. مثال: «پول 500» یا «F-35 2»"
    name, q = mt.group(1).strip(), num(mt.group(2))
    if q is None or q == 0 or (q < 0 and not signed):
        return None, "مقدار نامعتبره."
    if squash(name) in ("پول", "money", "دلار", "نقد", "مبلغ"):
        return ("money", q), None
    ks = find_units(name)
    if not ks:
        return None, "تجهیزی با نام «%s» پیدا نشد." % name
    if len(ks) > 1:
        return None, "اسم مبهمه: " + "، ".join(U[k]["name"] for k in ks[:4]) + " — دقیق‌تر بنویس (مثلاً f35)."
    if U[ks[0]]["cat"] == "nuke" and not allow_nuke:
        return None, "معامله‌ی تسلیحات هسته‌ای ممنوعه."
    return (ks[0], int(q)), None


def item_txt(it):
    k, q = it
    return ("%s M$ پول" % m(q)) if k == "money" else ("%s× %s" % (m(q), U[k]["name"]))


def has_item(c, it):
    k, q = it
    return c["money"] >= q if k == "money" else c["units"].get(k, 0) >= q


def move_item(src, dst, it):
    k, q = it
    if k == "money":
        src["money"] -= q
        dst["money"] += q
    else:
        src["units"][k] -= q
        dst["units"][k] = dst["units"].get(k, 0) + q


# ═════════════ دکمه‌ها و منوها ═════════════
B_BACK = "🔙 بازگشت"
B_MY, B_ARMY = "🏛 کشور من", "📦 ارتش من"
B_SHOP, B_WAR, B_DIP = "🛒 فروشگاه", "⚔️ جنگ", "🕊 دیپلماسی"
B_ECO, B_STMT = "💰 اقتصاد", "📜 بیانیه"
B_WORLD, B_NEWS, B_RANK, B_HELP = "🌐 وضعیت جهان", "🗞 اخبار", "🏆 رتبه‌بندی", "ℹ️ راهنما"
B_REQ, B_ADMIN = "🌍 درخواست کشور", "🛠 پنل ادمین"
B_DECL, B_ATK, B_PEACE, B_WARS, B_NUKE = "📣 اعلام جنگ", "💥 حمله", "🕊 درخواست صلح", "📊 جنگ‌های من", "☢️ حمله هسته‌ای"
B_TRADE, B_ALLY, B_BREAK, B_AID = "🤝 پیشنهاد معامله", "🛡 درخواست ائتلاف", "💔 لغو ائتلاف", "🎁 کمک مالی"
B_UP_ECO, B_UP_TECH, B_UP_FORT = "📈 ارتقای اقتصاد", "🔬 تحقیقات", "🧱 استحکامات"
A_PANEL = "⬅️ بازگشت به پنل"
A_REQ, A_COUNTRIES, A_PLAYERS, A_RES = "📥 درخواست‌ها", "🌍 مدیریت کشورها", "👥 بازیکنان", "💵 منابع و تجهیزات"
A_ANN, A_EVENT, A_SET, A_STATS = "📢 اعلان‌ها", "🎲 رویداد جهانی", "⚙️ تنظیمات", "📊 آمار"
A_ADD, A_DEL, A_FREE, A_REVIVE, A_GIVE = "➕ افزودن کشور", "🗑 حذف کشور", "🔓 آزادسازی کشور", "♻️ احیای کشور", "🎁 واگذاری مستقیم"
A_LIST, A_BAN, A_MSG, A_ADDADMIN = "📋 لیست بازیکنان", "🚫 بن/آنبن", "✉️ پیام به بازیکن", "👑 افزودن ادمین"
A_MONEY, A_UNITS, A_ATTR = "💰 تغییر پول", "🎖 تغییر تجهیزات", "⚙️ ویژگی‌های کشور"
A_CH, A_ALL = "📣 پیام به کانال", "📨 پیام به همه"
A_PAUSE, A_SPEED, A_PROT, A_AUTO = "⏸ توقف/ادامه بازی", "⚡ سرعت بازی", "🛡 مدت حفاظت", "🔁 رویداد خودکار"
A_SETCH, A_TESTCH, A_RESET = "📣 تنظیم کانال", "🧪 تست کانال", "♻️ ریست بازی"
A_RECOVERY, A_EXPORT, A_LOGSNAP = "📥 بازیابی از فایل/لاگ", "📤 دریافت پشتیبان کامل", "🧾 ثبت snapshot در لاگ Railway"

COUNTRY_ROWS = [[A_ADD, A_DEL], [A_FREE, A_REVIVE], [A_GIVE], [A_PANEL]]
PLAYER_ROWS = [[A_LIST, A_BAN], [A_MSG, A_ADDADMIN], [A_PANEL]]
RES_ROWS = [[A_MONEY, A_UNITS], [A_ATTR], [A_PANEL]]
ANN_ROWS = [[A_CH, A_ALL], [A_PANEL]]
SET_ROWS = [[A_PAUSE, A_SPEED], [A_PROT, A_AUTO], [A_SETCH, A_TESTCH], [A_RESET], [A_PANEL]]
# ═════════════ دکمه‌های امکانات جدید ═════════════
PG_NEXT, PG_PREV = "➡️ صفحه بعد", "⬅️ صفحه قبل"
B_BUILD, B_BANK, B_CRYPTO = "🏗 ساخت و ساز", "🏦 بانک", "₿ ارز دیجیتال"
B_UNION, B_PACKS, B_CYBER = "🛡 اتحاد", "🛍 پک‌های ویژه", "💻 عملیات سایبری"
B_FACT, B_MARKET, B_RES = "🏭 صنایع و معادن", "🛢 بازار منابع", "📦 منابع من"
B_POLICY, B_SALARY, B_QUEST, B_SANC = "💼 سیاست‌های داخلی", "🎁 حقوق روزانه", "🎯 ماموریت‌ها", "🚫 تحریم‌ها"
B_SENDSTMT, B_SETPHOTO, B_DELPHOTO = "✍️ ارسال بیانیه", "🖼 تنظیم عکس بیانیه", "🗑 حذف عکس بیانیه"
SH_NAT, SH_FOR, SH_LIC, SH_BLACK = "🏳️ تجهیزات ملی", "🌍 تجهیزات خارجی", "🎫 مجوزهای تسلیحاتی", "🕶 بازار سیاه"
LC_MY, LC_ISSUE, LC_REQ, LC_GR = "📜 مجوزهای من", "✍️ صدور مجوز", "📝 درخواست مجوز", "📤 مجوزهای صادرشده"
LK_REQ, LK_BLACK = "📝 درخواست مجوز برای این تجهیز", "🕶 خرید از بازار سیاه (گرون‌تر، ریسک رسوایی)"
LT_PERM, LT_PAID, LT_COUNT = "🔓 دائمی (بدون محدودیت)", "💰 در ازای پول (زمان‌دار)", "🔢 عددی (تعداد مشخص)"
BL_CITIES, BL_NEW, BL_BUILD = "🏙 شهرهای من", "➕ ساخت شهر جدید", "🏪 ساخت مرکز درآمدزا"
BL_UP, BL_FEST, BL_DEMO, BL_WONDER = "⬆️ ارتقای شهر", "🎉 برگزاری جشنواره", "💥 تخریب ساختمان", "🏛 ابرپروژه‌ها"
CR_MARKET, CR_WALLET, CR_BUY, CR_SELL, CR_MINE = "📊 بازار ارزها", "👛 کیف پول", "🛒 خرید ارز", "💱 فروش ارز", "⛏ ماینینگ"
BK_DEP, BK_WD, BK_LOAN, BK_REPAY, BK_STATUS = "💰 سپرده‌گذاری", "🏧 برداشت سپرده", "💳 دریافت وام", "💸 بازپرداخت وام", "📄 وضعیت حساب"
UN_NEW, UN_JOIN, UN_RANK, UN_INFO = "➕ ساخت اتحاد جدید", "📨 درخواست عضویت", "🏆 رتبه‌بندی اتحادها", "📋 اطلاعات اتحاد"
UN_MEMBERS, UN_DON, UN_UP, UN_MSG = "👥 اعضای اتحاد", "💰 کمک به خزانه‌ی اتحاد", "⬆️ ارتقای اتحاد", "📢 پیام به اعضا"
UN_INV, UN_MANAGE, UN_LEAVE, UN_LOG = "📩 دعوت کشور", "👑 مدیریت اتحاد", "🚪 ترک اتحاد", "📜 تاریخچه اتحاد"
UN_WAR, UN_WD, UN_SPLIT, UN_KICK = "⚔️ جنگ اتحادی", "🏧 برداشت از خزانه‌ی اتحاد", "🎁 پخش پول بین اعضا", "👢 اخراج عضو"
UN_OFF, UN_TRANS, UN_MOTTO, UN_PHOTO, UN_DIS = "🎖 افسر کردن/عزل", "🔄 انتقال رهبری", "✏️ تغییر شعار", "🖼 تصویر اتحاد", "💥 انحلال اتحاد"
CY_FIN, CY_SPY, CY_DEF = "🏦 هک مالی", "🕵️ جاسوسی", "🛡 وضعیت سایبری من"
SC_ADD, SC_LIFT, SC_LIST = "🚫 اعمال تحریم", "🕊 لغو تحریم", "📋 تحریم‌های فعال"
PO_TAX, PO_GOV, PO_DRAFT, PO_PROPA = "🧾 نرخ مالیات", "🏛 نوع حکومت", "🪖 سربازگیری عمومی", "📣 تبلیغات ملی"
A_PACKADM, A_PACKGIVE, A_PACKLOG = "🛍 مدیریت پک‌ها", "🎁 فعال‌سازی پک برای کشور", "📜 تاریخچه‌ی پک‌ها"
A_IMG, A_ECOADM, A_RULES, A_LICADM = "🖼 عکس گزارش‌ها", "📈 بازار و بانک", "📜 قوانین و مجوزها", "🎫 مدیریت مجوزها"

SHOP_HUB = [[SH_NAT, SH_FOR], [SH_LIC, SH_BLACK], [B_PACKS], [B_BACK]]
LIC_ROWS = [[LC_MY, LC_REQ], [LC_ISSUE, LC_GR], [B_SHOP], [B_BACK]]
BUILD_ROWS = [[BL_CITIES, BL_NEW], [BL_BUILD, BL_UP], [BL_FEST, BL_DEMO], [BL_WONDER], [B_BACK]]
CRYPTO_ROWS = [[CR_MARKET, CR_WALLET], [CR_BUY, CR_SELL], [CR_MINE], [B_BACK]]
BANK_ROWS = [[BK_DEP, BK_WD], [BK_LOAN, BK_REPAY], [BK_STATUS], [B_BACK]]
UN_NONE_ROWS = [[UN_NEW, UN_JOIN], [UN_RANK], [B_BACK]]
UN_ROWS = [[UN_INFO, UN_MEMBERS], [UN_DON], [UN_MSG, UN_INV], [UN_LOG, UN_RANK], [UN_MANAGE, UN_LEAVE], [B_BACK]]
UN_MAN_ROWS = [[UN_WAR, UN_WD], [UN_SPLIT, UN_KICK], [UN_OFF, UN_TRANS], [UN_MOTTO, UN_PHOTO], [UN_DIS], [B_UNION]]
CYBER_ROWS = [[CY_FIN, CY_SPY], [CY_DEF], [B_WAR]]
SANC_ROWS = [[SC_ADD, SC_LIFT], [SC_LIST], [B_DIP]]
POLICY_ROWS = [[PO_TAX, PO_GOV], [PO_DRAFT, PO_PROPA], [B_ECO]]
PACK_ADM_ROWS = [[A_PACKGIVE, A_PACKLOG], [A_PANEL]]
RULES_ROWS = [[A_LICADM], [A_PANEL]]



WAR_ROWS = [[B_DECL, B_ATK], [B_PEACE, B_WARS], [B_NUKE, B_CYBER], [B_BACK]]
DIP_ROWS = [[B_TRADE, B_ALLY], [B_BREAK, B_AID], [B_UNION, B_SANC], [B_BACK]]
ECO_ROWS = [[B_UP_ECO, B_UP_TECH], [B_UP_FORT, B_FACT], [B_MARKET, B_RES], [B_POLICY, B_SALARY], [B_BACK]]
ADMIN_ROWS = [[A_REQ, A_COUNTRIES], [A_MONEY, A_PACKADM], [A_PLAYERS, A_RES], [A_RULES, A_IMG],
              [A_ECOADM, A_ANN], [A_EVENT, A_SET], [A_LOGSNAP, A_RECOVERY], [A_EXPORT], [A_STATS], [B_BACK]]


def main_rows(uid):
    if mine(uid):
        rows = [[B_MY, B_SHOP], [B_WAR, B_DIP], [B_ECO, B_BUILD], [B_BANK, B_CRYPTO], [B_UNION, B_PACKS],
                [B_STMT, B_STRAIT], [B_CUP, B_RANK]]
    else:
        rows = [[B_REQ], [B_CUP, B_RANK]]
    rows.append([B_LANG])
    if is_admin(uid):
        n = len(DB["requests"])
        rows.append([B_ADMIN] + (["📥 درخواست‌ها (%d)" % n] if n else []))
    return rows


def start_text(uid):
    return ("🌍 WORLD WAR | SEASON 2\n"
            "ــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
            "🫡 سلام فرمانده! به میدان نبرد خوش آمدی!\n\n"
            "⚔️ «نبرد آغاز می‌شود، قدرت‌ها به میدان می‌آیند، و تاریخ را فاتحان می‌نویسند!»\n\n"
            "🎖️ فرمانده، کشور خود را انتخاب کن و سرنوشت ملتت را رقم بزن!\n\n"
            "🔥 آماده‌ای برای فتح تاریخ؟")


# ═════════════ امکانات بازیکن ═════════════
def r_help(uid):
    tell(uid, (
        "ℹ️ راهنمای بازی\n\n"
        "🎯 هدف: کشورت رو قدرتمند کن، متحد بساز، بجنگ و امپراتوری بشو!\n\n"
        "1️⃣ «درخواست کشور» بزن؛ بعد از تأیید ادمین کشور مال توئه (۱۲ ساعت اول تحت حفاظتی).\n"
        "2️⃣ هر ساعت درآمد می‌گیری (M$ = میلیون دلار). از «اقتصاد» درآمد، تکنولوژی و استحکامات رو ارتقا بده.\n"
        "3️⃣ از «فروشگاه» تجهیزات واقعی بخر: F-35، آبرامز، B-2، S-400، ناو، موشک، بمب ...\n"
        "4️⃣ «جنگ»: اعلام جنگ ← حمله زمینی/هوایی/موشکی ← تصرف استان. "
        "پدافند هوایی جلوی حمله هوایی و موشکی رو می‌گیره. حمله هسته‌ای فقط با تأیید ادمین.\n"
        "5️⃣ «دیپلماسی»: معامله، ائتلاف و کمک مالی. با «درخواست صلح» جنگ رو تموم کن.\n"
        "6️⃣ «بیانیه»: پیامت رو (حتی با عکس) توی کانال منتشر کن.\n"
        "7️⃣ «فروشگاه»: هر کشور تجهیزات واقعیِ ساخت خودش رو آزاد می‌خره؛ تجهیزات کشورهای دیگه «مجوز» می‌خواد "
        "(دائمی / در ازای پول / عددی) یا از بازار سیاه با ریسک.\n"
        "8️⃣ «ساخت و ساز»، «بانک»، «ارز دیجیتال»، «اتحاد»، «پک‌های ویژه» و «ماموریت‌ها» رو هم امتحان کن!\n\n"
        "💡 کشورهای بدون رهبر رو می‌شه بدون اعلام جنگ مورد حمله قرار داد.\n"
        "📢 کانال: @%s" % CHANNEL_USERNAME), main_rows(uid))


@route(B_REQ)
def r_request(uid):
    if mine(uid):
        return menu(uid, "تو همین حالا یک کشور داری 😉")
    if any(r["type"] == "country" and r["uid"] == uid for r in DB["requests"]):
        return menu(uid, "⏳ درخواست قبلی‌ات هنوز در انتظار تأیید ادمینه.")

    def free(c):
        return c["alive"] and not c["owner"]

    fr = [c for c in DB["countries"].values() if free(c)]
    if not fr:
        return menu(uid, "😕 فعلاً کشور آزادی نیست. بعداً دوباره امتحان کن.")
    lines = []
    for tier in (5, 4, 3, 2, 1):
        cs = [c for c in fr if c["tier"] == tier]
        if cs:
            names = "، ".join(cname(c) for c in cs[:10]) + (" و %d کشور دیگه" % (len(cs) - 10) if len(cs) > 10 else "")
            lines.append("%s (%d): %s" % (TIER_NAME[tier], len(cs), names))
    pick_country(uid, "🌍 %d کشور آزاده:\n\n%s\n\n👇 با دکمه‌ها ورق بزن یا اسم کشور رو تایپ کن" % (len(fr), "\n\n".join(lines)),
                 lambda iso: req_leader(uid, iso), free)


def req_leader(uid, iso):
    ask_text(uid, "🎖 لقب رهبرت رو انتخاب کن (اسمت کنارش گذاشته می‌شه):", LEADER_TITLES,
             lambda t: req_submit(uid, iso, leader_name(uid, t)), "✍️ اسم یا لقب رهبرت رو بنویس:", per_row=2)


def req_submit(uid, iso, leader):
    c = C(iso)
    leader = leader.strip()[:40]
    if not c or not c["alive"] or c["owner"] or not leader:
        return menu(uid, "😕 این کشور دیگه در دسترس نیست یا نام رهبر خالیه. دوباره تلاش کن.")
    if is_admin(uid):  # ادمین هم بازیکنه و کشورش بدون نیاز به تأیید داده می‌شه
        return assign(uid, iso, leader)
    r = {"id": nid(), "type": "country", "uid": uid, "iso": iso, "leader": leader, "t": now()}
    DB["requests"].append(r)
    notify_admins(req_text(r), [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]], [A_PANEL]])
    menu(uid, "✅ درخواست %s برای ادمین ارسال شد.\nمنتظر تأیید بمون ⏳" % cname(c))


def req_text(r):
    if r["type"] in EXT_REQ:
        return ext_req_text(r)
    if r["type"] == "country":
        c = C(r["iso"])
        return "🆕 درخواست کشور (%d)\n👤 %s\n🏳️ %s\n🎖 رهبر: %s" % (
            r["id"], ulabel(r["uid"]), cname(c) if c else r["iso"], r["leader"])
    if r["type"] == "pack":
        c, pk = C(r["iso"]), PK[r["pack"]]
        return "🛍 درخواست خرید پک (%d)\n👤 %s\n🏳️ %s\n📦 %s\n💰 قیمت: %s تومان" % (
            r["id"], ulabel(r["uid"]), cname(c) if c else r["iso"], pk["name"], m(pk["price"]))
    if r["type"] == "license":
        c, g = C(r["iso"]), C(r["org"])
        return "🎫 درخواست مجوز تسلیحاتی (%d)\n👤 %s\n🏳️ خریدار: %s\n🏭 سازنده: %s\n%s\n%s" % (
            r["id"], ulabel(r["uid"]), cname(c) if c else r["iso"], cname(g) if g else r["org"],
            scope_text(r["scope"]), terms_text(r["terms"]))
    a, d = C(r["att"]), C(r["de"])
    return "☢️ درخواست حمله هسته‌ای (%d)\n👤 %s\n⚔️ مهاجم: %s\n🛡 هدف: %s\n🚀 %s" % (
        r["id"], ulabel(r["uid"]), cname(a) if a else r["att"], cname(d) if d else r["de"], U[r["key"]]["name"])


@route(B_MY)
def r_my(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    en = [cname(C(i)) for i in enemies(c["iso"]) if C(i)]
    al = [cname(C(i)) for i in allies_of(c["iso"]) if C(i)]
    L = ["🏛 " + cname(c), "👤 رهبر: " + c["leader"], "━━━━━━━━━━━━",
         "💰 خزانه: %s M$  (+%s در ساعت)" % (m(c["money"]), m(income(c))),
         "🔬 تکنولوژی: %d/6 | 🏭 اقتصاد: %d/10 | 🧱 استحکامات: %d/10" % (c["tech"], c["eco"], c["fort"]),
         "🗺 استان‌ها: %d | 😐 ثبات: %d٪" % (c["prov"], int(c["stab"])),
         "💪 قدرت نظامی: " + m(power(c)),
         "👥 جمعیت: %s | 🎖 رتبه: %s" % (m(c["pop"]), RANKS[rank_idx(c)])]
    if nuke_count(c):
        L.append("☢️ کلاهک هسته‌ای: %d" % nuke_count(c))
    L.append("😊 رضایت مردمی: %d٪%s" % (int(c.get("sat", 60)), " 🚨 اعتراضات" if c.get("protest") else ""))
    L.append("⚔️ در جنگ با: " + ("، ".join(en) if en else "—"))
    L.append("🤝 متحدان: " + ("، ".join(al) if al else "—"))
    un = un_get(c)
    if un:
        L.append("🛡 اتحاد: %s (سطح %d)" % (un_label(un), un["lvl"]))
    if c.get("vip"):
        L.append("💎 اشتراک VIP فعاله")
    if c["prot"] > now():
        L.append("🛡 تحت حفاظت تا %s دیگر" % dur(c["prot"] - now()))
    tell(uid, "\n".join(L), [[B_ARMY, B_ECO], [B_CHANGE], [B_BACK]])


@route(B_ARMY)
def r_army(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    by = {}
    for k, n in c["units"].items():
        if n > 0 and k in U:
            by.setdefault(U[k]["cat"], []).append((U[k]["name"], n))
    L = ["📦 ارتش " + cname(c), "💪 قدرت کل: " + m(power(c)), ""]
    for cat in CAT_LABEL:
        if cat in by:
            L.append(CAT_LABEL[cat])
            L += ["  • %s: %s" % (nm, m(n)) for nm, n in by[cat]]
    if not by:
        L.append("هیچ تجهیزاتی نداری!")
    tell(uid, "\n".join(L), [[B_SHOP, B_BACK]])


def pack_of(t):
    return next((p for p in PACKS if squash(p["name"]) == squash(t)), None)


def national_units(iso):
    return [u for u in U.values() if iso in u["org"]]


def lab_of(u):
    return next(k for k, cats in SHOP.items() if u["cat"] in cats)


# ═════════════ انتخاب‌گرهای صفحه‌بندی‌شده ═════════════
def ask_photo(uid, prompt, cb, rows=None, on_text=None):
    """منتظر عکس می‌مونه؛ cb(file_id, caption). اگه متن بفرسته on_text(متن) صدا زده می‌شه."""
    def th(t):
        PHOTO.pop(uid, None)
        if on_text:
            return on_text(t)
        tell(uid, "❌ باید خودِ عکس رو (به‌صورت Photo) می‌فرستادی؛ لغو شد.")
        menu(uid)

    ask(uid, prompt, th, rows)
    PHOTO[uid] = cb


def pick_unit(uid, prompt, units, cb, page=0, per=10, lines=None):
    """انتخاب تجهیز با صفحه‌بندی؛ cb(key). با تایپ بخشی از اسم هم پیدا می‌شه."""
    pages = max(1, (len(units) + per - 1) // per)
    page = max(0, min(page, pages - 1))
    view = units[page * per:(page + 1) * per]
    txt = prompt
    if lines:
        txt += "\n\n" + "\n".join(lines(u) for u in view)
    if pages > 1:
        txt += "\n\n📄 صفحه %d از %d (یا بخشی از اسم رو تایپ کن)" % (page + 1, pages)
    rows = [[u["name"]] for u in view]
    nav = ([PG_PREV] if page > 0 else []) + ([PG_NEXT] if page < pages - 1 else [])
    if nav:
        rows.append(nav)

    def h(t):
        s = squash(t)
        if s == squash(PG_NEXT):
            return pick_unit(uid, prompt, units, cb, page + 1, per, lines)
        if s == squash(PG_PREV):
            return pick_unit(uid, prompt, units, cb, page - 1, per, lines)
        u = next((x for x in units if squash(x["name"]) == s), None)
        if not u and s:
            hits = [x for x in units if s in squash(x["name"])]
            u = hits[0] if len(hits) == 1 else None
        if not u:
            tell(uid, "❓ پیدا نشد؛ از دکمه‌ها انتخاب کن یا اسم رو دقیق‌تر بنویس.")
            return pick_unit(uid, prompt, units, cb, page, per, lines)
        cb(u["key"])

    ask(uid, txt, h, rows)


def pick_country(uid, prompt, fn, flt=None, extra=None, page=0):
    opts = [c for c in DB["countries"].values() if flt is None or flt(c)]
    opts.sort(key=lambda c: (-c["tier"], c["fa"]))
    ex = extra or {}
    if not opts and not ex:
        return back_to(uid, "😕 گزینه‌ای برای انتخاب وجود نداره.", main_rows(uid))
    per = 30
    pages = max(1, (len(opts) + per - 1) // per)
    page = max(0, min(page, pages - 1))
    view = opts[page * per:(page + 1) * per]
    clabels = {cname(c): c["iso"] for c in opts}
    rows = [[lab] for lab in ex] + chunk([cname(c) for c in view], 3)
    nav = ([PG_PREV] if page > 0 else []) + ([PG_NEXT] if page < pages - 1 else [])
    if nav:
        rows.append(nav)
    txt = prompt if pages == 1 else "%s\n\n📄 صفحه %d از %d — یا اسم کشور رو تایپ کن" % (prompt, page + 1, pages)

    def h(t):
        if t in ex:
            return fn(ex[t])
        if squash(t) == squash(PG_NEXT):
            return pick_country(uid, prompt, fn, flt, extra, page + 1)
        if squash(t) == squash(PG_PREV):
            return pick_country(uid, prompt, fn, flt, extra, page - 1)
        iso = clabels.get(t)
        if not iso:
            hit = find_country(t, opts)
            iso = hit["iso"] if hit else None
        if not iso:
            tell(uid, "❓ پیدا نشد. از دکمه‌ها انتخاب کن یا اسم کشور رو درست بنویس.")
            return pick_country(uid, prompt, fn, flt, extra, page)
        fn(iso)

    ask(uid, txt, h, rows)


def item_cat(uid, prompt, cb, owner, t):
    lab = next((k for k in SHOP if squash(k) == squash(t) and k != "☢️ هسته‌ای"), None)
    if not lab:
        return item_kind(uid, prompt, cb, owner, "تجهیزات")
    units = sorted((u for u in U.values() if u["cat"] in SHOP[lab]
                    and (not owner or owner["units"].get(u["key"], 0) > 0)), key=lambda u: (u["tech"], u["cost"]))
    if not units:
        tell(uid, "😕 تجهیزاتی در این بخش نداری.")
        return item_kind(uid, prompt, cb, owner, "تجهیزات")
    pick_unit(uid, "🎖 کدوم تجهیز؟", units, lambda key: item_unit(uid, prompt, cb, owner, lab, key), per=12,
              lines=lambda u: "• %s%s" % (u["name"], (" — داری: %s" % m(owner["units"][u["key"]])) if owner else ""))


def item_unit(uid, prompt, cb, owner, lab, key):
    have = owner["units"].get(key, 0) if owner else None
    rows = chunk([str(q) for q in (1, 5, 10, 25, 50, 100) if have is None or q <= have], 3)
    if have:
        rows.append(["همه"])
    ask(uid, "چند تا؟ (دکمه بزن یا عدد بنویس)", lambda q: item_qty(uid, prompt, cb, owner, lab, key, q), rows)


def item_qty(uid, prompt, cb, owner, lab, key, t):
    have = owner["units"].get(key, 0) if owner else None
    if squash(t) == "همه" and have:
        q = have
    else:
        v = num(t)
        q = int(v) if v and v > 0 else 0
    if q <= 0 or (have is not None and q > have):
        tell(uid, "❌ تعداد نامعتبر.")
        return item_unit(uid, prompt, cb, owner, lab, key)
    cb((key, q))


# ═════════════ فروشگاه: تجهیزات ملی / خارجی با مجوز / بازار سیاه ═════════════
@route(B_SHOP)
def r_shop(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    nat = [u for u in national_units(c["iso"]) if u["cat"] != "nuke"]
    gen = sum(1 for u in U.values() if not u["org"])
    on = DB["settings"].get("lic_on", True)
    back_to(uid, ("🛒 فروشگاه نظامی\n💰 موجودی: %s M$ | 🔬 تکنولوژی: %d\n\n"
                  "🏳️ تجهیزات ملی %s: %d مدل ساخت خودت + %d مدل عمومی\n🎫 مجوزهای فعال تو: %d\n\n%s")
            % (m(c["money"]), c["tech"], cname(c), len(nat), gen, len(my_licenses(c["iso"])),
               ("هر کشور تجهیزات واقعیِ ساخت خودش رو آزادانه می‌خره؛ برای تجهیزات کشورهای دیگه باید «مجوز» بگیری "
                "(دائمی / در ازای پول / عددی) یا از بازار سیاه با ریسک بخری.") if on else
               "ℹ️ سیستم مجوز فعلاً توسط ادمین خاموشه؛ همه چیز آزاده."), SHOP_HUB)


def shop_units(c, scope):
    if scope["mode"] == "nat":
        return [u for u in U.values() if c["iso"] in u["org"] or not u["org"]]
    return [u for u in U.values() if scope["org"] in u["org"] and c["iso"] not in u["org"] and u["cat"] != "nuke"]


def shop_head(c, scope):
    if scope["mode"] == "nat":
        return "🏳️ تجهیزات ملی %s (آزاد + تجهیزات عمومی)" % cname(c)
    o = C(scope["org"])
    if scope["mode"] == "black":
        return "🕶 بازار سیاه — تجهیزات ساخت %s بدون مجوز (×%s قیمت، ۲۰٪ ریسک رسوایی)" % (
            cname(o), DB["settings"].get("black_mult", 2.2))
    return "🌍 تجهیزات ساخت %s — برای خرید «مجوز» لازمه" % cname(o)


@route(SH_NAT)
def r_shop_nat(uid):
    if mine(uid):
        shop_cats(uid, {"mode": "nat"})
    else:
        no_country(uid)


@route(SH_FOR)
def r_shop_for(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_country(uid, "🌍 تجهیزات ساخت کدوم کشور رو می‌خوای ببینی؟", lambda iso: shop_cats(uid, {"mode": "for", "org": iso}),
                 lambda x: x["iso"] in ORG_INDEX and x["iso"] != c["iso"])


@route(SH_BLACK)
def r_shop_black(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if not DB["settings"].get("black_on", True):
        return back_to(uid, "🕶 بازار سیاه فعلاً توسط ادمین بسته‌ست.", SHOP_HUB)
    pick_country(uid, "🕶 بازار سیاه: تجهیزات ساخت کدوم کشور؟", lambda iso: shop_cats(uid, {"mode": "black", "org": iso}),
                 lambda x: x["iso"] in ORG_INDEX and x["iso"] != c["iso"])


def shop_cats(uid, scope):
    c = mine(uid)
    if not c:
        return no_country(uid)
    units = shop_units(c, scope)
    rows, L = [], []
    for lab, cats in SHOP.items():
        n = sum(1 for u in units if u["cat"] in cats)
        if n:
            rows.append(lab)
            L.append("%s: %d مدل" % (lab, n))
    head = shop_head(c, scope)
    if not rows:
        return back_to(uid, head + "\n\n😕 تجهیزاتی توی این بخش نیست.", SHOP_HUB)
    ask(uid, "%s\n\n%s\n\n👇 بخش رو انتخاب کن" % (head, "\n".join(L)), lambda t: shop_cat(uid, scope, t), chunk(rows, 2))


def shop_line(c, scope, u):
    acc = unit_access(c, u["key"])
    black = scope["mode"] == "black"
    st = "🕶" if black else {"own": "✅", "generic": "✅", "lic": "🎫"}.get(acc["how"], "🔐")
    if u["tech"] > c["tech"]:
        st = "🔒"
    price = ucost(c, u) * (DB["settings"].get("black_mult", 2.2) if black else 1.0)
    extra = ""
    if acc["how"] == "lic" and not black:
        extra = " | مجوز: " + ("نامحدود" if acc["cap"] is None else "%s عدد" % m(acc["cap"]))
    return "%s %s\n    💲%s M$ | سطح %d | داری: %s%s" % (st, u["name"], m(price), u["tech"],
                                                      m(c["units"].get(u["key"], 0)), extra)


def shop_cat(uid, scope, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    lab = next((k for k in SHOP if squash(k) == squash(t)), None)
    if not lab:
        return shop_cats(uid, scope)
    units = sorted((u for u in shop_units(c, scope) if u["cat"] in SHOP[lab]), key=lambda u: (u["tech"], u["cost"]))
    if not units:
        tell(uid, "😕 این بخش خالیه.")
        return shop_cats(uid, scope)
    head = "%s\n%s\n💰 %s M$ | 🔬 تکنولوژی %d" % (lab, shop_head(c, scope), m(c["money"]), c["tech"])
    pick_unit(uid, head, units, lambda key: shop_unit(uid, scope, key, lab), per=8, lines=lambda u: shop_line(c, scope, u))


def shop_unit(uid, scope, key, lab):
    c = mine(uid)
    if not c:
        return no_country(uid)
    u = U[key]
    if u["tech"] > c["tech"]:
        tell(uid, "🔒 برای «%s» باید تکنولوژی %d داشته باشی (الان %d)." % (u["name"], u["tech"], c["tech"]))
        return shop_cat(uid, scope, lab)
    black = scope["mode"] == "black"
    acc = unit_access(c, key)
    if not black and acc["how"] == "none":
        return shop_locked(uid, scope, key, lab)
    price = ucost(c, u) * (DB["settings"].get("black_mult", 2.2) if black else 1.0)
    mx = int(c["money"] // price)
    cap = None if (black or acc["how"] != "lic") else acc["cap"]
    if cap is not None:
        mx = min(mx, cap)
    note = ""
    if black:
        note = "\n🕶 بازار سیاه: ۲۰٪ ریسک رسوایی (افت ثبات + خبر در کانال)"
    elif acc["how"] == "lic":
        note = "\n🎫 با مجوز — " + ("نامحدود" if cap is None else "حداکثر %s عدد طبق مجوز" % m(cap)) + \
               "\n💰 ۱۰٪ از خرید به‌عنوان درآمد صادرات به کشور سازنده می‌رسه"
    ask(uid, "🛒 %s\n🏷 سازنده: %s\n💲 قیمت: %s M$\n💰 موجودی: %s M$ (حداکثر %s عدد)%s\n\nچند تا می‌خوای؟"
        % (u["name"], ("، ".join(cname(C(i)) for i in u["org"] if C(i)) or "عمومی"), m(price), m(c["money"]), m(mx), note),
        lambda q: shop_buy(uid, scope, key, lab, q), [["1", "5", "10"], ["25", "50", "100"], ["حداکثر"]])


def shop_locked(uid, scope, key, lab):
    u = U[key]
    orgs = "، ".join(cname(C(i)) for i in u["org"] if C(i))
    rows = [[LK_REQ]]
    if DB["settings"].get("black_on", True) and u["cat"] != "nuke":
        rows.append([LK_BLACK])
    if u["cat"] == "nuke":
        return back_to(uid, "☢️ «%s» فقط برای کشورهای هسته‌ای قابل خریده و مجوز‌پذیر نیست." % u["name"], SHOP_HUB)

    def h(t):
        s = squash(t)
        if s == squash(LK_REQ):
            return lic_request_unit(uid, key)
        if s == squash(LK_BLACK):
            return shop_unit(uid, {"mode": "black", "org": scope.get("org")}, key, lab)
        shop_cat(uid, scope, lab)

    ask(uid, "🔐 «%s» ساخت %s هست و تو مجوز خریدش رو نداری.\n\nیا از سازنده «مجوز» بگیر (دائمی / در ازای پول / عددی)، "
             "یا با ریسک از بازار سیاه بخر." % (u["name"], orgs), h, rows)


def shop_buy(uid, scope, key, lab, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    u = U[key]
    black = scope["mode"] == "black"
    acc = {"how": "black", "cap": None} if black else unit_access(c, key)
    if not black and acc["how"] == "none":
        return shop_locked(uid, scope, key, lab)
    price = ucost(c, u) * (DB["settings"].get("black_mult", 2.2) if black else 1.0)
    mx = int(c["money"] // price)
    if acc["how"] == "lic" and acc["cap"] is not None:
        mx = min(mx, acc["cap"])
    n = mx if squash(t) in ("حداکثر", "max") else (int(num(t)) if num(t) and num(t) > 0 else 0)
    cost = n * price
    if n <= 0 or cost > c["money"] + 1e-9:
        tell(uid, "❌ مقدار نامعتبر یا پول کافی نیست.")
        return shop_cat(uid, scope, lab)
    if acc["how"] == "lic" and acc["cap"] is not None and n > acc["cap"]:
        tell(uid, "❌ مجوزت فقط تا %s عدد اعتبار داره." % m(acc["cap"]))
        return shop_cat(uid, scope, lab)
    if u["cat"] == "nuke" and nuke_count(c) + n > nuke_cap(c):
        tell(uid, "☢️ سقف نگهداری کلاهک هسته‌ای %d عدده." % nuke_cap(c))
        return shop_cat(uid, scope, lab)
    src = lic_consume(c, key, n) if acc["how"] == "lic" else None
    c["money"] -= cost
    c["units"][key] = c["units"].get(key, 0) + n
    tell(uid, "✅ %s× %s خریداری شد.\n💸 هزینه: %s M$ | 💰 مانده: %s M$" % (m(n), u["name"], m(cost), m(c["money"])))
    if src and C(src):
        roy = cost * DB["settings"].get("export_pct", 0.10)
        C(src)["money"] += roy
        notify_country(src, "💰 درآمد صادرات: %s %s× %s خرید (+%s M$)" % (cname(c), m(n), u["name"], m(roy)))
    if black and random.random() < 0.20:
        c["stab"] = max(0.0, c["stab"] - 12)
        announce("🕶 رسوایی تسلیحاتی!\n%s خرید غیرقانونی %s× %s از بازار سیاه رو لو داد.\n🚨 افت ثبات داخلی!\n#بازار_سیاه"
                 % (cname(c), m(n), u["name"]), cat="black", iso=c["iso"])
        for i in u["org"]:
            notify_country(i, "🕶 %s تجهیز ساخت تو (%s) رو غیرقانونی از بازار سیاه خرید!" % (cname(c), u["name"]))
        tell(uid, "🚨 خریدت لو رفت! ثباتت ۱۲٪ افت کرد.")
    xp_add(c, max(1, int(cost // 500)))
    quest_add(c, "buy", n)
    if cost >= 3000 and u["cat"] != "nuke":
        announce("🛒 خرید تسلیحاتی بزرگ\n%s تعداد %s× %s خرید!\n#تسلیحات" % (cname(c), m(n), u["name"]),
                 cat="arms", sub=u["cat"], iso=c["iso"])
    shop_cat(uid, scope, lab)


def deal_ok(src, dst, key):
    """در معامله: گیرنده باید حق خرید داشته باشه، مگه اینکه فروشنده خودش سازنده باشه."""
    if not DB["settings"].get("lic_on", True) or U[key]["cat"] == "nuke":
        return True
    u = U[key]
    if src["iso"] in u["org"]:
        return True
    return unit_access(dst, key)["how"] != "none"


# ═════════════ مجوزهای تسلیحاتی ═════════════
@route(SH_LIC)
def r_lic(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    back_to(uid, ("🎫 مجوزهای تسلیحاتی\n\n"
                  "برای خرید تجهیزات ساخت کشورهای دیگه باید از «کشور سازنده» مجوز بگیری:\n"
                  "🔓 دائمی — بدون محدودیت تعداد و زمان\n"
                  "💰 در ازای پول — مجوز زمان‌دار؛ قیمتش رو می‌دی و تا پایان مدت هر تعداد می‌خری\n"
                  "🔢 عددی — فقط برای تعداد مشخص (مثلاً ۱۰۰ عدد)\n\n"
                  "سازنده می‌تونه مجوز رو برای یک تجهیز، یک دسته یا همه‌ی تجهیزاتش بده. "
                  "🎫 مجوزهای فعال تو: %d | صادرشده توسط تو: %d")
            % (len(my_licenses(c["iso"])), sum(1 for l in DB["licenses"] if l["from"] == c["iso"] and lic_valid(l))),
            LIC_ROWS)


@route(LC_MY)
def r_lic_my(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ls = my_licenses(c["iso"])
    back_to(uid, "📜 مجوزهای من\n\n" + ("\n\n".join(lic_text(l) for l in ls) if ls else "هنوز مجوزی نداری.\nاز «%s» درخواست بده." % LC_REQ), LIC_ROWS)


@route(LC_GR)
def r_lic_gr(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ls = [l for l in DB["licenses"] if l["from"] == c["iso"] and lic_valid(l)][-8:]
    rows = [["🚫 لغو مجوز %d" % l["id"]] for l in ls if not l.get("price")]
    back_to(uid, "📤 مجوزهای صادرشده توسط من\n\n" + ("\n\n".join(lic_text(l) for l in ls) if ls else "مجوزی صادر نکردی.")
            + ("\n\n(فقط مجوزهای رایگان قابل لغو هستن)" if rows else ""), rows + LIC_ROWS)


@rx_route(r"^\W*لغو\s*مجوز\s*(\d+)\s*$")
def rx_lic_revoke(uid, mt):
    l = next((x for x in DB["licenses"] if x["id"] == int(mt.group(1))), None)
    c = mine(uid)
    if not l or not (is_admin(uid) or (c and c["iso"] == l["from"])):
        return menu(uid, "❓ مجوز پیدا نشد یا مال تو نیست.")
    if l.get("price") and not is_admin(uid):
        return menu(uid, "❌ مجوز پولی قابل لغو نیست؛ تا پایان اعتبارش می‌مونه.")
    DB["licenses"].remove(l)
    notify_country(l["to"], "🚫 مجوز #%d (%s) لغو شد." % (l["id"], scope_text(l["scope"])))
    menu(uid, "🚫 مجوز لغو شد.")


def lic_ask_terms(uid, hint, cb):
    """نوع مجوز + پارامترها + قیمت؛ cb(terms)."""
    def price_step(terms):
        std = lic_std_price(hint, terms["kind"], terms.get("qty", 0), terms.get("hours", 0)) if hint else None
        rows = [["0", "100", "500"], ["1000", "5000", "20000"]]
        if std:
            rows.insert(0, [str(int(std))])
        ask(uid, "💵 قیمت مجوز (M$) رو بنویس یا دکمه بزن%s\n(۰ = رایگان؛ برای «در ازای پول» باید بیشتر از صفر باشه)"
            % ((" — 🏷 قیمت استاندارد: %s M$" % m(std)) if std else ""), lambda t: price_h(terms, t), rows)

    def price_h(terms, t):
        v = num(t)
        if v is None or v < 0:
            tell(uid, "❌ عدد نامعتبر.")
            return price_step(terms)
        if terms["kind"] == "paid" and v <= 0:
            tell(uid, "❌ مجوز «در ازای پول» باید قیمت داشته باشه.")
            return price_step(terms)
        terms["price"] = float(v)
        cb(terms)

    def hours_h(t):
        v = num(t)
        if not v or v < 1 or v > 24 * 90:
            tell(uid, "❌ بین ۱ تا ۲۱۶۰ ساعت بنویس.")
            return kind_h(LT_PAID)
        price_step({"kind": "paid", "hours": int(v)})

    def qty_h(t):
        v = num(t)
        if not v or v < 1:
            tell(uid, "❌ تعداد نامعتبر.")
            return kind_h(LT_COUNT)
        price_step({"kind": "count", "qty": int(v)})

    def kind_h(t):
        s = squash(t)
        if s == squash(LT_PERM):
            return price_step({"kind": "perm"})
        if s == squash(LT_PAID):
            return ask(uid, "⏱ مجوز چند ساعت اعتبار داشته باشه؟", hours_h, [["24", "72", "168"], ["336", "720"]])
        if s == squash(LT_COUNT):
            return ask(uid, "🔢 مجوز برای چند عدد؟", qty_h, [["10", "50", "100"], ["250", "500", "1000"]])
        lic_ask_terms(uid, hint, cb)

    ask(uid, "🎫 نوع مجوز؟", kind_h, [[LT_PERM], [LT_PAID], [LT_COUNT]])


@route(LC_ISSUE)
def r_lic_issue(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if not [u for u in national_units(c["iso"]) if u["cat"] != "nuke"]:
        return back_to(uid, "🏳️ کشورت صنعت دفاعی بومی نداره؛ چیزی نداری که مجوزش رو بدی.", LIC_ROWS)
    pick_country(uid, "🎫 به کدوم کشور مجوز می‌دی؟", lambda iso: lic_issue_scope(uid, iso),
                 lambda x: x["alive"] and x["owner"] and x["iso"] != c["iso"] and not sanctioned_between(c["iso"], x["iso"]))


def lic_issue_scope(uid, to_iso):
    c = mine(uid)
    own = [u for u in national_units(c["iso"]) if u["cat"] != "nuke"]
    labs = [k for k, cats in SHOP.items() if k != "☢️ هسته‌ای" and any(u["cat"] in cats for u in own)]

    def done(scope, hint=None):
        lic_ask_terms(uid, hint, lambda terms: lic_issue_send(uid, to_iso, scope, terms))

    def h(t):
        s = squash(t)
        if "یکتجهیز" in s:
            return pick_unit(uid, "🎯 مجوز کدوم تجهیز؟", sorted(own, key=lambda u: (u["cat"], u["tech"])),
                             lambda key: done({"t": "unit", "k": key}, key), per=12)
        if "یکدسته" in s:
            return ask(uid, "📂 کدوم دسته؟", lambda x: (done({"t": "cat", "c": next(k for k in labs if squash(k) == squash(x))})
                                                  if any(squash(k) == squash(x) for k in labs) else lic_issue_scope(uid, to_iso)),
                       chunk(labs, 2))
        if "همه" in s:
            return done({"t": "all"})
        lic_issue_scope(uid, to_iso)

    ask(uid, "🎫 مجوز برای چی باشه؟", h, [["🎯 یک تجهیز مشخص"], ["📂 یک دسته"], ["🔰 همه‌ی تجهیزات من"]])


def lic_issue_send(uid, to_iso, scope, terms):
    c, d = mine(uid), C(to_iso)
    if not c or not d or not d["owner"]:
        return back_to(uid, "❌ ممکن نیست.", LIC_ROWS)
    p = {"id": nid(), "type": "lic", "a": c["iso"], "b": to_iso, "scope": scope, "terms": terms, "t": now()}
    DB["props"].append(p)
    send_prop(p, "🎫 %s پیشنهاد صدور مجوز تسلیحاتی داده:\n%s\n%s\n\nمی‌پذیری؟" % (cname(c), scope_text(scope), terms_text(terms)))
    back_to(uid, "🎫 پیشنهاد مجوز برای %s ارسال شد." % cname(d), LIC_ROWS)


@route(LC_REQ)
def r_lic_req(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_country(uid, "📝 از کدوم کشور سازنده مجوز می‌خوای؟", lambda iso: lic_req_unit_pick(uid, iso),
                 lambda x: x["iso"] in ORG_INDEX and x["iso"] != c["iso"])


def lic_req_unit_pick(uid, iso):
    c = mine(uid)
    us = sorted((u for u in national_units(iso) if u["cat"] != "nuke" and c["iso"] not in u["org"]),
                key=lambda u: (u["cat"], u["tech"]))
    if not us:
        return back_to(uid, "😕 این کشور تجهیز قابل مجوزی نداره.", LIC_ROWS)
    pick_unit(uid, "📝 مجوز کدوم تجهیز %s؟" % cname(C(iso)), us, lambda key: lic_request_unit(uid, key, iso), per=12)


def lic_request_unit(uid, key, org=None):
    c = mine(uid)
    if not c:
        return no_country(uid)
    u = U[key]
    orgs = [i for i in u["org"] if C(i) and C(i)["alive"] and not sanctioned_between(i, c["iso"])]
    if not orgs:
        return back_to(uid, "🚫 سازنده‌ی این تجهیز با تو تحریم داره یا وجود نداره.", LIC_ROWS)
    if org is None:
        if len(orgs) > 1:
            return pick_country(uid, "📝 از کدوم سازنده مجوز می‌خوای؟", lambda iso: lic_request_unit(uid, key, iso),
                                lambda x: x["iso"] in orgs)
        org = orgs[0]
    g = C(org)
    scope = {"t": "unit", "k": key}
    if g["owner"] and g["owner"] != uid:
        return lic_ask_terms(uid, key, lambda terms: lic_req_send(uid, org, scope, terms))
    if DB["settings"].get("auto_lic", True):
        return lic_auto_offer(uid, key, org)
    lic_ask_terms(uid, key, lambda terms: lic_req_admin(uid, org, scope, terms))


def lic_req_send(uid, org, scope, terms):
    c, g = mine(uid), C(org)
    p = {"id": nid(), "type": "licreq", "a": c["iso"], "b": org, "scope": scope, "terms": terms, "t": now()}
    DB["props"].append(p)
    send_prop(p, "📝 %s از تو درخواست مجوز تسلیحاتی داره:\n%s\n%s\n\n(با پذیرش، قیمت به خزانه‌ی تو واریز می‌شه) می‌پذیری؟"
              % (cname(c), scope_text(scope), terms_text(terms)))
    back_to(uid, "📝 درخواستت برای %s فرستاده شد؛ منتظر پاسخشون باش." % cname(g), LIC_ROWS)


def lic_req_admin(uid, org, scope, terms):
    c = mine(uid)
    r = {"id": nid(), "type": "license", "uid": uid, "iso": c["iso"], "org": org, "scope": scope, "terms": terms, "t": now()}
    DB["requests"].append(r)
    notify_admins(req_text(r), [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]], [A_PANEL]])
    back_to(uid, "📝 درخواست مجوز برای ادمین ارسال شد ⏳", LIC_ROWS)


STD_OFFERS = [("perm", {}), ("paid", {"hours": 24}), ("paid", {"hours": 72}), ("paid", {"hours": 168}),
              ("count", {"qty": 10}), ("count", {"qty": 50}), ("count", {"qty": 100}), ("count", {"qty": 500})]


def lic_auto_offer(uid, key, org):
    """کشور سازنده رهبر نداره: مجوز استاندارد رو سیستم می‌فروشه."""
    c = mine(uid)
    labs = {}
    for kind, kw in STD_OFFERS:
        price = lic_std_price(key, kind, kw.get("qty", 0), kw.get("hours", 0))
        lab = ("🔓 دائمی — %s M$" % m(price)) if kind == "perm" else \
              ("💰 %d ساعته — %s M$" % (kw["hours"], m(price))) if kind == "paid" else \
              ("🔢 %d عدد — %s M$" % (kw["qty"], m(price)))
        labs[lab] = (kind, kw, price)

    def h(t):
        o = labs.get(t)
        if not o:
            return shop_cat(uid, {"mode": "for", "org": org}, lab_of(U[key]))
        kind, kw, price = o
        if c["money"] < price:
            tell(uid, "❌ پول کافی نداری (%s M$ لازمه)." % m(price))
            return lic_auto_offer(uid, key, org)
        c["money"] -= price
        l = lic_new(org, c["iso"], {"t": "unit", "k": key}, kind, kw.get("qty", 0), kw.get("hours", 0), price)
        announce("🎫 مجوز تسلیحاتی صادر شد\n%s برای %s: %s\n%s\n#مجوز" % (cname(C(org)), cname(c), U[key]["name"], kind_text(l)),
                 cat="license", iso=(org, c["iso"]))
        quest_add(c, "deal")
        tell(uid, "✅ مجوز صادر شد! حالا می‌تونی بخری.")
        shop_unit(uid, {"mode": "for", "org": org}, key, lab_of(U[key]))

    ask(uid, "🏛 %s رهبر نداره؛ مجوز استاندارد از «بازار جهانی» فروخته می‌شه.\n🎖 %s\n💰 موجودی: %s M$\n\nیکی رو انتخاب کن:"
        % (cname(C(org)), U[key]["name"], m(c["money"])), h, chunk(list(labs), 2))


def lic_grant_accept(a, c, p):
    """پذیرش پیشنهاد/درخواست مجوز: a فرستنده، c پذیرنده. خروجی (ok، متن)."""
    grantor, grantee = (a, c) if p["type"] == "lic" else (c, a)
    t = p["terms"]
    price = float(t.get("price", 0))
    if grantee["money"] < price:
        return False, "❌ %s پول کافی برای قیمت مجوز (%s M$) نداره." % (cname(grantee), m(price))
    grantee["money"] -= price
    grantor["money"] += price
    l = lic_new(grantor["iso"], grantee["iso"], p["scope"], t["kind"], t.get("qty", 0), t.get("hours", 0), price)
    announce("🎫 مجوز تسلیحاتی صادر شد\nاز %s برای %s\n%s\n%s\n#مجوز" % (cname(grantor), cname(grantee), scope_text(l["scope"]),
                                                              kind_text(l)), cat="license", iso=(grantor["iso"], grantee["iso"]))
    quest_add(a, "deal")
    quest_add(c, "deal")
    return True, "✅ مجوز صادر شد."


# ═════════════ پک‌های ویژه ═════════════
def pack_card(pk, c=None):
    L = ["📦 " + pk["name"], "━━━━━━━━━━━━━━━━━", "", "💰 قیمت: %s تومان" % m(pk["price"])]
    if pk.get("limit"):
        L.append("🛒تعداد سفارش: %d/%d" % (pk["limit"], c["packs"].get(pk["key"], 0) if c else 0))
    L += ["", "📋 محتویات پک:"]
    if pk.get("note"):
        L += [pk["note"], ""]
    L += ["   • %s × %s" % (lab, m(amt)) for lab, _k, _key, amt in pk["items"]]
    L += ["", "👇 اگه مطمئنی، درخواست خرید بفرست:"]
    return "\n".join(L)


def activate_pack(iso, key, silent=False):
    c, pk = C(iso), PK[key]
    for _lab, kind, k, amt in pk["items"]:
        if kind == "u":
            c["units"][k] = c["units"].get(k, 0) + amt
        elif kind == "r":
            c["res"][k] = c["res"].get(k, 0.0) + amt
        elif kind == "p":
            c["pop"] += amt
    if pk.get("vip"):
        c["vip"] = True
    c["packs"][key] = c["packs"].get(key, 0) + 1
    DB["pack_log"].append({"t": now(), "iso": iso, "pack": key})
    del DB["pack_log"][:-200]
    notify_country(iso, "🛍 پک «%s» برای کشورت فعال شد! محتویات به خزانه و ارتشت اضافه شد. 🎉" % pk["name"])
    if not silent:
        announce("🛍️ خرید پک ویژه!\n━━━━━━━━━━━━━━━━━\n\n🌍 کشور %s پک «%s» را خریداری کرد!\n\n"
                 "💎 این پک شامل تجهیزات ارزشمندی است که قدرت این کشور را افزایش می‌دهد!\n\n#پک_ویژه" % (cname(c), pk["name"]),
                 cat="pack", sub=key, iso=iso)


@route(B_PACKS)
def r_packs(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ask(uid, "🛍 پک‌های ویژه\nیکی رو انتخاب کن تا جزئیاتش رو ببینی 👇\n(پرداخت به تومانه؛ بعد از ارسال درخواست، ادمین پک رو برات فعال می‌کنه)",
        lambda t: pack_pick(uid, t), [[p["name"]] for p in PACKS])


def pack_pick(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pk = pack_of(t)
    if not pk:
        return r_packs(uid)
    ask(uid, pack_card(pk, c), lambda x: pack_req(uid, pk["key"], x), [["🛒 ارسال درخواست خرید"]])


def pack_req(uid, key, t):
    c, pk = mine(uid), PK[key]
    if not c:
        return no_country(uid)
    if "درخواست" not in t:
        return r_packs(uid)
    if pk.get("limit") and c["packs"].get(key, 0) >= pk["limit"]:
        return back_to(uid, "✅ این پک قبلاً برای کشورت فعال شده و فقط یک بار قابل خریده.", main_rows(uid))
    if any(r["type"] == "pack" and r["uid"] == uid and r["pack"] == key for r in DB["requests"]):
        return menu(uid, "⏳ درخواست قبلیِ همین پک هنوز در انتظار ادمینه.")
    r = {"id": nid(), "type": "pack", "uid": uid, "iso": c["iso"], "pack": key, "t": now()}
    DB["requests"].append(r)
    notify_admins(req_text(r), [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]], [A_PANEL]])
    menu(uid, "✅ درخواست خرید «%s» ثبت شد.\nادمین برای پرداخت و فعال‌سازی باهات هماهنگ می‌کنه ⏳" % pk["name"])



# ───── اقتصاد ─────
# ═════════════ اقتصاد پیشرفته ═════════════
@route(B_ECO)
def r_eco(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ct = cost_tech(c)
    ip = income_parts(c)
    back_to(uid, ("💰 اقتصاد %s\n\n💵 خزانه: %s M$\n📈 درآمد کل: +%s M$ در ساعت\n"
                  "   ├ پایه: %s\n   ├ صنایع و معادن: %s\n   ├ ساخت‌وساز: %s\n   └ مالیات جمعیت: %s\n\n"
                  "👥 جمعیت: %s | 🧾 مالیات: %s | 🏛 حکومت: %s\n"
                  "🏭 اقتصاد %d/10 — ارتقا: %s\n🔬 تکنولوژی %d/6 — ارتقا: %s\n🧱 استحکامات %d/10 — ارتقا: %s")
            % (cname(c), m(c["money"]), m(income(c)), m(ip["core"]), m(ip["fac"]), m(ip["bld"]), m(ip["tax"]),
               m(c["pop"]), TAX_LEVELS[c["tax"]][0], GOVS[c["gov"]][0] if c.get("gov") else "—",
               c["eco"], (m(cost_eco(c)) + " M$") if c["eco"] < 10 else "حداکثر",
               c["tech"], (m(ct) + " M$") if ct else "حداکثر",
               c["fort"], (m(cost_fort(c)) + " M$") if c["fort"] < 10 else "حداکثر"), ECO_ROWS)


@route(B_FACT)
def r_fact(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["🏭 صنایع و معادن %s" % cname(c), "💰 %s M$ | 🔬 تکنولوژی %d" % (m(c["money"]), c["tech"]), ""]
    rows = []
    for f in FD.values():
        lv, mx = fac_lvl(c, f["key"]), fac_max(c, f["key"])
        st = ("🔒 تکنولوژی %d" % f["tech"]) if c["tech"] < f["tech"] else \
             ("✅ حداکثر" if lv >= mx else "⬆️ %s M$" % m(fac_cost(c, f["key"])))
        prod = []
        if f["money"]:
            prod.append("💵 %s/h" % m(f["money"] * lv))
        if f["res"]:
            prod.append("%s %s/h" % (RES[f["res"][0]][0], m(f["res"][1] * lv * (1.5 if (c["vip"] and f["mine"]) else 1))))
        L.append("%s [%d/%d] %s\n    %s%s" % (f["name"], lv, mx, st, " | ".join(prod) + "\n    " if prod else "", f["desc"]))
        rows.append([f["name"]])
    ask(uid, "\n".join(L) + "\n\n👇 برای ارتقا یکی رو انتخاب کن", lambda t: fac_up(uid, t), rows)


def fac_up(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    f = next((x for x in FD.values() if squash(x["name"]) == squash(t)), None)
    if not f:
        return r_fact(uid)
    k = f["key"]
    if c["tech"] < f["tech"]:
        tell(uid, "🔒 «%s» تکنولوژی %d می‌خواد." % (f["name"], f["tech"]))
    elif fac_lvl(c, k) >= fac_max(c, k):
        tell(uid, "✅ این بخش در بالاترین سطحه.")
    elif fac_cost(c, k) > c["money"]:
        tell(uid, "❌ پول کافی نداری (%s M$ لازمه)." % m(fac_cost(c, k)))
    else:
        c["money"] -= fac_cost(c, k)
        c["fac"][k] = fac_lvl(c, k) + 1
        xp_add(c, 5)
        quest_add(c, "fac")
        tell(uid, "✅ %s به سطح %d رسید!" % (f["name"], c["fac"][k]))
        if now() - c.get("ann_b", 0) > 20:
            c["ann_b"] = now()
            announce("🏭 توسعه‌ی صنعتی\n%s «%s» رو به سطح %d رسوند!\n#ساخت_و_ساز" % (cname(c), f["name"], c["fac"][k]),
                     cat="build", sub="fac:" + k, iso=c["iso"])
    r_fact(uid)


@route(B_RES)
def r_res(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["📦 منابع %s" % cname(c), "", "👥 جمعیت: %s (سقف رشد: %s)" % (m(c["pop"]), m(pop_cap(c))), ""]
    for k, (e, n) in RES.items():
        L.append("%s %s: %s  (≈ %s M$)" % (e, n, m(c["res"][k]), m(c["res"][k] / 1000.0 * res_price(k))))
    cv = crypto_value(c)
    L.append("")
    L.append("₿ کریپتو: ≈ %s M$" % m(cv))
    b = c["bank"]
    L.append("🏦 سپرده‌ها: %s M$ | وام: %s M$" % (m(sum(d["amt"] for d in b["deps"])), m(b["loan"])))
    L.append("🏙 شهرها: %d | 🏭 صنایع: %d سطح | 🎖 رتبه: %s" % (len(c["cities"]), sum(c["fac"].values()), RANKS[rank_idx(c)]))
    if c["vip"]:
        L.append("💎 اشتراک VIP فعاله")
    wd = wonders_of(c)
    if wd:
        L.append("🏛 شگفتی‌ها: " + "، ".join(WD[k]["name"] for k in wd))
    back_to(uid, "\n".join(L), ECO_ROWS)


@route(B_MARKET)
def r_market(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["🛢 بازار منابع جهانی (قیمت هر ۱۰۰۰ واحد)", ""]
    for k, (e, n) in RES.items():
        pr = res_price(k)
        ar = "🔺" if pr > RES_PRICE[k] * 1.02 else ("🔻" if pr < RES_PRICE[k] * 0.98 else "▫️")
        L.append("%s %s: %s M$ %s | داری: %s" % (e, n, fp(pr), ar, m(c["res"][k])))
    L.append("\n💰 موجودی: %s M$ | کارمزد ۳٪" % m(c["money"]))
    ask(uid, "\n".join(L), lambda t: mkt_side(uid, t), [["📤 فروش منابع", "📥 خرید منابع"]])


def mkt_side(uid, t):
    sell = "فروش" in t
    if not sell and "خرید" not in t:
        return r_market(uid)
    ask(uid, "کدوم منبع؟", lambda x: mkt_res(uid, sell, x), chunk(["%s %s" % (e, n) for e, n in RES.values()], 2))


def mkt_res(uid, sell, t):
    k = next((k for k, (e, n) in RES.items() if squash("%s %s" % (e, n)) == squash(t) or squash(n) == squash(t)), None)
    if not k:
        return r_market(uid)
    if sell:
        ask(uid, "چقدر بفروشی؟ (درصد یا عدد واحد)", lambda x: mkt_do(uid, True, k, x), [["25%", "50%", "100%"]])
    else:
        ask(uid, "چند M$ خرج خرید کنی؟", lambda x: mkt_do(uid, False, k, x),
            [["100", "500", "1000"], ["5000", "10000", "همه"]])


def mkt_do(uid, sell, k, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    raw = en_digits(t).strip()
    pr = res_price(k) / 1000.0
    if sell:
        have = c["res"][k]
        if raw.endswith("%"):
            v = num(raw[:-1])
            q = have * min(100.0, v) / 100.0 if v else 0
        else:
            q = num(raw) or 0
        q = min(q, have)
        if q <= 0:
            tell(uid, "❌ مقدار نامعتبر.")
            return r_market(uid)
        gain = q * pr * 0.97
        c["res"][k] -= q
        c["money"] += gain
        tell(uid, "✅ %s %s فروخته شد؛ +%s M$" % (m(q), RES[k][1], m(gain)))
    else:
        spend = c["money"] if squash(raw) == "همه" else (num(raw) or 0)
        spend = min(spend, c["money"])
        if spend <= 0:
            tell(uid, "❌ مبلغ نامعتبر.")
            return r_market(uid)
        q = spend / (pr * 1.03)
        c["money"] -= spend
        c["res"][k] += q
        tell(uid, "✅ %s %s خریده شد؛ −%s M$" % (m(q), RES[k][1], m(spend)))
    quest_add(c, "market")
    r_market(uid)


@route(B_SALARY)
def r_salary(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if c["daily"] > now():
        return back_to(uid, "⏱ حقوق روزانه‌ات رو گرفتی؛ %s دیگه دوباره آماده می‌شه." % dur(c["daily"] - now()), ECO_ROWS)
    amt = income(c) * 12
    c["money"] += amt
    c["daily"] = now() + 86400
    xp_add(c, 10)
    back_to(uid, "🎁 حقوق روزانه (معادل ۱۲ ساعت درآمد) دریافت شد: +%s M$ 💰" % m(amt), ECO_ROWS)


# ───── سیاست‌های داخلی ─────
@route(B_POLICY)
def r_policy(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    g = GOVS.get(c.get("gov") or "")
    back_to(uid, "💼 سیاست‌های داخلی %s\n\n🧾 نرخ مالیات: %s\n🏛 حکومت: %s%s\n👥 جمعیت: %s\n😐 ثبات: %d٪" % (
        cname(c), TAX_LEVELS[c["tax"]][0], g[0] if g else "—", (" — " + g[6]) if g else "", m(c["pop"]), int(c["stab"])), POLICY_ROWS)


@route(PO_TAX)
def r_tax(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["🧾 نرخ مالیات (الان: %s)\n" % TAX_LEVELS[c["tax"]][0]]
    for n, (lab, mul, st) in enumerate(TAX_LEVELS):
        L.append("%s — درآمد ×%s | ثبات %+d در ساعت" % (lab, mul, st))
    ask(uid, "\n".join(L), lambda t: tax_do(uid, t), chunk([x[0] for x in TAX_LEVELS], 2))


def tax_do(uid, t):
    c = mine(uid)
    i = next((n for n, x in enumerate(TAX_LEVELS) if squash(x[0]) == squash(t)), None)
    if c and i is not None:
        c["tax"] = i
        tell(uid, "✅ نرخ مالیات: " + TAX_LEVELS[i][0])
    r_policy(uid)


@route(PO_GOV)
def r_gov(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["🏛 نوع حکومت (تغییر: %s M$، ثبات −۱۰، هر ۴۸ ساعت یک‌بار)\n" % m(GOV_COST)]
    L += ["%s — %s" % (g[0], g[6]) for g in GOVS.values()]
    ask(uid, "\n".join(L), lambda t: gov_do(uid, t), chunk([g[0] for g in GOVS.values()], 2))


def gov_do(uid, t):
    c = mine(uid)
    k = next((k for k, g in GOVS.items() if squash(g[0]) == squash(t)), None)
    if not c or not k:
        return r_policy(uid)
    if c["gov"] == k:
        tell(uid, "این حکومت همین الان برقراره.")
    elif c["gov_t"] > now():
        tell(uid, "⏱ تا %s دیگه نمی‌تونی حکومت رو عوض کنی." % dur(c["gov_t"] - now()))
    elif c["money"] < GOV_COST:
        tell(uid, "❌ %s M$ لازمه." % m(GOV_COST))
    else:
        c["money"] -= GOV_COST
        c["gov"], c["gov_t"] = k, now() + 48 * 3600
        c["stab"] = max(0.0, c["stab"] - 10)
        tell(uid, "✅ حکومت %s برقرار شد." % GOVS[k][0])
        announce("🏛 تغییر نظام سیاسی\n%s نظام حکومتی‌اش را به «%s» تغییر داد.\n#رویداد" % (cname(c), GOVS[k][0]),
                 cat="event", iso=c["iso"])
    r_policy(uid)


@route(PO_DRAFT)
def r_draft(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if c["draft_t"] > now():
        return back_to(uid, "⏱ سربازگیری بعدی %s دیگه." % dur(c["draft_t"] - now()), POLICY_ROWS)
    ask(uid, "🪖 سربازگیری عمومی: بخشی از جمعیت (%s) به «سرباز» تبدیل می‌شه ولی ثبات افت می‌کنه (هر ۶ ساعت)." % m(c["pop"]),
        lambda t: draft_do(uid, t), [["0.25%", "0.5%", "1%", "2%"]])


def draft_do(uid, t):
    c = mine(uid)
    v = num(en_digits(t).replace("%", ""))
    if not c or not v or v <= 0 or v > 2:
        tell(uid, "❌ بین ۰.۲۵ تا ۲ درصد.")
        return r_policy(uid)
    n = int(c["pop"] * v / 100.0)
    c["pop"] -= n
    c["units"]["soldier"] = c["units"].get("soldier", 0) + n
    c["stab"] = max(0.0, c["stab"] - 4 * v)
    c["draft_t"] = now() + 6 * 3600
    tell(uid, "✅ %s سرباز جذب ارتش شد. ثباتت %d٪ افت کرد." % (m(n), int(4 * v)))
    r_policy(uid)


@route(PO_PROPA)
def r_propa(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    cost = max(100.0, income(c) * 3)
    if c["propa_t"] > now():
        return back_to(uid, "⏱ تبلیغات بعدی %s دیگه." % dur(c["propa_t"] - now()), POLICY_ROWS)
    if c["money"] < cost:
        return back_to(uid, "❌ %s M$ لازمه." % m(cost), POLICY_ROWS)
    c["money"] -= cost
    c["stab"] = min(100.0, c["stab"] + 15)
    sat_bump(c, 8)
    c["propa_t"] = now() + 6 * 3600
    back_to(uid, "📣 کمپین تبلیغات ملی اجرا شد: ثبات +۱۵٪ (هزینه %s M$)." % m(cost), POLICY_ROWS)


# ───── ماموریت‌های روزانه ─────
def quest_roll(c):
    qd = c["quest"]
    day = int(now() // 86400)
    if qd.get("day") != day or not qd.get("q"):
        rnd = random.Random(day * 131 + sum(map(ord, c["iso"])))
        picks = rnd.sample(QUESTS, 3)
        reward = max(300.0, income(c) * 2)
        qd["day"], qd["bonus"] = day, False
        qd["q"] = [{"k": k, "n": rnd.randint(*rg), "p": 0, "done": False, "r": reward} for k, _t, rg in picks]


def quest_add(c, kind, n=1):
    try:
        quest_roll(c)
        qd = c["quest"]
        for q in qd["q"]:
            if q["k"] == kind and not q["done"]:
                q["p"] += n
                if q["p"] >= q["n"]:
                    q["done"] = True
                    c["money"] += q["r"]
                    xp_add(c, 15)
                    notify_country(c["iso"], "🎯 ماموریت انجام شد! جایزه: +%s M$" % m(q["r"]))
        if all(q["done"] for q in qd["q"]) and not qd["bonus"]:
            qd["bonus"] = True
            c["money"] += income(c) * 6
            xp_add(c, 60)
            notify_country(c["iso"], "🏆 هر سه ماموریت امروز رو تموم کردی! پاداش ویژه: +%s M$" % m(income(c) * 6))
    except Exception as e:  # noqa: BLE001
        print("quest error:", e)


def r_quest(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    quest_roll(c)
    qd = c["quest"]
    txt = {k: t for k, t, _r in QUESTS}
    L = ["🎯 ماموریت‌های امروز %s" % cname(c), "🎖 رتبه: %s | XP: %d" % (RANKS[rank_idx(c)], c["xp"]), ""]
    for q in qd["q"]:
        L.append("%s %s — %d/%d (جایزه %s M$)" % ("✅" if q["done"] else "⬜", txt[q["k"]].format(n=q["n"]),
                                                  min(q["p"], q["n"]), q["n"], m(q["r"])))
    L.append("\n🏆 پاداش انجام هر سه: ۶ ساعت درآمد + XP")
    back_to(uid, "\n".join(L), main_rows(uid))


# ───── رتبه‌بندی چندگانه ─────
@route(B_RANK)
def r_rank(uid):
    ask(uid, "🏆 رتبه‌بندی بر اساس چی؟", lambda t: rank_show(uid, t),
        [["💪 قدرت نظامی", "💰 ثروت"], ["🗺 قلمرو", "₿ ثروت کریپتو"], ["🛡 اتحادها", "🎖 فرماندهان"]])


def rank_show(uid, t):
    s = squash(t)
    cs = [c for c in DB["countries"].values() if c["alive"]]
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    L = []
    if "اتحاد" in s:
        us = sorted(DB["unions"].values(), key=un_power, reverse=True)[:10]
        L = ["🛡 برترین اتحادها", ""] + (["%s %s — 💪 %s | 👥 %d | ⭐ سطح %d" % (
            medals[i], un_label(u), m(un_power(u)), len(un_members(u)), u["lvl"]) for i, u in enumerate(us)] or ["هنوز اتحادی نیست."])
    else:
        if "کریپتو" in s:
            key, title, fmt = crypto_value, "₿ پولدارترین کریپتویی‌ها", lambda c: "₿ %s M$" % m(crypto_value(c))
        elif "ثروت" in s:
            key, title, fmt = (lambda c: c["money"] + crypto_value(c)), "💰 ثروتمندترین کشورها", lambda c: "💰 %s M$" % m(c["money"] + crypto_value(c))
        elif "قلمرو" in s:
            key, title, fmt = (lambda c: c["prov"]), "🗺 بزرگ‌ترین قلمروها", lambda c: "🗺 %d استان" % c["prov"]
        elif "فرمانده" in s:
            key, title, fmt = (lambda c: c.get("xp", 0)), "🎖 برترین فرماندهان", lambda c: "%s | XP %d" % (RANKS[rank_idx(c)], c.get("xp", 0))
        else:
            key, title, fmt = score, "💪 قدرتمندترین کشورها", lambda c: "💪 %s | 🗺 %d" % (m(power(c)), c["prov"])
        L = [title, ""]
        for i, c in enumerate(sorted(cs, key=key, reverse=True)[:10]):
            who = ("👤 " + c["leader"]) if c["owner"] else "🤖 بدون رهبر"
            L.append("%s %s — %s | %s" % (medals[i], cname(c), fmt(c), who))
    back_to(uid, "\n".join(L), main_rows(uid))


# ───── بیانیه با عکس ─────
ST_SAVED, ST_DEF, ST_NEW = "🖼 با عکس ذخیره‌شده", "📝 با عکس پیش‌فرض گزارش‌ها", "📷 ارسال عکس جدید برای این بیانیه"


@route(B_STMT)
def r_stmt(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    back_to(uid, "📜 بیانیه رسمی\n🖼 عکس ثابت بیانیه: %s\n\n«ارسال بیانیه» رو بزن؛ می‌تونی متن بنویسی یا مستقیم یک عکس همراه کپشن بفرستی."
            % ("✅ تنظیم شده" if c.get("stmt_photo") else "— (عکس پیش‌فرض گزارش‌ها)"),
            [[B_SENDSTMT, B_SENDMIL], [B_SETPHOTO, B_DELPHOTO], [B_BACK]])


@route(B_SENDSTMT)
def r_sendstmt(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if c["stmt"] > now():
        return menu(uid, "⏱ برای بیانیه‌ی بعدی %s صبر کن." % dur(c["stmt"] - now()))

    def with_photo(fid, cap):
        if cap.strip():
            return stmt_go(uid, cap, fid)
        ask_text(uid, "✍️ متن بیانیه برای این عکس:", STMT_PRESETS, lambda t: stmt_go(uid, t, fid), "✍️ متن بیانیه:")

    STMT_KIND[uid] = "off"
    ask_text(uid, "📜 بیانیه‌ات رو انتخاب کن (توی کانال منتشر می‌شه) — یا یک عکس همراه کپشن بفرست:", STMT_PRESETS,
             lambda t: stmt_text(uid, t), "✍️ متن بیانیه‌ات رو بنویس (حداکثر ۶۰۰ حرف):")
    PHOTO[uid] = with_photo


def stmt_text(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    t = t.strip()
    if not t or len(t) > 600:
        return menu(uid, "❌ متن خالیه یا بیشتر از ۶۰۰ حرفه.")
    if not c.get("stmt_photo"):
        return stmt_go(uid, t, None)
    ask(uid, "🖼 بیانیه با کدوم عکس منتشر بشه؟", lambda x: stmt_choice(uid, t, x), [[ST_SAVED], [ST_DEF], [ST_NEW]])


def stmt_choice(uid, t, x):
    c = mine(uid)
    s = squash(x)
    if s == squash(ST_SAVED):
        return stmt_go(uid, t, c.get("stmt_photo"))
    if s == squash(ST_NEW):
        return ask_photo(uid, "📷 عکس بیانیه رو بفرست:", lambda fid, cap: stmt_go(uid, t, fid), on_text=lambda tx: stmt_go(uid, t, None))
    stmt_go(uid, t, None)


def stmt_go(uid, t, fid=None):
    c = mine(uid)
    if not c:
        return no_country(uid)
    t = t.strip()
    if not t or len(t) > 600:
        return menu(uid, "❌ متن خالیه یا بیشتر از ۶۰۰ حرفه.")
    if c["stmt"] > now():
        return menu(uid, "⏱ برای بیانیه‌ی بعدی %s صبر کن." % dur(c["stmt"] - now()))
    c["stmt"] = now() + STATEMENT_COOLDOWN
    kind = STMT_KIND.pop(uid, "off")
    announce(statement_text(c, t, kind), cat=("milstmt" if kind == "mil" else "statement"), iso=c["iso"], photo=fid)
    xp_add(c, 3)
    menu(uid, "✅ بیانیه‌ات منتشر شد%s." % (" (با عکس)" if fid else ""))


@route(B_SETPHOTO)
def r_setphoto(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)

    def save(fid, cap):
        c["stmt_photo"] = fid
        back_to(uid, "✅ عکس بیانیه ذخیره شد؛ از این به بعد می‌تونی بیانیه‌ها رو باهاش منتشر کنی.", [[B_SENDSTMT], [B_BACK]])

    ask_photo(uid, "🖼 عکس بیانیه‌ات رو بفرست (به‌صورت Photo). این عکس برای بیانیه‌های بعدی ذخیره می‌شه.", save)


@route(B_DELPHOTO)
def r_delphoto(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    c["stmt_photo"] = None
    back_to(uid, "🗑 عکس بیانیه حذف شد.", [[B_SENDSTMT], [B_BACK]])


# ═════════════ ساخت‌وساز: شهرها، ساختمان‌های درآمدزا، ابرپروژه‌ها ═════════════
def city_slots(city):
    return 8 + 4 * city["lvl"]


def city_used(city):
    return sum(BD[k]["slots"] * n for k, n in city["b"].items() if k in BD)


def max_cities(c):
    return 2 + c["prov"]


def city_label(city):
    return "%s (سطح %d · %d/%d)" % (city["name"], city["lvl"], city_used(city), city_slots(city))


def bcost(c, k):
    return BD[k]["cost"] * bdisc(c)


@route(B_BUILD)
def r_build(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    nb = sum(sum(ct["b"].values()) for ct in c["cities"])
    back_to(uid, ("🏗 ساخت و ساز %s\n\n🏙 شهرها: %d از %d\n🏢 ساختمان‌ها: %d\n📈 درآمد ساخت‌وساز: +%s M$ در ساعت\n"
                  "👥 جمعیت: %s\n\n"
                  "شهر بساز، توش کافه، پارک، موزه، هتل، دانشگاه، فرودگاه و برج تجاری بساز؛ شهرها رو ارتقا بده و جشنواره برگزار کن. "
                  "ابرپروژه‌ها (شگفتی‌های جهان) فقط یک‌بار تو کل بازی ساخته می‌شن!")
            % (cname(c), len(c["cities"]), max_cities(c), nb, m(build_income(c) * stab_f(c)), m(c["pop"])), BUILD_ROWS)


@route(BL_CITIES)
def r_cities(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if not c["cities"]:
        return back_to(uid, "🏙 هنوز شهری نساختی. «%s» رو بزن." % BL_NEW, BUILD_ROWS)
    L = ["🏙 شهرهای %s" % cname(c), ""]
    for ct in c["cities"]:
        bl = "، ".join("%s×%d" % (BD[k]["name"].split(" ", 1)[1], n) for k, n in ct["b"].items() if n and k in BD)
        fest = " 🎉" if ct.get("fest", 0) > now() else ""
        L.append("🏙 %s%s — سطح %d | اسلات %d/%d | 💵 +%s/h\n    %s" % (
            ct["name"], fest, ct["lvl"], city_used(ct), city_slots(ct), m(city_income(c, ct)), bl or "خالی"))
    back_to(uid, "\n".join(L), BUILD_ROWS)


def new_city_cost(c):
    return 400 * (len(c["cities"]) + 1) ** 1.7 * bdisc(c)


@route(BL_NEW)
def r_newcity(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if len(c["cities"]) >= max_cities(c):
        return back_to(uid, "🏙 به سقف شهرها (%d) رسیدی؛ استان بیشتر تصرف کن." % max_cities(c), BUILD_ROWS)
    cost = new_city_cost(c)
    if c["money"] < cost:
        return back_to(uid, "❌ ساخت شهر %s M$ می‌خواد." % m(cost), BUILD_ROWS)
    ask_text(uid, "🏙 اسم شهر جدید؟ (هزینه: %s M$)" % m(cost), CITY_PRESETS, lambda t: newcity_do(uid, t), "✍️ اسم شهر:", per_row=2)


def newcity_do(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    name = re.sub(r"^[^\w]+", "", t.strip())[:24] or "شهر"
    cost = new_city_cost(c)
    if len(c["cities"]) >= max_cities(c) or c["money"] < cost or any(x["name"] == name for x in c["cities"]):
        return back_to(uid, "❌ ممکن نیست (پول کم، سقف شهرها یا اسم تکراری).", BUILD_ROWS)
    c["money"] -= cost
    c["cities"].append({"name": name, "lvl": 1, "b": {}, "fest": 0})
    xp_add(c, 8)
    announce("🏙 شهر جدید\n%s شهر «%s» رو بنا کرد!\n#ساخت_و_ساز" % (cname(c), name), cat="build", sub="tower", iso=c["iso"])
    back_to(uid, "🏙 شهر «%s» ساخته شد! حالا توش ساختمان بساز." % name, BUILD_ROWS)


def pick_city(uid, prompt, cb, flt=None):
    c = mine(uid)
    cs = [ct for ct in c["cities"] if flt is None or flt(ct)]
    if not cs:
        return back_to(uid, "🏙 شهر مناسبی نداری؛ اول «%s» رو بزن." % BL_NEW, BUILD_ROWS)
    labels = {city_label(ct): ct["name"] for ct in cs}

    def h(t):
        nm = labels.get(t)
        ct = next((x for x in c["cities"] if x["name"] == nm), None)
        if not ct:
            return pick_city(uid, prompt, cb, flt)
        cb(ct)

    ask(uid, prompt, h, [[l] for l in labels])


@route(BL_BUILD)
def r_bl_build(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_city(uid, "🏪 توی کدوم شهر بسازی؟", lambda ct: bl_pick(uid, ct["name"]), lambda ct: city_used(ct) < city_slots(ct))


def bl_pick(uid, cname_):
    c = mine(uid)
    ct = next((x for x in c["cities"] if x["name"] == cname_), None)
    if not ct:
        return r_build(uid)
    L = ["🏪 ساخت در %s — اسلات خالی: %d" % (ct["name"], city_slots(ct) - city_used(ct)), "💰 %s M$ | 🔬 تکنولوژی %d" % (m(c["money"]), c["tech"]), ""]
    for b in BD.values():
        L.append("%s%s — 💲%s | 💵 +%s/h | %d اسلات%s" % ("🔒" if c["tech"] < b["tech"] else "", b["name"], m(bcost(c, b["key"])),
                                                       m(b["inc"]), b["slots"], (" | " + b["note"]) if b["note"] else ""))
    ask(uid, "\n".join(L), lambda t: bl_qty(uid, cname_, t), chunk([b["name"] for b in BD.values()], 2))


def bl_qty(uid, cname_, t):
    c = mine(uid)
    b = next((x for x in BD.values() if squash(x["name"]) == squash(t)), None)
    ct = next((x for x in c["cities"] if x["name"] == cname_), None) if c else None
    if not b or not ct:
        return r_build(uid)
    if c["tech"] < b["tech"]:
        tell(uid, "🔒 تکنولوژی %d لازمه." % b["tech"])
        return bl_pick(uid, cname_)
    free = (city_slots(ct) - city_used(ct)) // b["slots"]
    mx = min(free, int(c["money"] // bcost(c, b["key"])))
    ask(uid, "چند تا %s بسازی؟ (حداکثر %d)" % (b["name"], mx), lambda q: bl_do(uid, cname_, b["key"], q),
        [["1", "5", "10"], ["25", "50", "حداکثر"]])


def bl_do(uid, cname_, key, t):
    c = mine(uid)
    ct = next((x for x in c["cities"] if x["name"] == cname_), None) if c else None
    if not ct:
        return r_build(uid)
    b = BD[key]
    free = (city_slots(ct) - city_used(ct)) // b["slots"]
    mx = min(free, int(c["money"] // bcost(c, key)))
    n = mx if squash(t) in ("حداکثر", "max") else (int(num(t)) if num(t) and num(t) > 0 else 0)
    if n <= 0 or n > mx:
        tell(uid, "❌ مقدار نامعتبر (اسلات یا پول کافی نیست).")
        return bl_pick(uid, cname_)
    cost = n * bcost(c, key)
    c["money"] -= cost
    ct["b"][key] = ct["b"].get(key, 0) + n
    xp_add(c, max(1, n // 2))
    quest_add(c, "build", n)
    tell(uid, "✅ %d× %s در %s ساخته شد؛ هزینه %s M$." % (n, b["name"], ct["name"], m(cost)))
    if now() - c.get("ann_b", 0) > 20:
        c["ann_b"] = now()
        announce("🏗 ساخت‌وساز جدید\n%s در شهر %s تعداد %d× %s ساخت!\n📈 درآمد: +%s M$ در ساعت\n#ساخت_و_ساز"
                 % (cname(c), ct["name"], n, b["name"], m(b["inc"] * n * city_mult(ct))), cat="build", sub=key, iso=c["iso"])
    bl_pick(uid, cname_)


@route(BL_UP)
def r_bl_up(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_city(uid, "⬆️ کدوم شهر ارتقا پیدا کنه؟", lambda ct: bl_up_do(uid, ct["name"]), lambda ct: ct["lvl"] < 10)


def bl_up_do(uid, nm):
    c = mine(uid)
    ct = next((x for x in c["cities"] if x["name"] == nm), None)
    cost = 500 * ct["lvl"] ** 1.8 * bdisc(c)
    if c["money"] < cost:
        return back_to(uid, "❌ ارتقای %s به سطح %d: %s M$ لازمه." % (ct["name"], ct["lvl"] + 1, m(cost)), BUILD_ROWS)
    c["money"] -= cost
    ct["lvl"] += 1
    xp_add(c, 10)
    back_to(uid, "⬆️ %s به سطح %d رسید! (اسلات %d، درآمد ساختمان‌ها ×%.2f)" % (ct["name"], ct["lvl"], city_slots(ct), city_mult(ct)), BUILD_ROWS)


@route(BL_FEST)
def r_bl_fest(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_city(uid, "🎉 جشنواره‌ی کدوم شهر؟ (۳ ساعت درآمد ×۱.۵ و ثبات +۳)", lambda ct: bl_fest_do(uid, ct["name"]),
              lambda ct: ct.get("fest", 0) < now())


def bl_fest_do(uid, nm):
    c = mine(uid)
    ct = next((x for x in c["cities"] if x["name"] == nm), None)
    cost = max(50.0, city_income(c, ct) * 6)
    if c["money"] < cost:
        return back_to(uid, "❌ جشنواره %s M$ می‌خواد." % m(cost), BUILD_ROWS)
    c["money"] -= cost
    ct["fest"] = now() + 3 * 3600
    c["stab"] = min(100.0, c["stab"] + 3)
    sat_bump(c, 4)
    announce("🎉 جشنواره‌ی بزرگ\nشهر %s در %s میزبان جشنواره‌ی بین‌المللی شد!\n#ساخت_و_ساز" % (ct["name"], cname(c)), cat="build", sub="theme", iso=c["iso"])
    back_to(uid, "🎉 جشنواره در %s شروع شد! (هزینه %s M$)" % (ct["name"], m(cost)), BUILD_ROWS)


@route(BL_DEMO)
def r_bl_demo(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_city(uid, "💥 تخریب در کدوم شهر؟ (۵۰٪ هزینه برمی‌گرده)", lambda ct: bl_demo_pick(uid, ct["name"]), lambda ct: any(ct["b"].values()))


def bl_demo_pick(uid, nm):
    c = mine(uid)
    ct = next((x for x in c["cities"] if x["name"] == nm), None)
    have = [BD[k]["name"] for k, n in ct["b"].items() if n and k in BD]
    ask(uid, "کدوم ساختمان؟", lambda t: bl_demo_do(uid, nm, t), chunk(have, 2))


def bl_demo_do(uid, nm, t):
    c = mine(uid)
    ct = next((x for x in c["cities"] if x["name"] == nm), None)
    b = next((x for x in BD.values() if squash(x["name"]) == squash(t) and ct["b"].get(x["key"])), None)
    if b:
        ct["b"][b["key"]] -= 1
        c["money"] += b["cost"] * 0.5
        tell(uid, "💥 یک %s تخریب شد؛ +%s M$." % (b["name"], m(b["cost"] * 0.5)))
    r_build(uid)


@route(BL_WONDER)
def r_wonders(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["🏛 ابرپروژه‌ها (هر کدوم فقط برای یک کشور)", "💰 %s M$ | 🔬 تکنولوژی %d" % (m(c["money"]), c["tech"]), ""]
    for w in WD.values():
        own = DB["wonders"].get(w["key"])
        st = ("✅ ساخته‌شده: " + cname(C(own))) if own and C(own) else "🆓 آزاد — %s M$ | تکنولوژی %d" % (m(w["cost"]), w["tech"])
        L.append("%s\n    %s | %s" % (w["name"], w["desc"], st))
    ask(uid, "\n".join(L), lambda t: wonder_build(uid, t), chunk([w["name"] for w in WD.values()], 2))


def wonder_build(uid, t):
    c = mine(uid)
    w = next((x for x in WD.values() if squash(x["name"]) == squash(t)), None)
    if not c or not w:
        return r_build(uid)
    if DB["wonders"].get(w["key"]):
        tell(uid, "😕 این ابرپروژه قبلاً توسط کشور دیگه‌ای ساخته شده.")
    elif c["tech"] < w["tech"]:
        tell(uid, "🔒 تکنولوژی %d لازمه." % w["tech"])
    elif c["money"] < w["cost"]:
        tell(uid, "❌ %s M$ لازمه." % m(w["cost"]))
    else:
        c["money"] -= w["cost"]
        DB["wonders"][w["key"]] = c["iso"]
        xp_add(c, 80)
        announce("🏛 شگفتی جهان ساخته شد!\n%s ابرپروژه‌ی «%s» را تکمیل کرد!\n✨ %s\n#شگفتی" % (cname(c), w["name"], w["desc"]),
                 cat="wonder", sub=w["key"], iso=c["iso"])
        tell(uid, "🏛 «%s» ساخته شد! اثرش: %s" % (w["name"], w["desc"]))
    r_wonders(uid)


# ═════════════ ارز دیجیتال و ماینینگ ═════════════
def coin_change(sym, mins=60):
    h = DB["market"]["coins"][sym]["hist"]
    old = h[-min(len(h), mins)]
    return (h[-1] / old - 1) * 100 if old else 0.0


@route(B_CRYPTO)
def r_crypto(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    b = DB["market"]["coins"]["BTC"]
    back_to(uid, ("₿ ارز دیجیتال\n\n₿ بیت‌کوین: %s M$ (%+.1f٪ در ساعت اخیر)\n%s\n\n"
                  "👛 ارزش کیف پول: %s M$\n⛏ ماینرها: %d دستگاه/مزرعه\n⚡ برق: %s\n\n"
                  "قیمت‌ها زنده تغییر می‌کنن و گاهی جهش یا سقوط بزرگ دارن. ماینرها برق مصرف می‌کنن و بیت‌کوین تولید می‌کنن.")
            % (fp(b["p"]), coin_change("BTC"), spark(b["hist"][-120:][::5]), m(crypto_value(c)),
               sum(c["miners"].values()), m(c["res"]["elec"])), CRYPTO_ROWS)


@route(CR_MARKET)
def r_cr_market(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["📊 بازار ارزهای دیجیتال (قیمت به M$)", ""]
    for sym, d in COINS.items():
        cc = DB["market"]["coins"][sym]
        ch = coin_change(sym)
        L.append("%s %s (%s): %s %s %+.1f٪\n    %s" % (d["sym"], d["name"], sym, fp(cc["p"]), "🟢" if ch >= 0 else "🔴", ch,
                                                      spark(cc["hist"][-120:][::5])))
    back_to(uid, "\n".join(L), CRYPTO_ROWS)


@route(CR_WALLET)
def r_cr_wallet(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["👛 کیف پول %s" % cname(c), ""]
    for sym, d in COINS.items():
        a = c["crypto"].get(sym, 0.0)
        if a > 0:
            L.append("%s %s: %s ≈ %s M$" % (d["sym"], sym, ("%.6f" % a).rstrip("0").rstrip("."), m(a * coin_price(sym))))
    if len(L) == 2:
        L.append("خالیه.")
    L.append("\n💎 مجموع: %s M$" % m(crypto_value(c)))
    back_to(uid, "\n".join(L), CRYPTO_ROWS)


@route(CR_BUY)
def r_cr_buy(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ask(uid, "🛒 کدوم ارز رو بخری؟\n💰 موجودی: %s M$ | کارمزد ٪%.1f" % (m(c["money"]), CRYPTO_FEE * 100),
        lambda t: cr_buy_pick(uid, t), chunk(["%s %s" % (d["sym"], s) for s, d in COINS.items()], 2))


def coin_of(t):
    return next((s for s, d in COINS.items() if s.lower() in t.lower().split() or squash(d["name"]) == squash(t)
                 or squash(t).endswith(s.lower())), None)


def cr_buy_pick(uid, t):
    s = coin_of(t)
    if not s:
        return r_crypto(uid)
    ask(uid, "چند M$ خرج خرید %s کنی؟ (قیمت: %s)" % (s, fp(coin_price(s))), lambda x: cr_buy_do(uid, s, x),
        [["100", "500", "1000"], ["5000", "20000", "همه"]])


def cr_buy_do(uid, s, t):
    c = mine(uid)
    spend = c["money"] if squash(t) == "همه" else (num(t) or 0)
    spend = min(spend, c["money"])
    if spend <= 0:
        tell(uid, "❌ مبلغ نامعتبر.")
        return r_crypto(uid)
    q = spend * (1 - CRYPTO_FEE) / coin_price(s)
    c["money"] -= spend
    c["crypto"][s] = c["crypto"].get(s, 0.0) + q
    quest_add(c, "market")
    tell(uid, "✅ %.6f %s خریده شد (−%s M$)." % (q, s, m(spend)))
    r_crypto(uid)


@route(CR_SELL)
def r_cr_sell(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    have = [s for s in COINS if c["crypto"].get(s, 0) > 0]
    if not have:
        return back_to(uid, "👛 ارزی برای فروش نداری.", CRYPTO_ROWS)
    ask(uid, "💱 کدوم ارز رو بفروشی؟", lambda t: cr_sell_pick(uid, t), chunk(["%s %s" % (COINS[s]["sym"], s) for s in have], 2))


def cr_sell_pick(uid, t):
    s = coin_of(t)
    if not s:
        return r_crypto(uid)
    ask(uid, "چقدر بفروشی؟", lambda x: cr_sell_do(uid, s, x), [["25%", "50%", "100%"]])


def cr_sell_do(uid, s, t):
    c = mine(uid)
    raw = en_digits(t).strip()
    have = c["crypto"].get(s, 0.0)
    v = num(raw.replace("%", ""))
    q = have * min(100.0, v) / 100.0 if (raw.endswith("%") and v) else min(have, v or 0)
    if q <= 0:
        tell(uid, "❌ مقدار نامعتبر.")
        return r_crypto(uid)
    gain = q * coin_price(s) * (1 - CRYPTO_FEE)
    c["crypto"][s] = have - q
    c["money"] += gain
    quest_add(c, "market")
    tell(uid, "✅ %.6f %s فروخته شد (+%s M$)." % (q, s, m(gain)))
    r_crypto(uid)


@route(CR_MINE)
def r_cr_mine(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    need = sum(MD[k]["elec"] * n for k, n in c["miners"].items() if k in MD)
    prod = sum(MD[k]["btc"] * n for k, n in c["miners"].items() if k in MD)
    L = ["⛏ ماینینگ بیت‌کوین", "⚡ برق موجود: %s | مصرف ماینرها: %s در ساعت" % (m(c["res"]["elec"]), m(need)),
         "₿ تولید: %.4f BTC در ساعت (≈ %s M$)" % (prod, m(prod * coin_price("BTC"))), "",
         "اگه برق کم بیاد تولید متناسب کم می‌شه؛ نیروگاه بساز یا برق بخر.", ""]
    for x in MD.values():
        L.append("%s%s [داری: %d]\n    💲%s M$ | ₿ %.4f/h | ⚡ %s/h" % ("🔒" if c["tech"] < x["tech"] else "", x["name"],
                                                                 c["miners"].get(x["key"], 0), m(x["cost"]), x["btc"], m(x["elec"])))
    ask(uid, "\n".join(L), lambda t: cr_mine_pick(uid, t), [[x["name"]] for x in MD.values()])


def cr_mine_pick(uid, t):
    c = mine(uid)
    x = next((y for y in MD.values() if squash(y["name"]) == squash(t)), None)
    if not x:
        return r_crypto(uid)
    if c["tech"] < x["tech"]:
        tell(uid, "🔒 تکنولوژی %d لازمه." % x["tech"])
        return r_cr_mine(uid)
    ask(uid, "چند تا بخری؟ (حداکثر %d)" % int(c["money"] // x["cost"]), lambda q: cr_mine_do(uid, x["key"], q),
        [["1", "5", "10"], ["25", "50", "حداکثر"]])


def cr_mine_do(uid, key, t):
    c = mine(uid)
    x = MD[key]
    mx = int(c["money"] // x["cost"])
    n = mx if squash(t) in ("حداکثر", "max") else (int(num(t)) if num(t) and num(t) > 0 else 0)
    if n <= 0 or n > mx:
        tell(uid, "❌ مقدار نامعتبر یا پول کافی نیست.")
        return r_cr_mine(uid)
    c["money"] -= n * x["cost"]
    c["miners"][key] = c["miners"].get(key, 0) + n
    tell(uid, "✅ %d× %s نصب شد." % (n, x["name"]))
    r_cr_mine(uid)


# ═════════════ بانک ═════════════
def bank_cap(c):
    return max(20000.0, 40 * income(c))


def credit_limit(c):
    return max(500.0, 24 * income(c) * (0.5 + c["stab"] / 200.0))


def dep_total(c):
    return sum(d["amt"] for d in c["bank"]["deps"])


@route(B_BANK)
def r_bank(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    back_to(uid, ("🏦 بانک مرکزی\n\n💰 موجودی: %s M$\n🏧 مجموع سپرده‌ها: %s M$ (سقف %s)\n💳 وام: %s M$ | سقف اعتبار جدید: %s M$\n\n"
                  "🟢 انعطاف‌پذیر: ٪%.2f در ساعت (هر وقت خواستی برداشت)\n🟡 ۲۴ ساعته: ٪%.2f در ساعت\n🔴 ۷۲ ساعته: ٪%.2f در ساعت\n"
                  "برداشت زودتر از موعد %d٪ جریمه داره.\n💳 سود وام: ٪%.2f در ساعت؛ بعد از %d ساعت جریمه و بعد از %d ساعت برداشت اجباری!")
            % (m(c["money"]), m(dep_total(c)), m(bank_cap(c)), m(c["bank"]["loan"]),
               m(max(0.0, credit_limit(c) - c["bank"]["loan"])),
               BANK_KINDS["flex"]["rate"] * 100 * DB["settings"].get("bank_dep_mult", 1.0),
               BANK_KINDS["d1"]["rate"] * 100 * DB["settings"].get("bank_dep_mult", 1.0),
               BANK_KINDS["d3"]["rate"] * 100 * DB["settings"].get("bank_dep_mult", 1.0),
               EARLY_PENALTY * 100, LOAN_RATE * 100 * DB["settings"].get("bank_loan_mult", 1.0), LOAN_GRACE_H, LOAN_FORCE_H),
            BANK_ROWS)


@route(BK_DEP)
def r_bk_dep(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ask(uid, "💰 نوع سپرده؟", lambda t: bk_dep_kind(uid, t), [[v["name"]] for v in BANK_KINDS.values()])


def bk_dep_kind(uid, t):
    k = next((k for k, v in BANK_KINDS.items() if squash(v["name"]) == squash(t)), None)
    if not k:
        return r_bank(uid)
    ask(uid, "چند M$ سپرده بذاری؟", lambda x: bk_dep_do(uid, k, x), [["500", "1000", "5000"], ["10000", "50000", "همه"]])


def bk_dep_do(uid, k, t):
    c = mine(uid)
    amt = c["money"] if squash(t) == "همه" else (num(t) or 0)
    amt = min(amt, c["money"], max(0.0, bank_cap(c) - dep_total(c)))
    if amt <= 0:
        tell(uid, "❌ مبلغ نامعتبر یا سقف سپرده پر شده.")
        return r_bank(uid)
    c["money"] -= amt
    c["bank"]["deps"].append({"id": nid(), "kind": k, "amt": amt, "p": amt, "t": now(), "unlock": now() + BANK_KINDS[k]["lock"] * 3600})
    quest_add(c, "deposit")
    tell(uid, "✅ %s M$ در «%s» سپرده شد." % (m(amt), BANK_KINDS[k]["name"]))
    r_bank(uid)


@route(BK_WD)
def r_bk_wd(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ds = c["bank"]["deps"]
    if not ds:
        return back_to(uid, "🏧 سپرده‌ای نداری.", BANK_ROWS)
    labels = {}
    for d in ds:
        lock = (" 🔒 %s" % dur(d["unlock"] - now())) if d["unlock"] > now() else ""
        labels["#%d %s — %s M$%s" % (d["id"], BANK_KINDS[d["kind"]]["name"].split(" ", 1)[0], m(d["amt"]), lock)] = d["id"]
    ask(uid, "🏧 کدوم سپرده رو برداشت کنی؟ (سود تا الان: %s M$)" % m(sum(d["amt"] - d["p"] for d in ds)),
        lambda t: bk_wd_do(uid, labels.get(t)), [[l] for l in labels])


def bk_wd_do(uid, did):
    c = mine(uid)
    d = next((x for x in c["bank"]["deps"] if x["id"] == did), None) if did else None
    if not d:
        return r_bank(uid)
    c["bank"]["deps"].remove(d)
    if d["unlock"] > now():
        got = d["p"] * (1 - EARLY_PENALTY)
        tell(uid, "⚠️ برداشت زودهنگام: سود از دست رفت و %d٪ جریمه کسر شد." % int(EARLY_PENALTY * 100))
    else:
        got = d["amt"]
    c["money"] += got
    tell(uid, "🏧 %s M$ به خزانه برگشت." % m(got))
    r_bank(uid)


@route(BK_LOAN)
def r_bk_loan(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    room = max(0.0, credit_limit(c) - c["bank"]["loan"])
    if room < 100:
        return back_to(uid, "💳 سقف اعتبارت پر شده. اول وام قبلی رو بازپرداخت کن.", BANK_ROWS)
    ask(uid, "💳 دریافت وام (حداکثر %s M$)\nسود ٪%.2f در ساعت؛ بعد از %d ساعت جریمه!" % (m(room), LOAN_RATE * 100, LOAN_GRACE_H),
        lambda t: bk_loan_do(uid, t), [["25%", "50%", "100%"]])


def bk_loan_do(uid, t):
    c = mine(uid)
    room = max(0.0, credit_limit(c) - c["bank"]["loan"])
    raw = en_digits(t).strip()
    v = num(raw.replace("%", ""))
    amt = room * min(100.0, v) / 100.0 if (raw.endswith("%") and v) else min(room, v or 0)
    if amt <= 0:
        tell(uid, "❌ مبلغ نامعتبر.")
        return r_bank(uid)
    b = c["bank"]
    if b["loan"] <= 0:
        b["loan_t"], b["warned"] = now(), 0
    b["loan"] += amt
    c["money"] += amt
    tell(uid, "💳 وام %s M$ دریافت شد." % m(amt))
    r_bank(uid)


@route(BK_REPAY)
def r_bk_repay(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    b = c["bank"]
    if b["loan"] <= 0:
        return back_to(uid, "✅ وامی نداری.", BANK_ROWS)
    ask(uid, "💸 بدهی: %s M$ | موجودی: %s M$\nچقدر بازپرداخت کنی؟" % (m(b["loan"]), m(c["money"])), lambda t: bk_repay_do(uid, t),
        [["25%", "50%", "100%"]])


def bk_repay_do(uid, t):
    c = mine(uid)
    b = c["bank"]
    raw = en_digits(t).strip()
    v = num(raw.replace("%", ""))
    amt = b["loan"] * min(100.0, v) / 100.0 if (raw.endswith("%") and v) else (v or 0)
    amt = min(amt, b["loan"], c["money"])
    if amt <= 0:
        tell(uid, "❌ مبلغ نامعتبر یا پول کافی نداری.")
        return r_bank(uid)
    c["money"] -= amt
    b["loan"] -= amt
    if b["loan"] < 1:
        b["loan"], b["warned"] = 0.0, 0
    tell(uid, "💸 %s M$ بازپرداخت شد. بدهی باقی‌مانده: %s M$" % (m(amt), m(b["loan"])))
    r_bank(uid)


@route(BK_STATUS)
def r_bk_status(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    b = c["bank"]
    L = ["📄 وضعیت حساب بانکی %s" % cname(c), ""]
    for d in b["deps"]:
        L.append("🏧 #%d %s: %s M$ (سود: +%s)%s" % (d["id"], BANK_KINDS[d["kind"]]["name"], m(d["amt"]), m(d["amt"] - d["p"]),
                                                    (" 🔒 %s" % dur(d["unlock"] - now())) if d["unlock"] > now() else ""))
    if not b["deps"]:
        L.append("🏧 سپرده‌ای نداری.")
    if b["loan"] > 0:
        age = (now() - b["loan_t"]) / 3600
        L.append("\n💳 وام: %s M$ — %.0f ساعت از دریافت %s" % (m(b["loan"]), age, "⚠️ معوق!" if age > LOAN_GRACE_H else ""))
    else:
        L.append("\n💳 وامی نداری.")
    back_to(uid, "\n".join(L), BANK_ROWS)


# ═════════════ اتحادها (ائتلاف‌های بزرگ) ═════════════
UN_CREATE_COST = 3000
UN_EMOJIS = ["🛡", "⚔️", "🦅", "🌐", "⭐", "🔱", "🐺", "🦁", "🐉", "🗡"]
UN_MOTTOS = ["🤝 متحد می‌مونیم", "💪 قدرت در اتحاد", "🕊 صلح با اقتدار", "🔥 هر که به یکی تجاوز کنه به همه"]


def un_can_join(un, c):
    if c.get("union"):
        return False, "این کشور عضو اتحاد دیگه‌ایه."
    if len(un_members(un)) >= un_cap(un):
        return False, "ظرفیت اتحاد پره."
    for i in un_members(un):
        if at_war(i, c["iso"]):
            return False, "این کشور با یکی از اعضای اتحاد در جنگه."
    return True, ""


def un_join(un, c):
    c["union"] = un["id"]
    un["members"].append(c["iso"])
    un_log(un, "%s به اتحاد پیوست" % cname(c))
    un_tell(un, "🛡 %s به اتحاد «%s» پیوست!" % (cname(c), un_label(un)), skip=c["iso"])
    announce("🛡 عضو جدید اتحاد!\n%s به اتحاد «%s» پیوست.\n#اتحاد" % (cname(c), un_label(un)),
             cat="union", iso=c["iso"], photo=un.get("photo"))


def un_ctx(uid, need=None):
    c = mine(uid)
    if not c:
        no_country(uid)
        return None, None
    un = un_get(c)
    if not un:
        back_to(uid, "🛡 عضو هیچ اتحادی نیستی.", UN_NONE_ROWS)
        return None, None
    if need == "leader" and un["leader"] != c["iso"]:
        back_to(uid, "👑 این کار فقط برای رهبر اتحاده.", UN_ROWS)
        return None, None
    if need == "staff" and un_role(un, c["iso"]) == "member":
        back_to(uid, "🎖 این کار فقط برای رهبر یا افسرهاست.", UN_ROWS)
        return None, None
    return c, un


def un_summary(un):
    ld = DB["countries"].get(un["leader"])
    return ("🛡 %s\n«%s»\n━━━━━━━━━━━━\n👑 رهبر: %s\n⭐ سطح %d/10 | 👥 اعضا: %d/%d\n💪 قدرت کل: %s\n💰 خزانه: %s M$\n"
            "✨ مزایا: درآمد اعضا +%d٪ | دفاع +%d٪ | کمک دفاعی هم‌اتحادی‌ها %d٪ از دفاعشون") % (
        un_label(un), un["motto"], cname(ld) if ld else "—", un["lvl"], len(un_members(un)), un_cap(un), m(un_power(un)),
        m(un["bank"]), 3 * un["lvl"], 2 * un["lvl"], int((0.15 + 0.02 * un["lvl"]) * 100))


@route(B_UNION)
def r_union(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    un = un_get(c)
    if not un:
        return back_to(uid, ("🛡 اتحاد (ائتلاف بزرگ)\n\nتو عضو هیچ اتحادی نیستی.\n\n"
                             "اتحاد یعنی ائتلافی از چند کشور با خزانه‌ی مشترک، ارتقای سطح، مزایای درآمد و دفاع، "
                             "کمک دفاعی در جنگ، اعلام جنگ مشترک، افسر و پیام‌رسانی. ساختنش %s M$ هزینه داره.") % m(UN_CREATE_COST),
                       UN_NONE_ROWS)
    back_to(uid, un_summary(un) + "\n\n🎖 نقش تو: " + {"leader": "👑 رهبر", "officer": "🎖 افسر", "member": "🪖 عضو"}[un_role(un, c["iso"])], UN_ROWS)


@route(UN_INFO)
def r_un_info(uid):
    c, un = un_ctx(uid)
    if un:
        back_to(uid, un_summary(un), UN_ROWS)


@route(UN_MEMBERS)
def r_un_members(uid):
    c, un = un_ctx(uid)
    if not un:
        return
    L = ["👥 اعضای %s" % un_label(un), ""]
    for i in un_members(un):
        x = DB["countries"][i]
        L.append("%s %s — 💪 %s | 🗺 %d" % ({"leader": "👑", "officer": "🎖", "member": "🪖"}[un_role(un, i)], cname(x), m(power(x)), x["prov"]))
    back_to(uid, "\n".join(L), UN_ROWS)


@route(UN_LOG)
def r_un_log(uid):
    c, un = un_ctx(uid)
    if un:
        back_to(uid, "📜 تاریخچه‌ی اتحاد\n\n" + ("\n".join("• %s پیش — %s" % (dur(now() - t), tx) for t, tx in reversed(un["log"][-12:])) or "هنوز رویدادی نیست."), UN_ROWS)


@route(UN_RANK)
def r_un_rank(uid):
    rank_show(uid, "اتحادها")


@route(UN_NEW)
def r_un_new(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if c.get("union"):
        return back_to(uid, "تو همین حالا عضو یک اتحادی.", UN_ROWS)
    if c["money"] < UN_CREATE_COST:
        return back_to(uid, "❌ ساختن اتحاد %s M$ می‌خواد." % m(UN_CREATE_COST), UN_NONE_ROWS)
    ask(uid, "✍️ اسم اتحاد رو بنویس (حداکثر ۲۴ حرف):", lambda t: un_new_name(uid, t))


def un_new_name(uid, t):
    name = t.strip()[:24]
    if len(name) < 2 or any(squash(u["name"]) == squash(name) for u in DB["unions"].values()):
        tell(uid, "❌ اسم خیلی کوتاه یا تکراریه.")
        return r_un_new(uid)
    ask(uid, "🎨 یک ایموجی برای نشان اتحاد انتخاب کن (یا خودت یکی بفرست):", lambda e: un_new_emoji(uid, name, e), chunk(UN_EMOJIS, 5))


def un_new_emoji(uid, name, e):
    emoji = e.strip()[:4] or "🛡"
    ask_text(uid, "📜 شعار اتحاد؟", UN_MOTTOS, lambda mt: un_new_do(uid, name, emoji, mt), "✍️ شعار اتحاد (حداکثر ۶۰ حرف):")


def un_new_do(uid, name, emoji, motto):
    c = mine(uid)
    if not c or c.get("union") or c["money"] < UN_CREATE_COST:
        return menu(uid, "❌ ساخت اتحاد ممکن نیست.")
    un = {"id": nid(), "name": name, "emoji": emoji, "motto": motto.strip()[:60], "leader": c["iso"], "officers": [],
          "members": [c["iso"]], "bank": 0.0, "lvl": 1, "created": now(), "photo": None, "log": []}
    DB["unions"][str(un["id"])] = un
    c["union"] = un["id"]
    c["money"] -= UN_CREATE_COST
    un_log(un, "اتحاد توسط %s تأسیس شد" % cname(c))
    announce("🛡 اتحاد جدید تأسیس شد!\n%s\n«%s»\n👑 رهبر: %s\n#اتحاد" % (un_label(un), un["motto"], cname(c)), cat="union", iso=c["iso"])
    back_to(uid, "🎉 اتحاد «%s» ساخته شد! کشورها رو دعوت کن." % un_label(un), UN_ROWS)


@route(UN_JOIN)
def r_un_join(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if c.get("union"):
        return back_to(uid, "تو همین حالا عضو یک اتحادی.", UN_ROWS)
    open_ = [u for u in DB["unions"].values() if un_can_join(u, c)[0]]
    if not open_:
        return back_to(uid, "😕 اتحاد بازی برای پیوستن نیست.", UN_NONE_ROWS)
    labels = {"%s (%d/%d · ⭐%d)" % (un_label(u), len(un_members(u)), un_cap(u), u["lvl"]): u["id"] for u in open_[:30]}
    ask(uid, "📨 به کدوم اتحاد درخواست عضویت می‌دی؟", lambda t: un_join_req(uid, labels.get(t)), [[l] for l in labels])


def un_join_req(uid, unid):
    c = mine(uid)
    un = DB["unions"].get(str(unid)) if unid else None
    if not c or not un:
        return r_un_join(uid)
    ok, why = un_can_join(un, c)
    if not ok:
        return back_to(uid, "❌ " + why, UN_NONE_ROWS)
    p = {"id": nid(), "type": "unionreq", "a": c["iso"], "b": un["leader"], "un": un["id"], "t": now()}
    DB["props"].append(p)
    send_prop(p, "📨 %s درخواست عضویت در اتحاد «%s» داده.\nمی‌پذیری؟" % (cname(c), un_label(un)))
    back_to(uid, "📨 درخواستت برای رهبر اتحاد ارسال شد.", UN_NONE_ROWS)


@route(UN_DON)
def r_un_don(uid):
    c, un = un_ctx(uid)
    if not un:
        return
    ask(uid, "💰 چند M$ به خزانه‌ی اتحاد کمک می‌کنی؟\n(خزانه: %s M$ | موجودی تو: %s M$)" % (m(un["bank"]), m(c["money"])),
        lambda t: un_don_do(uid, t), [["500", "1000", "5000"], ["20000", "100000", "همه"]])


def un_don_do(uid, t):
    c, un = un_ctx(uid)
    if not un:
        return
    amt = c["money"] if squash(t) == "همه" else (num(t) or 0)
    amt = min(amt, c["money"])
    if amt <= 0:
        tell(uid, "❌ مبلغ نامعتبر.")
        return r_union(uid)
    c["money"] -= amt
    un["bank"] += amt
    un_log(un, "%s مبلغ %s M$ کمک کرد" % (cname(c), m(amt)))
    xp_add(c, 4)
    tell(uid, "✅ %s M$ به خزانه‌ی اتحاد واریز شد." % m(amt))
    r_union(uid)


@route(UN_UP)
def r_un_up(uid):
    c, un = un_ctx(uid, "staff")
    if not un:
        return
    return back_to(uid, "⛔ ارتقای سطح اتحاد حذف شده؛ ظرفیت اتحاد رو ادمین تعیین می‌کنه.", UN_ROWS)
    if un["lvl"] >= 10:
        return back_to(uid, "⭐ اتحاد در بالاترین سطحه.", UN_ROWS)
    cost = un_up_cost(un)
    ask(uid, "⬆️ ارتقای اتحاد: از سطح %d به %d\n💲 هزینه از خزانه: %s M$ (خزانه: %s)\n✨ درآمد اعضا +۳٪، دفاع +۲٪، ظرفیت +۲ کشور\n\nانجام بشه؟"
        % (un["lvl"], un["lvl"] + 1, m(cost), m(un["bank"])), lambda t: un_up_do(uid, t), [["✅ بله", "❌ خیر"]])


def un_up_do(uid, t):
    c, un = un_ctx(uid, "staff")
    if not un:
        return
    cost = un_up_cost(un)
    if "بله" not in t or un["bank"] < cost or un["lvl"] >= 10:
        return back_to(uid, "❌ انجام نشد (خزانه کافی نیست یا لغو شد).", UN_ROWS)
    un["bank"] -= cost
    un["lvl"] += 1
    un_log(un, "اتحاد به سطح %d ارتقا یافت" % un["lvl"])
    un_tell(un, "⭐ اتحاد «%s» به سطح %d رسید!" % (un_label(un), un["lvl"]))
    announce("⭐ ارتقای اتحاد\nاتحاد «%s» به سطح %d رسید!\n#اتحاد" % (un_label(un), un["lvl"]), cat="union", iso=c["iso"], photo=un.get("photo"))
    back_to(uid, "⭐ اتحاد به سطح %d رسید!" % un["lvl"], UN_ROWS)


@route(UN_MSG)
def r_un_msg(uid):
    c, un = un_ctx(uid)
    if not un:
        return
    if c["un_msg_t"] > now():
        return back_to(uid, "⏱ %s دیگه می‌تونی پیام بدی." % dur(c["un_msg_t"] - now()), UN_ROWS)
    ask(uid, "📢 پیامت برای همه‌ی اعضا (حداکثر ۳۰۰ حرف):", lambda t: un_msg_do(uid, t))


def un_msg_do(uid, t):
    c, un = un_ctx(uid)
    if not un:
        return
    t = t.strip()[:300]
    if not t:
        return r_union(uid)
    c["un_msg_t"] = now() + 60
    un_tell(un, "📢 پیام اتحاد «%s» از %s:\n\n%s" % (un_label(un), cname(c), t), skip=c["iso"])
    back_to(uid, "✅ پیام برای اعضا ارسال شد.", UN_ROWS)


@route(UN_INV)
def r_un_inv(uid):
    c, un = un_ctx(uid, "staff")
    if not un:
        return
    pick_country(uid, "📩 کدوم کشور رو دعوت می‌کنی؟", lambda iso: un_inv_do(uid, iso),
                 lambda x: x["alive"] and x["owner"] and not x.get("union") and un_can_join(un, x)[0])


def un_inv_do(uid, iso):
    c, un = un_ctx(uid, "staff")
    d = C(iso)
    if not un or not d or not d["owner"]:
        return
    ok, why = un_can_join(un, d)
    if not ok:
        return back_to(uid, "❌ " + why, UN_ROWS)
    p = {"id": nid(), "type": "union", "a": c["iso"], "b": iso, "un": un["id"], "t": now()}
    DB["props"].append(p)
    send_prop(p, "📩 %s تو رو به اتحاد «%s» دعوت کرده!\n%s\nمی‌پذیری؟" % (cname(c), un_label(un), "«%s»" % un["motto"]))
    back_to(uid, "📩 دعوت برای %s ارسال شد." % cname(d), UN_ROWS)


@route(UN_LEAVE)
def r_un_leave(uid):
    c, un = un_ctx(uid)
    if un:
        ask(uid, "🚪 مطمئنی از اتحاد «%s» خارج بشی؟" % un_label(un), lambda t: un_leave_do(uid, t), [["✅ بله، خارج می‌شم", "❌ خیر"]])


def un_leave_do(uid, t):
    c, un = un_ctx(uid)
    if not un or "بله" not in t:
        return r_union(uid)
    announce("🚪 خروج از اتحاد\n%s از اتحاد «%s» خارج شد.\n#اتحاد" % (cname(c), un_label(un)), cat="union", iso=c["iso"])
    un_tell(un, "🚪 %s از اتحاد خارج شد." % cname(c), skip=c["iso"])
    un_remove(c["iso"], "ترک")
    back_to(uid, "🚪 از اتحاد خارج شدی.", UN_NONE_ROWS)


@route(UN_MANAGE)
def r_un_manage(uid):
    c, un = un_ctx(uid, "staff")
    if un:
        back_to(uid, "👑 مدیریت اتحاد %s\n(بعضی کارها فقط مخصوص رهبره)" % un_label(un), UN_MAN_ROWS)


@route(UN_WD)
def r_un_wd(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        ask(uid, "🏧 چند M$ از خزانه (%s M$) برداشت بشه؟" % m(un["bank"]), lambda t: un_wd_do(uid, t), [["1000", "5000", "20000"], ["همه"]])


def un_wd_do(uid, t):
    c, un = un_ctx(uid, "leader")
    if not un:
        return
    amt = un["bank"] if squash(t) == "همه" else (num(t) or 0)
    amt = min(amt, un["bank"])
    if amt <= 0:
        return back_to(uid, "❌ مبلغ نامعتبر.", UN_MAN_ROWS)
    un["bank"] -= amt
    c["money"] += amt
    un_log(un, "رهبر %s M$ از خزانه برداشت کرد" % m(amt))
    back_to(uid, "🏧 %s M$ به خزانه‌ی کشورت منتقل شد." % m(amt), UN_MAN_ROWS)


@route(UN_SPLIT)
def r_un_split(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        ask(uid, "🎁 چند M$ از خزانه (%s M$) بین %d عضو به‌طور مساوی پخش بشه؟" % (m(un["bank"]), len(un_members(un))),
            lambda t: un_split_do(uid, t), [["1000", "5000", "20000"], ["همه"]])


def un_split_do(uid, t):
    c, un = un_ctx(uid, "leader")
    if not un:
        return
    amt = un["bank"] if squash(t) == "همه" else (num(t) or 0)
    amt = min(amt, un["bank"])
    ms = un_members(un)
    if amt <= 0 or not ms:
        return back_to(uid, "❌ مبلغ نامعتبر.", UN_MAN_ROWS)
    un["bank"] -= amt
    each = amt / len(ms)
    for i in ms:
        DB["countries"][i]["money"] += each
        notify_country(i, "🎁 سهم تو از خزانه‌ی اتحاد: +%s M$" % m(each))
    un_log(un, "%s M$ بین اعضا پخش شد" % m(amt))
    back_to(uid, "🎁 هر عضو %s M$ گرفت." % m(each), UN_MAN_ROWS)


@route(UN_KICK)
def r_un_kick(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        pick_country(uid, "👢 کدوم عضو اخراج بشه؟", lambda iso: un_kick_do(uid, iso), lambda x: x["iso"] in un["members"] and x["iso"] != c["iso"])


def un_kick_do(uid, iso):
    c, un = un_ctx(uid, "leader")
    if not un or iso not in un["members"] or iso == c["iso"]:
        return
    d = C(iso)
    notify_country(iso, "👢 از اتحاد «%s» اخراج شدی." % un_label(un))
    un_remove(iso, "اخراج")
    announce("👢 اخراج از اتحاد\n%s از اتحاد «%s» اخراج شد.\n#اتحاد" % (cname(d), un_label(un)), cat="union", iso=iso)
    back_to(uid, "👢 %s اخراج شد." % cname(d), UN_MAN_ROWS)


@route(UN_OFF)
def r_un_off(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        pick_country(uid, "🎖 کدوم عضو افسر بشه یا از افسری عزل بشه؟", lambda iso: un_off_do(uid, iso),
                     lambda x: x["iso"] in un["members"] and x["iso"] != c["iso"])


def un_off_do(uid, iso):
    c, un = un_ctx(uid, "leader")
    if not un or iso not in un["members"]:
        return
    if iso in un["officers"]:
        un["officers"].remove(iso)
        msg = "از افسری عزل شد"
    else:
        un["officers"].append(iso)
        msg = "افسر شد"
    un_log(un, "%s %s" % (cname(C(iso)), msg))
    notify_country(iso, "🎖 در اتحاد «%s» %s." % (un_label(un), msg))
    back_to(uid, "✅ %s %s." % (cname(C(iso)), msg), UN_MAN_ROWS)


@route(UN_TRANS)
def r_un_trans(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        pick_country(uid, "🔄 رهبری به کدوم عضو منتقل بشه؟", lambda iso: ask(
            uid, "مطمئنی؟ رهبری به %s منتقل می‌شه." % cname(C(iso)), lambda t: un_trans_do(uid, iso, t), [["✅ بله", "❌ خیر"]]),
            lambda x: x["iso"] in un["members"] and x["iso"] != c["iso"])


def un_trans_do(uid, iso, t):
    c, un = un_ctx(uid, "leader")
    if not un or "بله" not in t or iso not in un["members"]:
        return back_to(uid, "لغو شد.", UN_MAN_ROWS)
    if iso in un["officers"]:
        un["officers"].remove(iso)
    un["officers"].append(c["iso"])
    un["leader"] = iso
    un_log(un, "رهبری به %s منتقل شد" % cname(C(iso)))
    un_tell(un, "👑 رهبر جدید اتحاد: %s" % cname(C(iso)))
    back_to(uid, "👑 رهبری منتقل شد.", UN_ROWS)


@route(UN_MOTTO)
def r_un_motto(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        ask_text(uid, "✏️ شعار جدید؟", UN_MOTTOS, lambda t: un_motto_do(uid, t), "✍️ شعار (حداکثر ۶۰ حرف):")


def un_motto_do(uid, t):
    c, un = un_ctx(uid, "leader")
    if un and t.strip():
        un["motto"] = t.strip()[:60]
    back_to(uid, "✅ شعار تغییر کرد.", UN_MAN_ROWS)


@route(UN_PHOTO)
def r_un_photo(uid):
    c, un = un_ctx(uid, "leader")
    if not un:
        return

    def save(fid, cap):
        un["photo"] = fid
        back_to(uid, "✅ تصویر اتحاد ذخیره شد؛ برای گزارش‌های اتحاد توی کانال استفاده می‌شه.", UN_MAN_ROWS)

    ask_photo(uid, "🖼 تصویر/پرچم اتحاد رو بفرست (Photo):", save)


@route(UN_DIS)
def r_un_dis(uid):
    c, un = un_ctx(uid, "leader")
    if un:
        ask(uid, "💥 اتحاد «%s» برای همیشه منحل بشه؟ (خزانه‌ی اتحاد بین اعضا پخش می‌شه)" % un_label(un), lambda t: un_dis_do(uid, t),
            [["💥 بله، منحل کن", "❌ خیر"]])


def un_dis_do(uid, t):
    c, un = un_ctx(uid, "leader")
    if not un or "بله" not in t:
        return back_to(uid, "لغو شد.", UN_MAN_ROWS)
    ms = un_members(un)
    for i in ms:
        DB["countries"][i]["money"] += un["bank"] / max(1, len(ms))
        DB["countries"][i]["union"] = None
        notify_country(i, "💥 اتحاد «%s» منحل شد." % un_label(un))
    DB["unions"].pop(str(un["id"]), None)
    announce("💥 اتحاد «%s» منحل شد.\n#اتحاد" % un_label(un), cat="union", iso=c["iso"])
    back_to(uid, "💥 اتحاد منحل شد.", UN_NONE_ROWS)


@route(UN_WAR)
def r_un_war(uid):
    c, un = un_ctx(uid, "staff")
    if not un:
        return
    ms = set(un["members"])
    pick_country(uid, "⚔️ اتحاد به کدوم کشور اعلام جنگ بده؟ (همه‌ی اعضا وارد جنگ می‌شن)", lambda iso: un_war_do(uid, iso),
                 lambda x: x["alive"] and x["iso"] not in ms and x["prot"] < now() and not any(is_ally(i, x["iso"]) for i in ms))


def un_war_do(uid, iso):
    c, un = un_ctx(uid, "staff")
    d = C(iso)
    if not un or not d or not d["alive"] or d["prot"] > now():
        return back_to(uid, "❌ جنگ اتحادی ممکن نیست.", UN_MAN_ROWS)
    if war_blocked(uid, "conv", UN_MAN_ROWS):
        return
    joined = []
    for i in un_members(un):
        if i == iso or is_ally(i, iso):
            continue
        if not at_war(i, iso):
            add_war(i, iso)
            joined.append(i)
        DB["countries"][i]["prot"] = 0
    if not joined:
        return back_to(uid, "😕 همه‌ی اعضا همین الان با این کشور در جنگن.", UN_MAN_ROWS)
    announce("⚔️ جنگ اتحادی!\nاتحاد «%s» به %s اعلام جنگ کرد!\n🪖 کشورهای درگیر: %s\n#اعلام_جنگ" % (
        un_label(un), cname(d), "، ".join(cname(DB["countries"][i]) for i in joined)), cat="war", iso=(joined[0], iso), photo=un.get("photo"))
    un_log(un, "جنگ اتحادی علیه %s" % cname(d))
    un_tell(un, "⚔️ اتحاد به %s اعلام جنگ کرد؛ همه‌ی اعضا وارد جنگ شدن!" % cname(d))
    notify_country(iso, "🚨 اتحاد «%s» به کشورت اعلام جنگ کرد!" % un_label(un))
    back_to(uid, "⚔️ جنگ اتحادی اعلام شد.", UN_MAN_ROWS)


# ═════════════ عملیات سایبری ═════════════
def cyber_atk(c):
    u = c["units"]
    return u.get("redhat", 0) + 0.5 * u.get("fin", 0) + 0.2 * u.get("spy", 0)


def cyber_def(c):
    u = c["units"]
    return 1.3 * u.get("whitehat", 0) + 0.15 * u.get("redhat", 0) + 0.1 * u.get("spy", 0)


@route(B_CYBER)
def r_cyber(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    back_to(uid, "💻 عملیات سایبری\n\n🔴 هکر قرمز: %s | 💰 هکر مالی: %s | 🕵️ جاسوس: %s | ⚪ هکر سفید: %s\n"
                 "⚔️ قدرت حمله‌ی سایبری: %s | 🛡 دفاع سایبری: %s\n⏱ آماده‌باش: %s\n\n"
                 "🏦 هک مالی: بخشی از پول و برق هدف رو می‌دزدی.\n🕵️ جاسوسی: اطلاعات کامل هدف رو می‌گیری.\n"
                 "هکرهای سفید از حمله‌ی دیگران دفاع می‌کنن. تجهیزات سایبری رو از فروشگاه (💻 سایبری) یا پک «یورش سایبری» بگیر."
            % (m(c["units"].get("redhat", 0)), m(c["units"].get("fin", 0)), m(c["units"].get("spy", 0)), m(c["units"].get("whitehat", 0)),
               m(cyber_atk(c)), m(cyber_def(c)), dur(c["cd_cy"] - now()) if c["cd_cy"] > now() else "آماده ✅"), CYBER_ROWS)


@route(CY_DEF)
def r_cy_def(uid):
    r_cyber(uid)


def cy_targets(c):
    return lambda x: x["alive"] and x["iso"] != c["iso"] and not is_ally(c["iso"], x["iso"])


@route(CY_FIN)
def r_cy_fin(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid) or war_blocked(uid, "cyber", CYBER_ROWS):
        return
    if c["cd_cy"] > now():
        return back_to(uid, "⏱ %s دیگه آماده‌ای." % dur(c["cd_cy"] - now()), CYBER_ROWS)
    if cyber_atk(c) < 1:
        return back_to(uid, "❌ هکر نداری؛ از فروشگاه یا پک سایبری بگیر.", CYBER_ROWS)
    pick_country(uid, "🏦 هک مالیِ کدوم کشور؟", lambda iso: cy_fin_do(uid, iso), cy_targets(c))


def cy_fin_do(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or c["cd_cy"] > now():
        return back_to(uid, "❌ ممکن نیست.", CYBER_ROWS)
    atk, dfn = cyber_atk(c), cyber_def(d)
    p = atk / (atk + dfn * 1.2 + 20)
    c["cd_cy"] = now() + 600
    quest_add(c, "cyber")
    xp_add(c, 6)
    if random.random() < p:
        loot = d["money"] * min(0.15, 0.03 + 0.08 * p)
        d["money"] -= loot
        c["money"] += loot
        d["res"]["elec"] *= 0.9
        d["stab"] = max(0.0, d["stab"] - 3)
        announce("💻 حمله‌ی سایبری موفق!\n%s به شبکه‌ی بانکی %s نفوذ کرد و %s M$ دزدید!\n#سایبری" % (cname(c), cname(d), m(loot)),
                 cat="cyber", iso=(c["iso"], iso))
        notify_country(iso, "🚨 هکرهای %s به خزانه‌ات نفوذ کردن! %s M$ دزدیده شد." % (cname(c), m(loot)))
        back_to(uid, "✅ نفوذ موفق! +%s M$ دزدیدی." % m(loot), CYBER_ROWS)
    else:
        for k in ("redhat", "fin"):
            c["units"][k] = c["units"].get(k, 0) - lose_count(c["units"].get(k, 0), 0.10)
        notify_country(iso, "🛡 یک حمله‌ی سایبری از سمت %s دفع شد!" % cname(c))
        back_to(uid, "❌ حمله دفع شد و ۱۰٪ هکرهات شناسایی و از دست رفتن.", CYBER_ROWS)


@route(CY_SPY)
def r_cy_spy(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid) or war_blocked(uid, "cyber", CYBER_ROWS):
        return
    if c["cd_cy"] > now():
        return back_to(uid, "⏱ %s دیگه آماده‌ای." % dur(c["cd_cy"] - now()), CYBER_ROWS)
    if c["units"].get("spy", 0) < 1:
        return back_to(uid, "❌ جاسوس نداری؛ از فروشگاه یا پک سایبری بگیر.", CYBER_ROWS)
    pick_country(uid, "🕵️ جاسوسی از کدوم کشور؟", lambda iso: cy_spy_do(uid, iso), cy_targets(c))


def cy_spy_do(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or c["cd_cy"] > now():
        return back_to(uid, "❌ ممکن نیست.", CYBER_ROWS)
    sp = c["units"].get("spy", 0)
    p = sp / (sp + cyber_def(d) * 0.5 + 5)
    c["cd_cy"] = now() + 600
    quest_add(c, "cyber")
    xp_add(c, 4)
    if random.random() < p:
        by = {}
        for k, n in d["units"].items():
            if n > 0 and k in U:
                by[CAT_LABEL[U[k]["cat"]]] = by.get(CAT_LABEL[U[k]["cat"]], 0) + n
        un = un_get(d)
        L = ["🕵️ گزارش اطلاعاتی از %s" % cname(d), "👤 رهبر: %s" % (d["leader"] or "—"), "💰 خزانه: %s M$ | 👥 %s" % (m(d["money"]), m(d["pop"])),
             "💪 قدرت: %s | 🔬 تکنولوژی %d | 🧱 استحکامات %d | 🗺 %d استان | 😐 ثبات %d٪" % (m(power(d)), d["tech"], d["fort"], d["prov"], int(d["stab"])),
             "☢️ کلاهک: %d | 💻 دفاع سایبری: %s" % (nuke_count(d), m(cyber_def(d))),
             "🛡 اتحاد: %s" % (un_label(un) if un else "—"), "", "🎖 ارتش:"]
        L += ["  %s: %s" % (k, m(v)) for k, v in by.items()]
        L += ["", "📦 منابع: " + " | ".join("%s %s" % (RES[k][0], m(v)) for k, v in d["res"].items())]
        back_to(uid, "\n".join(L), CYBER_ROWS)
    else:
        lost = max(1, int(sp * 0.1))
        c["units"]["spy"] = sp - lost
        notify_country(iso, "🕵️ یک جاسوس %s دستگیر شد!" % cname(c))
        back_to(uid, "❌ جاسوست لو رفت؛ %d جاسوس از دست رفتن." % lost, CYBER_ROWS)


# ═════════════ تحریم‌ها ═════════════
SANCTION_COST = 500
SANCTION_H = 24


@route(B_SANC)
def r_sanc(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    on_me = [s for s in sanc_active() if s["on"] == c["iso"]]
    by_me = [s for s in sanc_active() if s["by"] == c["iso"]]
    back_to(uid, ("🚫 تحریم‌ها\n\nتحریم، درآمد کشور هدف رو ۶٪ کم می‌کنه (تا ۵ تحریم هم‌زمان) و معامله/مجوز بین دو کشور رو قطع می‌کنه.\n"
                  "💲 هزینه‌ی اعمال: %s M$ برای %d ساعت\n\n🚫 تحریم‌های روی تو: %d\n🚫 تحریم‌های اعمال‌شده توسط تو: %d")
            % (m(SANCTION_COST), SANCTION_H, len(on_me), len(by_me)), SANC_ROWS)


@route(SC_ADD)
def r_sc_add(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid):
        return
    mine_on = {s["on"] for s in sanc_active() if s["by"] == c["iso"]}
    pick_country(uid, "🚫 کدوم کشور تحریم بشه؟ (هزینه %s M$)" % m(SANCTION_COST), lambda iso: sc_do(uid, iso),
                 lambda x: x["alive"] and x["iso"] != c["iso"] and x["iso"] not in mine_on and not is_ally(c["iso"], x["iso"]))


def sc_do(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or c["money"] < SANCTION_COST:
        return back_to(uid, "❌ ممکن نیست (پول کافی نیست؟).", SANC_ROWS)
    c["money"] -= SANCTION_COST
    DB["sanctions"].append({"by": c["iso"], "on": iso, "until": now() + SANCTION_H * 3600})
    xp_add(c, 5)
    announce("🚫 تحریم جدید!\n%s کشور %s را به مدت %d ساعت تحریم کرد.\n#تحریم" % (cname(c), cname(d), SANCTION_H), cat="sanction", iso=(c["iso"], iso))
    notify_country(iso, "🚫 %s تو رو تحریم کرد؛ درآمدت کم می‌شه و معامله/مجوز با اون قطعه." % cname(c))
    back_to(uid, "🚫 تحریم اعمال شد.", SANC_ROWS)


@route(SC_LIFT)
def r_sc_lift(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    mine_on = {s["on"] for s in sanc_active() if s["by"] == c["iso"]}
    if not mine_on:
        return back_to(uid, "تحریم فعالی نداری.", SANC_ROWS)
    pick_country(uid, "🕊 تحریم کدوم کشور لغو بشه؟", lambda iso: sc_lift_do(uid, iso), lambda x: x["iso"] in mine_on)


def sc_lift_do(uid, iso):
    c = mine(uid)
    DB["sanctions"] = [s for s in DB["sanctions"] if not (s["by"] == c["iso"] and s["on"] == iso)]
    notify_country(iso, "🕊 %s تحریمت رو لغو کرد." % cname(c))
    back_to(uid, "🕊 تحریم لغو شد.", SANC_ROWS)


@route(SC_LIST)
def r_sc_list(uid):
    ss = sanc_active()
    L = ["📋 تحریم‌های فعال جهان", ""] + ["🚫 %s تحریم کرده: %s (%s مانده)" % (cname(C(s["by"])), cname(C(s["on"])), dur(s["until"] - now()))
                                          for s in ss if C(s["by"]) and C(s["on"])]
    back_to(uid, "\n".join(L) if ss else "🕊 هیچ تحریم فعالی نیست.", SANC_ROWS)


def upgrade_flow(uid, kind):
    c = mine(uid)
    if not c:
        return no_country(uid)
    lvl, mx, cost, label = {"eco": (c["eco"], 10, cost_eco(c), "اقتصاد"),
                            "tech": (c["tech"], 6, cost_tech(c), "تکنولوژی"),
                            "fort": (c["fort"], 10, cost_fort(c), "استحکامات")}[kind]
    if lvl >= mx or not cost:
        return back_to(uid, "✅ %s در بالاترین سطح قرار داره." % label, ECO_ROWS)
    ask(uid, "%s: از سطح %d به %d\n💲 هزینه: %s M$\n💰 موجودی: %s M$\n\nانجام بشه؟" % (label, lvl, lvl + 1, m(cost), m(c["money"])),
        lambda t: upgrade_do(uid, kind, t), [["✅ بله", "❌ خیر"]])


def upgrade_do(uid, kind, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if "بله" not in t:
        return r_eco(uid)
    key = {"eco": "eco", "tech": "tech", "fort": "fort"}[kind]
    cost = {"eco": cost_eco, "tech": cost_tech, "fort": cost_fort}[kind](c)
    if not cost or cost > c["money"]:
        return back_to(uid, "❌ پول کافی نداری.", ECO_ROWS)
    c["money"] -= cost
    c[key] += 1
    if kind == "tech":
        announce("🔬 جهش فناوری\n%s به سطح تکنولوژی %d رسید!\n#تکنولوژی" % (cname(c), c["tech"]))
    r_eco(uid)


@route(B_UP_ECO)
def r_up_eco(uid):
    upgrade_flow(uid, "eco")


@route(B_UP_TECH)
def r_up_tech(uid):
    upgrade_flow(uid, "tech")


@route(B_UP_FORT)
def r_up_fort(uid):
    upgrade_flow(uid, "fort")


# ───── جنگ ─────
@route(B_WAR)
def r_war(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    en = [cname(C(i)) for i in enemies(c["iso"]) if C(i)]
    cd = max(0, c["cd"] - now())
    back_to(uid, "⚔️ مرکز فرماندهی جنگ\n🏳️ در جنگ با: %s\n⏱ آماده‌باش حمله: %s"
            % ("، ".join(en) if en else "هیچ‌کس", dur(cd) if cd else "آماده ✅"), WAR_ROWS)


@route(B_DECL)
def r_declare(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid) or war_blocked(uid, "conv", WAR_ROWS):
        return
    pick_country(uid, "🎯 به کدوم کشور اعلام جنگ می‌دی؟", lambda iso: declare_text(uid, iso),
                 lambda x: x["alive"] and x["owner"] and x["iso"] != c["iso"]
                 and not at_war(c["iso"], x["iso"]) and not is_ally(c["iso"], x["iso"]))


def declare_text(uid, iso):
    d = C(iso)
    if d and d["prot"] > now():
        return back_to(uid, "🛡 %s تا %s دیگه تحت حفاظته." % (cname(d), dur(d["prot"] - now())), WAR_ROWS)
    ask_text(uid, "✍️ پیام اعلامیه‌ی جنگ رو انتخاب کن:", DECL_PRESETS,
             lambda t: declare_do(uid, iso, "-" if "بدون متن" in t else t), "✍️ متن اعلامیه‌ی جنگ رو بنویس:")


def declare_do(uid, iso, t):
    c, d = mine(uid), C(iso)
    if not c:
        return no_country(uid)
    if frozen(uid) or war_blocked(uid, "conv", WAR_ROWS):
        return
    if (not d or not d["alive"] or not d["owner"] or at_war(c["iso"], iso)
            or is_ally(c["iso"], iso) or iso == c["iso"]):
        return back_to(uid, "❌ اعلام جنگ ممکن نیست.", WAR_ROWS)
    add_war(c["iso"], iso)
    c["prot"] = 0
    c["stab"] = max(0.0, c["stab"] - 5)
    msg = t.strip()[:500]
    text = "⚔️ اعلام جنگ!\n🔥 %s به %s اعلام جنگ داد!\n⚔️ آغازگر: %s\n🛡 هدف: %s" % (cname(c), cname(d), cname(c), cname(d))
    if msg and msg != "-":
        text += "\n\n💬 «%s»\n— %s" % (msg, c["leader"])
    text += "\n\n#اعلام_جنگ"
    announce(text, cat="war", iso=(c["iso"], iso))
    notify_country(iso, "🚨 %s به کشورت اعلام جنگ داد!" % cname(c))
    back_to(uid, "✅ اعلام جنگ منتشر شد. حالا از «💥 حمله» استفاده کن.", WAR_ROWS)


# ═════════════ حمله با انتخاب نیروها ═════════════
ATK = {}     # uid ← {"iso": هدف، "sent": {کلید تجهیز: تعداد}}
ATK_ADD, ATK_ALL, ATK_CLR, ATK_GO, ATK_CANCEL = (
    "➕ افزودن نیرو", "⚡ اعزام همه‌ی نیروها", "🗑 پاک کردن انتخاب", "✅ تایید و حمله", "❌ انصراف از حمله")
FORCE_CATS = {"🪖 زمینی": ["gnd"], "✈️ جنگنده": ["fighter"], "🛩 بمب‌افکن": ["bomber"], "🚁 بالگرد": ["heli"],
              "🛸 پهپاد": ["drone"], "🚢 ناوگان": ["navy"], "🚀 موشک": ["missile"], "💣 بمب": ["bomb"]}
ATTACK_CATS = {c for cs in FORCE_CATS.values() for c in cs}
MODE_NAME = {"ground": "🪖 یورش زمینی", "air": "✈️ حمله‌ی هوایی", "naval": "🚢 نبرد دریایی", "missile": "🚀 حمله‌ی موشکی"}
AIR_CATS = {"fighter", "bomber", "heli", "drone", "bomb"}


def force_mode(sent):
    cats = {U[k]["cat"] for k in sent}
    if "gnd" in cats:
        return "ground"
    if cats & AIR_CATS:
        return "air"
    if "navy" in cats:
        return "naval"
    return "missile"


def atk_free(c, st, key):
    return c["units"].get(key, 0) - st["sent"].get(key, 0)


@route(B_ATK)
def r_attack(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid) or war_blocked(uid, "conv", WAR_ROWS):
        return
    if c["cd"] > now():
        return back_to(uid, "⏱ نیروهات هنوز آماده نیستن (%s)." % dur(c["cd"] - now()), WAR_ROWS)
    pick_country(uid, "🎯 هدف حمله؟\n(دشمنان در جنگ + کشورهای بدون رهبر)", lambda iso: atk_start(uid, iso),
                 lambda x: x["alive"] and x["iso"] != c["iso"]
                 and ((x["owner"] and at_war(c["iso"], x["iso"])) or not x["owner"]))


def atk_start(uid, iso):
    if not mine(uid) or not C(iso):
        return menu(uid)
    ATK[uid] = {"iso": iso, "sent": {}}
    atk_hub(uid)


def force_lines(sent, limit=10):
    by = sorted(sent.items(), key=lambda kv: -U[kv[0]]["atk"] * kv[1])
    L = ["   • %s × %s" % (U[k]["name"], m(q)) for k, q in by[:limit]]
    if len(by) > limit:
        L.append("   • و %d نوع دیگر ..." % (len(by) - limit))
    return L


def atk_hub(uid, note=""):
    c, st = mine(uid), ATK.get(uid)
    if not c or not st:
        return menu(uid)
    d = C(st["iso"])
    sel = st["sent"]
    L = []
    if note:
        L += [note, ""]
    L += ["💥 آماده‌سازی حمله", "🎯 هدف: %s" % cname(d), "━━━━━━━━━━━━━━━━━", ""]
    if sel:
        for lab, cats in FORCE_CATS.items():
            items = {k: q for k, q in sel.items() if U[k]["cat"] in cats}
            if items:
                L.append(lab)
                L += force_lines(items, 6)
        L += ["", "💥 قدرت حمله‌ی تخمینی: %s" % m(sent_atk(sel) * atk_mult(c)), "📌 نوع عملیات: " + MODE_NAME[force_mode(sel)]]
        if force_mode(sel) == "ground":
            L.append("🗺 با یگان زمینی می‌تونی استان فتح کنی")
        else:
            L.append("ℹ️ بدون یگان زمینی فقط ضربه می‌زنی (استان فتح نمی‌شه)")
    else:
        L.append("هنوز نیرویی انتخاب نکردی.\n«%s» رو بزن و دسته، مدل و تعداد رو انتخاب کن." % ATK_ADD)
    ask(uid, "\n".join(L), lambda t: atk_hub_do(uid, t), [[ATK_ADD, ATK_ALL], [ATK_CLR], [ATK_GO], [ATK_CANCEL]])


def atk_hub_do(uid, t):
    st, c = ATK.get(uid), mine(uid)
    if not st or not c:
        return menu(uid)
    s = squash(t)
    if s == squash(ATK_ADD):
        return atk_add_cat(uid)
    if s == squash(ATK_ALL):
        st["sent"] = {k: q for k, q in c["units"].items() if k in U and U[k]["cat"] in ATTACK_CATS and q > 0}
        return atk_hub(uid, "⚡ همه‌ی نیروهای رزمی انتخاب شدن.")
    if s == squash(ATK_CLR):
        st["sent"].clear()
        return atk_hub(uid, "🗑 انتخاب پاک شد.")
    if s == squash(ATK_GO):
        return atk_go(uid)
    if s == squash(ATK_CANCEL):
        ATK.pop(uid, None)
        return back_to(uid, "❌ حمله لغو شد.", WAR_ROWS)
    atk_hub(uid)


def atk_add_cat(uid):
    c, st = mine(uid), ATK.get(uid)
    if not c or not st:
        return menu(uid)
    rows, L = [], []
    for lab, cats in FORCE_CATS.items():
        n = sum(1 for k, q in c["units"].items() if k in U and U[k]["cat"] in cats and atk_free(c, st, k) > 0)
        if n:
            rows.append(lab)
            L.append("%s — %d مدل" % (lab, n))
    if not rows:
        return atk_hub(uid, "😕 نیروی آزاد دیگه‌ای نداری.")
    ask(uid, "کدوم دسته از نیروها؟\n\n" + "\n".join(L), lambda t: atk_pick_cat(uid, t), chunk(rows, 2))


def atk_pick_cat(uid, t):
    c, st = mine(uid), ATK.get(uid)
    if not c or not st:
        return menu(uid)
    lab = next((l for l in FORCE_CATS if squash(l) == squash(t)), None)
    if not lab:
        return atk_hub(uid)
    units = sorted((U[k] for k, q in c["units"].items() if k in U and U[k]["cat"] in FORCE_CATS[lab] and atk_free(c, st, k) > 0),
                   key=lambda u: -u["atk"])
    if not units:
        return atk_hub(uid, "😕 از این دسته نیروی آزاد نداری.")
    pick_unit(uid, "%s — کدوم مدل؟" % lab, units, lambda key: atk_pick_qty(uid, key), per=8,
              lines=lambda u: "• %s\n    داری: %s | قدرت هر عدد: %s" % (u["name"], m(atk_free(c, st, u["key"])), m(u["atk"])))


def atk_pick_qty(uid, key):
    c, st = mine(uid), ATK.get(uid)
    if not c or not st:
        return menu(uid)
    free = atk_free(c, st, key)
    nums = [str(n) for n in (1, 5, 10, 50, 100, 500, 1000, 5000, 10000) if n < free]
    rows = [["25%", "50%", "100%"]] + chunk(nums[:6], 3)
    ask(uid, "چند تا از «%s» بفرستی؟\n(موجود آزاد: %s) — دکمه بزن یا عدد بنویس" % (U[key]["name"], m(free)),
        lambda t: atk_qty_do(uid, key, t), rows)


def atk_qty_do(uid, key, t):
    c, st = mine(uid), ATK.get(uid)
    if not c or not st:
        return menu(uid)
    free = atk_free(c, st, key)
    raw = en_digits(t).strip()
    v = num(raw.replace("%", "").replace("٪", ""))
    if not v or v <= 0:
        tell(uid, "❌ عدد نامعتبر.")
        return atk_pick_qty(uid, key)
    q = max(1, int(free * min(v, 100.0) / 100.0)) if raw.endswith(("%", "٪")) else int(v)
    q = min(q, free)
    st["sent"][key] = st["sent"].get(key, 0) + q
    atk_hub(uid, "✅ %s × %s اضافه شد." % (U[key]["name"], m(q)))


def atk_go(uid):
    c, st = mine(uid), ATK.get(uid)
    if not c or not st:
        return menu(uid)
    if frozen(uid) or war_blocked(uid, "conv", WAR_ROWS):
        return
    iso = st["iso"]
    if ceasefire_between(c["iso"], iso):
        ATK.pop(uid, None)
        return back_to(uid, "🕊 بین شما و این کشور آتش‌بس موقت سازمان ملل برقراره؛ حمله ممکن نیست.", WAR_ROWS)
    d = C(iso)
    if not d or not d["alive"] or d["iso"] == c["iso"]:
        ATK.pop(uid, None)
        return back_to(uid, "❌ هدف معتبر نیست.", WAR_ROWS)
    if d["owner"] and not at_war(c["iso"], iso):
        ATK.pop(uid, None)
        return back_to(uid, "❌ با این کشور در جنگ نیستی.", WAR_ROWS)
    if d["owner"] and d["prot"] > now():
        ATK.pop(uid, None)
        return back_to(uid, "🛡 این کشور تا %s دیگه تحت حفاظته." % dur(d["prot"] - now()), WAR_ROWS)
    if c["cd"] > now():
        return back_to(uid, "⏱ نیروهات هنوز آماده نیستن (%s)." % dur(c["cd"] - now()), WAR_ROWS)
    sent = {k: min(q, c["units"].get(k, 0)) for k, q in st["sent"].items() if k in U}
    sent = {k: q for k, q in sent.items() if q > 0}
    if not sent or sent_atk(sent) <= 0:
        return atk_hub(uid, "❌ اول نیرو انتخاب کن.")
    note = ""
    planes = sum(q for k, q in sent.items() if U[k]["cat"] in ("fighter", "bomber", "heli", "drone"))
    bombs = [k for k in sent if U[k]["cat"] == "bomb"]
    tot = sum(sent[k] for k in bombs)
    if tot > planes * 8:                       # هر هواپیما حداکثر ۸ بسته بمب می‌بره
        for k in bombs:
            sent[k] = int(sent[k] * planes * 8 / tot) if tot else 0
        sent = {k: q for k, q in sent.items() if q > 0}
        note = "ℹ️ تعداد بمب‌ها به ظرفیت هواپیماها (×۸) کم شد.\n"
        if not sent:
            return atk_hub(uid, "❌ بدون هواپیما نمی‌شه بمب انداخت.")
    mode = force_mode(sent)
    defender = d["owner"]
    prov0, att0, m0 = d["prov"], c["prov"], d["money"]
    res, la, ld = resolve_attack(c, d, mode, sent)
    cap = capture(c, d, res["captured"]) if (mode == "ground" and res["win"]) else None
    c["cd"] = now() + ATTACK_COOLDOWN
    c["prot"] = 0
    ATK.pop(uid, None)
    detail = battle_text(c, d, mode, res, la, ld, cap, sent, prov0, att0)
    kind = atk_kind(sent, mode)
    text = battle_report(kind, c, d, res, la, ld, cap, sent, m0, prov0)
    quest_add(c, "attack")
    xp_add(c, 10 + (25 if res["win"] else 0))
    announce(text, cat="atk_" + kind, iso=(c["iso"], iso))
    text = text + "\n\n" + detail
    if defender and defender != uid:
        tell(defender, "🚨 %s به کشورت حمله کرد!\n\n%s" % (cname(c), text))
    back_to(uid, note + text, WAR_ROWS)


def loss_text(lost):
    agg = {}
    for k, n in lost.items():
        agg[U[k]["cat"]] = agg.get(U[k]["cat"], 0) + n
    return "، ".join("%s %s" % (CAT_LABEL[cat], m(n)) for cat, n in agg.items()) or "ندارد"


def battle_text(att, de, mode, res, la, ld, cap, sent, de_prov0, att_prov0):
    L = [MODE_NAME[mode], "━━━━━━━━━━━━━━━━━", "⚔️ مهاجم: %s" % cname(att), "🛡 مدافع: %s" % cname(de), "",
         "💥 قدرت حمله: %s" % m(res["A"]), "🛡 قدرت دفاع: %s" % m(res["D"])]
    if res["inter"] > 0:
        L.append("🛰 رهگیری پدافند: %d٪" % int(res["inter"] * 100))
    L += ["", "🎖 نیروهای اعزامی:"] + force_lines(sent, 8) + [""]
    if mode == "ground":
        if res["win"] and cap:
            n, loot, fell = cap
            L += ["🏆 نتیجه: پیروزی مهاجم!",
                  "🗺 فتح %d استان از %d استان %s (باقی‌مانده: %d)" % (n, de_prov0, cname(de), max(0, de_prov0 - n)),
                  "📈 قلمرو %s: از %d به %d استان رسید" % (cname(att), att_prov0, att["prov"]),
                  "💰 غنیمت: %s M$" % m(loot)]
            if fell:
                L.append("💀 %s به‌طور کامل سقوط کرد!" % cname(de))
        elif res["R"] <= 0.9:
            L += ["🏁 نتیجه: ❌ حمله دفع شد؛ مهاجم شکست خورد.", "🗺 فتح: 0 استان از %d استان %s" % (de_prov0, cname(de))]
        else:
            L += ["🏁 نتیجه: ⚖️ نبرد بی‌نتیجه ماند.", "🗺 فتح: 0 استان از %d استان %s" % (de_prov0, cname(de))]
    else:
        L += ["🏁 نتیجه: " + ("💥 ضربه‌ی مؤثر" if res["win"] else "🛡 بیشتر حمله رهگیری/دفع شد"),
              "📉 خسارت به مدافع: %d٪" % int(res["dmg"] * 100),
              "🗺 استان‌ها: ضربه‌ی غیرزمینی؛ فتح 0 از %d استان %s" % (de_prov0, cname(de))]
    L += ["", "☠️ تلفات مهاجم: " + loss_text(la), "☠️ تلفات مدافع: " + loss_text(ld), "", "#جنگ"]
    return "\n".join(L)



@route(B_NUKE)
def r_nuke(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid) or war_blocked(uid, "nuke", WAR_ROWS):
        return
    owned = [k for k in NUKE if c["units"].get(k, 0) > 0]
    if not owned:
        return back_to(uid, "☢️ کلاهک هسته‌ای نداری! از «فروشگاه ← هسته‌ای» بخر (نیاز به تکنولوژی ۶).", WAR_ROWS)
    pick_country(uid, "☢️ هدف حمله‌ی هسته‌ای؟ (نیازمند تأیید ادمین)", lambda iso: nuke_pick(uid, iso, owned),
                 lambda x: x["alive"] and x["iso"] != c["iso"]
                 and ((x["owner"] and at_war(c["iso"], x["iso"])) or not x["owner"]))


def nuke_pick(uid, iso, owned):
    ask(uid, "کدوم کلاهک؟", lambda t: nuke_req(uid, iso, t), [[U[k]["name"]] for k in owned])


def nuke_req(uid, iso, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    key = next((k for k in NUKE if squash(U[k]["name"]) == squash(t) and c["units"].get(k, 0) > 0), None)
    if not key:
        return back_to(uid, "❌ انتخاب نامعتبر.", WAR_ROWS)
    if any(r["type"] == "nuke" and r["uid"] == uid for r in DB["requests"]):
        return back_to(uid, "⏳ یک درخواست هسته‌ای در انتظار داری.", WAR_ROWS)
    r = {"id": nid(), "type": "nuke", "uid": uid, "att": c["iso"], "de": iso, "key": key, "t": now()}
    DB["requests"].append(r)
    notify_admins(req_text(r), [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]], [A_PANEL]])
    back_to(uid, "☢️ درخواستت برای ادمین ارسال شد؛ منتظر تأیید بمون.", WAR_ROWS)


def nuke_text(att, de, key, res):
    return nuke_report(att, de, key, res)


@route(B_PEACE)
def r_peace(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_country(uid, "🕊 به کدوم کشور پیشنهاد صلح می‌دی؟", lambda iso: peace_send(uid, iso),
                 lambda x: x["owner"] and x["alive"] and at_war(c["iso"], x["iso"]))


def peace_send(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or not at_war(c["iso"], iso):
        return back_to(uid, "❌ پیشنهاد صلح ممکن نیست.", WAR_ROWS)
    p = {"id": nid(), "type": "peace", "a": c["iso"], "b": iso, "t": now()}
    DB["props"].append(p)
    send_prop(p, "🕊 %s پیشنهاد صلح داده.\nمی‌پذیری؟" % cname(c))
    back_to(uid, "🕊 پیشنهاد صلح برای %s ارسال شد." % cname(d), WAR_ROWS)


@route(B_WARS)
def r_wars(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = []
    for a, b, t0 in DB["wars"]:
        if c["iso"] in (a, b):
            o = C(b if a == c["iso"] else a)
            if o:
                L.append("⚔️ %s — %s پیش | 💪 %s | 🗺 %d" % (cname(o), dur(now() - t0), m(power(o)), o["prov"]))
    back_to(uid, "📊 جنگ‌های من\n\n" + ("\n".join(L) if L else "🕊 در صلح هستی."), WAR_ROWS)


# ───── دیپلماسی ─────
@route(B_DIP)
def r_dip(uid):
    if not mine(uid):
        return no_country(uid)
    back_to(uid, "🕊 دیپلماسی و تجارت", DIP_ROWS)


def peers(c):
    return lambda x: x["alive"] and x["owner"] and x["iso"] != c["iso"] and not at_war(c["iso"], x["iso"])


def send_prop(p, text):
    b = C(p["b"])
    if b and b["owner"]:
        tell(b["owner"], text, [["✅ قبول %d" % p["id"], "❌ رد پیشنهاد %d" % p["id"]], [B_BACK]])


@route(B_TRADE)
def r_trade(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid):
        return
    pick_country(uid, "🤝 با کدوم کشور معامله می‌کنی؟", lambda iso: trade_give(uid, iso), peers(c))


def trade_give(uid, iso):
    c = mine(uid)
    if not c:
        return no_country(uid)
    pick_item(uid, "📤 چی می‌دی؟", lambda give: trade_get(uid, iso, give), owner=c)


def trade_get(uid, iso, give):
    pick_item(uid, "📥 در برابر چی می‌خوای؟", lambda get: trade_send(uid, iso, give, get))


def trade_send(uid, iso, give, get):
    c, d = mine(uid), C(iso)
    if not c or not d or not d["owner"] or not has_item(c, give) or sanctioned_between(c["iso"], iso):
        return back_to(uid, "❌ معامله ممکن نیست (تحریم یا کمبود موجودی).", DIP_ROWS)
    p = {"id": nid(), "type": "deal", "a": c["iso"], "b": iso, "give": list(give), "get": list(get), "t": now()}
    DB["props"].append(p)
    send_prop(p, "🤝 %s پیشنهاد معامله داده:\n📤 می‌ده: %s\n📥 می‌خواد: %s" % (cname(c), item_txt(give), item_txt(get)))
    back_to(uid, "🤝 پیشنهاد معامله برای %s ارسال شد." % cname(d), DIP_ROWS)


@route(B_ALLY)
def r_ally(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid):
        return
    ok = peers(c)
    pick_country(uid, "🛡 به کدوم کشور پیشنهاد ائتلاف می‌دی؟", lambda iso: ally_send(uid, iso),
                 lambda x: ok(x) and not is_ally(c["iso"], x["iso"]))


def ally_send(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or not d["owner"] or is_ally(c["iso"], iso):
        return back_to(uid, "❌ پیشنهاد ممکن نیست.", DIP_ROWS)
    p = {"id": nid(), "type": "ally", "a": c["iso"], "b": iso, "t": now()}
    DB["props"].append(p)
    send_prop(p, "🛡 %s پیشنهاد ائتلاف داده.\n(متحدان از حمله‌ی هم جلوگیری می‌کنن، درآمد بیشتر می‌گیرن و در دفاع کمک می‌کنن)" % cname(c))
    back_to(uid, "🛡 پیشنهاد ائتلاف برای %s ارسال شد." % cname(d), DIP_ROWS)


@route(B_BREAK)
def r_break(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    al = pact_allies(c["iso"])
    if not al:
        return back_to(uid, "💔 پیمان دوجانبه‌ای نداری (برای اتحاد از بخش «اتحاد» خارج شو).", DIP_ROWS)
    pick_country(uid, "💔 ائتلاف با کدوم کشور لغو بشه؟", lambda iso: break_do(uid, iso), lambda x: x["iso"] in al)


def break_do(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or iso not in pact_allies(c["iso"]):
        return back_to(uid, "❌ ممکن نیست.", DIP_ROWS)
    DB["allies"] = [a for a in DB["allies"] if {c["iso"], iso} != set(a)]
    announce("💔 پایان ائتلاف\n%s و %s ائتلافشان را لغو کردند.\n#دیپلماسی" % (cname(c), cname(d)))
    notify_country(iso, "💔 %s ائتلاف رو لغو کرد." % cname(c))
    back_to(uid, "💔 ائتلاف لغو شد.", DIP_ROWS)


@route(B_AID)
def r_aid(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    return r_bk_tx(uid)
    pick_country(uid, "🎁 به کدوم کشور کمک مالی می‌کنی؟", lambda iso: aid_amount(uid, iso), peers(c))


def aid_amount(uid, iso):
    ask(uid, "💵 مبلغ کمک (M$)؟ دکمه بزن یا عدد بنویس.", lambda t: aid_do(uid, iso, t),
        [["100", "500", "1000"], ["5000", "10000", "50000"]])


def aid_do(uid, iso, t):
    c, d = mine(uid), C(iso)
    v = num(t)
    if not c or not d or not v or v <= 0 or v > c["money"]:
        return back_to(uid, "❌ مبلغ نامعتبر یا پول کافی نیست.", DIP_ROWS)
    c["money"] -= v
    d["money"] += v
    announce("🎁 کمک مالی\n%s مبلغ %s M$ به %s کمک کرد.\n#دیپلماسی" % (cname(c), m(v), cname(d)))
    notify_country(iso, "🎁 %s مبلغ %s M$ به خزانه‌ات واریز کرد!" % (cname(c), m(v)))
    back_to(uid, "✅ کمک مالی ارسال شد.", DIP_ROWS)


@rx_route(r"^\W*قبول\s*(\d+)\s*$")
def rx_accept(uid, mt):
    pid = int(mt.group(1))
    p = next((x for x in DB["props"] if x["id"] == pid), None)
    c = mine(uid)
    if not p or not c or p["b"] != c["iso"]:
        return menu(uid, "❓ پیشنهاد پیدا نشد یا منقضی شده.")
    DB["props"].remove(p)
    a = C(p["a"])
    if not a or not a["alive"] or not a["owner"]:
        return menu(uid, "❌ فرستنده‌ی پیشنهاد دیگه وجود نداره.")
    if p["type"] == "peace":
        end_war(a["iso"], c["iso"])
        announce("🕊 اعلام صلح!\n%s و %s پایان جنگ را اعلام کردند.\n#صلح" % (cname(a), cname(c)), iso=(a["iso"], c["iso"]))
        notify_country(a["iso"], "🕊 %s صلح رو پذیرفت." % cname(c))
        menu(uid, "🕊 صلح برقرار شد.")
    elif p["type"] == "ally":
        if not is_ally(a["iso"], c["iso"]):
            DB["allies"].append([a["iso"], c["iso"]])
        announce("🛡 پیمان ائتلاف!\n%s و %s متحد شدند.\n#ائتلاف" % (cname(a), cname(c)), iso=(a["iso"], c["iso"]))
        notify_country(a["iso"], "🛡 %s ائتلاف رو پذیرفت." % cname(c))
        menu(uid, "🛡 ائتلاف برقرار شد.")
    elif p["type"] == "deal":
        give, get = tuple(p["give"]), tuple(p["get"])
        if not has_item(a, give) or not has_item(c, get):
            notify_country(a["iso"], "❌ معامله به خاطر کمبود موجودی لغو شد.")
            return menu(uid, "❌ معامله به خاطر کمبود موجودی یکی از طرفین لغو شد.")
        bad = next((U[it[0]]["name"] for s_, d_, it in ((a, c, give), (c, a, get))
                    if it[0] != "money" and not deal_ok(s_, d_, it[0])), None)
        if bad or sanctioned_between(a["iso"], c["iso"]):
            notify_country(a["iso"], "❌ معامله لغو شد: %s" % (("گیرنده‌ی «%s» مجوز لازم رو نداره." % bad) if bad else "تحریم بین دو کشور"))
            return menu(uid, "❌ معامله لغو شد: %s" % (("برای «%s» مجوز تسلیحاتی لازمه." % bad) if bad else "تحریم بین دو کشور"))
        move_item(a, c, give)
        move_item(c, a, get)
        quest_add(a, "deal")
        quest_add(c, "deal")
        announce("🤝 معامله‌ی بین‌المللی\n%s ⇄ %s\n📤 %s\n📥 %s\n#تجارت" % (cname(a), cname(c), item_txt(give), item_txt(get)),
                 iso=(a["iso"], c["iso"]))
        notify_country(a["iso"], "✅ %s معامله رو پذیرفت." % cname(c))
        menu(uid, "✅ معامله انجام شد.")
    elif p["type"] == "union":
        un = DB["unions"].get(str(p.get("un")))
        if not un:
            return menu(uid, "❌ این اتحاد دیگه وجود نداره.")
        ok, why = un_can_join(un, c)
        if not ok:
            return menu(uid, "❌ " + why)
        un_join(un, c)
        menu(uid, "🛡 به اتحاد «%s» پیوستی!" % un_label(un))
    elif p["type"] == "unionreq":
        un = un_get(c)
        if not un or un_role(un, c["iso"]) == "member" or str(un["id"]) != str(p.get("un")):
            return menu(uid, "❌ این درخواست دیگه معتبر نیست.")
        ok, why = un_can_join(un, a)
        if not ok:
            return menu(uid, "❌ " + why)
        un_join(un, a)
        notify_country(a["iso"], "🛡 درخواست عضویتت در اتحاد «%s» پذیرفته شد!" % un_label(un))
        menu(uid, "✅ %s به اتحاد پیوست." % cname(a))
    elif p["type"] in ("lic", "licreq"):
        ok, txt = lic_grant_accept(a, c, p)
        notify_country(a["iso"], txt if not ok else "✅ %s مجوز رو پذیرفت." % cname(c))
        menu(uid, txt)


@rx_route(r"^\W*رد\s*پیشنهاد\s*(\d+)\s*$")
def rx_decline(uid, mt):
    pid = int(mt.group(1))
    p = next((x for x in DB["props"] if x["id"] == pid), None)
    c = mine(uid)
    if not p or not c or p["b"] != c["iso"]:
        return menu(uid, "❓ پیشنهاد پیدا نشد.")
    DB["props"].remove(p)
    notify_country(p["a"], "❌ %s پیشنهادت رو رد کرد." % cname(c))
    menu(uid, "❌ پیشنهاد رد شد.")


# ───── بیانیه و اطلاعات ─────
def r_world(uid):
    cs = sorted(DB["countries"].values(), key=lambda c: -power(c))
    L = ["🌐 وضعیت جهان", ""]
    if DB["wars"]:
        L.append("⚔️ جنگ‌های فعال:")
        for a, b, _t in DB["wars"]:
            if C(a) and C(b):
                L.append("  %s ⚔️ %s" % (cname(C(a)), cname(C(b))))
    else:
        L.append("🕊 هیچ جنگ فعالی نیست.")
    if DB["allies"]:
        L.append("\n🛡 ائتلاف‌ها:")
        for a, b in DB["allies"]:
            if C(a) and C(b):
                L.append("  %s 🤝 %s" % (cname(C(a)), cname(C(b))))
    L.append("\n🏛 کشورهای دارای رهبر:")
    owned = [c for c in cs if c["owner"] and c["alive"]]
    for c in owned:
        L.append("%s — 👤 %s | 💪 %s | 🗺 %d" % (cname(c), c["leader"], m(power(c)), c["prov"]))
    if not owned:
        L.append("  —")
    free = [cname(c) for c in cs if c["alive"] and not c["owner"]]
    if free:
        L.append("\n🆓 آزاد (%d کشور): %s%s" % (len(free), "، ".join(free[:25]), " ..." if len(free) > 25 else ""))
    if DB["unions"]:
        L.append("\n🛡 اتحادها:")
        for un in sorted(DB["unions"].values(), key=un_power, reverse=True)[:8]:
            L.append("  %s — 👥 %d | 💪 %s" % (un_label(un), len(un_members(un)), m(un_power(un))))
    if sanc_active():
        L.append("\n🚫 تحریم‌های فعال: %d" % len(sanc_active()))
    if DB["wonders"]:
        L.append("\n🏛 شگفتی‌های ساخته‌شده: " + "، ".join("%s (%s)" % (WD[k]["name"], cname(C(v))) for k, v in DB["wonders"].items() if C(v)))
    dead = [cname(c) for c in cs if not c["alive"]]
    if dead:
        L.append("\n💀 سقوط‌کرده: " + "، ".join(dead))
    tell(uid, "\n".join(L), main_rows(uid))


def r_news(uid):
    items = DB["log"][-10:]
    L = ["🗞 آخرین اخبار جهان", ""]
    if not items:
        L.append("هنوز خبری نیست.")
    for it in reversed(items):
        parts = [p for p in it["text"].split("\n") if p.strip()][:2]
        L.append("• " + " — ".join(parts))
    L.append("\n📢 همه‌ی اخبار: @" + CHANNEL_USERNAME)
    tell(uid, "\n".join(L), main_rows(uid))


# ═════════════ پنل ادمین ═════════════

# ═════════════ پشتیبان‌گیری و بازیابی امن ═════════════
MAX_RECOVERY_BYTES = 18 * 1024 * 1024


def _validate_game_db(candidate):
    """فقط snapshot کامل دیتابیس بازی پذیرفته می‌شود؛ متن لاگ به‌تنهایی کافی نیست."""
    if not isinstance(candidate, dict):
        raise ValueError("ساختار فایل JSON نیست.")
    required = ("settings", "users", "countries")
    if any(k not in candidate for k in required):
        raise ValueError("فایل، snapshot کامل بازی نیست؛ settings/users/countries ناقص است.")
    if not all(isinstance(candidate[k], dict) for k in required):
        raise ValueError("ساختار بخش‌های اصلی دیتابیس نامعتبر است.")
    if not candidate["countries"]:
        raise ValueError("فهرست کشورها خالی است.")
    for iso, country in candidate["countries"].items():
        if not isinstance(country, dict) or not isinstance(country.get("units"), dict):
            raise ValueError("اطلاعات کشور %s ناقص است." % iso)
        if "money" not in country or "owner" not in country:
            raise ValueError("اطلاعات مالی/مالکیت کشور %s ناقص است." % iso)
    return True


def _extract_recovery_db(raw):
    """پذیرش JSON مستقیم یا snapshot مشخص‌شده در لاگ؛ از حدس زدن دارایی‌ها خودداری می‌کند."""
    text_data = raw.decode("utf-8-sig", errors="replace") if isinstance(raw, bytes) else str(raw)
    text_data = text_data.strip()

    # حالت اول: فایل پشتیبان JSON که خود ربات صادر می‌کند
    try:
        obj = json.loads(text_data)
        _validate_game_db(obj)
        return obj, "فایل پشتیبان JSON"
    except (ValueError, json.JSONDecodeError, TypeError):
        pass

    # حالت دوم: snapshot چندبخشی؛ برای جلوگیری از بریده‌شدن خطوط طولانی در لاگ میزبان
    parts_by_id = {}
    part_re = re.compile(r"WW_STATE_SNAPSHOT_PART:([A-Za-z0-9_-]+):(\d+):(\d+):([A-Za-z0-9+/=]+)")
    for line in text_data.splitlines():
        match = part_re.search(line)
        if match:
            sid, index, total, payload = match.groups()
            index, total = int(index), int(total)
            if 1 <= index <= total <= 10000:
                group = parts_by_id.setdefault(sid, {"total": total, "parts": {}})
                if group["total"] == total:
                    group["parts"][index] = payload
    for sid, group in reversed(list(parts_by_id.items())):
        if len(group["parts"]) == group["total"] and all(i in group["parts"] for i in range(1, group["total"] + 1)):
            try:
                packed = base64.b64decode("".join(group["parts"][i] for i in range(1, group["total"] + 1)), validate=True)
                decoded = zlib.decompress(packed).decode("utf-8")
                obj = json.loads(decoded)
                _validate_game_db(obj)
                return obj, "snapshot چندبخشی Railway"
            except Exception as exc:
                raise ValueError("snapshot چندبخشی %s خراب است: %s" % (sid, exc))

    # حالت سوم: snapshot فشرده تک‌خطی که در صورت وجود در لاگ درج شده باشد
    marker = "WW_STATE_SNAPSHOT_BASE64:"
    for line in reversed(text_data.splitlines()):
        if marker in line:
            encoded = line.split(marker, 1)[1].strip()
            try:
                packed = base64.b64decode(encoded, validate=True)
                decoded = zlib.decompress(packed).decode("utf-8")
                obj = json.loads(decoded)
                _validate_game_db(obj)
                return obj, "snapshot فشرده داخل لاگ"
            except Exception as exc:
                raise ValueError("نشانگر snapshot در لاگ پیدا شد، اما داده خراب یا ناقص است: %s" % exc)

    # حالت چهارم: snapshot JSON تک‌خطی با نشانگر صریح
    marker = "WW_STATE_JSON:"
    for line in reversed(text_data.splitlines()):
        if marker in line:
            try:
                obj = json.loads(line.split(marker, 1)[1].strip())
                _validate_game_db(obj)
                return obj, "snapshot JSON داخل لاگ"
            except Exception as exc:
                raise ValueError("snapshot داخل لاگ قابل خواندن نیست: %s" % exc)

    raise ValueError(
        "در این فایل فقط لاگ عملیاتی دیده شد و snapshot کامل دیتابیس وجود ندارد. "
        "لاگ Railway معمولاً پول، منابع، مالکیت کشورها و تمام وضعیت بازی را ثبت نمی‌کند؛ "
        "برای بازیابی دقیق، فایل JSON پشتیبان ربات را بارگذاری کن."
    )


def _normalize_imported_db(candidate):
    """اعمال پیش‌فرض‌های نسخه فعلی بدون بازنویسی مقادیر ذخیره‌شده."""
    base = new_db()
    for key, value in base.items():
        candidate.setdefault(key, value)
    if not isinstance(candidate.get("settings"), dict):
        raise ValueError("تنظیمات دیتابیس نامعتبر است.")
    for key, value in base["settings"].items():
        candidate["settings"].setdefault(key, value)
    if isinstance(candidate.get("wonders"), list) or not isinstance(candidate.get("wonders"), dict):
        candidate["wonders"] = {}
    for country in candidate["countries"].values():
        ensure(country)
    if candidate["settings"].get("seed_v", 0) < SEED_V:
        for iso, fa, en, tier in COUNTRIES:
            if iso not in candidate["countries"]:
                candidate["countries"][iso] = make_country(iso, fa, en, tier)
        candidate["settings"]["seed_v"] = SEED_V
    init_market_for = candidate.get("market")
    if not isinstance(init_market_for, dict):
        candidate["market"] = {}
    # init_market به DB سراسری وابسته است؛ موقتاً دیتابیس مقصد را جایگزین می‌کنیم.
    return candidate


def send_document(chat, filename, content, caption=""):
    data = {"chat_id": chat, "caption": caption}
    files = {"document": (filename, content, "application/json")}
    return api_form("sendDocument", data, files, read_timeout=60)


@route(A_LOGSNAP, admin=True)
def a_log_snapshot(uid):
    try:
        raw = json.dumps(DB, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        packed = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
        sid = "%x" % int(now())
        chunks = [packed[i:i + 2800] for i in range(0, len(packed), 2800)]
        print("[WW_STATE_SNAPSHOT_BEGIN:%s:%d]" % (sid, len(chunks)))
        for index, chunk_data in enumerate(chunks, 1):
            print("WW_STATE_SNAPSHOT_PART:%s:%d:%d:%s" % (sid, index, len(chunks), chunk_data))
        print("[WW_STATE_SNAPSHOT_END:%s]" % sid)
        tell(uid,
             "✅ snapshot کامل در لاگ‌های Railway ثبت شد.\n"
             "حالا از Deployments → View Logs متن لاگ را کپی کن، به فایل .txt تبدیل کن "
             "و از گزینه «📥 بازیابی از فایل/لاگ» بارگذاری کن.\n"
             "شناسه snapshot: %s | بخش‌ها: %d" % (sid, len(chunks)),
             ADMIN_ROWS)
    except Exception as exc:
        print("log snapshot error:", repr(exc))
        tell(uid, "❌ ثبت snapshot در لاگ ناموفق بود: " + str(exc)[:250], ADMIN_ROWS)


@route(A_EXPORT, admin=True)
def a_export(uid):
    try:
        payload = json.dumps(DB, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        result = send_document(uid, "worldwar-backup-%s.json" % stamp, io.BytesIO(payload),
                               "📦 نسخه پشتیبان کامل بازی\nکشورها: %d | کاربران: %d\nاین فایل را در جای امن نگه دار."
                               % (len(DB.get("countries", {})), len(DB.get("users", {}))))
        if result.get("ok"):
            tell(uid, "✅ فایل پشتیبان کامل ارسال شد.", ADMIN_ROWS)
        else:
            tell(uid, "⚠️ ارسال فایل ناموفق بود.", ADMIN_ROWS)
    except Exception as exc:
        print("backup export error:", repr(exc))
        tell(uid, "❌ ساخت/ارسال پشتیبان ناموفق بود: " + str(exc)[:250], ADMIN_ROWS)


@route(A_RECOVERY, admin=True)
def a_recovery(uid):
    IMPORT_WAIT.add(uid)
    back_to(uid,
        "📥 فایل بازیابی را همین‌جا ارسال کن.\n\n"
        "فرمت قابل قبول:\n"
        "• فایل JSON پشتیبان کامل که از همین ربات گرفته‌ای\n"
        "• فایل لاگی که واقعاً شامل نشانگر snapshot کامل باشد\n\n"
        "⚠️ لاگ عادی Railway معمولاً برای بازسازی پول، منابع، ارتش و مالکیت کشورها کافی نیست. "
        "قبل از جایگزینی، فایل بررسی می‌شود و از دیتابیس فعلی نسخه احتیاطی ساخته می‌شود.",
        ADMIN_ROWS)


def _restore_from_upload(uid, document):
    global DB
    IMPORT_WAIT.discard(uid)
    file_id = (document or {}).get("file_id")
    name = (document or {}).get("file_name") or "uploaded-file"
    size = int((document or {}).get("file_size") or 0)
    if not file_id:
        return tell(uid, "❌ فایل تلگرام شناسه معتبر ندارد.", ADMIN_ROWS)
    if size and size > MAX_RECOVERY_BYTES:
        return tell(uid, "❌ حجم فایل بیشتر از سقف ۱۸ مگابایت است.", ADMIN_ROWS)
    try:
        meta = api("getFile", {"file_id": file_id}).get("result") or {}
        remote_path = meta.get("file_path")
        if not remote_path:
            raise ValueError("مسیر فایل از تلگرام دریافت نشد.")
        url = "%s/file/bot%s/%s" % (API_HOST, TOKEN, remote_path)
        response = _session().get(url, timeout=(10, 60))
        response.raise_for_status()
        raw = response.content
        if len(raw) > MAX_RECOVERY_BYTES:
            raise ValueError("حجم فایل دانلودشده بیشتر از ۱۸ مگابایت است.")
        candidate, source_kind = _extract_recovery_db(raw)
        _validate_game_db(candidate)

        # نگهداری نسخه احتیاطی پیش از هر تغییری
        backup_path = DATA_FILE + ".pre_restore_" + str(int(now()))
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(DB, f, ensure_ascii=False)

        previous = DB
        try:
            candidate = _normalize_imported_db(candidate)
            DB = candidate
            init_market()
            for admin_id in ADMIN_IDS:
                if admin_id not in DB["settings"]["admins"]:
                    DB["settings"]["admins"].append(admin_id)
            DB["settings"]["admins"] = list(dict.fromkeys(DB["settings"]["admins"]))
            DB["settings"]["channel"] = DB["settings"].get("channel") or CHANNEL
            save()
        except Exception:
            DB = previous
            raise

        # زمان مرجع بازی پس از بازیابی، برای جلوگیری از جهش زمانی نامحدود
        owned = sum(1 for c in DB["countries"].values() if c.get("owner") and c.get("alive"))
        tell(uid,
             "✅ بازیابی با موفقیت انجام شد.\n"
             "📄 منبع: %s\n🌍 کشورها: %s\n👥 کاربران: %s\n"
             "🏳️ کشورهای دارای رهبر: %s\n🛟 نسخه قبلی: %s\n\n"
             "دارایی‌ها و تاریخچه از snapshot خوانده شدند؛ هیچ مقدار حدسی ساخته نشد."
             % (source_kind, len(DB["countries"]), len(DB["users"]), owned, os.path.basename(backup_path)),
             ADMIN_ROWS)
        print("[RECOVERY] restored by admin=%s source=%s file=%s countries=%d users=%d"
              % (uid, source_kind, name[:100], len(DB["countries"]), len(DB["users"])))
    except Exception as exc:
        print("recovery import error:", repr(exc))
        tell(uid, "❌ بازیابی انجام نشد؛ دیتابیس فعلی دست‌نخورده ماند.\n" + str(exc)[:900], ADMIN_ROWS)


def on_document(chat, msg):
    uid = str(chat)
    u = user(uid, chat)
    u["seen"] = now()
    note_user(uid, msg.get("from") or {})
    if not is_admin(uid):
        return tell(uid, "⛔ بارگذاری فایل بازیابی فقط برای ادمین مجاز است.")
    if uid not in IMPORT_WAIT:
        return tell(uid, "برای دریافت فایل، ابتدا از پنل ادمین گزینه «📥 بازیابی از فایل/لاگ» را بزن.")
    return _restore_from_upload(uid, msg.get("document") or {})


@route(B_ADMIN, A_PANEL, admin=True)
def a_panel(uid):
    s = DB["settings"]
    back_to(uid, "🛠 پنل ادمین\n📥 درخواست در انتظار: %d\n⏸ بازی: %s | ⚡ سرعت ×%s\n📣 کانال: %s"
            % (len(DB["requests"]), "متوقف" if s["paused"] else "فعال", s["speed"],
               "ثبت‌شده ✅" if s["channel"] else "ثبت نشده ❌"), ADMIN_ROWS)


@route(A_REQ, admin=True)
def a_requests(uid):
    reqs = DB["requests"][:8]
    if not reqs:
        return back_to(uid, "📭 درخواستی در انتظار نیست.", ADMIN_ROWS)
    rows = [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]] for r in reqs]
    back_to(uid, "\n\n".join(req_text(r) for r in reqs), rows + [[A_PANEL]])


@rx_route(r"^\W*تایید\s*(\d+)\s*$", admin=True)
def rx_approve(uid, mt):
    r = next((x for x in DB["requests"] if x["id"] == int(mt.group(1))), None)
    if not r:
        return back_to(uid, "❓ این درخواست دیگه وجود نداره.", ADMIN_ROWS)
    DB["requests"].remove(r)
    if r["type"] in EXT_REQ:
        return ext_approve(uid, r)
    if r["type"] == "country":
        c = C(r["iso"])
        if not c or not c["alive"] or c["owner"]:
            tell(r["uid"], "😕 کشور انتخابی دیگه در دسترس نیست. دوباره درخواست بده.", main_rows(r["uid"]))
            return back_to(uid, "⚠️ کشور دیگه آزاد نبود؛ درخواست حذف شد.", ADMIN_ROWS)
        assign(r["uid"], r["iso"], r["leader"])
        return back_to(uid, "✅ %s به %s واگذار شد." % (cname(c), ulabel(r["uid"])), ADMIN_ROWS)
    if r["type"] == "pack":
        c = C(r["iso"])
        if not c or not c["alive"]:
            return back_to(uid, "⚠️ کشور دیگه وجود نداره.", ADMIN_ROWS)
        pk = PK[r["pack"]]
        if pk.get("limit") and c["packs"].get(pk["key"], 0) >= pk["limit"]:
            return back_to(uid, "⚠️ این پک قبلاً فعال شده (محدودیت تعداد).", ADMIN_ROWS)
        activate_pack(r["iso"], r["pack"])
        return back_to(uid, "✅ پک «%s» برای %s فعال شد." % (pk["name"], cname(c)), ADMIN_ROWS)
    if r["type"] == "license":
        g, c = C(r["org"]), C(r["iso"])
        t_ = r["terms"]
        if not c or not c["alive"] or not g:
            return back_to(uid, "⚠️ کشور دیگه وجود نداره.", ADMIN_ROWS)
        price = float(t_.get("price", 0))
        if c["money"] < price:
            tell(r["uid"], "❌ پول کافی برای قیمت مجوز (%s M$) نداشتی؛ درخواست لغو شد." % m(price), main_rows(r["uid"]))
            return back_to(uid, "⚠️ خریدار پول کافی نداشت.", ADMIN_ROWS)
        c["money"] -= price
        l = lic_new(r["org"], r["iso"], r["scope"], t_["kind"], t_.get("qty", 0), t_.get("hours", 0), price)
        announce("🎫 مجوز تسلیحاتی صادر شد\nاز %s برای %s\n%s\n%s\n#مجوز" % (cname(g), cname(c), scope_text(l["scope"]), kind_text(l)),
                 cat="license", iso=(r["org"], r["iso"]))
        tell(r["uid"], "✅ مجوز درخواستی‌ات تأیید شد:\n" + lic_text(l), main_rows(r["uid"]))
        return back_to(uid, "✅ مجوز صادر شد.", ADMIN_ROWS)
    att, de = C(r["att"]), C(r["de"])
    res = None
    if not war_on("nuke") or (att and de and ceasefire_between(att["iso"], de["iso"])):
        tell(r["uid"], "❌ حمله‌ی هسته‌ای لغو شد (جنگ هسته‌ای غیرفعاله یا آتش‌بس برقراره).", main_rows(r["uid"]))
        return back_to(uid, "⚠️ اجرا نشد (جنگ هسته‌ای خاموشه یا آتش‌بس).", ADMIN_ROWS)
    if att and de and att["alive"] and de["alive"] and att["owner"] == r["uid"]:
        res = launch_nuke(att, de, r["key"])
    if res is None:
        tell(r["uid"], "❌ حمله‌ی هسته‌ای لغو شد (شرایط تغییر کرده).", main_rows(r["uid"]))
        return back_to(uid, "⚠️ اجرا نشد.", ADMIN_ROWS)
    text = nuke_text(att, de, r["key"], res)
    announce(text, cat="nuke", iso=(att["iso"], de["iso"]))
    tell(r["uid"], text)
    if de["owner"] != r["uid"]:
        notify_country(de["iso"], "🚨 کشورت هدف حمله‌ی هسته‌ای قرار گرفت!\n\n" + text)
    back_to(uid, "☢️ اجرا شد.", ADMIN_ROWS)


@rx_route(r"^\W*رد\s*درخواست\s*(\d+)\s*$", admin=True)
def rx_reject(uid, mt):
    r = next((x for x in DB["requests"] if x["id"] == int(mt.group(1))), None)
    if not r:
        return back_to(uid, "❓ این درخواست دیگه وجود نداره.", ADMIN_ROWS)
    DB["requests"].remove(r)
    tell(r["uid"], "❌ متأسفانه درخواستت توسط ادمین رد شد.", main_rows(r["uid"]))
    back_to(uid, "🚫 درخواست رد شد.", ADMIN_ROWS)


def assign_to(uid, tuid, iso, leader):
    c = C(iso)
    if not c or not c["alive"] or c["owner"]:
        return back_to(uid, "❌ این کشور آزاد نیست.", COUNTRY_ROWS)
    assign(tuid, iso, leader)
    back_to(uid, "✅ %s به %s واگذار شد." % (cname(c), ulabel(tuid)), COUNTRY_ROWS)


# ───── مدیریت کشورها ─────
@route(A_COUNTRIES, admin=True)
def a_countries(uid):
    back_to(uid, "🌍 مدیریت کشورها", COUNTRY_ROWS)


@route(A_ADD, admin=True)
def a_add(uid):
    ask(uid, "➕ نام فارسی کشور جدید؟", lambda fa: a_add2(uid, fa.strip()))


def a_add2(uid, fa):
    ask(uid, "کد دوحرفی انگلیسی کشور (برای پرچم، مثلاً FR):", lambda code: a_add3(uid, fa, code))


def a_add3(uid, fa, code):
    iso = re.sub(r"[^A-Za-z]", "", code).upper()[:2]
    if not fa or len(iso) != 2 or iso in DB["countries"]:
        return back_to(uid, "❌ کد نامعتبر یا تکراریه.", COUNTRY_ROWS)
    ask(uid, "سطح کشور؟ (۱ تا ۵ — ۵ = ابرقدرت)", lambda t: a_add4(uid, fa, iso, t), [["1", "2", "3", "4", "5"]])


def a_add4(uid, fa, iso, t):
    v = num(t)
    if v is None or int(v) not in (1, 2, 3, 4, 5):
        return back_to(uid, "❌ سطح نامعتبر.", COUNTRY_ROWS)
    DB["countries"][iso] = make_country(iso, fa, fa, int(v))
    back_to(uid, "✅ %s اضافه شد." % cname(DB["countries"][iso]), COUNTRY_ROWS)


@route(A_DEL, admin=True)
def a_del(uid):
    pick_country(uid, "🗑 کدوم کشور حذف بشه؟", lambda iso: a_del2(uid, iso))


def a_del2(uid, iso):
    ask(uid, "⚠️ %s برای همیشه حذف بشه؟" % cname(C(iso)), lambda t: a_del3(uid, iso, t), [["✅ بله", "❌ خیر"]])


def a_del3(uid, iso, t):
    c = C(iso)
    if "بله" not in t or not c:
        return back_to(uid, "لغو شد.", COUNTRY_ROWS)
    if c["owner"]:
        free_country(iso)
    remove_links(iso)
    del DB["countries"][iso]
    back_to(uid, "🗑 حذف شد.", COUNTRY_ROWS)


@route(A_FREE, admin=True)
def a_free(uid):
    pick_country(uid, "🔓 کشور چه کسی آزاد بشه؟", lambda iso: (free_country(iso), back_to(uid, "🔓 آزاد شد.", COUNTRY_ROWS)),
                 lambda c: c["owner"])


@route(A_REVIVE, admin=True)
def a_revive(uid):
    pick_country(uid, "♻️ کدوم کشور احیا بشه؟", lambda iso: a_revive2(uid, iso), lambda c: not c["alive"])


def a_revive2(uid, iso):
    c = C(iso)
    DB["countries"][iso] = make_country(iso, c["fa"], c["en"], c["tier"])
    announce("♻️ %s دوباره متولد شد و آماده‌ی رهبر جدید است!\n#احیا" % cname(DB["countries"][iso]))
    back_to(uid, "♻️ احیا شد.", COUNTRY_ROWS)


@route(A_GIVE, admin=True)
def a_give(uid):
    pick_user(uid, "🎁 کشور به کدوم کاربر واگذار بشه؟", lambda tuid: a_give2(uid, tuid))


def a_give2(uid, tuid):
    pick_country(uid, "کدوم کشور؟", lambda iso: a_give3(uid, tuid, iso), lambda c: c["alive"] and not c["owner"])


def a_give3(uid, tuid, iso):
    ask_text(uid, "🎖 لقب رهبر؟", LEADER_TITLES, lambda t: assign_to(uid, tuid, iso, leader_name(tuid, t) or "رهبر"),
             "✍️ اسم/لقب رهبر رو بنویس:", per_row=2)


# ───── بازیکنان ─────
@route(A_PLAYERS, admin=True)
def a_players(uid):
    back_to(uid, "👥 مدیریت بازیکنان\nتعداد کاربران: %d" % len(DB["users"]), PLAYER_ROWS)


@route(A_LIST, admin=True)
def a_list(uid):
    us = sorted(DB["users"].items(), key=lambda p: -p[1].get("seen", 0))[:40]
    L = ["📋 بازیکنان (۴۰ نفر آخر)", ""]
    for i, x in us:
        c = C(x["country"]) if x.get("country") else None
        L.append("• %s — %s%s%s" % (ulabel(i), cname(c) if c else "بدون کشور",
                                   " 🚫" if x.get("banned") else "", " 👑" if is_admin(i) else ""))
    back_to(uid, "\n".join(L), PLAYER_ROWS)


@route(A_BAN, admin=True)
def a_ban(uid):
    pick_user(uid, "🚫 کدوم کاربر بن/آنبن بشه؟", lambda tuid: a_ban2(uid, tuid), lambda i, x: not is_admin(i))


def a_ban2(uid, tuid):
    u = DB["users"][tuid]
    u["banned"] = not u.get("banned")
    if u["banned"]:
        clear(tuid)
        tell(tuid, "🚫 دسترسی شما توسط ادمین مسدود شد.")
    else:
        tell(tuid, "✅ دسترسی شما دوباره فعال شد.", main_rows(tuid))
    back_to(uid, ("🚫 بن شد: " if u["banned"] else "✅ آنبن شد: ") + ulabel(tuid), PLAYER_ROWS)


@route(A_MSG, admin=True)
def a_msg(uid):
    pick_user(uid, "✉️ پیام برای کی؟", lambda tuid: a_msg2(uid, tuid))


def a_msg2(uid, tuid):
    ask(uid, "متن پیام رو بنویس:", lambda t: (tell(tuid, "📩 پیام ادمین:\n\n" + t), back_to(uid, "✅ ارسال شد.", PLAYER_ROWS)))


@route(A_ADDADMIN, admin=True)
def a_addadmin(uid):
    pick_user(uid, "👑 کدوم کاربر ادمین بشه؟", lambda tuid: a_addadmin2(uid, tuid), lambda i, x: not is_admin(i))


def a_addadmin2(uid, tuid):
    if tuid not in DB["settings"]["admins"]:
        DB["settings"]["admins"].append(tuid)
    save()
    tell(tuid, "👑 تو حالا ادمین هستی! دکمه‌ی «🛠 پنل ادمین» اضافه شد.", main_rows(tuid), force=True)
    back_to(uid, "✅ %s ادمین شد." % ulabel(tuid), PLAYER_ROWS)


# ───── منابع و تجهیزات ─────
@route(A_RES, admin=True)
def a_res(uid):
    back_to(uid, "💵 مدیریت منابع و تجهیزات", RES_ROWS)


@route(A_MONEY, admin=True)
def a_money(uid):
    pick_country(uid, "💰 پول و منابع کدوم کشور تغییر کنه؟ (هر کشوری رو می‌تونی انتخاب کنی)", lambda iso: a_money2(uid, iso),
                 lambda c: c["alive"])


def a_money2(uid, iso):
    c = C(iso)
    info = "%s\n💵 %s M$ | 👥 %s\n%s" % (cname(c), m(c["money"]), m(c["pop"]),
                                         " | ".join("%s %s" % (RES[k][0], m(v)) for k, v in c["res"].items()))
    ask(uid, info + "\n\nچه کاری؟", lambda t: a_money3(uid, iso, t),
        [["➕ افزایش پول", "➖ کاهش پول"], ["🎯 تنظیم دقیق پول", "🛢 تغییر منابع"], ["👥 تغییر جمعیت", "₿ تغییر ارز دیجیتال"]])


def adm_done(uid, iso, text):
    notify_country(iso, text)
    back_to(uid, "✅ " + text, RES_ROWS)


def a_money3(uid, iso, t):
    s = squash(t)
    c = C(iso)
    if not c:
        return back_to(uid, "❌ ممکن نیست.", RES_ROWS)
    if "افزایشپول" in s:
        return ask(uid, "➕ چقدر به خزانه اضافه بشه (M$)؟", lambda x: a_money_apply(uid, iso, "add", x),
                   [["1000", "5000", "20000"], ["100000", "1000000", "10000000"]])
    if "کاهشپول" in s:
        return ask(uid, "➖ چقدر از خزانه کم بشه (M$)؟", lambda x: a_money_apply(uid, iso, "sub", x),
                   [["1000", "5000", "20000"], ["100000", "1000000", "همه"]])
    if "تنظیمدقیق" in s:
        return ask(uid, "🎯 خزانه دقیقاً چند M$ بشه؟", lambda x: a_money_apply(uid, iso, "set", x), [["0", "10000", "100000"]])
    if "منابع" in s:
        return ask(uid, "کدوم منبع؟", lambda x: a_res_pick(uid, iso, x), chunk(["%s %s" % (e, n) for e, n in RES.values()], 2))
    if "جمعیت" in s:
        return ask(uid, "👥 تغییر جمعیت (منفی = کم):", lambda x: a_delta_apply(uid, iso, "pop", None, x),
                   [["+1000000", "+10000000", "+50000000"], ["-1000000", "-10000000"]])
    if "ارز" in s:
        return ask(uid, "کدوم ارز؟", lambda x: a_coin_pick(uid, iso, x), chunk(["%s %s" % (d["sym"], k) for k, d in COINS.items()], 2))
    a_money2(uid, iso)


def a_money_apply(uid, iso, mode, t):
    c = C(iso)
    v = c["money"] if squash(t) == "همه" else num(t)
    if v is None or v < 0:
        tell(uid, "❌ عدد نامعتبر.")
        return a_money2(uid, iso)
    old = c["money"]
    c["money"] = max(0.0, old + v if mode == "add" else (old - v if mode == "sub" else v))
    adm_done(uid, iso, "خزانه %s تغییر کرد: از %s به %s M$" % (cname(c), m(old), m(c["money"])))


def a_res_pick(uid, iso, t):
    k = next((k for k, (e, n) in RES.items() if squash("%s %s" % (e, n)) == squash(t) or squash(n) == squash(t)), None)
    if not k:
        return a_money2(uid, iso)
    ask(uid, "مقدار تغییر %s (منفی = کم)؟" % RES[k][1], lambda x: a_delta_apply(uid, iso, "res", k, x),
        [["+10000", "+100000", "+1000000"], ["-10000", "-100000", "-1000000"]])


def a_coin_pick(uid, iso, t):
    s = coin_of(t)
    if not s:
        return a_money2(uid, iso)
    ask(uid, "مقدار تغییر %s (منفی = کم)؟" % s, lambda x: a_delta_apply(uid, iso, "coin", s, x),
        [["+0.1", "+1", "+10"], ["-0.1", "-1", "-10"]])


def a_delta_apply(uid, iso, kind, key, t):
    c, v = C(iso), num(t)
    if not c or v is None or v == 0:
        tell(uid, "❌ عدد نامعتبر.")
        return a_money2(uid, iso)
    if kind == "pop":
        c["pop"] = max(0.0, c["pop"] + v)
        txt = "جمعیت %s: %s" % (cname(c), m(c["pop"]))
    elif kind == "res":
        c["res"][key] = max(0.0, c["res"][key] + v)
        txt = "%s %s: %s" % (RES[key][1], cname(c), m(c["res"][key]))
    else:
        c["crypto"][key] = max(0.0, c["crypto"].get(key, 0.0) + v)
        txt = "%s %s: %s" % (key, cname(c), ("%.6f" % c["crypto"][key]).rstrip("0").rstrip("."))
    adm_done(uid, iso, txt)



@route(A_UNITS, admin=True)
def a_units(uid):
    pick_country(uid, "🎖 تجهیزات کدوم کشور تغییر کنه؟", lambda iso: a_units2(uid, iso), lambda c: c["alive"])


def a_units2(uid, iso):
    ask(uid, "🎖 کدوم بخش؟", lambda t: a_units3(uid, iso, t), chunk(list(SHOP), 2))


def a_units3(uid, iso, t):
    lab = next((k for k in SHOP if squash(k) == squash(t)), None)
    if not lab:
        return a_units2(uid, iso)
    units = sorted((u for u in U.values() if u["cat"] in SHOP[lab]), key=lambda u: (u["tech"], u["cost"]))
    pick_unit(uid, "کدوم تجهیز؟", units, lambda key: a_units4(uid, iso, lab, key), per=14)


def a_units4(uid, iso, lab, key):
    ask(uid, "چند تا اضافه/کم بشه؟ دکمه بزن یا عدد بنویس (منفی = کم)", lambda q: a_units5(uid, iso, key, q),
        [["+1", "+5", "+10"], ["+50", "+100", "-5"], ["-10", "-50", "-100"]])


def a_units5(uid, iso, key, t):
    c, v = C(iso), num(t)
    if not c or v is None or int(v) == 0:
        return back_to(uid, "❌ عدد نامعتبر.", RES_ROWS)
    q = int(v)
    c["units"][key] = max(0, c["units"].get(key, 0) + q)
    notify_country(iso, "🎖 ادمین تجهیزات را تغییر داد: %+d× %s" % (q, U[key]["name"]))
    back_to(uid, "✅ %s: %s× %s" % (cname(c), m(c["units"][key]), U[key]["name"]), RES_ROWS)


ATTR_PRESETS = {"tech": ["1", "2", "3", "4", "5", "6"], "eco": ["0", "2", "4", "6", "8", "10"],
                "fort": ["0", "2", "4", "6", "8", "10"], "prov": ["1", "3", "5", "8", "10", "15", "20", "30"],
                "stab": ["25", "50", "75", "100"]}


ATTR_BTN = {"🔬 تکنولوژی": ("tech", 1, 6), "🏭 اقتصاد": ("eco", 0, 10), "🧱 استحکامات": ("fort", 0, 10),
            "🗺 استان": ("prov", 1, 99), "😐 ثبات": ("stab", 0, 100)}


@route(A_ATTR, admin=True)
def a_attr(uid):
    pick_country(uid, "⚙️ ویژگی کدوم کشور تغییر کنه؟", lambda iso: a_attr2(uid, iso), lambda c: c["alive"])


def a_attr2(uid, iso):
    ask(uid, "کدوم ویژگی؟", lambda t: a_attr3(uid, iso, t), chunk(list(ATTR_BTN), 2))


def a_attr3(uid, iso, t):
    key = next((k for k in ATTR_BTN if squash(k) == squash(t)), None)
    if not key:
        return a_attr2(uid, iso)
    ask(uid, "مقدار جدید برای %s؟ (دکمه بزن یا عدد بنویس)" % key, lambda v: a_attr4(uid, iso, key, v),
        chunk(ATTR_PRESETS[ATTR_BTN[key][0]], 3))


def a_attr4(uid, iso, key, t):
    c, v = C(iso), num(t)
    fld, lo, hi = ATTR_BTN[key]
    if not c or v is None:
        return back_to(uid, "❌ عدد نامعتبر.", RES_ROWS)
    c[fld] = max(lo, min(hi, v if fld == "stab" else int(v)))
    back_to(uid, "✅ %s: %s = %s" % (cname(c), key, m(c[fld])), RES_ROWS)


# ───── اعلان‌ها ─────
@route(A_ANN, admin=True)
def a_ann(uid):
    back_to(uid, "📢 اعلان‌ها", ANN_ROWS)


@route(A_CH, admin=True)
def a_ch(uid):
    def with_photo(fid, cap):
        a_ch_send(uid, cap or "📢", fid)

    ask_text(uid, "📣 اعلامیه برای کانال رو انتخاب کن (یا یک عکس همراه کپشن بفرست):", ANN_PRESETS,
             lambda t: a_ch_photo(uid, t), "✍️ متن اعلامیه برای کانال:")
    PHOTO[uid] = with_photo


def a_ch_photo(uid, t):
    ask(uid, "🖼 اعلامیه با عکس منتشر بشه؟", lambda x: a_ch_choice(uid, t, x), [["📷 ارسال با عکس جدید"], ["📝 با عکس پیش‌فرض"]])


def a_ch_choice(uid, t, x):
    if "جدید" in x:
        return ask_photo(uid, "📷 عکس رو بفرست:", lambda fid, cap: a_ch_send(uid, t, fid), on_text=lambda tx: a_ch_send(uid, t, None))
    a_ch_send(uid, t, None)


def a_ch_send(uid, t, fid):
    ok = announce("📢 اعلامیه‌ی ادمین\n\n" + t, cat="admin", photo=fid)
    back_to(uid, "✅ ارسال شد." if ok else "⚠️ در کانال ارسال نشد (در لاگ ثبت شد).", ANN_ROWS)


@route(A_ALL, admin=True)
def a_all(uid):
    ask_text(uid, "📨 پیام برای همه‌ی بازیکنان رو انتخاب کن:", ANN_PRESETS, lambda t: a_all2(uid, t),
             "✍️ متن پیام برای همه‌ی بازیکنان:")


def a_all2(uid, t):
    n = 0
    for i, x in list(DB["users"].items()):
        if not x.get("banned"):
            tell(i, "📢 پیام ادمین:\n\n" + t)
            n += 1
            time.sleep(0.05)
    back_to(uid, "✅ برای %d نفر ارسال شد." % n, ANN_ROWS)


@route(A_EVENT, admin=True)
def a_event(uid):
    ask(uid, "🎲 کدوم رویداد؟", lambda t: a_event2(uid, t), [[e["name"]] for e in EVENTS])


def a_event2(uid, t):
    e = next((x for x in EVENTS if squash(x["name"]) == squash(t)), None)
    if not e:
        return a_event(uid)

    def go(iso):
        owned = [c for c in DB["countries"].values() if c["owner"] and c["alive"]]
        c = random.choice(owned) if iso == "*" and owned else C(iso)
        if not c or iso == "*" and not owned:
            return back_to(uid, "❌ کشوری برای اعمال رویداد نیست.", ADMIN_ROWS)
        fire_event(c, e)
        back_to(uid, "✅ رویداد اعمال شد.", ADMIN_ROWS)

    pick_country(uid, "🎯 روی کدوم کشور؟", go, lambda c: c["alive"], extra={"🎲 تصادفی (یکی از کشورهای دارای رهبر)": "*"})


# ───── تنظیمات ─────
@route(A_SET, admin=True)
def a_set(uid):
    back_to(uid, "⚙️ تنظیمات بازی", SET_ROWS)


@route(A_PAUSE, admin=True)
def a_pause(uid):
    s = DB["settings"]
    s["paused"] = not s["paused"]
    announce("⏸ بازی موقتاً متوقف شد." if s["paused"] else "▶️ بازی دوباره شروع شد!")
    back_to(uid, "⏸ بازی متوقف شد." if s["paused"] else "▶️ بازی ادامه پیدا کرد.", SET_ROWS)


@route(A_SPEED, admin=True)
def a_speed(uid):
    ask(uid, "⚡ ضریب سرعت درآمد؟ (الان ×%s) مثلاً 1 یا 2 یا 0.5" % DB["settings"]["speed"],
        lambda t: a_speed2(uid, t), [["0.5", "1", "2", "5"]])


def a_speed2(uid, t):
    v = num(t)
    if not v or v <= 0 or v > 100:
        return back_to(uid, "❌ عدد نامعتبر.", SET_ROWS)
    DB["settings"]["speed"] = v
    back_to(uid, "✅ سرعت: ×%s" % v, SET_ROWS)


@route(A_PROT, admin=True)
def a_prot(uid):
    ask(uid, "🛡 مدت حفاظت کشور جدید (ساعت)؟ الان %s" % DB["settings"]["protect_h"], lambda t: a_prot2(uid, t),
        [["0", "6", "12", "24"]])


def a_prot2(uid, t):
    v = num(t)
    if v is None or v < 0 or v > 720:
        return back_to(uid, "❌ عدد نامعتبر.", SET_ROWS)
    DB["settings"]["protect_h"] = v
    back_to(uid, "✅ مدت حفاظت: %s ساعت" % m(v), SET_ROWS)


@route(A_AUTO, admin=True)
def a_auto(uid):
    s = DB["settings"]
    s["auto_events"] = not s["auto_events"]
    s["last_event"] = now()
    back_to(uid, "🔁 رویداد خودکار (هر ۶ ساعت): " + ("روشن ✅" if s["auto_events"] else "خاموش ⛔"), SET_ROWS)


@route(A_SETCH, admin=True)
def a_setch(uid):
    back_to(uid, ("📣 کانال فعلی: %s\n\n"
                  "برای اینکه ربات توی کانال پست بذاره:\n"
                  "1) ربات رو توی کانال «ادمین» کن (دسترسی ارسال پیام).\n"
                  "2) با «🧪 تست کانال» امتحان کن.\n\n"
                  "برای عوض کردن کانال بفرست:\n/setchannel @آیدی_کانال") % (DB["settings"]["channel"] or "ثبت نشده ❌"), SET_ROWS)


@route(A_TESTCH, admin=True)
def a_testch(uid):
    ok, err = post_channel("🧪 پیام آزمایشی — ربات «جنگ جهانی» به کانال وصل است ✅")
    if ok:
        DB["settings"]["warned"] = False
    back_to(uid, "✅ پیام به کانال ارسال شد." if ok else "❌ ارسال نشد: %s\nبات باید ادمین کانال باشه و کانال ثبت شده باشه." % err, SET_ROWS)


@route(A_RESET, admin=True)
def a_reset(uid):
    ask(uid, "⚠️ همه‌ی کشورها، جنگ‌ها و پیشرفت بازی پاک می‌شه (کاربران و ادمین‌ها می‌مونن).\nمطمئنی؟",
        lambda t: a_reset2(uid, t), [["⚠️ بله، ریست کن", "❌ انصراف"]])


def a_reset2(uid, t):
    if "ریست" not in t:
        return back_to(uid, "لغو شد.", SET_ROWS)
    try:
        snap_take("pre")                                   # قبل از ریست از وضعیت فعلی بکاپ می‌گیره
    except Exception as e:  # noqa: BLE001
        print("pre-reset snapshot error:", e)
    seed_countries()
    for k in ("wars", "allies", "props", "requests", "licenses", "sanctions", "pack_log", "log"):
        DB[k] = []
    DB["unions"], DB["wonders"] = {}, {}
    DB["market"] = {}
    init_market()
    DB.pop("ext", None)                                    # بانک‌ها، تنگه‌ها، محاصره، جام جهانی، فایروال و ...
    EXT()
    for i, x in DB["users"].items():
        x["country"] = None
        clear(i)
    ATK.clear()
    save()                                                 # همین الان روی فایل ذخیره بشه
    announce("🔄 بازی از نو شروع شد! همه‌ی کشورها آزادند.\n#شروع_دوباره")
    back_to(uid, "✅ بازی ریست شد و ذخیره شد. همه‌ی کشورها آزاد شدند.", SET_ROWS)


@route(A_STATS, admin=True)
def a_stats(uid):
    cs = DB["countries"].values()
    owned = [c for c in cs if c["owner"]]
    s = DB["settings"]
    L = ["📊 آمار بازی",
         "👥 کاربران: %d" % len(DB["users"]),
         "🏛 کشورهای دارای رهبر: %d از %d" % (len(owned), len(DB["countries"])),
         "⚔️ جنگ فعال: %d | 🤝 ائتلاف: %d" % (len(DB["wars"]), len(DB["allies"])),
         "📥 درخواست در انتظار: %d" % len(DB["requests"]),
         "💰 مجموع خزانه‌ها: %s M$" % m(sum(c["money"] for c in owned)),
         "⏸ وضعیت: %s | ⚡ سرعت ×%s" % ("متوقف" if s["paused"] else "فعال", s["speed"]),
         "📣 کانال: %s" % ("ثبت‌شده ✅" if s["channel"] else "ثبت نشده ❌"),
         "🛡 اتحادها: %d | 🎫 مجوز فعال: %d | 🛍 پک فعال‌شده: %d | 🏛 شگفتی‌ها: %d" % (
             len(DB["unions"]), sum(1 for l in DB["licenses"] if lic_valid(l)), len(DB["pack_log"]), len(DB["wonders"])),
         "🖼 عکس گزارش‌ها: %s | 🎫 سیستم مجوز: %s" % ("روشن" if s.get("img_on", True) else "خاموش", "روشن" if s.get("lic_on", True) else "خاموش")]
    back_to(uid, "\n".join(L), ADMIN_ROWS)


# ═════════════ پنل ادمین: پک‌ها ═════════════
@route(A_PACKADM, admin=True)
def a_packadm(uid):
    n = sum(1 for r in DB["requests"] if r["type"] == "pack")
    back_to(uid, "🛍 مدیریت پک‌ها\n📥 درخواست خرید پک در انتظار: %d (از «📥 درخواست‌ها» تأیید کن)\n\n"
                 "اینجا می‌تونی هر پکی رو برای هر کشوری (حتی بدون رهبر) فعال کنی." % n, PACK_ADM_ROWS)


@route(A_PACKGIVE, admin=True)
def a_packgive(uid):
    ask(uid, "🎁 کدوم پک؟", lambda t: a_packgive2(uid, t), [[p["name"]] for p in PACKS])


def a_packgive2(uid, t):
    pk = pack_of(t)
    if not pk:
        return a_packadm(uid)
    tell(uid, pack_card(pk))
    pick_country(uid, "🌍 پک «%s» برای کدوم کشور فعال بشه؟" % pk["name"], lambda iso: a_packgive3(uid, pk["key"], iso), lambda c: c["alive"])


def a_packgive3(uid, key, iso):
    c, pk = C(iso), PK[key]
    warn = "\n⚠️ این کشور قبلاً این پک رو گرفته." if pk.get("limit") and c["packs"].get(key, 0) >= pk["limit"] else ""
    ask(uid, "فعال‌سازی «%s» برای %s؟%s" % (pk["name"], cname(c), warn), lambda t: a_packgive4(uid, key, iso, t),
        [["✅ فعال‌سازی + اعلام در کانال"], ["🔕 فعال‌سازی بی‌صدا"], ["❌ انصراف"]])


def a_packgive4(uid, key, iso, t):
    if "انصراف" in t:
        return back_to(uid, "لغو شد.", PACK_ADM_ROWS)
    activate_pack(iso, key, silent=("بیصدا" in squash(t)))
    back_to(uid, "✅ پک «%s» برای %s فعال شد." % (PK[key]["name"], cname(C(iso))), PACK_ADM_ROWS)


@route(A_PACKLOG, admin=True)
def a_packlog(uid):
    L = ["📜 آخرین پک‌های فعال‌شده", ""] + ["• %s پیش — %s: %s" % (dur(now() - x["t"]), cname(C(x["iso"])) if C(x["iso"]) else x["iso"],
                                                                    PK[x["pack"]]["name"]) for x in reversed(DB["pack_log"][-15:])]
    back_to(uid, "\n".join(L) if DB["pack_log"] else "هنوز پکی فعال نشده.", PACK_ADM_ROWS)


# ═════════════ پنل ادمین: عکس گزارش‌ها ═════════════
IMG_TOGGLE = "🔁 روشن/خاموش کردن عکس گزارش‌ها"


def img_btn(cat):
    return "🖼 عکس " + IMG_CATS[cat].split(" ", 1)[1]


@route(A_IMG, admin=True)
def a_img(uid):
    s = DB["settings"]
    L = ["🖼 عکس گزارش‌های کانال", "وضعیت: %s" % ("روشن ✅" if s.get("img_on", True) else "خاموش ❌"),
         "برای هر نوع گزارش یک عکس دلخواه بذار. اگه نذاری، عکس خودکار ساخته می‌شه (یا فایل‌های پوشه‌ی %s/ مثل war.jpg)." % IMG_DIR, ""]
    L += ["%s %s" % ("✅" if c in s["imgs"] else "▫️", img_btn(c)) for c in IMG_CATS]
    ask(uid, "\n".join(L), lambda t: a_img2(uid, t), chunk([img_btn(c) for c in IMG_CATS], 2) + [[IMG_TOGGLE]])


def a_img2(uid, t):
    s = DB["settings"]
    if squash(t) == squash(IMG_TOGGLE):
        s["img_on"] = not s.get("img_on", True)
        return a_img(uid)
    cat = next((k for k in IMG_CATS if squash(img_btn(k)) == squash(t)), None)
    if not cat:
        return a_img(uid)
    ask(uid, "🖼 %s\nچه کاری؟" % IMG_CATS[cat], lambda x: a_img3(uid, cat, x), [["📷 ارسال عکس جدید"], ["🗑 حذف عکس"], ["🧪 تست ارسال به کانال"]])


def a_img3(uid, cat, t):
    s = DB["settings"]
    if "جدید" in t:
        def save(fid, cap):
            s["imgs"][cat] = fid
            back_to(uid, "✅ عکس «%s» ذخیره شد." % IMG_CATS[cat], ADMIN_ROWS)
        return ask_photo(uid, "📷 عکس رو بفرست (Photo):", save)
    if "حذف" in t:
        s["imgs"].pop(cat, None)
        return back_to(uid, "🗑 عکس «%s» حذف شد." % IMG_CATS[cat], ADMIN_ROWS)
    if "تست" in t:
        ok, err = post_channel("🧪 تست عکس گزارش: %s" % IMG_CATS[cat], cat=cat, isos=("US", "RU"))
        return back_to(uid, "✅ تست ارسال شد." if ok else "⚠️ ارسال نشد: %s" % err, ADMIN_ROWS)
    a_img(uid)


# ═════════════ پنل ادمین: بازار، بانک، قوانین و مجوزها ═════════════
AE_CRYPTO, AE_BANK, AE_STATUS = "₿ دستکاری قیمت ارز", "🏦 تنظیم سود بانک", "📊 وضعیت بازار و بانک"
ECOADM_ROWS = [[AE_CRYPTO, AE_BANK], [AE_STATUS], [A_PANEL]]


@route(A_ECOADM, admin=True)
def a_ecoadm(uid):
    back_to(uid, "📈 مدیریت بازار و بانک", ECOADM_ROWS)


@route(AE_STATUS, admin=True)
def a_ae_status(uid):
    s = DB["settings"]
    cs = [c for c in DB["countries"].values() if c["owner"]]
    L = ["📊 وضعیت بازار و بانک", ""]
    for sym, d in COINS.items():
        L.append("%s %s: %s M$ (%+.1f٪)" % (d["sym"], sym, fp(coin_price(sym)), coin_change(sym)))
    L += ["", "🏧 مجموع سپرده‌ها: %s M$" % m(sum(dep_total(c) for c in cs)), "💳 مجموع وام‌ها: %s M$" % m(sum(c["bank"]["loan"] for c in cs)),
          "ضریب سود سپرده ×%s | ضریب سود وام ×%s" % (s["bank_dep_mult"], s["bank_loan_mult"]),
          "⛏ مجموع ماینرها: %d" % sum(sum(c["miners"].values()) for c in cs)]
    back_to(uid, "\n".join(L), ECOADM_ROWS)


@route(AE_CRYPTO, admin=True)
def a_ae_crypto(uid):
    ask(uid, "₿ قیمت کدوم ارز دستکاری بشه؟", lambda t: a_ae_coin(uid, t), chunk(["%s %s" % (d["sym"], k) for k, d in COINS.items()], 2))


def a_ae_coin(uid, t):
    s = coin_of(t)
    if not s:
        return a_ecoadm(uid)
    ask(uid, "%s الان %s M$ است. چه تغییری؟ (درصد، مثل +30 یا -40)" % (s, fp(coin_price(s))), lambda x: a_ae_do(uid, s, x),
        [["+10", "+25", "+50"], ["-10", "-25", "-50"]])


def a_ae_do(uid, s, t):
    v = num(en_digits(t).replace("%", ""))
    if v is None or v <= -95 or v > 1000:
        tell(uid, "❌ عدد نامعتبر.")
        return a_ecoadm(uid)
    crypto_shock(s, v / 100.0)
    back_to(uid, "✅ قیمت %s اکنون %s M$ است (در کانال اعلام شد)." % (s, fp(coin_price(s))), ECOADM_ROWS)


@route(AE_BANK, admin=True)
def a_ae_bank(uid):
    s = DB["settings"]
    ask(uid, "🏦 ضریب سود سپرده (الان ×%s)؟" % s["bank_dep_mult"], lambda t: a_ae_bank2(uid, t), [["0.5", "1", "2"], ["3", "5"]])


def a_ae_bank2(uid, t):
    v = num(t)
    if v is None or v < 0 or v > 20:
        tell(uid, "❌ عدد نامعتبر.")
        return a_ecoadm(uid)
    DB["settings"]["bank_dep_mult"] = v
    ask(uid, "💳 ضریب سود وام (الان ×%s)؟" % DB["settings"]["bank_loan_mult"], lambda x: a_ae_bank3(uid, x), [["0.5", "1", "2"], ["3", "5"]])


def a_ae_bank3(uid, t):
    v = num(t)
    if v is None or v < 0 or v > 20:
        tell(uid, "❌ عدد نامعتبر.")
        return a_ecoadm(uid)
    DB["settings"]["bank_loan_mult"] = v
    back_to(uid, "✅ ضرایب سود بانک ذخیره شد.", ECOADM_ROWS)


def rules_labels():
    s = DB["settings"]
    on = lambda v: "روشن ✅" if v else "خاموش ❌"  # noqa: E731
    return [("lic", "🎫 سیستم مجوز: " + on(s.get("lic_on", True))),
            ("auto", "🤖 فروش خودکار مجوز (کشورهای بدون رهبر): " + on(s.get("auto_lic", True))),
            ("black", "🕶 بازار سیاه: " + on(s.get("black_on", True))),
            ("exp", "💰 درصد درآمد صادرات: %d٪" % int(s.get("export_pct", 0.10) * 100))]


@route(A_RULES, admin=True)
def a_rules(uid):
    labs = rules_labels()
    ask(uid, "📜 قوانین بازی و مجوزها\n\nروی هر مورد بزن تا تغییر کنه.", lambda t: a_rules2(uid, t),
        [[l] for _k, l in labs] + [[A_LICADM]])


def a_rules2(uid, t):
    s = DB["settings"]
    if squash(t) == squash(A_LICADM):
        return a_licadm(uid)
    k = next((k for k, l in rules_labels() if squash(l) == squash(t)), None)
    if k == "lic":
        s["lic_on"] = not s.get("lic_on", True)
    elif k == "auto":
        s["auto_lic"] = not s.get("auto_lic", True)
    elif k == "black":
        s["black_on"] = not s.get("black_on", True)
    elif k == "exp":
        s["export_pct"] = {0.0: 0.05, 0.05: 0.10, 0.10: 0.20, 0.20: 0.0}.get(round(s.get("export_pct", 0.10), 2), 0.10)
    a_rules(uid)


@route(A_LICADM, admin=True)
def a_licadm(uid):
    ask(uid, "🎫 مدیریت مجوزها\nبرای لغو یک مجوز بنویس: «لغو مجوز <شماره>»", lambda t: a_licadm2(uid, t),
        [["📋 همه‌ی مجوزها"], ["🎁 صدور مجوز برای کشور"]])


def a_licadm2(uid, t):
    if "همه" in t:
        ls = [l for l in DB["licenses"] if lic_valid(l)][-15:]
        return back_to(uid, ("\n\n".join(lic_text(l) for l in ls)) if ls else "مجوز فعالی نیست.", ADMIN_ROWS)
    if "صدور" in t:
        return pick_country(uid, "🎁 مجوز برای کدوم کشور (گیرنده)؟", lambda iso: a_lic_from(uid, iso), lambda c: c["alive"])
    a_licadm(uid)


def a_lic_from(uid, to_iso):
    pick_country(uid, "🏭 از طرف کدوم کشور سازنده؟", lambda iso: a_lic_scope(uid, to_iso, iso),
                 lambda c: c["iso"] in ORG_INDEX and c["iso"] != to_iso)


def a_lic_scope(uid, to_iso, frm):
    own = [u for u in national_units(frm) if u["cat"] != "nuke"]

    def done(scope):
        lic_ask_terms(uid, None, lambda terms: a_lic_do(uid, to_iso, frm, scope, terms))

    def h(t):
        s = squash(t)
        if "یکتجهیز" in s:
            return pick_unit(uid, "🎯 کدوم تجهیز؟", sorted(own, key=lambda u: (u["cat"], u["tech"])),
                             lambda key: done({"t": "unit", "k": key}), per=12)
        if "یکدسته" in s:
            labs = [k for k, cats in SHOP.items() if k != "☢️ هسته‌ای" and any(u["cat"] in cats for u in own)]
            return ask(uid, "📂 کدوم دسته؟", lambda x: done({"t": "cat", "c": next((k for k in labs if squash(k) == squash(x)), labs[0])}),
                       chunk(labs, 2))
        done({"t": "all"})

    ask(uid, "مجوز برای چی؟", h, [["🎯 یک تجهیز مشخص"], ["📂 یک دسته"], ["🔰 همه‌ی تجهیزات"]])


def a_lic_do(uid, to_iso, frm, scope, terms):
    l = lic_new(frm, to_iso, scope, terms["kind"], terms.get("qty", 0), terms.get("hours", 0), 0.0)
    notify_country(to_iso, "🎫 ادمین یک مجوز تسلیحاتی برات صادر کرد:\n" + lic_text(l))
    back_to(uid, "✅ مجوز صادر شد:\n" + lic_text(l), ADMIN_ROWS)


# ═════════════════════════════════════════════════════════════════════
# ═════════════ آپدیت بزرگ ۲ ═════════════
# دوزبانه (فارسی + انگلیسی)، کلید جنگ‌ها، قالب‌های جدید گزارش، بانک‌ها و کارت به کارت،
# بازار منابع و کریپتو، پنل سازمان ملل، بکاپ و ریست ساعتی
# ═════════════════════════════════════════════════════════════════════
import datetime
import gzip
import html as _html

# ───── ابزارهای پایه‌ی آپدیت ۲ ─────
EXT_REQ = {"change", "vipcard"}
EXT_TICKS = []
STMT_KIND = {}
EN_MAP = {}                 # uid ← {برچسب انگلیسی: برچسب فارسی اصلی}
B_LANG = "🌐 زبان / Language"
B_SENDMIL = "🎖 بیانیه نظامی"


def EXT():
    e = DB.setdefault("ext", {})
    e.setdefault("banks", {})        # iso ← {bank_key: card}
    e.setdefault("cards", {})        # card ← iso
    e.setdefault("vip_owner", {})    # card ← iso
    e.setdefault("cease", [])
    e.setdefault("rep", {"crypto_t": 0, "econ_t": 0, "econ_total": None, "board_t": 0, "snap_t": 0,
                         "crypto_prev": {}, "board_prev": {}, "board_cur": {}, "board_snap_t": 0})
    e.setdefault("fw", {"lvl": 0, "pool": 0.0})
    e.setdefault("tx", 0)
    return e


def M2D(x):
    """میلیون‌دلار ← دلار"""
    return float(x) * 1_000_000.0


def dol(mm):
    """مبلغ داخلی (M$) را به دلار کامل با کاما نشان می‌دهد."""
    return "{:,}".format(int(round(float(mm) * 1_000_000.0)))


def dols(d):
    return "{:,}".format(int(round(float(d))))


def bnum(t):
    """عدد بزرگ: 1,000,000 یا 5b / 2t / 300m / 10k"""
    s = en_digits(t).strip().lower().replace(",", "").replace("٬", "").replace("،", "").replace("$", "")
    mult = 1.0
    if s and s[-1] in "kmbt":
        mult = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}[s[-1]]
        s = s[:-1]
    try:
        v = float(s) * mult
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def tnow():
    return datetime.datetime.utcfromtimestamp(now() + 12600)      # وقت تهران (UTC+3:30)


def stamp():
    t = tnow()
    return "%s | %s" % (t.strftime("%Y-%m-%d"), t.strftime("%H:%M"))


def ext_tick(t):
    for fn in EXT_TICKS:
        try:
            fn(t)
        except Exception:  # noqa: BLE001
            traceback.print_exc()


# ───── ترجمه‌ی خودکار (گوگل) + گزارش‌های دوزبانه ─────
TR = {"cache": {}, "bad_until": 0.0}
FA_RE = re.compile(r"[؀-ۿ]")
Q_OPEN, Q_CLOSE = "⟦Q⟧", "⟦/Q⟧"


def strip_q(text):
    return (text or "").replace(Q_OPEN + "\n", "").replace("\n" + Q_CLOSE, "").replace(Q_OPEN, "").replace(Q_CLOSE, "")


def to_html(text):
    return _html.escape(text).replace(Q_OPEN, "<blockquote>").replace(Q_CLOSE, "</blockquote>")


TR_BACKENDS = ["gapi", "gweb", "gclient", "mymemory", "lingva"]
TR_STATE = {"ok": None, "err": ""}


def _tr_call(name, text, px):
    pxs = None
    if name == "gapi":
        r = requests.post("https://translate.googleapis.com/translate_a/single", params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t"},
                          data={"q": text}, timeout=(5, 12), proxies=pxs)
        return "".join(seg[0] for seg in r.json()[0] if seg and seg[0])
    if name == "gweb":
        r = requests.post("https://translate.google.com/translate_a/single", params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t"},
                          data={"q": text}, timeout=(5, 12), proxies=pxs)
        return "".join(seg[0] for seg in r.json()[0] if seg and seg[0])
    if name == "gclient":
        r = requests.get("https://clients5.google.com/translate_a/t", params={"client": "dict-chrome-ex", "sl": "auto", "tl": "en", "q": text},
                         timeout=(5, 12), proxies=pxs)
        js = r.json()
        return "".join(x[0] if isinstance(x, list) else x for x in js) if isinstance(js, list) else js["sentences"][0]["trans"]
    if name == "mymemory":
        r = requests.get("https://api.mymemory.translated.net/get", params={"q": text[:480], "langpair": "fa|en"}, timeout=(5, 12), proxies=pxs)
        out = r.json()["responseData"]["translatedText"]
        if not out or "MYMEMORY" in out.upper() and "WARNING" in out.upper():
            raise ValueError("mymemory limit")
        return out
    if name == "lingva":
        import urllib.parse as up
        r = requests.get("https://lingva.ml/api/v1/fa/en/" + up.quote(text[:800], safe=""), timeout=(5, 12), proxies=pxs)
        return r.json()["translation"]
    raise ValueError(name)


def _gtx(text):
    """ترجمه‌ی فارسی ← انگلیسی؛ چند سرویس رو (مستقیم و بعد با پروکسی) امتحان می‌کنه و آخرین سرویس سالم رو اول می‌ذاره."""
    order = list(TR_BACKENDS)
    good = TR_STATE.get("ok")
    if good in order:
        order.remove(good)
        order.insert(0, good)
    last = None
    for name in order:
        for px in (None,):
            if px is None and name != order[0] and TR_STATE.get("direct_bad", {}).get(name):
                continue
            try:
                out = _tr_call(name, text, px)
                out = (out or "").strip("\n")
                if out:
                    TR_STATE["ok"], TR_STATE["err"] = name, ""
                    return out
            except Exception as e:  # noqa: BLE001
                last = "%s: %s" % (name, repr(e)[:100])
    TR_STATE["err"] = last or "unknown"
    print("translate failed:", TR_STATE["err"])
    return None


def tr_line(line):
    """یک خط فارسی ← انگلیسی (با کش)؛ اگه نشد None."""
    if not FA_RE.search(line):
        return line
    c = TR["cache"]
    if line in c:
        return c[line]
    if TR["bad_until"] > now():
        return None
    out = _gtx(line)
    if out is None:
        TR["bad_until"] = now() + 90
        return None
    if len(c) > 6000:
        c.clear()
    c[line] = out
    return out


def tr_lines(lines):
    todo = [l for l in dict.fromkeys(lines) if FA_RE.search(l) and l not in TR["cache"]]
    if todo and TR["bad_until"] <= now():
        with ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(tr_line, todo))
    return [tr_line(l) for l in lines]


def tr_en(text):
    lines = text.split("\n")
    out = tr_lines(lines)
    if any(o is None for o, l in zip(out, lines) if FA_RE.search(l)):
        return None
    return "\n".join(out)


def english_of(text):
    """ترجمه‌ی انگلیسی متن (یا None)."""
    if True:  # گزارش‌های کانال فقط فارسی‌اند (ترجمه‌ی انگلیسی کانال حذف شد)
        return None
    if not FA_RE.search(text):
        return None
    return tr_en(text)


def bilingual(text):
    en = english_of(text)
    return text + "\n\n━━━━━━━━━━━━━━━━━━━━\n🇬🇧 ENGLISH\n" + en if en else text


def en_ui(uid, text, rows):
    """پیام و دکمه‌ها رو برای کاربر انگلیسی‌زبان ترجمه می‌کنه (دکمه‌ها برگشت‌پذیرن)."""
    mp = EN_MAP.setdefault(uid, {})
    if len(mp) > 3000:
        mp.clear()
    if text and FA_RE.search(text):
        lines = text.split("\n")
        out = tr_lines(lines)
        text = "\n".join(o if o is not None else l for o, l in zip(out, lines))
    if rows:
        labels = [b for r in rows for b in r if FA_RE.search(b)]
        tr_lines(labels)
        used = {}
        new_rows = []
        for r in rows:
            nr = []
            for b in r:
                if not FA_RE.search(b):
                    nr.append(b)
                    continue
                en = tr_line(b)
                if not en:
                    nr.append(b)
                    continue
                while used.get(en, b) != b:
                    en += " ·"
                used[en] = b
                mp[en] = b
                nr.append(en)
            new_rows.append(nr)
        rows = new_rows
    return text, rows


@route(B_LANG)
def r_lang(uid):
    ask(uid, "🌐 زبان ربات رو انتخاب کن | Choose your language", lambda t: lang_do(uid, t),
        [["🇮🇷 فارسی", "🇬🇧 English"]])


def lang_do(uid, t):
    u = user(uid)
    if "English" in t or "انگلیسی" in t or t.lower().startswith("en"):
        u["lang"] = "en"
        EN_MAP.pop(uid, None)
        SENT_KP.pop(uid, None)
        menu(uid, "✅ Language set to English. Messages are translated automatically.")
    else:
        u["lang"] = "fa"
        SENT_KP.pop(uid, None)
        menu(uid, "✅ زبان روی فارسی تنظیم شد.")


A_LANG = "🌐 زبان کانال (فارسی+انگلیسی)"


@route(A_LANG, admin=True)
def a_lang(uid):
    s = DB["settings"]
    s["bilingual"] = not s.get("bilingual", True)
    TR["bad_until"] = 0.0
    test = _gtx("سلام فرمانده، به میدان نبرد خوش آمدی")
    st = ("✅ سرویس ترجمه کار می‌کنه (%s):\n%s" % (TR_STATE.get("ok"), test)) if test else "❌ سرویس ترجمه از این سرور در دسترس نیست.\nدلیل: %s\n(اینترنت/فیلترینگ سرور رو چک کن)" % TR_STATE.get("err")
    back_to(uid, "🌐 ترجمه‌ی انگلیسی زیر هر گزارش کانال: " + ("روشن ✅" if s["bilingual"] else "خاموش ⛔") + "\n\n" + st, ADMIN_ROWS)


# ───── کلید روشن/خاموش انواع جنگ ─────
WAR_KINDS = {"conv": "⚔️ جنگ معمولی", "cyber": "💻 جنگ سایبری", "nuke": "☢️ جنگ هسته‌ای"}
A_WARS = "⚔️ مدیریت جنگ‌ها"


def war_on(k):
    return DB["settings"].setdefault("war_on", {}).get(k, True)


def war_blocked(uid, k, rows):
    if war_on(k):
        return False
    if is_admin(uid) and False:
        return False
    back_to(uid, "⛔ %s فعلاً توسط ادمین غیرفعاله." % WAR_KINDS[k], rows)
    return True


def war_btn(k):
    return "%s: %s" % (WAR_KINDS[k], "روشن ✅" if war_on(k) else "خاموش ⛔")


@route(A_WARS, admin=True)
def a_wars(uid):
    L = ["⚔️ مدیریت جنگ‌ها", "با زدن هر دکمه، اون نوع جنگ روشن/خاموش می‌شه.", ""]
    L += [war_btn(k) for k in WAR_KINDS]
    ask(uid, "\n".join(L), lambda t: a_wars2(uid, t), [[war_btn(k)] for k in WAR_KINDS] + [[A_PANEL]], back=False)


def a_wars2(uid, t):
    k = next((k for k in WAR_KINDS if squash(WAR_KINDS[k]) in squash(t)), None)
    if not k:
        return a_wars(uid)
    on = DB["settings"].setdefault("war_on", {})
    on[k] = not war_on(k)
    announce("%s %s توسط ادمین %s شد.\n#اعلامیه_ادمین" % ("🟢" if on[k] else "🔴", WAR_KINDS[k], "فعال" if on[k] else "غیرفعال"),
             cat="admin")
    a_wars(uid)


# ───── دسته‌های جدید عکس گزارش ─────
IMG_CATS.update({
    "atk_naval": "🌊 حمله دریایی", "atk_missile": "🚀 حمله موشکی", "atk_drone": "🛸 حمله پهپادی",
    "atk_air": "✈️ حمله هوایی", "atk_bomber": "💣 بمباران", "atk_ground": "⚔️ یورش زمینی",
    "milstmt": "🎖 بیانیه نظامی", "ceasefire": "🕊 آتش‌بس سازمان ملل", "strait": "🌊 تنگه‌ها و کانال‌ها",
    "market": "📊 بازار منابع", "economy": "🌍 گردش اقتصاد جهانی", "bankfound": "🏛 تأسیس بانک",
    "banktx": "💸 تراکنش بانکی", "uprising": "🚨 خیزش مردمی", "fall": "🏚 سقوط حکومت",
    "worldcup": "🏆 جام جهانی", "heist": "☠️ سرقت کریپتو", "firewall": "🛡 فایروال جهانی",
    "industry": "🏭 خبر صنعتی", "vipcard": "💎 کارت VIP",
})
CARD_STYLE.update({
    "atk_naval": ("NAVAL ASSAULT", (10, 60, 110), (5, 15, 40)), "atk_missile": ("MISSILE STRIKE", (140, 50, 10), (30, 10, 10)),
    "atk_drone": ("DRONE STRIKE", (60, 70, 90), (15, 15, 30)), "atk_air": ("AIRSTRIKE", (30, 80, 140), (10, 20, 50)),
    "atk_bomber": ("BOMBING RAID", (110, 60, 20), (30, 15, 10)), "atk_ground": ("GROUND OFFENSIVE", (90, 90, 40), (25, 28, 12)),
    "milstmt": ("MILITARY STATEMENT", (50, 70, 50), (12, 22, 12)), "ceasefire": ("UN CEASEFIRE", (40, 110, 170), (10, 30, 70)),
    "strait": ("STRATEGIC STRAIT", (10, 90, 130), (5, 25, 50)), "market": ("MARKET CONTROL", (120, 100, 20), (30, 25, 8)),
    "economy": ("GLOBAL ECONOMY", (30, 110, 70), (8, 35, 25)), "bankfound": ("NEW BANK", (30, 90, 140), (10, 25, 50)),
    "banktx": ("BANK TRANSFER", (30, 120, 90), (8, 40, 30)), "uprising": ("UPRISING", (150, 30, 30), (40, 8, 8)),
    "fall": ("REGIME COLLAPSE", (60, 20, 20), (15, 5, 5)), "worldcup": ("WORLD CUP", (20, 120, 60), (8, 40, 25)),
    "heist": ("CRYPTO HEIST", (90, 20, 120), (20, 5, 40)), "firewall": ("GLOBAL FIREWALL", (20, 90, 150), (8, 25, 55)),
    "industry": ("INDUSTRY NEWS", (110, 110, 120), (30, 30, 38)), "vipcard": ("VIP CARD", (170, 130, 30), (45, 30, 8)),
})
TAG_CAT.update({"آتشبس": "ceasefire", "بیانیهنظامی": "milstmt", "تنگه": "strait", "خیزشمردمی": "uprising",
                "جامجهانی": "worldcup", "خبرصنعتی": "industry"})


# ───── قالب‌های جدید گزارش جنگ ─────
CREW = {"gnd": 4, "fighter": 1, "bomber": 5, "heli": 2, "drone": 0, "aa": 15, "navy": 180, "missile": 0, "bomb": 0}
CREW_K = {"inf": 2000, "sof": 600, "soldier": 1}


def crew_loss(lost):
    n = 0
    for k, q in lost.items():
        u = U.get(k)
        if not u:
            continue
        n += CREW_K.get(k, CREW.get(u["cat"], 0)) * q
    return n


def lost_value(lost):
    return sum(U[k]["cost"] * q for k, q in lost.items() if k in U)


def atk_kind(sent, mode):
    if mode in ("ground", "naval", "missile"):
        return mode
    w = {}
    for k, q in sent.items():
        cat = U[k]["cat"]
        w[cat] = w.get(cat, 0) + U[k]["atk"] * q
    best = max(w, key=w.get) if w else "fighter"
    return {"drone": "drone", "bomber": "bomber", "bomb": "bomber"}.get(best, "air")


def target_place(de):
    cts = [x["name"] for x in de.get("cities", []) if x.get("name")]
    if cts:
        return "%s، %s" % (random.choice(cts), cname(de))
    return cname(de)


def count_cat(sent, cats):
    return sum(q for k, q in sent.items() if U[k]["cat"] in cats)


def region_state(dmg):
    return "آسیب شدید" if dmg >= 0.5 else ("آسیب متوسط تا شدید" if dmg >= 0.3 else ("آسیب محدود" if dmg > 0.1 else "آسیب جزئی"))


def battle_report(kind, att, de, res, la, ld, cap, sent, m0, prov0):
    ground = kind == "ground"
    dmg = res.get("dmg", 0.0)
    win = res["win"]
    fin = (m0 - de["money"]) + lost_value(ld) * 0.6 + (dmg * income(de) * 24 if not ground else 0)
    if cap:
        fin = max(fin, 0.0)
    casu = crew_loss(ld) + (int(dmg * de["pop"] * 0.0004) if not ground else 0)
    heavy = "بسیار سنگین" if dmg >= 0.5 else ("سنگین" if dmg >= 0.25 else "متوسط")
    place = target_place(de)
    head = ["🏴 مهاجم: نیروهای %s" % cname(att), "🎯 هدف: %s" % place]
    result_ok = "موفق" if win else ("ناموفق" if (ground and res["R"] <= 0.9) or (not ground and dmg < 0.2) else "بی‌نتیجه")
    foot = ["━━━━━━━━━━━━━━━━━━━━", "📡 OPERATION STATUS: COMPLETED", "🕒 " + stamp()]
    if kind == "naval":
        ships = count_cat(sent, {"navy"})
        mis = count_cat(sent, {"missile"}) or ships * random.randint(120, 220)
        dships = sum(q for k, q in ld.items() if U[k]["cat"] == "navy")
        top = ["🌊⚓ NAVAL ASSAULT OPERATION ⚓🌊", "━━━━━━━━━━━━━━━━━━━━",
               "🚨 ناوگان دریایی نیروهای مهاجم وارد محدوده عملیاتی شد. یگان‌های دریایی با آغاز یک عملیات گسترده، حمله‌ای سنگین را علیه منطقه ساحلی دشمن آغاز کردند.",
               "💥 درگیری دریایی با تبادل آتش میان نیروهای دو طرف همراه شد و خسارات سنگینی به تجهیزات و تأسیسات نظامی منطقه وارد گردید.",
               "━━━━━━━━━━━━━━━━━━━━"]
        body = head + ["🚢 ناوگان اعزامی: %s فروند ناو جنگی" % m(ships), "🚀 موشک‌های مصرفی: %s فروند" % m(mis),
                       "💸 خسارت مالی: %s دلار" % dol(fin), "💀 خسارت جانی: %s نفر" % m(casu),
                       "🛳️ خسارت ناوگان مدافع: %s فروند" % m(dships),
                       "🛡️ وضعیت دفاع دریایی: %s" % ("تضعیف‌شده" if win else "مقاوم"),
                       "📊 وضعیت منطقه: %s" % ("خسارات گسترده" if dmg >= 0.3 else "خسارات محدود"),
                       "⚔️ نتیجه عملیات: %s" % ("موفقیت‌آمیز" if win else "ناموفق")]
        return "\n".join(top + body + foot)
    if kind == "missile":
        n = count_cat(sent, {"missile"})
        top = ["🚀⚠️ STRATEGIC MISSILE STRIKE ⚠️🚀", "━━━━━━━━━━━━━━━━━━━━",
               "🚨 سامانه‌های هشدار دفاعی در منطقه هدف فعال شدند. حمله موشکی گسترده در چارچوب یک عملیات نظامی آغاز شد.",
               "💥 چندین موشک به سمت منطقه هدف شلیک شدند. انفجارهای متوالی در محدوده موردنظر گزارش شده و خسارات سنگینی به زیرساخت‌های منطقه وارد شده است.",
               "━━━━━━━━━━━━━━━━━━━━"]
        body = head + ["🚀 نوع عملیات: Strategic Missile Strike", "📦 تعداد موشک: %s فروند" % m(n),
                       "💸 خسارت مالی: %s دلار" % dol(fin), "💀 خسارت جانی: %s نفر" % m(casu),
                       "💣 قدرت تخریبی: %s" % heavy, "🛡️ وضعیت پدافند: %s" % ("رهگیری %d٪" % int(res["inter"] * 100) if res["inter"] > 0 else "گزارش نشده"),
                       "📊 وضعیت منطقه: %s" % region_state(dmg), "⚔️ نتیجه عملیات: %s" % result_ok]
        return "\n".join(top + body + foot)
    if kind == "drone":
        n = count_cat(sent, {"drone"})
        top = ["🛸⚠️ STRATEGIC DRONE STRIKE ⚠️🛸", "━━━━━━━━━━━━━━━━━━━━",
               "🚨 سامانه‌های هشدار دفاعی در منطقه هدف فعال شدند. موجی از پهپادهای تهاجمی در چارچوب یک عملیات نظامی به سمت منطقه موردنظر اعزام شدند.",
               "💥 حملات پهپادی چندین نقطه از منطقه هدف را مورد اصابت قرار دادند. انفجارها و خسارات وارده در محدوده عملیات گزارش شده است.",
               "━━━━━━━━━━━━━━━━━━━━"]
        body = head + ["🛸 نوع عملیات: Strategic Drone Strike", "🚀 تعداد پهپاد: %s فروند" % m(n),
                       "💸 خسارت مالی: %s دلار" % dol(fin), "💀 خسارت جانی: %s نفر" % m(casu),
                       "💣 قدرت تخریبی: %s" % heavy, "🛡️ وضعیت پدافند: %s" % ("رهگیری %d٪" % int(res["inter"] * 100) if res["inter"] > 0 else "گزارش نشده"),
                       "📊 وضعیت منطقه: %s" % region_state(dmg), "⚔️ نتیجه عملیات: %s" % result_ok]
        return "\n".join(top + body + foot)
    if kind == "bomber":
        n = count_cat(sent, {"bomber"}) or count_cat(sent, {"bomb"})
        top = ["💣⚠️ STRATEGIC BOMBING OPERATION ⚠️💣", "━━━━━━━━━━━━━━━━━━━━",
               "🚨 هشدارهای اضطراری در منطقه هدف فعال شدند. گروهی از بمب‌افکن‌های راهبردی در چارچوب یک عملیات هوایی گسترده به سمت منطقه موردنظر اعزام شدند.",
               "💥 موجی از انفجارهای مهیب در منطقه هدف گزارش شده است. زیرساخت‌ها و تأسیسات مختلف دچار خسارات گسترده شده‌اند.",
               "━━━━━━━━━━━━━━━━━━━━"]
        body = head + ["💣 نوع عملیات: Strategic Bomber Strike", "🛩️ تعداد بمب‌افکن: %s فروند" % m(n),
                       "💸 خسارت مالی: %s دلار" % dol(fin), "💀 خسارت جانی: %s نفر" % m(casu),
                       "💣 قدرت تخریبی: %s" % heavy, "🛡️ وضعیت پدافند: %s" % ("رهگیری %d٪" % int(res["inter"] * 100) if res["inter"] > 0 else "گزارش نشده"),
                       "📊 وضعیت منطقه: %s" % ("تخریب گسترده" if dmg >= 0.4 else region_state(dmg)), "⚔️ نتیجه عملیات: %s" % result_ok]
        return "\n".join(top + body + foot)
    if kind == "air":
        n = count_cat(sent, {"fighter", "heli"})
        top = ["✈️⚠️ STRATEGIC AIRSTRIKE ⚠️✈️", "━━━━━━━━━━━━━━━━━━━━",
               "🚨 آژیرهای هشدار هوایی در منطقه هدف به صدا درآمدند. اسکادرانی از جنگنده‌های نظامی در چارچوب یک عملیات هوایی گسترده وارد حریم هوایی منطقه شدند.",
               "💥 حملات هوایی با استفاده از جنگنده‌های رزمی انجام شد. انفجارهای متعدد و خسارات گسترده به تأسیسات و زیرساخت‌های منطقه گزارش شده است.",
               "━━━━━━━━━━━━━━━━━━━━"]
        body = head + ["✈️ نوع عملیات: Strategic Airstrike", "🛩️ تعداد جنگنده: %s فروند" % m(n),
                       "💸 خسارت مالی: %s دلار" % dol(fin), "💀 خسارت جانی: %s نفر" % m(casu),
                       "💣 قدرت تخریبی: %s" % heavy, "🛡️ وضعیت پدافند: %s" % ("رهگیری %d٪" % int(res["inter"] * 100) if res["inter"] > 0 else "گزارش نشده"),
                       "📊 وضعیت منطقه: %s" % region_state(dmg), "⚔️ نتیجه عملیات: %s" % result_ok]
        return "\n".join(top + body + foot)
    # زمینی
    troops = sum(q * (CREW_K.get(k, 4) if k in CREW_K else 1) for k, q in sent.items() if U[k]["cat"] == "gnd")
    armor = sum(q for k, q in sent.items() if U[k]["cat"] == "gnd" and k not in CREW_K)
    top = ["⚔️🚨 LARGE-SCALE GROUND OFFENSIVE 🚨⚔️", "━━━━━━━━━━━━━━━━━━━━",
           "🚨 نیروهای زمینی مهاجم عملیات تهاجمی گسترده‌ای را علیه مواضع کشور هدف آغاز کردند. درگیری‌های سنگین در مناطق مرزی و خطوط دفاعی گزارش شده است.",
           "🔥 یگان‌های نظامی وارد مناطق درگیری شده و نبردهای شدیدی میان نیروهای مهاجم و مدافع شکل گرفته است. گزارش‌ها از خسارات نظامی و تغییر وضعیت برخی مناطق حکایت دارند.",
           "━━━━━━━━━━━━━━━━━━━━"]
    if cap and win:
        res_t, state = "🏴 نتیجه عملیات: پیشروی مهاجم (فتح %d استان)" % cap[0], "درگیری شدید"
    elif res["R"] <= 0.9:
        res_t, state = "🏴 نتیجه عملیات: حمله دفع شد", "مقاومت موفق"
    else:
        res_t, state = "🏴 نتیجه عملیات: نبرد بی‌نتیجه", "درگیری شدید"
    body = head + ["⚔️ نوع عملیات: Ground Offensive", "🪖 تعداد نیرو: %s نفر" % m(troops), "🚛 تجهیزات زرهی: %s دستگاه" % m(armor),
                   "💸 خسارت مالی: %s دلار" % dol(fin), "💀 تلفات انسانی: %s نفر" % m(crew_loss(la) + casu),
                   "🛡️ وضعیت دفاعی: %s" % ("مقاومت فعال" if not win else "در حال شکست"), "📊 وضعیت منطقه: %s" % state, res_t]
    return "\n".join(top + body + foot)


def nuke_report(att, de, key, res):
    top = ["☢️⚠️ STRATEGIC NUCLEAR STRIKE ⚠️☢️", "━━━━━━━━━━━━━━━━━━━━",
           "🚨 آژیرهای هشدار در منطقه هدف به صدا درآمدند. یک حمله هسته‌ای گسترده در چارچوب عملیات نظامی آغاز شد.", ""]
    if res["hit"]:
        top += ["💥 انفجار هسته‌ای، آسمان منطقه را روشن کرد و موج عظیمی از انرژی، محدوده هدف را دربر گرفت."]
    else:
        top += ["🛡 سامانه‌های پدافندی موشک را رهگیری کردند و حمله ناکام ماند."]
    top += ["━━━━━━━━━━━━━━━━━━━━", ""]
    casu = (crew_loss(res.get("lost", {})) + int(res.get("pop", 0))) if res["hit"] else 0
    body = ["🏴 مهاجم: نیروهای %s" % cname(att), "🎯 هدف: %s" % target_place(de), "☢️ نوع عملیات: Nuclear Strike", "🚀 تعداد کلاهک: 1",
            "💸 خسارت مالی: %s دلار" % dol(res.get("mloss", 0)), "💀 خسارت جانی: %s نفر" % m(casu),
            "💣 قدرت تخریبی: %s" % ("حداکثری" if res["hit"] else "هیچ"),
            "🛡️ وضعیت پدافند: %s" % ("رهگیری شد (احتمال %d٪)" % int(res["p"] * 100) if not res["hit"] else "شکسته شد"),
            "📊 وضعیت منطقه: %s" % ("آسیب شدید" if res["hit"] else "سالم"), "⚔️ نتیجه عملیات: %s" % ("موفق" if res["hit"] else "ناموفق")]
    if res.get("cap"):
        body.append("🗺 %d استان از نقشه پاک شد." % res["cap"][0])
        if res["cap"][2]:
            body.append("💀 %s به‌طور کامل سقوط کرد!" % cname(de))
    foot = ["", "━━━━━━━━━━━━━━━━━━━━", "📡 OPERATION STATUS: COMPLETED", "🕒 " + stamp()]
    return "\n".join(top + body + foot)


def statement_text(c, t, kind="off"):
    nm = "%s %s" % (c["fa"], flag(c["iso"]))
    if kind == "mil":
        head = ["⚔️ MILITARY OFFICIAL STATEMENT", "━━━━━━━━━━━━━━━━━━━━", "🏴 کشور: %s" % nm, "🎖️ فرمانده: %s" % c["leader"],
                "━━━━━━━━━━━━━━━━━━━━"]
        tag = "#بیانیه_نظامی"
    else:
        head = ["📜 OFFICIAL STATEMENT", "━━━━━━━━━━━━━━━━━━━━", "🏳️ نام کشور: %s" % nm, "👤 رهبر: %s" % c["leader"],
                "━━━━━━━━━━━━━━━━━━━━"]
        tag = "#بیانیه"
    return "\n".join(head + [Q_OPEN, t.strip(), Q_CLOSE, "", tag])


@route(B_SENDMIL)
def r_sendmil(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    r_sendstmt(uid)
    if CTX.get(uid):
        STMT_KIND[uid] = "mil"


# ───── آتش‌بس موقت سازمان ملل + پنل ملل ─────
A_UN, UA_CEASE, UA_UNIONS = "🌐 پنل سازمان ملل", "🕊 آتش‌بس موقت ۲۴ ساعته", "🛡 مدیریت اتحادها"
UN_PANEL_ROWS = [[A_REQ, UA_CEASE], [UA_UNIONS, A_COUNTRIES], [A_PANEL]]


def ceasefire_between(a, b):
    t = now()
    cf = EXT()["cease"]
    cf[:] = [x for x in cf if x["until"] > t]
    return any({x["a"], x["b"]} == {a, b} for x in cf)


@route(A_UN, admin=True)
def a_un(uid):
    back_to(uid, "🌐 پنل سازمان ملل\n• تأیید درخواست‌ها (گرفتن/تغییر کشور)\n• آتش‌بس موقت بین دو کشور\n• مدیریت اتحادها (حذف عضو، ظرفیت)", UN_PANEL_ROWS)


@route(UA_CEASE, admin=True)
def ua_cease(uid):
    pick_country(uid, "🕊 کشور اول آتش‌بس؟", lambda a: ua_cease2(uid, a), lambda x: x["alive"] and x["owner"])


def ua_cease2(uid, a):
    pick_country(uid, "🕊 کشور دوم؟", lambda b: ua_cease3(uid, a, b), lambda x: x["alive"] and x["owner"] and x["iso"] != a)


def ua_cease3(uid, a, b):
    ca, cb = C(a), C(b)
    EXT()["cease"].append({"a": a, "b": b, "until": now() + 86400})
    announce("🌐🕊️ UNITED NATIONS | TEMPORARY CEASEFIRE\n━━━━━━━━━━━━━━━━━━━━\n\n"
             "🚨 سازمان ملل متحد میان دو کشور توافق آتش‌بس موقت ۲۴ ساعته برقرار کرد.\n\n"
             "🏳️ کشور اول: %s\n🏳️ کشور دوم: %s\n🕊️ مدت آتش‌بس: ۲۴ ساعت\n⚖️ میانجی‌گر: سازمان ملل متحد (UN)\n"
             "⚔️ وضعیت درگیری: توقف موقت عملیات نظامی\n🤝 وضعیت توافق: لازم‌الاجرا\n⏳ مدت اعتبار: ۲۴ ساعت از زمان اعلام توافق\n\n"
             "━━━━━━━━━━━━━━━━━━━━\n📡 STATUS: TEMPORARY CEASEFIRE ACTIVE\n#آتش_بس" % (cname(ca), cname(cb)), cat="ceasefire", iso=(a, b))
    for iso in (a, b):
        notify_country(iso, "🕊 سازمان ملل یک آتش‌بس ۲۴ ساعته بین %s و %s برقرار کرد." % (cname(ca), cname(cb)))
    back_to(uid, "✅ آتش‌بس اعلام شد.", UN_PANEL_ROWS)


# مدیریت اتحادها
UA_KICK, UA_CAP = "👢 حذف عضو از اتحاد", "🔢 تغییر ظرفیت اتحاد"


@route(UA_UNIONS, admin=True)
def ua_unions(uid):
    uns = list(DB["unions"].values())
    if not uns:
        return back_to(uid, "🛡 هیچ اتحادی وجود نداره.", UN_PANEL_ROWS)
    labels = {"%s (%d/%d)" % (un_label(un), len(un_members(un)), un_cap(un)): un for un in uns[:40]}
    L = ["🛡 اتحادها:"] + ["• %s — قدرت %s" % (k, m(un_power(un))) for k, un in labels.items()]
    ask(uid, "\n".join(L), lambda t: ua_union_pick(uid, labels, t), chunk(list(labels), 2) + [[A_UN]], back=False)


def ua_union_pick(uid, labels, t):
    un = labels.get(t)
    if not un:
        return ua_unions(uid)
    mem = ", ".join(cname(DB["countries"][i]) for i in un_members(un)) or "—"
    ask(uid, "🛡 %s\n👥 اعضا (%d/%d): %s\n💰 خزانه: %s M$" % (un_label(un), len(un_members(un)), un_cap(un), mem, m(un["bank"])),
        lambda x: ua_union_act(uid, un, x), [[UA_KICK, UA_CAP], [UA_UNIONS]], back=False)


def ua_union_act(uid, un, t):
    if squash(t) == squash(UA_KICK):
        mem = {cname(DB["countries"][i]): i for i in un_members(un)}
        if not mem:
            return ua_unions(uid)
        return ask(uid, "کدوم عضو حذف بشه؟", lambda x: ua_kick_do(uid, un, mem.get(x)), chunk(list(mem), 2) + [[UA_UNIONS]], back=False)
    if squash(t) == squash(UA_CAP):
        return ask(uid, "🔢 ظرفیت جدید اتحاد (فعلی %d) — عدد بنویس:" % un_cap(un), lambda x: ua_cap_do(uid, un, x),
                   [["4", "6", "8", "10"], ["15", "20", "30"]], back=False)
    ua_unions(uid)


def ua_kick_do(uid, un, iso):
    if not iso or iso not in un["members"]:
        return ua_unions(uid)
    c = C(iso)
    un_remove(iso, "اخراج توسط ادمین")
    notify_country(iso, "👢 ادمین کشورت رو از اتحاد «%s» حذف کرد." % un_label(un))
    back_to(uid, "✅ %s از اتحاد حذف شد." % cname(c), UN_PANEL_ROWS)


def ua_cap_do(uid, un, t):
    v = num(t)
    if not v or v < 1 or v > 200:
        return back_to(uid, "❌ عدد نامعتبر.", UN_PANEL_ROWS)
    un["capx"] = int(v)
    un_tell(un, "🔢 ظرفیت اتحاد توسط ادمین به %d کشور تغییر کرد." % int(v))
    back_to(uid, "✅ ظرفیت «%s» شد %d." % (un_label(un), int(v)), UN_PANEL_ROWS)


# درخواست تغییر کشور (تأیید ادمین)
B_CHANGE = "🔄 درخواست تغییر کشور"


@route(B_CHANGE)
def r_change(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if any(r["type"] == "change" and r["uid"] == uid for r in DB["requests"]):
        return menu(uid, "⏳ درخواست تغییر کشورت هنوز در انتظار ادمینه.")
    pick_country(uid, "🔄 می‌خوای به کدوم کشور آزاد منتقل بشی؟", lambda iso: change_send(uid, iso),
                 lambda x: x["alive"] and not x["owner"])


def change_send(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or d["owner"] or not d["alive"]:
        return menu(uid, "😕 این کشور در دسترس نیست.")
    r = {"id": nid(), "type": "change", "uid": uid, "old": c["iso"], "iso": iso, "leader": c["leader"], "t": now()}
    DB["requests"].append(r)
    notify_admins(req_text(r), [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]], [A_PANEL]])
    menu(uid, "✅ درخواست تغییر کشور برای ادمین ارسال شد ⏳")


def ext_req_text(r):
    if r["type"] == "change":
        a, b = C(r["old"]), C(r["iso"])
        return "🔄 درخواست تغییر کشور (%d)\n👤 %s\nاز: %s\nبه: %s" % (r["id"], ulabel(r["uid"]), cname(a) if a else r["old"], cname(b) if b else r["iso"])
    c = C(r["iso"])
    bk = BANKS[r["bank"]]
    return "💎 درخواست خرید کارت VIP (%d)\n👤 %s\n🏳️ %s\n🏦 %s\n💳 %s\n💰 قیمت: %s تومان" % (
        r["id"], ulabel(r["uid"]), cname(c) if c else r["iso"], bk["name"], r["card"], m(r["price"]))


def ext_approve(uid, r):
    if r["type"] == "change":
        new, old = C(r["iso"]), C(r["old"])
        if not new or not new["alive"] or new["owner"] or not old or old["owner"] != r["uid"]:
            tell(r["uid"], "😕 تغییر کشور ممکن نشد (شرایط عوض شده).", main_rows(r["uid"]))
            return back_to(uid, "⚠️ ممکن نبود؛ درخواست حذف شد.", ADMIN_ROWS)
        free_country(r["old"])
        assign(r["uid"], r["iso"], r["leader"])
        return back_to(uid, "✅ %s ← %s منتقل شد." % (ulabel(r["uid"]), cname(new)), ADMIN_ROWS)
    # کارت VIP
    c = C(r["iso"])
    if not c or not c["alive"] or r["card"] in EXT()["vip_owner"] or r["bank"] not in EXT()["banks"].get(r["iso"], {}):
        tell(r["uid"], "❌ خرید کارت VIP انجام نشد (کارت فروخته شده یا بانک تأسیس نشده).", main_rows(r["uid"]))
        return back_to(uid, "⚠️ انجام نشد.", ADMIN_ROWS)
    vip_activate(c, r["bank"], r["card"])
    back_to(uid, "✅ کارت VIP %s برای %s فعال شد." % (r["card"], cname(c)), ADMIN_ROWS)


# ───── بانک‌ها و کارت به کارت ─────
# حداقل/حداکثر انتقال به «دلار»؛ کارمزد به صورت کسری (۰.۰۳٪ = 0.0003)
BANKS = {
    "blue": {"name": "بلو بانک", "pre": "6219-86", "min": 1_000, "max": 500_000_000_000, "fee": 0.0003, "found": 500_000},
    "city": {"name": "سیتی‌بانک", "pre": "5287-34", "min": 500_000_000_000, "max": 1_000_000_000_000, "fee": 0.0005, "found": 2_000_000},
    "tej": {"name": "بانک تجارت", "pre": "5859-63", "min": 100_000_000, "max": 1_000_000_000_000, "fee": 0.0004, "found": 1_000_000},
    "arsh": {"name": "بانک ارشیا", "pre": "1111-11", "min": 100_000_000, "max": 100_000_000_000_000, "fee": 0.0001, "found": 3_000_000},
}
VIP_CARDS = {
    "blue": [("6219-8666-6666-6666", 10000), ("6219-8600-0000-0000", 10000)],
    "city": [("5287-3434-3434-3434", 5000), ("5287-3400-0000-0000", 10000), ("5287-3444-4444-4444", 15000)],
    "tej": [("5859-6333-3333-3333", 5000), ("5859-6300-0000-0000", 10000)],
    "arsh": [("1111-1111-1111-1111", 30000), ("1111-1100-0000-0000", 25000), ("1111-1122-2222-2222", 25000),
             ("1111-1122-1122-1122", 20000), ("1111-1112-1212-1212", 20000), ("1111-1166-6666-6666", 10000)],
}
VIP_ALL = {c for v in VIP_CARDS.values() for c, _p in v}
VIP_GIFT = {"std": {"iron": 100000, "oil": 100000, "elec": 50000, "_money": 200_000_000_000},
            "arsh": {"alu": 50000, "iron": 100000, "oil": 100000, "gold": 50000, "uranium": 300, "elec": 20000, "_money": 500_000_000_000}}
BK_MY, BK_FOUND, BK_TX, BK_VIP = "🏛 بانک‌های من", "➕ تأسیس بانک", "💳 کارت به کارت", "👑 کارت‌های VIP"
BANK_ROWS.insert(0, [BK_MY, BK_FOUND])
BANK_ROWS.insert(1, [BK_TX, BK_VIP])


def bank_btn(k):
    return "🏦 " + BANKS[k]["name"]


def new_card(k):
    e = EXT()
    for _ in range(200):
        d = BANKS[k]["pre"].replace("-", "") + "".join(random.choice("0123456789") for _ in range(10))
        card = "-".join(d[i:i + 4] for i in range(0, 16, 4))
        if card not in e["cards"] and card not in VIP_ALL:
            return card
    return card


def found_bank(c, k, announce_it=True):
    e = EXT()
    mybanks = e["banks"].setdefault(c["iso"], {})
    if k in mybanks:
        return mybanks[k]
    card = new_card(k)
    mybanks[k] = card
    e["cards"][card] = c["iso"]
    if announce_it:
        bn = BANKS[k]["name"]
        announce("🏛️ اعلام تأسیس مؤسسه بانکی جدید\n━━━━━━━━━━━━━━━━━━\n🌍 کشور: %s\n🏦 بانک تأسیس‌شده: %s\n"
                 "📅 وضعیت: تأسیس و راه‌اندازی موفق\n━━━━━━━━━━━━━━━━━━\n📢 کشور %s از تأسیس و راه‌اندازی بانک %s خبر داد. "
                 "این بانک از این پس به‌عنوان یکی از مراکز رسمی نقل‌وانتقال مالی در بازار جهانی فعالیت خواهد کرد.\n"
                 "🌐 WORLD BANKING NETWORK" % (cname(c), bn, cname(c), bn), cat="bankfound", iso=c["iso"])
    return card


@route(BK_MY)
def r_bk_my(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    mb = EXT()["banks"].get(c["iso"], {})
    if not mb:
        return back_to(uid, "🏛 هنوز هیچ بانکی تأسیس نکردی.\nبرای انتقال پول باید حداقل یک بانک داشته باشی (از «%s»)." % BK_FOUND, BANK_ROWS)
    L = ["🏛 بانک‌های %s" % cname(c), ""]
    for k, card in mb.items():
        b = BANKS[k]
        L += ["🏦 %s%s" % (b["name"], "  💎VIP" if EXT()["vip_owner"].get(card) == c["iso"] else ""), "💳 %s" % card,
              "   انتقال: %s تا %s دلار | کارمزد %s٪" % (dols(b["min"]), dols(b["max"]), ("%.3f" % (b["fee"] * 100)).rstrip("0").rstrip(".")), ""]
    back_to(uid, "\n".join(L), BANK_ROWS)


@route(BK_FOUND)
def r_bk_found(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    mb = EXT()["banks"].get(c["iso"], {})
    left = [k for k in BANKS if k not in mb]
    if not left:
        return back_to(uid, "✅ هر چهار بانک رو تأسیس کردی.", BANK_ROWS)
    L = ["➕ تأسیس بانک (از خزانه کم می‌شه)", ""] + ["%s — هزینه: %s دلار" % (bank_btn(k), dols(BANKS[k]["found"])) for k in left]
    ask(uid, "\n".join(L), lambda t: bk_found_do(uid, t), [[bank_btn(k)] for k in left])


def bk_found_do(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    k = next((k for k in BANKS if squash(bank_btn(k)) == squash(t) or squash(BANKS[k]["name"]) == squash(t)), None)
    if not k or k in EXT()["banks"].get(c["iso"], {}):
        return r_bk_found(uid)
    cost = BANKS[k]["found"] / 1e6
    if c["money"] < cost:
        return back_to(uid, "❌ برای تأسیس %s به %s دلار نیاز داری." % (BANKS[k]["name"], dols(BANKS[k]["found"])), BANK_ROWS)
    c["money"] -= cost
    card = found_bank(c, k)
    back_to(uid, "✅ %s تأسیس شد.\n💳 شماره کارتت: %s" % (BANKS[k]["name"], card), BANK_ROWS)


@route(BK_TX)
def r_bk_tx(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if frozen(uid):
        return
    mb = EXT()["banks"].get(c["iso"], {})
    if not mb:
        return back_to(uid, "🏛 برای انتقال پول باید اول یک بانک تأسیس کنی (از «%s»)." % BK_FOUND, BANK_ROWS)
    L = ["💳 کارت به کارت", "💰 موجودی: %s دلار" % dol(c["money"]), "", "کدوم بانک؟"]
    for k in mb:
        b = BANKS[k]
        L.append("%s | %s تا %s دلار | کارمزد %s٪" % (bank_btn(k), dols(b["min"]), dols(b["max"]), ("%.3f" % (b["fee"] * 100)).rstrip("0").rstrip(".")))
    ask(uid, "\n".join(L), lambda t: bk_tx_bank(uid, t), [[bank_btn(k)] for k in mb])


def bk_tx_bank(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    mb = EXT()["banks"].get(c["iso"], {})
    k = next((k for k in mb if squash(bank_btn(k)) == squash(t) or squash(BANKS[k]["name"]) == squash(t)), None)
    if not k:
        return r_bk_tx(uid)

    def h(x):
        if squash(x) == squash("🌍 انتخاب از لیست کشورها"):
            return pick_country(uid, "🌍 مقصد؟", lambda iso: bk_tx_amt(uid, k, iso), lambda y: y["alive"] and y["owner"] and y["iso"] != c["iso"])
        card = x.strip()
        iso = EXT()["cards"].get(card) or next((i for cd, i in EXT()["cards"].items() if en_digits(cd).replace("-", "") == en_digits(card).replace("-", "").replace(" ", "")), None)
        if iso and iso != c["iso"] and C(iso) and C(iso)["owner"]:
            return bk_tx_amt(uid, k, iso)
        hit = find_country(x, [y for y in DB["countries"].values() if y["alive"] and y["owner"] and y["iso"] != c["iso"]])
        if hit:
            return bk_tx_amt(uid, k, hit["iso"])
        tell(uid, "❓ کشور یا شماره کارت پیدا نشد.")
        bk_tx_bank(uid, t)

    ask(uid, "🏦 %s\nشماره کارت مقصد یا اسم کشور رو بنویس، یا از لیست انتخاب کن:" % BANKS[k]["name"], h, [["🌍 انتخاب از لیست کشورها"]])


def bk_tx_amt(uid, k, iso):
    b, d = BANKS[k], C(iso)
    ask(uid, "💵 مبلغ انتقال به %s (دلار)\nحداقل %s | حداکثر %s | کارمزد %s٪\nمثال: 5000000 یا 5m یا 2b یا 1t"
        % (cname(d), dols(b["min"]), dols(b["max"]), ("%.3f" % (b["fee"] * 100)).rstrip("0").rstrip(".")),
        lambda t: bk_tx_do(uid, k, iso, t), [["1m", "10m", "100m"], ["1b", "10b", "100b"], ["1t"]])


def bk_tx_do(uid, k, iso, t):
    c, d, b = mine(uid), C(iso), BANKS[k]
    if not c or not d or not d["owner"] or not d["alive"]:
        return back_to(uid, "❌ انتقال ممکن نیست.", BANK_ROWS)
    if frozen(uid):
        return
    a = bnum(t)
    if not a or a < b["min"] or a > b["max"]:
        return back_to(uid, "❌ مبلغ باید بین %s و %s دلار باشه." % (dols(b["min"]), dols(b["max"])), BANK_ROWS)
    if sanctioned_between(c["iso"], iso):
        return back_to(uid, "🚫 بین شما تحریمه؛ انتقال ممکن نیست.", BANK_ROWS)
    fee = a * b["fee"]
    if c["money"] * 1e6 < a + fee:
        return back_to(uid, "❌ پول کافی نیست (نیاز: %s دلار با کارمزد %s)." % (dols(a + fee), dols(fee)), BANK_ROWS)
    c["money"] -= (a + fee) / 1e6
    d["money"] += a / 1e6
    e = EXT()
    e["tx"] += 1
    code = "TX-%s-%05d" % (tnow().strftime("%y%m%d"), e["tx"] % 100000) + "".join(random.choice("0123456789ABCDEF") for _ in range(4))
    announce("💸 گزارش رسمی تراکنش بین‌المللی\n━━━━━━━━━━━━━━━━━━\n🌍 کشور مبدأ: %s\n🏦 بانک مبدأ: %s\n🌍 کشور مقصد: %s\n💰 مبلغ انتقال: %s دلار\n"
             "━━━━━━━━━━━━━━━━━━\n✅ تراکنش موفق\nمبلغ فوق با موفقیت از طریق شبکه بانکی %s به کشور %s ارسال شد.\n🔐 کد رهگیری: %s\n🌐 INTERNATIONAL BANKING SYSTEM"
             % (cname(c), b["name"], cname(d), dols(a), b["name"], cname(d), code), cat="banktx", iso=(c["iso"], iso))
    notify_country(iso, "💸 %s مبلغ %s دلار از طریق %s به خزانه‌ات واریز کرد!" % (cname(c), dols(a), b["name"]))
    quest_add(c, "deal")
    back_to(uid, "✅ انتقال انجام شد.\n💸 مبلغ: %s دلار | کارمزد: %s دلار\n🔐 کد رهگیری: %s" % (dols(a), dols(fee), code), BANK_ROWS)


@route(BK_VIP)
def r_bk_vip(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    ask(uid, "👑 کارت‌های VIP (فروش تومانی؛ ادمین بعد از پرداخت فعال می‌کنه)\nهر کارت تا آخر سیزن فقط مال یک کشوره.\nکدوم بانک؟",
        lambda t: bk_vip_bank(uid, t), [[bank_btn(k)] for k in BANKS])


def bk_vip_bank(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    k = next((k for k in BANKS if squash(bank_btn(k)) == squash(t)), None)
    if not k:
        return r_bk_vip(uid)
    vo = EXT()["vip_owner"]
    L = ["👑 کارت‌های VIP %s" % BANKS[k]["name"], ""]
    labels = {}
    for card, price in VIP_CARDS[k]:
        own = vo.get(card)
        L.append("💳 %s — %s تومان %s" % (card, m(price), ("✖️ فروخته شد (%s)" % cname(C(own))) if own else "✅ موجود"))
        if not own:
            labels["💳 %s" % card] = (card, price)
    g = VIP_GIFT["arsh" if k == "arsh" else "std"]
    L += ["", "🎁 هدیه‌ی خرید: " + " | ".join("%s %s" % (RES[x][0], m(v)) for x, v in g.items() if x != "_money") + " | 💵 %s دلار" % dols(g["_money"])]
    if not labels:
        return back_to(uid, "\n".join(L) + "\n\nهمه‌ی کارت‌ها فروخته شدن.", BANK_ROWS)
    ask(uid, "\n".join(L), lambda x: bk_vip_pick(uid, k, labels, x), [[l] for l in labels])


def bk_vip_pick(uid, k, labels, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    it = labels.get(t)
    if not it:
        return bk_vip_bank(uid, bank_btn(k))
    card, price = it
    if k not in EXT()["banks"].get(c["iso"], {}):
        return back_to(uid, "🏛 اول باید %s رو تأسیس کنی (از «%s»)." % (BANKS[k]["name"], BK_FOUND), BANK_ROWS)
    if EXT()["vip_owner"].get(card):
        return back_to(uid, "✖️ این کارت فروخته شده.", BANK_ROWS)
    if any(r["type"] == "vipcard" and r["card"] == card for r in DB["requests"]):
        return back_to(uid, "⏳ برای این کارت درخواست در انتظار هست.", BANK_ROWS)
    r = {"id": nid(), "type": "vipcard", "uid": uid, "iso": c["iso"], "bank": k, "card": card, "price": price, "t": now()}
    DB["requests"].append(r)
    notify_admins(req_text(r), [["✅ تایید %d" % r["id"], "🚫 رد درخواست %d" % r["id"]], [A_PANEL]])
    back_to(uid, "✅ درخواست خرید کارت VIP ثبت شد. ادمین برای پرداخت %s تومان هماهنگ می‌کنه ⏳" % m(price), BANK_ROWS)


def vip_activate(c, k, card):
    e = EXT()
    mb = e["banks"].setdefault(c["iso"], {})
    old = mb.get(k)
    if old:
        e["cards"].pop(old, None)
    mb[k] = card
    e["cards"][card] = c["iso"]
    e["vip_owner"][card] = c["iso"]
    g = VIP_GIFT["arsh" if k == "arsh" else "std"]
    for x, v in g.items():
        if x == "_money":
            c["money"] += v / 1e6
        else:
            c["res"][x] = c["res"].get(x, 0.0) + v
    notify_country(c["iso"], "💎 کارت VIP %s برات فعال شد و هدیه‌ها به حسابت اضافه شد! 🎉" % card)
    announce("💎 کارت VIP فروخته شد!\n🏳️ %s شماره کارت اختصاصی %s را تا پایان سیزن در اختیار گرفت.\n💳 %s\n#بانک" % (
        cname(c), BANKS[k]["name"], card), cat="vipcard", iso=c["iso"])


A_BANKADM = "🏦 مدیریت بانک‌ها"
A_SEASON = "🏁 پایان سیزن (آزادسازی کارت‌های VIP)"


@route(A_BANKADM, admin=True)
def a_bankadm(uid):
    e = EXT()
    L = ["🏦 مدیریت بانک‌ها", "کشورهای دارای بانک: %d" % len(e["banks"]), ""]
    for k in BANKS:
        n = sum(1 for mb in e["banks"].values() if k in mb)
        L.append("%s: %d بانک تأسیس‌شده" % (BANKS[k]["name"], n))
    L += ["", "💎 کارت‌های VIP فروخته‌شده:"] + ["• %s ← %s" % (cd, cname(C(i))) for cd, i in e["vip_owner"].items() if C(i)] or ["—"]
    ask(uid, "\n".join(L), lambda t: a_bankadm2(uid, t), [[A_SEASON], [A_PANEL]], back=False)


def a_bankadm2(uid, t):
    if squash(t) != squash(A_SEASON):
        return a_bankadm(uid)
    e = EXT()
    n = 0
    for card, iso in list(e["vip_owner"].items()):
        for k, cd in list(e["banks"].get(iso, {}).items()):
            if cd == card:
                e["cards"].pop(card, None)
                nc = new_card(k)
                e["banks"][iso][k] = nc
                e["cards"][nc] = iso
        n += 1
    e["vip_owner"].clear()
    announce("🏁 پایان سیزن! همه‌ی کارت‌های VIP آزاد شدند و دوباره قابل خریدن.\n#بانک", cat="bankfound")
    back_to(uid, "✅ %d کارت VIP آزاد شد." % n, ADMIN_ROWS)


# ───── بازار منابع (تابلو + فروش تک‌تک منابع) ─────
SELL_RES = ["oil", "iron", "alu", "gold", "uranium", "elec"]
SELL_LAB = {"oil": "فروش نفت🛢️", "iron": "فروش آهن🔩", "alu": "فروش آلومینیوم⛏", "gold": "فروش طلا🥇", "uranium": "فروش اورانیوم☢️", "elec": "فروش برق⚡"}
B_BOARD, B_BUY = "📊 تابلو بازار", "📥 خرید منابع"


def trade_blocked(c):
    return False


def strait_status_lines():
    return []


def board_text():
    rep = EXT()["rep"]
    prev = rep.get("board_prev", {})
    L = ["🌍 MARKET CONTROL", "📊 تابلو بازار جهانی منابع (قیمت هر ۱۰۰۰ واحد، دلار)", "━━━━━━━━━━━━━━━━━━", ""]
    for k in ["oil", "iron", "alu", "gold", "uranium"]:
        pr = M2D(res_price(k))
        old = prev.get(k)
        ch = (pr / old - 1) * 100 if old else 0.0
        ar = "📈" if ch >= 0 else "📉"
        L += ["%s %s" % RES[k], "💰 %s 　%s %+.1f%% %s" % (dols(pr), ar, ch, "🟢" if ch >= 0 else "🔴"), ""]
    L.append("━━━━━━━━━━━━━━━━━━")
    st = strait_status_lines()
    if st:
        L += ["🌊 CHOKEPOINT STATUS", ""] + st + ["", "━━━━━━━━━━━━━━━━━━"]
    L += ["📡 وضعیت بازار: 🟢 فعال", "⏱ بروزرسانی: لحظاتی پیش"]
    return "\n".join(L)


def board_tick(t):
    rep = EXT()["rep"]
    if t - rep.get("board_snap_t", 0) >= 3600:
        rep["board_prev"] = dict(rep.get("board_cur") or {})
        rep["board_cur"] = {k: M2D(res_price(k)) for k in RES}
        rep["board_snap_t"] = t
    h = DB["settings"].get("board_h", 6)
    if h and t - rep.get("board_t", 0) >= h * 3600:
        if rep.get("board_t"):
            announce(board_text(), cat="market")
        rep["board_t"] = t


EXT_TICKS.append(board_tick)


@route(B_MARKET)
def r_market(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = [board_text(), "", "📦 انبار شما:"] + ["%s %s: %s" % (RES[k][0], RES[k][1], m(c["res"][k])) for k in SELL_RES]
    L.append("💰 موجودی: %s دلار | کارمزد ۳٪" % dol(c["money"]))
    rows = chunk([SELL_LAB[k] for k in SELL_RES], 2) + [[B_BUY, B_BOARD]]
    ask(uid, "\n".join(L), lambda t: mkt_main(uid, t), rows)


def mkt_main(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    s = squash(t)
    if s == squash(B_BOARD):
        return r_market(uid)
    if s == squash(B_BUY):
        return mkt_side(uid, "خرید")
    k = next((k for k in SELL_RES if squash(SELL_LAB[k]) == s), None)
    if not k:
        return r_market(uid)
    if trade_blocked(c):
        return back_to(uid, "🚢 کشورت تحت محاصره‌ی دریاییه؛ تجارت متوقفه!", ECO_ROWS)
    ask(uid, "💰 فروش %s %s\n━━━━━━━━━━━━━━━━━\n\n📦 موجودی شما در انبار: %s\n💵 قیمت هر ۱۰۰۰ واحد: %s دلار\n\n"
             "📝 تعداد واحدی که می‌خوای بفروشی رو بفرست:\n(مثال: 100 یا 50%%)" % (RES[k][0], RES[k][1], m(c["res"][k]), dols(M2D(res_price(k)))),
        lambda x: mkt_do(uid, True, k, x), [["25%", "50%", "100%"]])


# ───── گزارش‌های دوره‌ای: کریپتو (۳۰ دقیقه) و گردش اقتصاد جهانی (۱۲ ساعت) ─────
COIN_ORDER = [("BTC", "₿ BITCOIN"), ("ETH", "Ξ ETHEREUM"), ("DOGE", "Ð DOGE"), ("SOL", "◎ SOLANA")]


def usd_fmt(x):
    if x >= 100:
        return "{:,.0f}".format(x)
    if x >= 1:
        return "{:,.2f}".format(x)
    return ("{:.10f}".format(x)).rstrip("0").rstrip(".")


CG_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "DOGE": "dogecoin", "SOL": "solana"}


def cg_prices():
    """قیمت واقعی از CoinGecko؛ اگه در دسترس نبود None."""
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": ",".join(CG_IDS.values()), "vs_currencies": "usd", "include_24hr_change": "true"}, timeout=8)
        js = r.json()
        return {sym: (float(js[i]["usd"]), float(js[i].get("usd_24h_change") or 0.0)) for sym, i in CG_IDS.items()}
    except Exception:  # noqa: BLE001
        return None


def crypto_report():
    rep = EXT()["rep"]
    prev = rep.get("crypto_prev", {})
    real = cg_prices()
    L = ["📊 صرافی جهانی | بازار کریپتو", "🌐 گزارش ارز دیجیتال | ساعت %s" % tnow().strftime("%H:%M"), "━━━━━━━━━━━━━━━━━━━━"]
    cur = {}
    for sym, nm in COIN_ORDER:
        if real:
            p, ch = real[sym]
        else:
            p = M2D(coin_price(sym))
            o = prev.get(sym)
            ch = (p / o - 1) * 100 if o else 0.0
        cur[sym] = p
        L += [nm, "$%s %s %.2f%%" % (usd_fmt(p), "▲" if ch >= 0 else "▼", abs(ch)), ""]
    L += ["━━━━━━━━━━━━━━━━━━━━", "📡 منبع: " + ("بازار عمومی CoinGecko" if real else "بازار کریپتو جهانی"),
          "⚠️ اطلاعات نمایشی‌اند؛ دارایی و معاملهٔ واقعی نیستند.", "#کریپتو"]
    rep["crypto_prev"] = cur
    return "\n".join(L)


def rank_report():
    cs = [c for c in DB["countries"].values() if c["owner"] and c["alive"]]
    if not cs:
        return None
    top = sorted(cs, key=score, reverse=True)[:10]
    L = ["🏆 رده‌بندی ساعتی فرماندهان", "━━━━━━━━━━━━━━━━━━"]
    for i, c in enumerate(top, 1):
        L.append("%d. %s — ⭐ %s | 💰 %s" % (i, cname(c), "{:,.2f}".format(score(c)).rstrip("0").rstrip("."), dol(c["money"])))
    dep = sorted(cs, key=dep_total, reverse=True)[:10]
    L += ["", "🏦 برترین سپرده‌گذاران بانک جهانی:"]
    for i, c in enumerate(dep, 1):
        L.append("%d. %s — %s دلار" % (i, cname(c), dol(dep_total(c))))
    L += ["", "#رده_بندی"]
    return "\n".join(L)


def econ_report():
    rep = EXT()["rep"]
    total = M2D(sum(c["money"] for c in DB["countries"].values() if c["owner"] and c["alive"]))
    old = rep.get("econ_total")
    ch = total - old if old is not None else 0.0
    rep["econ_total"] = total
    return ("📊 گزارش رسمی گردش حساب اقتصاد جهانی\n━━━━━━━━━━━━━━━━━━\n\n🌍 بانک مرکزی جهان | World Bank\n\n"
            "💰 مجموع کل موجودی پول بازیکنان: %s دلار\n\n💹 تغییرات موجودی نسبت به گزارش قبلی: %s%s دلار\n\n━━━━━━━━━━━━━━━━━━\n\n"
            "⚙️ این گزارش به‌صورت خودکار توسط سیستم اقتصادی بازی منتشر شده است.\n🌐 WORLD WAR | GLOBAL ECONOMY"
            % (dols(total), "+" if ch >= 0 else "-", dols(abs(ch))))


def report_tick(t):
    rep = EXT()["rep"]
    if DB["settings"]["paused"]:
        return
    if t - rep.get("crypto_t", 0) >= 1800:
        first = not rep.get("crypto_t")
        rep["crypto_t"] = t
        txt = crypto_report()
        if not first:
            announce(txt, cat="crypto")
    if t - rep.get("rank_t", 0) >= 3600:
        first = not rep.get("rank_t")
        rep["rank_t"] = t
        txt = rank_report()
        if txt and not first:
            announce(txt, cat="economy")
    if t - rep.get("econ_t", 0) >= 12 * 3600:
        first = not rep.get("econ_t")
        rep["econ_t"] = t
        txt = econ_report()
        if not first:
            announce(txt, cat="economy")


EXT_TICKS.append(report_tick)


# ───── بکاپ خودکار + ریست کامل/ساعتی ─────
BK_DIR = os.environ.get("WW_BACKUPS", "ww_backups")
A_BKP, A_FULLRESET, A_HRESET = "🕰 بکاپ و ریست", "♻️ ریست کامل بازی", "🕰 ریست ساعتی"


def snap_list():
    out = []
    if os.path.isdir(BK_DIR):
        for fn in os.listdir(BK_DIR):
            mt = re.match(r"^(?:snap|pre)_(\d+)\.json\.gz$", fn)
            if mt:
                out.append((int(mt.group(1)), os.path.join(BK_DIR, fn)))
    return sorted(out)


def snap_take(tag="snap"):
    os.makedirs(BK_DIR, exist_ok=True)
    path = os.path.join(BK_DIR, "%s_%d.json.gz" % (tag, int(now())))
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False)
    keep = now() - 48 * 3600
    for ts, p in snap_list():
        if ts < keep:
            try:
                os.remove(p)
            except OSError:
                pass
    return path


def snap_tick(t):
    rep = EXT()["rep"]
    if t - rep.get("snap_t", 0) >= 1800:
        rep["snap_t"] = t
        try:
            snap_take()
        except Exception as e:  # noqa: BLE001
            print("snapshot error:", e)


EXT_TICKS.append(snap_tick)


def restore_snap(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        new = json.load(f)
    keep = {"settings": DB["settings"], "offset": DB.get("offset"), "admin_code": DB.get("admin_code")}
    cur_users = DB["users"]
    DB.clear()
    DB.update(new)
    DB.update(keep)
    for i, u in cur_users.items():                  # زبان و آخرین چت کاربران حفظ بشه
        if i in DB["users"]:
            DB["users"][i]["lang"] = u.get("lang", "fa")
            DB["users"][i]["chat"] = u.get("chat", i)
    for c in DB["countries"].values():
        ensure(c)
    init_market()
    for i in list(CTX):
        clear(i)
    ATK.clear()
    save()


@route(A_BKP, admin=True)
def a_bkp(uid):
    sn = snap_list()
    rng = ("از %s تا %s" % (datetime.datetime.utcfromtimestamp(sn[0][0] + 12600).strftime("%m-%d %H:%M"),
                            datetime.datetime.utcfromtimestamp(sn[-1][0] + 12600).strftime("%m-%d %H:%M"))) if sn else "هنوز بکاپی گرفته نشده"
    ask(uid, "🕰 بکاپ و ریست\n\n📦 بکاپ‌ها (هر ۳۰ دقیقه، ۴۸ ساعت اخیر): %d عدد — %s (به وقت تهران)\n\n"
             "• %s: کل بازی از صفر شروع می‌شه.\n• %s: بازی به قبل از یک ساعت مشخص برمی‌گرده." % (len(sn), rng, A_FULLRESET, A_HRESET),
        lambda t: a_bkp2(uid, t), [[A_FULLRESET, A_HRESET], [A_PANEL]], back=False)


def a_bkp2(uid, t):
    if squash(t) == squash(A_FULLRESET):
        return a_reset(uid)
    if squash(t) == squash(A_HRESET):
        return ask(uid, "🕰 بازی به قبل از چه ساعتی برگرده؟ (به وقت تهران)\nمثال: 9 یا 21:30\n(نزدیک‌ترین بکاپ قبل از اون ساعت پیدا می‌شه)",
                   lambda x: a_hreset(uid, x), [["9", "12", "18", "21"]])
    a_bkp(uid)


def a_hreset(uid, t):
    s = en_digits(t).strip().replace(".", ":")
    mt = re.match(r"^(\d{1,2})(?::(\d{2}))?$", s)
    if not mt:
        return back_to(uid, "❌ ساعت نامعتبر. مثلاً 9 یا 21:30 بنویس.", ADMIN_ROWS)
    hh, mm_ = int(mt.group(1)), int(mt.group(2) or 0)
    if hh > 23 or mm_ > 59:
        return back_to(uid, "❌ ساعت نامعتبر.", ADMIN_ROWS)
    tn = tnow()
    target = tn.replace(hour=hh, minute=mm_, second=0, microsecond=0)
    if target > tn:
        target -= datetime.timedelta(days=1)
    ts_target = (target - datetime.timedelta(seconds=12600) - datetime.datetime(1970, 1, 1)).total_seconds()
    cand = [(ts, p) for ts, p in snap_list() if ts <= ts_target]
    if not cand:
        return back_to(uid, "❌ بکاپی قبل از %s پیدا نشد." % target.strftime("%m-%d %H:%M"), ADMIN_ROWS)
    ts, path = cand[-1]
    when = datetime.datetime.utcfromtimestamp(ts + 12600).strftime("%Y-%m-%d %H:%M")
    ask(uid, "⚠️ بازی به بکاپ %s (به وقت تهران) برمی‌گرده و هر چی بعدش اتفاق افتاده پاک می‌شه.\n(قبلش از وضعیت فعلی هم بکاپ می‌گیرم)\nمطمئنی؟" % when,
        lambda x: a_hreset2(uid, path, when, x), [["⚠️ بله، برگردون", "❌ انصراف"]])


def a_hreset2(uid, path, when, t):
    if "بله" not in t:
        return back_to(uid, "لغو شد.", ADMIN_ROWS)
    try:
        snap_take("pre")
        restore_snap(path)
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        return back_to(uid, "❌ بازگردانی ناموفق: %s" % str(e)[:150], ADMIN_ROWS)
    announce("🕰 بازی به وضعیت %s برگشت.\n#اعلامیه_ادمین" % when, cat="admin")
    back_to(uid, "✅ بازی به بکاپ %s برگشت." % when, ADMIN_ROWS)


# ───── ردیف‌های پنل ادمین (اضافه‌شده) ─────
ADMIN_ROWS.insert(-2, [A_WARS, A_UN])
ADMIN_ROWS.insert(-2, [A_BANKADM, A_BKP])



# ═════════════════════════════════════════════════════════════════════
# ═════════════ آپدیت بزرگ ۲ — بخش دوم ═════════════
# خیزش مردمی، تنگه‌ها و محاصره، سایبری کریپتو + فایروال جهانی، برند خودرو، جام جهانی
# ═════════════════════════════════════════════════════════════════════

CAPS_RAW = """US واشنگتن|CN پکن|RU مسکو|GB لندن|FR پاریس|DE برلین|IN دهلی نو|JP توکیو|TR آنکارا|IR تهران|IL اورشلیم|KR سئول|SA ریاض|IT رم|ES مادرید|PL ورشو|UA کیف|PK اسلام‌آباد|EG قاهره|BR برازیلیا|AU کانبرا|CA اتاوا|KP پیونگ‌یانگ|ID جاکارتا|MX مکزیکوسیتی|ZA پرتوریا|IQ بغداد|AZ باکو|GR آتن|SE استکهلم|AE ابوظبی|AR بوئنوس‌آیرس|TH بانکوک|VN هانوی|NG ابوجا|CU هاوانا|VE کاراکاس|AM ایروان|BY مینسک|AL تیرانا|AD آندورا لا ویا|AT وین|BE بروکسل|BA سارایوو|BG صوفیه|HR زاگرب|CY نیکوزیا|CZ پراگ|DK کپنهاگ|EE تالین|FI هلسینکی|HU بوداپست|IS ریکیاویک|IE دوبلین|LV ریگا|LI فادوتس|LT ویلنیوس|LU لوکزامبورگ|MT والتا|MD کیشینیو|MC موناکو|ME پودگوریتسا|NL آمستردام|MK اسکوپیه|NO اسلو|PT لیسبون|RO بخارست|SM سن مارینو|RS بلگراد|SK براتیسلاوا|SI لیوبلیانا|CH برن|VA شهر واتیکان|GE تفلیس|AF کابل|BH منامه|BD داکا|BT تیمفو|BN بندر سری بگاوان|KH پنوم‌پن|JO عمان|KZ آستانه|KW شهر کویت|KG بیشکک|LA ویانتیان|LB بیروت|MY کوالالامپور|MV مالـه|MN اولان‌باتور|MM نایپیداو|NP کاتماندو|OM مسقط|PH مانیل|QA دوحه|SG سنگاپور|LK کلمبو|SY دمشق|TJ دوشنبه|TL دیلی|TM عشق‌آباد|UZ تاشکند|YE صنعا|PS رام‌الله|TW تایپه|DZ الجزیره|AO لوآندا|BJ پورتو نوو|BW گابورون|BF واگادوگو|BI گیتگا|CV پرایا|CM یائونده|CF بانگی|TD انجامنا|KM مورونی|CG برازاویل|CD کینشاسا|CI یاموسوکرو|DJ جیبوتی|GQ مالابو|ER اسمره|SZ مبابانه|ET آدیس‌آبابا|GA لیبرویل|GM بانجول|GH آکرا|GN کوناکری|GW بیسائو|KE نایروبی|LS ماسرو|LR مونروویا|LY طرابلس|MG آنتاناناریو|MW لیلانگوه|ML باماکو|MR نواکشوط|MU پورت‌لوئیس|MA رباط|MZ ماپوتو|NA ویندهوک|NE نیامی|RW کیگالی|ST سائوتومه|SN داکار|SC ویکتوریا|SL فری‌تاون|SO مقدیشو|SS جوبا|SD خارطوم|TZ دودوما|TG لومه|TN تونس|UG کامپالا|ZM لوزاکا|ZW هراره|AG سنت جان|BS نسائو|BB بریج‌تاون|BZ بلموپان|BO سوکره|CL سانتیاگو|CO بوگوتا|CR سن‌خوزه|DM روزو|DO سانتو دومینگو|EC کیتو|SV سن‌سالوادور|GD سنت جورج|GT گواتمالا سیتی|GY جورج‌تاون|HT پورتوپرنس|HN تگوسیگالپا|JM کینگستون|NI ماناگوا|PA پاناما سیتی|PY آسونسیون|PE لیما|KN باستر|LC کستری|VC کینگزتاون|SR پاراماریبو|TT پورت آو اسپین|UY مونته‌ویدئو|FJ سووا|KI تاراوا|MH مجورو|FM پالیکیر|NR یارن|NZ ولینگتون|PW نگرولمود|PG پورت مورزبی|WS آپیا|SB هونیارا|TO نوکوآلوفا|TV فونافوتی|VU پورت ویلا"""
CAPITALS = dict(x.split(" ", 1) for x in CAPS_RAW.split("|"))


def capital_of(c):
    return CAPITALS.get(c["iso"], "پایتخت " + c["fa"])


# ───── خیزش مردمی (رضایت مردمی) ─────
PROTEST_DAYS = 5
SAT_ON = 50.0


def sat_target(c):
    T = c["stab"] * 0.8 - 8 + [12, 0, -10, -25][min(3, max(0, c.get("tax", 1)))] - 6 * len(enemies(c["iso"]))
    b = c["bank"]
    if b["loan"] > 0 and (now() - b["loan_t"]) / 3600.0 > LOAN_GRACE_H:
        T -= 10
    return max(-100.0, min(100.0, T))


def free_silent(c):
    iso, owner = c["iso"], c["owner"]
    un_remove(iso, "سقوط حکومت")
    wonder_release(iso)
    if owner:
        u = DB["users"].get(owner)
        if u and u.get("country") == iso:
            u["country"] = None
    c["owner"], c["leader"] = None, ""
    DB["wars"] = [w for w in DB["wars"] if iso not in (w[0], w[1])]
    DB["allies"] = [a for a in DB["allies"] if iso not in a]
    if owner:
        clear(owner)
    return owner


def protest_start(c):
    t = now()
    c["protest"] = {"start": t}
    c["sat_t_warn"] = t
    announce("🚨┃ فوری | آغاز خیزش مردمی\n\n⚠️ موج گسترده نارضایتی و اعتراضات مردمی در پایتخت کشور %s آغاز شد!\n\n"
             "🏛️ محل آغاز اعتراضات: %s\n\n📉 رضایت مردمی: %d%%\n\n🔥 وضعیت کشور: بحران داخلی\n\n"
             "📢 مردم در اعتراض به شرایط موجود به خیابان‌ها آمده‌اند و نارضایتی‌ها در حال گسترش به سایر مناطق کشور است.\n\n"
             "⏳ از لحظه آغاز اعتراضات، شمارش معکوس سقوط حکومت آغاز شده است.\n\n"
             "⚠️ هرچه دامنه اعتراضات گسترده‌تر شود، احتمال سقوط حکومت افزایش خواهد یافت.\n\n"
             "🔴 هشدار: در صورت تداوم اعتراضات برای بیش از %d روز، حکومت به‌طور قطعی سقوط خواهد کرد.\n\n"
             "━━━━━━━━━━━━━━━━━━\n🌍 WORLD WAR | اخبار و تحولات جهانی\n#خیزش_مردمی" % (
                 cname(c), capital_of(c), int(c["sat"]), PROTEST_DAYS), cat="uprising", iso=c["iso"], pin=True, tag="protest:" + c["iso"])
    notify_country(c["iso"], "🚨 مردم به خیابون ریختن! رضایت مردمی زیر صفره (%d٪).\nتا %d روز باید رضایت رو بالای %d٪ ببری (تبلیغات ملی، جشنواره، کاهش مالیات، ثبات، پایان جنگ) وگرنه حکومت سقوط می‌کنه!"
                   % (int(c["sat"]), PROTEST_DAYS, int(SAT_ON)))


def protest_end(c):
    c["protest"] = None
    mid = POST_MID.pop("protest:" + c["iso"], None)
    if mid and DB["settings"].get("channel"):
        try:
            api("unpinChatMessage", {"chat_id": DB["settings"]["channel"], "message_id": mid})
        except Exception:  # noqa: BLE001
            pass
    announce("🕊 اعتراضات در %s فروکش کرد؛ رضایت مردمی به %d٪ رسید و آرامش بازگشت.\n#خیزش_مردمی" % (cname(c), int(c["sat"])), cat="uprising", iso=c["iso"])
    notify_country(c["iso"], "🕊 اعتراضات فروکش کرد. حکومتت نجات پیدا کرد!")


def gov_fall(c):
    owner = free_silent(c)
    c["protest"] = None
    mid = POST_MID.pop("protest:" + c["iso"], None)
    if mid and DB["settings"].get("channel"):
        try:
            api("unpinChatMessage", {"chat_id": DB["settings"]["channel"], "message_id": mid})
        except Exception:  # noqa: BLE001
            pass
    c["stab"], c["sat"] = 45.0, 50.0
    announce("🔴┃ خبر فوری | سقوط حکومت\n\n⚠️ پس از %d روز اعتراضات مداوم و گسترش ناآرامی‌ها در سراسر کشور، حکومت سرانجام سقوط کرد!\n\n"
             "🏛️ کشور: %s\n\n👥 وضعیت مردمی: اعتراضات سراسری\n\n📉 ثبات سیاسی: فروپاشیده\n\n⚫ وضعیت حکومت: سقوط کرده\n\n"
             "📢 صدای اعتراض مردم پس از روزها ناآرامی به پایان دوران حکومت فعلی منجر شد. ساختار سیاسی کشور فروپاشیده و آینده آن در هاله‌ای از ابهام قرار گرفته است.\n\n"
             "⚔️ اکنون کشور وارد دوران جدیدی از تحولات سیاسی شده و سرنوشت قدرت در انتظار تصمیمات بعدی است.\n\n"
             "«هیچ حکومتی نمی‌تواند برای همیشه در برابر اراده مردمی که دیگر رضایت ندارند، ایستادگی کند.»\n\n"
             "━━━━━━━━━━━━━━━━━━\n🌍 WORLD WAR | اخبار و تحولات جهانی\n#سقوط_حکومت" % (PROTEST_DAYS, cname(c)), cat="fall", iso=c["iso"])
    if owner:
        tell(owner, "💀 حکومتت بعد از %d روز اعتراضات سقوط کرد! می‌تونی دوباره «🌍 درخواست کشور» بدی." % PROTEST_DAYS, main_rows(owner))


def uprising_tick(t):
    s = DB["settings"]
    if s["paused"]:
        return
    for c in DB["countries"].values():
        if not (c["owner"] and c["alive"]):
            continue
        c.setdefault("sat", 60.0)
        dt = min(t - c.get("sat_t", t), 6 * 3600) / 3600.0 * s["speed"]
        c["sat_t"] = t
        if dt > 0:
            c["sat"] += (sat_target(c) - c["sat"]) * min(1.0, 0.12 * dt)
            c["sat"] = max(-100.0, min(100.0, c["sat"]))
        pr = c.get("protest")
        if not pr:
            if c["sat"] < 0 and c["prot"] < t:
                protest_start(c)
        elif c["sat"] > SAT_ON:
            protest_end(c)
        elif t - pr["start"] >= PROTEST_DAYS * 86400:
            gov_fall(c)


EXT_TICKS.append(uprising_tick)


def sat_bump(c, n):
    c["sat"] = max(-100.0, min(100.0, c.get("sat", 60.0) + n))


# ───── تنگه‌ها و کانال‌ها + محاصره‌ی دریایی ─────
STRAITS = {
    "hormuz": {"fa": "تنگه هرمز", "orig": ["IR"], "def": 850, "mult": {"oil": 1.35, "elec": 1.15}},
    "bering": {"fa": "تنگه برینگ", "orig": ["RU", "US"], "def": 900, "mult": {"oil": 1.15, "iron": 1.2, "alu": 1.2}},
    "suez": {"fa": "کانال سوئز", "orig": ["EG"], "def": 700, "mult": {"oil": 1.15, "iron": 1.1, "alu": 1.1}},
}
ST_TEXT = {
    "hormuz": ("🛢 قیمت نفت: {d}\n⚡ قیمت برق: {d2}\n💰 هزینه تجارت و حمل‌ونقل: {d2}\n📉 تجارت دریایی کشورهای وابسته: {t}"),
    "bering": ("⛽ قیمت نفت: {d2}\n⛓️ قیمت آهن: {d2}\n🔩 قیمت آلومینیوم: {d2}\n💰 هزینه حمل‌ونقل دریایی: {d2}\n📉 تجارت کشورهای وابسته به مسیر: {t}"),
    "suez": ("📈 💰 هزینه حمل‌ونقل دریایی: {d}\n📈 ⛓️ قیمت آهن: {d2}\n📈 🔩 قیمت آلومینیوم: {d2}\n📈 🛢️ قیمت نفت: {d2}\n📉 🚢 حجم تجارت دریایی: {t}"),
}
B_STRAIT, B_BLOCK = "🌊 تنگه‌ها و کانال‌ها", "🚢 محاصره دریایی"
ST_CLOSE, ST_OPEN, ST_DEF, ST_ATK, ST_RETAKE = "🔒 بستن مسیر", "🔓 بازگشایی مسیر", "🛡 تقویت دفاعی تنگه", "⚔️ حمله به تنگه", "🏴 بازپس‌گیری تنگه"
ST_BREAK = "⚔️ عملیات شکستن محاصره"
BK_START, BK_HIT, BK_ADD = "🚢 آغاز محاصره", "⚔️ حمله به ناوگان", "🛡 تقویت محاصره"
SEL_ADD, SEL_ALL, SEL_GO, SEL_CANCEL = "➕ افزودن ناو", "⚡ همه‌ی ناوها", "✅ تایید و ارسال", "❌ انصراف"
ST_ROWS = None


def stx(k):
    e = EXT()
    ss = e.setdefault("straits", {})
    if k not in ss:
        ss[k] = {"ctrl": list(STRAITS[k]["orig"]), "status": "open", "def": STRAITS[k]["def"], "t": 0}
    return ss[k]


def st_closed(k):
    return stx(k)["status"] in ("closed", "blockaded")


def strait_mult(res):
    v = 1.0
    for k, s in STRAITS.items():
        if st_closed(k):
            v *= s["mult"].get(res, 1.0)
    return v


def st_flags(k):
    return "".join(flag(i) for i in stx(k)["ctrl"])


def st_ctrl_names(k):
    return "، ".join(cname(C(i)) for i in stx(k)["ctrl"] if C(i)) or "—"


def strait_status_lines():
    out = []
    for k, s in STRAITS.items():
        out.append("%s %s　　%s" % ("🌊" if k != "suez" else "🚢", s["fa"], "🔴 بسته" if st_closed(k) else "🟢 باز"))
    return out


def blockades():
    e = EXT()
    t = now()
    bl = e.setdefault("blockades", [])
    bl[:] = [b for b in bl if t - b["t"] < 48 * 3600 and C(b["on"]) and C(b["by"])]
    return bl


def trade_blocked(c):
    return any(b["on"] == c["iso"] for b in blockades())


def navy_of(c):
    return {k: q for k, q in c["units"].items() if k in U and U[k]["cat"] == "navy" and q > 0}


def navy_atk(sent, c):
    return sum(U[k]["atk"] * q for k, q in sent.items()) * atk_mult(c)


def navy_dfn(c):
    return sum(U[k]["dfn"] * q for k, q in navy_of(c).items()) + 0.3 * aa_power(c)


def equip_line(units, n=5):
    by = sorted(((k, q) for k, q in units.items() if k in U and q > 0), key=lambda kv: -U[kv[0]]["pw"] * kv[1])[:n]
    return "، ".join("%s×%s" % (U[k]["name"].split(" ")[0] if False else U[k]["name"], m(q)) for k, q in by) or "—"


@route(B_STRAIT)
def r_strait(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["🌊 تنگه‌ها و کانال‌های استراتژیک", "کنترل هر مسیر، قیمت منابع جهانی رو تکون می‌ده.", ""]
    for k, s in STRAITS.items():
        L.append("%s %s\n   🛡 کنترل‌کننده: %s | وضعیت: %s" % (st_flags(k), s["fa"], st_ctrl_names(k), "🔴 بسته" if st_closed(k) else "🟢 باز"))
    ask(uid, "\n".join(L), lambda t: strait_pick(uid, t), [[s["fa"]] for s in STRAITS.values()] + [[B_BLOCK]])


def strait_key(t):
    return next((k for k, s in STRAITS.items() if squash(s["fa"]) == squash(t)), None)


def strait_pick(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    if squash(t) == squash(B_BLOCK):
        return r_block(uid)
    k = strait_key(t)
    if not k:
        return r_strait(uid)
    s, x = STRAITS[k], stx(k)
    mine_ctrl = c["iso"] in x["ctrl"]
    rows = []
    if mine_ctrl:
        rows.append([ST_OPEN if st_closed(k) else ST_CLOSE])
        rows.append([ST_DEF])
        if x["status"] == "blockaded":
            rows.append([ST_BREAK])
    else:
        rows.append([ST_ATK])
        if c["iso"] in s["orig"]:
            rows.append([ST_RETAKE])
    ask(uid, "%s %s\n🛡 کنترل‌کننده: %s\n🚦 وضعیت: %s\n\nچه کاری انجام می‌دی؟" % (
        st_flags(k), s["fa"], st_ctrl_names(k), "بسته" if st_closed(k) else "باز"), lambda a: strait_act(uid, k, a), rows)


def strait_act(uid, k, a):
    c = mine(uid)
    if not c:
        return no_country(uid)
    x = stx(k)
    s = squash(a)
    if s in (squash(ST_CLOSE), squash(ST_OPEN)):
        if c["iso"] not in x["ctrl"]:
            return back_to(uid, "❌ این مسیر دست تو نیست.", main_rows(uid))
        if x["t"] > now() - 1800:
            return back_to(uid, "⏱ برای تغییر دوباره‌ی وضعیت باید %s صبر کنی." % dur(x["t"] + 1800 - now()), main_rows(uid))
        return strait_toggle(uid, k, s == squash(ST_CLOSE))
    if s == squash(ST_DEF):
        cost = int(x["def"] * 0.6)
        ask(uid, "🛡 تقویت دفاعی %s\nقدرت دفاعی: %s ← %s\n💰 هزینه: %s M$ (موجودی %s)\n\nانجام بشه؟" % (
            STRAITS[k]["fa"], m(x["def"]), m(x["def"] + 200), m(cost), m(c["money"])), lambda t: strait_def_do(uid, k, cost, t), [["✅ بله", "❌ خیر"]])
        return
    if s in (squash(ST_ATK), squash(ST_RETAKE)):
        if not war_on("conv"):
            return back_to(uid, "⛔ جنگ معمولی توسط ادمین غیرفعاله.", main_rows(uid))
        ask(uid, "🚢 چند درصد از ناوگان و موشک‌هات رو بفرستی؟", lambda t: strait_attack(uid, k, t, s == squash(ST_RETAKE)), [["25%", "50%", "100%"]])
        return
    if s == squash(ST_BREAK):
        return block_hit_pick(uid)
    r_strait(uid)


def strait_toggle(uid, k, close):
    c = mine(uid)
    x = stx(k)
    x["status"] = "closed" if close else "open"
    x["t"] = now()
    nm = STRAITS[k]["fa"]
    who = " و ".join(cname(C(i)) for i in x["ctrl"] if C(i))
    if close:
        head = "🚨 هشدار استراتژیک | هشدار استراتژیک 🚨" if k != "suez" else "🚨 هشدار اقتصادی | خبر فوری 🚨"
        txt = ("%s\n\n🌊 %s بسته شد!\n\n🏛 %s رسماً %s را مسدود کرد.\n\n🚢 عبور و مرور کشتی‌های تجاری و نفتکش‌ها در این مسیر متوقف شده است.\n\n"
               "📈 تأثیرات اقتصادی:\n%s\n\n⚠️ بازار جهانی وارد وضعیت بحرانی شده و ادامه بسته‌بودن مسیر می‌تواند فشار اقتصادی بیشتری بر کشورهای وابسته وارد کند.\n\n"
               "🌍 وضعیت %s: 🔴 بسته\n#تنگه" % (head, nm, who, nm, ST_TEXT[k].format(d="افزایش شدید", d2="افزایش", t="کاهش"), nm))
    else:
        txt = ("🚨 خبر فوری | بازگشایی مسیر استراتژیک 🚨\n\n🌊 %s باز شد!\n\n🏛 %s رسماً محدودیت عبور و مرور از %s را لغو کرد.\n\n"
               "🚢 کشتیرانی و عبور نفتکش‌ها دوباره برقرار شد.\n\n📉 تأثیرات اقتصادی:\n%s\n\n"
               "🌍 با بازگشایی مسیر، فشار ایجادشده بر بازارهای جهانی کاهش یافته و تجارت دریایی به شرایط عادی بازمی‌گردد.\n\n🟢 وضعیت %s: باز\n#تنگه"
               % (nm, who, nm, ST_TEXT[k].format(d="کاهش", d2="کاهش", t="بهبود").replace("📉", "📈").replace("افزایش", "کاهش"), nm))
    announce(txt, cat="strait", iso=tuple(x["ctrl"]))
    back_to(uid, "✅ %s %s شد." % (nm, "بسته" if close else "باز"), main_rows(uid))


def strait_def_do(uid, k, cost, t):
    c, x = mine(uid), stx(k)
    if "بله" not in t or not c or c["iso"] not in x["ctrl"]:
        return back_to(uid, "لغو شد.", main_rows(uid))
    if c["money"] < cost:
        return back_to(uid, "❌ پول کافی نیست.", main_rows(uid))
    c["money"] -= cost
    old = x["def"]
    x["def"] = min(6000, old + 200)
    announce("🛡️ فرمان دفاعی صادر شد!\n\n🌊 %s در وضعیت دفاعی قرار گرفت.\n\n%s کشور %s نیروهای دفاعی خود را در اطراف مسیر مستقر و مواضع راهبردی آن را تقویت کرد.\n\n"
             "🛡️ قدرت دفاعی: %s ← %s\n🚢 حفاظت از مسیرهای دریایی: فعال\n⚠️ احتمال موفقیت عملیات دشمن: کاهش یافت\n\n"
             "🔒 مسیر از امنیت بیشتری در برابر حملات و تلاش برای تصرف برخوردار است.\n\n🟢 وضعیت: دفاع تقویت‌شده\n#تنگه" % (
                 STRAITS[k]["fa"], st_flags(k), cname(c), m(old), m(x["def"])), cat="strait", iso=c["iso"])
    back_to(uid, "✅ دفاع تنگه تقویت شد: %s" % m(x["def"]), main_rows(uid))


def pct_sent(c, t, cats):
    raw = en_digits(t).strip()
    v = num(raw.replace("%", "").replace("٪", ""))
    if not v or v <= 0:
        return {}
    f = min(v, 100.0) / 100.0
    return {k: max(1, int(q * f)) for k, q in c["units"].items() if k in U and U[k]["cat"] in cats and q > 0}


def strait_attack(uid, k, t, retake):
    c = mine(uid)
    if not c:
        return no_country(uid)
    x = stx(k)
    sent = pct_sent(c, t, {"navy", "missile"})
    if not sent:
        return back_to(uid, "❌ ناوگانی برای اعزام نداری یا عدد نامعتبر بود.", main_rows(uid))
    if c["iso"] in x["ctrl"] or any(ceasefire_between(c["iso"], i) or is_ally(c["iso"], i) for i in x["ctrl"]):
        return back_to(uid, "❌ حمله به این مسیر ممکن نیست (متحد/آتش‌بس/کنترل خودته).", main_rows(uid))
    if c.get("cd_st", 0) > now():
        return back_to(uid, "⏱ نیروهات هنوز آماده نیستن (%s)." % dur(c["cd_st"] - now()), main_rows(uid))
    ctrl = [C(i) for i in x["ctrl"] if C(i) and C(i)["alive"]]
    A = navy_atk(sent, c) * random.uniform(0.9, 1.1)
    D = x["def"] + sum(navy_dfn(d) for d in ctrl)
    R = A / max(D, 1.0)
    win = R >= 1.1
    c["cd_st"] = now() + 600
    att_equip, def_equip = equip_line(sent), equip_line({k2: q for d in ctrl for k2, q in navy_of(d).items()})
    for kk, q in sent.items():
        lost = lose_count(q, (0.12 if win else min(0.5, 0.25 + 0.1 / max(R, 0.1))) * (1.0 if U[kk]["cat"] != "missile" else 1.0))
        c["units"][kk] -= lost
    if U.get("corv"):
        pass
    for d in ctrl:
        for kk, q in navy_of(d).items():
            d["units"][kk] -= lose_count(q, 0.15 if win else 0.05)
    nm = STRAITS[k]["fa"]
    head = ("⚔️ عملیات بازپس‌گیری %s ⚔️\n\n🚨 هشدار نظامی!\n\n🌊 %s تحت کنترل نیروی خارجی قرار گرفته است.\n\n%s کشور %s عملیات بازپس‌گیری را آغاز کرد.\n"
            % (nm, nm, flag(c["iso"]), cname(c))) if retake else ("⚔️ حمله به %s!\n\n🌊 %s تحت حمله %s قرار گرفت.\n" % (nm, nm, cname(c)))
    ctrl_names = st_ctrl_names(k)
    body = ("\n⚔️ تجهیزات مهاجم: %s\n🛡 تجهیزات مدافع: %s\n\n🛡️ کنترل‌کننده: %s\n🔴 وضعیت: درگیری\n\n📊 نتیجه عملیات:\n" % (att_equip, def_equip, ctrl_names))
    if win:
        x["ctrl"] = [c["iso"]]
        x["def"] = max(300, int(x["def"] * 0.7))
        x["status"] = "open"
        x["t"] = now()
        res = ("🏆 تنگه با موفقیت %s!\n\n%s کنترل مسیر به %s %s.\n🟢 وضعیت کشتیرانی: فعال\n🌊 وضعیت: 🟢 تحت کنترل %s\n#تنگه" % (
            "بازپس‌گرفته شد" if retake else "تصرف شد", "🇮🇷" if False else "", flag(c["iso"]), "بازگشت" if retake else "منتقل شد", cname(c)))
        for d in ctrl:
            notify_country(d["iso"], "🚨 کنترل %s از دستت رفت!" % nm)
    else:
        res = "🛡 حمله دفع شد! مدافعان در برابر ناوگان مهاجم ایستادگی کردند.\n🌊 وضعیت: 🔴 همچنان تحت کنترل %s\n#تنگه" % ctrl_names
    announce(head + body + res, cat="strait", iso=(c["iso"],) + tuple(x["ctrl"]))
    back_to(uid, "⚔️ عملیات انجام شد: %s" % ("پیروزی ✅" if win else "شکست ❌"), main_rows(uid))


# محاصره
BLK = {}


def blk_rows(uid):
    return [[BK_START], [BK_HIT, BK_ADD], [B_STRAIT]]


@route(B_BLOCK)
def r_block(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    bl = blockades()
    L = ["🚢 محاصره دریایی", "با محاصره، تجارت دریایی کشور هدف (بازار منابع) متوقف می‌شه.", ""]
    for b in bl:
        L.append("• %s ← %s | قدرت ناوگان: %s" % (cname(C(b["by"])), cname(C(b["on"])), m(b["power"])))
    if not bl:
        L.append("فعلاً محاصره‌ای نیست.")
    ask(uid, "\n".join(L), lambda t: block_menu(uid, t), blk_rows(uid))


def block_menu(uid, t):
    s = squash(t)
    if s == squash(BK_START):
        return block_target(uid)
    if s == squash(BK_HIT):
        return block_hit_pick(uid)
    if s == squash(BK_ADD):
        return block_add_pick(uid)
    r_block(uid)


def block_target(uid):
    c = mine(uid)
    if not war_on("conv"):
        return back_to(uid, "⛔ جنگ معمولی توسط ادمین غیرفعاله.", main_rows(uid))
    if not navy_of(c):
        return back_to(uid, "🚢 ناوگان نداری! از «فروشگاه ← دریایی» ناو بخر.", main_rows(uid))
    ex = {"🇮🇷 ایران": "IR", "🇷🇺 روسیه": "RU", "🇺🇸 آمریکا": "US", "🌍 سایر کشورها": "*"}
    ex = {k: v for k, v in ex.items() if v == "*" or (C(v) and C(v)["owner"] and v != c["iso"])}

    def go(iso):
        if iso == "*":
            return pick_country(uid, "🎯 کدوم کشور؟", lambda i: block_fleet(uid, i), lambda x: x["alive"] and x["owner"] and x["iso"] != c["iso"] and not is_ally(c["iso"], x["iso"]))
        block_fleet(uid, iso)

    pick_country(uid, "🚢 محاصره دریایی\n🎯 هدف: انتخاب کشور برای محاصره", go, lambda x: False, extra=ex)


def block_fleet(uid, iso):
    c, d = mine(uid), C(iso)
    if not c or not d or not d["owner"] or ceasefire_between(c["iso"], iso):
        return back_to(uid, "❌ محاصره ممکن نیست.", main_rows(uid))
    BLK[uid] = {"iso": iso, "sent": {}}
    block_hub(uid)


def block_hub(uid, note=""):
    c, st = mine(uid), BLK.get(uid)
    if not c or not st:
        return menu(uid)
    d = C(st["iso"])
    L = [note, ""] if note else []
    L += ["🚨 عملیات محاصره دریایی", "🎯 هدف: %s" % cname(d), "━━━━━━━━━━━━━━━━━",
          "🚢 ناوگان محاصره‌کننده: %s" % (equip_line(st["sent"], 8) if st["sent"] else "هنوز ناوی انتخاب نکردی"),
          "📦 تجارت دریایی: متوقف", ""]
    nd = navy_of(d)
    L.append("🛡 ناوگان دفاعی هدف: %s" % (equip_line(nd) if nd else "ندارد — محاصره‌ی تنگ‌هاش خیلی راحت‌تره!"))
    ask(uid, "\n".join(L), lambda t: block_hub_do(uid, t), [[SEL_ADD, SEL_ALL], [BK_START], [SEL_CANCEL]])


def block_hub_do(uid, t):
    c, st = mine(uid), BLK.get(uid)
    if not c or not st:
        return menu(uid)
    s = squash(t)
    if s == squash(SEL_ADD):
        units = sorted((U[k] for k, q in navy_of(c).items() if q - st["sent"].get(k, 0) > 0), key=lambda u: -u["atk"])
        if not units:
            return block_hub(uid, "😕 ناوی نمونده.")
        return pick_unit(uid, "🚢 کدوم ناو؟", units, lambda key: block_qty(uid, key), per=8,
                         lines=lambda u: "• %s | داری: %s" % (u["name"], m(c["units"][u["key"]] - st["sent"].get(u["key"], 0))))
    if s == squash(SEL_ALL):
        st["sent"] = dict(navy_of(c))
        return block_hub(uid, "⚡ همه‌ی ناوها انتخاب شدن.")
    if s == squash(BK_START):
        return block_go(uid)
    if s == squash(SEL_CANCEL):
        BLK.pop(uid, None)
        return back_to(uid, "❌ لغو شد.", main_rows(uid))
    block_hub(uid)


def block_qty(uid, key):
    c, st = mine(uid), BLK.get(uid)
    if not c or not st:
        return menu(uid)
    free = c["units"][key] - st["sent"].get(key, 0)
    ask(uid, "چند تا «%s»؟ (موجود %s)" % (U[key]["name"], m(free)), lambda t: block_qty_do(uid, key, t), [["25%", "50%", "100%"], ["1", "5", "10"]])


def block_qty_do(uid, key, t):
    c, st = mine(uid), BLK.get(uid)
    if not c or not st:
        return menu(uid)
    free = c["units"][key] - st["sent"].get(key, 0)
    raw = en_digits(t).strip()
    v = num(raw.replace("%", "").replace("٪", ""))
    if not v or v <= 0:
        return block_qty(uid, key)
    q = max(1, int(free * min(v, 100) / 100)) if raw.endswith(("%", "٪")) else int(v)
    st["sent"][key] = st["sent"].get(key, 0) + min(q, free)
    block_hub(uid, "✅ %s × %s اضافه شد." % (U[key]["name"], m(min(q, free))))


def block_go(uid):
    c, st = mine(uid), BLK.get(uid)
    if not c or not st or not st["sent"]:
        return block_hub(uid, "❌ اول ناو انتخاب کن.")
    d = C(st["iso"])
    if not d or not d["owner"]:
        return back_to(uid, "❌ هدف معتبر نیست.", main_rows(uid))
    if frozen(uid):
        return
    sent = {k: min(q, c["units"].get(k, 0)) for k, q in st["sent"].items()}
    A = navy_atk(sent, c) * random.uniform(0.9, 1.1)
    nd = navy_of(d)
    D = navy_dfn(d) * 0.8
    easy = not nd
    win = easy or A >= D
    BLK.pop(uid, None)
    for k, q in sent.items():
        c["units"][k] -= lose_count(q, 0.03 if win else 0.3)
    if win:
        blockades().append({"by": c["iso"], "on": d["iso"], "power": A, "fleet": sent, "t": now()})
        for k, s in STRAITS.items():
            if d["iso"] in stx(k)["ctrl"] and stx(k)["status"] == "open":
                stx(k)["status"] = "blockaded"
                stx(k)["t"] = now()
        announce("🚨 عملیات محاصره دریایی\n\n🎯 هدف: %s\n🚢 ناوگان محاصره‌کننده: %s %s\n📦 تجارت دریایی: متوقف\n%s\n\n"
                 "🛡 قدرت ناوگان محاصره: %s\n#تنگه" % (cname(d), cname(c), equip_line(sent, 5),
                                                       "✅ کشور هدف ناو دفاعی نداشت؛ محاصره بدون مقاومت برقرار شد!" if easy else "✅ محاصره با موفقیت برقرار شد.", m(A)),
                 cat="strait", iso=(c["iso"], d["iso"]))
        notify_country(d["iso"], "🚨 %s کشورت رو در محاصره‌ی دریایی گرفت! تجارت دریایی متوقف شد. با «🌊 تنگه‌ها ← 🚢 محاصره ← ⚔️ حمله به ناوگان» محاصره رو بشکن." % cname(c))
        back_to(uid, "✅ محاصره برقرار شد.", main_rows(uid))
    else:
        back_to(uid, "❌ ناوگان هدف قوی‌تر بود؛ محاصره شکست خورد و بخشی از ناوهات از دست رفت.", main_rows(uid))


def block_hit_pick(uid):
    c = mine(uid)
    bl = blockades()
    if not c or not bl:
        return back_to(uid, "فعلاً محاصره‌ای وجود نداره.", main_rows(uid))
    lab = {"%s ← %s" % (cname(C(b["by"])), cname(C(b["on"]))): b for b in bl}
    ask(uid, "⚔️ به ناوگان کدوم محاصره حمله کنی؟", lambda t: block_hit_pct(uid, lab.get(t)), [[l] for l in lab])


def block_hit_pct(uid, b):
    if not b:
        return r_block(uid)
    ask(uid, "🚢 چند درصد از ناوگانت؟", lambda t: block_hit_do(uid, b, t), [["25%", "50%", "100%"]])


def block_hit_do(uid, b, t):
    c = mine(uid)
    if not c or b not in blockades():
        return back_to(uid, "این محاصره دیگه وجود نداره.", main_rows(uid))
    if c["iso"] == b["by"] or not war_on("conv"):
        return back_to(uid, "❌ ممکن نیست.", main_rows(uid))
    sent = pct_sent(c, t, {"navy"})
    if not sent:
        return back_to(uid, "❌ ناوگانی نداری.", main_rows(uid))
    A = navy_atk(sent, c) * random.uniform(0.9, 1.1)
    win = A >= b["power"]
    for k, q in sent.items():
        c["units"][k] -= lose_count(q, 0.1 if win else 0.3)
    br, victim = C(b["by"]), C(b["on"])
    own = c["iso"] == b["on"]
    if win:
        blockades().remove(b)
        for k in STRAITS:
            if stx(k)["status"] == "blockaded" and not any(x["on"] == i for x in blockades() for i in stx(k)["ctrl"]):
                stx(k)["status"] = "open"
        announce("⚔️ عملیات شکستن محاصره ⚔️\n\n🌊 %s تحت محاصره دریایی %s قرار داشت.\n\n%s %s برای باز کردن مسیر وارد عملیات شد.\n🛡 ناوگان محاصره‌کننده در برابر عملیات مقاومت کرد.\n\n"
                 "📊 نتیجه عملیات:\n🟢 محاصره شکسته شد!\n🚢 عبور و مرور دریایی دوباره برقرار شد.\n📉 فشار واردشده بر تجارت و بازار کاهش یافت.\n\n🌍 وضعیت: 🟢 باز\n#تنگه"
                 % (cname(victim), cname(br), flag(c["iso"]), cname(c)), cat="strait", iso=(c["iso"], b["by"]))
        back_to(uid, "🟢 محاصره شکسته شد!", main_rows(uid))
    else:
        b["power"] *= 0.8
        back_to(uid, "❌ ناوگان محاصره قوی‌تر بود؛ ولی ۲۰٪ ضعیف شد.", main_rows(uid))


def block_add_pick(uid):
    c = mine(uid)
    mybl = [b for b in blockades() if b["by"] == (c or {}).get("iso")]
    if not c or not mybl:
        return back_to(uid, "محاصره‌ی فعالی نداری.", main_rows(uid))
    lab = {"%s" % cname(C(b["on"])): b for b in mybl}
    ask(uid, "🛡 تقویت محاصره‌ی کدوم کشور؟", lambda t: block_add_do(uid, lab.get(t)), [[l] for l in lab])


def block_add_do(uid, b):
    c = mine(uid)
    if not c or not b:
        return r_block(uid)
    sent = {k: q for k, q in navy_of(c).items() if k not in b["fleet"]}
    if not sent:
        return back_to(uid, "ناوی برای تقویت نداری.", main_rows(uid))
    p = navy_atk(sent, c) * 0.5
    b["power"] += p
    for k, q in sent.items():
        b["fleet"][k] = q
    back_to(uid, "🛡 محاصره تقویت شد (+%s)." % m(p), main_rows(uid))


# ───── سایبری کریپتو + فایروال جهانی ─────
FW_COST = 20_000_000_000_000     # دلار برای هر سطح (ادمین می‌تونه عوض کنه)
FW_MAX = 10
CY_DISRUPT, CY_HEIST, CY_FW = "📉 اختلال در بازار کریپتو", "☠️ سرقت جهانی کریپتو", "🛡 فایروال جهانی کریپتو"
CYBER_ROWS.insert(1, [CY_DISRUPT, CY_HEIST])
CYBER_ROWS.insert(2, [CY_FW])


def fw_cost():
    return float(DB["settings"].get("fw_cost", FW_COST))


def fw():
    return EXT()["fw"]


def hackers(c):
    return int(c["units"].get("redhat", 0))


def cy_gate(uid, key):
    c = mine(uid)
    if not c:
        no_country(uid)
        return None
    if frozen(uid) or war_blocked(uid, "cyber", CYBER_ROWS):
        return None
    if c.get(key, 0) > now():
        back_to(uid, "⏱ %s دیگه آماده‌ای." % dur(c[key] - now()), CYBER_ROWS)
        return None
    if hackers(c) < 1:
        back_to(uid, "❌ هکر کلاه‌قرمز نداری؛ از «فروشگاه ← سایبری» یا پک سایبری بگیر.", CYBER_ROWS)
        return None
    return c


def cy_count(uid, prompt, cb):
    c = mine(uid)
    h = hackers(c)
    opts = [str(n) for n in (10, 100, 500, 1000, 5000) if n < h]
    ask(uid, "%s\n💻 هکر کلاه‌قرمز موجود: %s" % (prompt, m(h)), lambda t: cb(t), [opts[:3] + ["همه"]] if opts else [["همه"]])


def parse_h(c, t):
    h = hackers(c)
    if squash(t) == "همه":
        return h
    v = num(t)
    return int(min(v, h)) if v and v >= 1 else 0


@route(CY_DISRUPT)
def r_cy_disrupt(uid):
    c = cy_gate(uid, "cd_cy2")
    if not c:
        return
    cy_count(uid, "💻 عملیات سایبری | اختلال در بازار کریپتو\n\n⚠️ شما در حال آماده‌سازی یک حمله سایبری گسترده هستید.\n🎯 نوع عملیات: ایجاد اختلال در بازار کریپتو\n\n"
                  "چند هکر خرابکار بفرستی؟", lambda t: cy_disrupt_confirm(uid, parse_h(c, t)))


def cy_disrupt_confirm(uid, n):
    if n < 1:
        return back_to(uid, "❌ عدد نامعتبر.", CYBER_ROWS)
    ask(uid, "💻 تعداد هکر های خرابکار: %s\n━━━━━━━━━━━━━━━━━━\n⚠️ آیا از اجرای این عملیات اطمینان دارید؟" % m(n), lambda t: cy_disrupt_do(uid, n, t),
        [["✅ بله، اجرا کن", "❌ انصراف"]])


def cy_disrupt_do(uid, n, t):
    c = mine(uid)
    if not c or "بله" not in t:
        return back_to(uid, "لغو شد.", CYBER_ROWS)
    n = min(n, hackers(c))
    if n < 1 or c.get("cd_cy2", 0) > now():
        return back_to(uid, "❌ ممکن نیست.", CYBER_ROWS)
    lvl = fw()["lvl"]
    p = n / (n + 600.0 + 700.0 * lvl)
    c["cd_cy2"] = now() + 3600
    quest_add(c, "cyber")
    if random.random() < p:
        c["units"]["redhat"] -= lose_count(n, 0.05)
        for sym in COINS:
            cc = DB["market"]["coins"][sym]
            cc["p"] = max(COINS[sym]["p"] * 0.05, cc["p"] * 0.8)
            cc["hist"].append(round(cc["p"], 8))
        announce("🚨 CYBER ATTACK | MARKET DISRUPTION\n━━━━━━━━━━━━━━━━━━\n💻 یک حمله سایبری گسترده علیه زیرساخت بازار جهانی ارزهای دیجیتال انجام شد.\n\n"
                 "📉 در پی این حمله سایبری %s، تمام رمزارزها با ریزش شدید مواجه شدند.\n\n📊 میزان ریزش بازار:\n🔻 DOGE (دوج‌کوین): 20٪\n🔻 BTC (بیت‌کوین): 20٪\n"
                 "🔻 ETH (اتریوم): 20٪\n🔻 SOL (سولانا): 20٪\n\n━━━━━━━━━━━━━━━━━━\n⚠️ وضعیت بازار: سقوط شدید\n🌐 دامنه اختلال: تمامی ارزهای فعال بازی\n"
                 "💥 میزان افت: 20 درصد برای هر ارز\n🔴 بازار کریپتو تحت تأثیر حمله سایبری قرار گرفت.\n#سایبری" % cname(c), cat="cyber", iso=c["iso"])
        back_to(uid, "✅ بازار کریپتو با موفقیت مختل شد!", CYBER_ROWS)
    else:
        lost = lose_count(n, 0.3)
        c["units"]["redhat"] -= lost
        back_to(uid, "❌ فایروال جهانی حمله رو دفع کرد و %s هکر از دست رفتن." % m(lost), CYBER_ROWS)


@route(CY_HEIST)
def r_cy_heist(uid):
    c = cy_gate(uid, "cd_cy3")
    if not c:
        return
    cy_count(uid, "☠️ GLOBAL CRYPTO HEIST\n💻 عملیات سرقت جهانی کریپتو\n━━━━━━━━━━━━━━━━━━\n\n⚠️ شما در حال آماده‌سازی یک عملیات سایبری فوق‌سنگین هستید.\n\n"
                  "🎯 هدف: کیف پول تمامی کشورهای فعال\n💰 نوع عملیات: سرقت دارایی‌های دیجیتال\n📊 دامنه: کل بازار جهانی کریپتو\n\nچند هکر اعزام کنی؟",
             lambda t: cy_heist_pct(uid, parse_h(c, t)))


def cy_heist_pct(uid, n):
    if n < 1:
        return back_to(uid, "❌ عدد نامعتبر.", CYBER_ROWS)
    ask(uid, "💸 چند درصد از کیف پول‌ها برداشت بشه؟ (هرچه بیشتر، احتمال شکست بیشتر)", lambda t: cy_heist_confirm(uid, n, t), [["1", "2", "3"], ["5", "7", "10"]])


def cy_heist_confirm(uid, n, t):
    v = num(t.replace("%", ""))
    if not v or v < 0.5 or v > 10:
        return back_to(uid, "❌ درصد باید بین 0.5 و 10 باشه.", CYBER_ROWS)
    ask(uid, "☠️ GLOBAL CRYPTO HEIST\n━━━━━━━━━━━━━━━━━━\n👨‍💻 تعداد هکرهای اعزامی: %s\n💸 درصد برداشت از کیف پول‌ها: %s%%\n"
             "⚠️ هشدار: احتمال شناسایی هویت هکرها و ازدست‌رفتن نیروهای سایبری وجود دارد.\nآیا عملیات را تأیید می‌کنید؟" % (m(n), ("%g" % v)),
        lambda x: cy_heist_do(uid, n, v, x), [["✅ تایید عملیات", "❌ انصراف"]])


def cy_heist_do(uid, n, pct, t):
    c = mine(uid)
    if not c or "تایید" not in t or "انصراف" in t:
        return back_to(uid, "لغو شد.", CYBER_ROWS)
    n = min(n, hackers(c))
    if n < 1 or c.get("cd_cy3", 0) > now():
        return back_to(uid, "❌ ممکن نیست.", CYBER_ROWS)
    lvl = fw()["lvl"]
    p = n / (n + 1500.0 + 1200.0 * lvl) * max(0.05, 1 - pct / 20.0)
    c["cd_cy3"] = now() + 3 * 3600
    quest_add(c, "cyber")
    if random.random() < p:
        c["units"]["redhat"] -= lose_count(n, 0.05)
        stolen, total = {}, 0.0
        for d in DB["countries"].values():
            if d is c or not d["alive"] or not d["crypto"]:
                continue
            got = False
            for sym, a in list(d["crypto"].items()):
                if sym in COINS and a > 0:
                    take = a * pct / 100.0
                    d["crypto"][sym] = a - take
                    c["crypto"][sym] = c["crypto"].get(sym, 0.0) + take
                    stolen[sym] = stolen.get(sym, 0.0) + take
                    total += take * coin_price(sym)
                    got = True
            if got and d["owner"]:
                notify_country(d["iso"], "☠️ هکرها %s٪ از کیف پول رمزارزت رو دزدیدن!" % ("%g" % pct))
        rows = "\n".join("%s %s: %s" % (COINS[s]["sym"], COINS[s]["name"], fp(v)) for s, v in stolen.items()) or "—"
        announce("☠️ GLOBAL CRYPTO HEIST\n🔴 گزارش عملیات سایبری جهانی\n━━━━━━━━━━━━━━━━━━\n\n💻 نفوذ گسترده به کیف پول کشورهای جهان با موفقیت انجام شد.\n\n"
                 "💰 بخشی از دارایی‌های دیجیتال کشورها استخراج و به کیف پول کشور ناشناس 🏴‍☠️ منتقل شد.\n\n📊 دارایی‌های سرقت‌شده:\n%s\n\n"
                 "━━━━━━━━━━━━━━━━━━\n💎 ارزش کل سرقت: %s دلار 👨‍💻\n#سایبری" % (rows, dol(total)), cat="heist")
        back_to(uid, "✅ عملیات موفق بود!\n💎 ارزش کل: %s دلار" % dol(total), CYBER_ROWS)
    else:
        lost = lose_count(n, 0.4)
        c["units"]["redhat"] -= lost
        announce("🚨 GLOBAL CRYPTO HEIST\n⚠️ گزارش شکست عملیات سایبری\n━━━━━━━━━━━━━━━━━━\n\n💻 تلاش برای نفوذ به کیف‌پول‌های جهانی با شکست مواجه شد.\n\n"
                 "🛡️ سیستم‌های امنیتی بازار حمله را شناسایی و عملیات را متوقف کردند.\n\n❌ هیچ دارایی دیجیتالی سرقت نشد.\n\n━━━━━━━━━━━━━━━━━━\n"
                 "👨‍💻 هکرهای ازدست‌رفته: %s\n🔴 هویت مهاجم شناسایی شد:\n🌍 کشور: %s\n👤 عامل عملیات: %s\n⚠️ هویت کشور مهاجم برای تمامی بازیکنان افشا شد.\n"
                 "عملیات ناموفق\n🌐 GLOBAL CRYPTO SECURITY\n#سایبری" % (m(lost), cname(c), ulabel(uid)), cat="heist", iso=c["iso"])
        back_to(uid, "❌ عملیات لو رفت! %s هکر از دست رفت و هویتت افشا شد." % m(lost), CYBER_ROWS)


@route(CY_FW)
def r_cy_fw(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    f = fw()
    need = fw_cost()
    ask(uid, "🌐 GLOBAL CRYPTO DEFENSE\n🛡️ سامانه امنیت جهانی بازار کریپتو\n━━━━━━━━━━━━━━━━━━\n\n"
             "تمامی کشورهای جهان می‌توانند با واریز بودجه به خزانه امنیت جهانی، در تقویت فایروال و حفاظت از بازار ارزهای دیجیتال مشارکت کنند.\n\n"
             "💰 هزینه هر سطح فایروال: %s دلار\n\n🛡️ سطح فعلی امنیت جهانی: %d / %d\n\n🏦 بودجه جمع‌آوری‌شده: %s دلار\n\n🎯 بودجه موردنیاز برای ارتقا: %s دلار\n\n"
             "━━━━━━━━━━━━━━━━━━\n💵 مبلغ مشارکت خود را وارد کنید (دلار؛ مثال 5m یا 2b یا 1t).\n🌍 مشارکت شما به حفاظت از دارایی‌های دیجیتال تمام کشورها کمک می‌کند.\n💰 موجودی شما: %s دلار"
        % (dols(need), f["lvl"], FW_MAX, dols(f["pool"]), dols(max(0, need - f["pool"])), dol(c["money"])), lambda t: cy_fw_do(uid, t), [["1m", "100m", "1b"], ["100b", "1t"]])


def cy_fw_do(uid, t):
    c = mine(uid)
    v = bnum(t)
    if not c or not v or v <= 0 or v > c["money"] * 1e6:
        return back_to(uid, "❌ مبلغ نامعتبر یا پول کافی نیست.", CYBER_ROWS)
    f = fw()
    if f["lvl"] >= FW_MAX:
        return back_to(uid, "🛡 فایروال به حداکثر سطح رسیده.", CYBER_ROWS)
    c["money"] -= v / 1e6
    f["pool"] += v
    announce("🌐 GLOBAL CRYPTO DEFENSE\n💰 گزارش مشارکت جهانی\n━━━━━━━━━━━━━━━━━━\n\n🏳️ کشور مشارکت‌کننده: %s\n💵 مبلغ واریزی: %s دلار\n"
             "🏦 مجموع بودجه جهانی: %s دلار\n🛡️ سطح فایروال جهانی: %d\n━━━━━━━━━━━━━━━━━━\n✅ مشارکت کشور با موفقیت ثبت شد.\n"
             "🔐 تمامی کشورهای جهان تحت پوشش سامانه امنیت جهانی کریپتو قرار دارند.\n🌍 GLOBAL CRYPTO DEFENSE" % (cname(c), dols(v), dols(f["pool"]), f["lvl"]),
             cat="firewall", iso=c["iso"])
    while f["pool"] >= fw_cost() and f["lvl"] < FW_MAX:
        f["pool"] -= fw_cost()
        old = f["lvl"]
        f["lvl"] += 1
        announce("🚨 GLOBAL FIREWALL UPGRADE\n━━━━━━━━━━━━━━━━━━\n\n🎉 با تکمیل بودجه موردنیاز، سطح امنیت جهانی بازار کریپتو ارتقا یافت.\n\n"
                 "🛡️ سطح قبلی: %d\n🛡️ سطح جدید: %d\n\n🌍 این ارتقا برای تمامی کشورهای جهان فعال شد.\n\n🔐 GLOBAL CRYPTO DEFENSE" % (old, f["lvl"]), cat="firewall")
    back_to(uid, "✅ %s دلار به خزانه امنیت جهانی واریز شد. ممنون!" % dols(v), CYBER_ROWS)


A_FWCOST = "🛡 هزینه هر سطح فایروال"


@route(A_FWCOST, admin=True)
def a_fwcost(uid):
    ask(uid, "🛡 هزینه‌ی هر سطح فایروال جهانی (دلار) — الان %s\nمثال: 20t یا 500b" % dols(fw_cost()), lambda t: a_fwcost2(uid, t), [["500b", "1t", "20t"]])


def a_fwcost2(uid, t):
    v = bnum(t)
    if not v or v < 1000:
        return back_to(uid, "❌ عدد نامعتبر.", ADMIN_ROWS)
    DB["settings"]["fw_cost"] = v
    back_to(uid, "✅ هزینه‌ی هر سطح: %s دلار" % dols(v), ADMIN_ROWS)


# ───── جام جهانی ─────
B_CUP = "🏆 جام جهانی"
CP_MY, CP_BRACKET, CP_TEAMS, CP_UP, CP_LUCK, CP_PRIZE, CP_RULES = ("⚽ مسابقات من", "🏆 جدول جام حذفی", "🌍 تیم‌های شرکت‌کننده", "🏃🏼 ارتقا تیم",
                                                                    "🎲 خرید شانس", "💰 جوایز مسابقات", "ℹ️ قوانین جام جهانی")
CP_REG, CP_UNREG = "🏆 ثبت‌نام در جام جهانی", "❌ انصراف"
WC_MAXPW = 200
MAXLUCK = 100
WC_UPG = [("🏃 تمرین", "🏃 تمرین بازیکنان", 2, 20_000_000), ("🧠 تاکتیک", "🧠 تاکتیک تیم", 3, 60_000_000),
          ("💪 بدنسازی", "💪 بدنسازی حرفه‌ای", 4, 150_000_000), ("⚡ اردو", "⚡ اردوی آماده‌سازی", 5, 250_000_000),
          ("👨‍🏫 مربی", "👨‍🏫 مربی حرفه‌ای", 7, 400_000_000), ("🏟️ مرکز تمرین", "🏟️ مرکز تمرینی پیشرفته", 10, 600_000_000)]
WC_LUCKS = [("🍀 معمولی", "🍀 شانس معمولی", 1, 50_000_000), ("🍀 خوب", "🍀 شانس خوب", 3, 140_000_000),
            ("🍀 عالی", "🍀 شانس عالی", 5, 220_000_000), ("🍀 ویژه", "🍀 شانس ویژه", 10, 400_000_000),
            ("🍀 افسانه‌ای", "🍀 شانس افسانه‌ای", 20, 700_000_000)]
WC_PRIZE = {"champ": 5_000_000_000, "second": 3_000_000_000, "third": 1_500_000_000,
            "sf": 600_000_000, "qf": 300_000_000, "r16": 150_000_000, "r32": 100_000_000}
WC_WIN = 10_000_000
SLOTS = [18, 20, 22]
STAGE_FA = {2: "فینال", 4: "نیمه‌نهایی", 8: "یک‌چهارم نهایی", 16: "یک‌هشتم نهایی", 32: "یک‌شانزدهم نهایی"}
A_CUP = "🏆 مدیریت جام جهانی"
AC_CREATE, AC_OPEN, AC_START, AC_TABLE, AC_PRIZES, AC_CLOSE, AC_END = ("🏆 ایجاد جام جهانی", "📝 باز کردن ثبت‌نام", "⚽ شروع مسابقات", "📊 جدول مسابقات",
                                                                       "🏅 جوایز جام", "🔴 بستن ثبت‌نام", "🛑 پایان جام جهانی")
AC_NOW, AC_MULT, AC_CAP = "⏩ اجرای فوری مسابقه‌ی بعدی", "💱 ضریب هزینه/جایزه", "👥 ظرفیت جام"
CUP_ADM_ROWS = [[AC_CREATE, AC_OPEN], [AC_START, AC_TABLE], [AC_PRIZES, AC_CLOSE], [AC_NOW, AC_MULT], [AC_CAP, AC_END], [A_PANEL]]
CUP_ROWS = [[CP_MY, CP_BRACKET], [CP_TEAMS, CP_UP], [CP_LUCK, CP_PRIZE], [CP_RULES], [B_BACK]]


def cup():
    e = EXT()
    cp = e.setdefault("cup", {"state": "none", "cap": 16, "teams": {}, "rounds": [], "champion": None, "year": 2026, "prog": "", "third": None})
    return cp


def wc_mult():
    return float(DB["settings"].get("wc_mult", 1.0))


def usd_m(d):
    return d * wc_mult() / 1e6


def pdol(d):
    return dols(d * wc_mult())


def cup_state_fa():
    st = cup()["state"]
    return {"none": "🔴 برگزار نشده", "created": "🟠 ایجاد شده (ثبت‌نام بسته)", "reg": "🟢 ثبت‌نام باز", "closed": "🟠 ثبت‌نام بسته", "running": "⚽ در حال برگزاری",
            "finished": "🏁 پایان یافته"}[st]


def all_matches():
    return [mt for r in cup()["rounds"] for mt in r["m"]] + ([cup()["third"]] if cup().get("third") else [])


def next_match():
    up = [mt for mt in all_matches() if not mt.get("res") and mt.get("a") and mt.get("b")]
    return min(up, key=lambda mt: mt["ts"]) if up else None


def fmt_ts(ts):
    return datetime.datetime.utcfromtimestamp(ts + 12600).strftime("%m/%d %H:%M")


def team_label(iso):
    c = C(iso) if iso else None
    return cname(c) if c else "❓"


def cup_header():
    cp = cup()
    L = ["🏆 جام جهانی | WORLD CUP 🌍", "", "⚽ به بزرگ‌ترین رقابت فوتبالی کشورها خوش آمدید!", "", "━━━━━━━━━━━━━━━━━━", "",
         "📅 دوره: جام جهانی %d" % cp["year"], "👥 تعداد تیم‌ها: %d / %d" % (len(cp["teams"]), cp["cap"]), "🏟 وضعیت: %s" % cup_state_fa(), "", "━━━━━━━━━━━━━━━━━━"]
    nm = next_match()
    if nm:
        L += ["", "🔥 مسابقه بعدی", "", "%s  🆚  %s" % (team_label(nm["a"]), team_label(nm["b"])), "", "⏰ زمان: %s (به وقت تهران)" % fmt_ts(nm["ts"]), "🏟 مرحله: %s" % nm["stage"], "", "━━━━━━━━━━━━━━━━━━"]
    L += ["", "💡 تیم کشورت را مدیریت کن،", "⚔️ در مسابقات پیروز شو،", "🏆 و جام جهانی را فتح کن!"]
    return "\n".join(L)


@route(B_CUP)
def r_cup(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    rows = [list(r) for r in CUP_ROWS]
    if cup()["state"] == "reg":
        rows.insert(0, [CP_UNREG] if c["iso"] in cup()["teams"] else [CP_REG])
    ask(uid, cup_header(), lambda t: cup_menu(uid, t), rows, back=False)


def cup_menu(uid, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    s = squash(t)
    for lab, fn in ((CP_REG, cup_reg), (CP_UNREG, cup_unreg), (CP_MY, cup_my), (CP_BRACKET, cup_bracket), (CP_TEAMS, cup_teams), (CP_UP, cup_up),
                    (CP_LUCK, cup_luck), (CP_PRIZE, cup_prizes), (CP_RULES, cup_rules)):
        if s == squash(lab):
            return fn(uid)
    r_cup(uid)


def cup_reg(uid):
    c, cp = mine(uid), cup()
    if cp["state"] != "reg":
        return back_to(uid, "📝 ثبت‌نام باز نیست.", CUP_ROWS)
    if c["iso"] in cp["teams"]:
        return back_to(uid, "✅ کشورت قبلاً ثبت‌نام شده.", CUP_ROWS)
    if len(cp["teams"]) >= cp["cap"]:
        return back_to(uid, "😕 ظرفیت جام تکمیله.", CUP_ROWS)
    cp["teams"][c["iso"]] = {"pw": 0, "luck": 0}
    back_to(uid, "🏆 ثبت‌نام جام جهانی 🌍⚽\n\n🏳️ کشور: %s\n👥 تعداد ثبت‌نامی‌ها: %d / %d\n💰 هزینه ثبت‌نام: رایگان 💵\n\n"
                 "✅ ثبت‌نامت انجام شد! بعد از شروع مسابقات امکان انصراف نیست.\n🔥 آماده‌ای برای فتح جام؟" % (cname(c), len(cp["teams"]), cp["cap"]), CUP_ROWS)


def cup_unreg(uid):
    c, cp = mine(uid), cup()
    if cp["state"] == "reg" and c["iso"] in cp["teams"]:
        cp["teams"].pop(c["iso"])
        return back_to(uid, "❌ از جام جهانی انصراف دادی.", CUP_ROWS)
    back_to(uid, "❌ انصراف ممکن نیست (مسابقات شروع شده یا ثبت‌نام نکردی).", CUP_ROWS)


def cup_my(uid):
    c = mine(uid)
    L = ["⚽ مسابقات %s" % cname(c), ""]
    ms = [mt for mt in all_matches() if c["iso"] in (mt.get("a"), mt.get("b"))]
    if not ms:
        L.append("هنوز مسابقه‌ای برای کشورت ثبت نشده." if c["iso"] in cup()["teams"] else "کشورت در جام ثبت‌نام نکرده.")
    for mt in sorted(ms, key=lambda x: x["ts"]):
        res = mt.get("res")
        L.append("%s | %s  %s  %s %s" % (mt["stage"], team_label(mt["a"]), ("%d-%d" % (res["ga"], res["gb"])) if res else "🆚", team_label(mt["b"]),
                                         "" if res else "⏰ " + fmt_ts(mt["ts"])))
    back_to(uid, "\n".join(L), CUP_ROWS)


def bracket_text():
    cp = cup()
    L = ["🏆 جام جهانی | جدول حذفی 🌍", "", "━━━━━━━━━━━━━━━━━━━━"]
    if not cp["rounds"]:
        L += ["", "هنوز قرعه‌کشی انجام نشده.", ""]
    for r in cp["rounds"]:
        L += ["", "⚔️ " + r["stage"], ""]
        for mt in r["m"]:
            res = mt.get("res")
            L.append("%s ── %s ── %s" % (team_label(mt["a"]), ("%d-%d" % (res["ga"], res["gb"])) if res else "🆚", team_label(mt["b"])))
        L += ["", "━━━━━━━━━━━━━━━━━━━━"]
    L += ["", "🏆 قهرمان جام جهانی: %s" % (team_label(cp["champion"]) if cp["champion"] else "❓"), "", "━━━━━━━━━━━━━━━━━━━━"]
    return "\n".join(L)


def cup_bracket(uid):
    back_to(uid, bracket_text(), CUP_ROWS)


def cup_teams(uid):
    cp = cup()
    L = ["🌍 تیم‌های شرکت‌کننده (%d / %d)" % (len(cp["teams"]), cp["cap"]), ""]
    L += ["%s — ⭐ %d / %d" % (team_label(i), tm["pw"], WC_MAXPW) for i, tm in cp["teams"].items()] or ["هنوز تیمی ثبت‌نام نکرده."]
    back_to(uid, "\n".join(L), CUP_ROWS)


def cup_team(uid):
    c, cp = mine(uid), cup()
    tm = cp["teams"].get(c["iso"])
    if not tm:
        back_to(uid, "🏆 اول باید کشورت رو برای جام ثبت‌نام کنی.", CUP_ROWS)
    return tm


def cup_up(uid):
    c = mine(uid)
    tm = cup_team(uid)
    if not tm:
        return
    L = ["⚽️ تقویت تیم ملی", "", "تیم ملی: %s" % cname(c), "⭐ قدرت فعلی: %d / %d" % (tm["pw"], WC_MAXPW), "", "━━━━━━━━━━━━━━━━━━", ""]
    for lab, full, gain, cost in WC_UPG:
        L += [full, "قدرت +%d" % gain, "💰 هزینه: %s" % pdol(cost), ""]
    L += ["━━━━━━━━━━━━━━━━━━", "", "📊 حداکثر قدرت تیم: %d" % WC_MAXPW, "💡 هرچه قدرت تیم بیشتر باشد، شانس پیروزی در مسابقات جام جهانی افزایش پیدا می‌کند.", "",
          "💰 موجودی: %s دلار" % dol(c["money"]), "", "👇 یک گزینه را انتخاب کنید:"]
    ask(uid, "\n".join(L), lambda t: cup_up_do(uid, t), chunk([u[0] for u in WC_UPG], 2) + [[B_CUP]], back=False)


def cup_up_do(uid, t):
    c, tm = mine(uid), cup_team(uid)
    if not tm:
        return
    u = next((u for u in WC_UPG if squash(u[0]) == squash(t)), None)
    if not u:
        return r_cup(uid)
    if tm["pw"] >= WC_MAXPW:
        return back_to(uid, "⭐ تیم به حداکثر قدرت رسیده.", CUP_ROWS)
    cost = usd_m(u[3])
    if c["money"] < cost:
        return back_to(uid, "❌ پول کافی نیست (نیاز: %s دلار)." % pdol(u[3]), CUP_ROWS)
    c["money"] -= cost
    tm["pw"] = min(WC_MAXPW, tm["pw"] + u[2])
    tell(uid, "✅ %s انجام شد! قدرت تیم: %d / %d" % (u[1], tm["pw"], WC_MAXPW))
    cup_up(uid)


def cup_luck(uid):
    c = mine(uid)
    tm = cup_team(uid)
    if not tm:
        return
    L = ["🍀 فروشگاه شانس", "", "کشور شرکت‌کننده: %s" % cname(c), "تعداد شانس های شما: %d/%d" % (tm["luck"], MAXLUCK), "━━━━━━━━━━━━━━━━━━", ""]
    for lab, full, n, cost in WC_LUCKS:
        L += [full, "➕ %d واحد شانس" % n, "💰 %s" % pdol(cost), ""]
    L += ["━━━━━━━━━━━━━━━━━━", "", "🍀 شانس خریداری‌شده در مسابقات جام جهانی مصرف می‌شود (هر بازی ۱ واحد)."]
    ask(uid, "\n".join(L), lambda t: cup_luck_do(uid, t), chunk([u[0] for u in WC_LUCKS], 2) + [[B_CUP]], back=False)


def cup_luck_do(uid, t):
    c, tm = mine(uid), cup_team(uid)
    if not tm:
        return
    u = next((u for u in WC_LUCKS if squash(u[0]) == squash(t)), None)
    if not u:
        return r_cup(uid)
    if tm["luck"] + u[2] > MAXLUCK:
        return back_to(uid, "❌ سقف شانس %d واحده." % MAXLUCK, CUP_ROWS)
    cost = usd_m(u[3])
    if c["money"] < cost:
        return back_to(uid, "❌ پول کافی نیست (نیاز: %s دلار)." % pdol(u[3]), CUP_ROWS)
    c["money"] -= cost
    tm["luck"] += u[2]
    tell(uid, "✅ %d واحد شانس خریدی! (مجموع %d/%d)" % (u[2], tm["luck"], MAXLUCK))
    cup_luck(uid)


def prize_text():
    P = WC_PRIZE
    return ("🏆 جوایز جام جهانی\n\n━━━━━━━━━━━━━━━━━━\n\n🥇 قهرمان جام جهانی\n💰 %s$\n🏆 جام قهرمانی\n⭐ پاداش ویژه قدرت تیم\n\n🥈 نایب‌قهرمان\n💰 %s$\n🥈 مدال نقره\n\n"
            "🥉 مقام سوم\n💰 %s$\n🥉 مدال برنز\n\n━━━━━━━━━━━━━━━━━━\n\n⚽ پاداش مراحل\n\n🔥 صعود به نیمه‌نهایی\n💰 %s$\n\n⚡ صعود به یک‌چهارم نهایی\n💰 %s$\n\n"
            "🎯 صعود به یک‌هشتم نهایی\n💰 %s$\n\n🌍 صعود به مرحله یک‌شانزدهم\n💰 %s$\n\n💥 هر برد: %s$\n\n━━━━━━━━━━━━━━━━━━\n\n⚖️ در بازی‌های جام جهانی تساوی وجود ندارد."
            % (pdol(P["champ"]), pdol(P["second"]), pdol(P["third"]), pdol(P["sf"]), pdol(P["qf"]), pdol(P["r16"]), pdol(P["r32"]), pdol(WC_WIN)))


def cup_prizes(uid):
    back_to(uid, prize_text(), CUP_ROWS)


def cup_rules(uid):
    cp = cup()
    back_to(uid, "ℹ️ قوانین جام جهانی\n\n▫️ هر کشور فقط یک تیم؛ ظرفیت جام: %d کشور\n▫️ ثبت‌نام رایگانه و تا تکمیل ظرفیت بازه\n▫️ قرعه‌کشی کاملاً تصادفیه\n"
                 "▫️ بازی‌ها بدون تساوی‌ان\n▫️ شانس پیروزی از «قدرت تیم» و «شانس» حساب می‌شه؛ هر بازی ۱ واحد شانس مصرف می‌شه\n"
                 "▫️ پاداش مرحله وقتی داده می‌شه که تیم به اون مرحله صعود کنه\n▫️ بازی‌ها ساعت ۱۸، ۲۰ و ۲۲ (به وقت تهران) برگزار می‌شن\n"
                 "▫️ بعد از شروع مسابقات امکان انصراف نیست" % cp["cap"], CUP_ROWS)


def cup_draw(cp):
    isos = list(cp["teams"])
    random.shuffle(isos)
    size = 1
    while size * 2 <= len(isos):
        size *= 2
    # اگر تعداد توان ۲ نبود، بقیه با «بای» مستقیم میرن (به‌ترتیب قرعه)
    byes = []
    if len(isos) > size:
        extra = len(isos) - size
        # حذف extra تیم اضافی با بازی پلی‌آف
        play = isos[:extra * 2]
        rest = isos[extra * 2:]
        ms = [{"a": play[i], "b": play[i + 1], "stage": "پلی‌آف", "res": None} for i in range(0, len(play), 2)]
        cp["rounds"].append({"stage": "پلی‌آف", "m": ms, "size": 0})
        cp["bye"] = rest
        return
    cp["rounds"].append(make_round(isos))


def make_round(isos):
    n = len(isos)
    stage = STAGE_FA.get(n, "مرحله %d تیمی" % n)
    return {"stage": stage, "size": n, "m": [{"a": isos[i], "b": isos[i + 1], "stage": stage, "res": None} for i in range(0, n, 2)]}


def next_slot(ts):
    d = datetime.datetime.utcfromtimestamp(ts + 12600)
    for day in range(0, 4):
        base = (d + datetime.timedelta(days=day)).replace(minute=0, second=0, microsecond=0)
        for h in SLOTS:
            cand = base.replace(hour=h)
            ct = (cand - datetime.datetime(1970, 1, 1)).total_seconds() - 12600
            if ct > ts:
                return ct
    return ts + 3600


def schedule_round(r, start):
    t = start
    for mt in r["m"]:
        t = next_slot(t)
        mt["ts"] = t
    return t


def rating(tm):
    return 50.0 + tm["pw"] + (25.0 if tm["luck"] > 0 else 0.0)


def sim_match(mt):
    cp = cup()
    ta, tb = cp["teams"][mt["a"]], cp["teams"][mt["b"]]
    ra, rb = rating(ta), rating(tb)
    for tm in (ta, tb):
        if tm["luck"] > 0:
            tm["luck"] -= 1
    win_a = random.random() < ra / (ra + rb)
    gw = random.choices([1, 2, 3, 4, 5], [30, 35, 20, 10, 5])[0]
    gl = random.randint(0, gw - 1)
    mt["res"] = {"ga": gw if win_a else gl, "gb": gl if win_a else gw, "w": mt["a"] if win_a else mt["b"]}
    return mt["res"]["w"], (mt["b"] if win_a else mt["a"])


def pay(iso, dollars, note=""):
    c = C(iso)
    if c and c["alive"]:
        c["money"] += usd_m(dollars)
        notify_country(iso, "🏆 %s: %s دلار به خزانه‌ات اضافه شد!" % (note, pdol(dollars)))


def stage_prize(size):
    return {2: None, 4: WC_PRIZE["sf"], 8: WC_PRIZE["qf"], 16: WC_PRIZE["r16"], 32: WC_PRIZE["r32"]}.get(size)


def cup_play(mt):
    cp = cup()
    w, l = sim_match(mt)
    pay(w, WC_WIN, "پاداش پیروزی")
    res = mt["res"]
    if mt.get("final"):
        cp["champion"] = w
        pay(w, WC_PRIZE["champ"], "قهرمانی جام جهانی")
        pay(l, WC_PRIZE["second"], "نایب‌قهرمانی")
        cp["state"] = "finished"
        announce("🏆 فینال جام جهانی به پایان رسید! ⚽️\n\n━━━━━━━━━━━━━━━━━━\n\n🔥 پس از هفته‌ها رقابت،\nسرانجام قهرمان جام جهانی مشخص شد!\n\n🏟️ نتیجه فینال\n\n"
                 "🥇 قهرمان: 🏆 %s\n🥈 نایب‌قهرمان: %s\n\n⚽️ نتیجه نهایی:\n%s  🆚  %s\n%d ─ %d\n\n━━━━━━━━━━━━━━━━━━\n\n👑 قهرمان جهان\n\n"
                 "تیمی که با قدرت، تلاش و عملکردی درخشان\nتا آخرین لحظه جنگید و جام قهرمانی را بالای سر برد.\n\n💰 جایزه قهرمان: %s$\n🏆 عنوان: قهرمان جام جهانی\n\n"
                 "━━━━━━━━━━━━━━━━━━\n\n🎉 پایان جام جهانی\n\nاز تمام کشورهایی که در این رقابت بزرگ شرکت کردند\nتشکر می‌کنیم.\n\n🌍 یک جام تمام شد...\n"
                 "🔥 اما رقابت‌های بزرگ بعدی در راه است!\n\n🏆 تبریک به قهرمان جهان!\n#جام_جهانی" % (
                     team_label(w), team_label(l), team_label(mt["a"]), team_label(mt["b"]), res["ga"], res["gb"], pdol(WC_PRIZE["champ"])), cat="worldcup", iso=(w, l))
        return
    if mt.get("third"):
        pay(w, WC_PRIZE["third"], "مقام سوم")
        announce("🥉 مقام سوم جام جهانی\n\n%s با نتیجه %d-%d %s را شکست داد و سوم شد!\n💰 جایزه: %s$\n#جام_جهانی" % (
            team_label(w), max(res["ga"], res["gb"]), min(res["ga"], res["gb"]), team_label(l), pdol(WC_PRIZE["third"])), cat="worldcup", iso=(w, l))
        return
    announce("GOOOOOOOOLL⚽️\n\n🏆 پایان مسابقه جام جهانی ⚽️\n\n🎉 پیروزی بزرگ!\n\n %s با عملکردی درخشان موفق شد\n%s را شکست دهد!\n\n━━━━━━━━━━━━━━━━━━\n\n"
             "⚽️ نتیجه نهایی:\n%s  %d ─ %d  %s\n\n🏅 برنده: %s\n\n💰 پاداش پیروزی: %s$\n\n🔥 یک قدم دیگر تا قهرمانی جهان!\n\n🌍 جام جهانی ادامه دارد...\n#جام_جهانی" % (
                 team_label(w), team_label(l), team_label(mt["a"]), res["ga"], res["gb"], team_label(mt["b"]), team_label(w), dols(WC_WIN * wc_mult())),
             cat="worldcup", iso=(w, l))


def cup_advance(cp, t):
    """اگر همه‌ی بازی‌های دور تموم شده، دور بعد رو می‌سازه."""
    r = cp["rounds"][-1]
    if any(not mt.get("res") for mt in r["m"]):
        return
    winners = [mt["res"]["w"] for mt in r["m"]]
    if r["size"] == 0:                                    # پلی‌آف تموم شد
        winners += cp.pop("bye", [])
        random.shuffle(winners)
        nr = make_round(winners)
    elif r["size"] == 2:
        return
    else:
        nr = make_round(winners)
    prize = stage_prize(nr["size"])
    if prize:
        for iso in winners:
            pay(iso, prize, "صعود به %s" % nr["stage"])
    last = max(mt["ts"] for mt in r["m"])
    if nr["size"] == 2:
        losers = [(mt["a"] if mt["res"]["w"] == mt["b"] else mt["b"]) for mt in r["m"]]
        cp["third"] = {"a": losers[0], "b": losers[1], "stage": "رده‌بندی (سوم و چهارم)", "res": None, "third": True}
        tt = next_slot(last)
        cp["third"]["ts"] = tt
        nr["m"][0]["final"] = True
        nr["m"][0]["ts"] = next_slot(tt)
    else:
        schedule_round(nr, last)
    cp["rounds"].append(nr)
    announce("🏆 %s جام جهانی مشخص شد!\n\n%s\n\n⏰ اولین بازی: %s (به وقت تهران)\n#جام_جهانی" % (
        nr["stage"], "\n".join("%s 🆚 %s" % (team_label(mt["a"]), team_label(mt["b"])) for mt in nr["m"]), fmt_ts(min(mt["ts"] for mt in nr["m"]))), cat="worldcup")


def cup_tick(t):
    cp = cup()
    if cp["state"] != "running" or DB["settings"]["paused"]:
        return
    for mt in sorted(all_matches(), key=lambda x: x["ts"]):
        if not mt.get("res") and mt.get("a") and mt.get("b") and mt["ts"] <= t:
            cup_play(mt)
    if cp["state"] == "running":
        cup_advance(cp, t)
        # برنامه‌ی امروز
        tn = tnow()
        day = tn.strftime("%Y-%m-%d")
        if tn.hour >= 12 and cp.get("prog") != day:
            today = [mt for mt in all_matches() if not mt.get("res") and mt.get("a") and
                     datetime.datetime.utcfromtimestamp(mt["ts"] + 12600).strftime("%Y-%m-%d") == day]
            cp["prog"] = day
            if today:
                today.sort(key=lambda x: x["ts"])
                announce("🏆 WORLD WAR | جام جهانی\n\n⚽️ برنامه مسابقات امروز\n\n━━━━━━━━━━━━━━━━━━\n\n%s\n\n━━━━━━━━━━━━━━━━━━\n\n📢 توجه:\n"
                         "تمام مسابقات طبق ساعت اعلام‌شده برگزار می‌شوند.\nنتیجه بازی پس از پایان مسابقه در همین چنل اعلام خواهد شد.\n\n🔥 آماده رقابت باشید!\n\n"
                         "🏆 چه کشوری قهرمان جام جهانی می‌شود؟\n#جام_جهانی" % "\n\n".join(
                             "%s 🆚 %s\n🕐 ساعت برگزاری: %s" % (team_label(mt["a"]), team_label(mt["b"]), datetime.datetime.utcfromtimestamp(mt["ts"] + 12600).strftime("%H:%M")) for mt in today),
                         cat="worldcup")


EXT_TICKS.append(cup_tick)


@route(A_CUP, admin=True)
def a_cup(uid):
    cp = cup()
    back_to(uid, "👑 پنل مدیریت جام جهانی\n\n🏆 مدیریت کامل مسابقات از این بخش انجام می‌شود.\n\n━━━━━━━━━━━━━━━━━━\n\n🏆 وضعیت جام: %s\n👥 تیم‌های ثبت‌نام‌شده: \"%d / %d\"\n"
                 "💱 ضریب هزینه/جایزه: ×%s\n\n━━━━━━━━━━━━━━━━━━\n\n⚠️ مدیریت جام جهانی فقط در اختیار مالک و ادمین ربات است." % (
                     cup_state_fa(), len(cp["teams"]), cp["cap"], wc_mult()), CUP_ADM_ROWS)


@route(AC_CREATE, admin=True)
def ac_create(uid):
    cp = cup()
    if cp["state"] in ("running",):
        return back_to(uid, "⚠️ جام در حال برگزاریه.", CUP_ADM_ROWS)
    cp.update(state="created", teams={}, rounds=[], champion=None, third=None, prog="")
    cp["year"] = max(cp.get("year", 2026), 2026)
    back_to(uid, "✅ جام جهانی %d ایجاد شد. حالا «%s» رو بزن." % (cp["year"], AC_OPEN), CUP_ADM_ROWS)


@route(AC_OPEN, admin=True)
def ac_open(uid):
    cp = cup()
    if cp["state"] not in ("created", "closed", "reg"):
        return back_to(uid, "⚠️ اول «%s» رو بزن." % AC_CREATE, CUP_ADM_ROWS)
    cp["state"] = "reg"
    announce("🏆 ثبت‌نام جام جهانی آغاز شد! 🌍\n\n⚽ کشور خود را وارد بزرگ‌ترین رقابت فوتبال کنید!\n\n━━━━━━━━━━━━━━━━━━\n\n👥 ظرفیت مسابقات: %d تیم\n💰 هزینه ثبت‌نام: رایگان$\n\n"
             "🗓 مهلت ثبت‌نام:\nتا تکمیل ظرفیت\n\n━━━━━━━━━━━━━━━━━━\n\n📌 شرایط شرکت:\n\n▫️ هر کشور فقط یک تیم\n▫️ ظرفیت جام: %d کشور\n▫️ جوایز به تیم‌های برتر تعلق می‌گیرد\n\n"
             "━━━━━━━━━━━━━━━━━━\n\n🔥 آماده رقابت برای قهرمانی جهان هستی؟\n#جام_جهانی" % (cp["cap"], cp["cap"]), cat="worldcup")
    back_to(uid, "✅ ثبت‌نام باز شد و اعلان به کانال رفت.", CUP_ADM_ROWS)


@route(AC_CLOSE, admin=True)
def ac_close(uid):
    cp = cup()
    if cp["state"] == "reg":
        cp["state"] = "closed"
    back_to(uid, "🔴 ثبت‌نام بسته شد.", CUP_ADM_ROWS)


@route(AC_START, admin=True)
def ac_start(uid):
    cp = cup()
    if cp["state"] not in ("reg", "closed"):
        return back_to(uid, "⚠️ اول جام رو بساز و ثبت‌نام رو باز کن.", CUP_ADM_ROWS)
    if len(cp["teams"]) < 2:
        return back_to(uid, "⚠️ حداقل ۲ تیم لازمه.", CUP_ADM_ROWS)
    cp["rounds"] = []
    cup_draw(cp)
    r = cp["rounds"][0]
    schedule_round(r, now())
    cp["state"] = "running"
    cp["prog"] = ""
    announce("🏆 قرعه‌کشی جام جهانی انجام شد!\n\n%s\n\n⏰ اولین بازی: %s (به وقت تهران)\n#جام_جهانی" % (
        "\n".join("%s 🆚 %s" % (team_label(mt["a"]), team_label(mt["b"])) for mt in r["m"]), fmt_ts(min(mt["ts"] for mt in r["m"]))), cat="worldcup")
    back_to(uid, "⚽ مسابقات شروع شد.", CUP_ADM_ROWS)


@route(AC_TABLE, admin=True)
def ac_table(uid):
    back_to(uid, bracket_text(), CUP_ADM_ROWS)


@route(AC_PRIZES, admin=True)
def ac_prizes(uid):
    back_to(uid, prize_text(), CUP_ADM_ROWS)


@route(AC_END, admin=True)
def ac_end(uid):
    cp = cup()
    cp.update(state="none", teams={}, rounds=[], champion=None, third=None)
    back_to(uid, "🛑 جام جهانی پایان یافت/لغو شد.", CUP_ADM_ROWS)


@route(AC_NOW, admin=True)
def ac_now(uid):
    cp = cup()
    mt = next_match()
    if cp["state"] != "running" or not mt:
        return back_to(uid, "مسابقه‌ای در انتظار نیست.", CUP_ADM_ROWS)
    mt["ts"] = now() - 1
    cup_tick(now())
    back_to(uid, "✅ مسابقه برگزار شد.", CUP_ADM_ROWS)


@route(AC_MULT, admin=True)
def ac_mult(uid):
    ask(uid, "💱 ضریب هزینه و جایزه‌ی جام جهانی (الان ×%s)\nمثلاً 0.001 یعنی همه‌چی هزار برابر ارزون‌تر." % wc_mult(), lambda t: ac_mult2(uid, t), [["0.0001", "0.001", "0.01", "1"]])


def ac_mult2(uid, t):
    v = num(t)
    if not v or v <= 0:
        return back_to(uid, "❌ عدد نامعتبر.", CUP_ADM_ROWS)
    DB["settings"]["wc_mult"] = v
    back_to(uid, "✅ ضریب: ×%s" % v, CUP_ADM_ROWS)


@route(AC_CAP, admin=True)
def ac_cap(uid):
    ask(uid, "👥 ظرفیت جام (الان %d) — ۴، ۸، ۱۶ یا ۳۲:" % cup()["cap"], lambda t: ac_cap2(uid, t), [["4", "8", "16", "32"]])


def ac_cap2(uid, t):
    v = num(t)
    if v not in (4, 8, 16, 32):
        return back_to(uid, "❌ فقط ۴، ۸، ۱۶ یا ۳۲.", CUP_ADM_ROWS)
    cup()["cap"] = int(v)
    back_to(uid, "✅ ظرفیت: %d" % v, CUP_ADM_ROWS)


ADMIN_ROWS.insert(-2, [A_CUP, A_FWCOST])


# ═════════════ تولید داخلی (خودرو سواری، خودرو سنگین، موبایل) ═════════════
B_DOM = "🏭 تولید داخلی"
DOM_GROUPS = {
    "car": ("🚗 کارخانه ماشین سواری", "ind_car", 2, [
        ("lambo", "🏎 لامبورگینی", "🏎 لامبورگینی", 4, 900), ("toyota", "🚗 تویوتا", "🚗 تویوتا", 3, 600),
        ("bugatti", "🏁 بوگاتی", "🏁 بوگاتی", 2, 1200), ("rolls", "👑 رولزرویس", "👑 رولزرویس", 1, 1500)]),
    "heavy": ("🚛 کارخانه ماشین سنگین", "ind_heavy", 3, [
        ("volvo", "🚛 ولوو", "🚛 ولوو", 3, 700), ("scania", "🚚 اسکانیا", "🚚 اسکانیا", 3, 650),
        ("renault", "🚐 رنو", "🚐 رنو تراک", 2, 500), ("mack", "🚜 ماک", "🚜 ماک", 2, 600)]),
    "phone": ("📱 تولید موبایل", "ind_phone", 3, []),
}
DOM_PHONES = {
    "🍎 اپل": ("apple", [("iPhone 18 Pro Max", 3, 800), ("iPhone 18", 4, 600), ("iPhone 17 Pro Max", 4, 600),
                         ("iPhone 17", 5, 450), ("iPhone 16 Pro Max", 5, 450), ("iPhone 16", 6, 350)]),
    "🌌 سامسونگ": ("samsung", [("Galaxy S26 Ultra", 3, 750), ("Galaxy S26", 4, 550), ("Galaxy S25 Ultra", 4, 550),
                               ("Galaxy S25", 5, 420), ("Galaxy S24 Ultra", 5, 420), ("Galaxy S24", 6, 320)]),
    "🔶 شیائومی": ("xiaomi", [("Xiaomi 17 Pro Max", 3, 500)]),
}
for _b, (_k, _ms) in DOM_PHONES.items():
    DOM_GROUPS["phone"][3].extend([("%s:%d" % (_k, i), _b, n, cap, cost) for i, (n, cap, cost) in enumerate(_ms)])
DOM_INCOME_PER_UNIT = 6          # M$ در ساعت به‌ازای هر دستگاه ظرفیت روزانه
IMG_CATS.update({"ind_car": "🚗 کارخانه ماشین سواری", "ind_heavy": "🚛 کارخانه ماشین سنگین", "ind_phone": "📱 کارخانه موبایل"})
CARD_STYLE.update({"ind_car": ("CAR FACTORY", (150, 30, 40), (30, 10, 14)), "ind_heavy": ("HEAVY TRUCKS", (90, 90, 100), (25, 25, 32)),
                   "ind_phone": ("MOBILE FACTORY", (40, 90, 160), (10, 20, 44))})
TAG_CAT.update({"خبرصنعتی": "industry"})
B_DOM_CAR, B_DOM_HEAVY, B_DOM_PHONE, B_DOM_MY = "🚗 کارخانه ماشین سواری", "🚛 کارخانه ماشین سنگین", "📱 تولید موبایل", "📋 کارخانه‌های من"
DOM_HUB = [[B_DOM_CAR, B_DOM_HEAVY], [B_DOM_PHONE, B_DOM_MY], [B_ECO, B_BACK]]
DOM_BTN = {B_DOM_CAR: "car", B_DOM_HEAVY: "heavy", B_DOM_PHONE: "phone"}


def dom_items(g):
    return DOM_GROUPS[g][3]


def dom_item(g, key):
    return next((x for x in dom_items(g) if x[0] == key), None)


def dom_btn(g, it):
    return it[2] if g == "phone" else it[1]


def dom_has(c, g, key):
    return key in c.setdefault("dom", {}).get(g, [])


def dom_income(c):
    tot = 0
    for g, ks in (c.get("dom") or {}).items():
        for k in ks:
            it = dom_item(g, k)
            if it:
                tot += it[3] * DOM_INCOME_PER_UNIT
    return tot


@route(B_DOM)
def r_dom(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    n = sum(len(v) for v in (c.get("dom") or {}).values())
    tell(uid, "🏭 تولید داخلی %s\n\n🏭 کارخانه‌های فعال: %d\n💵 درآمد تولید: %s M$ در ساعت\n💰 خزانه: %s M$\n\n👇 یک بخش رو انتخاب کن" % (
        cname(c), n, m(dom_income(c)), m(c["money"])), DOM_HUB)


@route(B_DOM_MY)
def r_dom_my(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    L = ["📋 کارخانه‌های %s" % cname(c), ""]
    any_ = False
    for g, (title, _cat, _t, _its) in DOM_GROUPS.items():
        ks = (c.get("dom") or {}).get(g, [])
        if ks:
            any_ = True
            L.append(title)
            for k in ks:
                it = dom_item(g, k)
                if it:
                    L.append("  • %s — ⚡ %d دستگاه در روز" % (it[2] if g != "phone" else it[1], it[3]))
    if not any_:
        L.append("هنوز کارخانه‌ای تأسیس نکردی.")
    L += ["", "💵 درآمد کل تولید: %s M$ در ساعت" % m(dom_income(c))]
    tell(uid, "\n".join(L), DOM_HUB)


def _dom_menu(uid, g):
    c = mine(uid)
    if not c:
        return no_country(uid)
    title, cat, tech, items = DOM_GROUPS[g]
    if c["tech"] < tech:
        return tell(uid, "🔒 «%s» تکنولوژی %d می‌خواد (الان %d داری)." % (title, tech, c["tech"]), DOM_HUB)
    L = [title, "💰 خزانه: %s M$" % m(c["money"]), ""]
    rows = []
    for it in items:
        have = dom_has(c, g, it[0])
        L.append("%s %s — ⚡ %d در روز | %s" % ("✅" if have else "🏭", dom_btn(g, it), it[3], "تأسیس شده" if have else "%s M$" % m(it[4])))
        rows.append(["تأسیس " + dom_btn(g, it)])
    ask(uid, "\n".join(L) + "\n\n👇 برای تأسیس انتخاب کن", lambda t: dom_found(uid, g, t), rows)


def _mk_dom_route(btn, g):
    @route(btn)
    def _r(uid):
        return dom_phone_brand(uid) if g == "phone" else _dom_menu(uid, g)
    return _r


def dom_phone_brand(uid):
    c = mine(uid)
    if not c:
        return no_country(uid)
    title, cat, tech, items = DOM_GROUPS["phone"]
    if c["tech"] < tech:
        return tell(uid, "🔒 «%s» تکنولوژی %d می‌خواد (الان %d داری)." % (title, tech, c["tech"]), DOM_HUB)
    ask(uid, "📱 تولید موبایل — یک برند انتخاب کن:", lambda t: dom_phone_list(uid, t), chunk(list(DOM_PHONES), 3))


def dom_phone_list(uid, t):
    c = mine(uid)
    b = next((b for b in DOM_PHONES if squash(b) == squash(t)), None)
    if not c or not b:
        return dom_phone_brand(uid)
    bk = DOM_PHONES[b][0]
    its = [x for x in dom_items("phone") if x[0].startswith(bk + ":")]
    L = ["%s — تولید موبایل" % b, "💰 خزانه: %s M$" % m(c["money"]), ""]
    rows = []
    for it in its:
        have = dom_has(c, "phone", it[0])
        L.append("%s %s — ⚡ %d در روز | %s" % ("✅" if have else "🏭", it[2], it[3], "تأسیس شده" if have else "%s M$" % m(it[4])))
        rows.append(["تأسیس " + it[2]])
    ask(uid, "\n".join(L) + "\n\n👇 برای تأسیس انتخاب کن", lambda x: dom_found(uid, "phone", x), rows)


def dom_found(uid, g, t):
    c = mine(uid)
    if not c:
        return no_country(uid)
    title, cat, tech, items = DOM_GROUPS[g]
    name = re.sub(r"^تأسیس\s*", "", (t or "").strip())
    it = next((x for x in items if squash(dom_btn(g, x)) == squash(name)), None)
    if not it:
        return r_dom(uid)
    if dom_has(c, g, it[0]):
        tell(uid, "✅ این کارخانه رو قبلاً تأسیس کردی.")
        return r_dom(uid)
    if c["money"] < it[4]:
        tell(uid, "❌ پول کافی نداری (%s M$ لازمه)." % m(it[4]))
        return r_dom(uid)
    c["money"] -= it[4]
    c.setdefault("dom", {}).setdefault(g, []).append(it[0])
    xp_add(c, 8)
    cap = it[3]
    if g == "phone":
        brand = {"apple": "اپل", "samsung": "سامسونگ", "xiaomi": "شیائومی"}[it[0].split(":")[0]]
        subj = "کارخانه 📱 %s ( %s ) خود را ساخت" % (brand, it[2])
    else:
        subj = "کارخانه %s خود را ساخت" % (it[2])
    txt = "🏭 خبر صنعتی!\n\nکشور %s %s!\n\n⚡ ظرفیت تولید روزانه:  %d دستگاه\n\n#خبر_صنعتی" % (cname(c), subj, cap)
    announce(txt, cat=cat, iso=c["iso"], sub=("car" if g == "car" else None))
    tell(uid, "✅ تأسیس شد! 💵 درآمد تولید تو الان %s M$ در ساعته." % m(dom_income(c)))
    r_dom(uid)


for _b, _g in DOM_BTN.items():
    _mk_dom_route(_b, _g)


def dom_tick(t):
    if DB["settings"]["paused"]:
        return
    for c in DB["countries"].values():
        if not (c["owner"] and c["alive"]) or not c.get("dom"):
            continue
        last = c.get("dom_t") or t
        hrs = int((t - last) / 3600)
        if hrs >= 1:
            hrs = min(hrs, 48)
            c["money"] += dom_income(c) * hrs * DB["settings"]["speed"]
            c["dom_t"] = t if hrs >= 48 else last + hrs * 3600
        else:
            c["dom_t"] = last


EXT_TICKS.append(dom_tick)

ECO_ROWS.insert(-1, [B_DOM])


# ═════════════ دریافت عکس ═════════════
def on_photo(chat, msg):
    uid = chat
    u = user(uid, chat)
    u["seen"] = now()
    note_user(uid, msg.get("from") or {})
    if u["banned"] and not is_admin(uid):
        return
    fid = msg["photo"][-1]["file_id"]
    cap = (msg.get("caption") or "").strip()
    fn = PHOTO.pop(uid, None)
    if fn:
        CTX.pop(uid, None)
        return fn(fid, cap)
    tell(uid, "🖼 عکس رسید ولی الان منتظر عکس نبودم. از بخش مربوطه (مثلاً «🖼 تنظیم عکس بیانیه») شروع کن.", main_rows(uid))


# ═════════════ دریافت پیام‌ها ═════════════
def note_user(uid, frm):
    u = user(uid)
    name = " ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x)
    if name:
        u["name"] = name
    u["uname"] = frm.get("username") or ""


def set_menu_commands():
    try:
        api("setMyCommands", {"commands": [
            {"command": "start", "description": "🏠 شروع / منوی اصلی"},
            {"command": "menu", "description": "📋 منوی اصلی"},
            {"command": "cancel", "description": "❌ انصراف از کار فعلی"},
            {"command": "ping", "description": "🏓 تست سرعت ربات"},
        ]})
    except Exception as e:  # noqa: BLE001
        print("setMyCommands ناموفق:", e)


# محافظت از کد ورود ادمین در برابر حدس‌زدن
_ADMIN_CODE_ATTEMPTS = defaultdict(deque)
_ADMIN_CODE_LOCKED = {}
_ADMIN_CODE_MAX_ATTEMPTS = 5
_ADMIN_CODE_WINDOW = 600
_ADMIN_CODE_LOCK_SECONDS = 900


def check_admin_code(uid, supplied):
    uid = str(uid)
    t = time.monotonic()
    locked_until = _ADMIN_CODE_LOCKED.get(uid, 0.0)
    if t < locked_until:
        return False, int(locked_until - t) + 1
    attempts = _ADMIN_CODE_ATTEMPTS[uid]
    while attempts and t - attempts[0] > _ADMIN_CODE_WINDOW:
        attempts.popleft()
    expected = str(admin_code() or "")
    if expected and hmac.compare_digest(str(supplied), expected):
        attempts.clear()
        _ADMIN_CODE_LOCKED.pop(uid, None)
        return True, 0
    attempts.append(t)
    if len(attempts) >= _ADMIN_CODE_MAX_ATTEMPTS:
        _ADMIN_CODE_LOCKED[uid] = t + _ADMIN_CODE_LOCK_SECONDS
        attempts.clear()
        return False, _ADMIN_CODE_LOCK_SECONDS
    return False, -(_ADMIN_CODE_MAX_ATTEMPTS - len(attempts))


def on_text(uid, chat, text, msg):
    u = user(uid, chat)
    u["seen"] = now()
    note_user(uid, msg.get("from") or {})
    admin = is_admin(uid)
    t = (text or "").strip()
    if not t:
        return
    if u["banned"] and not admin:
        return tell(uid, "🚫 دسترسی شما توسط ادمین مسدود شده است.")
    if u.get("lang") == "en":
        t = EN_MAP.get(uid, {}).get(t, t)
    if t.startswith("/"):
        cmd, _, arg = t[1:].partition(" ")
        cmd = cmd.lower().split("@")[0]
        arg = arg.strip()
        if cmd == "ping":
            lg = LAG.get(chat)
            return send(chat, "🏓 pong" + (("\n⏱ پیامت %.1f ثانیه بعد از ارسال به بات رسید" % lg) if lg is not None and lg >= 0 else ""))
        if cmd in ("start", "menu"):
            clear(uid)
            return tell(uid, start_text(uid), main_rows(uid), force=True)
        if cmd in ("lang", "language"):
            return r_lang(uid)
        if cmd == "cancel":
            return menu(uid)
        if cmd == "admin":
            if admin:
                return menu(uid, "👑 شما از قبل ادمین هستید.")
            valid, detail = check_admin_code(uid, arg)
            if valid:
                if uid not in DB["settings"]["admins"]:
                    DB["settings"]["admins"].append(uid)
                    save()
                clear(uid)
                return tell(uid, "👑 تو حالا ادمین هستی! دکمه‌ی «🛠 پنل ادمین» اضافه شد.", main_rows(uid), force=True)
            if detail > 0:
                return menu(uid, "⛔ تلاش‌های ورود موقتاً مسدود شد. %s ثانیه دیگر امتحان کن." % detail)
            return menu(uid, "❌ کد اشتباه است. تعداد تلاش باقی‌مانده: %d" % abs(detail))
        if cmd == "setchannel" and admin:
            if not arg:
                return tell(uid, "مثال: /setchannel @WorldWar_Empire")
            DB["settings"]["channel"] = arg
            DB["settings"]["warned"] = False
            return menu(uid, "✅ کانال ثبت شد: " + arg)
        return menu(uid, "❓ دستور ناشناخته.")
    if squash(t) in ("بازگشت", "لغو", "منو", "منوی اصلی", "شروع"):
        return menu(uid)
    tt = en_digits(t)
    for rx, fn, adm in REGEX_ROUTES:
        mt = rx.match(tt)
        if mt:
            if adm and not admin:
                return
            clear(uid)
            return fn(uid, mt)
    lab = ROUTE_N.get(squash(re.sub(r"\(\s*\d+\s*\)", "", tt)))
    if lab:
        fn, adm = ROUTES[lab]
        if adm and not admin:
            return tell(uid, "⛔ این بخش مخصوص ادمینه.")
        clear(uid)
        return fn(uid)
    fn = CTX.pop(uid, None)
    PHOTO.pop(uid, None)
    if fn:
        return fn(t)
    menu(uid, "❓ متوجه نشدم؛ از دکمه‌های منو استفاده کن 👇")


# ضداسپم ورودی: هر کاربر حداکثر ۸ پیام در ۱۰ ثانیه و ۴۰ پیام در دقیقه (قابل تنظیم).
_INCOMING_RATE = defaultdict(deque)
_INCOMING_RATE_LOCK = threading.Lock()
_INCOMING_CHECKS = 0


def allow_incoming(uid):
    global _INCOMING_CHECKS
    t = time.monotonic()
    with _INCOMING_RATE_LOCK:
        q = _INCOMING_RATE[str(uid)]
        while q and t - q[0] > 60:
            q.popleft()
        burst = sum(1 for stamp in q if t - stamp <= USER_BURST_WINDOW)
        if burst >= USER_BURST_COUNT or len(q) >= USER_MINUTE_LIMIT:
            return False
        q.append(t)
        _INCOMING_CHECKS += 1
        if _INCOMING_CHECKS % 500 == 0 and len(_INCOMING_RATE) > 10000:
            for key in list(_INCOMING_RATE.keys()):
                if not _INCOMING_RATE[key]:
                    _INCOMING_RATE.pop(key, None)
        return True


def handle_update(upd):
    msg = upd.get("message")
    if not msg:
        return
    ch = msg.get("chat") or {}
    frm = msg.get("from") or {}
    if ch.get("type") != "private" or frm.get("is_bot"):
        return
    chat = str(ch.get("id"))
    mid = msg.get("message_id")
    if mid and (chat, mid) in SEEN:
        return
    SEEN.append((chat, mid))
    del SEEN[:-500]
    if not allow_incoming(chat):
        # پاسخ ندادن به هر پیام اسپم، خودش از Flood شدن بات جلوگیری می‌کند.
        return
    try:
        lag = now() - float(msg.get("date"))
    except (TypeError, ValueError):
        lag = None
    LAG[chat] = lag
    if lag is not None and lag > 5:
        print("⏱ پیامِ %s با %.0f ثانیه تأخیر به بات رسید" % (chat[-6:], lag))
    if msg.get("document"):
        return on_document(chat, msg)
    if msg.get("photo"):
        return on_photo(chat, msg)
    on_text(chat, chat, msg.get("text") or "", msg)


def safe_handle(upd):
    try:
        handle_update(upd)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        try:
            chat = ((upd.get("message") or {}).get("chat") or {}).get("id")
            if chat:
                send(str(chat), "⚠️ یه خطای داخلی پیش اومد؛ دوباره امتحان کن. اگه تکرار شد به ادمین بگو.")
        except Exception:  # noqa: BLE001
            pass


def main():
    if not TOKEN or TOKEN.startswith("PUT_"):
        print("❌ اول توکن بات رو بذار:\n   BOT_TOKEN=\"توکن\" python main.py")
        sys.exit(1)
    load()
    print("🛡 محدودیت نرخ خروجی و ضداسپم ورودی فعال است.")
    print("🔐 سیستم ارتقای ادمین فعال است؛ کد از WW_ADMIN_CODE خوانده می‌شود.")
    # این نسخه از long polling استفاده می‌کند؛ webhook قدیمی را بدون حذف پیام‌های معوق پاک می‌کند.
    try:
        api("deleteWebhook", {"drop_pending_updates": False})
    except Exception as e:  # noqa: BLE001
        print("⚠️ پاک‌سازی webhook انجام نشد:", str(e)[:180])
    try:
        me = api("getMe").get("result") or {}
        print("✅ متصل شد: @%s" % me.get("username"))
    except Exception as e:  # noqa: BLE001
        print("⚠️ getMe ناموفق (توکن یا اینترنت رو چک کن):", e)
    set_menu_commands()
    CH_ASYNC["on"] = True
    threading.Thread(target=channel_worker, daemon=True).start()
    print("🌍 ربات روشن شد؛ برای توقف Ctrl+C بزن.")
    last_save = now()
    while True:
        got = []
        try:
            params = {"timeout": 20, "limit": 25, "allowed_updates": ["message"]}
            if DB.get("offset"):
                params["offset"] = DB["offset"]
            got = api("getUpdates", params, read_timeout=40).get("result") or []
            for upd in got:
                safe_handle(upd)
                DB["offset"] = upd["update_id"] + 1
            tick_all()
            if got or now() - last_save > 30:
                save()
                last_save = now()
        except KeyboardInterrupt:
            save()
            print("👋 خداحافظ")
            return
        except ApiError as e:
            msg = str(e)
            if "401" in msg:
                print("❌ توکن اشتباهه؛ از @BotFather توکن درست رو بگیر.")
            elif "409" in msg:
                print("❌ تداخل 409: این بات در نمونه دیگری هم در حال long polling است؛ تعداد Replicaهای Railway را روی ۱ بگذارید.")
                time.sleep(30)
                continue
            else:
                print("خطا:", msg)
            time.sleep(5)
        except requests.RequestException as e:
            print("خطای شبکه:", e)
            time.sleep(3)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            time.sleep(3)


if __name__ == "__main__":
    main()
