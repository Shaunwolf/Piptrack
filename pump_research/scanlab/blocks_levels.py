"""Level blocks: Fibonacci, Gann, support/resistance, market structure, gaps and ranges"""

from ..technicals import fib_tools as ft
from ..technicals.composites import sr_signals
from ..technicals.fibonacci import all_time_fibonacci, fibonacci_levels
from ..technicals.pivots import market_structure, support_resistance
from .engine import SWING, block, family, multi, number, opts, ramp, result, select, toggle, within

# --- Fibonacci & Gann ---------------------------------------------------------------------------------

family("fibgann", "Fibonacci & Gann", "Retracements, extensions, time zones, spirals, fans, boxes and their confluence")

RETRACE_LEVELS = opts(("0.236", "23.6%"), ("0.382", "38.2%"), ("0.5", "50%"), ("0.618", "61.8%"),
                      ("golden", "Golden pocket 61.8–65%"), ("0.705", "70.5% (OTE)"), ("0.786", "78.6%"), ("0.886", "88.6%"))
ANCHOR = select("anchor", "Swing to measure", opts(("last", "Latest completed swing"), ("dominant", "Dominant swing"),
                                                   ("alltime", "All-time high to low")), "last")


def _swing(ctx, p):
    """(start, end, label): price moving start→end; retracements measure back from end toward start"""
    if p["anchor"] == "alltime":
        f = ctx.memo("alltime_fib", lambda: all_time_fibonacci(ctx.df))
        return (f["low"], f["high"], "all-time range") if f else None
    if p["anchor"] == "dominant":
        f = ctx.memo("dominant_fib", lambda: fibonacci_levels(ctx.df))
        if not f:
            return None
        return ((f["swing_low"], f["swing_high"]) if f["direction"] == "up" else (f["swing_high"], f["swing_low"])) + ("dominant swing",)
    t = ctx.tools(p.get("swing", "auto"))
    if not t.anchors:
        return None
    a, b = t.anchors[0], t.anchors[1]
    return a.price, b.price, "latest swing"


@block("fib_retracement", "fibgann", "Fibonacci retracement",
       "Price pulling back into chosen retracement levels of a swing (golden pocket, OTE and more)",
       [multi("levels", "Levels", RETRACE_LEVELS, ["0.5", "golden"]), ANCHOR,
        select("context", "Swing direction", opts(("any", "Either"), ("pullback", "Pullback in an up-swing (buy zone)"),
                                                   ("bounce", "Bounce in a down-swing (sell zone)")), "pullback"),
        number("tolerance", "Tolerance", 1.5, 0.25, 6, 0.25, "% of the swing"),
        number("min_swing", "Swing at least", 8, 2, 100, 1, "%"), SWING],
       styles=("fibonacci",))
def fib_retracement(ctx, p):
    sw = _swing(ctx, p)
    if not sw:
        return result(False, 0, "not enough swing history")
    start, end, label = sw
    move = end - start
    if not move or abs(move) / min(start, end) * 100 < p["min_swing"]:
        return result(False, 0, f"{label} smaller than {p['min_swing']}%")
    up = move > 0
    if (p["context"] == "pullback" and not up) or (p["context"] == "bounce" and up):
        return result(False, 0, f"{label} runs the other way")
    pos = (end - ctx.close) / move                      # 0 at the swing end, 1 back at its start
    tol = p["tolerance"] / 100
    best = None
    for lv in p["levels"]:
        lo, hi = (0.618, 0.65) if lv == "golden" else (float(lv), float(lv))
        dist = 0 if lo - tol <= pos <= hi + tol else min(abs(pos - lo), abs(pos - hi))
        if best is None or dist < best[0]:
            best = (dist, lv)
    dist, lv = best
    name = dict((k, v) for k, v in RETRACE_LEVELS)[lv]
    hit = dist == 0
    return result(hit, 1.0 if hit else ramp(dist, 0.1, 0), f"Price at {pos * 100:.1f}% retracement of the {label} "
                  f"({start:.2f}→{end:.2f}); {'inside' if hit else 'nearest'} {name}",
                  "bullish" if up else "bearish")


@block("fib_extension", "fibgann", "Fibonacci extension",
       "Price reaching a trend-based extension target of the A→B move projected from C",
       [multi("levels", "Targets", opts(("1", "100%"), ("1.272", "127.2%"), ("1.414", "141.4%"), ("1.618", "161.8%"),
                                         ("2", "200%"), ("2.618", "261.8%"), ("3.618", "361.8%")), ["1.272", "1.618"]),
        select("mode", "Condition", opts(("near", "Testing the target"), ("above", "Pushed through it"),
                                          ("below", "Still below it (room to run)")), "near"),
        number("tolerance", "Tolerance", 1.5, 0.25, 6, 0.25, "%"), SWING],
       styles=("fibonacci",))
def fib_extension(ctx, p):
    t = ctx.tools(p["swing"])
    if not t.anchors:
        return result(False, 0, "not enough swing history")
    a, b, c = t.anchors
    move = b.price - a.price
    results = []
    for lv in p["levels"]:
        target = c.price + float(lv) * move
        if target <= 0:
            continue
        rel = ctx.close / target - 1
        up = move > 0
        ok = {"near": abs(rel) <= p["tolerance"] / 100,
              "above": (rel > 0) if up else (rel < 0),
              "below": (rel < 0) if up else (rel > 0)}[p["mode"]]
        results.append((ok, abs(rel), lv, target))
    if not results:
        return result(False, 0, "no valid targets")
    ok, rel, lv, target = sorted(results, key=lambda r: (not r[0], r[1]))[0]
    return result(ok, 1.0 if ok else ramp(rel, 0.1, 0), f"{float(lv) * 100:.1f}% extension at {target:.2f} "
                  f"(price {rel * 100:.1f}% away)", "bullish" if move > 0 else "bearish")


TOOL_CHOICES = opts(("fib_spiral", "Golden spiral"), ("fib_speed_resistance_arcs", "Speed resistance arcs"),
                    ("fib_circles", "Fibonacci circles"), ("fib_speed_resistance_fan", "Speed resistance fan"),
                    ("fib_channel", "Fibonacci channel"), ("fib_wedge", "Fibonacci wedge"), ("pitchfan", "Pitchfan"),
                    ("gann_fan", "Gann fan"), ("gann_box_price", "Gann box (price)"), ("gann_box_time", "Gann box (time)"))


@block("fib_tool_touch", "fibgann", "Fibonacci/Gann drawing tool",
       "Price touching a line, arc, circle or spiral of any drawing tool (anchored on real swings)",
       [multi("tools", "Tools", TOOL_CHOICES, ["fib_spiral", "fib_speed_resistance_arcs", "gann_fan"]),
        select("need", "Needs", opts(("any", "Any one of them"), ("all", "All of them")), "any"), SWING],
       styles=("fibonacci", "gann"))
def fib_tool_touch(ctx, p):
    from ..toolkit import TOOLS
    t = ctx.tools(p["swing"])
    touched = []
    for name in p["tools"]:
        base = "gann_box" if name.startswith("gann_box") else name
        r = ctx.memo(("tool", p["swing"], base), lambda: TOOLS[base].fn(t))
        if "error" in r:
            continue
        near = r.get("near_price") if name == "gann_box_price" else r.get("near_time") if name == "gann_box_time" else r.get("near")
        if near:
            touched.append(dict((k, v) for k, v in TOOL_CHOICES)[name])
    need = len(p["tools"]) if p["need"] == "all" else 1
    return result(len(touched) >= need, len(touched) / max(need, 1), ("Touching: " + ", ".join(touched)) if touched
                  else "price isn't on any selected tool")


@block("fib_gann_confluence", "fibgann", "Fib/Gann confluence",
       "Several independent Fibonacci and Gann tools agreeing on today's price (and optionally time)",
       [number("min_tools", "At least", 3, 2, 10, 1, "tools agree on price"),
        toggle("time", "Also needs a time confluence (time zone or Gann box line)", False), SWING],
       styles=("fibonacci", "gann"))
def fib_gann_confluence(ctx, p):
    t = ctx.tools(p["swing"])
    suite = ctx.memo(("suite", p["swing"]), lambda: ft.fib_gann_suite(ctx.df, t.pivots, t.atr))
    if not suite:
        return result(False, 0, "not enough swing history")
    price, timed = suite["price_confluence"], suite["time_confluence"]
    ok = len(price) >= p["min_tools"] and (bool(timed) or not p["time"])
    names = ", ".join(x.replace("_", " ") for x in price)
    return result(ok, ramp(len(price), 0, p["min_tools"]) * (1 if timed or not p["time"] else 0.6),
                  f"{len(price)} tools on price ({names or 'none'}){'; time: ' + ', '.join(timed) if timed else ''}")


@block("gann_angle", "fibgann", "Gann fan angle", "Where price sits against the Gann angles from the swing anchor",
       [select("condition", "Condition", opts(("above_1x1", "Above the 1×1 (strong trend)"), ("below_1x1", "Below the 1×1"),
                                               ("near", "Testing any angle")), "above_1x1"), SWING],
       styles=("gann",))
def gann_angle(ctx, p):
    from ..toolkit import TOOLS
    t = ctx.tools(p["swing"])
    r = ctx.memo(("tool", p["swing"], "gann_fan"), lambda: TOOLS["gann_fan"].fn(t))
    if "error" in r:
        return result(False, 0, r["error"])
    one = r["values_now"].get("1x1")
    ok = {"above_1x1": r["above_1x1"], "below_1x1": not r["above_1x1"], "near": r["near"]}[p["condition"]]
    return result(ok, 1.0 if ok else 0.2, f"1×1 angle at {one:.2f}; price {'above' if r['above_1x1'] else 'below'} it"
                  f"{', testing an angle' if r['near'] else ''}",
                  "bullish" if p["condition"] == "above_1x1" else "bearish" if p["condition"] == "below_1x1" else None)


@block("fib_time", "fibgann", "Fibonacci time", "A Fibonacci time zone or trend-based time line arriving now or soon",
       [select("tool", "Time tool", opts(("fib_time_zone", "Fibonacci time zones"), ("trend_based_fib_time", "Trend-based Fib time"),
                                          ("either", "Either")), "either"),
        number("bars", "Within", 2, 0, 10, 1, "bars of a time line"), SWING],
       styles=("fibonacci",))
def fib_time(ctx, p):
    from ..toolkit import TOOLS
    t = ctx.tools(p["swing"])
    names = ["fib_time_zone", "trend_based_fib_time"] if p["tool"] == "either" else [p["tool"]]
    best = None
    for n in names:
        r = ctx.memo(("tool", p["swing"], n), lambda n=n: TOOLS[n].fn(t))
        if "error" in r:
            continue
        gaps = [r.get("bars_to_next")] + ([r.get("bars_since_last")] if "bars_since_last" in r else [])
        gap = min(g for g in gaps if g is not None) if any(g is not None for g in gaps) else None
        if gap is not None and (best is None or gap < best[0]):
            best = (gap, n)
    if not best:
        return result(False, 0, "not enough swing history")
    gap, n = best
    return result(gap <= p["bars"], ramp(gap, p["bars"] + 5, 0), f"{n.replace('_', ' ')}: nearest line {gap} bar{'s' if gap != 1 else ''} away")


@block("alltime_fib", "fibgann", "All-time Fibonacci level", "Price at a retracement of the full all-time range",
       [multi("levels", "Levels", RETRACE_LEVELS[:4] + RETRACE_LEVELS[6:7], ["0.382", "0.5", "0.618"]),
        number("tolerance", "Tolerance", 2, 0.5, 8, 0.5, "% of the range")],
       styles=("fibonacci",))
def alltime_fib(ctx, p):
    return fib_retracement(ctx, {"levels": p["levels"], "anchor": "alltime", "context": "any",
                                 "tolerance": p["tolerance"], "min_swing": 0, "swing": "auto"})


# --- Structure & levels -----------------------------------------------------------------------------------

family("structure", "Structure & levels", "Support and resistance, market structure, signals at levels, gaps and highs/lows")


@block("sr_level", "structure", "Support / resistance",
       "Price at, breaking, or losing a level that has been touched several times",
       [select("condition", "Condition", opts(("near_support", "Sitting on support"), ("near_resistance", "Testing resistance"),
                                               ("broke_resistance", "Just broke resistance"), ("lost_support", "Just lost support")),
               "near_support"),
        number("tolerance", "Tolerance", 2, 0.5, 8, 0.5, "%"), number("touches", "Level touched at least", 2, 2, 8, 1, "times"),
        within(5, 20, "Break within"), SWING],
       styles=("price_action",))
def sr_level(ctx, p):
    piv = ctx.pivots(p["swing"])
    tol = p["tolerance"] / 100
    lv = support_resistance(piv, ctx.close, tolerance=tol, min_touches=p["touches"])
    cond = p["condition"]
    if cond in ("near_support", "near_resistance"):
        level = lv["support" if cond == "near_support" else "resistance"]
        if not level:
            return result(False, 0, "no qualifying level")
        d = abs(ctx.close / level["price"] - 1)
        return result(d <= tol, ramp(d, tol * 3, 0), f"{'Support' if cond == 'near_support' else 'Resistance'} "
                      f"{level['price']:.2f} ({level['touches']} touches), price {d * 100:.1f}% away",
                      "bullish" if cond == "near_support" else "bearish")
    start = max(1, ctx.end - p["within"] + 1)
    past = support_resistance(piv, float(ctx.c.iloc[start - 1]), tolerance=tol, min_touches=p["touches"])
    level = past["resistance" if cond == "broke_resistance" else "support"]
    if not level:
        return result(False, 0, "no qualifying level")
    crossed = ctx.close > level["price"] * (1 + tol / 2) if cond == "broke_resistance" else ctx.close < level["price"] * (1 - tol / 2)
    return result(crossed, 1.0 if crossed else 0.2, f"{'Resistance' if cond == 'broke_resistance' else 'Support'} "
                  f"{level['price']:.2f} ({level['touches']} touches) {'broken' if crossed else 'intact'}",
                  "bullish" if cond == "broke_resistance" else "bearish")


@block("structure", "structure", "Market structure", "Higher highs and lows (uptrend), lower ones (downtrend), or a break of structure",
       [select("state", "State", opts(("uptrend", "Uptrend (HH + HL)"), ("downtrend", "Downtrend (LH + LL)"), ("range", "Range"),
                                       ("bos_up", "Break of structure up"), ("bos_down", "Break of structure down")), "uptrend"),
        within(5, 30, "Break within"), SWING],
       styles=("price_action",))
def structure(ctx, p):
    piv = ctx.pivots(p["swing"])
    ms = market_structure(piv)
    if p["state"] in ("uptrend", "downtrend", "range"):
        ok = ms["structure"] == p["state"]
        return result(ok, 1.0 if ok else 0.1, f"Structure: {ms['structure']} ({ms['higher_highs']} HH, {ms['higher_lows']} HL, "
                      f"{ms['lower_highs']} LH, {ms['lower_lows']} LL)",
                      "bullish" if p["state"] == "uptrend" else "bearish" if p["state"] == "downtrend" else None)
    up = p["state"] == "bos_up"
    swings = [x for x in piv if x.confirmed and x.kind == ("high" if up else "low")]
    if not swings:
        return result(False, 0, "no confirmed swing")
    level = swings[-1].price
    series = ctx.c > level if up else ctx.c < level
    hits = [i for i in ctx.recent(series, p["within"]) if i > swings[-1].idx]
    ok = bool(hits)
    first = hits[0] if ok else None
    return result(ok, 1.0 if ok else 0.1, f"{'Broke above' if up else 'Broke below'} the last swing {'high' if up else 'low'} "
                  f"{level:.2f}" if ok else f"last swing {'high' if up else 'low'} {level:.2f} not broken recently",
                  "bullish" if up else "bearish", ctx.date(first) if ok else None)


@block("sr_signal", "structure", "Buy/sell signal at a level",
       "Support bounce, breakout, resistance rejection or breakdown, each confirmed by its close (and volume for breaks)",
       [multi("signals", "Signals", opts(("support_bounce_buy", "▲ Support bounce"), ("breakout_buy", "▲ Breakout buy"),
                                         ("resistance_reject_sell", "▼ Resistance rejection"), ("breakdown_sell", "▼ Breakdown sell")),
              ["support_bounce_buy", "breakout_buy"]), within(3, 15), SWING],
       styles=("price_action",))
def sr_signal(ctx, p):
    piv = ctx.pivots(p["swing"])
    levels = support_resistance(piv, ctx.close)["levels"]
    sigs = [s for s in sr_signals(ctx.df, levels, max(1, ctx.end - p["within"] + 1)) if s["name"] in p["signals"]]
    if not sigs:
        return result(False, 0, "no level signal")
    s = sigs[-1]
    age = ctx.end - s["idx"]
    return result(True, 1 - 0.3 * age / p["within"], f"{s['name'].replace('_', ' ').capitalize()} at {s['level']:.2f}",
                  s["direction"], ctx.date(s["idx"]))


@block("gap", "structure", "Gap", "An opening gap up or down, filled or still open",
       [select("side", "Gap", opts(("up", "Gap up"), ("down", "Gap down")), "up"),
        number("size", "At least", 3, 0.5, 50, 0.5, "%"), within(3, 20),
        select("fill", "Status", opts(("any", "Any"), ("open", "Still unfilled"), ("filled", "Filled")), "any")],
       styles=("price_action", "pump"))
def gap(ctx, p):
    up = p["side"] == "up"
    for i in range(ctx.end, max(1, ctx.end - p["within"] + 1) - 1, -1):
        prev_h, prev_l = ctx.h.iloc[i - 1], ctx.l.iloc[i - 1]
        size = (ctx.l.iloc[i] / prev_h - 1) if up else (1 - ctx.h.iloc[i] / prev_l)
        if size * 100 >= p["size"]:
            after = ctx.l.iloc[i:].min() <= prev_h if up else ctx.h.iloc[i:].max() >= prev_l
            if p["fill"] == "open" and after or p["fill"] == "filled" and not after:
                continue
            return result(True, ramp(size * 100, p["size"] * 0.5, p["size"] * 2), f"{'Gap up' if up else 'Gap down'} "
                          f"{size * 100:.1f}% on {ctx.date(i)} ({'filled' if after else 'open'})",
                          "bullish" if up else "bearish", ctx.date(i))
    return result(False, 0, f"no {p['size']}%+ gap")


@block("high_low", "structure", "Near highs / lows", "Distance to the 52-week (or N-bar) high or low",
       [select("side", "Near the", opts(("high", "High"), ("low", "Low")), "high"),
        select("lookback", "Range", opts(("20", "20 bars"), ("50", "50 bars"), ("126", "6 months"), ("252", "52 weeks")), "252"),
        number("within_pct", "Within", 5, 0, 50, 0.5, "%")],
       styles=("momentum", "price_action"))
def high_low(ctx, p):
    n = min(int(p["lookback"]), ctx.end + 1)
    hi, lo = ctx.h.iloc[-n:].max(), ctx.l.iloc[-n:].min()
    d = (1 - ctx.close / hi) if p["side"] == "high" else (ctx.close / lo - 1)
    lim = p["within_pct"] / 100
    return result(d <= lim, ramp(d, lim * 3 + 0.01, 0), f"{d * 100:.1f}% from the {n}-bar {p['side']}",
                  "bullish" if p["side"] == "high" else "bearish")

