# polling_wallet_monitor.py — Helius HTTP polling fallback

import threading
import requests
import time
import streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])
LOG_FILE = "/tmp/helius_poll_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def poll_wallet_transactions():
    try:
        api_key = st.secrets["HELIUS_API_KEY2"]
        wallet = st.secrets["SOLANA_WALLET"]
        url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={api_key}&limit=5"

        seen_signatures = set()

        while True:
            try:
                response = requests.get(url)
                response.raise_for_status()
                txs = response.json()
                
                print(f"🔍 Polled {len(data.get('transactions', []))} transactions...")


                for tx in txs:
                    sig = tx.get("signature")
                    if sig and sig not in seen_signatures:
                        TX_LOG.append(tx)
                        seen_signatures.add(sig)
                        log(f"✅ New transaction: {sig}")

                time.sleep(10)  # Poll every 10 seconds
            except Exception as e:
                log(f"❌ Polling error: {e}")
                time.sleep(15)  # Wait longer after error
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
