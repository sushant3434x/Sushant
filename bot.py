#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shein India Coupon Checker + Protector
SAFE • FAST • PER-USER • GITHUB READY
"""

import os
import re
import time
import csv
import json
from datetime import datetime
from threading import Lock, Timer, Event
from collections import defaultdict

import requests
import telebot
from telebot.apihelper import ApiTelegramException

# =========================
# CONFIG & DEFAULT CREDENTIALS
# =========================
# Hardcoded defaults as requested
DEFAULT_TOKEN = "8387153384:AAHXQc9Rf9i7aIzZAPusdNTeCLtGIJi_Obs"
DEFAULT_OWNER_ID = 7835819531

COOKIES_FILE = "cook.txt"
URL = "https://www.sheinindia.in/api/cart/apply-voucher"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
)

BASE_RESULTS_DIR = "results"
BASE_STORED_DIR = "stored_coupons"
MAX_CODES = 5000

# =========================
# CONSTANT TEXTS
# =========================
COMMON_FOOTER = "\n\n🛑 𝗨𝘀𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 /stop 𝘁𝗼 𝘀𝘁𝗼𝗽 𝘁𝗵𝗲 𝗯𝗼𝘁"

IMPORTANT_PROTECTION_TEXT = (
    "⚠️ 𝗜𝗠𝗣𝗢𝗥𝗧𝗔𝗡𝗧:\n"
    "𝗬𝗢𝗨𝗥 𝗖𝗢𝗨𝗣𝗢𝗡𝗦 𝗔𝗥𝗘 𝗡𝗢𝗪 𝗖𝗛𝗘𝗖𝗞𝗘𝗗 𝗔𝗡𝗗 𝗔𝗥𝗘 𝗜𝗡 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡.\n"
    "𝗨𝗦𝗘 /stop 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗧𝗢 𝗦𝗧𝗢𝗣 𝗕𝗢𝗧 𝗔𝗡𝗗 𝗬𝗢𝗨 𝗖𝗔𝗡 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗨𝗣𝗢𝗡 𝗔𝗙𝗧𝗘𝗥 𝟭𝟬–𝟭𝟱 𝗠𝗜𝗡𝗦."
)

STARTUP_BROADCAST_TEXT = (
    "✅ 𝗕𝗢𝗧 𝗥𝗘𝗔𝗗𝗬 • 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 💥\n"
    "🎯 𝗖𝗵𝗲𝗰𝗸𝗲𝗿 + 𝗣𝗿𝗼𝘁𝗲𝗰𝘁𝗼𝗿 𝗼𝗻𝗹𝗶𝗻𝗲 😈\n\n"
    "🧾 /input → Instant check\n"
    "🍪 /cookies → Upload cook.txt\n"
    "💾 /store → Save coupons\n"
    "🛡️ /protect → Auto check 10 min\n"
    "📂 /mystored → See stored\n"
    "🛑 /stop → Stop everything"
)

# =========================
# GLOBALS
# =========================
bot: telebot.TeleBot = None
cookies_header: str = None
OWNER_CHAT_ID: int = None

USER_LOCKS = defaultdict(Lock)
USER_STOP_EVENTS = defaultdict(Event)
PROTECTION_TIMERS = {}
RAW_CODE_RE = re.compile(r"\b(SV[A-Z0-9.]+)\b", re.IGNORECASE)

# =========================
# UTILS & STORAGE
# =========================

def load_cookies():
    global cookies_header
    if not os.path.exists(COOKIES_FILE):
        cookies_header = None
        return False
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        cookies_header = f.read().strip() or None
    return cookies_header is not None

def build_headers():
    return {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "X-TENANT-ID": "SHEIN",
        "content-type": "application/json",
        "Cookie": cookies_header or "",
    }

def ensure_stored_dir(chat_id):
    path = os.path.join(BASE_STORED_DIR, str(chat_id))
    os.makedirs(path, exist_ok=True)
    return path

def get_user_stored_coupons(chat_id):
    path = os.path.join(ensure_stored_dir(chat_id), "coupons.json")
    if not os.path.exists(path): return []
    try:
        with open(path, "r") as f: return json.load(f).get("codes", [])
    except: return []

def save_user_stored_coupons(chat_id, codes):
    old = get_user_stored_coupons(chat_id)
    merged = list(dict.fromkeys(old + codes))
    path = os.path.join(ensure_stored_dir(chat_id), "coupons.json")
    with open(path, "w") as f:
        json.dump({"codes": merged, "count": len(merged)}, f)
    return merged

def safe_send_message(chat_id, text):
    if not text.endswith(COMMON_FOOTER): text += COMMON_FOOTER
    try: return bot.send_message(chat_id, text)
    except: return None

def extract_codes(text):
    found = RAW_CODE_RE.findall(text.upper())
    return list(dict.fromkeys([c.replace(".", "") for c in found]))

# =========================
# CORE LOGIC
# =========================

def check_coupon(session, voucher_id):
    headers = build_headers()
    payload = {"voucherId": voucher_id, "device": {"client_type": "web"}}
    try:
        r = session.post(URL, headers=headers, json=payload, timeout=7)
        body = r.text.lower()
        ok = any(k in body for k in ("save", "discount", "success"))
        return ok, f"HTTP {r.status_code}", r.text[:500]
    except Exception as e:
        return False, str(e), ""

def process_coupons_and_reply(chat_id, codes, announce_protection=True):
    if not codes:
        safe_send_message(chat_id, "❌ No SV codes found.")
        return
    
    stop_event = USER_STOP_EVENTS[chat_id]
    total = len(codes)
    safe_send_message(chat_id, f"🚀 Starting check for {total} codes...")

    with USER_LOCKS[chat_id]:
        with requests.Session() as session:
            for idx, code in enumerate(codes, start=1):
                if stop_event.is_set(): return
                
                ok, info, body = check_coupon(session, code)
                status_icon = "✅" if ok else "❌"
                
                if (idx % 10 == 0) or (idx == total):
                    safe_send_message(chat_id, f"[{idx}/{total}] {status_icon} Code: {code}\nResult: {'SUCCESS' if ok else 'FAILED'}")
                time.sleep(0.3)

    if announce_protection:
        safe_send_message(chat_id, IMPORTANT_PROTECTION_TEXT)

# =========================
# HANDLERS
# =========================

def register_handlers():
    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        if message.chat.id != OWNER_CHAT_ID: return
        safe_send_message(message.chat.id, STARTUP_BROADCAST_TEXT)

    @bot.message_handler(commands=["cookies"])
    def cmd_cookies(message):
        if message.chat.id != OWNER_CHAT_ID: return
        msg = bot.send_message(message.chat.id, "📤 Upload `cook.txt` now.")
        bot.register_next_step_handler(msg, handle_cookie_upload)

    def handle_cookie_upload(message):
        if message.content_type == 'document':
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            with open(COOKIES_FILE, "wb") as f: f.write(downloaded)
            load_cookies()
            bot.send_message(message.chat.id, "✅ Cookies Updated!")
        else: bot.send_message(message.chat.id, "❌ Upload a file.")

    @bot.message_handler(commands=["input"])
    def cmd_input(message):
        if message.chat.id != OWNER_CHAT_ID: return
        if not cookies_header: return safe_send_message(message.chat.id, "⚠️ Load cookies first!")
        USER_STOP_EVENTS[message.chat.id].clear()
        msg = bot.send_message(message.chat.id, "📥 Send SV codes or file.")
        bot.register_next_step_handler(msg, lambda m: process_coupons_and_reply(m.chat.id, extract_codes(m.text or "")))

    @bot.message_handler(commands=["store"])
    def cmd_store(message):
        if message.chat.id != OWNER_CHAT_ID: return
        msg = bot.send_message(message.chat.id, "💾 Send codes to STORE.")
        bot.register_next_step_handler(msg, handle_store)

    def handle_store(message):
        codes = extract_codes(message.text or "")
        merged = save_user_stored_coupons(message.chat.id, codes)
        safe_send_message(message.chat.id, f"💾 Stored! Total: {len(merged)}")

    @bot.message_handler(commands=["protect"])
    def cmd_protect(message):
        if message.chat.id != OWNER_CHAT_ID: return
        chat_id = message.chat.id
        USER_STOP_EVENTS[chat_id].clear()
        
        def loop():
            if USER_STOP_EVENTS[chat_id].is_set(): return
            codes = get_user_stored_coupons(chat_id)
            if codes: process_coupons_and_reply(chat_id, codes, False)
            PROTECTION_TIMERS[chat_id] = Timer(600, loop)
            PROTECTION_TIMERS[chat_id].start()
        
        loop()
        safe_send_message(chat_id, "🛡️ Protection Started (Every 10 mins).")

    @bot.message_handler(commands=["stop"])
    def cmd_stop(message):
        chat_id = message.chat.id
        USER_STOP_EVENTS[chat_id].set()
        if chat_id in PROTECTION_TIMERS: PROTECTION_TIMERS[chat_id].cancel()
        bot.send_message(chat_id, "🛑 All processes stopped.")

# =========================
# START
# =========================
if __name__ == "__main__":
    os.makedirs(BASE_RESULTS_DIR, exist_ok=True)
    os.makedirs(BASE_STORED_DIR, exist_ok=True)

    # Use defaults if environment variables aren't set
    token = os.environ.get("BOT_TOKEN", DEFAULT_TOKEN)
    owner_id = int(os.environ.get("OWNER_ID", DEFAULT_OWNER_ID))
    
    OWNER_CHAT_ID = owner_id
    bot = telebot.TeleBot(token)
    
    register_handlers()
    load_cookies()
    
    print(f"Running bot for {OWNER_CHAT_ID}...")
    bot.infinity_polling()
