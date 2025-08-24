# MOEX Chart Server

This simple Flask application fetches historical candle data from the Moscow Exchange (MOEX) for any list of tickers and displays interactive Plotly charts in a web interface. The page can render multiple tickers at once and supports both line and candlestick charts. Optional Elliott wave markers and other popular indicators (SMA, EMA, Bollinger Bands, MACD, RSI) help with technical analysis.

## Usage

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:8000` in your browser. Enter tickers separated by commas (e.g., `SBER, GAZP`) to view multiple charts simultaneously. You can select the date range, choose between line or candlestick display, and toggle Elliott waves or any of the other indicators.
