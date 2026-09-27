"""Fibonacci retracements and extensions of the dominant swing"""

import pandas as pd

RETRACEMENTS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
EXTENSIONS = (1.272, 1.618, 2.0, 2.618, 3.618, 4.236)


def fibonacci_levels(df: pd.DataFrame, lookback: int = 120) -> dict:
    """
    Take the highest high and lowest low of the lookback as the swing.
    - Upswing (low came first): retracement = how far price has pulled back from the high.
    - Downswing (high came first): retracement = how far price has bounced off the low.
    Extensions project the swing's range from the low (upside targets).
    """
    seg = df.tail(lookback)
    if len(seg) < 5:
        return {}
    hi_pos, lo_pos = int(seg["high"].to_numpy().argmax()), int(seg["low"].to_numpy().argmin())
    high, low = float(seg["high"].iloc[hi_pos]), float(seg["low"].iloc[lo_pos])
    rng = high - low
    if rng <= 0:
        return {}
    close = float(seg["close"].iloc[-1])
    direction = "up" if lo_pos < hi_pos else "down"
    retracement = (high - close) / rng if direction == "up" else (close - low) / rng
    nearest = min(RETRACEMENTS, key=lambda lv: abs(lv - retracement))

    if direction == "up":
        levels = {f"{lv:g}": high - rng * lv for lv in RETRACEMENTS}
    else:
        levels = {f"{lv:g}": low + rng * lv for lv in RETRACEMENTS}
    return {
        "direction": direction,
        "swing_high": high, "swing_low": low,
        "swing_high_date": seg.index[hi_pos], "swing_low_date": seg.index[lo_pos],
        "retracement": float(retracement),
        "nearest_level": nearest,
        "distance_to_nearest": float(abs(retracement - nearest)),
        # Classic reversal zone for a pullback in an upswing (0.618-0.65, with a little tolerance for wicks)
        "in_golden_pocket": direction == "up" and 0.61 <= retracement <= 0.66,
        "levels": levels,
        "extensions": {f"{e:g}": low + rng * e for e in EXTENSIONS},
    }


def extension_multiple(price: float, fib: dict):
    """Where a price sits on the swing's extension scale (1.0 = swing high, 1.618 = the 1.618 extension)"""
    if not fib:
        return None
    rng = fib["swing_high"] - fib["swing_low"]
    return (price - fib["swing_low"]) / rng if rng > 0 else None
