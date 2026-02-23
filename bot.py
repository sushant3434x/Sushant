#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shein India Coupon Checker + Protector
SAFE • FAST • PER-USER
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
# CREDENTIALS (REPLACE THESE)
# =========================
DEFAULT_TOKEN = "8387153384:AAHXQc9Rf9i7aIzZAPusdNTeCLtGIJi_Obs"
DEFAULT_OWNER_ID = 7835819531

# Your specific cookie string
HARDCODED_COOKIES = (
    "_abck=74BB7A4ED4BD7D7F579B11BD8D523EF0~-1~YAAQBncsMSinSmqcAQAAsxP+iQ9E0Ct684plRV8u+LIhoak1nnSuqqbtLCKQulDsQKCSDytm9MOHNkCmp8bCrw3ppEK+EmlBPz5/MCMhII4Kp3bHSDW3BN+8nZlnn+3R96GYCrORqImZybqu649I8VBTG5I381NOZR+xGSnMolvKeBqi7eXCMqrTxEhzdYd/pVsJQtdT2ggyg+Rq+CT2EGOMWHavJFLlC7lhFRPhzgldfAlrLO1Vk7Vmaj8e8VNupUJkrN5Sw2zkDw/e4vwZhcttroG2cojboahzlTgobwVJT0eAUsVdYj4t6KxVPR4sRyW4lcguYRkGAYDti6XvhdMpSWY8mPQX0YaVInDK1xSzOk927ZwOKAfZdXSMgFSYgmZSBSq1LKHUollY3dfHl/C89kTbLsnJqWakc1If5Chn83nCV5w9MDfaNbVvycwN9dXSkltdCz6yB9i0VD9VLFBGB1FlkepBpUZveX0wyKS0tmGWIcHrrEiqQJy4SjDTF9jI8Gd14swV0GifJstdekOGTA+++06OnPQCRNSkPQAfqAEswuBxMcpuzqlMuYobLpoyV+vV4GApCqnakagcGnpuh5Vr7Rtg+2Pjo61JisrbgF2Ig2ViDGmhwsqZ/K67VhONoVhHA/2Rkvf5GlCertFI8aM6KWppp8rywvMd6w0oPag1/LL1TeunvB0sRYYEk8D7kLzcoho/346gndNdbg+dHe+mlDfyv0NFgDVtYcWLEaAV0akS4ZaKUQlOq+AsgrK2VG+hGBhXedhH9ho8GhTqeRn6aBy79qIeCW8yxLEJg+fMBUvxwh0V1ACjUKreHmLMqYp2MH1ybAW60CQBTCuxUVj3~-1~-1~1771845223~AAQAAAAF%2f%2f%2f%2f%2f3OnhtaKvND37OdFVOfgqZzm%2fS3Y6Y1YJUudN0QsBFaFfsluNA7xeb4tXR1IxHdb6crkGo7IflVFVXW8y07pffQguYfYScqa4D5y~-1; "
    "bookingType=SHEIN; GUID=3c0cb479-6976-4646-9c77-cccfbdff863c; SN=richa; C=SH9745705243; "
    "ak_bmsc=4BA96FF3058040A272ABEBA63F9A3590~000000000000000000000000000000~YAAQFncsMcysn2mcAQAAsqD9iR7xEu+A/FOQ2YcExz/SwkXGXqivashOL3IZFD4hNVIDamkoE6XNSjRWMsBtXr+adU/HzlJjhLH/iYtuqcdmSnlclL3kaN0rJtwHnKLugqW8Fxh+zQYRN1RWN1Bk/5IzmOG/fte5jHD3qXkYkzvEHvQCsugJ0U5UnJVmn2Ere9N8CZ86FWz8oHuJrxse9TJKq4I+83TzIZGVUGWWjAJj/rtPbCKdkGEM2rDY9SburOLyvh8dMoTmoFgGa79bbec5FwMqkjLntdSQ+1zkjkjKMGIezSVkvfdAN5xg+QPPoN9j5SCUArlEo9DlZrtCo/fVtGw9Hk2F6mte1A1gWur1AHqzBg7mV2aYjT6kP71oPpNuymQc77b5FR0xMOBvB5blCm4SejL1ZADWxCBiWgrcRv4E7kkgJaJ3OSlzDVzt8u6hwpZ8lhEfjosMMYWn7KvWEnKAQCvfEd3y0hHq4W64IQ3xyrmPYBv2Q+DspjAF8+u16kM1SgqHewCYyU7xmo7A; "
    "R=eyJhbGciOiJSUzI1NiJ9.eyJzZXNzaW9uIjp7InNlc3Npb25JZCI6IjMwY2U1ZTJhLTFjYjgtNDFjNS04MmMxLTM1MWM3ODgzNmE1NSIsImNsaWVudE5hbWUiOiJ3ZWJfY2xpZW50Iiwicm9sZXMiOlt7Im5hbWUiOiJST0xFX0NVU1RPTUVSR1JPVVAifV19LCJ0eXBlIjoicmVmcmVzaCIsInRlbmFudElkIjoiU0hFSU4iLCJzdWIiOiJzaGVpbl9yaWNoYXNoIiwiaWF0IjoxNzcxODQxNjQ3fQ; "
    "A=eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzaGVpbl9yaWNoYXNoIiwicm9sZXMiOlt7Im5hbWUiOiJST0xFX0NVU1RPTUVSR1JPVVAifV0sIm1vYmlsZSI6IjYzOTgzMTYxMjAiLCJ0ZW5hbnRJZCI6IlNIRUlOIiwiZXhwIjoxNzc0NDMzNjQ3LCJ1dWlkIjoiZTRiNTBkYTUtNWFkMS00YzVlLTgzNDUtNDQwMDYyNmU2NTQ1IiwiaWF0IjoxNzcxODQxNjQ3fQ; "
    "uI=6398316120; LS=LOGGED_IN; deviceId=QX9cnHlTpFqv8w306m5pA"
)

# =========================
# CONFIG
# =========================
COOKIES_FILE = "cook.txt"
URL = "https://www.sheinindia.in/api/cart/apply-voucher"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"

BASE_RESULTS_DIR = "results"
BASE_STORED_DIR = "stored_coupons"
MAX_CODES = 5000

COMMON_FOOTER = "\n\n🛑 𝗨𝘀𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 /stop 𝘁𝗼 𝘀𝘁𝗼𝗽 𝘁𝗵𝗲 𝗯𝗼𝘁"
IMPORTANT_PROTECTION_TEXT = "⚠️ 𝗜𝗠𝗣𝗢𝗥𝗧𝗔𝗡𝗧:\n𝗬𝗢𝗨𝗥 𝗖𝗢𝗨𝗣𝗢𝗡𝗦 𝗔𝗥𝗘 𝗡𝗢𝗪 𝗖𝗛𝗘𝗖𝗞𝗘𝗗 𝗔𝗡𝗗 𝗔𝗥𝗘 𝗜𝗡 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡.\n𝗨𝗦𝗘 /stop 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗧𝗢 𝗦𝗧𝗢𝗣 𝗕𝗢𝗧."

STARTUP_BROADCAST_TEXT = (
    "✅ 𝗕𝗢𝗧 𝗥𝗘𝗔𝗗𝗬 • 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 💥\n"
    "🎯 𝗖𝗵𝗲𝗰𝗸𝗲𝗿 + 𝗣𝗿𝗼𝘁𝗲𝗰𝘁𝗼𝗿 𝗼𝗻𝗹𝗶𝗻𝗲 😈\n\n"
    "🧾 /input → Instant check\n"
    "💾 /store → Save coupons\n"
    "🛡️ /protect → Auto check 10 min\n"
    "📂 /mystored → See stored\n"
    "🗑️ /clearstored → Clear stored\n"
    "🛑 /stop → Stop everything" + COMMON_FOOTER
)

# =========================
# GLOBALS
# =========================
bot = None
cookies_header = HARDCODED_COOKIES
OWNER_CHAT_ID = DEFAULT_OWNER_ID

USER_LOCKS = defaultdict(Lock)
USER_STOP_EVENTS = defaultdict(Event)
PROTECTION_TIMERS = {}
RAW_CODE_RE = re.compile(r"\b(SV[A-Z0-9.]+)\b", re.IGNORECASE)

# =========================
# FUNCTIONS
# =========================

def load_cookies() -> bool:
    global cookies_header
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                cookies_header = raw
                return True
    cookies_header = HARDCODED_COOKIES
    return True

def build_headers() -> dict:
    return {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "X-TENANT-ID": "SHEIN",
        "content-type": "application/json",
        "Cookie": cookies_header,
    }

def safe_send_message(chat_id, text, retries=3):
    if not text.endswith(COMMON_FOOTER):
        text = text + COMMON_FOOTER
    for attempt in range(1, retries + 1):
        try:
            return bot.send_message(chat_id, text)
        except Exception:
            time.sleep(1)
    return None

# [Include all other original logic functions like check_coupon, extract_codes, process_coupons_and_reply, etc. exactly as in your source]

# (Original logic continues below...)

def check_coupon(session, voucher_id):
    headers = build_headers()
    payload = {"voucherId": voucher_id, "device": {"client_type": "web"}}
    try:
        r = session.post(URL, headers=headers, json=payload, timeout=5)
        body = r.text.lower()
        ok = any(k in body for k in ("save", "discount", "success"))
        return ok, f"http_{r.status_code}", r.text[:200]
    except Exception as e:
        return False, "error", str(e)

def extract_codes(text):
    found = RAW_CODE_RE.findall(text.upper())
    return list(dict.fromkeys(found))

def process_coupons_and_reply(chat_id, codes, announce_protection=True):
    if not codes:
        safe_send_message(chat_id, "No SV codes found.")
        return
    
    with requests.Session() as session:
        for idx, code in enumerate(codes, 1):
            if USER_STOP_EVENTS[chat_id].is_set(): break
            ok, info, body = check_coupon(session, code)
            icon = "✅" if ok else "❌"
            safe_send_message(chat_id, f"[{idx}/{len(codes)}] {icon} {code}: {info}")
            time.sleep(0.3)

# =========================
# MAIN HANDLER REGISTRATION
# =========================

def register_handlers():
    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        if message.chat.id == OWNER_CHAT_ID:
            safe_send_message(message.chat.id, STARTUP_BROADCAST_TEXT)

    @bot.message_handler(commands=["input"])
    def cmd_input(message):
        if message.chat.id != OWNER_CHAT_ID: return
        msg = safe_send_message(message.chat.id, "📥 Send SV codes or file.")
        bot.register_next_step_handler(msg, handle_input)

    def handle_input(message):
        text = message.text or ""
        if message.content_type == 'document':
            file_info = bot.get_file(message.document.file_id)
            text = bot.download_file(file_info.file_path).decode('utf-8')
        codes = extract_codes(text)
        process_coupons_and_reply(message.chat.id, codes)

    @bot.message_handler(commands=["stop"])
    def cmd_stop(message):
        USER_STOP_EVENTS[message.chat.id].set()
        safe_send_message(message.chat.id, "🛑 Stopped.")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    os.makedirs(BASE_RESULTS_DIR, exist_ok=True)
    os.makedirs(BASE_STORED_DIR, exist_ok=True)
    
    bot = telebot.TeleBot(DEFAULT_TOKEN)
    load_cookies()
    register_handlers()
    
    print(f"Bot starting for Owner: {OWNER_CHAT_ID}")
    try:
        safe_send_message(OWNER_CHAT_ID, "✅ Bot Online (Running on GitHub/Server)")
    except: pass
    
    bot.infinity_polling()
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

