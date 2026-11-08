"""
The Fibonacci and Gann drawing tools, computed automatically for scans.

A trader drawing these by hand picks the anchor points; here they come from the
zigzag swings:
  A = start of the last completed swing, B = its end, C = the latest pullback
  (the developing swing point, or the last bar if there isn't one yet).

Round tools (circles, arcs, spiral, wedge) and fans use "swing units": time is
measured in multiples of the A→B duration and price in multiples of the A→B
range. That makes every result independent of chart zoom, which on a charting
platform changes how circles and angles look.

Every tool returns its geometry (for drawing) and where the latest close sits
relative to it (for scanning). `fib_gann_suite` runs them all and adds
confluence counts: how many tools put a level, or a time line, at the current bar.
"""

import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .pivots import Pivot

PHI = (1 + 5 ** 0.5) / 2
RETRACEMENT_LEVELS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
EXTENSION_LEVELS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.414, 1.618, 2.0, 2.618, 3.618, 4.236)
CHANNEL_LEVELS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618)
FIB_NUMBERS = (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233)
TIME_RATIOS = (0.382, 0.5, 0.618, 1.0, 1.382, 1.618, 2.0, 2.382, 2.618, 3.0, 3.618, 4.236)
SPEED_FAN_LEVELS = (0.25, 0.382, 0.5, 0.618, 0.75, 1.0)
ARC_LEVELS = (0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618)
PITCHFAN_LEVELS = (0.236, 0.382, 0.5, 0.618, 0.786)
GANN_BOX_LEVELS = (0.0, 0.25, 0.382, 0.5, 0.618, 0.75, 1.0)
GANN_ANGLES = (("1x8", 1 / 8), ("1x4", 1 / 4), ("1x3", 1 / 3), ("1x2", 1 / 2), ("1x1", 1.0),
               ("2x1", 2.0), ("3x1", 3.0), ("4x1", 4.0), ("8x1", 8.0))


def select_anchors(pivots: List[Pivot], end_idx: int, close: float):
    """A, B = last completed swing; C = developing swing point or the current bar"""
    confirmed = [p for p in pivots if p.confirmed]
    if len(confirmed) < 2:
        return None
    a, b = confirmed[-2], confirmed[-1]
    last = pivots[-1]
    c = last if not last.confirmed and last.idx > b.idx else Pivot(end_idx, close, "low" if b.kind == "high" else "high", False)
    if b.idx == a.idx or b.price == a.price:
        return None
    return a, b, c


def _nearest(value: float, levels) -> tuple:
    lvl = min(levels, key=lambda x: abs(x - value))
    return lvl, abs(value - lvl)


def _near_inner_level(close: float, levels: Dict[str, float], tol: float, anchors=("0", "1")) -> bool:
    """Near a level other than the anchor points themselves (price at a swing point is trivially 'at' 0 or 1)"""
    return any(abs(close - price) <= tol for name, price in levels.items() if name not in anchors)


# --- Price-level tools ----------------------------------------------------------------

def fib_retracement(a: Pivot, b: Pivot, close: float, tol: float) -> Dict:
    rng = b.price - a.price
    levels = {f"{r:g}": b.price - rng * r for r in RETRACEMENT_LEVELS}
    pos = (b.price - close) / rng
    lvl, _ = _nearest(pos, RETRACEMENT_LEVELS)
    return {"levels": levels, "position": pos, "nearest": lvl, "near": _near_inner_level(close, levels, tol)}


def trend_fib_extension(a: Pivot, b: Pivot, c: Pivot, close: float, tol: float, end_idx: int = None) -> Dict:
    """Three points: project the A→B move from C at extension ratios"""
    move = b.price - a.price
    levels = {f"{r:g}": c.price + move * r for r in EXTENSION_LEVELS}
    pos = (close - c.price) / move
    lvl, _ = _nearest(pos, EXTENSION_LEVELS)
    # With no developing swing, C is the current bar itself and the projection says nothing yet
    real_c = end_idx is None or c.idx < end_idx
    return {"levels": levels, "position": pos, "nearest": lvl,
            "near": real_c and _near_inner_level(close, levels, tol, anchors=("0",))}


def fib_channel(a: Pivot, b: Pivot, c: Pivot, end_idx: int, close: float, tol: float) -> Dict:
    """Trend line through A→B, channel width set by C, parallel lines at Fibonacci multiples of the width"""
    slope = (b.price - a.price) / (b.idx - a.idx)

    def base(i):
        return a.price + slope * (i - a.idx)

    width = c.price - base(c.idx)
    if width == 0:
        return {}
    pos = (close - base(end_idx)) / width
    lvl, _ = _nearest(pos, CHANNEL_LEVELS)
    level_now = base(end_idx) + width * lvl
    return {"slope": slope, "width": width, "position": pos, "nearest": lvl, "near": abs(close - level_now) <= tol,
            "lines": {f"{r:g}": [(a.idx, base(a.idx) + width * r), (end_idx, base(end_idx) + width * r)] for r in CHANNEL_LEVELS}}


# --- Time tools -----------------------------------------------------------------------

def fib_time_zones(a: Pivot, b: Pivot, end_idx: int) -> Dict:
    """Vertical lines at A + unit × Fibonacci numbers; the unit is a fifth of the A→B duration (at least one bar)"""
    unit = max(1, round((b.idx - a.idx) / 5))  # TradingView-style zones grow from a short base unit
    zones = [a.idx + unit * n for n in FIB_NUMBERS]
    future = [z - end_idx for z in zones if z >= end_idx]
    past = [end_idx - z for z in zones if z <= end_idx]
    return {"unit": unit, "zones": zones, "bars_to_next": future[0] if future else None,
            "bars_since_last": past[-1] if past else None, "now": end_idx in zones}


def trend_fib_time(a: Pivot, b: Pivot, c: Pivot, end_idx: int) -> Dict:
    """Three points: project the A→B duration from C at Fibonacci time ratios"""
    span = b.idx - a.idx
    lines = [round(c.idx + span * r) for r in TIME_RATIOS]
    future = [x - end_idx for x in lines if x >= end_idx]
    return {"lines": lines, "bars_to_next": future[0] if future else None, "now": end_idx in lines[3:]}


# --- Angle / fan tools (swing units) --------------------------------------------------------

def _to_units(a: Pivot, b: Pivot, idx: float, price: float):
    return (idx - a.idx) / (b.idx - a.idx), (price - a.price) / (b.price - a.price)


def _from_units(a: Pivot, b: Pivot, u: float, v: float):
    return a.idx + u * (b.idx - a.idx), a.price + v * (b.price - a.price)


def fib_speed_fan(a: Pivot, b: Pivot, end_idx: int, close: float, tol: float) -> Dict:
    """Fan lines from A through B's time at Fibonacci fractions of the move"""
    u, _ = _to_units(a, b, end_idx, close)
    if u <= 0:
        return {}
    values = {f"{r:g}": a.price + (b.price - a.price) * r * u for r in SPEED_FAN_LEVELS}
    up = b.price > a.price
    above = sum(1 for v in values.values() if (close > v if up else close < v))
    near = min(values.values(), key=lambda v: abs(v - close))
    return {"values_now": values, "lines_above_price": len(values) - above, "zone": above,
            "near": abs(close - near) <= tol,
            "lines": {k: [(a.idx, a.price), (end_idx, v)] for k, v in values.items()}}


def fib_speed_arcs(a: Pivot, b: Pivot, end_idx: int, close: float) -> Dict:
    """Arcs centred on B with radii at Fibonacci fractions of |AB| (swing units)"""
    u, v = _to_units(a, b, end_idx, close)
    d = math.hypot(u - 1, v - 1) / math.hypot(1, 1)
    lvl, dist = _nearest(d, ARC_LEVELS)
    return {"ratio": d, "nearest": lvl, "near": dist <= 0.02, "arcs": _circles(a, b, (1, 1), math.hypot(1, 1), ARC_LEVELS, end_idx)}


def fib_circles(a: Pivot, b: Pivot, end_idx: int, close: float) -> Dict:
    """Concentric circles centred on the midpoint of AB, radius = half of AB × Fibonacci ratios"""
    u, v = _to_units(a, b, end_idx, close)
    r0 = math.hypot(1, 1) / 2
    d = math.hypot(u - 0.5, v - 0.5) / r0
    lvl, dist = _nearest(d, ARC_LEVELS + (PHI + 1, 2 * PHI + 1))
    return {"ratio": d, "nearest": lvl, "near": dist <= 0.02, "circles": _circles(a, b, (0.5, 0.5), r0, ARC_LEVELS, end_idx)}


def _circles(a, b, centre, base_r, ratios, end_idx, points=48):
    out = {}
    for r in ratios:
        pts = []
        for k in range(points + 1):
            t = 2 * math.pi * k / points
            idx, price = _from_units(a, b, centre[0] + base_r * r * math.cos(t), centre[1] + base_r * r * math.sin(t))
            if a.idx <= idx <= end_idx:
                pts.append((idx, price))
        if pts:
            out[f"{r:g}"] = pts
    return out


def fib_spiral(a: Pivot, b: Pivot, end_idx: int, close: float) -> Dict:
    """Golden spiral centred on A passing through B: radius grows by φ every quarter turn"""
    u, v = _to_units(a, b, end_idx, close)
    r_now = math.hypot(u, v)
    if r_now == 0:
        return {}
    theta = math.atan2(v, u) - math.atan2(1, 1)
    growth = math.log(PHI) / (math.pi / 2)
    r_b = math.hypot(1, 1)
    # Spiral radius at this angle, over several windings; take the closest winding
    candidates = [r_b * math.exp(growth * (theta + 2 * math.pi * k)) for k in range(-3, 4)]
    r_s = min(candidates, key=lambda r: abs(math.log(r_now / r)))
    proximity = abs(math.log(r_now / r_s)) / math.log(PHI ** 4)  # 0 = on the spiral, 1 = a full winding away
    pts = []
    for k in range(0, 200):
        t = -2 * math.pi + k * (4 * math.pi / 200)
        r = r_b * math.exp(growth * t)
        idx, price = _from_units(a, b, r * math.cos(t + math.atan2(1, 1)), r * math.sin(t + math.atan2(1, 1)))
        if a.idx <= idx <= end_idx:
            pts.append((idx, price))
    return {"proximity": proximity, "near": proximity <= 0.04, "path": pts}


def fib_wedge(a: Pivot, b: Pivot, c: Pivot, end_idx: int, close: float) -> Dict:
    """Apex A, arms through B and C; Fibonacci arcs inside the wedge at fractions of |AB|"""
    u, v = _to_units(a, b, end_idx, close)
    uc, vc = _to_units(a, b, c.idx, c.price)
    ang_b, ang_c, ang = math.atan2(1, 1), math.atan2(vc, uc), math.atan2(v, u)
    lo, hi = sorted((ang_b, ang_c))
    inside = lo <= ang <= hi
    d = math.hypot(u, v) / math.hypot(1, 1)
    lvl, dist = _nearest(d, ARC_LEVELS)
    return {"ratio": d, "inside": inside, "nearest": lvl, "near": inside and dist <= 0.02}


def pitchfan(a: Pivot, b: Pivot, c: Pivot, end_idx: int, close: float, tol: float) -> Dict:
    """Andrews-style pitchfan: median line from A to the midpoint of BC, fan lines to Fibonacci points on BC"""
    def line_at(target_idx, target_price, i):
        if target_idx == a.idx:
            return target_price
        return a.price + (target_price - a.price) * (i - a.idx) / (target_idx - a.idx)

    points = {"median": ((b.idx + c.idx) / 2, (b.price + c.price) / 2)}
    for r in PITCHFAN_LEVELS:
        points[f"{r:g}"] = (b.idx + (c.idx - b.idx) * r, b.price + (c.price - b.price) * r)
    values = {k: line_at(ti, tp, end_idx) for k, (ti, tp) in points.items()}
    median = values["median"]
    spread = abs(line_at(b.idx, b.price, end_idx) - line_at(c.idx, c.price, end_idx)) / 2 or 1e-9
    near = min(values.values(), key=lambda x: abs(x - close))
    return {"values_now": values, "position": (close - median) / spread, "above_median": close > median,
            "near": abs(close - near) <= tol,
            "lines": {k: [(a.idx, a.price), (end_idx, v)] for k, v in values.items()}}


# --- Gann tools ------------------------------------------------------------------------------

def gann_box(a: Pivot, b: Pivot, end_idx: int, close: float, tol: float) -> Dict:
    """Box spanning A→B in time and price, divided at Gann/Fibonacci fractions on both axes"""
    tf = (end_idx - a.idx) / (b.idx - a.idx)
    pf = (close - a.price) / (b.price - a.price)
    plvl, _ = _nearest(pf, GANN_BOX_LEVELS)
    tlvl, tdist = _nearest(tf, GANN_BOX_LEVELS + (1.25, 1.382, 1.5, 1.618, 1.75, 2.0))
    levels = {f"{r:g}": a.price + (b.price - a.price) * r for r in GANN_BOX_LEVELS}
    return {"price_fraction": pf, "time_fraction": tf, "nearest_price_level": plvl, "nearest_time_level": tlvl,
            # Only the Gann-specific quarters count: 0.382/0.5/0.618 are the retracement's levels already
            "near_price": _near_inner_level(close, {k: v for k, v in levels.items() if k in ("0.25", "0.75")}, tol),
            "near_time": tlvl > 1 and tdist * (b.idx - a.idx) < 0.5,
            "levels": levels,
            "times": [round(a.idx + (b.idx - a.idx) * r) for r in GANN_BOX_LEVELS]}


def _gann_square_position(origin_idx, origin_price, side_bars, side_price, end_idx, close):
    """Position in a square of side (bars, price): its diagonal is the 1x1 line"""
    tf = (end_idx - origin_idx) / side_bars
    pf = (close - origin_price) / side_price
    eighth, _ = _nearest(pf % 1 if pf >= 0 else pf, [i / 8 for i in range(9)])
    return {"time_fraction": tf, "price_fraction": pf, "above_diagonal": pf > tf,
            "diagonal_gap": pf - tf, "nearest_eighth": eighth}


def gann_square(a: Pivot, b: Pivot, end_idx: int, close: float) -> Dict:
    """Square sized by the swing: side = A→B duration in time and A→B range in price"""
    return {"side_bars": b.idx - a.idx, "side_price": b.price - a.price,
            **_gann_square_position(a.idx, a.price, b.idx - a.idx, b.price - a.price, end_idx, close)}


def gann_square_fixed(a: Pivot, b: Pivot, end_idx: int, close: float, atr_at_a: float) -> Dict:
    """Square with a fixed price/time scale (1 bar = 1 ATR at A), side = the A→B price range"""
    if not atr_at_a:
        return {}
    side_price = b.price - a.price
    side_bars = max(1.0, abs(side_price) / atr_at_a)
    return {"side_bars": side_bars, "side_price": side_price, "scale_per_bar": atr_at_a,
            **_gann_square_position(a.idx, a.price, side_bars, side_price, end_idx, close)}


def gann_fan(a: Pivot, b: Pivot, end_idx: int, close: float, tol: float) -> Dict:
    """Gann angles from A; the 1x1 rises one swing-price unit per swing-time unit (the A→B slope)"""
    slope = (b.price - a.price) / (b.idx - a.idx)
    bars = end_idx - a.idx
    values = {name: a.price + slope * k * bars for name, k in GANN_ANGLES}
    up = slope > 0
    below_price = [name for name, v in values.items() if (close > v if up else close < v)]
    near = min(values.values(), key=lambda v: abs(v - close))
    return {"values_now": values, "zone": len(below_price), "above_1x1": (close > values["1x1"]) if up else (close < values["1x1"]),
            "near": abs(close - near) <= tol,
            "lines": {name: [(a.idx, a.price), (end_idx, v)] for name, v in values.items()}}


# --- Everything together ------------------------------------------------------------------------

def fib_gann_suite(df: pd.DataFrame, pivots: List[Pivot], atr: pd.Series) -> Optional[Dict]:
    end_idx = len(df) - 1
    close = float(df["close"].iloc[-1])
    anchors = select_anchors(pivots, end_idx, close)
    if not anchors:
        return None
    a, b, c = anchors
    atr_now = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else close * 0.03
    atr_a = float(atr.iloc[a.idx]) if not pd.isna(atr.iloc[a.idx]) else atr_now
    # Tight on purpose: with 11 tools and many levels, a loose tolerance would find "confluence" everywhere
    tol = min(0.2 * atr_now, 0.03 * abs(b.price - a.price))

    tools = {
        "retracement": fib_retracement(a, b, close, tol),
        "trend_extension": trend_fib_extension(a, b, c, close, tol, end_idx),
        "channel": fib_channel(a, b, c, end_idx, close, tol),
        "time_zones": fib_time_zones(a, b, end_idx),
        "speed_fan": fib_speed_fan(a, b, end_idx, close, tol),
        "trend_time": trend_fib_time(a, b, c, end_idx),
        "circles": fib_circles(a, b, end_idx, close),
        "spiral": fib_spiral(a, b, end_idx, close),
        "speed_arcs": fib_speed_arcs(a, b, end_idx, close),
        "wedge": fib_wedge(a, b, c, end_idx, close),
        "pitchfan": pitchfan(a, b, c, end_idx, close, tol),
        "gann_box": gann_box(a, b, end_idx, close, tol),
        "gann_square_fixed": gann_square_fixed(a, b, end_idx, close, atr_a),
        "gann_square": gann_square(a, b, end_idx, close),
        "gann_fan": gann_fan(a, b, end_idx, close, tol),
    }
    price_hits = [name for name, key in (("retracement", "near"), ("trend_extension", "near"), ("channel", "near"),
                                         ("speed_fan", "near"), ("circles", "near"), ("spiral", "near"),
                                         ("speed_arcs", "near"), ("wedge", "near"), ("pitchfan", "near"),
                                         ("gann_box", "near_price"), ("gann_fan", "near"))
                  if tools[name].get(key)]
    time_hits = [name for name, key in (("time_zones", "now"), ("trend_time", "now"), ("gann_box", "near_time"))
                 if tools[name].get(key)]
    return {"anchors": {k: {"idx": p.idx, "price": p.price, "kind": p.kind} for k, p in zip("ABC", (a, b, c))},
            "tools": tools, "price_confluence": price_hits, "time_confluence": time_hits}


def suite_features(suite: Optional[Dict]) -> Dict:
    """Flat ta_* features for statistics and scoring"""
    if not suite:
        return {}
    t = suite["tools"]

    def g(tool, key):
        v = t.get(tool, {}).get(key)
        return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v

    return {
        "ta_fib_confluence": len(suite["price_confluence"]),
        "ta_fib_time_confluence": len(suite["time_confluence"]),
        "ta_fib_ext_position": g("trend_extension", "position"),
        "ta_fib_ext_nearest": g("trend_extension", "nearest"),
        "ta_fib_ext_near": g("trend_extension", "near"),
        "ta_fib_channel_position": g("channel", "position"),
        "ta_fib_channel_near": g("channel", "near"),
        "ta_fib_timezone_bars_to_next": g("time_zones", "bars_to_next"),
        "ta_fib_timezone_now": g("time_zones", "now"),
        "ta_fib_trend_time_bars_to_next": g("trend_time", "bars_to_next"),
        "ta_fib_trend_time_now": g("trend_time", "now"),
        "ta_fib_speed_fan_zone": g("speed_fan", "zone"),
        "ta_fib_speed_fan_near": g("speed_fan", "near"),
        "ta_fib_circle_ratio": g("circles", "ratio"),
        "ta_fib_circle_near": g("circles", "near"),
        "ta_fib_spiral_proximity": g("spiral", "proximity"),
        "ta_fib_spiral_near": g("spiral", "near"),
        "ta_fib_arc_ratio": g("speed_arcs", "ratio"),
        "ta_fib_arc_near": g("speed_arcs", "near"),
        "ta_fib_wedge_ratio": g("wedge", "ratio"),
        "ta_fib_wedge_inside": g("wedge", "inside"),
        "ta_pitchfan_position": g("pitchfan", "position"),
        "ta_pitchfan_above_median": g("pitchfan", "above_median"),
        "ta_gann_box_price_fraction": g("gann_box", "price_fraction"),
        "ta_gann_box_time_fraction": g("gann_box", "time_fraction"),
        "ta_gann_box_near_price": g("gann_box", "near_price"),
        "ta_gann_square_diagonal_gap": g("gann_square", "diagonal_gap"),
        "ta_gann_square_above_diagonal": g("gann_square", "above_diagonal"),
        "ta_gann_fixed_diagonal_gap": g("gann_square_fixed", "diagonal_gap"),
        "ta_gann_fixed_above_diagonal": g("gann_square_fixed", "above_diagonal"),
        "ta_gann_fan_zone": g("gann_fan", "zone"),
        "ta_gann_above_1x1": g("gann_fan", "above_1x1"),
        "ta_gann_fan_near": g("gann_fan", "near"),
    }
