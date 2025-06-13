import threading
import websocket
import json
import streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "transaction":
            TX_LOG.append(data)
            print("✅ Transaction appended to TX_LOG")
        else:
            print("📨 Non-transaction message:", data)
    except Exception as e:
        print("❌ Failed to process message:", e)

def on_open(ws):
    try:
        HELIUS_API_KEY = st.secrets["HELIUS_API_KEY"]
        WALLET_ADDRESS = st.secrets["SOLANA_WALLET"]
        print(f"🔌 Subscribing to transactions for {WALLET_ADDRESS}")

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
        print("📤 Helius subscription message sent.")
    except Exception as e:
        print("❌ Error in on_open:", e)

def start_wallet_monitor():
    try:
        HELIUS_API_KEY = st.secrets["HELIUS_API_KEY"]
        ws_url = f"wss://rpc.helius.xyz/v0/stream/{HELIUS_API_KEY}"
        print(f"🌐 Connecting to {ws_url}")
        ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        ws.run_forever()
    except Exception as e:
        print("❌ Error starting wallet monitor:", e)

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        print("🧵 Launching wallet monitor thread...")
        try:
            thread = threading.Thread(target=start_wallet_monitor)
            thread.daemon = True
            thread.start()
            st.session_state.wallet_thread = thread
            print("✅ Wallet monitor thread started.")
        except Exception as e:
            print("❌ Failed to start wallet monitor thread:", e)
