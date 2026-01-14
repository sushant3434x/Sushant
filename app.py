import os
import json
import time
import asyncio
import aiohttp
from aiohttp import web

# ================= CONFIG =================
BOT_TOKEN = "8501641376:AAGUZPD44R-zXd6dClu0SA-O9u0bX4cRnKo"
OWNER_ID = 7032063067
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
STATE_FILE = "state.json"

# ================= STATE =================
DEFAULT_STATE = {
    "gender": None,      # male / female / both
    "sizes": [],
    "pincode": None,
    "awaiting": None,
    "last_check": 0
}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)
else:
    state = DEFAULT_STATE.copy()

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ================= TELEGRAM =================
async def tg_send(chat_id, text):
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )

# ================= MOCK PRODUCT SOURCE =================
# Replace this later with real SHEIN scraping
def fetch_products():
    return [
        {
            "title": "Oversized Hoodie",
            "price": "₹1,899",
            "gender": "male",
            "sizes": ["M", "L", "XL"],
            "link": "https://shein.in/product/hoodie123",
            "pincode_ok": True
        },
        {
            "title": "Crop Top",
            "price": "₹799",
            "gender": "female",
            "sizes": ["S", "M"],
            "link": "https://shein.in/product/top456",
            "pincode_ok": True
        }
    ]

# ================= FILTER MATCH =================
def product_matches(p):
    if state["gender"] and state["gender"] != "both":
        if p["gender"] != state["gender"]:
            return False

    if state["sizes"]:
        if not any(s in p["sizes"] for s in state["sizes"]):
            return False

    if state["pincode"] and not p["pincode_ok"]:
        return False

    return True

# ================= BACKGROUND CHECK =================
async def monitor_loop():
    while True:
        await asyncio.sleep(600)  # 10 minutes
        if not state["gender"] or not state["sizes"] or not state["pincode"]:
            continue

        products = fetch_products()
        for p in products:
            if product_matches(p):
                msg = (
                    "🔥 SHEINVERSE MATCH FOUND\n\n"
                    f"👕 {p['title']}\n"
                    f"💰 Price: {p['price']}\n"
                    f"📏 Sizes: {', '.join(p['sizes'])}\n"
                    f"📍 Pincode: {state['pincode']}\n\n"
                    f"🔗 {p['link']}"
                )
                await tg_send(OWNER_ID, msg)

# ================= WEBHOOK =================
async def webhook(request):
    data = await request.json()
    msg = data.get("message")
    if not msg:
        return web.Response(text="ok")

    chat_id = msg["chat"]["id"]

    # PRIVATE BOT LOCK
    if chat_id != OWNER_ID:
        return web.Response(text="ok")

    text = msg.get("text", "").strip().lower()

    # ANTI-SPAM
    now = time.time()
    if now - state.get("last_check", 0) < 0.5:
        return web.Response(text="ok")
    state["last_check"] = now
    save_state()

    # COMMANDS
    if text == "/start":
        await tg_send(
            chat_id,
            "✅ Private SHEINVERSE Bot Running\n\n"
            "Commands:\n"
            "/setgender\n"
            "/setsize\n"
            "/setpincode\n"
            "/status"
        )

    elif text == "/status":
        await tg_send(
            chat_id,
            f"📊 STATUS\n"
            f"Gender: {state['gender']}\n"
            f"Sizes: {', '.join(state['sizes'])}\n"
            f"Pincode: {state['pincode']}"
        )

    elif text == "/setgender":
        state["awaiting"] = "gender"
        save_state()
        await tg_send(chat_id, "Send gender: male / female / both")

    elif text == "/setsize":
        state["awaiting"] = "size"
        save_state()
        await tg_send(chat_id, "Send sizes like: M,L,XL")

    elif text == "/setpincode":
        state["awaiting"] = "pincode"
        save_state()
        await tg_send(chat_id, "Send pincode")

    elif state["awaiting"] == "gender":
        if text in ("male", "female", "both"):
            state["gender"] = text
            state["awaiting"] = None
            save_state()
            await tg_send(chat_id, f"✅ Gender set: {text}")
        else:
            await tg_send(chat_id, "❌ Use male / female / both")

    elif state["awaiting"] == "size":
        state["sizes"] = [s.strip().upper() for s in text.split(",") if s.strip()]
        state["awaiting"] = None
        save_state()
        await tg_send(chat_id, f"✅ Sizes set: {', '.join(state['sizes'])}")

    elif state["awaiting"] == "pincode":
        if text.isdigit():
            state["pincode"] = text
            state["awaiting"] = None
            save_state()
            await tg_send(chat_id, f"✅ Pincode set: {text}")
        else:
            await tg_send(chat_id, "❌ Pincode must be numbers")

    else:
        await tg_send(chat_id, "❓ Unknown command")

    return web.Response(text="ok")

# ================= APP =================
app = web.Application()
app.router.add_get("/", lambda r: web.Response(text="OK"))
app.router.add_post("/webhook", webhook)

async def start_bg(app):
    app["monitor"] = asyncio.create_task(monitor_loop())

app.on_startup.append(start_bg)

port = int(os.environ.get("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)
