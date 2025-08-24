import datetime
import json
from typing import List

import plotly
import plotly.graph_objs as go
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

MOEX_CANDLES_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/candles.json"


def fetch_candles(ticker: str, days: int = 60) -> str:
    """Fetch candle data for a ticker and return a Plotly figure JSON string."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    params = {"from": start, "till": end, "interval": 24}
    response = requests.get(MOEX_CANDLES_URL.format(ticker=ticker), params=params)
    response.raise_for_status()
    candles = response.json()["candles"]
    columns = candles["columns"]
    data = candles["data"]
    if not data:
        raise ValueError(f"No data for ticker {ticker}")
    idx_date = columns.index("begin")
    idx_close = columns.index("close")
    dates = [row[idx_date][:10] for row in data]
    closes = [row[idx_close] for row in data]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=closes, mode="lines", name=ticker))
    fig.update_layout(title=ticker, xaxis_title="Date", yaxis_title="Price")
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


@app.route("/", methods=["GET", "POST"])
def index():
    graphs: List[str] = []
    tickers_input = ""
    if request.method == "POST":
        tickers_input = request.form.get("tickers", "")
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        for ticker in tickers:
            try:
                graphs.append(fetch_candles(ticker))
            except Exception:
                # Skip tickers with errors
                continue
    return render_template("index.html", graphs=graphs, tickers=tickers_input)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
