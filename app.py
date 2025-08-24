import datetime
import json
<<<<<<< HEAD
from typing import List
=======
from typing import List, Sequence, Tuple
>>>>>>> origin/codex/-api-5dhsxm

import plotly
import plotly.graph_objs as go
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

<<<<<<< HEAD
MOEX_CANDLES_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/candles.json"


def fetch_candles(ticker: str, days: int = 60) -> str:
    """Fetch candle data for a ticker and return a Plotly figure JSON string."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
=======
MOEX_CANDLES_URL = (
    "https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/candles.json"
)


def _elliott_waves(dates: Sequence[str], prices: Sequence[float]) -> List[Tuple[str, float, int]]:
    """Very naive Elliott wave detection returning up to five wave points."""
    extrema = []
    for i in range(1, len(prices) - 1):
        if prices[i - 1] < prices[i] > prices[i + 1]:
            extrema.append((i, "max"))
        elif prices[i - 1] > prices[i] < prices[i + 1]:
            extrema.append((i, "min"))
    waves: List[Tuple[str, float, int]] = []
    last = None
    for idx, kind in extrema:
        if last and kind == last:
            continue
        waves.append((dates[idx], prices[idx], len(waves) + 1))
        last = kind
        if len(waves) == 5:
            break
    return waves


def fetch_candles(
    ticker: str,
    start: datetime.date,
    end: datetime.date,
    chart_type: str = "line",
    elliott: bool = False,
) -> str:
    """Fetch candle data for a ticker and return a Plotly figure JSON string."""
>>>>>>> origin/codex/-api-5dhsxm
    params = {"from": start, "till": end, "interval": 24}
    response = requests.get(MOEX_CANDLES_URL.format(ticker=ticker), params=params)
    response.raise_for_status()
    candles = response.json()["candles"]
    columns = candles["columns"]
    data = candles["data"]
    if not data:
        raise ValueError(f"No data for ticker {ticker}")
<<<<<<< HEAD
    idx_date = columns.index("begin")
    idx_close = columns.index("close")
    dates = [row[idx_date][:10] for row in data]
    closes = [row[idx_close] for row in data]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=closes, mode="lines", name=ticker))
=======

    idx_date = columns.index("begin")
    idx_open = columns.index("open")
    idx_close = columns.index("close")
    idx_high = columns.index("high")
    idx_low = columns.index("low")

    dates = [row[idx_date][:10] for row in data]
    opens = [row[idx_open] for row in data]
    closes = [row[idx_close] for row in data]
    highs = [row[idx_high] for row in data]
    lows = [row[idx_low] for row in data]

    fig = go.Figure()
    if chart_type == "candlestick":
        fig.add_trace(
            go.Candlestick(
                x=dates, open=opens, high=highs, low=lows, close=closes, name=ticker
            )
        )
    else:
        fig.add_trace(go.Scatter(x=dates, y=closes, mode="lines", name=ticker))

    if elliott:
        waves = _elliott_waves(dates, closes)
        if waves:
            fig.add_trace(
                go.Scatter(
                    x=[w[0] for w in waves],
                    y=[w[1] for w in waves],
                    mode="markers+text",
                    marker=dict(color="red", size=8),
                    text=[f"W{w[2]}" for w in waves],
                    textposition="top center",
                    name="Elliott Waves",
                )
            )

>>>>>>> origin/codex/-api-5dhsxm
    fig.update_layout(title=ticker, xaxis_title="Date", yaxis_title="Price")
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


@app.route("/", methods=["GET", "POST"])
def index():
    graphs: List[str] = []
    tickers_input = ""
<<<<<<< HEAD
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
=======
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=60)
    start_str = default_start.isoformat()
    end_str = today.isoformat()
    chart_type = "line"
    elliott = False

    if request.method == "POST":
        tickers_input = request.form.get("tickers", "")
        start_str = request.form.get("start") or start_str
        end_str = request.form.get("end") or end_str
        chart_type = request.form.get("chart_type", "line")
        elliott = request.form.get("elliott") == "on"

        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        start_date = datetime.date.fromisoformat(start_str)
        end_date = datetime.date.fromisoformat(end_str)

        for ticker in tickers:
            try:
                graphs.append(
                    fetch_candles(ticker, start=start_date, end=end_date, chart_type=chart_type, elliott=elliott)
                )
            except Exception:
                # Skip tickers with errors
                continue

    return render_template(
        "index.html",
        graphs=graphs,
        tickers=tickers_input,
        start=start_str,
        end=end_str,
        chart_type=chart_type,
        elliott=elliott,
    )
>>>>>>> origin/codex/-api-5dhsxm


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
