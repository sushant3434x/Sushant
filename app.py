import os
import json
import aiohttp
from aiohttp import web

BOT_TOKEN = "8501641376:AAGUZPD44R-zXd6dClu0SA-O9u0bX4cRnKo"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
STATE_FILE = "state.json"

# ---------------- STATE ----------------
DEFAULT_STATE = {
    "gender": None,
    "sizes": [],
    "pincode": None
}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)
else:
    state = DEFAULT_STATE.copy()

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ---------------- TELEGRAM SEND ----------------
async def tg_send(chat_id, text):
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )

# ---------------- WEBHOOK ----------------
async def webhook(request):
    data = await request.json()

    msg = data.get("message")
    if not msg:
        return web.Response(text="ok")

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    # ---------- COMMANDS ----------
    if text == "/start":
        await tg_send(
            chat_id,
            "✅ Bot is running\n\n"
            "Commands:\n"
            "/setgender male|female|both\n"
            "/setsize M,L,XL\n"
            "/setpincode 110001\n"
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

    elif text.startswith("/setgender"):
        g = text.split()[-1].lower()
        if g in ("male", "female", "both"):
            state["gender"] = g
            save_state()
            await tg_send(chat_id, f"✅ Gender set: {g}")
        else:
            await tg_send(chat_id, "❌ Use: /setgender male|female|both")

    elif text.startswith("/setsize"):
        sizes = text.split(maxsplit=1)[-1]
        state["sizes"] = [s.strip().upper() for s in sizes.split(",") if s.strip()]
        save_state()
        await tg_send(chat_id, f"✅ Sizes set: {', '.join(state['sizes'])}")

    elif text.startswith("/setpincode"):
        p = text.split()[-1]
        if p.isdigit():
            state["pincode"] = p
            save_state()
            await tg_send(chat_id, f"✅ Pincode set: {p}")
        else:
            await tg_send(chat_id, "❌ Pincode must be numbers only")

    else:
        await tg_send(chat_id, "❓ Unknown command")

    return web.Response(text="ok")

# ---------------- ROOT ----------------
async def root(request):
    return web.Response(text="OK")

# ---------------- APP ----------------
app = web.Application()
app.router.add_get("/", root)
app.router.add_post("/webhook", webhook)

# ---------------- RUN ----------------
port = int(os.environ.get("PORT", 8080))
web.run_app(app, host="0.0.0.0", port=port)

