import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

def to_series(x):
    """Ensure input is 1D pandas Series"""
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    return x.squeeze()

def compute_features(df):
    df = df.copy()

    close = to_series(df["Close"])
    high = to_series(df["High"])
    low = to_series(df["Low"])

    df["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(close=close, window=50).ema_indicator()

    df["RSI"] = RSIIndicator(close=close, window=14).rsi()
    df["RSI_SLOPE"] = df["RSI"].diff(5)

    macd = MACD(close=close)
    df["MACD_HIST"] = macd.macd_diff()

    df["ADX"] = ADXIndicator(high=high, low=low, close=close).adx()
    df["ATR"] = AverageTrueRange(high=high, low=low, close=close).average_true_range()

    df["RET_20D"] = close.pct_change(20)
    df["RET_20D_ADJ"] = df["RET_20D"] / df["ATR"]

    df.dropna(inplace=True)
    return df
