import requests
import pandas as pd
import numpy as np

def get_binance_sol_ohlcv(limit=1000):
    url = "https://api.binance.us/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
        "interval": "1h",
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
    if len(df) < 250:
        raise ValueError("Not enough data to calculate all indicators (need at least 250 rows)")

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

    # ROC
    df["roc"] = df["close"].pct_change(periods=12) * 100

    # CCI
    tp = (df["high"] + df["low"] + df["close"]) / 3
    ma = tp.rolling(20).mean()
    md = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())))
    df["cci"] = (tp - ma) / (0.015 * md)

    # UO
    bp = df["close"] - df[["low", "close"]].min(axis=1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs()
    ], axis=1).max(axis=1)

    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum()
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
    df["uo"] = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7

    # Stochastic Oscillator
    lowest_low = df["low"].rolling(14).min()
    highest_high = df["high"].rolling(14).max()
    df["stoch_k"] = 100 * ((df["close"] - lowest_low) / (highest_high - lowest_low))
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()

    # Williams %R
    df["williams_r"] = -100 * ((highest_high - df["close"]) / (highest_high - lowest_low))

    # ADX / DMI
    plus_dm = df["high"].diff()
    minus_dm = df["low"].diff().abs()
    tr = df[["high", "low", "close"]].apply(lambda x: max(
        x["high"] - x["low"],
        abs(x["high"] - x["close"]),
        abs(x["low"] - x["close"])
    ), axis=1)
    atr = tr.rolling(14).mean()
    df["+DI"] = 100 * (plus_dm.rolling(14).mean() / atr)
    df["-DI"] = 100 * (minus_dm.rolling(14).mean() / atr)
    df["adx"] = abs(df["+DI"] - df["-DI"]).rolling(14).mean()

    # OBV
    df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()

    # CMF
    mfm = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"])
    mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
    mfv = mfm * df["volume"]
    df["cmf"] = mfv.rolling(20).sum() / df["volume"].rolling(20).sum()

    # A/D Line
    clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"])
    clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
    df["ad"] = (clv * df["volume"]).cumsum()

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