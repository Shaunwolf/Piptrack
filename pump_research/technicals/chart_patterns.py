"""Classic chart patterns detected from pivots and recent price action"""

from typing import List

import numpy as np
import pandas as pd

from .pivots import Pivot


def _p(name, direction, start_idx, end_idx, **info):
    return {"type": "chart", "name": name, "direction": direction,
            "start_idx": int(start_idx), "completed_idx": int(end_idx), **info}


def double_bottom_top(pivots: List[Pivot], closes: np.ndarray, tol=0.03, min_gap=5, min_depth=0.05):
    out = []
    conf = [p for p in pivots if p.confirmed] + [p for p in pivots if not p.confirmed]
    for i in range(len(conf) - 2):
        p1, mid, p2 = conf[i], conf[i + 1], conf[i + 2]
        if p1.kind != p2.kind or mid.kind == p1.kind or p2.idx - p1.idx < min_gap:
            continue
        if abs(p2.price - p1.price) / p1.price > tol:
            continue
        if p1.kind == "low" and mid.price >= max(p1.price, p2.price) * (1 + min_depth):
            broke = bool((closes[p2.idx:] > mid.price).any())
            out.append(_p("double_bottom", "bullish", p1.idx, p2.idx, neckline=mid.price, breakout=broke))
        if p1.kind == "high" and mid.price <= min(p1.price, p2.price) * (1 - min_depth):
            broke = bool((closes[p2.idx:] < mid.price).any())
            out.append(_p("double_top", "bearish", p1.idx, p2.idx, neckline=mid.price, breakout=broke))
    return out


def head_and_shoulders(pivots: List[Pivot], tol=0.05, min_head=0.03):
    out = []
    for kind, name, direction in (("low", "inverse_head_shoulders", "bullish"), ("high", "head_shoulders", "bearish")):
        pts = [p for p in pivots if p.kind == kind]
        for ls, head, rs in zip(pts, pts[1:], pts[2:]):
            shoulders_match = abs(rs.price - ls.price) / ls.price <= tol
            if kind == "low":
                head_ok = head.price <= min(ls.price, rs.price) * (1 - min_head)
            else:
                head_ok = head.price >= max(ls.price, rs.price) * (1 + min_head)
            if shoulders_match and head_ok:
                out.append(_p(name, direction, ls.idx, rs.idx, head=head.price))
    return out


def _slope(points):
    """Least-squares slope of pivot prices per bar, relative to their mean price"""
    xs = np.array([p.idx for p in points], float)
    ys = np.array([p.price for p in points], float)
    return float(np.polyfit(xs, ys, 1)[0] / ys.mean())


def triangles_wedges(pivots: List[Pivot], end_idx: int, lookback=40, flat=0.0015):
    recent = [p for p in pivots if p.idx >= end_idx - lookback]
    highs = [p for p in recent if p.kind == "high"]
    lows = [p for p in recent if p.kind == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return []
    sh, sl = _slope(highs), _slope(lows)
    start = min(p.idx for p in recent)
    info = {"upper_slope": round(sh, 5), "lower_slope": round(sl, 5)}
    if abs(sh) < flat and sl > flat:
        return [_p("ascending_triangle", "bullish", start, end_idx, **info)]
    if sh < -flat and abs(sl) < flat:
        return [_p("descending_triangle", "bearish", start, end_idx, **info)]
    if sh < -flat and sl > flat:
        return [_p("symmetrical_triangle", "neutral", start, end_idx, **info)]
    if sh > flat and sl > flat and sl > sh:
        return [_p("rising_wedge", "bearish", start, end_idx, **info)]
    if sh < -flat and sl < -flat and sh < sl:
        return [_p("falling_wedge", "bullish", start, end_idx, **info)]
    return []


def flags(df: pd.DataFrame, end_idx: int, max_pole=10, min_pole_gain=0.15, flag_bars=(3, 15)):
    """Bull flag: sharp rise (pole) followed by a tight, flat-to-down consolidation"""
    closes = df["close"].to_numpy(float)
    highs, lows = df["high"].to_numpy(float), df["low"].to_numpy(float)
    out = []
    for flag_len in range(flag_bars[0], flag_bars[1] + 1):
        top = end_idx - flag_len
        if top - max_pole < 0:
            break
        base_idx = top - max_pole + int(np.argmin(closes[top - max_pole:top + 1]))
        gain = closes[top] / closes[base_idx] - 1
        if gain < min_pole_gain or top - base_idx < 2:
            continue
        pole_h = closes[top] - closes[base_idx]
        flag_hi, flag_lo = highs[top + 1:end_idx + 1].max(), lows[top + 1:end_idx + 1].min()
        drift = closes[end_idx] - closes[top]
        if flag_hi <= closes[top] * 1.03 and closes[top] - flag_lo <= 0.5 * pole_h and drift <= 0.1 * pole_h:
            out.append(_p("bull_flag", "bullish", base_idx, end_idx, pole_gain=round(float(gain), 3), flag_bars=flag_len))
            break
    return out


def cup_and_handle(df: pd.DataFrame, end_idx: int, lookback=80):
    """Rounded base with rims at similar heights and a shallow handle near the end"""
    seg = df["close"].iloc[max(0, end_idx - lookback):end_idx + 1].to_numpy(float)
    if len(seg) < 30:
        return []
    third = len(seg) // 3
    left_i = int(np.argmax(seg[:third]))
    bottom_i = third + int(np.argmin(seg[third:2 * third]))
    right_i = 2 * third + int(np.argmax(seg[2 * third:-3])) if len(seg) - 3 > 2 * third else None
    if right_i is None:
        return []
    left, bottom, right = seg[left_i], seg[bottom_i], seg[right_i]
    depth = 1 - bottom / left
    handle_low = seg[right_i:].min()
    handle_depth = (right - handle_low) / (right - bottom) if right > bottom else 1
    if 0.12 <= depth <= 0.5 and abs(right / left - 1) <= 0.06 and 0.05 <= handle_depth <= 0.35:
        offset = max(0, end_idx - lookback)
        return [_p("cup_and_handle", "bullish", offset + left_i, end_idx, depth=round(float(depth), 3))]
    return []


def ranges_and_breakouts(df: pd.DataFrame, end_idx: int, range_bars=10, breakout_lookback=20):
    out = []
    seg = df.iloc[max(0, end_idx - range_bars + 1):end_idx + 1]
    if len(seg) == range_bars:
        width = seg["high"].max() / seg["low"].min() - 1
        typical = ((df["high"] - df["low"]) / df["close"]).iloc[max(0, end_idx - 60):end_idx + 1].median()
        if width <= max(0.08, 3 * typical):
            out.append(_p("consolidation", "neutral", end_idx - range_bars + 1, end_idx, width=round(float(width), 3)))
    prior = df.iloc[max(0, end_idx - breakout_lookback):end_idx]
    if len(prior) == breakout_lookback:
        bar = df.iloc[end_idx]
        vol_ok = bar["volume"] >= 1.5 * prior["volume"].mean()
        if bar["close"] > prior["high"].max() and vol_ok:
            out.append(_p("range_breakout", "bullish", end_idx - breakout_lookback, end_idx))
        if bar["close"] < prior["low"].min() and vol_ok:
            out.append(_p("range_breakdown", "bearish", end_idx - breakout_lookback, end_idx))
    return out


def find_chart_patterns(df: pd.DataFrame, pivots: List[Pivot], end_idx: int) -> List[dict]:
    closes = df["close"].to_numpy(float)
    found = double_bottom_top(pivots, closes) + head_and_shoulders(pivots) + triangles_wedges(pivots, end_idx)
    found += cup_and_handle(df, end_idx)
    # Flags and breakouts can occur on any bar: check each recent bar
    for i in range(max(0, end_idx - 15), end_idx + 1):
        found += flags(df, i) + ranges_and_breakouts(df, i)
    # De-duplicate: one entry per (name, completion bar); ongoing states only keep their latest bar
    ongoing = {"consolidation"}
    latest = {p["name"]: p["completed_idx"] for p in found if p["name"] in ongoing}
    found = [p for p in found if p["name"] not in ongoing or p["completed_idx"] == latest[p["name"]]]
    seen, unique = set(), []
    for p in found:
        key = (p["name"], p["completed_idx"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique
