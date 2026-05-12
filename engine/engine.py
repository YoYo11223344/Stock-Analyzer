# import numpy as np
# from engine.data import fetch_data
# from engine.indicators import compute_features
# from engine.fundamentals import get_fundamentals
# from engine.scoring import *

# CONFIDENCE_BASE = 0.5
# HOLDING_PERIOD = 20

# def analyze_stock(symbol):
#     stock, nifty = fetch_data(symbol)
#     stock_feat = compute_features(stock)
#     nifty_feat = compute_features(nifty)

#     latest = stock_feat.iloc[-1]
#     nifty_latest = nifty_feat.iloc[-1]

#     confidence = CONFIDENCE_BASE
#     reasons = []

#     # Market regime
#     if nifty_latest["EMA20"] < nifty_latest["EMA50"]:
#         confidence -= 0.2
#         reasons.append("Market in bearish regime")

#     # Trend
#     if latest["EMA20"] > latest["EMA50"]:
#         confidence += 0.1
#         reasons.append("Bullish EMA alignment")

#     confidence += score_adx(latest["ADX"])
#     confidence += score_rsi(latest["RSI"], latest["RSI_SLOPE"])
#     confidence += score_macd(latest["MACD_HIST"])

#     # Relative strength
#     if latest["RET_20D_ADJ"] > nifty_latest["RET_20D_ADJ"]:
#         confidence += 0.1
#         reasons.append("Risk-adjusted outperformance vs NIFTY")

#     # Late entry filter
#     ema_dist = (latest["Close"] - latest["EMA20"]) / latest["EMA20"]
#     if ema_dist > 0.08:
#         confidence -= 0.1
#         reasons.append("Price extended from EMA")

#     # Reward/Risk
#     expected_move = latest["ATR"] * np.sqrt(HOLDING_PERIOD)
#     rr = expected_move / (latest["ATR"] * 2)
#     if rr < 1:
#         confidence -= 0.1
#         reasons.append("Poor reward-to-risk")

#     # Fundamentals
#     f = get_fundamentals(symbol)
#     if f["revenue_growth"] and f["revenue_growth"] > 0:
#         confidence += 0.05
#     if f["earnings_growth"] and f["earnings_growth"] > 0:
#         confidence += 0.05
#     confidence += score_valuation(f["pe"])

#     confidence = max(0, min(confidence, 1))
#     signal = "BUY" if confidence >= 0.65 else "NO BUY"

#     return {
#         "signal": signal,
#         "confidence": round(confidence, 2),
#         "reasons": reasons,
#         "features": latest
#     }

import streamlit as st
import numpy as np

from engine.data import fetch_data
from engine.indicators import compute_features
from engine.fundamentals import get_fundamentals
from engine.scoring import *


CONFIDENCE_BASE = 0.5
HOLDING_PERIOD = 20


@st.cache_data(ttl=600)
def analyze_stock(symbol):

    # ==========================================
    # FETCH DATA
    # ==========================================
    stock, nifty = fetch_data(symbol)

    if stock is None or stock.empty:
        raise ValueError(f"No stock data found for {symbol}")

    if nifty is None or nifty.empty:
        raise ValueError("No NIFTY data available")

    # ==========================================
    # COMPUTE FEATURES
    # ==========================================
    stock_feat = compute_features(stock)
    nifty_feat = compute_features(nifty)

    latest = stock_feat.iloc[-1]
    nifty_latest = nifty_feat.iloc[-1]

    # ==========================================
    # INITIALIZE
    # ==========================================
    confidence = CONFIDENCE_BASE
    reasons = []

    # ==========================================
    # MARKET REGIME
    # ==========================================
    if nifty_latest["EMA20"] < nifty_latest["EMA50"]:

        confidence -= 0.2
        reasons.append("Market in bearish regime")

    # ==========================================
    # TREND
    # ==========================================
    if latest["EMA20"] > latest["EMA50"]:

        confidence += 0.1
        reasons.append("Bullish EMA alignment")

    # ==========================================
    # TECHNICAL SCORES
    # ==========================================
    confidence += score_adx(latest["ADX"])

    confidence += score_rsi(
        latest["RSI"],
        latest["RSI_SLOPE"]
    )

    confidence += score_macd(
        latest["MACD_HIST"]
    )

    # ==========================================
    # RELATIVE STRENGTH
    # ==========================================
    if latest["RET_20D_ADJ"] > nifty_latest["RET_20D_ADJ"]:

        confidence += 0.1
        reasons.append("Outperformance vs NIFTY")

    # ==========================================
    # LATE ENTRY FILTER
    # ==========================================
    ema_dist = (
        (latest["Close"] - latest["EMA20"])
        / latest["EMA20"]
    )

    if ema_dist > 0.08:

        confidence -= 0.1
        reasons.append("Price extended from EMA")

    # ==========================================
    # REWARD / RISK
    # ==========================================
    expected_move = (
        latest["ATR"] * np.sqrt(HOLDING_PERIOD)
    )

    rr = expected_move / (latest["ATR"] * 2)

    if rr < 1:

        confidence -= 0.1
        reasons.append("Poor reward-to-risk")

    # ==========================================
    # FUNDAMENTALS
    # ==========================================
    try:

        f = get_fundamentals(symbol)

        revenue_growth = f.get("revenue_growth")
        earnings_growth = f.get("earnings_growth")
        pe = f.get("pe")

        if (
            revenue_growth is not None
            and revenue_growth > 0
        ):
            confidence += 0.05

        if (
            earnings_growth is not None
            and earnings_growth > 0
        ):
            confidence += 0.05

        confidence += score_valuation(pe)

    except Exception:
        reasons.append("Fundamental data unavailable")

    # ==========================================
    # CLEAN CONFIDENCE
    # ==========================================
    confidence = max(0, min(confidence, 1))

    # ==========================================
    # FINAL SIGNAL
    # ==========================================
    signal = (
        "BUY"
        if confidence >= 0.65
        else "NO BUY"
    )

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "reasons": reasons,
        "features": latest
    }
