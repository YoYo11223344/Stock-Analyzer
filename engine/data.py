# import yfinance as yf
# import pandas as pd

# def normalize_symbol(symbol):
#     symbol = symbol.upper().strip()
#     if symbol.endswith(".NS") or symbol.endswith(".BO"):
#         return symbol
#     return f"{symbol}.NS"

# def _flatten_columns(df):
#     if isinstance(df.columns, pd.MultiIndex):
#         df.columns = df.columns.get_level_values(0)

#     # Remove column index name like "Price"
#     df.columns.name = None
#     return df


# def fetch_data(symbol, period="1y"):
#     symbol = normalize_symbol(symbol)

#     stock = yf.download(symbol, period=period, interval="1d", progress=False)
#     nifty = yf.download("^NSEI", period=period, interval="1d", progress=False)

#     stock = _flatten_columns(stock)
#     nifty = _flatten_columns(nifty)

#     stock.dropna(inplace=True)
#     nifty.dropna(inplace=True)

#     if stock.empty:
#         raise ValueError("No stock data found")

#     return stock, nifty


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
            wait = 2 ** attempt  # exponential backoff
            time.sleep(wait)
    raise Exception("Rate limit hit. Try again later.")


@st.cache_data(ttl=600)  # cache for 10 minutes
def fetch_data(symbol, period="6mo"):
    symbol = normalize_symbol(symbol)

    # ✅ Single batched request instead of two
    data = safe_download(
        [symbol, "^NSEI"],
        period=period,
        interval="1d",
        group_by="ticker",
        progress=False
    )

    if data.empty:
        raise ValueError("No data returned")

if symbol not in data.columns.get_level_values(0):
    raise ValueError(f"{symbol} not found in Yahoo data")

if "^NSEI" not in data.columns.get_level_values(0):
    raise ValueError("NIFTY data missing")

stock = data[symbol].copy()
nifty = data["^NSEI"].copy()

    stock = _flatten_columns(stock)
    nifty = _flatten_columns(nifty)

    stock.dropna(inplace=True)
    nifty.dropna(inplace=True)

    if stock.empty:
        raise ValueError("No stock data found")

    return stock, nifty
