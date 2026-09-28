"""
Composite indicators: adaptive Kalman trend filter, support/resistance buy/sell
signals and a per-stock Fear & Greed index. Original implementations of these
widely used concepts.
"""

from typing import Dict, List

import numpy as np
import pandas as pd

from . import indicators as ind


# --- Adaptive Kalman trend filter ------------------------------------------------------

def adaptive_kalman(close: pd.Series, volatility_window: int = 20, base_q: float = 0.01) -> pd.DataFrame:
    """
    Two-state (level, slope) Kalman filter on price. Measurement noise follows
    recent return variance, and process noise scales with it, so the filter
    tightens in calm markets and loosens when volatility expands.
    Returns the filtered level, its slope per bar, and a trend strength in -100..100
    (slope relative to the typical daily move).
    """
    prices = close.to_numpy(float)
    n = len(prices)
    level, slope = np.full(n, np.nan), np.full(n, np.nan)
    if n == 0:
        return pd.DataFrame({"kalman": level, "kalman_slope": slope, "kalman_strength": slope}, index=close.index)
    vol = close.pct_change().rolling(volatility_window, min_periods=5).std().bfill().fillna(0.02).to_numpy() + 1e-6
    x = np.array([prices[0], 0.0])
    P = np.eye(2)
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    for i in range(n):
        scale = (vol[i] * prices[i]) ** 2
        Q = base_q * scale * np.array([[0.25, 0.5], [0.5, 1.0]])
        R = scale
        if i:
            x = F @ x
            P = F @ P @ F.T + Q
        y = prices[i] - (H @ x)[0]
        S = (H @ P @ H.T)[0, 0] + R
        K = (P @ H.T / S).ravel()
        x = x + K * y
        P = (np.eye(2) - np.outer(K, H)) @ P
        level[i], slope[i] = x[0], x[1]
    daily_move = pd.Series(vol * prices, index=close.index)
    strength = np.clip(100 * np.tanh(slope / daily_move.to_numpy()), -100, 100)
    return pd.DataFrame({"kalman": level, "kalman_slope": slope, "kalman_strength": strength}, index=close.index)


# --- Support/resistance buy & sell signals ------------------------------------------------

def sr_signals(df: pd.DataFrame, levels: List[Dict], start_idx: int, tol_atr: float = 0.5) -> List[Dict]:
    """
    Buy: close breaks above a resistance level on 1.5x volume, or bounces off support
    (low within tolerance, close back above). Sell: close breaks below support on
    volume, or is rejected at resistance (high within tolerance, close back below).
    """
    if not levels or len(df) < 21:
        return []
    atr = ind.atr(df)
    vol_avg = df["volume"].rolling(20, min_periods=5).mean().shift(1)
    out = []
    prices = sorted(lv["price"] for lv in levels)
    for i in range(max(1, start_idx), len(df)):
        bar, prev = df.iloc[i], df.iloc[i - 1]
        tol = tol_atr * (atr.iloc[i] if not pd.isna(atr.iloc[i]) else bar["close"] * 0.02)
        loud = not pd.isna(vol_avg.iloc[i]) and bar["volume"] >= 1.5 * vol_avg.iloc[i]
        for p in prices:
            if prev["close"] <= p < bar["close"] and loud:
                out.append({"type": "signal", "name": "breakout_buy", "direction": "bullish", "idx": i, "level": p})
            elif prev["close"] >= p > bar["close"] and loud:
                out.append({"type": "signal", "name": "breakdown_sell", "direction": "bearish", "idx": i, "level": p})
            elif abs(bar["low"] - p) <= tol and bar["close"] > p and bar["close"] > bar["open"] and prev["close"] > p - tol:
                out.append({"type": "signal", "name": "support_bounce_buy", "direction": "bullish", "idx": i, "level": p})
            elif abs(bar["high"] - p) <= tol and bar["close"] < p and bar["close"] < bar["open"] and prev["close"] < p + tol:
                out.append({"type": "signal", "name": "resistance_reject_sell", "direction": "bearish", "idx": i, "level": p})
    # One signal per bar and name
    seen, unique = set(), []
    for s in out:
        if (s["idx"], s["name"]) not in seen:
            seen.add((s["idx"], s["name"]))
            unique.append(s)
    return unique


# --- Fear & Greed (per stock) ---------------------------------------------------------------

def fear_greed(df: pd.DataFrame) -> Dict:
    """
    0 = extreme fear, 100 = extreme greed, the average of five 0-100 components:
    momentum (price vs its 50-day SMA, ±10% ≈ the extremes), strength (position in the
    52-week range), RSI, volatility (20-day vs the stock's own 1-year median; calmer =
    greedier) and volume pressure (share of the last 20 days' volume on up days).
    """
    close = df["close"]
    if len(df) < 30:
        return {}
    sma50 = ind.sma(close, min(50, len(df) - 1))
    momentum = close / sma50 - 1
    hi, lo = close.rolling(250, min_periods=20).max(), close.rolling(250, min_periods=20).min()
    strength = (close - lo) / (hi - lo).replace(0, np.nan)
    rsi = ind.rsi(close)
    vol = close.pct_change().rolling(20, min_periods=10).std()
    up_vol = (df["volume"] * (close.diff() > 0)).rolling(20, min_periods=10).sum()
    pressure = up_vol / df["volume"].rolling(20, min_periods=10).sum()
    vol_median = vol.iloc[-250:].median()
    vol_ratio = vol.iloc[-1] / vol_median if vol_median and not pd.isna(vol.iloc[-1]) else 1.0
    components = {
        "momentum": float(50 + 50 * np.tanh((momentum.iloc[-1] if not pd.isna(momentum.iloc[-1]) else 0) / 0.10)),
        "strength": float(strength.iloc[-1] * 100) if not pd.isna(strength.iloc[-1]) else 50.0,
        "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0,
        "volatility": float(50 - 50 * np.tanh((vol_ratio - 1) / 0.5)),
        "volume_pressure": float(pressure.iloc[-1] * 100) if not pd.isna(pressure.iloc[-1]) else 50.0,
    }
    score = float(np.mean(list(components.values())))
    label = ("extreme fear" if score < 25 else "fear" if score < 45 else "neutral" if score <= 55
             else "greed" if score <= 75 else "extreme greed")
    return {"score": score, "label": label, "components": components}
