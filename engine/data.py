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

            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                return df

        except Exception:
            time.sleep(2 ** attempt)

    return pd.DataFrame()


def normalize_dataframe(df, symbol):
    """
    Forces OHLC format even if Yahoo returns weird structure
    """

    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol}")

    # If MultiIndex columns exist → flatten
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.columns = [str(c).strip() for c in df.columns]

    # Sometimes Yahoo returns lowercase or weird casing
    rename_map = {}
    for col in df.columns:
        if col.lower() == "open":
            rename_map[col] = "Open"
        elif col.lower() == "high":
            rename_map[col] = "High"
        elif col.lower() == "low":
            rename_map[col] = "Low"
        elif col.lower() == "close":
            rename_map[col] = "Close"
        elif col.lower() == "volume":
            rename_map[col] = "Volume"

    df = df.rename(columns=rename_map)

    return df


def validate(df, symbol):
    required = ["Open", "High", "Low", "Close"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"{symbol} missing columns {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    return True


@st.cache_data(ttl=1800)
def fetch_data(symbol, period="2y"):
    symbol = normalize_symbol(symbol)

    stock = safe_download(symbol, period)
    nifty = safe_download("^NSEI", period)

    stock = normalize_dataframe(stock, symbol)
    nifty = normalize_dataframe(nifty, "^NSEI")

    validate(stock, symbol)
    validate(nifty, "^NSEI")

    stock = stock.dropna().sort_index()
    nifty = nifty.dropna().sort_index()

    if len(stock) < 60:
        raise ValueError(
            f"Not enough data for {symbol}: {len(stock)} rows"
        )

    return stock, nifty
