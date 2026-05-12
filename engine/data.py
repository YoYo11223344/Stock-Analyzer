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
            df = yf.download(
                symbol,
                period=period,
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False
            )

            # IMPORTANT: validate structure immediately
            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                return df

        except Exception:
            time.sleep(2 ** attempt)

    return pd.DataFrame()


def validate_ohlc(df, symbol_name):
    required = ["Open", "High", "Low", "Close"]

    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol_name}")

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            f"{symbol_name} missing columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    return True


@st.cache_data(ttl=1800)
def fetch_data(symbol, period="2y"):
    symbol = normalize_symbol(symbol)

    stock = safe_download(symbol, period)
    nifty = safe_download("^NSEI", period)

    # =========================
    # VALIDATION
    # =========================
    validate_ohlc(stock, symbol)
    validate_ohlc(nifty, "^NSEI")

    # =========================
    # CLEANING
    # =========================
    stock = stock.dropna().sort_index()
    nifty = nifty.dropna().sort_index()

    if len(stock) < 60:
        raise ValueError(
            f"Not enough data for {symbol}: {len(stock)} rows. "
            "Try again later or increase period."
        )

    return stock, nifty
