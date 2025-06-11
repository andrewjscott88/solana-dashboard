import streamlit as st
import matplotlib.pyplot as plt
from sol_trend import get_binance_sol_ohlcv, calc_indicators


def evaluate_trend_by_category(df):
    latest = df.iloc[-1]
    categories = {
        "momentum": [
            latest["macd"] > latest["macd_signal"],
            latest["rsi"] > 50,
            latest["cci"] > 0,
            latest["roc"] > 0,
            latest["uo"] > 50,
            latest["stoch_k"] > latest["stoch_d"],
            latest["williams_r"] > -50,
        ],
        "trend": [
            latest["close"] > latest["ema_20"],
            latest["ema_20"] > latest["sma_50"],
            latest["close"] > latest["sma_20"],
            latest["sma_20"] > latest["sma_50"],
            latest["close"] > latest["sma_200"],
            latest["+DI"] > latest["-DI"],
            latest["adx"] > 20,
        ],
        "volatility": [
            latest["close"] > latest["sma_20"],
            latest["close"] > latest["sma_50"],
            latest["adx"] > df["adx"].mean(),
        ],
        "volume": [
            latest["obv"] > df["obv"].iloc[-2],
            latest["cmf"] > 0,
            latest["ad"] > df["ad"].iloc[-2],
        ]
    }

    summary = {}
    total_bullish = 0
    total_bearish = 0

    for category, checks in categories.items():
        bullish = sum(checks)
        bearish = len(checks) - bullish
        total_bullish += bullish
        total_bearish += bearish
        summary[category] = {
            "bullish": bullish,
            "bearish": bearish,
            "score": f"{bullish}/{len(checks)}"
        }

    summary["overall"] = {
        "bullish_score": int(total_bullish),
        "bearish_score": int(total_bearish),
        "trend": "BULLISH" if total_bullish > total_bearish else "BEARISH"
    }

    return summary

st.set_page_config(page_title="📊 Solana Trend Dashboard", layout="wide")
st.title("📈 Solana (SOL) Trend Dashboard")

try:
    df = get_binance_sol_ohlcv(limit=1000)
    df = calc_indicators(df)
    trend = evaluate_trend_by_category(df)

    st.subheader("🌿 Overall Trend Summary")
    st.metric("Bullish Signals", trend["overall"]["bullish_score"])
    st.metric("Bearish Signals", trend["overall"]["bearish_score"])
    st.metric("Trend", trend["overall"]["trend"])

    st.subheader("📁 Category Breakdown")
    cols = st.columns(2)
    for i, category in enumerate(["momentum", "trend", "volatility", "volume"]):
        if category in trend:
            with cols[i % 2]:
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
