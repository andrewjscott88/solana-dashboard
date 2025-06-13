import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
from sol_trend import get_binance_sol_ohlcv, calc_indicators
from polling_wallet_monitor import init_wallet_monitor, TX_LOG
import requests
import os
import re

st.set_page_config(page_title="Solana Dashboard", layout="wide")

# === Hide Streamlit system UI and reset top padding
st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        .block-container {padding-top: 1rem;}
        .metric-label { font-size: 18px !important; font-weight: 500; }
        .chat-message { margin-bottom: 0.75rem; }
        .chat-message-user { color: #1f77b4; font-weight: bold; }
        .chat-message-bot { color: #2ca02c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# === Add centered Purple Team logo as banner (smaller size)
logo = Image.open("PTC.png")
st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <img src='PTC.png' width='220'/>
    </div>
""", unsafe_allow_html=True)

# === Initialize wallet monitor
print("⚙️ Starting wallet monitor...")
init_wallet_monitor()
print("✅ Wallet monitor initialized.")

# === Define trend evaluation logic
... (no change to rest of code) ...
