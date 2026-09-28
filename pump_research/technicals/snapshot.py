"""
One call that runs every technical tool on the history up to a given bar and
returns (a) flat `ta_*` features for statistics and (b) the detected patterns,
Fibonacci levels, moving averages and key levels for display.
"""

import math

import numpy as np
import pandas as pd

from . import indicators as ind
from .candles import detect_candles
from .chart_patterns import find_chart_patterns
from .composites import adaptive_kalman, fear_greed, sr_signals
from .fib_tools import fib_gann_suite, suite_features
from .fibonacci import fibonacci_levels, all_time_fibonacci
from .harmonics import find_harmonics
from .pivots import zigzag, adaptive_pct, support_resistance, market_structure

MOVING_AVERAGES = {
    "ema8": lambda df: ind.ema(df["close"], 8),
    "ema21": lambda df: ind.ema(df["close"], 21),
    "ema50": lambda df: ind.ema(df["close"], 50),
    "ema200": lambda df: ind.ema(df["close"], 200),
    "wma10": lambda df: ind.wma(df["close"], 10),
    "wma20": lambda df: ind.wma(df["close"], 20),
    "wma50": lambda df: ind.wma(df["close"], 50),
    "hma20": lambda df: ind.hma(df["close"], 20),
    "vwma20": lambda df: ind.vwma(df["close"], df["volume"], 20),
    "sma50": lambda df: ind.sma(df["close"], 50),
    "sma200": lambda df: ind.sma(df["close"], 200),
}

CHART_PATTERN_NAMES = ("double_bottom", "double_top", "inverse_head_shoulders", "head_shoulders",
                       "ascending_triangle", "descending_triangle", "symmetrical_triangle", "rising_wedge",
                       "falling_wedge", "bull_flag", "cup_and_handle", "consolidation", "range_breakout",
                       "range_breakdown")
KEY_CANDLES = ("hammer", "bullish_engulfing", "doji", "gap_up", "inside_bar", "morning_star", "shooting_star")


def _last(s: pd.Series):
    v = s.iloc[-1] if len(s) else np.nan
    return None if v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v) else float(v)


def _rel(a, b):
    return None if a is None or b in (None, 0) else a / b - 1


def _any_in(mask: pd.Series, start: int) -> bool:
    return bool(mask.iloc[start:].fillna(False).any())


def _iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


def technical_snapshot(prices: pd.DataFrame, end_idx: int, window_days: int = 10) -> dict:
    """
    Analyze prices[: end_idx + 1]. Events inside the last `window_days` bars count
    as 'in window' (for a pre-pump window, pass the bar before the pump as end_idx).
    """
    df = prices.iloc[:end_idx + 1]
    n = len(df)
    if n < 15:
        return {"features": {}, "patterns": [], "fibonacci": {}, "moving_averages": {}, "levels": {}, "structure": {}}
    w0 = max(0, n - window_days)
    close = float(df["close"].iloc[-1])
    f = {}

    # Moving averages (simple, exponential, linearly weighted, Hull, volume-weighted)
    mas = {name: fn(df) for name, fn in MOVING_AVERAGES.items()}
    last_ma = {name: _last(s) for name, s in mas.items()}
    for name, v in last_ma.items():
        f[f"ta_close_vs_{name}"] = _rel(close, v)
    e8, e21, e50 = last_ma["ema8"], last_ma["ema21"], last_ma["ema50"]
    if None not in (e8, e21, e50):
        f["ta_ema_bull_stack"] = e8 > e21 > e50
        f["ta_ema_bear_stack"] = e8 < e21 < e50
        f["ta_ema_ribbon_width"] = (max(e8, e21, e50) - min(e8, e21, e50)) / close
    w10, w20, w50 = last_ma["wma10"], last_ma["wma20"], last_ma["wma50"]
    if None not in (w10, w20, w50):
        f["ta_wma_bull_stack"] = w10 > w20 > w50
    f["ta_ema8_cross_up_ema21_in_window"] = _any_in(ind.crossed_above(mas["ema8"], mas["ema21"]), w0)
    f["ta_close_cross_up_wma20_in_window"] = _any_in(ind.crossed_above(df["close"], mas["wma20"]), w0)
    f["ta_close_cross_up_hma20_in_window"] = _any_in(ind.crossed_above(df["close"], mas["hma20"]), w0)
    f["ta_golden_cross_in_window"] = _any_in(ind.crossed_above(mas["sma50"], mas["sma200"]), w0)
    e21s = mas["ema21"]
    f["ta_ema21_slope_5d"] = _rel(_last(e21s), _last(e21s.shift(5)))

    # Oscillators
    rsi = ind.rsi(df["close"])
    f["ta_rsi14"] = _last(rsi)
    f["ta_rsi_min_in_window"] = float(rsi.iloc[w0:].min()) if rsi.iloc[w0:].notna().any() else None
    k, d = ind.stochastic(df)
    f["ta_stoch_k"], f["ta_stoch_d"] = _last(k), _last(d)
    line, sig, hist = ind.macd(df["close"])
    f["ta_macd_hist_pct"] = None if _last(hist) is None else _last(hist) / close
    f["ta_macd_bull_cross_in_window"] = _any_in(ind.crossed_above(line, sig), w0)
    adx, pdi, mdi = ind.adx(df)
    f["ta_adx"] = _last(adx)
    f["ta_di_spread"] = None if _last(pdi) is None else _last(pdi) - _last(mdi)
    atr = ind.atr(df)
    f["ta_atr_pct"] = None if _last(atr) is None else _last(atr) / close

    # Volatility bands
    upper, mid, lower, pct_b, bw = ind.bollinger(df["close"])
    f["ta_bb_pct_b"] = _last(pct_b)
    f["ta_bb_bandwidth"] = _last(bw)
    recent_bw = bw.iloc[-120:].dropna()
    f["ta_bb_squeeze"] = bool(len(recent_bw) >= 40 and recent_bw.iloc[-1] <= recent_bw.quantile(0.2))

    # Volume / money flow
    obv = ind.obv(df)
    avg_vol = df["volume"].iloc[w0:].mean() or np.nan
    obv_change = (obv.iloc[-1] - obv.iloc[w0]) / avg_vol / max(1, n - w0)
    f["ta_obv_slope"] = None if pd.isna(obv_change) else float(obv_change)
    price_change = close / df["close"].iloc[w0] - 1
    f["ta_obv_bullish_divergence"] = bool(f["ta_obv_slope"] is not None and f["ta_obv_slope"] > 0.1 and price_change <= 0)
    f["ta_mfi14"] = _last(ind.mfi(df))
    f["ta_cmf20"] = _last(ind.cmf(df))
    f["ta_close_vs_vwap20"] = _rel(close, _last(ind.rolling_vwap(df)))

    # Swings, structure, support/resistance
    pivots = zigzag(df, adaptive_pct(df))
    structure = market_structure(pivots)
    f["ta_structure_uptrend"] = structure["structure"] == "uptrend"
    f["ta_structure_downtrend"] = structure["structure"] == "downtrend"
    f["ta_higher_lows"] = structure["higher_lows"]
    f["ta_break_of_structure"] = bool(structure["last_swing_high"] and close > structure["last_swing_high"])
    levels = support_resistance(pivots, close)
    f["ta_dist_to_resistance"] = _rel(levels["resistance"]["price"], close) if levels["resistance"] else None
    f["ta_dist_to_support"] = _rel(close, levels["support"]["price"]) if levels["support"] else None
    up = (df["close"].diff() > 0).to_numpy()[::-1]
    f["ta_consecutive_up_closes"] = int(np.argmin(up)) if not up.all() else len(up)
    tr = ind.true_range(df)
    f["ta_range_expansion_last"] = None if _last(atr) in (None, 0) else float(tr.iloc[-1]) / _last(atr)
    f["ta_close_vs_period_high"] = close / float(df["high"].iloc[-250:].max()) - 1
    # Bullish RSI divergence: the last two swing lows make a lower low in price but a higher low in RSI
    lows = [p for p in pivots if p.kind == "low"][-2:]
    f["ta_rsi_bullish_divergence"] = bool(
        len(lows) == 2 and lows[1].price < lows[0].price
        and not pd.isna(rsi.iloc[lows[0].idx]) and not pd.isna(rsi.iloc[lows[1].idx])
        and rsi.iloc[lows[1].idx] > rsi.iloc[lows[0].idx])

    # Fibonacci
    fib = fibonacci_levels(df)
    if fib:
        f["ta_fib_retracement"] = fib["retracement"]
        f["ta_fib_upswing"] = fib["direction"] == "up"
        f["ta_fib_nearest_level"] = fib["nearest_level"]
        f["ta_fib_golden_pocket"] = fib["in_golden_pocket"]

    # Adaptive Kalman trend filter
    kal = adaptive_kalman(df["close"])
    f["ta_kalman_strength"] = _last(kal["kalman_strength"])
    f["ta_close_vs_kalman"] = _rel(close, _last(kal["kalman"]))
    f["ta_kalman_uptrend"] = bool(f["ta_kalman_strength"] is not None and f["ta_kalman_strength"] > 0)
    f["ta_close_cross_up_kalman_in_window"] = _any_in(ind.crossed_above(df["close"], kal["kalman"]), w0)
    f["ta_kalman_turned_up_in_window"] = _any_in((kal["kalman_slope"] > 0) & (kal["kalman_slope"].shift(1) <= 0), w0)

    # All-time Fibonacci retracement
    atf = all_time_fibonacci(df)
    if atf:
        f["ta_alltime_fib_position"] = atf["position"]
        f["ta_alltime_fib_nearest"] = atf["nearest_level"]

    # Fibonacci & Gann tool suite (retracement, extension, channel, time zones, fans, circles, spiral, arcs,
    # wedge, pitchfan, Gann box, squares and fan), anchored on the last swings
    suite = fib_gann_suite(df, pivots, atr)
    f.update(suite_features(suite))

    # Fear & Greed (per stock)
    fg = fear_greed(df)
    f["ta_fear_greed"] = fg.get("score")

    # Patterns: harmonic, chart and candlestick, keeping those completed inside the window
    harmonics = [p for p in find_harmonics(pivots) if p["completed_idx"] >= w0]
    charts = [p for p in find_chart_patterns(df, pivots, n - 1) if p["completed_idx"] >= w0]
    candles = detect_candles(df, w0, n - 1)
    signals = sr_signals(df, levels["levels"], w0)
    f["ta_sr_buy_signals"] = sum(s["direction"] == "bullish" for s in signals)
    f["ta_sr_sell_signals"] = sum(s["direction"] == "bearish" for s in signals)
    f["ta_harmonic_bullish_in_window"] = sum(p["direction"] == "bullish" for p in harmonics)
    f["ta_harmonic_bearish_in_window"] = sum(p["direction"] == "bearish" for p in harmonics)
    f["ta_harmonic_best_score"] = max((p["score"] for p in harmonics), default=None)
    f["ta_chart_bullish_in_window"] = sum(p["direction"] == "bullish" for p in charts)
    f["ta_chart_bearish_in_window"] = sum(p["direction"] == "bearish" for p in charts)
    for name in CHART_PATTERN_NAMES:
        f[f"ta_pattern_{name}"] = any(p["name"] == name for p in charts)
    f["ta_candles_bullish"] = sum(c["direction"] == "bullish" for c in candles)
    f["ta_candles_bearish"] = sum(c["direction"] == "bearish" for c in candles)
    for name in KEY_CANDLES:
        f[f"ta_candle_{name}"] = sum(c["name"] == name for c in candles)

    dates = list(df.index)
    patterns = []
    for p in harmonics + charts + candles + signals:
        p = dict(p)
        for key in ("idx", "start_idx", "completed_idx"):
            if key in p:
                p[key.replace("idx", "date")] = _iso(dates[p[key]])
        for pt in p.get("points", []):
            pt["date"] = _iso(dates[pt["idx"]])
        patterns.append(p)

    if fib:
        fib = {**fib, "swing_high_date": _iso(fib["swing_high_date"]), "swing_low_date": _iso(fib["swing_low_date"])}
    return {
        "fib_gann": _suite_for_display(suite, dates),
        "alltime_fib": atf,
        "fear_greed": fg,
        "kalman": {"level": _last(kal["kalman"]), "strength": f["ta_kalman_strength"]},
        "features": {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v) for k, v in f.items()},
        "patterns": patterns,
        "fibonacci": fib,
        "moving_averages": last_ma,
        "levels": levels,
        "structure": structure,
        "pivots": [{"date": _iso(dates[p.idx]), "price": p.price, "kind": p.kind, "confirmed": p.confirmed}
                   for p in pivots[-12:]],
    }


def _suite_for_display(suite, dates):
    """Fib & Gann suite with bar positions turned into dates, and drawable overlays clipped to the data"""
    if not suite:
        return None
    last = len(dates) - 1

    def pt(idx, price):
        i = int(round(idx))
        return (_iso(dates[i]), float(price)) if 0 <= i <= last else None

    overlays = []

    def add(group, name, points):
        pts = [p for p in (pt(i, v) for i, v in points) if p]
        if len(pts) >= 2:
            overlays.append({"group": group, "name": name, "points": pts})

    t = suite["tools"]
    for group, key in (("Fib speed fan", "speed_fan"), ("Pitchfan", "pitchfan"), ("Gann fan", "gann_fan"), ("Fib channel", "channel")):
        for name, seg in (t.get(key, {}).get("lines") or {}).items():
            add(group, name, seg)
    for group, key, field in (("Fib circles", "circles", "circles"), ("Fib speed arcs", "speed_arcs", "arcs")):
        for name, pts in (t.get(key, {}).get(field) or {}).items():
            add(group, name, pts)
    add("Fib spiral", "spiral", t.get("spiral", {}).get("path") or [])
    a = suite["anchors"]["A"]["idx"]
    for name, price in (t.get("trend_extension", {}).get("levels") or {}).items():
        add("Trend fib extension", name, [(suite["anchors"]["C"]["idx"], price), (last, price)])
    for name, price in (t.get("gann_box", {}).get("levels") or {}).items():
        add("Gann box", name, [(a, price), (last, price)])
    times = {"Fib time zones": t.get("time_zones", {}).get("zones") or [],
             "Trend fib time": t.get("trend_time", {}).get("lines") or []}
    return {
        "anchors": {k: {**v, "date": _iso(dates[v["idx"]])} for k, v in suite["anchors"].items()},
        "price_confluence": suite["price_confluence"], "time_confluence": suite["time_confluence"],
        "summary": {name: {k: v for k, v in tool.items() if not isinstance(v, (list, dict))} for name, tool in t.items()},
        "overlays": overlays,
        "time_lines": {g: [_iso(dates[i]) for i in idxs if 0 <= i <= last] for g, idxs in times.items()},
        "future_time_lines": {g: [i - last for i in idxs if i > last] for g, idxs in times.items()},
    }
