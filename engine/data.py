import streamlit as st
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
            data = yf.download(
                symbol,
                period=period,
                interval="1d",
                progress=False
            )
            if data is not None and not data.empty:
                return data
        except Exception:
            time.sleep(2 ** attempt)

    return pd.DataFrame()


@st.cache_data(ttl=1800)
def fetch_data(symbol, period="2y"):
    symbol = normalize_symbol(symbol)

    stock = safe_download(symbol, period)
    nifty = safe_download("^NSEI", period)

    # =========================
    # VALIDATION
    # =========================
    if stock.empty:
        raise ValueError(f"No stock data found for {symbol}. Yahoo may be blocking or symbol invalid.")

    if nifty.empty:
        raise ValueError("No NIFTY data found (^NSEI)")

    # =========================
    # CLEANING
    # =========================
    stock = stock.dropna()
    nifty = nifty.dropna()

    stock = stock.sort_index()
    nifty = nifty.sort_index()

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in stock.columns:
            raise ValueError(f"Missing column in stock data: {col}")

    # =========================
    # FINAL SAFETY CHECK
    # =========================
    if len(stock) < 60:
        raise ValueError(
            f"Not enough data for {symbol}: {len(stock)} rows. "
            "Try again later or increase period."
        )

    return stock, nifty
