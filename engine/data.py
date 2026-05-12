import streamlit as st
import yfinance as yf
import pandas as pd
import time
from yfinance.exceptions import YFRateLimitError


def normalize_symbol(symbol):
    symbol = symbol.upper().strip()
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol
    return f"{symbol}.NS"


def _flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns.name = None
    return df


def safe_download(*args, **kwargs):
    for attempt in range(5):
        try:
            return yf.download(*args, **kwargs)
        except YFRateLimitError:
            time.sleep(2 ** attempt)
    raise Exception("Yahoo Finance rate limit hit. Try again later.")


@st.cache_data(ttl=1800)
def fetch_data(symbol, period="2y"):  # ✅ FIX: increased from 6mo → 2y
    symbol = normalize_symbol(symbol)

    data = safe_download(
        [symbol, "^NSEI"],
        period=period,
        interval="1d",
        group_by="ticker",
        progress=False
    )

    if data is None or data.empty:
        raise ValueError("No data returned from Yahoo Finance")

    # Ensure MultiIndex structure
    if not isinstance(data.columns, pd.MultiIndex):
        raise ValueError("Unexpected Yahoo Finance format (not MultiIndex)")

    tickers = data.columns.get_level_values(0)

    if symbol not in tickers:
        raise ValueError(f"{symbol} not found in Yahoo data")

    if "^NSEI" not in tickers:
        raise ValueError("NIFTY (^NSEI) data missing")

    stock = data[symbol].copy()
    nifty = data["^NSEI"].copy()

    # Flatten
    stock = _flatten_columns(stock)
    nifty = _flatten_columns(nifty)

    # Sort index (important for indicators)
    stock = stock.sort_index()
    nifty = nifty.sort_index()

    # Clean data
    stock.dropna(inplace=True)
    nifty.dropna(inplace=True)

    # ✅ FIX: enforce minimum dataset size BEFORE indicators
    if len(stock) < 60:
        raise ValueError(
            f"Not enough data for {symbol}: {len(stock)} rows. "
            "Try using a longer history period."
        )

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in stock.columns:
            raise ValueError(f"Missing column in stock data: {col}")

    return stock, nifty
