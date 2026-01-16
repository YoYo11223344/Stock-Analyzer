import yfinance as yf
import streamlit as st

@st.cache_data(ttl=86400)
def get_fundamentals(symbol):
    info = yf.Ticker(symbol).info
    return {
        "pe": info.get("trailingPE"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth")
    }
