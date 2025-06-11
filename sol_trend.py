import requests
import pandas as pd
import numpy as np

def get_binance_sol_ohlcv(limit=1000):
    url = "https://api.binance.us/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
        "interval": "1m",
        "limit": limit
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Binance API error: {response.text}")
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "_", "_", "_", "quote_volume", "_", "_"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df

def calc_indicators(df):
    df["sma_20"] = df["close"].rolling(window=20).mean()
    df["sma_50"] = df["close"].rolling(window=50).mean()
    df["sma_200"] = df["close"].rolling(window=200).mean()
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    df.dropna(inplace=True)
    return df

def evaluate_trend_by_category(df):
    latest = df.iloc[-1]
    categories = {
        "momentum": [
            latest["macd"] > latest["macd_signal"],
            latest["rsi"] > 50,
        ],
        "trend": [
            latest["close"] > latest["ema_20"],
            latest["ema_20"] > latest["sma_50"],
            latest["close"] > latest["sma_200"],
        ]
    }

    summary = {}
    total_bullish = 0
    total_bearish = 0

    for category, checks in categories.items():
        bullish = sum(checks)
        bearish = len(checks) - bullish
        total_bullish += bullish
        total_bearish += bearish
        summary[category] = {
            "bullish": bullish,
            "bearish": bearish,
            "score": f"{bullish}/{len(checks)}"
        }

    summary["overall"] = {
        "bullish_score": int(total_bullish),
        "bearish_score": int(total_bearish),
        "trend": "BULLISH" if total_bullish > total_bearish else "BEARISH"
    }

    return summary