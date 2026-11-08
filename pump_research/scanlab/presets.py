"""Starter scans for each trading style. Every one is an ordinary spec the builder can edit."""

import copy
import json
import os
from typing import Dict

from .blocks_patterns import BULLISH_REVERSALS


def b(type_, weight=1, negate=False, **params):
    return {"type": type_, "params": params, "weight": weight, "negate": negate}


def g(name, logic, *blocks, min=1, weight=1):
    return {"name": name, "logic": logic, "min": min, "weight": weight, "blocks": list(blocks)}


PRESETS: Dict[str, Dict] = {
    "squeeze_setup": {
        "title": "Squeeze setup", "style": "squeeze",
        "tagline": "Short pressure + rising attention + a tight base, minus the pump-and-dump red flags.",
        "universe": {"lists": ["reg_sho", "trending", "meme", "pump_history"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Squeeze fuel", "atleast", b("reg_sho", 2, mode="streak", days=5),
              b("short_interest", 2, pct_float=20, days_to_cover=3, rising=False),
              b("short_volume", ratio=0.55, rising=True), min=1),
            g("Ignition", "atleast", b("mention_velocity", mentions=20, growth=2), b("gamma", condition="negative", pct=5, vol_oi=1),
              b("gamma", condition="hot_calls", pct=5, vol_oi=1), b("volume_awakening", recent=3, mult=1.5, quiet=20), min=1),
            g("Timing", "any", b("vcp", 2, contractions=3, last_max=8, first_max=35, lookback=80, status="setting_up", near=5,
                                 within=3, stage2=False, dry=True),
              b("ema_coil", fast=10, slow=21, spread=1.5, above50=True),
              b("harmonic_forming", patterns=["gartley", "bat", "butterfly", "crab", "deep_crab", "shark", "cypher"],
                direction="bullish", status="near", distance=4, tolerance=5, overlap=False, swing="auto"),
              b("breakout", side="up", lookback="20", volume=1.5, within=3)),
            g("Not a pump-and-dump", "all", b("clean_setup", min_price=1, min_cap=50, min_dollar_vol=2, options=True, exchange=True)),
        ]},
    },
    "candlestick_purist": {
        "title": "Candlestick purist", "style": "candlestick",
        "tagline": "Bullish reversal candles at support after a pullback, nothing else.",
        "universe": {"sectors": ["Information Technology"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("The candle", "all", b("candle_pattern", 2, patterns=BULLISH_REVERSALS, within=3, trend="decline", level="support",
                                     level_tol=3, volume=0, confirm=False)),
            g("Confirmation", "any", b("candle_shape", shape="long_lower_wick", within=3, ratio=2, color="any"),
              b("volume_spike", mult=1.5, avg=20, direction="any", within=3),
              b("heikin_ashi", condition="flip_up", within=3)),
        ]},
    },
    "harmonic_hunter": {
        "title": "Harmonic hunter", "style": "harmonic",
        "tagline": "Bullish XABCD patterns completing now or forming into their reversal zone.",
        "universe": {"sectors": ["Financials", "Industrials"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Pattern", "any", b("harmonic_forming", 2, patterns=["gartley", "bat", "butterfly", "crab", "deep_crab", "shark", "cypher"],
                                  direction="bullish", status="near", distance=4, tolerance=5, overlap=False, swing="auto"),
              b("harmonic_complete", 2, patterns=["gartley", "bat", "alt_bat", "butterfly", "crab", "deep_crab", "shark", "cypher",
                                                  "five_zero"], direction="bullish", within=6, tolerance=5, quality=50,
                swing="auto", holding=True)),
            g("Momentum agrees", "any", b("rsi", length=14, condition="below", level=40, within=3),
              b("divergence", source="rsi", kind="bull", within=12, swing="auto"),
              b("stochastic", k=14, d=3, condition="os_cross_up", oversold=20, overbought=80, within=4)),
        ]},
    },
    "fib_gann": {
        "title": "Fibonacci & Gann", "style": "fibonacci",
        "tagline": "Pullbacks into the golden pocket where several Fibonacci and Gann tools agree.",
        "universe": {"sectors": ["Health Care", "Consumer Discretionary"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Retracement", "all", b("fib_retracement", 2, levels=["golden", "0.5", "0.705"], anchor="last", context="pullback",
                                      tolerance=2, min_swing=8, swing="auto")),
            g("Confluence", "atleast", b("fib_gann_confluence", min_tools=3, time=False, swing="auto"),
              b("fib_tool_touch", tools=["fib_spiral", "fib_speed_resistance_arcs", "gann_fan", "pitchfan"], need="any", swing="auto"),
              b("fib_time", tool="either", bars=2, swing="auto"), min=1),
            g("Trend intact", "any", b("ma_position", kind="ema", length=200, condition="above", within=3, distance=1),
              b("structure", state="uptrend", within=5, swing="auto")),
        ]},
    },
    "momentum_breakout": {
        "title": "Momentum breakout", "style": "momentum",
        "tagline": "New highs on heavy volume with every average stacked behind them.",
        "universe": {"sectors": ["Information Technology", "Communication Services"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Breakout", "all", b("breakout", 2, side="up", lookback="50", volume=1.5, within=3)),
            g("Trend", "atleast", b("ma_ribbon", kind="ema", lengths="8,21,50,200", order="bullish", expanding=False),
              b("adx", level=20, length=14, direction="up", rising=False),
              b("relative_strength", bars=63, side="outperform", margin=5), min=2),
            g("Not overheated", "all", b("rsi", length=14, condition="below", level=80, within=3)),
        ]},
    },
    "squeeze_hunter": {
        "title": "Squeeze hunter", "style": "bollinger",
        "tagline": "Bollinger Bands coiled inside Keltner, then firing upward.",
        "universe": {"sectors": ["Energy", "Materials"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Squeeze", "any", b("ttm_squeeze", 2, condition="fired_up", min_bars=5, within=4),
              b("bollinger", length=20, std=2, condition="squeeze", lookback=120, pctb=0.5, within=3)),
            g("Ignition", "any", b("macd", fast=12, slow=26, signal=9, condition="bull_cross", below_zero_only=False, within=5),
              b("volume_spike", mult=1.5, avg=20, direction="up", within=3)),
        ]},
    },
    "mean_reversion": {
        "title": "Oversold bounce", "style": "momentum",
        "tagline": "Washed-out stocks snapping back inside their lower band at support.",
        "universe": {"sectors": ["Consumer Staples", "Utilities", "Real Estate"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Washed out", "atleast", b("rsi", length=14, condition="cross_up", level=30, within=4),
              b("bollinger", length=20, std=2, condition="reentry_up", lookback=120, pctb=0, within=4),
              b("fear_greed", min=0, max=30), min=2),
            g("Floor", "any", b("sr_level", condition="near_support", tolerance=3, touches=2, within=5, swing="auto"),
              b("candle_pattern", patterns=BULLISH_REVERSALS, within=3, trend="any", level="any", level_tol=2, volume=0, confirm=False)),
        ]},
    },
    "trend_follower": {
        "title": "Trend follower", "style": "trend",
        "tagline": "Above the cloud, Supertrend up, Kalman rising: ride what's already working.",
        "universe": {"sectors": ["Industrials"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Trend", "atleast", b("ichimoku", condition="above_cloud", within=5), b("supertrend", length=10, mult=3, condition="bull", within=5),
              b("kalman_trend", direction="up", strength=20, turned=False),
              b("ma_cross", fast_kind="ema", fast=50, slow_kind="sma", slow=200, condition="fast_above", within=10), min=3),
            g("Entry", "any", b("ma_position", kind="ema", length=21, condition="near", within=3, distance=1.5),
              b("fib_retracement", levels=["0.382", "0.5"], anchor="last", context="pullback", tolerance=2, min_swing=5, swing="auto")),
        ]},
    },
    "pump_dna": {
        "title": "Pump DNA", "style": "pump",
        "tagline": "Small caps whose last 10 days look like the build-ups before historic pumps.",
        "universe": {"lists": ["meme", "pump_history", "crypto"]},
        "spec": {"match": "all", "mode": "strict", "groups": [
            g("Build-up", "atleast", b("pump_dna", 3, min=55), b("volume_awakening", 2, recent=3, mult=1.5, quiet=20),
              b("tight_base", bars=15, range=15, volume_dry=False), min=2),
            g("Spark", "any", b("macd", fast=12, slow=26, signal=9, condition="bull_cross", below_zero_only=False, within=5),
              b("structure", state="bos_up", within=5, swing="auto"), b("bollinger", length=20, std=2, condition="pctb_above",
                                                                         lookback=120, pctb=0.9, within=3)),
            g("Filter", "all", b("price_range", min=0.5, max=30)),
        ]},
    },
    "blank": {
        "title": "Blank canvas", "style": "custom", "tagline": "Start from nothing and drag in your own blocks.",
        "universe": {"sectors": ["Information Technology"]},
        "spec": {"match": "all", "mode": "strict", "groups": [g("Group 1", "all")]},
    },
}


LEARNED_DIR = os.path.join(os.path.dirname(__file__), "learned")


def learned_presets() -> Dict[str, Dict]:
    """Scans the tripler study learned from data (written by `pump_research triplers analyze --install`)"""
    out = {}
    try:
        names = sorted(os.listdir(LEARNED_DIR))
    except OSError:
        return out
    for name in names:
        if name.endswith(".json"):
            try:
                with open(os.path.join(LEARNED_DIR, name)) as f:
                    p = json.load(f)
                if p.get("spec", {}).get("groups"):
                    out[name[:-5]] = p
            except (OSError, ValueError):
                continue
    return out


def all_presets() -> Dict[str, Dict]:
    """Hand-built starter scans plus learned ones, learned first (blank stays last)"""
    out = dict(learned_presets())
    out.update(PRESETS)
    blank = out.pop("blank", None)
    if blank:
        out["blank"] = blank
    return out


def preset(key: str) -> Dict:
    return copy.deepcopy(all_presets()[key])
