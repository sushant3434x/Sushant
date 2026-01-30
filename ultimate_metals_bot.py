import os
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

from ta.momentum import RSIIndicator
from sklearn.linear_model import LinearRegression
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# -------- ENV VARIABLES --------
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# -------- YOUR PORTFOLIO --------
portfolio = {
    "GOLDBEES.NS": 137,
    "SILVERBEES.NS": 297
}

assets = {
    "Gold ETF": "GOLDBEES.NS",
    "Silver ETF": "SILVERBEES.NS",
    "Gold Intl": "GC=F",
    "Silver Intl": "SI=F"
}

# -------- AI PREDICTION --------
def ai_prediction(symbol):
    df = yf.download(symbol, period="3mo", progress=False)
    y = df['Close'].values
    X = np.arange(len(y)).reshape(-1,1)

    model = LinearRegression().fit(X,y)
    future = model.predict([[len(y)+5]])[0]
    current = y[-1]

    change = (future-current)/current*100

    if change > 2:
        return "🔮 AI: Bullish bias"
    elif change < -2:
        return "🔮 AI: Bearish bias"
    else:
        return "🔮 AI: Sideways"

# -------- SIGNAL ENGINE --------
def ultra_signal(symbol):

    df = yf.download(symbol, period="2mo", progress=False)
    close = df['Close']

    rsi = RSIIndicator(close).rsi().iloc[-1]
    change5 = (close.iloc[-1]-close.iloc[-5])/close.iloc[-5]*100

    score = 0
    reasons = []

    if rsi < 35:
        score += 2; reasons.append("RSI oversold")

    if change5 < -4:
        score += 2; reasons.append("Recent dip")

    if rsi > 70:
        score -= 2; reasons.append("Overbought")

    if change5 > 6:
        score -= 2; reasons.append("Sharp rally")

    if score >= 3:
        action="✅ BUY"
    elif score <= -2:
        action="⚠️ WAIT"
    else:
        action="🟡 HOLD"

    conf = min(abs(score)*20,95)

    msg=f"{action} | Confidence {conf}%\n"
    msg+="Reason:\n• "+"\n• ".join(reasons)

    return msg

# -------- PORTFOLIO TRACKER --------
def portfolio_tracker(symbol):

    if symbol not in portfolio:
        return ""

    df=yf.download(symbol,period="5d",progress=False)
    current=df['Close'].iloc[-1]
    avg=portfolio[symbol]

    pnl=(current-avg)/avg*100

    msg=f"\n📊 Your P/L: {round(pnl,1)}%\n"

    if pnl<-10:
        msg+="💡 Avg down zone"
    elif pnl>15:
        msg+="💡 Partial profit zone"
    else:
        msg+="💡 Hold"

    return msg

# -------- FULL ANALYSIS --------
def full_analysis(symbol):

    return (
        ultra_signal(symbol)+"\n"+
        ai_prediction(symbol)+"\n"+
        portfolio_tracker(symbol)
    )

# -------- CHART --------
def chart(symbol):
    df=yf.download(symbol,period="3mo",progress=False)

    plt.figure()
    plt.plot(df['Close'])
    plt.title(symbol)

    file="chart.png"
    plt.savefig(file)
    plt.close()

    return file

# -------- START MENU --------
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    kb=[
        [InlineKeyboardButton("🧠 Full Analysis",callback_data="analysis")],
        [InlineKeyboardButton("📊 Chart",callback_data="chart")]
    ]

    await update.message.reply_text(
        "📌 Metals Assistant Bot",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# -------- BUTTONS --------
async def buttons(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    if q.data=="analysis":
        msg="🧠 Market Analysis\n\n"
        for n,s in assets.items():
            msg+=f"{n}:\n{full_analysis(s)}\n\n"
        await q.message.reply_text(msg)

    if q.data=="chart":
        file=chart("GOLDBEES.NS")
        await q.message.reply_photo(photo=open(file,"rb"))

# -------- DAILY REPORT --------
def daily(app):
    msg="📊 Daily Update\n\n"
    for n,s in assets.items():
        msg+=f"{n}:\n{ultra_signal(s)}\n\n"
    app.bot.send_message(chat_id=CHAT_ID,text=msg)

# -------- RUN --------
app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(buttons))

scheduler=BackgroundScheduler()
scheduler.add_job(lambda:daily(app),"cron",hour=9)
scheduler.start()

print("Bot running...")
app.run_polling()


