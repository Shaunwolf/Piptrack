"""Swing highs/lows (zigzag) and support/resistance levels built from them"""

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass
class Pivot:
    idx: int
    price: float
    kind: str          # 'high' or 'low'
    confirmed: bool    # False for the still-developing last swing


def zigzag(df: pd.DataFrame, pct: float = 0.05) -> List[Pivot]:
    """
    Alternating swing highs and lows: a swing is confirmed once price reverses
    by at least `pct` from the extreme. The final extreme is returned unconfirmed.
    """
    highs, lows = df["high"].to_numpy(float), df["low"].to_numpy(float)
    if len(df) < 2:
        return []
    pivots: List[Pivot] = []
    trend = None
    start = df["close"].iloc[0]
    ext_idx, ext_price = 0, start
    for i in range(1, len(df)):
        if trend is None:
            if highs[i] >= start * (1 + pct):
                pivots.append(Pivot(int(np.argmin(lows[:i + 1])), float(lows[:i + 1].min()), "low", True))
                trend, ext_idx, ext_price = "up", i, highs[i]
            elif lows[i] <= start * (1 - pct):
                pivots.append(Pivot(int(np.argmax(highs[:i + 1])), float(highs[:i + 1].max()), "high", True))
                trend, ext_idx, ext_price = "down", i, lows[i]
        elif trend == "up":
            if highs[i] > ext_price:
                ext_idx, ext_price = i, highs[i]
            elif lows[i] <= ext_price * (1 - pct):
                pivots.append(Pivot(ext_idx, float(ext_price), "high", True))
                trend, ext_idx, ext_price = "down", i, lows[i]
        else:
            if lows[i] < ext_price:
                ext_idx, ext_price = i, lows[i]
            elif highs[i] >= ext_price * (1 + pct):
                pivots.append(Pivot(ext_idx, float(ext_price), "low", True))
                trend, ext_idx, ext_price = "up", i, highs[i]
    if trend is not None:
        pivots.append(Pivot(ext_idx, float(ext_price), "high" if trend == "up" else "low", False))
    return pivots


def adaptive_pct(df: pd.DataFrame, lookback: int = 60, floor: float = 0.03, cap: float = 0.25) -> float:
    """Zigzag threshold scaled to the stock's volatility (2.5x median daily range)"""
    rng = ((df["high"] - df["low"]) / df["close"]).tail(lookback).median()
    if not rng or np.isnan(rng):
        return 0.05
    return float(min(cap, max(floor, 2.5 * rng)))


def support_resistance(pivots: List[Pivot], close: float, tolerance: float = 0.03, min_touches: int = 2):
    """Cluster pivot prices into levels; return nearest support below and resistance above the close"""
    prices = sorted(p.price for p in pivots if p.confirmed)
    clusters = []
    for price in prices:
        if clusters and price <= clusters[-1][-1] * (1 + tolerance):
            clusters[-1].append(price)
        else:
            clusters.append([price])
    levels = [{"price": float(np.mean(c)), "touches": len(c)} for c in clusters if len(c) >= min_touches]
    below = [lv for lv in levels if lv["price"] < close]
    above = [lv for lv in levels if lv["price"] > close]
    return {
        "levels": levels,
        "support": max(below, key=lambda lv: lv["price"]) if below else None,
        "resistance": min(above, key=lambda lv: lv["price"]) if above else None,
    }


def market_structure(pivots: List[Pivot]) -> dict:
    """Higher highs / higher lows count and overall structure from confirmed pivots"""
    highs = [p.price for p in pivots if p.kind == "high" and p.confirmed]
    lows = [p.price for p in pivots if p.kind == "low" and p.confirmed]
    hh = sum(1 for a, b in zip(highs, highs[1:]) if b > a)
    hl = sum(1 for a, b in zip(lows, lows[1:]) if b > a)
    lh = sum(1 for a, b in zip(highs, highs[1:]) if b < a)
    ll = sum(1 for a, b in zip(lows, lows[1:]) if b < a)
    structure = "range"
    if len(highs) >= 2 and len(lows) >= 2:
        if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
            structure = "uptrend"
        elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
            structure = "downtrend"
    return {"structure": structure, "higher_highs": hh, "higher_lows": hl, "lower_highs": lh, "lower_lows": ll,
            "last_swing_high": highs[-1] if highs else None, "last_swing_low": lows[-1] if lows else None}
