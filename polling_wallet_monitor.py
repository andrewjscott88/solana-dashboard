import threading
import requests
import time
import streamlit as st
from collections import deque

TX_LOG = st.session_state.setdefault("wallet_log", [])
LOG_FILE = "/tmp/helius_poll_log.txt"
SEEN_SIGNATURES = deque(maxlen=100)  # Limits memory use

def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    full_msg = f"{timestamp} {msg}"
    #print(full_msg)
    with open(LOG_FILE, "a") as f:
        f.write(full_msg + "\n")

def poll_wallet_transactions():
    try:
        api_key = st.secrets["HELIUS_API_KEY"]
        wallet = st.secrets["SOLANA_WALLET"]

        url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={api_key}&limit=5"
        log(f"🌐 Polling URL: {url}")
        print("🚀 poll_wallet_transactions() started.")

        while True:
            try:
                response = requests.get(url)
                response.raise_for_status()

                data = response.json()
                if not isinstance(data, list):
                    log(f"⚠️ Unexpected response format: {data}")
                    continue

                for tx in data:
                    sig = tx.get("signature")
                    if sig and sig not in SEEN_SIGNATURES:
                        TX_LOG.append(tx)
                        SEEN_SIGNATURES.append(sig)
                        log(f"✅ New transaction: {sig}")

            except requests.exceptions.RequestException as e:
                try:
                    err_body = response.text
                except Exception:
                    err_body = "No response body"
                log(f"❌ Polling error: {e} | Response: {err_body}")

            time.sleep(10)

    except Exception as e:
        log(f"❌ Setup error: {e}")

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        log("🧵 Starting wallet polling thread...")
        thread = threading.Thread(target=poll_wallet_transactions)
        thread.daemon = True
        thread.start()
        st.session_state.wallet_thread = thread
        log("✅ Wallet polling thread started.")
