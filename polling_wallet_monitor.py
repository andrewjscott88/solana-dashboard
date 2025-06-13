import threading, requests, time, streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])
LOG_FILE = "/tmp/helius_poll_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def poll_wallet_transactions():
    log("🚀 poll_wallet_transactions() started.")
    api_key = st.secrets["HELIUS_API_KEY"]
    wallet = st.secrets["SOLANA_WALLET"]
    # Try both URL formats if needed
    url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions/?api-key={api_key}"
    # url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions/?api-key={api_key}"

    seen = set()
    while True:
        try:
            log(f"🌐 Polling URL: {url}")
            resp = requests.get(url)
            if resp.status_code == 400:
                log("❌ Bad Request 400 — check wallet/API key validity")
                time.sleep(30)
                continue
            resp.raise_for_status()
            txs = resp.json()
            log(f"🔍 Retrieved {len(txs)} tx(s)")

            for tx in txs:
                sig = tx.get("signature")
                if sig and sig not in seen:
                    seen.add(sig)
                    TX_LOG.append(tx)
                    log(f"✅ New transaction: {sig}")
            time.sleep(10)
        except Exception as e:
            log(f"❌ Polling error: {e}")
            time.sleep(15)

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        threading.Thread(target=poll_wallet_transactions, daemon=True).start()
        st.session_state.wallet_thread = True
        log("✅ Wallet polling thread started.")
