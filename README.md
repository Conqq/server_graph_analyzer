# MOEX Chart Server

This simple Flask application fetches historical candle data from the Moscow Exchange (MOEX) for any list of tickers and displays interactive Plotly charts in a web interface.

## Usage

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:8000` in your browser. Enter tickers separated by commas (e.g., `SBER, GAZP`) to view multiple charts simultaneously.
