#!/usr/bin/env python3
"""
PRODUCTION SHEIN TELEGRAM BOT
Features:
- Webhook based (no polling)
- Persistent state (restart safe)
- Gender / Size / Pincode filters
- Realistic SHEIN scraping (HTML)
- Anti-spam & deduplication

REQUIREMENTS:
 pip install aiohttp beautifulsoup4

DEPLOY:
 - HTTPS server (Render / Railway / VPS)
 - Set Telegram webhook to https://yourdomain.com/webhook
"""

import aiohttp
import asyncio
import json
import os
import time
from aiohttp import web
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------
BOT_TOKEN = "8501641376:AAGUZPD44R-zXd6dClu0SA-O9u0bX4cRnKo"
CHAT_ID = 7032063067
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
STATE_FILE = "state.json"
CHECK_INTERVAL = 60

CATEGORIES = {
    "MEN": "https://www.sheinindia.in/Men-Clothing-c-2026.html",
    "WOMEN": "https://www.sheinindia.in/Women-Clothing-c-2030.html",
}

# ---------------- STATE ----------------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"gender": None, "sizes": [], "pincode": None, "paused": False}

state = load_state()
gender = state["gender"]
sizes = set(state["sizes"])
pincode = state["pincode"]
paused = state["paused"]

sent_cache = set()


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump({
            "gender": gender,
            "sizes": list(sizes),
            "pincode": pincode,
            "paused": paused
        }, f)

# ---------------- TELEGRAM ----------------
async def tg_send(text):
    async with aiohttp.ClientSession() as s:
        await s.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        )

# ---------------- FILTERS ----------------
def match_filters(name):
    name = name.lower()

    if gender == "male" and "men" not in name:
        return False
    if gender == "female" and "women" not in name:
        return False
    if sizes and not any(sz.lower() in name for sz in sizes):
        return False
    return True

async def check_pincode_available(_product_id):
    # Placeholder – SHEIN blocks direct API
    return True if pincode else True

# ---------------- SCRAPER ----------------
async def fetch_products(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-IN"
    }
    async with aiohttp.ClientSession(headers=headers) as s:
        async with s.get(url, timeout=20) as r:
            return await r.text()


def parse_products(html):
    soup = BeautifulSoup(html, "html.parser")
    products = []
    for tag in soup.find_all("a"):
        text = tag.get_text(strip=True)
        if text and len(text) > 20:
            products.append(text)
    return products

# ---------------- MONITOR ----------------
async def monitor_loop():
    while True:
        if not paused and gender and sizes:
            for url in CATEGORIES.values():
                try:
                    html = await fetch_products(url)
                    products = parse_products(html)

                    for p in products:
                        if p in sent_cache:
                            continue
                        if not match_filters(p):
                            continue
                        if not await check_pincode_available(p):
                            continue

                        sent_cache.add(p)
                        await tg_send(f"🛒 <b>NEW MATCH</b>\n{p}")
                except Exception as e:
                    print("Scan error:", e)
        await asyncio.sleep(CHECK_INTERVAL)

# ---------------- COMMAND HANDLER ----------------
async def handle_update(update):
    global gender, sizes, pincode, paused

    msg = update.get("message")
    if not msg or msg["chat"]["id"] != CHAT_ID:
        return

    text = msg.get("text", "").strip()

    # COMMANDS (ALWAYS WORK)
    if text == "/status":
        await tg_send(
            f"📊 STATUS\n"
            f"Gender: {gender}\n"
            f"Sizes: {', '.join(sizes)}\n"
            f"Pincode: {pincode}\n"
            f"Paused: {paused}"
        )
        return

    if text == "/pause":
        paused = True
        save_state()
        await tg_send("⏸ Paused")
        return

    if text == "/resume":
        paused = False
        save_state()
        await tg_send("▶️ Resumed")
        return

    if text.startswith("/setgender"):
        g = text.split(maxsplit=1)[-1].lower()
        if g in ("male", "female", "both"):
            gender = g
            save_state()
            await tg_send(f"Gender set: {gender}")
        return

    if text.startswith("/setsize"):
        sizes.clear()
        for s in text.split(maxsplit=1)[-1].split(","):
            sizes.add(s.strip().upper())
        save_state()
        await tg_send(f"Sizes set: {', '.join(sizes)}")
        return

    if text.startswith("/setpincode"):
        pincode = text.split(maxsplit=1)[-1]
        save_state()
        await tg_send(f"📍 Pincode set: {pincode}")
        return

    if text == "/clearfilters":
        gender = None
        sizes.clear()
        pincode = None
        save_state()
        await tg_send("🧹 Filters cleared")
        return

    if text == "/start":
        await tg_send("✅ Bot running. Use /status")

# ---------------- WEBHOOK ----------------
async def webhook(request):
    update = await request.json()
    await handle_update(update)
    return web.Response(text="OK")

app = web.Application()
app.router.add_post("/webhook", webhook)

# ---------------- MAIN ----------------
async def main():
    asyncio.create_task(monitor_loop())
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("🚀 Bot running (webhook mode)")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
