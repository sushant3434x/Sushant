from flask import Flask, render_template
import yfinance as yf
import plotly.graph_objs as go

app = Flask(__name__)

ASSETS = {
    "Gold ETF": "GOLDBEES.NS",
    "Silver ETF": "SILVERBEES.NS"
}

PORTFOLIO = {
    "GOLDBEES.NS": 137,
    "SILVERBEES.NS": 297
}

def get_price(symbol):
    df = yf.download(symbol, period="1d", progress=False)
    return round(df['Close'].iloc[-1], 2)

@app.route("/")
def home():
    data = []

    for name, sym in ASSETS.items():
        price = get_price(sym)
        avg = PORTFOLIO.get(sym, None)
        pnl = round((price - avg) / avg * 100, 2) if avg else None

        data.append({
            "name": name,
            "price": price,
            "avg": avg,
            "pnl": pnl
        })

    return render_template("index.html", data=data)

@app.route("/chart/<symbol>")
def chart(symbol):
    df = yf.download(symbol, period="6mo", progress=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Price"))

    return fig.to_html(full_html=False)

if __name__ == "__main__":
    app.run()

