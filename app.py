import streamlit as st
from sol_trend import get_binance_sol_ohlcv, calc_indicators, evaluate_trend_by_category

st.set_page_config(page_title="📊 Solana Trend Dashboard", layout="wide")

st.title("📈 Solana (SOL) Trend Dashboard")

try:
    df = get_binance_sol_ohlcv(limit=1000)
    df = calc_indicators(df)
    trend = evaluate_trend_by_category(df)

    st.subheader("📊 Overall Trend Summary")
    st.json(trend["overall"])

    st.subheader("📂 Category Breakdown")
    cols = st.columns(2)
    for i, category in enumerate(["momentum", "trend"]):
        with cols[i]:
            st.metric(label=category.capitalize(), value=trend[category]["score"])

    st.subheader("📉 Price + SMAs")
    st.line_chart(df[["close", "sma_20", "sma_50", "sma_200"]])

    st.subheader("📈 RSI + MACD")
    st.line_chart(df[["rsi"]])
    st.line_chart(df[["macd", "macd_signal"]])

except Exception as e:
    st.error(f"❌ Failed to load dashboard: {e}")