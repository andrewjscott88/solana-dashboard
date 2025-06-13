import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
from sol_trend import get_binance_sol_ohlcv, calc_indicators
from polling_wallet_monitor import init_wallet_monitor, TX_LOG
import requests
import os
import re

st.set_page_config(page_title="Solana Dashboard", layout="wide")

# === Hide Streamlit system UI and reset top padding
st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        .block-container {padding-top: 1rem;}
        .metric-label { font-size: 18px !important; font-weight: 500; }
        .chat-message { margin-bottom: 0.75rem; }
        .chat-message-user { color: #1f77b4; font-weight: bold; }
        .chat-message-bot { color: #2ca02c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# === Add centered Purple Team logo as banner (smaller size)
logo = Image.open("PTC.png")
st.image(logo, width=220)

# === Initialize wallet monitor
print("⚙️ Starting wallet monitor...")
init_wallet_monitor()
print("✅ Wallet monitor initialized.")

# === Trend evaluation and app logic

def evaluate_trend_by_category(df):
    latest = df.iloc[-1]
    categories = {
        "momentum": [
            ("MACD > Signal", latest["macd"] > latest["macd_signal"]),
            ("RSI > 50", latest["rsi"] > 50),
            ("CCI > 0", latest["cci"] > 0),
            ("ROC > 0", latest["roc"] > 0),
            ("UO > 50", latest["uo"] > 50),
            ("Stoch K > D", latest["stoch_k"] > latest["stoch_d"]),
            ("Williams %R > -50", latest["williams_r"] > -50),
        ],
        "trend": [
            ("Close > EMA20", latest["close"] > latest["ema_20"]),
            ("EMA20 > SMA50", latest["ema_20"] > latest["sma_50"]),
            ("Close > SMA20", latest["close"] > latest["sma_20"]),
            ("SMA20 > SMA50", latest["sma_20"] > latest["sma_50"]),
            ("Close > SMA200", latest["close"] > latest["sma_200"]),
            ("+DI > -DI", latest["+DI"] > latest["-DI"]),
            ("ADX > 20", latest["adx"] > 20),
        ],
        "volatility": [
            ("Close > SMA20", latest["close"] > latest["sma_20"]),
            ("Close > SMA50", latest["close"] > latest["sma_50"]),
            ("ADX > ADX avg", latest["adx"] > df["adx"].mean()),
        ],
        "volume": [
            ("OBV up", latest["obv"] > df["obv"].iloc[-2]),
            ("CMF > 0", latest["cmf"] > 0),
            ("AD up", latest["ad"] > df["ad"].iloc[-2]),
        ]
    }

    summary = {}
    total_bullish = 0
    total_bearish = 0

    for category, rules in categories.items():
        checks = {label: result for label, result in rules}
        bullish = sum(checks.values())
        bearish = len(checks) - bullish
        total_bullish += bullish
        total_bearish += bearish
        summary[category] = {
            "bullish": bullish,
            "bearish": bearish,
            "score": f"{bullish}/{len(checks)}",
            "details": checks
        }

    summary["overall"] = {
        "bullish_score": int(total_bullish),
        "bearish_score": int(total_bearish),
        "trend": "BULLISH" if total_bullish > total_bearish else "BEARISH"
    }
    return summary


def build_trend_summary(summary):
    lines = [
        f"Current trend: {summary['overall']['trend']}",
        f"Bullish indicators: {summary['overall']['bullish_score']}",
        f"Bearish indicators: {summary['overall']['bearish_score']}",
        ""
    ]
    for cat in ["momentum", "trend", "volatility", "volume"]:
        cat_summary = summary[cat]
        lines.append(f"{cat.capitalize()} ({cat_summary['score']}):")
        for label, result in cat_summary["details"].items():
            emoji = "✅" if result else "❌"
            lines.append(f"  {emoji} {label}")
        lines.append("")
    return "\n".join(lines)


try:
    with st.spinner("📡 Loading SOL trend data..."):
        df = get_binance_sol_ohlcv(limit=1000)
        df = calc_indicators(df)
        trend = evaluate_trend_by_category(df)

    st.title("📈 Solana (SOL) Trend Dashboard")
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
                bullish_ratio = trend[category]["bullish"] / len(trend[category]["details"])
                st.progress(bullish_ratio)
                with st.expander(f"{category.capitalize()} Details"):
                    for label, result in trend[category]["details"].items():
                        emoji = "✅" if result else "❌"
                        st.write(f"{emoji} {label}")

    st.subheader("📉 Price with SMAs")
    fig, ax = plt.subplots(figsize=(10, 4))
    df[["close", "sma_20", "sma_50", "sma_200"]].plot(ax=ax)
    ax.set_title("Price with SMAs")
    st.pyplot(fig)

    def plot_indicator(name, cols):
        if all(col in df.columns for col in cols):
            st.subheader(name)
            st.line_chart(df[cols])
        else:
            st.warning(f"{name} not available.")

    plot_indicator("RSI", ["rsi"])
    plot_indicator("MACD", ["macd", "macd_signal"])

except Exception as e:
    st.error(f"❌ Failed to load dashboard: {e}")

st.divider()
st.title("💬 Chat with TinyLlama")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Ask TinyLlama about the trend, crypto, or anything...")
if user_input:
    st.session_state.chat_history.append(("🧑", user_input))
    context = build_trend_summary(trend)
    prompt = f"""
### Market Context:
{context}

### User Question:
{user_input}

### Response (keep it focused and insightful):
"""
    try:
        tinyllama_url = st.secrets.get("TINYLLAMA_ENDPOINT")
        response = requests.post(
            tinyllama_url,
            json={"model": "tinyllama", "prompt": prompt, "stream": False}
        )
        reply = response.json()["response"]
    except Exception as e:
        reply = f"⚠️ Error connecting to TinyLlama: {e}"
    st.session_state.chat_history.append(("🤖", reply))

for speaker, msg in st.session_state.chat_history:
    st.markdown(f"**{speaker}**: {msg}")

st.subheader("🪵 Wallet Debug Log")
log_path = "/tmp/helius_poll_log.txt"
if os.path.exists(log_path):
    with open(log_path) as f:
        raw_log = f.read()
        sanitized_log = re.sub(r"api-key=[\w\-]+", "api-key=***REDACTED***", raw_log)
        st.code(sanitized_log, language="text")
        st.download_button("Download Log", sanitized_log, file_name="helius_log.txt")
else:
    st.info("No log file yet.")
