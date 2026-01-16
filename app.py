import streamlit as st
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from engine.engine import analyze_stock
from engine.data import fetch_data
from engine.indicators import compute_features

def generate_explanations(features):
    explanations = []

    if features["EMA20"] > features["EMA50"]:
        explanations.append("📈 Short-term trend is bullish (20 EMA above 50 EMA).")
    else:
        explanations.append("📉 Trend is weak or bearish (20 EMA below 50 EMA).")

    if features["ADX"] > 25:
        explanations.append("💪 Strong trend strength (ADX above 25).")
    elif features["ADX"] > 20:
        explanations.append("⚖️ Moderate trend strength.")
    else:
        explanations.append("😴 Weak or sideways market.")

    if features["RSI"] > 60:
        explanations.append("🔥 Strong momentum indicated by RSI.")
    elif features["RSI"] > 50:
        explanations.append("🙂 Mild bullish momentum.")
    elif features["RSI"] > 40:
        explanations.append("⚠️ Momentum is weakening.")
    else:
        explanations.append("❌ Bearish momentum (RSI below 40).")

    if features["MACD_HIST"] > 0:
        explanations.append("✅ MACD supports the uptrend.")
    else:
        explanations.append("❌ MACD does not confirm bullish momentum.")

    volatility = features["ATR"] / features["Close"]
    if volatility > 0.04:
        explanations.append("⚠️ High volatility detected, risk is elevated.")
    else:
        explanations.append("🛡️ Volatility is within acceptable limits.")

    return explanations


st.set_page_config("📈 Stock Analyzer", layout="wide")

st.title("📈 Advanced Stock Analyzer")

symbol = st.text_input("Stock Symbol (comma-separated allowed)", "TCS")

if st.button("Analyze"):
    symbols = [s.strip() for s in symbol.split(",")]

    for sym in symbols:
        result = analyze_stock(sym)
        confidence = result["confidence"]

        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Chart", "📘 Details"])

        with tab1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=confidence * 100,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "green" if result["signal"] == "BUY" else "red"}
                }

            ))
            st.plotly_chart(fig)

            if result["signal"] == "BUY":
                st.markdown(
                    f"<h2 style='color:#2ecc71;'>🚀 BUY ({confidence*100:.0f}%)</h2>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<h2 style='color:#e74c3c;'>⛔ NO BUY ({confidence*100:.0f}%)</h2>",
                    unsafe_allow_html=True
                )

            for r in result["reasons"]:
                color = "#2ecc71" if result["signal"] == "BUY" else "#e74c3c"
                st.markdown(f"<span style='color:{color}'>• {r}</span>", unsafe_allow_html=True)


        with tab2:
            stock, _ = fetch_data(sym)
            feat = compute_features(stock).tail(80)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
            fig.add_trace(go.Scatter(x=feat.index, y=feat["Close"], name="Close"), row=1, col=1)
            fig.add_trace(go.Scatter(x=feat.index, y=feat["EMA20"], name="EMA20"), row=1, col=1)
            fig.add_trace(go.Scatter(x=feat.index, y=feat["EMA50"], name="EMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=feat.index, y=feat["RSI"], name="RSI"), row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("📘 Beginner-Friendly Explanation")

            explanations = generate_explanations(result["features"])
            for exp in explanations:
                st.markdown(f"- {exp}")

            st.markdown("---")
            st.info("ℹ️ Signal validity: ~20 trading days. This is not financial advice.")

