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

    def plot_indicator(name, cols):
        if all(col in df.columns for col in cols):
            st.subheader(name)
            st.line_chart(df[cols])
        else:
            st.warning(f"{name} not available.")

    plot_indicator("RSI", ["rsi"])
    plot_indicator("MACD", ["macd", "macd_signal"])
    plot_indicator("ROC", ["roc"])
    plot_indicator("CCI", ["cci"])
    plot_indicator("Ultimate Oscillator (UO)", ["uo"])
    plot_indicator("Stochastic Oscillator", ["stoch_k", "stoch_d"])
    plot_indicator("Williams %R", ["williams_r"])
    plot_indicator("ADX + DI", ["adx", "+DI", "-DI"])
    plot_indicator("OBV", ["obv"])
    plot_indicator("Chaikin Money Flow (CMF)", ["cmf"])
    plot_indicator("Accumulation/Distribution (AD)", ["ad"])

except Exception as e:
    st.error(f"❌ Failed to load dashboard: {e}")