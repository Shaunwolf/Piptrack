"""
Option-chain gamma exposure (GEX) from free Yahoo chains.

For each listed contract, Black-Scholes gamma comes from its strike, days to expiry and implied
volatility. Following the SqueezeMetrics/SpotGamma convention, dealers are assumed long the calls
customers sell and short the puts customers buy, so call gamma counts positive and put gamma negative:

    GEX per 1% move ($) = gamma × open interest × 100 × spot² × 0.01

Net GEX below zero means dealers hedge with the trend (amplifying moves). The gamma flip is the spot
price where net GEX crosses zero; the call wall is the strike with the most call gamma.
These are estimates: real dealer positioning is not public.
"""

import math
from datetime import date, datetime
from typing import Dict, List, Optional

import numpy as np

RATE = 0.04
MAX_EXPIRIES = 4
MAX_DAYS = 60


def bs_gamma(spot: float, strike: float, years: float, iv: float, rate: float = RATE) -> float:
    if spot <= 0 or strike <= 0 or years <= 0 or iv <= 0:
        return 0.0
    vs = iv * math.sqrt(years)
    d1 = (math.log(spot / strike) + (rate + iv * iv / 2) * years) / vs
    return math.exp(-d1 * d1 / 2) / (math.sqrt(2 * math.pi) * spot * vs)


def net_gex(contracts: List[Dict], spot: float) -> float:
    """$ dealers must trade per 1% move at `spot` (positive: stabilising, negative: amplifying)"""
    total = 0.0
    for c in contracts:
        g = bs_gamma(spot, c["strike"], c["years"], c["iv"])
        sign = 1 if c["kind"] == "call" else -1
        total += sign * g * c["oi"] * 100 * spot * spot * 0.01
    return total


def gamma_profile(contracts: List[Dict], spot: float) -> Dict:
    """Net GEX now, the gamma flip, call and put walls, and options activity"""
    if not contracts:
        return {}
    now = net_gex(contracts, spot)
    grid = np.linspace(spot * 0.6, spot * 1.6, 121)
    values = np.array([net_gex(contracts, s) for s in grid])
    flips = [float(grid[i] - values[i] * (grid[i + 1] - grid[i]) / (values[i + 1] - values[i]))
             for i in range(len(grid) - 1) if values[i] == 0 or (values[i] < 0) != (values[i + 1] < 0)]
    flip = min(flips, key=lambda f: abs(f - spot)) if flips else None
    by_strike: Dict[tuple, float] = {}
    for c in contracts:
        g = bs_gamma(spot, c["strike"], c["years"], c["iv"]) * c["oi"] * 100 * spot * spot * 0.01
        by_strike[(c["kind"], c["strike"])] = by_strike.get((c["kind"], c["strike"]), 0.0) + g
    calls = {k[1]: v for k, v in by_strike.items() if k[0] == "call"}
    puts = {k[1]: v for k, v in by_strike.items() if k[0] == "put"}
    call_oi = sum(c["oi"] for c in contracts if c["kind"] == "call")
    put_oi = sum(c["oi"] for c in contracts if c["kind"] == "put")
    call_vol = sum(c.get("volume", 0) for c in contracts if c["kind"] == "call")
    near = [c for c in contracts if c["kind"] == "call" and spot * 0.95 <= c["strike"] <= spot * 1.25 and c["years"] <= 21 / 365]
    near_vol, near_oi = sum(c.get("volume", 0) for c in near), sum(c["oi"] for c in near)
    return {
        "spot": spot, "net_gex": now, "regime": "negative" if now < 0 else "positive", "gamma_flip": flip,
        "call_wall": max(calls, key=calls.get) if calls else None, "put_wall": max(puts, key=puts.get) if puts else None,
        "call_oi": call_oi, "put_oi": put_oi, "put_call_oi": put_oi / call_oi if call_oi else None,
        "call_volume": call_vol, "short_dated_call_vol_oi": near_vol / near_oi if near_oi else None,
        "contracts": len(contracts),
    }


def load_chain(ticker: str, today: Optional[date] = None) -> Optional[Dict]:
    """Nearest expiries' contracts from Yahoo, as plain dicts, plus the spot price"""
    import yfinance as yf
    today = today or date.today()
    t = yf.Ticker(ticker)
    expiries = list(t.options or [])[:MAX_EXPIRIES]
    if not expiries:
        return {"has_options": False, "contracts": [], "spot": None}
    contracts = []
    for exp in expiries:
        exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
        days = (exp_date - today).days
        if days > MAX_DAYS:
            break
        chain = t.option_chain(exp)
        years = max(days, 0.5) / 365
        for kind, frame in (("call", chain.calls), ("put", chain.puts)):
            for row in frame.itertuples():
                oi = float(getattr(row, "openInterest", 0) or 0)
                iv = float(getattr(row, "impliedVolatility", 0) or 0)
                if oi > 0 and iv > 0.01:
                    contracts.append({"kind": kind, "strike": float(row.strike), "years": years, "iv": iv, "oi": oi,
                                      "volume": float(getattr(row, "volume", 0) or 0), "expiry": exp})
    spot = None
    try:
        hist = t.history(period="5d")
        spot = float(hist["Close"].iloc[-1]) if len(hist) else None
    except Exception:
        pass
    return {"has_options": True, "contracts": contracts, "spot": spot}


def options_snapshot(ticker: str, spot: Optional[float] = None) -> Dict:
    chain = load_chain(ticker)
    if not chain or not chain["has_options"]:
        return {"has_options": False}
    s = spot or chain["spot"]
    if not s:
        return {"has_options": True, "error": "no spot price"}
    return {"has_options": True, **gamma_profile(chain["contracts"], s)}
