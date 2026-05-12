import streamlit as st
import yfinance as yf
import pandas as pd
import time
from threading import Lock

# =========================
# GLOBAL REQUEST CACHE
# =========================
REQUEST_CACHE = {}
LOCK = Lock()


def normalize_symbol(symbol):
    symbol = symbol.upper().strip()
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol
    return f"{symbol}.NS"


def safe_download(symbol, period="2y"):
    """
    Cached + rate-limit safe downloader
    """

    key = f"{symbol}_{period}"

    # ✅ Step 1: return cached result if available
    if key in REQUEST_CACHE:
        return REQUEST_CACHE[key]

    # ✅ Step 2: prevent simultaneous API calls
    with LOCK:
        # double-check inside lock
        if key in REQUEST_CACHE:
            return REQUEST_CACHE[key]

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

                if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                    REQUEST_CACHE[key] = df
                    return df

            except Exception:
                time.sleep(2 ** attempt)

    return pd.DataFrame()


def normalize_dataframe(df, symbol):
    """
    Ensures OHLC format is always clean
    """

    if df is None or df.empty:
        return df

    # flatten MultiIndex if exists
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        lower = col.lower()

        if lower == "open":
            rename_map[col] = "Open"
        elif lower == "high":
            rename_map[col] = "High"
        elif lower == "low":
            rename_map[col] = "Low"
        elif lower == "close":
            rename_map[col] = "Close"
        elif lower == "volume":
            rename_map[col] = "Volume"

    df = df.rename(columns=rename_map)

    return df


def validate_ohlc(df, symbol):
    required = ["Open", "High", "Low", "Close"]

    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol}")

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"{symbol} missing columns {missing}. "
            f"Available: {list(df.columns)}"
        )

    return True


@st.cache_data(ttl=1800)
def fetch_data(symbol, period="2y"):
    symbol = normalize_symbol(symbol)

    # =========================
    # FETCH DATA
    # =========================
    stock = safe_download(symbol, period)
    nifty = safe_download("^NSEI", period)

    # =========================
    # NORMALIZE STRUCTURE
    # =========================
    stock = normalize_dataframe(stock, symbol)
    nifty = normalize_dataframe(nifty, "^NSEI")

    # =========================
    # VALIDATE
    # =========================
    validate_ohlc(stock, symbol)
    validate_ohlc(nifty, "^NSEI")

    # =========================
    # CLEAN
    # =========================
    stock = stock.dropna().sort_index()
    nifty = nifty.dropna().sort_index()

    # =========================
    # FINAL CHECK
    # =========================
    if len(stock) < 60:
        raise ValueError(
            f"Not enough data for {symbol}: {len(stock)} rows"
        )

    return stock, nifty
