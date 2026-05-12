import streamlit as st
import numpy as np
from engine.data import fetch_data
from engine.indicators import compute_features
from engine.fundamentals import get_fundamentals
from engine.scoring import *


CONFIDENCE_BASE = 0.5
HOLDING_PERIOD = 20


def safe_compute_features(df, name="stock"):
    """
    HARD GUARD: prevents 1-row / empty dataframe crashing indicators
    """
    if df is None:
        raise ValueError(f"{name} data is None")

    if len(df) < 60:
        raise ValueError(f"Not enough data for {name}: {len(df)} rows (need ≥ 60)")

    return compute_features(df)


@st.cache_data(ttl=600)
def analyze_stock(symbol):
    # =========================
    # FETCH DATA
    # =========================
    stock, nifty = fetch_data(symbol)

    # =========================
    # HARD SAFETY CHECKS
    # =========================
    if stock is None or len(stock) < 60:
        raise ValueError(f"Stock data invalid: {len(stock) if stock is not None else 0} rows")

    if nifty is None or len(nifty) < 60:
        raise ValueError(f"NIFTY data invalid: {len(nifty) if nifty is not None else 0} rows")

    # =========================
    # FEATURES (SAFE)
    # =========================
    stock_feat = safe_compute_features(stock, "stock")
    nifty_feat = safe_compute_features(nifty, "nifty")

    latest = stock_feat.iloc[-1]
    nifty_latest = nifty_feat.iloc[-1]

    # =========================
    # SCORING ENGINE
    # =========================
    confidence = CONFIDENCE_BASE
    reasons = []

    # Market regime filter
    if nifty_latest["EMA20"] < nifty_latest["EMA50"]:
        confidence -= 0.2
        reasons.append("Market in bearish regime")

    # Trend
    if latest["EMA20"] > latest["EMA50"]:
        confidence += 0.1
        reasons.append("Bullish EMA alignment")

    # Momentum scoring
    confidence += score_adx(latest["ADX"])
    confidence += score_rsi(latest["RSI"], latest["RSI_SLOPE"])
    confidence += score_macd(latest["MACD_HIST"])

    # Relative strength
    if latest["RET_20D_ADJ"] > nifty_latest["RET_20D_ADJ"]:
        confidence += 0.1
        reasons.append("Outperformance vs NIFTY")

    # Overextension filter
    ema_dist = (latest["Close"] - latest["EMA20"]) / latest["EMA20"]
    if ema_dist > 0.08:
        confidence -= 0.1
        reasons.append("Price extended from EMA")

    # Risk/Reward sanity check
    expected_move = latest["ATR"] * np.sqrt(HOLDING_PERIOD)
    rr = expected_move / (latest["ATR"] * 2)

    if rr < 1:
        confidence -= 0.1
        reasons.append("Poor reward-to-risk")

    # Fundamentals
    f = get_fundamentals(symbol)

    if f.get("revenue_growth") and f["revenue_growth"] > 0:
        confidence += 0.05

    if f.get("earnings_growth") and f["earnings_growth"] > 0:
        confidence += 0.05

    confidence += score_valuation(f.get("pe", 0))

    # =========================
    # FINAL NORMALIZATION
    # =========================
    confidence = max(0, min(confidence, 1))
    signal = "BUY" if confidence >= 0.65 else "NO BUY"

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "reasons": reasons,
        "features": latest
    }
