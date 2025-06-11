import streamlit as st
import matplotlib.pyplot as plt
from sol_trend import get_binance_sol_ohlcv, calc_indicators, evaluate_trend_by_category

st.set_page_config(page_title="📊 Solana Trend Dashboard", layout="wide")
st.title("📈 Solana (SOL) Trend Dashboard")

try:
    df = get_binance_sol_ohlcv(limit=1000)
    df = calc_indicators(df)
    trend = evaluate_trend_by_category(df)

    st.subheader("🌿 Overall Trend Summary")
    st.json(trend["overall"])

    st.subheader("📁 Category Breakdown")
    cols = st.columns(2)
    for i, category in enumerate(["momentum", "trend"]):
        with cols[i]:
            st.metric(label=category.capitalize(), value=trend[category]["score"])

    st.subheader("📉 Price + SMAs")
    fig, ax = plt.subplots(figsize=(10, 4))
    df[["close", "sma_20", "sma_50", "sma_200"]].plot(ax=ax)
    ax.set_title("Price with SMAs")
    ax.set_ylabel("Price")
    ax.set_xlabel("")
    st.pyplot(fig)

    st.subheader("📊 RSI")
    st.line_chart(df[["rsi"]])

    st.subheader("📈 MACD")
    st.line_chart(df[["macd", "macd_signal"]])

    st.subheader("📈 ROC, CCI, UO")
    for ind in ["roc", "cci", "uo"]:
        if ind in df.columns:
            st.line_chart(df[[ind]])
        else:
            st.warning(f"{ind.upper()} not found in DataFrame.")

    st.subheader("🔍 Stochastic Oscillator")
    if "stoch_k" in df.columns and "stoch_d" in df.columns:
        st.line_chart(df[["stoch_k", "stoch_d"]])
    else:
        st.warning("Stochastic Oscillator data not available.")

    st.subheader("Williams %R")
    if "williams_r" in df.columns:
        st.line_chart(df[["williams_r"]])
    else:
        st.warning("Williams %R not available.")

    st.subheader("ADX + DI")
    if all(col in df.columns for col in ["adx", "+DI", "-DI"]):
        st.line_chart(df[["adx", "+DI", "-DI"]])
    else:
        st.warning("ADX/DMI data not available.")

    st.subheader("OBV, CMF, AD")
    for vol_col in ["obv", "cmf", "ad"]:
        if vol_col in df.columns:
            st.line_chart(df[[vol_col]])
        else:
            st.warning(f"{vol_col.upper()} not available.")

except Exception as e:
    st.error(f"❌ Failed to load dashboard: {e}")