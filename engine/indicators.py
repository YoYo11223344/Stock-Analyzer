import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, ADXIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


def ensure_series(x):
    """
    Convert input into a clean pandas Series.
    Prevents numpy.float64 / scalar crashes.
    """
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]

    if isinstance(x, pd.Series):
        return x.astype(float)

    return pd.Series(x).astype(float)


def validate_dataframe(df):
    required_cols = ["Open", "High", "Low", "Close"]

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    if len(df) < 60:
        raise ValueError(f"Not enough data: {len(df)} rows (need >= 60)")


def compute_features(df):
    """
    Compute technical indicators safely.
    Expects full OHLCV historical dataframe.
    """

    df = df.copy()

    # 🔒 Validate input
    validate_dataframe(df)

    # 🔒 Force numeric stability
    close = ensure_series(df["Close"])
    high = ensure_series(df["High"])
    low = ensure_series(df["Low"])

    # Extra safety (prevents hidden string/object issues)
    close = pd.to_numeric(close, errors="coerce")
    high = pd.to_numeric(high, errors="coerce")
    low = pd.to_numeric(low, errors="coerce")

    # Drop rows with invalid data early
    df = df.dropna(subset=["Close", "High", "Low"]).copy()

    # =========================
    # TREND INDICATORS
    # =========================
    df["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(close=close, window=50).ema_indicator()

    # =========================
    # MOMENTUM
    # =========================
    df["RSI"] = RSIIndicator(close=close, window=14).rsi()
    df["RSI_SLOPE"] = df["RSI"].diff(5)

    macd = MACD(close=close)
    df["MACD_HIST"] = macd.macd_diff()

    # =========================
    # TREND STRENGTH
    # =========================
    df["ADX"] = ADXIndicator(high=high, low=low, close=close).adx()

    # =========================
    # VOLATILITY
    # =========================
    df["ATR"] = AverageTrueRange(
        high=high,
        low=low,
        close=close
    ).average_true_range()

    # =========================
    # RETURNS
    # =========================
    df["RET_20D"] = close.pct_change(20)

    # Avoid division by zero
    df["RET_20D_ADJ"] = df["RET_20D"] / df["ATR"].replace(0, np.nan)

    # =========================
    # CLEANUP
    # =========================
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    if df.empty:
        raise ValueError("Indicator computation failed: empty output")

    return df
