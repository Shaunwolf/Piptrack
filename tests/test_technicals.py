"""Correctness tests for the technical analysis engine on hand-built price paths"""

import numpy as np
import pandas as pd
import pytest

from pump_research.technicals import indicators as ind
from pump_research.technicals.candles import detect_candles
from pump_research.technicals.chart_patterns import double_bottom_top, flags, head_and_shoulders
from pump_research.technicals.fibonacci import fibonacci_levels, extension_multiple
from pump_research.technicals.harmonics import find_harmonics
from pump_research.technicals.pivots import Pivot, zigzag, market_structure
from pump_research.technicals.snapshot import technical_snapshot


def path(points, bars_per_leg=10, noise=0.0, seed=0):
    """OHLCV frame that walks linearly through the given prices"""
    closes = []
    for a, b in zip(points, points[1:]):
        closes.extend(np.linspace(a, b, bars_per_leg, endpoint=False))
    closes.append(points[-1])
    closes = np.array(closes, float)
    if noise:
        closes *= 1 + np.random.default_rng(seed).normal(0, noise, len(closes))
    dates = [d.date() for d in pd.bdate_range("2021-01-04", periods=len(closes))]
    opens = np.r_[closes[0], closes[:-1]]
    return pd.DataFrame({"open": opens, "high": np.maximum(opens, closes) * 1.001,
                         "low": np.minimum(opens, closes) * 0.999, "close": closes,
                         "volume": np.full(len(closes), 1e5)}, index=dates)


def bars(rows):
    dates = [d.date() for d in pd.bdate_range("2021-01-04", periods=len(rows))]
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=dates)


# --- Moving averages and oscillators -----------------------------------------

def test_weighted_moving_average_weights_recent_bars_more():
    s = pd.Series(np.arange(1, 11, dtype=float))
    assert ind.wma(s, 10).iloc[-1] == pytest.approx(385 / 55)  # sum(i*i)/sum(i)
    assert ind.sma(s, 10).iloc[-1] == pytest.approx(5.5)
    assert ind.wma(s, 10).iloc[-1] > ind.sma(s, 10).iloc[-1]


def test_ema_and_hull_track_trend():
    s = pd.Series(np.arange(1, 101, dtype=float))
    assert ind.ema(s, 10).iloc[-1] == pytest.approx(100 - 4.5, abs=0.01)  # lag (n-1)/2 on a linear trend
    assert abs(ind.hma(s, 20).iloc[-1] - 100) < 1  # Hull nearly removes lag
    assert ind.ema(s, 10).iloc[:8].isna().all()


def test_vwma_weights_by_volume():
    close = pd.Series([10.0, 20.0])
    volume = pd.Series([1.0, 3.0])
    assert ind.vwma(close, volume, 2).iloc[-1] == pytest.approx(17.5)


def test_rsi_extremes():
    up = pd.Series(np.arange(1, 40, dtype=float))
    down = up[::-1].reset_index(drop=True)
    assert ind.rsi(up).iloc[-1] == 100
    assert ind.rsi(down).iloc[-1] < 5


def test_bollinger_squeeze_flags_compression():
    rng = np.random.default_rng(1)
    wide = 10 * np.cumprod(1 + rng.normal(0, 0.04, 150))
    tight = wide[-1] * (1 + rng.normal(0, 0.002, 30))
    df = path(list(np.r_[wide, tight]), bars_per_leg=1)
    assert technical_snapshot(df, len(df) - 1)["features"]["ta_bb_squeeze"] is True


# --- Swings, structure, Fibonacci ----------------------------------------------

def test_zigzag_finds_swings():
    df = path([10, 20, 14, 24, 18])
    pv = zigzag(df, 0.1)
    assert [p.kind for p in pv] == ["low", "high", "low", "high", "low"]
    assert [round(p.price) for p in pv[1:4]] == [20, 14, 24]
    assert market_structure(pv)["structure"] == "uptrend"


def test_fibonacci_golden_pocket_pullback():
    df = path([100, 200, 138.5], bars_per_leg=20)
    fib = fibonacci_levels(df)
    assert fib["direction"] == "up"
    assert fib["retracement"] == pytest.approx(0.618, abs=0.01)
    assert fib["in_golden_pocket"]
    assert fib["extensions"]["1.618"] == pytest.approx(fib["swing_low"] + 1.618 * (fib["swing_high"] - fib["swing_low"]))
    assert extension_multiple(fib["swing_high"], fib) == pytest.approx(1.0)


# --- Harmonics ----------------------------------------------------------------

def pivots(prices, first_kind="low"):
    kinds = [first_kind, "high" if first_kind == "low" else "low"]
    return [Pivot(i * 10, p, kinds[i % 2], True) for i, p in enumerate(prices)]


def test_bullish_gartley():
    # X=100, A=200, B=.618 retrace, C=.618 of AB, D=.786 retrace of XA
    found = find_harmonics(pivots([100, 200, 138.2, 176.4, 121.4]))
    names = {p["name"]: p for p in found}
    assert "gartley" in names
    assert names["gartley"]["direction"] == "bullish"
    assert names["gartley"]["ratios"]["ad_xa"] == pytest.approx(0.786, abs=0.001)


def test_bearish_bat():
    # Mirror image: X high, D is a swing high at .886 of XA
    found = find_harmonics(pivots([200, 100, 145, 115, 188.6], first_kind="high"))
    assert any(p["name"] == "bat" and p["direction"] == "bearish" for p in found)


def test_abcd_and_non_match():
    assert any(p["name"] == "abcd" for p in find_harmonics(pivots([100, 150, 120, 170])))
    assert find_harmonics(pivots([100, 101, 150, 151, 300])) == []


def test_harmonic_detected_end_to_end_from_prices():
    df = path([100, 200, 138.2, 176.4, 121.4, 125], bars_per_leg=12)
    snap = technical_snapshot(df, len(df) - 1, window_days=15)
    assert any(p["type"] == "harmonic" and p["name"] == "gartley" for p in snap["patterns"])
    assert snap["features"]["ta_harmonic_bullish_in_window"] >= 1


# --- Chart patterns -------------------------------------------------------------

def test_double_bottom_with_breakout():
    df = path([20, 10, 15, 10.1, 16], bars_per_leg=10)
    pv = zigzag(df, 0.1)
    found = double_bottom_top(pv, df["close"].to_numpy())
    db = [p for p in found if p["name"] == "double_bottom"]
    assert db and db[0]["breakout"] and db[0]["neckline"] == pytest.approx(15, rel=0.01)


def test_inverse_head_and_shoulders():
    pv = pivots([10, 14, 8, 14, 10.2, 15], first_kind="low")
    assert any(p["name"] == "inverse_head_shoulders" for p in head_and_shoulders(pv))


def test_bull_flag():
    # 30% pole in 6 bars, then a tight drift lower for 6 bars
    df = path([10, 10, 13, 12.4], bars_per_leg=6)
    assert flags(df, len(df) - 1)[0]["name"] == "bull_flag"


# --- Candlesticks -----------------------------------------------------------------

def test_candles():
    rows = [
        [12, 12.2, 11.4, 11.5, 1e5], [11.5, 11.6, 10.8, 10.9, 1e5], [10.9, 11.0, 10.2, 10.3, 1e5],
        [10.0, 10.35, 9.2, 10.3, 1e5],   # hammer after a decline
        [10.2, 10.25, 9.6, 9.7, 1e5],    # red
        [9.6, 10.6, 9.55, 10.5, 1e5],    # bullish engulfing
        [11.0, 11.5, 10.9, 11.4, 1e5],   # gap up
    ]
    names = {(c["idx"], c["name"]) for c in detect_candles(bars(rows), 1, 6)}
    assert (3, "hammer") in names
    assert (5, "bullish_engulfing") in names
    assert (6, "gap_up") in names


# --- Snapshot -----------------------------------------------------------------------

def test_snapshot_never_looks_ahead():
    df = path([10, 20, 15, 30], bars_per_leg=30, noise=0.01)
    cut = 70
    a = technical_snapshot(df, cut)["features"]
    b = technical_snapshot(df.iloc[:cut + 1], cut)["features"]
    assert a == b


def test_snapshot_handles_short_history():
    df = path([10, 12], bars_per_leg=20)
    feats = technical_snapshot(df, len(df) - 1)["features"]
    assert feats["ta_close_vs_ema200"] is None and feats["ta_rsi14"] is not None
