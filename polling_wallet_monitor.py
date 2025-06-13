import threading
import requests
import time
import streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])
LOG_FILE = "/tmp/helius_poll_log.txt"

def log(msg):
    # Save logs for debugging in the sidebar
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
    print(msg)

def poll_wallet_transactions():
    log("🚀 poll_wallet_transactions() started.")
    try:
        api_key = st.secrets["HELIUS_API_KEY2"]
        wallet = st.secrets["SOLANA_WALLET"]
        url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={api_key}"

        seen = set()
        while True:
            try:
                log(f"🌐 Polling URL: {url}")
                response = requests.get(url)
                if response.status_code == 400:
                    log("❌ Bad Request (400) — likely invalid wallet or API key")
                response.raise_for_status()

                transactions = response.json()  # returns list of tx dicts
                log(f"🔍 Retrieved {len(transactions)} transaction(s).")

                for tx in transactions:
                    sig = tx.get("signature")
                    if sig and sig not in seen:
                        seen.add(sig)
                        TX_LOG.append(tx)
                        log(f"✅ New transaction: {sig}")

                time.sleep(10)
            except Exception as e:
                log(f"❌ Polling error: {e}")
                time.sleep(15)
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
