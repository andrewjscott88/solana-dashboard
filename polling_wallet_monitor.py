import threading, requests, time, streamlit as st

TX_LOG = st.session_state.setdefault("wallet_log", [])
LOG_FILE = "/tmp/helius_poll_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def poll_wallet_transactions():
    log("🚀 poll_wallet_transactions() started.")
    try:
        api_key = st.secrets["HELIUS_API_KEY"]
        wallet = st.secrets["SOLANA_WALLET"]

        seen = set()
        while True:
            try:
                # 1️⃣ Fetch recent signature list via JSON-RPC
                rpc_resp = requests.post(
                    "https://mainnet.helius-rpc.com/",
                    json={"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":[wallet,{"limit":5}]}
                )
                rpc_resp.raise_for_status()
                sigs = [item["signature"] for item in rpc_resp.json().get("result", [])]
                log(f"🔍 Got {len(sigs)} signatures")

                if sigs:
                    # 2️⃣ POST to decode transactions
                    url = f"https://api.helius.xyz/v0/transactions?api-key={api_key}"
                    log(f"🌐 Decoding via POST to {url}")
                    dec_resp = requests.post(url, json={"transactions": sigs})
                    dec_resp.raise_for_status()
                    decs = dec_resp.json()
                    log(f"✅ Decoded {len(decs)} transactions")

                    for tx in decs:
                        sig = tx.get("signature")
                        if sig and sig not in seen:
                            seen.add(sig)
                            TX_LOG.append(tx)
                            log(f"🟢 New decoded TX: {sig}")

                time.sleep(10)
            except Exception as e:
                log(f"❌ Polling error: {e}")
                time.sleep(15)
    except Exception as e:
        log(f"❌ Setup error: {e}")

def init_wallet_monitor():
    if "wallet_thread" not in st.session_state:
        threading.Thread(target=poll_wallet_transactions, daemon=True).start()
        st.session_state.wallet_thread = True
        log("✅ Wallet polling thread started.")
