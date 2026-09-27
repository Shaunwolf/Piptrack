"""
Every technical tool behind one function.

    from pump_research import run_all_tools, run_tool, list_tools

    results = run_all_tools(prices)                 # every tool, one dict keyed by tool name
    fan = run_tool("gann_fan", prices)              # a single tool
    list_tools()                                    # names, categories and descriptions

`prices` is a daily OHLCV DataFrame indexed by date. Columns may be lowercase
(open, high, low, close, volume) or yfinance-style (Open, High, ...). Results are
plain JSON-ready dicts describing the latest bar. Anchor points for the drawing
tools (Fibonacci, Gann, harmonics) come from the stock's own zigzag swings.
"""

import math
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .technicals import indicators as ind
from .technicals import fib_tools as ft
from .technicals.candles import detect_candles
from .technicals.chart_patterns import find_chart_patterns
from .technicals.composites import adaptive_kalman, fear_greed, sr_signals
from .technicals.fibonacci import fibonacci_levels, all_time_fibonacci
from .technicals.harmonics import find_harmonics
from .technicals.pivots import zigzag, adaptive_pct, support_resistance, market_structure
from .technicals.snapshot import technical_snapshot


@dataclass
class Tool:
    name: str
    category: str
    description: str
    fn: Callable


def normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Lowercase OHLCV columns, sorted by date, numeric"""
    df = prices.rename(columns={c: c.lower() for c in prices.columns})
    missing = {"open", "high", "low", "close", "volume"} - set(df.columns)
    if missing:
        raise ValueError(f"prices is missing columns: {sorted(missing)}")
    return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


def _clean(value):
    """Make results JSON-ready: numpy scalars, NaN/inf, dates, nested containers"""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not math.isfinite(float(value)) else float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _last(s: pd.Series):
    v = s.iloc[-1] if len(s) else np.nan
    return None if pd.isna(v) else float(v)


class _Context:
    """Shared, lazily computed pieces (pivots, anchors, ATR) so tools don't recompute them"""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.end = len(df) - 1
        self.close = float(df["close"].iloc[-1])
        self._pivots = self._atr = self._anchors = None

    @property
    def pivots(self):
        if self._pivots is None:
            self._pivots = zigzag(self.df, adaptive_pct(self.df))
        return self._pivots

    @property
    def atr(self):
        if self._atr is None:
            self._atr = ind.atr(self.df)
        return self._atr

    @property
    def tol(self):
        a = _last(self.atr) or self.close * 0.03
        anchors = self.anchors
        rng = abs(anchors[1].price - anchors[0].price) if anchors else a
        return min(0.2 * a, 0.03 * rng)

    @property
    def anchors(self):
        if self._anchors is None:
            self._anchors = ft.select_anchors(self.pivots, self.end, self.close) or ()
        return self._anchors

    def with_anchors(self, fn):
        if not self.anchors:
            return {"error": "not enough swing history to anchor this tool"}
        return fn(*self.anchors)


# --- Tool implementations (each takes the shared context) -----------------------------------

def _dates(ctx, idxs):
    return [ctx.df.index[i].isoformat() if 0 <= i <= ctx.end else f"+{i - ctx.end} bars" for i in idxs]


def _anchor_info(ctx):
    return {k: {"date": ctx.df.index[p.idx].isoformat(), "price": p.price} for k, p in zip("ABC", ctx.anchors)}


def _strip_geometry(result: Dict) -> Dict:
    return {k: v for k, v in result.items() if k not in ("lines", "arcs", "circles", "path")}


def t_fib_retracement(ctx):
    return ctx.with_anchors(lambda a, b, c: {"anchors": _anchor_info(ctx), **ft.fib_retracement(a, b, ctx.close, ctx.tol)})


def t_trend_fib_extension(ctx):
    return ctx.with_anchors(lambda a, b, c: {"anchors": _anchor_info(ctx),
                                             **ft.trend_fib_extension(a, b, c, ctx.close, ctx.tol, ctx.end)})


def t_fib_channel(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.fib_channel(a, b, c, ctx.end, ctx.close, ctx.tol)))


def t_fib_time_zone(ctx):
    def run(a, b, c):
        r = ft.fib_time_zones(a, b, ctx.end)
        return {**r, "zones": _dates(ctx, r["zones"])}
    return ctx.with_anchors(run)


def t_fib_speed_fan(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.fib_speed_fan(a, b, ctx.end, ctx.close, ctx.tol)))


def t_trend_fib_time(ctx):
    def run(a, b, c):
        r = ft.trend_fib_time(a, b, c, ctx.end)
        return {**r, "lines": _dates(ctx, r["lines"])}
    return ctx.with_anchors(run)


def t_fib_circles(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.fib_circles(a, b, ctx.end, ctx.close)))


def t_fib_spiral(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.fib_spiral(a, b, ctx.end, ctx.close)))


def t_fib_speed_arcs(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.fib_speed_arcs(a, b, ctx.end, ctx.close)))


def t_fib_wedge(ctx):
    return ctx.with_anchors(lambda a, b, c: ft.fib_wedge(a, b, c, ctx.end, ctx.close))


def t_pitchfan(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.pitchfan(a, b, c, ctx.end, ctx.close, ctx.tol)))


def t_gann_box(ctx):
    def run(a, b, c):
        r = ft.gann_box(a, b, ctx.end, ctx.close, ctx.tol)
        return {**r, "times": _dates(ctx, r["times"])}
    return ctx.with_anchors(run)


def t_gann_square_fixed(ctx):
    return ctx.with_anchors(lambda a, b, c: ft.gann_square_fixed(
        a, b, ctx.end, ctx.close, float(ctx.atr.iloc[a.idx]) if not pd.isna(ctx.atr.iloc[a.idx]) else _last(ctx.atr)))


def t_gann_square(ctx):
    return ctx.with_anchors(lambda a, b, c: ft.gann_square(a, b, ctx.end, ctx.close))


def t_gann_fan(ctx):
    return ctx.with_anchors(lambda a, b, c: _strip_geometry(ft.gann_fan(a, b, ctx.end, ctx.close, ctx.tol)))


def t_fib_gann_confluence(ctx):
    suite = ft.fib_gann_suite(ctx.df, ctx.pivots, ctx.atr)
    if not suite:
        return {"error": "not enough swing history"}
    return {"price_confluence": suite["price_confluence"], "time_confluence": suite["time_confluence"],
            "strong": len(suite["price_confluence"]) >= 4}


def t_auto_fib_retracement(ctx):
    fib = fibonacci_levels(ctx.df)
    return fib or {"error": "not enough history"}


def t_all_time_fib(ctx):
    return all_time_fibonacci(ctx.df) or {"error": "not enough history"}


def t_fibonacci_levels(ctx):
    fib = fibonacci_levels(ctx.df)
    return {"retracements": fib.get("levels"), "extensions": fib.get("extensions"), "direction": fib.get("direction")} \
        if fib else {"error": "not enough history"}


def t_kalman(ctx):
    k = adaptive_kalman(ctx.df["close"])
    slope = k["kalman_slope"]
    return {"level": _last(k["kalman"]), "slope_per_bar": _last(slope), "trend_strength": _last(k["kalman_strength"]),
            "trend": "up" if (_last(slope) or 0) > 0 else "down",
            "close_vs_filter": ctx.close / _last(k["kalman"]) - 1 if _last(k["kalman"]) else None}


def t_candles(ctx):
    return {"patterns": [{**c, "date": ctx.df.index[c["idx"]].isoformat()} for c in detect_candles(ctx.df, max(1, ctx.end - 9), ctx.end)]}


def t_harmonics(ctx):
    found = find_harmonics(ctx.pivots)
    return {"patterns": [{**p, "completed_date": ctx.df.index[p["completed_idx"]].isoformat()} for p in found[-10:]]}


def t_bollinger(ctx):
    upper, mid, lower, pct_b, bw = ind.bollinger(ctx.df["close"])
    recent = bw.iloc[-120:].dropna()
    return {"upper": _last(upper), "middle": _last(mid), "lower": _last(lower), "percent_b": _last(pct_b),
            "bandwidth": _last(bw), "squeeze": bool(len(recent) >= 40 and recent.iloc[-1] <= recent.quantile(0.2))}


def t_sr_signals(ctx):
    levels = support_resistance(ctx.pivots, ctx.close)
    sig = sr_signals(ctx.df, levels["levels"], max(1, ctx.end - 9))
    return {"support": levels["support"], "resistance": levels["resistance"],
            "signals": [{**s, "date": ctx.df.index[s["idx"]].isoformat()} for s in sig]}


def t_fear_greed(ctx):
    return fear_greed(ctx.df) or {"error": "needs at least 30 bars"}


def t_moving_averages(ctx):
    c, v = ctx.df["close"], ctx.df["volume"]
    mas = {"ema8": ind.ema(c, 8), "ema21": ind.ema(c, 21), "ema50": ind.ema(c, 50), "ema200": ind.ema(c, 200),
           "wma10": ind.wma(c, 10), "wma20": ind.wma(c, 20), "wma50": ind.wma(c, 50), "hma20": ind.hma(c, 20),
           "vwma20": ind.vwma(c, v, 20), "sma50": ind.sma(c, 50), "sma200": ind.sma(c, 200)}
    return {name: _last(s) for name, s in mas.items()}


def t_oscillators(ctx):
    df = ctx.df
    line, sig, hist = ind.macd(df["close"])
    k, d = ind.stochastic(df)
    adx, pdi, mdi = ind.adx(df)
    return {"rsi14": _last(ind.rsi(df["close"])), "macd": _last(line), "macd_signal": _last(sig), "macd_hist": _last(hist),
            "stoch_k": _last(k), "stoch_d": _last(d), "adx": _last(adx), "plus_di": _last(pdi), "minus_di": _last(mdi),
            "atr": _last(ctx.atr), "obv": _last(ind.obv(df)), "mfi14": _last(ind.mfi(df)), "cmf20": _last(ind.cmf(df)),
            "vwap20": _last(ind.rolling_vwap(df))}


def t_structure(ctx):
    return {**market_structure(ctx.pivots), **support_resistance(ctx.pivots, ctx.close),
            "pivots": [{"date": ctx.df.index[p.idx].isoformat(), "price": p.price, "kind": p.kind, "confirmed": p.confirmed}
                       for p in ctx.pivots[-12:]]}


def t_chart_patterns(ctx):
    found = find_chart_patterns(ctx.df, ctx.pivots, ctx.end)
    return {"patterns": [{**p, "completed_date": ctx.df.index[p["completed_idx"]].isoformat()} for p in found]}


def t_snapshot(ctx):
    snap = technical_snapshot(ctx.df, ctx.end)
    return {"features": snap["features"], "fear_greed": snap.get("fear_greed"),
            "price_confluence": (snap.get("fib_gann") or {}).get("price_confluence")}


TOOLS: Dict[str, Tool] = {t.name: t for t in [
    # Fibonacci drawing tools
    Tool("fib_retracement", "fibonacci", "Retracement levels of the last swing A→B", t_fib_retracement),
    Tool("trend_based_fib_extension", "fibonacci", "A→B move projected from pullback C", t_trend_fib_extension),
    Tool("fib_channel", "fibonacci", "A→B trend line with parallels at Fibonacci multiples of the channel width", t_fib_channel),
    Tool("fib_time_zone", "fibonacci", "Vertical time lines at Fibonacci-number intervals from A", t_fib_time_zone),
    Tool("fib_speed_resistance_fan", "fibonacci", "Fan lines from A at Fibonacci fractions of the move", t_fib_speed_fan),
    Tool("trend_based_fib_time", "fibonacci", "A→B duration projected from C at Fibonacci time ratios", t_trend_fib_time),
    Tool("fib_circles", "fibonacci", "Concentric circles on the A→B midpoint (swing units)", t_fib_circles),
    Tool("fib_spiral", "fibonacci", "Golden spiral from A through B", t_fib_spiral),
    Tool("fib_speed_resistance_arcs", "fibonacci", "Arcs centred on B at Fibonacci fractions of |AB|", t_fib_speed_arcs),
    Tool("fib_wedge", "fibonacci", "Wedge from apex A through B and C with Fibonacci arcs", t_fib_wedge),
    Tool("pitchfan", "fibonacci", "Median line from A to the BC midpoint plus Fibonacci fan lines", t_pitchfan),
    # Gann tools
    Tool("gann_box", "gann", "A→B box divided at Gann/Fibonacci fractions in price and time", t_gann_box),
    Tool("gann_square_fixed", "gann", "Square on a fixed scale (1 bar = 1 ATR)", t_gann_square_fixed),
    Tool("gann_square", "gann", "Square sized by the swing; its diagonal is the 1×1", t_gann_square),
    Tool("gann_fan", "gann", "Gann angles 1×8 … 8×1 from A", t_gann_fan),
    Tool("fib_gann_confluence", "gann", "How many Fibonacci/Gann tools agree on today's price and time", t_fib_gann_confluence),
    # Indicator scripts
    Tool("adaptive_kalman_trend_filter", "trend", "Volatility-adaptive Kalman filter with trend strength −100..100", t_kalman),
    Tool("all_candlestick_patterns", "patterns", "Every candlestick pattern over the last 10 bars", t_candles),
    Tool("all_time_fibonacci_retracement", "fibonacci", "Levels between the all-time high and low", t_all_time_fib),
    Tool("auto_fib_retracement", "fibonacci", "Retracement/extension of the dominant swing", t_auto_fib_retracement),
    Tool("auto_harmonic_patterns", "patterns", "Gartley, Bat, Butterfly, Crab, Shark, Cypher, 5-0, AB=CD", t_harmonics),
    Tool("bollinger_bands", "volatility", "Bands, %B, bandwidth and squeeze", t_bollinger),
    Tool("support_resistance_signals", "signals", "Support/resistance levels with breakout, bounce, rejection and breakdown signals",
         t_sr_signals),
    Tool("fear_greed_index", "sentiment", "Per-stock Fear & Greed 0–100 with its components", t_fear_greed),
    Tool("fibonacci_levels", "fibonacci", "Retracement and extension price levels", t_fibonacci_levels),
    # Core
    Tool("moving_averages", "trend", "EMA 8/21/50/200, weighted 10/20/50, Hull 20, volume-weighted 20, SMA 50/200",
         t_moving_averages),
    Tool("oscillators", "momentum", "RSI, MACD, stochastic, ADX/DI, ATR, OBV, MFI, CMF, VWAP", t_oscillators),
    Tool("market_structure", "price_action", "Swings, higher highs/lows, support and resistance", t_structure),
    Tool("chart_patterns", "patterns", "Double tops/bottoms, head & shoulders, triangles, wedges, flags, cup & handle, breakouts",
         t_chart_patterns),
    Tool("technical_snapshot", "all", "All 120+ ta_* features used for scoring", t_snapshot),
]}

# Names as they appear in charting platforms, mapped to the tool that implements them
ALIASES = {
    "fibonacci_toolkit": "fib_gann_confluence",
    "auto_fibonacci_and_gann": "fib_gann_confluence", "harmonic_pattern_detection": "auto_harmonic_patterns",
    "harmonic_patterns": "auto_harmonic_patterns", "adaptive_kalman_filter": "adaptive_kalman_trend_filter",
    "kalman": "adaptive_kalman_trend_filter", "candlestick_patterns": "all_candlestick_patterns",
    "buy_sell_signals": "support_resistance_signals", "fear_and_greed": "fear_greed_index",
}


def list_tools() -> List[Dict]:
    return [{"name": t.name, "category": t.category, "description": t.description} for t in TOOLS.values()]


def run_tool(name: str, prices: pd.DataFrame) -> Dict:
    key = ALIASES.get(name, name)
    if key not in TOOLS:
        raise KeyError(f"unknown tool {name!r}; see list_tools()")
    return _clean(TOOLS[key].fn(_Context(normalize_prices(prices))))


def run_all_tools(prices: pd.DataFrame, tools: Optional[Iterable[str]] = None) -> Dict[str, Dict]:
    """Run every tool (or the named subset) on the same prices, sharing swings and ATR between them"""
    df = normalize_prices(prices)
    if len(df) < 15:
        raise ValueError("need at least 15 bars of prices")
    ctx = _Context(df)
    names = [ALIASES.get(n, n) for n in tools] if tools else list(TOOLS)
    out = {"as_of": df.index[-1].isoformat() if hasattr(df.index[-1], "isoformat") else str(df.index[-1]),
           "close": ctx.close}
    for name in names:
        try:
            out[name] = TOOLS[name].fn(ctx)
        except Exception as e:  # one tool failing shouldn't sink the rest
            out[name] = {"error": f"{type(e).__name__}: {e}"}
    return _clean(out)
