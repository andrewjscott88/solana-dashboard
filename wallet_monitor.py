import threading
import websocket
import json
import streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])

def on_message(ws, message):
    print("📨 Raw WebSocket message received:")
    print(message)
    data = json.loads(message)
    if data.get("type") == "transaction":
        TX_LOG.append(data)
        print("✅ Transaction appended to TX_LOG")
    else:
        print("ℹ️ Non-transaction message:", data)

def on_open(ws):
    try:
        HELIUS_API_KEY = st.secrets["HELIUS_API_KEY"]
        WALLET_ADDRESS = st.secrets["SOLANA_WALLET"]
        print(f"🔌 Connected to WebSocket. Subscribing to {WALLET_ADDRESS}")
        subscribe_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "transactionSubscribe",
            "params": {
                "account": WALLET_ADDRESS,
                "apiKey": HELIUS_API_KEY,
                "commitment": "confirmed"
            }
        }
        ws.send(json.dumps(subscribe_msg))
        print("📤 Subscription message sent to Helius")
    except Exception as e:
        print("❌ Error in on_open:", e)

def start_wallet_monitor():
    try:
        HELIUS_API_KEY = st.secrets["HELIUS_API_KEY"]
        ws_url = f"wss://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"
        print(f"🌐 Connecting to {ws_url}")
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open)
        ws.run_forever()
    except Exception as e:
        print("❌ Error in start_wallet_monitor:", e)

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        print("🧵 Starting wallet monitor thread...")
        thread = threading.Thread(target=start_wallet_monitor)
        thread.daemon = True
        thread.start()
        st.session_state.wallet_thread = thread
