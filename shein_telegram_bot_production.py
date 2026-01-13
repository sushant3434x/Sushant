import os
import json
import asyncio
import aiohttp
from aiohttp import web

BOT_TOKEN = "8501641376:AAGUZPD44R-zXd6dClu0SA-O9u0bX4cRnKo"
CHAT_ID = 7032063067
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
STATE_FILE = "state.json"

# ---------------- STATE ----------------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"gender": None, "sizes": [], "pincode": None, "paused": False}

state = load_state()
gender = state["gender"]
sizes = set(state["sizes"])
pincode = state["pincode"]
paused = state["paused"]

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
            json={"chat_id": CHAT_ID, "text": text}
        )

# ---------------- HANDLER ----------------
async def handle_update(update):
    global gender, sizes, pincode, paused

    msg = update.get("message")
    if not msg or msg["chat"]["id"] != CHAT_ID:
        return

    text = msg.get("text", "")

    if text == "/status":
        await tg_send(
            f"Gender: {gender}\nSizes: {', '.join(sizes)}\nPincode: {pincode}\nPaused: {paused}"
        )
        return

    if text.startswith("/setgender"):
        gender = text.split()[-1]
        save_state()
        await tg_send(f"Gender set: {gender}")

    if text.startswith("/setsize"):
        sizes.clear()
        for s in text.split()[-1].split(","):
            sizes.add(s.strip().upper())
        save_state()
        await tg_send(f"Sizes set: {', '.join(sizes)}")

    if text.startswith("/setpincode"):
        pincode = text.split()[-1]
        save_state()
        await tg_send(f"Pincode set: {pincode}")

# ---------------- WEB APP ----------------
app = web.Application()

async def root(request):
    return web.Response(text="OK")

async def webhook(request):
    update = await request.json()
    await handle_update(update)
    return web.Response(text="OK")

app.router.add_get("/", root)
app.router.add_post("/webhook", webhook)

# ---------------- RUN ----------------
port = int(os.environ.get("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)
