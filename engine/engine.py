import yfinance as yf
import pandas as pd
import time


def normalize_symbol(symbol):
    symbol = symbol.upper().strip()
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol
    return f"{symbol}.NS"


def safe_download(symbol, period="2y"):
    for attempt in range(5):
        try:
            df = yf.download(
                symbol,
                period=period,
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False
            )

            if df is not None and isinstance(df, pd.DataFrame) and len(df) > 5:
                return df

        except Exception:
            time.sleep(2 ** attempt)

    return pd.DataFrame()


def validate(df, name):
    if df is None or df.empty:
        raise ValueError(f"{name}: empty dataframe")

    required = ["Open", "High", "Low", "Close"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"{name}: missing columns {missing}")

    return True


def fetch_data(symbol, period="2y"):
    symbol = normalize_symbol(symbol)

    stock = safe_download(symbol, period)
    nifty = safe_download("^NSEI", period)

    validate(stock, symbol)
    validate(nifty, "^NSEI")

    stock = stock.dropna().sort_index()
    nifty = nifty.dropna().sort_index()

    return stock, nifty
