
import threading
import websocket
import json
import streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])

def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "transaction":
        TX_LOG.append(data)

def on_open(ws):
    from streamlit.runtime.secrets import get_secret
    HELIUS_API_KEY = get_secret("HELIUS_API_KEY")
    WALLET_ADDRESS = get_secret("SOLANA_WALLET")
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

def start_wallet_monitor():
    from streamlit.runtime.secrets import get_secret
    HELIUS_API_KEY = get_secret("HELIUS_API_KEY")
    ws_url = f"wss://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open)
    ws.run_forever()

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        thread = threading.Thread(target=start_wallet_monitor)
        thread.daemon = True
        thread.start()
        st.session_state.wallet_thread = thread
