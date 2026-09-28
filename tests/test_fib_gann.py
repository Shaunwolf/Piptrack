"""Correctness tests for the Fibonacci & Gann suite and the composite indicators"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_technicals import path, bars  # noqa: E402
from test_pump_research import make_prices  # noqa: E402

from pump_research.technicals import fib_tools as ft
from pump_research.technicals.candles import detect_candles
from pump_research.technicals.composites import adaptive_kalman, fear_greed, sr_signals
from pump_research.technicals.fibonacci import all_time_fibonacci
from pump_research.technicals.harmonics import find_harmonics
from pump_research.technicals.pivots import Pivot
from pump_research.technicals.snapshot import technical_snapshot

A, B = Pivot(0, 100.0, "low", True), Pivot(50, 200.0, "high", True)
C = Pivot(70, 150.0, "low", False)


def test_trend_based_extension_projects_the_move_from_c():
    ext = ft.trend_fib_extension(A, B, C, close=311.8, tol=1.0, end_idx=90)
    assert ext["levels"]["1.618"] == pytest.approx(311.8)
    assert ext["nearest"] == 1.618 and ext["near"]


def test_extension_says_nothing_when_c_is_the_current_bar():
    c_now = Pivot(90, 150.0, "low", False)
    assert not ft.trend_fib_extension(A, B, c_now, close=150.0, tol=1.0, end_idx=90)["near"]


def test_retracement_ignores_the_anchor_points():
    assert not ft.fib_retracement(A, B, close=200.0, tol=0.5)["near"]      # sitting on B (level 0)
    assert ft.fib_retracement(A, B, close=138.2, tol=0.5)["near"]          # the 0.618 level


def test_time_zones_and_trend_time():
    tz = ft.fib_time_zones(A, B, end_idx=80)  # unit = 10 bars -> zones at 10, 20, 30, 50, 80, 130...
    assert tz["zones"][:6] == [10, 20, 30, 50, 80, 130] and tz["now"] and tz["bars_to_next"] == 0
    tt = ft.trend_fib_time(A, B, C, end_idx=120)  # C + 50 x ratios -> 1.0 lands on bar 120
    assert 120 in tt["lines"] and tt["now"]


def test_gann_fan_angles():
    fan = ft.gann_fan(A, B, end_idx=100, close=330.0, tol=1.0)  # 1x1 = 2 per bar from A
    assert fan["values_now"]["1x1"] == pytest.approx(300.0)
    assert fan["values_now"]["2x1"] == pytest.approx(500.0)
    assert fan["values_now"]["1x2"] == pytest.approx(200.0)
    assert fan["above_1x1"] and fan["zone"] == 5  # above 1x8, 1x4, 1x3, 1x2, 1x1


def test_gann_box_and_squares():
    box = ft.gann_box(A, B, end_idx=75, close=175.0, tol=1.0)
    assert box["price_fraction"] == pytest.approx(0.75) and box["near_price"]
    assert box["time_fraction"] == pytest.approx(1.5) and box["near_time"]
    sq = ft.gann_square(A, B, end_idx=25, close=175.0)
    assert sq["above_diagonal"] and sq["diagonal_gap"] == pytest.approx(0.25)
    fixed = ft.gann_square_fixed(A, B, end_idx=25, close=175.0, atr_at_a=2.0)
    assert fixed["side_bars"] == pytest.approx(50.0)


def test_speed_fan_circles_arcs_spiral_wedge_pitchfan():
    fan = ft.fib_speed_fan(A, B, end_idx=50, close=161.8, tol=0.5)  # at B's time the 0.618 line = 161.8
    assert fan["values_now"]["0.618"] == pytest.approx(161.8) and fan["near"]
    assert ft.fib_circles(A, B, end_idx=25, close=150.0)["ratio"] == pytest.approx(0.0)   # the centre
    assert ft.fib_speed_arcs(A, B, end_idx=50, close=200.0)["ratio"] == pytest.approx(0.0)  # B itself
    assert ft.fib_spiral(A, B, end_idx=50, close=200.0)["proximity"] == pytest.approx(0.0, abs=1e-9)
    wedge = ft.fib_wedge(A, B, Pivot(50, 120.0, "low", False), end_idx=40, close=150.0)
    assert wedge["inside"]
    pf = ft.pitchfan(A, B, C, end_idx=60, close=180.0, tol=0.5)
    assert pf["values_now"]["median"] == pytest.approx(100 + (175 - 100) * 60 / 60)
    assert pf["above_median"]


def test_confluence_is_rare_on_random_walks():
    """4+ tools agreeing should stay uncommon on data with no structure (guards against loose tolerances)"""
    hits = []
    for seed in range(4):
        df = make_prices("2020-01-01", 400, seed=200 + seed)
        hits += [technical_snapshot(df, end)["features"].get("ta_fib_confluence", 0) >= 4 for end in range(150, 399, 9)]
    assert np.mean(hits) < 0.15


def test_all_time_fibonacci():
    atf = all_time_fibonacci(path([50, 150, 100], bars_per_leg=20))
    assert atf["position"] == pytest.approx(0.5, abs=0.01) and atf["nearest_level"] == 0.5


def test_kalman_tracks_trend_and_reports_strength():
    up = pd.Series(np.linspace(10, 30, 120))
    k = adaptive_kalman(up)
    assert abs(k["kalman"].iloc[-1] - 30) < 1.0 and k["kalman_strength"].iloc[-1] > 20
    down = adaptive_kalman(pd.Series(np.linspace(30, 10, 120)))
    assert down["kalman_strength"].iloc[-1] < -20


def test_fear_greed_reads_the_tape():
    rng = np.random.default_rng(3)
    rally = path(list(np.linspace(10, 40, 260) * (1 + rng.normal(0, 0.003, 260))), bars_per_leg=1)
    slump = path(list(np.linspace(40, 10, 260) * (1 + rng.normal(0, 0.003, 260))), bars_per_leg=1)
    assert fear_greed(rally)["score"] > 60 and fear_greed(slump)["score"] < 40


def test_support_resistance_breakout_signal():
    rows = [[10, 10.4, 9.8, 10.0, 1e5]] * 25 + [[10.0, 11.2, 9.9, 11.0, 4e5]]
    sig = sr_signals(bars(rows), [{"price": 10.5, "touches": 3}], start_idx=20)
    assert [(s["name"], s["idx"]) for s in sig] == [("breakout_buy", 25)]


def test_more_candles():
    harami = [[12, 12.2, 10.8, 11.0, 1e5], [11.0, 11.2, 10.9, 11.0, 1e5], [11.8, 12.0, 11.7, 11.9, 1e5],
              [11.9, 11.95, 11.2, 11.3, 1e5], [11.4, 11.6, 11.35, 11.5, 1e5]]
    names = {(c["idx"], c["name"]) for c in detect_candles(bars(harami), 1, 4)}
    assert (4, "bullish_harami") in names
    methods = [[10, 10.1, 9.9, 10.0, 1e5], [10.0, 11.05, 9.95, 11.0, 1e5], [10.9, 10.95, 10.6, 10.7, 1e5],
               [10.7, 10.8, 10.5, 10.6, 1e5], [10.6, 10.7, 10.4, 10.5, 1e5], [10.5, 11.6, 10.45, 11.5, 1e5]]
    assert (5, "rising_three_methods") in {(c["idx"], c["name"]) for c in detect_candles(bars(methods), 1, 5)}


def test_five_zero_harmonic():
    kinds = ["low", "high", "low", "high", "low"]
    pts = [Pivot(i * 10, p, k, True) for i, (p, k) in enumerate(zip([100, 200, 70, 330, 200], kinds))]
    assert any(p["name"] == "five_zero" for p in find_harmonics(pts))
