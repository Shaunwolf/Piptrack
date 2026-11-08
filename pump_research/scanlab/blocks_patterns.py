"""Pattern blocks: candlesticks, harmonics and chart patterns"""

import numpy as np

from ..technicals import indicators as ind
from ..technicals.candles import BULLISH, BEARISH
from ..technicals.chart_patterns import find_chart_patterns
from ..technicals.harmonics import find_harmonics, projected_harmonics
from ..technicals.pivots import support_resistance
from .engine import SWING, block, family, multi, number, opts, ramp, result, select, toggle, within

# --- Candlesticks --------------------------------------------------------------------------------

family("candles", "Candlesticks", "Single, double and triple-bar patterns, candle anatomy, streaks and Heikin-Ashi")


def _pretty(name):
    return name.replace("_", " ").replace("three", "3").capitalize()


NEUTRAL = {"doji", "spinning_top", "inside_bar", "outside_bar"}
CANDLE_OPTIONS = (opts(*[(n, "▲ " + _pretty(n)) for n in sorted(BULLISH)])
                  + opts(*[(n, "▼ " + _pretty(n)) for n in sorted(BEARISH)])
                  + opts(*[(n, "◆ " + _pretty(n)) for n in sorted(NEUTRAL)]))
BULLISH_REVERSALS = ["hammer", "inverted_hammer", "bullish_engulfing", "piercing_line", "morning_star",
                     "morning_doji_star", "dragonfly_doji", "bullish_harami", "tweezer_bottom", "three_inside_up",
                     "three_outside_up", "bullish_kicker"]


def _prior_move(ctx, idx, bars=5):
    start = max(0, idx - bars)
    return ctx.c.iloc[idx - 1] / ctx.c.iloc[start] - 1 if idx - 1 > start else 0.0


@block("candle_pattern", "candles", "Candlestick pattern",
       "Any of 35+ classic patterns (TA-Lib definitions), with optional trend, level and volume confirmation",
       [multi("patterns", "Patterns", CANDLE_OPTIONS, BULLISH_REVERSALS[:6]),
        within(3, 20),
        select("trend", "Prior trend", opts(("any", "Any"), ("decline", "After a decline (reversal up)"),
                                            ("rally", "After a rally (reversal down)")), "any"),
        select("level", "Location", opts(("any", "Anywhere"), ("support", "At support"), ("resistance", "At resistance")),
               "any"),
        number("level_tol", "Level tolerance", 2, 0.5, 8, 0.5, "%"),
        number("volume", "Volume at least", 0, 0, 5, 0.1, "× average", help="0 turns the volume check off"),
        toggle("confirm", "Needs a confirmation candle", False,
               help="The next bar closes beyond the pattern in its direction")],
       styles=("candlestick",))
def candle_pattern(ctx, p):
    wanted = set(p["patterns"])
    found = [c for c in ctx.candles(p["within"]) if c["name"] in wanted]
    if not found:
        return result(False, 0, f"none of {len(wanted)} patterns in the last {p['within']} bars")
    avg = ctx.avg_volume(20)
    levels = None
    best = None
    for c in found:
        i, checks, passed = c["idx"], 0, 0
        if p["trend"] != "any":
            checks += 1
            mv = _prior_move(ctx, i)
            passed += (mv <= -0.03) if p["trend"] == "decline" else (mv >= 0.03)
        if p["level"] != "any":
            checks += 1
            levels = levels or support_resistance(ctx.pivots("auto"), ctx.close, tolerance=p["level_tol"] / 100)
            lvl = levels.get("support" if p["level"] == "support" else "resistance")
            ref = ctx.l.iloc[i] if p["level"] == "support" else ctx.h.iloc[i]
            passed += bool(lvl) and abs(ref / lvl["price"] - 1) <= p["level_tol"] / 100
        if p["volume"] > 0:
            checks += 1
            a = avg.iloc[i]
            passed += bool(a and a > 0 and ctx.v.iloc[i] >= p["volume"] * a)
        if p["confirm"]:
            checks += 1
            if i < ctx.end:
                up = c["direction"] == "bullish"
                passed += (ctx.c.iloc[i + 1] > ctx.h.iloc[i]) if up else (ctx.c.iloc[i + 1] < ctx.l.iloc[i])
        age = ctx.end - i
        strength = (0.55 + 0.45 * (passed / checks if checks else 1)) * (1 - 0.35 * age / max(p["within"], 1))
        cand = (passed == checks, strength, c, age)
        if best is None or cand[:2] > best[:2]:
            best = cand
    ok, strength, c, age = best
    return result(ok, strength, f"{_pretty(c['name'])} {age} bar{'s' if age != 1 else ''} ago",
                  c["direction"], ctx.date(c["idx"]))


SHAPES = opts(("long_lower_wick", "Long lower wick (rejection of lows)"), ("long_upper_wick", "Long upper wick"),
              ("marubozu", "Marubozu (no wicks, all body)"), ("small_body", "Small body / indecision"),
              ("wide_range", "Wide-range bar"), ("narrow_range", "Narrowest range in 7 bars (NR7)"),
              ("inside_bar", "Inside bar"), ("outside_bar", "Outside bar"), ("close_near_high", "Closes in the top 10%"),
              ("close_near_low", "Closes in the bottom 10%"))


@block("candle_shape", "candles", "Candle anatomy",
       "Pure price-action reads of a single bar: wicks, bodies, ranges and where it closes",
       [select("shape", "Shape", SHAPES, "long_lower_wick"), within(1, 10),
        number("ratio", "Wick at least", 2, 1, 6, 0.5, "× body", help="For wick shapes"),
        select("color", "Candle colour", opts(("any", "Any"), ("green", "Green"), ("red", "Red")), "any")],
       styles=("candlestick", "price_action"))
def candle_shape(ctx, p):
    o, h, l, c = (x.to_numpy(float) for x in (ctx.o, ctx.h, ctx.l, ctx.c))
    rng = h - l
    body = np.abs(c - o)
    avg_rng = np.convolve(rng, np.ones(20) / 20, mode="full")[:len(rng)]
    best = (0.0, None)
    for i in range(max(1, ctx.end - p["within"] + 1), ctx.end + 1):
        if rng[i] <= 0 or (p["color"] == "green" and c[i] < o[i]) or (p["color"] == "red" and c[i] > o[i]):
            continue
        upper, lower = h[i] - max(o[i], c[i]), min(o[i], c[i]) - l[i]
        b = max(body[i], rng[i] * 0.02)
        s = {
            "long_lower_wick": ramp(lower / b, p["ratio"] * 0.7, p["ratio"]) * ramp(upper / rng[i], 0.4, 0.15),
            "long_upper_wick": ramp(upper / b, p["ratio"] * 0.7, p["ratio"]) * ramp(lower / rng[i], 0.4, 0.15),
            "marubozu": ramp(body[i] / rng[i], 0.85, 0.97),
            "small_body": ramp(body[i] / rng[i], 0.35, 0.1),
            "wide_range": ramp(rng[i] / (avg_rng[i - 1] or rng[i]), 1.3, 2.0) if i > 20 else 0,
            "narrow_range": 1.0 if i >= 6 and rng[i] <= rng[i - 6:i].min() else 0.0,
            "inside_bar": 1.0 if h[i] < h[i - 1] and l[i] > l[i - 1] else 0.0,
            "outside_bar": 1.0 if h[i] > h[i - 1] and l[i] < l[i - 1] else 0.0,
            "close_near_high": ramp((c[i] - l[i]) / rng[i], 0.8, 0.9),
            "close_near_low": ramp((h[i] - c[i]) / rng[i], 0.8, 0.9),
        }[p["shape"]]
        s *= 1 - 0.3 * (ctx.end - i) / max(p["within"], 1)
        if s > best[0]:
            best = (s, i)
    s, i = best
    label = dict((k, v) for k, v in SHAPES)[p["shape"]]
    if i is None:
        return result(False, 0, f"no {label.lower()}")
    bullish = p["shape"] in ("long_lower_wick", "close_near_high") or (p["shape"] == "marubozu" and c[i] > o[i])
    bearish = p["shape"] in ("long_upper_wick", "close_near_low") or (p["shape"] == "marubozu" and c[i] < o[i])
    return result(s >= 0.6, s, f"{label} on {ctx.date(i)}", "bullish" if bullish else "bearish" if bearish else None, ctx.date(i))


@block("candle_streak", "candles", "Candle streak", "A run of same-colour candles, optionally with rising or falling closes",
       [select("color", "Colour", opts(("green", "Green (up)"), ("red", "Red (down)")), "green"),
        number("count", "At least", 3, 2, 12, 1, "candles in a row"),
        toggle("progressive", "Each close beyond the last", True)],
       styles=("candlestick", "price_action"))
def candle_streak(ctx, p):
    o, c = ctx.o.to_numpy(float), ctx.c.to_numpy(float)
    up = p["color"] == "green"
    n = 0
    for i in range(ctx.end, 0, -1):
        same = c[i] > o[i] if up else c[i] < o[i]
        prog = (c[i] > c[i - 1] if up else c[i] < c[i - 1]) if p["progressive"] else True
        if not (same and prog):
            break
        n += 1
    return result(n >= p["count"], ramp(n, 0, p["count"]), f"{n} {p['color']} candle{'s' if n != 1 else ''} in a row",
                  "bullish" if up else "bearish")


@block("heikin_ashi", "candles", "Heikin-Ashi trend", "Smoothed candles: colour flips and strong no-wick trend bars",
       [select("condition", "Condition", opts(("flip_up", "Turned green"), ("flip_down", "Turned red"),
                                               ("strong_up", "Green with no lower wick"),
                                               ("strong_down", "Red with no upper wick")), "flip_up"),
        within(3, 20)],
       styles=("candlestick", "trend"))
def heikin_ashi(ctx, p):
    ha = ctx.memo("ha", lambda: ind.heikin_ashi(ctx.df))
    green = (ha["close"] > ha["open"]).to_numpy(bool)
    no_low = (np.minimum(ha["open"], ha["close"]) - ha["low"]).to_numpy(float) <= 1e-9 * ctx.close
    no_high = (ha["high"] - np.maximum(ha["open"], ha["close"])).to_numpy(float) <= 1e-9 * ctx.close
    cond = p["condition"]
    for i in range(ctx.end, max(1, ctx.end - p["within"] + 1) - 1, -1):
        hit = {"flip_up": green[i] and not green[i - 1], "flip_down": (not green[i]) and green[i - 1],
               "strong_up": green[i] and no_low[i], "strong_down": (not green[i]) and no_high[i]}[cond]
        if hit:
            age = ctx.end - i
            return result(True, 1 - 0.3 * age / p["within"], f"Heikin-Ashi {cond.replace('_', ' ')} {age} bars ago",
                          "bullish" if "up" in cond else "bearish", ctx.date(i))
    return result(False, 0, f"no Heikin-Ashi {cond.replace('_', ' ')}")


# --- Harmonics ----------------------------------------------------------------------------------

family("harmonics", "Harmonics", "XABCD patterns: completed patterns and ones still forming toward their reversal zone")

HARMONIC_OPTIONS = opts(("gartley", "Gartley"), ("bat", "Bat"), ("alt_bat", "Alternate Bat"), ("butterfly", "Butterfly"),
                        ("crab", "Crab"), ("deep_crab", "Deep Crab"), ("shark", "Shark"), ("cypher", "Cypher"),
                        ("five_zero", "5-0"), ("abcd", "AB=CD"))
ALL_HARMONICS = [o[0] for o in HARMONIC_OPTIONS]
DIRECTION = select("direction", "Direction", opts(("any", "Either"), ("bullish", "Bullish"), ("bearish", "Bearish")), "any")


def _hname(name):
    return dict((k, v) for k, v in HARMONIC_OPTIONS).get(name, name)


@block("harmonic_complete", "harmonics", "Harmonic pattern (completed)",
       "A finished XABCD pattern whose D point landed in the last few bars",
       [multi("patterns", "Patterns", HARMONIC_OPTIONS, ALL_HARMONICS), DIRECTION, within(8, 40, "D within the last"),
        number("tolerance", "Ratio tolerance", 4, 1, 12, 0.5, "%", help="How far each Fibonacci ratio may stray"),
        number("quality", "Minimum ratio quality", 50, 0, 100, 5, "%"), SWING,
        toggle("holding", "Price still holding D", True, help="Close hasn't moved beyond D by more than 3%")],
       styles=("harmonic",))
def harmonic_complete(ctx, p):
    found = [h for h in find_harmonics(ctx.pivots(p["swing"]), tol=p["tolerance"] / 100)
             if h["name"] in p["patterns"] and (p["direction"] == "any" or h["direction"] == p["direction"])
             and ctx.end - h["completed_idx"] < p["within"] and 100 * h["score"] >= p["quality"]]
    if not found:
        return result(False, 0, "no completed harmonic in range")
    h = max(found, key=lambda x: (x["score"], x["completed_idx"]))
    d = h["points"][-1]["price"]
    beyond = (ctx.close < d * 0.97) if h["direction"] == "bullish" else (ctx.close > d * 1.03)
    ok = not (p["holding"] and beyond)
    age = ctx.end - h["completed_idx"]
    return result(ok, h["score"] * (1 - 0.3 * age / p["within"]) * (1 if ok else 0.4),
                  f"{h['direction'].capitalize()} {_hname(h['name'])}, D at {d:.2f} ({age} bars ago, quality {100 * h['score']:.0f}%)",
                  h["direction"], ctx.date(h["completed_idx"]), points=h["points"])


@block("harmonic_forming", "harmonics", "Harmonic pattern (forming)",
       "X, A, B and C are in place: price is heading for the projected reversal zone (PRZ) of D",
       [multi("patterns", "Patterns", [o for o in HARMONIC_OPTIONS if o[0] != "five_zero"],
              [n for n in ALL_HARMONICS if n != "five_zero"]), DIRECTION,
        select("status", "Price position", opts(("in_zone", "Inside the PRZ now"), ("near", "Inside or approaching")), "near"),
        number("distance", "Approaching within", 5, 0.5, 25, 0.5, "% of the PRZ"),
        number("tolerance", "Ratio tolerance", 4, 1, 12, 0.5, "%"),
        toggle("overlap", "XA and BC projections must overlap", False), SWING],
       styles=("harmonic",))
def harmonic_forming(ctx, p):
    found = [h for h in projected_harmonics(ctx.pivots(p["swing"]), ctx.close, tol=p["tolerance"] / 100)
             if h["name"] in p["patterns"] and (p["direction"] == "any" or h["direction"] == p["direction"])
             and (h["zones_overlap"] or not p["overlap"]) and h["status"] != "overshot"]
    if p["status"] == "in_zone":
        found = [h for h in found if h["status"] == "in_zone"]
    found = [h for h in found if h["distance"] * 100 <= p["distance"]]
    if not found:
        return result(False, 0, "no forming harmonic near its PRZ")
    h = min(found, key=lambda x: (x["distance"], not x["zones_overlap"]))
    where = "inside" if h["status"] == "in_zone" else f"{100 * h['distance']:.1f}% from"
    return result(True, 1 - 0.6 * h["distance"] * 100 / max(p["distance"], 0.5),
                  f"{h['direction'].capitalize()} {_hname(h['name'])} forming: price {where} PRZ {h['prz_low']:.2f}–{h['prz_high']:.2f}",
                  h["direction"], ctx.date(h["completed_idx"]), prz=[h["prz_low"], h["prz_high"]], points=h["points"])


# --- Chart patterns ---------------------------------------------------------------------------------

family("chart", "Chart patterns", "Classic shapes, breakouts and tight bases")

CHART_OPTIONS = opts(("double_bottom", "▲ Double bottom"), ("double_top", "▼ Double top"),
                     ("inverse_head_shoulders", "▲ Inverse head & shoulders"), ("head_shoulders", "▼ Head & shoulders"),
                     ("ascending_triangle", "▲ Ascending triangle"), ("descending_triangle", "▼ Descending triangle"),
                     ("symmetrical_triangle", "◆ Symmetrical triangle"), ("falling_wedge", "▲ Falling wedge"),
                     ("rising_wedge", "▼ Rising wedge"), ("bull_flag", "▲ Bull flag"),
                     ("cup_and_handle", "▲ Cup & handle"), ("range_breakout", "▲ Range breakout"),
                     ("range_breakdown", "▼ Range breakdown"), ("consolidation", "◆ Consolidation"))


@block("chart_pattern", "chart", "Chart pattern", "Double tops/bottoms, head & shoulders, triangles, wedges, flags, cup & handle",
       [multi("patterns", "Patterns", CHART_OPTIONS, ["double_bottom", "inverse_head_shoulders", "ascending_triangle",
                                                      "falling_wedge", "bull_flag", "cup_and_handle"]),
        DIRECTION, within(10, 60, "Completed within"),
        toggle("breakout", "Breakout confirmed", False, help="Only patterns whose neckline or boundary has broken"), SWING],
       styles=("chart_pattern", "price_action"))
def chart_pattern(ctx, p):
    pats = ctx.memo(("chart", p["swing"]), lambda: find_chart_patterns(ctx.df, ctx.pivots(p["swing"]), ctx.end))
    found = [x for x in pats if x["name"] in p["patterns"] and ctx.end - x["completed_idx"] < p["within"]
             and (p["direction"] == "any" or x["direction"] == p["direction"])
             and (not p["breakout"] or x.get("breakout", x["name"] in ("range_breakout", "range_breakdown", "bull_flag")))]
    if not found:
        return result(False, 0, "no matching chart pattern")
    x = max(found, key=lambda q: q["completed_idx"])
    age = ctx.end - x["completed_idx"]
    label = dict((k, v) for k, v in CHART_OPTIONS)[x["name"]][2:]
    extra = " · breakout" if x.get("breakout") else ""
    return result(True, 1 - 0.4 * age / p["within"], f"{label}{extra} ({age} bars ago)", x["direction"],
                  ctx.date(x["completed_idx"]))


@block("breakout", "chart", "Price breakout", "Close above the N-bar high (or below the low), optionally on heavy volume",
       [select("side", "Side", opts(("up", "Breakout above the high"), ("down", "Breakdown below the low")), "up"),
        select("lookback", "Range", opts(("20", "20-bar range"), ("50", "50-bar range"), ("100", "100-bar range"),
                                          ("252", "52-week range")), "20"),
        number("volume", "Volume at least", 1.5, 0, 6, 0.1, "× average"), within(3, 20)],
       styles=("momentum", "price_action", "chart_pattern"))
def breakout(ctx, p):
    n = int(p["lookback"])
    up = p["side"] == "up"
    ref = (ctx.h.rolling(n, min_periods=n).max() if up else ctx.l.rolling(n, min_periods=n).min()).shift(1)
    crossed = (ctx.c > ref) if up else (ctx.c < ref)
    avg = ctx.avg_volume(20)
    for i in sorted(ctx.recent(crossed, p["within"]), reverse=True):
        vr = ctx.v.iloc[i] / avg.iloc[i] if avg.iloc[i] else 0
        if p["volume"] <= 0 or vr >= p["volume"]:
            age = ctx.end - i
            return result(True, (0.7 + 0.3 * ramp(vr, 1, 3)) * (1 - 0.3 * age / p["within"]),
                          f"{'Broke above' if up else 'Broke below'} the {n}-bar {'high' if up else 'low'} on {vr:.1f}× volume",
                          "bullish" if up else "bearish", ctx.date(i))
    edge = ref.iloc[-1]
    gap = (edge / ctx.close - 1) if up else (ctx.close / edge - 1) if edge else None
    return result(False, ramp(-(gap or 1), -0.05, 0) * 0.5,
                  f"{abs(gap or 0) * 100:.1f}% from the {n}-bar {'high' if up else 'low'}" if gap is not None else "not enough history")


@block("tight_base", "chart", "Tight base (volatility contraction)",
       "Price coiling in a narrow range: the quiet before a move",
       [number("bars", "Over the last", 15, 5, 60, 1, "bars"), number("range", "Range at most", 12, 2, 40, 0.5, "%"),
        toggle("volume_dry", "Volume drying up", True, help="Average volume in the base below its 50-bar average")],
       styles=("price_action", "momentum", "pump"))
def tight_base(ctx, p):
    n = int(p["bars"])
    if ctx.end < n + 50:
        return result(False, 0, "not enough history")
    hi, lo = ctx.h.iloc[-n:].max(), ctx.l.iloc[-n:].min()
    width = (hi / lo - 1) * 100
    dry = ctx.v.iloc[-n:].mean() < ctx.v.iloc[-n - 50:-n].mean()
    ok = width <= p["range"] and (dry or not p["volume_dry"])
    return result(ok, ramp(width, p["range"] * 2, p["range"] * 0.6) * (1 if dry or not p["volume_dry"] else 0.6),
                  f"{n}-bar range {width:.1f}%{' · volume drying up' if dry else ''}")
