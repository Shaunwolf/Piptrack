"""Moving averages, oscillators, volatility and volume indicators"""

import numpy as np
import pandas as pd


# --- Moving averages ---------------------------------------------------------

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def wma(s: pd.Series, n: int) -> pd.Series:
    """Linearly weighted moving average: the most recent bar has weight n, the oldest weight 1"""
    weights = np.arange(1, n + 1, dtype=float)
    return s.rolling(n, min_periods=n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def hma(s: pd.Series, n: int) -> pd.Series:
    """Hull moving average: WMA(2*WMA(n/2) - WMA(n), sqrt(n)) - fast and smooth"""
    half, root = max(1, n // 2), max(1, int(np.sqrt(n)))
    return wma(2 * wma(s, half) - wma(s, n), root)


def vwma(close: pd.Series, volume: pd.Series, n: int) -> pd.Series:
    """Volume-weighted moving average"""
    return (close * volume).rolling(n, min_periods=n).sum() / volume.rolling(n, min_periods=n).sum()


# --- Oscillators -------------------------------------------------------------

def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0).where(gain.notna())


def macd(close: pd.Series, fast=12, slow=26, signal=9):
    line = ema(close, fast) - ema(close, slow)
    sig = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return line, sig, line - sig


def stochastic(df: pd.DataFrame, n=14, d=3):
    lo, hi = df["low"].rolling(n, min_periods=n).min(), df["high"].rolling(n, min_periods=n).max()
    k = 100 * (df["close"] - lo) / (hi - lo).replace(0, np.nan)
    return k, k.rolling(d, min_periods=d).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)


def atr(df: pd.DataFrame, n=14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def adx(df: pd.DataFrame, n=14):
    """Average directional index with +DI / -DI (trend strength and direction)"""
    up, down = df["high"].diff(), -df["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = atr(df, n)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False, min_periods=n).mean() / tr
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False, min_periods=n).mean() / tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False, min_periods=n).mean(), plus_di, minus_di


def bollinger(close: pd.Series, n=20, k=2.0):
    mid = sma(close, n)
    sd = close.rolling(n, min_periods=n).std()
    upper, lower = mid + k * sd, mid - k * sd
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    bandwidth = (upper - lower) / mid
    return upper, mid, lower, pct_b, bandwidth


# --- Volume ------------------------------------------------------------------

def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff()).fillna(0)
    return (direction * df["volume"]).cumsum()


def mfi(df: pd.DataFrame, n=14) -> pd.Series:
    """Money flow index: RSI weighted by volume"""
    tp = (df["high"] + df["low"] + df["close"]) / 3
    flow = tp * df["volume"]
    pos = flow.where(tp > tp.shift(1), 0.0).rolling(n, min_periods=n).sum()
    neg = flow.where(tp < tp.shift(1), 0.0).rolling(n, min_periods=n).sum()
    return 100 - 100 / (1 + pos / neg.replace(0, np.nan))


def cmf(df: pd.DataFrame, n=20) -> pd.Series:
    """Chaikin money flow: accumulation (+) vs distribution (-)"""
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    mfm = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / rng
    return (mfm.fillna(0) * df["volume"]).rolling(n, min_periods=n).sum() / df["volume"].rolling(n, min_periods=n).sum()


def rolling_vwap(df: pd.DataFrame, n=20) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).rolling(n, min_periods=n).sum() / df["volume"].rolling(n, min_periods=n).sum()


def crossed_above(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a > b) & (a.shift(1) <= b.shift(1))


def crossed_below(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))
