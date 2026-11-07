"""Indicator blocks: trend, momentum, volatility, volume, filters and composite scores"""

import numpy as np
import pandas as pd

from ..technicals import indicators as ind
from ..technicals.composites import fear_greed
from .engine import MA_KINDS, SWING, block, family, last, number, opts, ramp, result, select, toggle, within

# --- Trend & moving averages ----------------------------------------------------------------------

family("trend", "Trend & averages", "Moving averages of every kind, crosses, ribbons, Kalman, ADX, Supertrend and Ichimoku")


def _ma_label(kind, n):
    return f"{dict((k, v) for k, v in MA_KINDS)[kind].split(' (')[0]} {n}" if kind != "kalman" else "Kalman filter"


@block("ma_position", "trend", "Price vs moving average", "Price above, below or crossing any moving average, or the average's slope",
       [select("kind", "Average", MA_KINDS, "ema"), number("length", "Length", 50, 2, 400, 1, "bars"),
        select("condition", "Condition", opts(("above", "Price above it"), ("below", "Price below it"),
                                               ("cross_up", "Price crossed above"), ("cross_down", "Price crossed below"),
                                               ("rising", "Average rising"), ("falling", "Average falling"),
                                               ("near", "Price touching it")), "above"),
        within(3, 30, "Cross / touch within"), number("distance", "Touch tolerance", 1, 0.2, 10, 0.1, "%")],
       styles=("trend",))
def ma_position(ctx, p):
    ma = ctx.ma(p["kind"], p["length"])
    m = last(ma)
    if m is None:
        return result(False, 0, "not enough history for this average")
    label = _ma_label(p["kind"], p["length"])
    rel = ctx.close / m - 1
    cond = p["condition"]
    if cond in ("above", "below"):
        ok = rel > 0 if cond == "above" else rel < 0
        return result(ok, ramp(rel if cond == "above" else -rel, -0.03, 0.03), f"Price {rel * 100:+.1f}% vs {label}",
                      "bullish" if cond == "above" else "bearish")
    if cond in ("cross_up", "cross_down"):
        crossed = ind.crossed_above(ctx.c, ma) if cond == "cross_up" else ind.crossed_below(ctx.c, ma)
        hits = ctx.recent(crossed, p["within"])
        if hits:
            age = ctx.end - hits[-1]
            return result(True, 1 - 0.3 * age / p["within"], f"Crossed {'above' if cond == 'cross_up' else 'below'} {label} {age} bars ago",
                          "bullish" if cond == "cross_up" else "bearish", ctx.date(hits[-1]))
        return result(False, ramp(abs(rel), 0.05, 0) * 0.5, f"No cross of {label}; price {rel * 100:+.1f}%")
    if cond in ("rising", "falling"):
        slope = ma.iloc[-1] / ma.iloc[-6] - 1 if len(ma.dropna()) > 6 else 0
        ok = slope > 0 if cond == "rising" else slope < 0
        return result(ok, ramp(slope if cond == "rising" else -slope, 0, 0.03), f"{label} {slope * 100:+.2f}% over 5 bars",
                      "bullish" if cond == "rising" else "bearish")
    lows, highs = ctx.l.iloc[-p["within"]:], ctx.h.iloc[-p["within"]:]
    mas = ma.iloc[-p["within"]:]
    touched = ((lows <= mas * (1 + p["distance"] / 100)) & (highs >= mas * (1 - p["distance"] / 100))).any()
    return result(bool(touched), 1.0 if touched else ramp(abs(rel), 0.08, 0), f"{'Touching' if touched else 'Away from'} {label} ({rel * 100:+.1f}%)")


@block("ma_cross", "trend", "Moving-average cross", "Fast average crossing a slow one: golden/death crosses and any custom pair",
       [select("fast_kind", "Fast average", MA_KINDS[:5], "ema"), number("fast", "Fast length", 50, 2, 300, 1, "bars"),
        select("slow_kind", "Slow average", MA_KINDS[:5], "sma"), number("slow", "Slow length", 200, 3, 400, 1, "bars"),
        select("condition", "Condition", opts(("golden", "Bullish cross (fast over slow)"), ("death", "Bearish cross"),
                                               ("fast_above", "Fast above slow"), ("fast_below", "Fast below slow")), "golden"),
        within(10, 60, "Cross within")],
       styles=("trend",))
def ma_cross(ctx, p):
    f, s = ctx.ma(p["fast_kind"], p["fast"]), ctx.ma(p["slow_kind"], p["slow"])
    if last(f) is None or last(s) is None:
        return result(False, 0, "not enough history")
    names = f"{_ma_label(p['fast_kind'], p['fast'])} / {_ma_label(p['slow_kind'], p['slow'])}"
    cond = p["condition"]
    if cond in ("fast_above", "fast_below"):
        spread = last(f) / last(s) - 1
        ok = spread > 0 if cond == "fast_above" else spread < 0
        return result(ok, ramp(spread if cond == "fast_above" else -spread, -0.02, 0.03), f"{names} spread {spread * 100:+.1f}%",
                      "bullish" if cond == "fast_above" else "bearish")
    crossed = ind.crossed_above(f, s) if cond == "golden" else ind.crossed_below(f, s)
    hits = ctx.recent(crossed, p["within"])
    if hits:
        age = ctx.end - hits[-1]
        return result(True, 1 - 0.3 * age / p["within"], f"{'Bullish' if cond == 'golden' else 'Bearish'} cross {names} {age} bars ago",
                      "bullish" if cond == "golden" else "bearish", ctx.date(hits[-1]))
    return result(False, 0, f"no {names} cross in {p['within']} bars")


@block("ma_ribbon", "trend", "Moving-average ribbon", "A stack of averages in bullish or bearish order, optionally fanning out",
       [select("kind", "Average", MA_KINDS[:5], "ema"),
        select("lengths", "Ribbon", opts(("8,21,50", "8 / 21 / 50"), ("8,21,50,200", "8 / 21 / 50 / 200"),
                                          ("10,20,50,100,200", "10 / 20 / 50 / 100 / 200"), ("5,8,13,21,34,55", "Fibonacci 5…55")),
               "8,21,50,200"),
        select("order", "Order", opts(("bullish", "Bullish (shortest on top)"), ("bearish", "Bearish")), "bullish"),
        toggle("expanding", "Ribbon widening", False)],
       styles=("trend",))
def ma_ribbon(ctx, p):
    lengths = [int(x) for x in p["lengths"].split(",")]
    vals = [last(ctx.ma(p["kind"], n)) for n in lengths]
    if any(v is None for v in vals):
        return result(False, 0, "not enough history")
    pairs = list(zip(vals, vals[1:]))
    good = sum((a > b) if p["order"] == "bullish" else (a < b) for a, b in pairs)
    width = abs(vals[0] / vals[-1] - 1)
    prev = [ctx.ma(p["kind"], n).iloc[-6] for n in lengths]
    widening = abs(prev[0] / prev[-1] - 1) < width if all(pd.notna(prev)) else False
    ok = good == len(pairs) and (widening or not p["expanding"])
    return result(ok, good / len(pairs) * (1 if widening or not p["expanding"] else 0.7),
                  f"{good}/{len(pairs)} averages in {p['order']} order; ribbon width {width * 100:.1f}%{' and widening' if widening else ''}",
                  p["order"])


@block("kalman_trend", "trend", "Adaptive Kalman trend", "Volatility-adaptive Kalman filter: trend direction and strength",
       [select("direction", "Trend", opts(("up", "Up"), ("down", "Down")), "up"),
        number("strength", "Strength at least", 20, 0, 100, 5, "/100"), toggle("turned", "Just turned (last 5 bars)", False)],
       styles=("trend",))
def kalman_trend(ctx, p):
    k = ctx.kalman()
    st = k["kalman_strength"]
    s = last(st)
    if s is None:
        return result(False, 0, "not enough history")
    up = p["direction"] == "up"
    val = s if up else -s
    ok = val >= p["strength"]
    if p["turned"]:
        recent = st.iloc[-6:-1]
        ok = ok and ((recent <= 0).any() if up else (recent >= 0).any())
    return result(ok, ramp(val, 0, max(p["strength"], 1) * 1.5), f"Kalman trend strength {s:+.0f}",
                  "bullish" if up else "bearish")


@block("adx", "trend", "ADX trend strength", "How strong the trend is (ADX) and who is in control (+DI vs −DI)",
       [number("level", "ADX at least", 25, 10, 60, 1), number("length", "Length", 14, 5, 50, 1, "bars"),
        select("direction", "Direction", opts(("any", "Either"), ("up", "+DI above −DI"), ("down", "−DI above +DI")), "up"),
        toggle("rising", "ADX rising", False)],
       styles=("trend",))
def adx(ctx, p):
    a, pdi, mdi = ctx.memo(("adx", p["length"]), lambda: ind.adx(ctx.df, int(p["length"])))
    v, pl, mn = last(a), last(pdi), last(mdi)
    if v is None:
        return result(False, 0, "not enough history")
    dir_ok = p["direction"] == "any" or (pl > mn if p["direction"] == "up" else mn > pl)
    rising = a.iloc[-1] > a.iloc[-4]
    ok = v >= p["level"] and dir_ok and (rising or not p["rising"])
    return result(ok, ramp(v, p["level"] * 0.6, p["level"]) * (1 if dir_ok else 0.3), f"ADX {v:.0f}, +DI {pl:.0f} / −DI {mn:.0f}",
                  "bullish" if pl > mn else "bearish")


@block("supertrend", "trend", "Supertrend", "ATR-band trend follower: current state or a fresh flip",
       [number("length", "ATR length", 10, 5, 50, 1, "bars"), number("mult", "Multiplier", 3, 1, 6, 0.5, "× ATR"),
        select("condition", "Condition", opts(("bull", "In an uptrend"), ("bear", "In a downtrend"),
                                               ("flip_up", "Flipped up"), ("flip_down", "Flipped down")), "flip_up"),
        within(5, 30, "Flip within")],
       styles=("trend",))
def supertrend(ctx, p):
    line, d = ctx.memo(("st", p["length"], p["mult"]), lambda: ind.supertrend(ctx.df, int(p["length"]), float(p["mult"])))
    cur = d.iloc[-1]
    cond = p["condition"]
    if cond in ("bull", "bear"):
        ok = cur == (1 if cond == "bull" else -1)
        return result(ok, 1.0 if ok else 0.0, f"Supertrend {'up' if cur == 1 else 'down'} (line {last(line) or 0:.2f})",
                      "bullish" if cur == 1 else "bearish")
    want = 1 if cond == "flip_up" else -1
    flips = ctx.recent((d == want) & (d.shift(1) == -want), p["within"])
    if flips:
        age = ctx.end - flips[-1]
        return result(cur == want, 1 - 0.3 * age / p["within"], f"Supertrend flipped {'up' if want == 1 else 'down'} {age} bars ago",
                      "bullish" if want == 1 else "bearish", ctx.date(flips[-1]))
    return result(False, 0, f"no Supertrend flip in {p['within']} bars")


@block("ichimoku", "trend", "Ichimoku cloud", "Price vs the cloud, Tenkan/Kijun crosses and cloud colour",
       [select("condition", "Condition", opts(("above_cloud", "Price above the cloud"), ("below_cloud", "Price below the cloud"),
                                               ("tk_cross_up", "Tenkan crossed above Kijun"), ("tk_cross_down", "Tenkan crossed below Kijun"),
                                               ("cloud_breakout", "Broke out above the cloud"), ("green_cloud", "Cloud bullish (A over B)")),
               "above_cloud"),
        within(5, 30, "Cross / breakout within")],
       styles=("trend",))
def ichimoku(ctx, p):
    t, k, a, b = ctx.memo("ichimoku", lambda: ind.ichimoku(ctx.df))
    top, bot = np.maximum(a, b), np.minimum(a, b)
    if pd.isna(top.iloc[-1]):
        return result(False, 0, "not enough history (needs ~80 bars)")
    cond = p["condition"]
    if cond in ("above_cloud", "below_cloud"):
        ok = ctx.close > top.iloc[-1] if cond == "above_cloud" else ctx.close < bot.iloc[-1]
        return result(ok, 1.0 if ok else 0.2, f"Price {ctx.close:.2f}, cloud {bot.iloc[-1]:.2f}–{top.iloc[-1]:.2f}",
                      "bullish" if cond == "above_cloud" else "bearish")
    if cond == "green_cloud":
        ok = a.iloc[-1] > b.iloc[-1]
        return result(ok, 1.0 if ok else 0.0, f"Cloud {'bullish' if ok else 'bearish'}", "bullish" if ok else "bearish")
    series = {"tk_cross_up": ind.crossed_above(t, k), "tk_cross_down": ind.crossed_below(t, k),
              "cloud_breakout": ind.crossed_above(ctx.c, top)}[cond]
    hits = ctx.recent(series, p["within"])
    if hits:
        age = ctx.end - hits[-1]
        return result(True, 1 - 0.3 * age / p["within"], f"{cond.replace('_', ' ').capitalize()} {age} bars ago",
                      "bearish" if cond == "tk_cross_down" else "bullish", ctx.date(hits[-1]))
    return result(False, 0, f"no {cond.replace('_', ' ')} in {p['within']} bars")


# --- Momentum ---------------------------------------------------------------------------------------

family("momentum", "Momentum", "RSI, MACD, stochastics, CCI, Williams %R, ROC, MFI and divergences")

THRESHOLD_CONDITIONS = opts(("below", "Below the level"), ("above", "Above the level"), ("cross_up", "Crossed up through the level"),
                            ("cross_down", "Crossed down through the level"), ("rising", "Rising"), ("falling", "Falling"))


def _threshold(ctx, series, p, name, bull_when_low=True):
    v = last(series)
    if v is None:
        return result(False, 0, f"not enough history for {name}")
    lvl, cond = p["level"], p["condition"]
    if cond == "below":
        return result(v < lvl, ramp(v, lvl + 15, lvl - 5), f"{name} {v:.1f} (level {lvl:g})", "bullish" if bull_when_low else "bearish")
    if cond == "above":
        return result(v > lvl, ramp(v, lvl - 15, lvl + 5), f"{name} {v:.1f} (level {lvl:g})", "bearish" if bull_when_low else "bullish")
    if cond in ("cross_up", "cross_down"):
        ref = pd.Series(lvl, index=series.index)
        hits = ctx.recent(ind.crossed_above(series, ref) if cond == "cross_up" else ind.crossed_below(series, ref), p["within"])
        if hits:
            age = ctx.end - hits[-1]
            return result(True, 1 - 0.3 * age / p["within"], f"{name} crossed {'up' if cond == 'cross_up' else 'down'} through {lvl:g} "
                          f"{age} bars ago (now {v:.1f})", "bullish" if cond == "cross_up" else "bearish", ctx.date(hits[-1]))
        return result(False, ramp(-abs(v - lvl), -20, 0) * 0.4, f"{name} {v:.1f}, no cross of {lvl:g}")
    n = int(p["within"])
    delta = v - series.iloc[-1 - n] if len(series.dropna()) > n else 0
    ok = delta > 0 if cond == "rising" else delta < 0
    return result(ok, ramp(abs(delta), 0, 10) if ok else 0, f"{name} {delta:+.1f} over {n} bars (now {v:.1f})",
                  "bullish" if cond == "rising" else "bearish")


@block("rsi", "momentum", "RSI", "Relative Strength Index: oversold/overbought, level crosses and direction",
       [number("length", "Length", 14, 2, 50, 1, "bars"), select("condition", "Condition", THRESHOLD_CONDITIONS, "cross_up"),
        number("level", "Level", 30, 1, 99, 1), within(3, 20)],
       styles=("momentum",))
def rsi(ctx, p):
    return _threshold(ctx, ctx.memo(("rsi", p["length"]), lambda: ind.rsi(ctx.c, int(p["length"]))), p, f"RSI {p['length']}")


@block("macd", "momentum", "MACD", "Signal-line and zero-line crosses, histogram turns and position",
       [number("fast", "Fast", 12, 2, 50, 1), number("slow", "Slow", 26, 5, 100, 1), number("signal", "Signal", 9, 2, 30, 1),
        select("condition", "Condition", opts(("bull_cross", "Bullish signal cross"), ("bear_cross", "Bearish signal cross"),
                                               ("zero_up", "Crossed above zero"), ("zero_down", "Crossed below zero"),
                                               ("hist_up", "Histogram turning up"), ("hist_down", "Histogram turning down"),
                                               ("above_zero", "Above zero"), ("below_zero", "Below zero")), "bull_cross"),
        toggle("below_zero_only", "Bullish cross must happen below zero", False), within(3, 20)],
       styles=("momentum",))
def macd(ctx, p):
    line, sig, hist = ctx.memo(("macd", p["fast"], p["slow"], p["signal"]),
                               lambda: ind.macd(ctx.c, int(p["fast"]), int(p["slow"]), int(p["signal"])))
    if last(hist) is None:
        return result(False, 0, "not enough history")
    cond = p["condition"]
    zero = pd.Series(0.0, index=line.index)
    if cond in ("above_zero", "below_zero"):
        ok = (last(line) > 0) == (cond == "above_zero")
        return result(ok, 1.0 if ok else 0.0, f"MACD {last(line):+.3f}", "bullish" if cond == "above_zero" else "bearish")
    if cond in ("hist_up", "hist_down"):
        h = hist.iloc[-3:].to_numpy()
        ok = (h[-1] > h[-2] and h[-2] <= h[-3]) if cond == "hist_up" else (h[-1] < h[-2] and h[-2] >= h[-3])
        return result(bool(ok), 1.0 if ok else 0.0, f"Histogram {h[-1]:+.3f} (prev {h[-2]:+.3f})",
                      "bullish" if cond == "hist_up" else "bearish")
    series = {"bull_cross": ind.crossed_above(line, sig), "bear_cross": ind.crossed_below(line, sig),
              "zero_up": ind.crossed_above(line, zero), "zero_down": ind.crossed_below(line, zero)}[cond]
    if cond == "bull_cross" and p["below_zero_only"]:
        series = series & (line < 0)
    hits = ctx.recent(series, p["within"])
    if hits:
        age = ctx.end - hits[-1]
        return result(True, 1 - 0.3 * age / p["within"], f"MACD {cond.replace('_', ' ')} {age} bars ago",
                      "bullish" if cond in ("bull_cross", "zero_up") else "bearish", ctx.date(hits[-1]))
    return result(False, 0, f"no MACD {cond.replace('_', ' ')} in {p['within']} bars")


@block("stochastic", "momentum", "Stochastic", "%K/%D crosses inside oversold or overbought zones",
       [number("k", "%K length", 14, 3, 50, 1), number("d", "%D smoothing", 3, 1, 10, 1),
        select("condition", "Condition", opts(("os_cross_up", "%K crossed above %D while oversold"),
                                               ("ob_cross_down", "%K crossed below %D while overbought"),
                                               ("oversold", "Oversold"), ("overbought", "Overbought")), "os_cross_up"),
        number("oversold", "Oversold below", 20, 5, 40, 1), number("overbought", "Overbought above", 80, 60, 95, 1), within(3, 20)],
       styles=("momentum",))
def stochastic(ctx, p):
    k, d = ctx.memo(("stoch", p["k"], p["d"]), lambda: ind.stochastic(ctx.df, int(p["k"]), int(p["d"])))
    kv = last(k)
    if kv is None or last(d) is None:
        return result(False, 0, "not enough history")
    cond = p["condition"]
    if cond == "oversold":
        return result(kv < p["oversold"], ramp(kv, p["oversold"] + 20, p["oversold"] - 5), f"%K {kv:.0f}", "bullish")
    if cond == "overbought":
        return result(kv > p["overbought"], ramp(kv, p["overbought"] - 20, p["overbought"] + 5), f"%K {kv:.0f}", "bearish")
    up = cond == "os_cross_up"
    zone = (k.shift(1) < p["oversold"]) if up else (k.shift(1) > p["overbought"])
    hits = ctx.recent((ind.crossed_above(k, d) if up else ind.crossed_below(k, d)) & zone, p["within"])
    if hits:
        age = ctx.end - hits[-1]
        return result(True, 1 - 0.3 * age / p["within"], f"Stochastic cross {'up from oversold' if up else 'down from overbought'} "
                      f"{age} bars ago", "bullish" if up else "bearish", ctx.date(hits[-1]))
    return result(False, 0, f"%K {kv:.0f}, no qualifying cross")


OSCILLATORS = opts(("cci", "CCI"), ("williams", "Williams %R"), ("roc", "Rate of change (%)"), ("mfi", "Money Flow Index"),
                   ("cmf", "Chaikin Money Flow (×100)"))


@block("oscillator", "momentum", "Other oscillators", "CCI, Williams %R, rate of change, MFI or CMF against any level",
       [select("indicator", "Oscillator", OSCILLATORS, "cci"), number("length", "Length", 20, 2, 100, 1, "bars"),
        select("condition", "Condition", THRESHOLD_CONDITIONS, "cross_up"), number("level", "Level", -100, -300, 300, 1),
        within(3, 20)],
       styles=("momentum",))
def oscillator(ctx, p):
    n = int(p["length"])
    calc = {"cci": lambda: ind.cci(ctx.df, n), "williams": lambda: ind.williams_r(ctx.df, n), "roc": lambda: ind.roc(ctx.c, n),
            "mfi": lambda: ind.mfi(ctx.df, n), "cmf": lambda: 100 * ind.cmf(ctx.df, n)}[p["indicator"]]
    series = ctx.memo(("osc", p["indicator"], n), calc)
    name = dict((k, v) for k, v in OSCILLATORS)[p["indicator"]]
    return _threshold(ctx, series, p, f"{name} {n}", bull_when_low=p["indicator"] not in ("roc", "cmf"))


DIV_SOURCES = opts(("rsi", "RSI 14"), ("macd", "MACD histogram"), ("obv", "On-balance volume"), ("mfi", "Money Flow Index"),
                   ("stoch", "Stochastic %K"), ("cci", "CCI 20"))


@block("divergence", "momentum", "Divergence", "Price and an oscillator disagreeing at the last two swings (regular or hidden)",
       [select("source", "Oscillator", DIV_SOURCES, "rsi"),
        select("kind", "Type", opts(("bull", "Regular bullish (lower low, oscillator higher low)"),
                                     ("bear", "Regular bearish (higher high, oscillator lower high)"),
                                     ("hidden_bull", "Hidden bullish (higher low, oscillator lower low)"),
                                     ("hidden_bear", "Hidden bearish (lower high, oscillator higher high)")), "bull"),
        within(10, 40, "Second swing within"), SWING],
       styles=("momentum",))
def divergence(ctx, p):
    src = p["source"]
    osc = ctx.memo(("div_src", src), lambda: {"rsi": lambda: ind.rsi(ctx.c), "macd": lambda: ind.macd(ctx.c)[2],
                                              "obv": lambda: ind.obv(ctx.df), "mfi": lambda: ind.mfi(ctx.df),
                                              "stoch": lambda: ind.stochastic(ctx.df)[0], "cci": lambda: ind.cci(ctx.df)}[src]())
    lows = p["kind"] in ("bull", "hidden_bull")
    piv = [x for x in ctx.pivots(p["swing"]) if x.kind == ("low" if lows else "high")]
    if len(piv) < 2:
        return result(False, 0, "not enough swings")
    a, b = piv[-2], piv[-1]
    if ctx.end - b.idx >= p["within"]:
        return result(False, 0, "latest swing too old")
    oa, ob = osc.iloc[a.idx], osc.iloc[b.idx]
    if pd.isna(oa) or pd.isna(ob):
        return result(False, 0, "oscillator not ready at the swings")
    price_dn, osc_dn = b.price < a.price, ob < oa
    ok = {"bull": price_dn and not osc_dn, "bear": (not price_dn) and osc_dn,
          "hidden_bull": (not price_dn) and osc_dn, "hidden_bear": price_dn and not osc_dn}[p["kind"]]
    label = dict((k, v) for k, v in DIV_SOURCES)[src]
    return result(ok, 1.0 if ok else 0.0, f"{'Swing lows' if lows else 'Swing highs'} {a.price:.2f}→{b.price:.2f}, {label} "
                  f"{oa:.1f}→{ob:.1f}", "bullish" if "bull" in p["kind"] else "bearish", ctx.date(b.idx))


# --- Volatility ---------------------------------------------------------------------------------------

family("volatility", "Volatility & Bollinger", "Bollinger Bands in every configuration, TTM squeeze and ATR expansion")


@block("bollinger", "volatility", "Bollinger Bands", "Squeezes, band tags, re-entries, %B and band walks with your own length and width",
       [number("length", "Length", 20, 5, 100, 1, "bars"), number("std", "Width", 2, 1, 4, 0.1, "std devs"),
        select("condition", "Condition", opts(("squeeze", "Squeeze (narrowest bands in N bars)"),
                                               ("close_below", "Closed below the lower band"), ("close_above", "Closed above the upper band"),
                                               ("reentry_up", "Re-entered from below (mean reversion buy)"),
                                               ("reentry_down", "Re-entered from above"), ("walk_up", "Walking the upper band"),
                                               ("pctb_below", "%B below a value"), ("pctb_above", "%B above a value"),
                                               ("expansion", "Bands expanding out of a squeeze")), "squeeze"),
        number("lookback", "Squeeze lookback", 120, 20, 400, 10, "bars"), number("pctb", "%B value", 0.05, -0.5, 1.5, 0.05),
        within(3, 20)],
       styles=("bollinger", "volatility"))
def bollinger(ctx, p):
    up, mid, lo, pctb, bw = ctx.memo(("bb", p["length"], p["std"]), lambda: ind.bollinger(ctx.c, int(p["length"]), float(p["std"])))
    if last(bw) is None:
        return result(False, 0, "not enough history")
    cond, n = p["condition"], int(p["within"])
    if cond in ("squeeze", "expansion"):
        hist = bw.iloc[-int(p["lookback"]):].dropna()
        rank = (hist <= hist.iloc[-1]).mean()
        if cond == "squeeze":
            return result(rank <= 0.1, ramp(rank, 0.4, 0.05), f"Bandwidth {last(bw) * 100:.1f}%, lower than {100 - rank * 100:.0f}% "
                          f"of the last {len(hist)} bars")
        was = (hist.iloc[-n - 5:-n] <= hist.quantile(0.15)).any() if len(hist) > n + 5 else False
        growing = hist.iloc[-1] > hist.iloc[-n - 1] * 1.3 if len(hist) > n else False
        ok = bool(was and growing)
        return result(ok, 1.0 if ok else 0.2 * growing, f"Bandwidth {hist.iloc[-1] * 100:.1f}% {'expanding from a squeeze' if ok else ''}",
                      "bullish" if ctx.close > last(mid) else "bearish")
    if cond in ("close_below", "close_above"):
        series = ctx.c < lo if cond == "close_below" else ctx.c > up
        hits = ctx.recent(series, n)
        return result(bool(hits), 1.0 if hits else ramp(abs(last(pctb) - (0 if cond == "close_below" else 1)), 0.4, 0),
                      f"%B {last(pctb):.2f}", "bearish" if cond == "close_above" else "bullish", ctx.date(hits[-1]) if hits else None)
    if cond in ("reentry_up", "reentry_down"):
        series = (ctx.c > lo) & (ctx.c.shift(1) < lo.shift(1)) if cond == "reentry_up" else (ctx.c < up) & (ctx.c.shift(1) > up.shift(1))
        hits = ctx.recent(series, n)
        return result(bool(hits), 1.0 if hits else 0, f"{'Back inside from below' if cond == 'reentry_up' else 'Back inside from above'}"
                      if hits else f"no re-entry (%B {last(pctb):.2f})", "bullish" if cond == "reentry_up" else "bearish",
                      ctx.date(hits[-1]) if hits else None)
    if cond == "walk_up":
        streak = 0
        for v in pctb.iloc[::-1]:
            if v >= 0.8:
                streak += 1
            else:
                break
        return result(streak >= n, ramp(streak, 0, n), f"{streak} bars hugging the upper band", "bullish")
    v = last(pctb)
    ok = v < p["pctb"] if cond == "pctb_below" else v > p["pctb"]
    return result(ok, ramp(v, p["pctb"] + 0.3, p["pctb"]) if cond == "pctb_below" else ramp(v, p["pctb"] - 0.3, p["pctb"]),
                  f"%B {v:.2f}", "bullish" if cond == "pctb_below" else "bearish")


@block("ttm_squeeze", "volatility", "TTM squeeze", "Bollinger Bands inside Keltner Channels (coiled), or the squeeze just firing",
       [select("condition", "Condition", opts(("on", "Squeeze on"), ("fired_up", "Fired upward"), ("fired_down", "Fired downward")),
               "fired_up"),
        number("min_bars", "Squeeze lasted at least", 5, 1, 40, 1, "bars"), within(3, 15, "Fired within")],
       styles=("bollinger", "volatility", "momentum"))
def ttm_squeeze(ctx, p):
    def calc():
        up, _, lo, _, _ = ind.bollinger(ctx.c, 20, 2.0)
        ku, km, kl = ind.keltner(ctx.df, 20, 1.5)
        return (up < ku) & (lo > kl)
    on = ctx.memo("ttm_on", calc)
    arr = on.fillna(False).to_numpy(bool)
    mom = ctx.c - (ctx.h.rolling(20).max() + ctx.l.rolling(20).min() + ind.sma(ctx.c, 20) * 2) / 4
    run = 0
    if p["condition"] == "on":
        for v in arr[::-1]:
            if not v:
                break
            run += 1
        return result(run >= p["min_bars"], ramp(run, 0, p["min_bars"]), f"Squeeze on for {run} bars")
    want_up = p["condition"] == "fired_up"
    for i in range(ctx.end, max(1, ctx.end - p["within"] + 1) - 1, -1):
        if arr[i - 1] and not arr[i]:
            j, length = i - 1, 0
            while j >= 0 and arr[j]:
                length, j = length + 1, j - 1
            m = mom.iloc[i]
            if length >= p["min_bars"] and pd.notna(m) and (m > 0) == want_up:
                age = ctx.end - i
                return result(True, 1 - 0.3 * age / p["within"], f"Squeeze ({length} bars) fired {'up' if want_up else 'down'} "
                              f"{age} bars ago", "bullish" if want_up else "bearish", ctx.date(i))
    return result(False, 0, "no squeeze fired")


@block("atr_expansion", "volatility", "Range expansion", "Volatility waking up: today's range or ATR well above normal",
       [select("measure", "Measure", opts(("bar", "Today's range vs ATR"), ("atr", "ATR(5) vs ATR(50)")), "bar"),
        number("mult", "At least", 1.8, 1, 6, 0.1, "×")],
       styles=("volatility", "pump"))
def atr_expansion(ctx, p):
    if p["measure"] == "bar":
        a = ctx.atr(14).iloc[-2]
        r = (ctx.h.iloc[-1] - ctx.l.iloc[-1]) / a if a else 0
    else:
        a5, a50 = last(ctx.atr(5)), last(ctx.atr(50))
        r = a5 / a50 if a5 and a50 else 0
    return result(r >= p["mult"], ramp(r, 1, p["mult"]), f"{r:.1f}× normal range")


# --- Volume ---------------------------------------------------------------------------------------------

family("volume", "Volume & flow", "Volume spikes, quiet-then-waking volume, accumulation and VWAP")


@block("volume_spike", "volume", "Volume spike", "Volume several times its average, on an up day, a down day or either",
       [number("mult", "At least", 2, 1, 20, 0.1, "× average"), number("avg", "Average over", 20, 5, 100, 1, "bars"),
        select("direction", "Day type", opts(("any", "Any"), ("up", "Up day"), ("down", "Down day")), "up"), within(1, 10)],
       styles=("volume", "pump", "momentum"))
def volume_spike(ctx, p):
    avg = ctx.avg_volume(p["avg"])
    best = (0.0, None)
    for i in range(max(1, ctx.end - p["within"] + 1), ctx.end + 1):
        a = avg.iloc[i]
        if not a or pd.isna(a):
            continue
        up = ctx.c.iloc[i] >= ctx.c.iloc[i - 1]
        if p["direction"] != "any" and up != (p["direction"] == "up"):
            continue
        r = ctx.v.iloc[i] / a
        if r > best[0]:
            best = (r, i)
    r, i = best
    return result(r >= p["mult"], ramp(r, 1, p["mult"]), f"Volume {r:.1f}× its {p['avg']}-bar average" if i is not None else "no volume data",
                  "bullish" if p["direction"] == "up" else "bearish" if p["direction"] == "down" else None,
                  ctx.date(i) if i is not None else None)


@block("volume_awakening", "volume", "Quiet, then waking", "The pump tremor: volume dead for weeks, then the last few days pick up",
       [number("recent", "Recent window", 3, 1, 10, 1, "bars"), number("mult", "Recent volume at least", 1.5, 1, 10, 0.1, "× the quiet stretch"),
        number("quiet", "Quiet stretch", 20, 10, 60, 1, "bars")],
       styles=("volume", "pump"))
def volume_awakening(ctx, p):
    r, q = int(p["recent"]), int(p["quiet"])
    if ctx.end < r + q + 60:
        return result(False, 0, "not enough history")
    recent = ctx.v.iloc[-r:].mean()
    quiet = ctx.v.iloc[-r - q:-r].mean()
    longer = ctx.v.iloc[-r - q - 60:-r - q].mean()
    ratio = recent / quiet if quiet else 0
    was_quiet = quiet <= longer * 1.1
    ok = ratio >= p["mult"] and was_quiet
    return result(ok, ramp(ratio, 1, p["mult"]) * (1 if was_quiet else 0.5),
                  f"Last {r} bars {ratio:.1f}× the prior {q}; prior stretch {quiet / longer:.2f}× the longer average", "bullish")


@block("accumulation", "volume", "Accumulation", "Money flowing in: OBV trend, Chaikin Money Flow or up/down volume",
       [select("measure", "Measure", opts(("obv", "OBV making a new high"), ("cmf", "Chaikin Money Flow above"),
                                           ("updown", "Up-day volume ÷ down-day volume above")), "obv"),
        number("bars", "Over", 20, 5, 100, 1, "bars"), number("level", "Level", 0.1, -1, 5, 0.05)],
       styles=("volume",))
def accumulation(ctx, p):
    n = int(p["bars"])
    if p["measure"] == "obv":
        obv = ctx.memo("obv", lambda: ind.obv(ctx.df))
        ok = obv.iloc[-1] >= obv.iloc[-n:].max()
        slope = (obv.iloc[-1] - obv.iloc[-n]) / (ctx.v.iloc[-n:].mean() * n or 1)
        return result(bool(ok), 1.0 if ok else ramp(slope, 0, 0.5), f"OBV {'at' if ok else 'below'} its {n}-bar high", "bullish")
    if p["measure"] == "cmf":
        v = last(ctx.memo(("cmf", n), lambda: ind.cmf(ctx.df, n)))
        return result(v is not None and v > p["level"], ramp(v or 0, p["level"] - 0.15, p["level"] + 0.05), f"CMF {v or 0:+.2f}", "bullish")
    chg = ctx.c.diff().iloc[-n:]
    vol = ctx.v.iloc[-n:]
    up, dn = vol[chg > 0].sum(), vol[chg < 0].sum()
    ratio = up / dn if dn else float("inf")
    return result(ratio > p["level"], ramp(min(ratio, 10), 1, max(p["level"], 1.01)), f"Up/down volume {ratio:.2f}", "bullish")


@block("vwap", "volume", "VWAP", "Price against a rolling volume-weighted average price",
       [number("length", "Length", 20, 5, 200, 1, "bars"),
        select("condition", "Condition", opts(("above", "Above VWAP"), ("below", "Below VWAP"), ("cross_up", "Reclaimed VWAP"),
                                               ("cross_down", "Lost VWAP")), "above"), within(3, 20)],
       styles=("volume", "trend"))
def vwap(ctx, p):
    w = ctx.memo(("vwap", p["length"]), lambda: ind.rolling_vwap(ctx.df, int(p["length"])))
    v = last(w)
    if v is None:
        return result(False, 0, "not enough history")
    rel = ctx.close / v - 1
    cond = p["condition"]
    if cond in ("above", "below"):
        ok = rel > 0 if cond == "above" else rel < 0
        return result(ok, ramp(rel if cond == "above" else -rel, -0.02, 0.03), f"Price {rel * 100:+.1f}% vs VWAP {p['length']}",
                      "bullish" if cond == "above" else "bearish")
    hits = ctx.recent(ind.crossed_above(ctx.c, w) if cond == "cross_up" else ind.crossed_below(ctx.c, w), p["within"])
    return result(bool(hits), 1.0 if hits else 0, f"{'Reclaimed' if cond == 'cross_up' else 'Lost'} VWAP" if hits else "no VWAP cross",
                  "bullish" if cond == "cross_up" else "bearish", ctx.date(hits[-1]) if hits else None)


# --- Filters ---------------------------------------------------------------------------------------------

family("filters", "Price & liquidity filters", "Price range, performance, liquidity and strength against the market")


@block("price_range", "filters", "Price range", "Only stocks trading between two prices (penny stocks, mid-priced, large)",
       [number("min", "From", 1, 0, 100000, 0.5, "$"), number("max", "To", 1000, 0, 100000, 1, "$")], styles=("filter",))
def price_range(ctx, p):
    ok = p["min"] <= ctx.close <= p["max"]
    return result(ok, 1.0 if ok else 0.0, f"Price {ctx.close:.2f}")


@block("performance", "filters", "Performance", "Percent change over a period within a range",
       [number("bars", "Over the last", 20, 1, 252, 1, "bars"), number("min", "Change from", 5, -100, 1000, 1, "%"),
        number("max", "Change to", 1000, -100, 10000, 1, "%")], styles=("filter", "momentum"))
def performance(ctx, p):
    n = min(int(p["bars"]), ctx.end)
    chg = (ctx.close / ctx.c.iloc[-n - 1] - 1) * 100
    ok = p["min"] <= chg <= p["max"]
    return result(ok, 1.0 if ok else ramp(-min(abs(chg - p["min"]), abs(chg - p["max"])), -20, 0) * 0.5,
                  f"{chg:+.1f}% over {n} bars", "bullish" if chg > 0 else "bearish")


@block("liquidity", "filters", "Liquidity", "Average daily dollar volume and share volume floors",
       [number("dollars", "Dollar volume at least", 5, 0, 10000, 0.5, "$M / day"),
        number("shares", "Share volume at least", 0, 0, 100000, 10, "K / day"), number("bars", "Averaged over", 20, 5, 100, 1, "bars")],
       styles=("filter",))
def liquidity(ctx, p):
    n = int(p["bars"])
    dv = float((ctx.c.iloc[-n:] * ctx.v.iloc[-n:]).mean()) / 1e6
    sv = float(ctx.v.iloc[-n:].mean()) / 1e3
    ok = dv >= p["dollars"] and sv >= p["shares"]
    return result(ok, 1.0 if ok else ramp(dv, 0, max(p["dollars"], 0.01)) * 0.5, f"${dv:.1f}M and {sv:,.0f}K shares a day")


@block("relative_strength", "filters", "Relative strength vs market", "Beating (or lagging) the S&P 500 over a period",
       [number("bars", "Over the last", 20, 5, 252, 1, "bars"),
        select("side", "Stock is", opts(("outperform", "Outperforming"), ("underperform", "Underperforming")), "outperform"),
        number("margin", "By at least", 3, 0, 100, 0.5, "percentage points")], styles=("filter", "momentum", "trend"))
def relative_strength(ctx, p):
    b = ctx.benchmark
    if b is None or len(b) < 10:
        return result(False, 0, "market benchmark unavailable")
    n = min(int(p["bars"]), ctx.end)
    bc = b["close"] if "close" in b else b["Close"]
    start_date = ctx.df.index[-n - 1]
    bstart = bc[bc.index <= start_date]
    if bstart.empty:
        return result(False, 0, "benchmark history too short")
    mine = (ctx.close / ctx.c.iloc[-n - 1] - 1) * 100
    mkt = (float(bc.iloc[-1]) / float(bstart.iloc[-1]) - 1) * 100
    diff = mine - mkt
    ok = diff >= p["margin"] if p["side"] == "outperform" else diff <= -p["margin"]
    return result(ok, ramp(diff if p["side"] == "outperform" else -diff, -5, p["margin"] + 5),
                  f"{mine:+.1f}% vs market {mkt:+.1f}% over {n} bars", "bullish" if diff > 0 else "bearish")


# --- Sentiment & composite ------------------------------------------------------------------------------

family("composite", "Sentiment & composites", "Per-stock Fear & Greed and the pump-similarity model trained on real pumps")


@block("fear_greed", "composite", "Fear & Greed", "A 0–100 blend of momentum, 52-week position, RSI, volatility and volume pressure",
       [number("min", "From", 0, 0, 100, 1), number("max", "To", 25, 0, 100, 1)], styles=("sentiment",))
def fear_greed_block(ctx, p):
    fg = ctx.memo("fg", lambda: fear_greed(ctx.df))
    if not fg:
        return result(False, 0, "needs at least 30 bars")
    s = fg["score"]
    ok = p["min"] <= s <= p["max"]
    return result(ok, 1.0 if ok else ramp(-min(abs(s - p["min"]), abs(s - p["max"])), -25, 0) * 0.5,
                  f"Fear & Greed {s:.0f} ({fg['label'].replace('_', ' ')})", "bullish" if s < 50 else "bearish")


@block("pump_dna", "composite", "Pump DNA", "How closely the last 10 days resemble the build-ups before 20+ historic pumps",
       [number("min", "Similarity at least", 60, 0, 100, 1, "/100")], styles=("pump",))
def pump_dna(ctx, p):
    if not ctx.model:
        return result(False, 0, "the pump model isn't trained or loaded yet")
    from ..config import Settings
    from ..features import price_features
    from ..model import score_features
    from ..technicals.snapshot import technical_snapshot
    settings = ctx.settings or Settings()
    snap = ctx.memo("snapshot", lambda: technical_snapshot(ctx.df, ctx.end, settings.pre_window_days))
    feats = price_features(ctx.df, ctx.end, settings, snap) or dict(snap["features"])
    score = score_features(feats, ctx.model).get("score")
    if score is None:
        return result(False, 0, "not enough history to score")
    return result(score >= p["min"], ramp(score, p["min"] - 30, p["min"] + 10), f"Pump similarity {score:.0f}/100", "bullish")

