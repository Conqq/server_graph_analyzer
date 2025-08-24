import datetime
import json
from typing import List, Sequence, Tuple

import plotly
import plotly.graph_objs as go
import pandas as pd
from plotly.subplots import make_subplots
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

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
    sma: bool = False,
    ema: bool = False,
    bollinger: bool = False,
    macd: bool = False,
    rsi: bool = False,
) -> str:
    """Fetch candle data for a ticker and return a Plotly figure JSON string."""
    params = {"from": start, "till": end, "interval": 24}
    response = requests.get(MOEX_CANDLES_URL.format(ticker=ticker), params=params)
    response.raise_for_status()
    candles = response.json()["candles"]
    columns = candles["columns"]
    data = candles["data"]
    if not data:
        raise ValueError(f"No data for ticker {ticker}")

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

    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(dates),
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
        }
    )

    if sma or bollinger:
        df["SMA"] = df["Close"].rolling(window=20).mean()
    if ema or macd:
        df["EMA"] = df["Close"].ewm(span=20, adjust=False).mean()
    if bollinger:
        rolling_std = df["Close"].rolling(window=20).std()
        df["Bollinger_Upper"] = df["SMA"] + 2 * rolling_std
        df["Bollinger_Lower"] = df["SMA"] - 2 * rolling_std
    if macd:
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    if rsi:
        delta = df["Close"].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        rs = roll_up / roll_down
        df["RSI"] = 100 - (100 / (1 + rs))

    rows = 1
    row_heights = [0.6]
    row_map = {"price": 1}
    if macd:
        rows += 1
        row_heights.append(0.2)
        row_map["macd"] = rows
    if rsi:
        rows += 1
        row_heights.append(0.2)
        row_map["rsi"] = rows

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=row_heights, vertical_spacing=0.03)

    if chart_type == "candlestick":
        fig.add_trace(
            go.Candlestick(
                x=dates, open=opens, high=highs, low=lows, close=closes, name=ticker
            ),
            row=row_map["price"],
            col=1,
        )
    else:
        fig.add_trace(
            go.Scatter(x=dates, y=closes, mode="lines", name=ticker),
            row=row_map["price"],
            col=1,
        )

    if sma:
        fig.add_trace(
            go.Scatter(x=dates, y=df["SMA"], mode="lines", name="SMA"),
            row=row_map["price"],
            col=1,
        )
    if ema:
        fig.add_trace(
            go.Scatter(x=dates, y=df["EMA"], mode="lines", name="EMA"),
            row=row_map["price"],
            col=1,
        )
    if bollinger:
        fig.add_trace(
            go.Scatter(x=dates, y=df["Bollinger_Upper"], line=dict(color="rgba(0,0,255,0.2)"), name="Bollinger Upper"),
            row=row_map["price"],
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df["Bollinger_Lower"],
                line=dict(color="rgba(0,0,255,0.2)"),
                fill="tonexty",
                name="Bollinger Lower",
            ),
            row=row_map["price"],
            col=1,
        )
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
                ),
                row=row_map["price"],
                col=1,
            )
    if macd:
        fig.add_trace(
            go.Scatter(x=dates, y=df["MACD"], mode="lines", name="MACD"),
            row=row_map["macd"],
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=dates, y=df["Signal"], mode="lines", name="Signal"),
            row=row_map["macd"],
            col=1,
        )
    if rsi:
        fig.add_trace(
            go.Scatter(x=dates, y=df["RSI"], mode="lines", name="RSI"),
            row=row_map["rsi"],
            col=1,
        )
        fig.add_hline(y=70, line=dict(color="red", dash="dash"), row=row_map["rsi"], col=1)
        fig.add_hline(y=30, line=dict(color="green", dash="dash"), row=row_map["rsi"], col=1)

    fig.update_yaxes(title_text="Price", row=row_map["price"], col=1)
    if macd:
        fig.update_yaxes(title_text="MACD", row=row_map["macd"], col=1)
    if rsi:
        fig.update_yaxes(title_text="RSI", row=row_map["rsi"], col=1)
    fig.update_layout(title=ticker, xaxis_title="Date", height=300 * rows)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


@app.route("/", methods=["GET", "POST"])
def index():
    graphs: List[str] = []
    tickers_input = ""
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=60)
    start_str = default_start.isoformat()
    end_str = today.isoformat()
    chart_type = "line"
    elliott = False
    sma = False
    ema = False
    bollinger = False
    macd = False
    rsi = False

    if request.method == "POST":
        tickers_input = request.form.get("tickers", "")
        start_str = request.form.get("start") or start_str
        end_str = request.form.get("end") or end_str
        chart_type = request.form.get("chart_type", "line")
        elliott = request.form.get("elliott") == "on"
        sma = request.form.get("sma") == "on"
        ema = request.form.get("ema") == "on"
        bollinger = request.form.get("bollinger") == "on"
        macd = request.form.get("macd") == "on"
        rsi = request.form.get("rsi") == "on"

        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        start_date = datetime.date.fromisoformat(start_str)
        end_date = datetime.date.fromisoformat(end_str)

        for ticker in tickers:
            try:
                graphs.append(
                    fetch_candles(
                        ticker,
                        start=start_date,
                        end=end_date,
                        chart_type=chart_type,
                        elliott=elliott,
                        sma=sma,
                        ema=ema,
                        bollinger=bollinger,
                        macd=macd,
                        rsi=rsi,
                    )
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
        sma=sma,
        ema=ema,
        bollinger=bollinger,
        macd=macd,
        rsi=rsi,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
