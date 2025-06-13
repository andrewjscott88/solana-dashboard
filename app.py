import streamlit as st
import matplotlib.pyplot as plt
from sol_trend import get_binance_sol_ohlcv, calc_indicators
from polling_wallet_monitor import init_wallet_monitor, TX_LOG
import requests
import os
import re

st.set_page_config(page_title="📊 Solana Trend Dashboard", layout="wide")

print("⚙️ Calling init_wallet_monitor()...")
init_wallet_monitor()
print("✅ init_wallet_monitor() call completed.")

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

    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
    log_file = "trend_state.txt"

    def send_telegram_alert(summary):
        if not bot_token or not chat_id:
            return
        bullish_reasons = []
        bearish_reasons = []
        for category in ["momentum", "trend", "volatility", "volume"]:
            for label, result in summary[category]["details"].items():
                if result and len(bullish_reasons) < 3:
                    bullish_reasons.append(f"✅ {label}")
                elif not result and len(bearish_reasons) < 3:
                    bearish_reasons.append(f"❌ {label}")
        text = (
            f"📈 Trend Flip Alert!\n"
            f"New Trend: {summary['overall']['trend']}\n"
            f"Bullish: {summary['overall']['bullish_score']}\n"
            f"Bearish: {summary['overall']['bearish_score']}\n\n"
            f"🔼 Bullish Signals:\n" + "\n".join(bullish_reasons) + "\n\n"
            f"🔽 Bearish Signals:\n" + "\n".join(bearish_reasons)
        )
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text})

    def check_and_alert_trend(summary):
        new_trend = summary["overall"]["trend"]
        last_trend = None
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                last_trend = f.read().strip()
        if new_trend != last_trend:
            send_telegram_alert(summary)
            with open(log_file, "w") as f:
                f.write(new_trend)

    check_and_alert_trend(trend)

    st.title("📈 Solana (SOL) Trend Dashboard")
    st.subheader("🌿 Overall Trend Summary")
    st.metric("Bullish Signals", trend["overall"]["bullish_score"])
    st.metric("Bearish Signals", trend["overall"]["bearish_score"])
    st.metric("Trend", trend["overall"]["trend"])

    st.subheader("📁 Category Breakdown")
    for category in ["momentum", "trend", "volatility", "volume"]:
        if category in trend:
            cat_summary = trend[category]
            bullish = cat_summary["bullish"]
            total = len(cat_summary["details"])
            bullish_ratio = bullish / total

            with st.expander(f"📂 {category.capitalize()} — {bullish}/{total} bullish"):
                st.progress(bullish_ratio)
                for label, result in cat_summary["details"].items():
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        st.markdown("✅" if result else "❌")
                    with col2:
                        st.markdown(f"**{label}**")

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

    # Only keep RSI and MACD
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

# 🧼 Sanitize debug log before display
with st.sidebar.expander("🪵 Wallet Debug Log"):
    log_path = "/tmp/helius_poll_log.txt"
    if os.path.exists(log_path):
        with open(log_path) as f:
            raw_log = f.read()
            sanitized_log = re.sub(r'api-key=[\w-]+', 'api-key=***REDACTED***', raw_log)
            st.code(sanitized_log, language="text")
    else:
        st.info("No log file yet.")
