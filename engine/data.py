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
            wait = 2 ** attempt
            time.sleep(wait)
    raise Exception("Rate limit hit. Try again later.")


@st.cache_data(ttl=1800)
def fetch_data(symbol, period="6mo"):
    symbol = normalize_symbol(symbol)

    # Download stock + NIFTY together
    data = safe_download(
        [symbol, "^NSEI"],
        period=period,
        interval="1d",
        group_by="ticker",
        progress=False
    )

    if data is None or data.empty:
        raise ValueError("No data returned from Yahoo Finance")

    # Validate structure
    if not isinstance(data.columns, pd.MultiIndex):
        raise ValueError("Unexpected data format from Yahoo Finance")

    tickers = data.columns.get_level_values(0)

    if symbol not in tickers:
        raise ValueError(f"{symbol} not found in Yahoo data")

    if "^NSEI" not in tickers:
        raise ValueError("NIFTY (^NSEI) data missing")

    # Split data
    stock = data[symbol].copy()
    nifty = data["^NSEI"].copy()

    # Flatten columns
    stock = _flatten_columns(stock)
    nifty = _flatten_columns(nifty)

    # Clean
    stock.dropna(inplace=True)
    nifty.dropna(inplace=True)

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in stock.columns:
            raise ValueError(f"Missing column in stock data: {col}")

    if stock.empty:
        raise ValueError("Stock data is empty after cleaning")

    return stock, nifty
