import threading
import websocket
import json
import streamlit as st
import os

TX_LOG = st.session_state.setdefault("wallet_log", [])

LOG_FILE = "/tmp/helius_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def on_message(ws, message):
    log("📨 Message received:")
    log(message)
    try:
        data = json.loads(message)
        if data.get("type") == "transaction":
            TX_LOG.append(data)
            log("✅ Transaction added to TX_LOG")
    except Exception as e:
        log(f"❌ Error parsing message: {e}")

def on_open(ws):
    try:
        HELIUS_API_KEY = st.secrets["HELIUS_API_KEY"]
        WALLET_ADDRESS = st.secrets["SOLANA_WALLET"]
        log(f"🔌 Subscribing to {WALLET_ADDRESS}")

        subscribe_msg = {
            "type": "subscribe",
            "channels": [
                {
                    "name": "transactions",
                    "accounts": [WALLET_ADDRESS]
                }
            ]
        }
        ws.send(json.dumps(subscribe_msg))
        log("📤 Helius subscription sent.")
    except Exception as e:
        log(f"❌ Error in on_open: {e}")

def start_wallet_monitor():
    try:
        HELIUS_API_KEY = st.secrets["HELIUS_API_KEY"]
        ws_url = f"wss://rpc.helius.xyz/v0/stream/{HELIUS_API_KEY}"
        log(f"🌐 Connecting to {ws_url}")
        ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        ws.run_forever()
    except Exception as e:
        log(f"❌ Error starting monitor: {e}")

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        log("🧵 Starting wallet monitor thread...")
        thread = threading.Thread(target=start_wallet_monitor)
        thread.daemon = True
        thread.start()
        st.session_state.wallet_thread = thread
        log("✅ Wallet monitor thread started.")
