"""Squeeze-mechanics blocks: settlement stress, short positioning, dealer gamma, crowd attention, VCP and fraud filters"""

import numpy as np

from .engine import block, family, number, opts, ramp, result, select, toggle, within

family("squeeze", "Squeeze mechanics", "Reg SHO threshold lists, short interest and short volume, dealer gamma, "
       "mention velocity, volatility contraction and pump-and-dump red flags")


def _missing(name):
    return result(False, 0, f"{name} data unavailable for this ticker")


@block("reg_sho", "squeeze", "Reg SHO threshold list",
       "Persistent fails-to-deliver: days in a row on the threshold list. Brokers must close out fails by day 13",
       [select("mode", "Condition", opts(("streak", "On the list at least N days"),
                                          ("closeout", "Close-out window (day 8 to 13)")), "streak"),
        number("days", "At least", 5, 1, 30, 1, "days")],
       styles=("squeeze",), needs=("squeeze",))
def reg_sho(ctx, p):
    d = ctx.external("squeeze")
    if d is None or "sq_threshold_streak" not in d:
        return _missing("Threshold-list")
    n = d["sq_threshold_streak"]
    if p["mode"] == "closeout":
        ok = 8 <= n <= 13
        return result(ok, 1.0 if ok else ramp(n, 3, 8) * 0.7, f"Day {n} on the threshold list" if n else "Not on the threshold list",
                      "bullish" if ok else None)
    return result(n >= p["days"], ramp(n, 0, p["days"]), f"{n} day{'s' if n != 1 else ''} in a row on the threshold list",
                  "bullish" if n >= p["days"] else None)


@block("short_interest", "squeeze", "Short interest", "Short % of float and days to cover (short interest ÷ average volume)",
       [number("pct_float", "Short % of float at least", 20, 0, 150, 1, "%"),
        number("days_to_cover", "Days to cover at least", 3, 0, 30, 0.5, "days"),
        toggle("rising", "Short interest rising since last month", False)],
       styles=("squeeze",), needs=("short_interest",))
def short_interest(ctx, p):
    d = ctx.external("short_interest")
    if not d or d.get("shortPercentOfFloat") is None:
        return _missing("Short-interest")
    pct = 100 * float(d["shortPercentOfFloat"] or 0)
    dtc = float(d.get("shortRatio") or 0)
    rising = bool(d.get("sharesShort") and d.get("sharesShortPriorMonth") and d["sharesShort"] > d["sharesShortPriorMonth"])
    ok = pct >= p["pct_float"] and dtc >= p["days_to_cover"] and (rising or not p["rising"])
    s = 0.5 * ramp(pct, p["pct_float"] * 0.4, max(p["pct_float"], 1)) + 0.5 * ramp(dtc, p["days_to_cover"] * 0.4, max(p["days_to_cover"], 0.5))
    return result(ok, s * (1 if rising or not p["rising"] else 0.6),
                  f"{pct:.1f}% of float short, {dtc:.1f} days to cover{', rising' if rising else ''}", "bullish" if ok else None)


@block("short_volume", "squeeze", "Short-volume ratio",
       "Off-exchange short volume ÷ total (FINRA). Market makers short to fill buyers, so a high ratio hints at hidden buying",
       [number("ratio", "10-day average at least", 0.55, 0.2, 0.9, 0.01), toggle("rising", "Higher than the 10 days before", True)],
       styles=("squeeze",), needs=("squeeze",))
def short_volume(ctx, p):
    d = ctx.external("squeeze")
    if not d or d.get("sq_short_vol_ratio") is None:
        return _missing("FINRA short-volume")
    r, ch = d["sq_short_vol_ratio"], d.get("sq_short_vol_ratio_change") or 0
    ok = r >= p["ratio"] and (ch > 0 or not p["rising"])
    return result(ok, ramp(r, p["ratio"] - 0.15, p["ratio"]) * (1 if ch > 0 or not p["rising"] else 0.6),
                  f"Short-volume ratio {r:.2f} ({ch:+.2f} vs the 10 days before)", "bullish" if ok else None)


@block("gamma", "squeeze", "Dealer gamma (options)",
       "Estimated from open interest: dealers short gamma amplify moves; the gamma flip and call wall are the key prices",
       [select("condition", "Condition", opts(("negative", "Dealers short gamma (net GEX below zero)"),
                                               ("near_flip", "Price within N% of the gamma flip"),
                                               ("near_wall", "Price within N% below the call wall"),
                                               ("above_wall", "Price above the call wall"),
                                               ("hot_calls", "Short-dated call volume ≥ X × open interest")), "negative"),
        number("pct", "N", 5, 0.5, 30, 0.5, "%"), number("vol_oi", "X", 1, 0.2, 10, 0.1, "×")],
       styles=("squeeze", "options"), needs=("options",))
def gamma(ctx, p):
    d = ctx.external("options")
    if not d:
        return _missing("Options")
    if not d.get("has_options"):
        return result(False, 0, "No listed options")
    if "net_gex" not in d:
        return _missing("Options")
    spot = ctx.close
    flip, wall, cond = d.get("gamma_flip"), d.get("call_wall"), p["condition"]
    gex_m = d["net_gex"] / 1e6
    base = f"net GEX {gex_m:+.2f}M$/1%" + (f", flip {flip:.2f}" if flip else "") + (f", call wall {wall:g}" if wall else "")
    if cond == "negative":
        ok = d["net_gex"] < 0
        return result(ok, 1.0 if ok else 0.2, ("Dealers short gamma: " if ok else "Dealers long gamma: ") + base, "bullish" if ok else None)
    if cond == "near_flip":
        if not flip:
            return result(False, 0, "No gamma flip within ±60%: " + base)
        dist = abs(spot / flip - 1) * 100
        return result(dist <= p["pct"], ramp(dist, p["pct"] * 3, 0), f"{dist:.1f}% from the gamma flip; " + base)
    if cond in ("near_wall", "above_wall"):
        if not wall:
            return result(False, 0, "No call wall: " + base)
        gap = (wall / spot - 1) * 100
        ok = 0 <= gap <= p["pct"] if cond == "near_wall" else gap < 0
        return result(ok, 1.0 if ok else ramp(-abs(gap), -20, 0) * 0.5, f"Call wall {wall:g} is {gap:+.1f}% away; " + base,
                      "bullish" if ok else None)
    ratio = d.get("short_dated_call_vol_oi") or 0
    return result(ratio >= p["vol_oi"], ramp(ratio, 0, p["vol_oi"]), f"Short-dated call volume {ratio:.2f}× open interest; " + base,
                  "bullish" if ratio >= p["vol_oi"] else None)


@block("mention_velocity", "squeeze", "Mention velocity", "Reddit and StockTwits chatter accelerating (ApeWisdom): mentions now vs 24 hours ago",
       [number("mentions", "Mentions at least", 20, 1, 5000, 1), number("growth", "Growing at least", 2, 1, 50, 0.5, "× in 24h")],
       styles=("squeeze", "sentiment"), needs=("social",))
def mention_velocity(ctx, p):
    d = ctx.external("social")
    if d is None:
        return _missing("Mention")
    now, before = d.get("mentions") or 0, d.get("mentions_24h_ago") or 0
    growth = now / max(before, 1)
    ok = now >= p["mentions"] and growth >= p["growth"]
    rank = f" (rank {int(d['rank'])})" if d.get("rank") else ""
    return result(ok, 0.5 * ramp(now, 0, p["mentions"]) + 0.5 * ramp(growth, 1, p["growth"]),
                  f"{int(now)} mentions vs {int(before)} a day ago{rank}", "bullish" if ok else None)


@block("vcp", "squeeze", "Volatility contraction pattern (VCP)",
       "Minervini-style base: each pullback shallower than the last on drying volume, then a breakout through the pivot",
       [number("contractions", "Contractions at least", 3, 2, 6, 1), number("last_max", "Last pullback at most", 8, 2, 20, 0.5, "%"),
        number("first_max", "First pullback at most", 35, 10, 60, 1, "%"), number("lookback", "Base length up to", 80, 30, 250, 5, "bars"),
        select("status", "Status", opts(("setting_up", "Setting up: within N% under the pivot"),
                                          ("breakout", "Breaking out through the pivot on volume")), "setting_up"),
        number("near", "N", 5, 0.5, 15, 0.5, "%"), within(3, 10, "Breakout within"),
        toggle("stage2", "Stage 2 uptrend (above a rising 200-day EMA)", True), toggle("dry", "Volume drying up in the last contraction", True)],
       styles=("squeeze", "price_action", "momentum"))
def vcp(ctx, p):
    n = int(p["lookback"])
    piv = [x for x in ctx.pivots("3") if x.idx >= ctx.end - n]
    legs = []
    for i, x in enumerate(piv[:-1]):
        if x.kind == "high" and piv[i + 1].kind == "low":
            legs.append((x, piv[i + 1], (x.price - piv[i + 1].price) / x.price * 100))
    if len(legs) < p["contractions"]:
        return result(False, 0, f"{len(legs)} pullbacks in the base (needs {p['contractions']})")
    seq = legs[-int(p["contractions"]):]
    depths = [d for _, _, d in seq]
    shrinking = all(b < a * 0.9 for a, b in zip(depths, depths[1:]))
    pivot_bar, last_low = seq[-1][0], seq[-1][1]
    pivot = pivot_bar.price                      # the high of the last, tightest contraction
    checks = {"shrinking": shrinking, "last": depths[-1] <= p["last_max"], "first": depths[0] <= p["first_max"]}
    if p["stage2"]:
        e200 = ctx.ma("ema", 200)
        checks["stage2"] = bool(e200.notna().iloc[-1] and ctx.close > e200.iloc[-1] and e200.iloc[-1] > e200.iloc[-21])
    if p["dry"]:
        recent = ctx.v.iloc[pivot_bar.idx:last_low.idx + 1].mean()
        checks["dry"] = bool(recent < 0.8 * ctx.v.iloc[-50:].mean())
    shape = " → ".join(f"{d:.0f}%" for d in depths)
    if p["status"] == "breakout":
        avg = ctx.avg_volume(50)
        broke = [i for i in range(max(last_low.idx + 1, ctx.end - p["within"] + 1), ctx.end + 1)
                 if ctx.c.iloc[i] > pivot and ctx.v.iloc[i] >= 1.5 * (avg.iloc[i] or np.inf)]
        checks["breakout"] = bool(broke)
    else:
        gap = (pivot / ctx.close - 1) * 100
        checks["near_pivot"] = 0 <= gap <= p["near"]
    ok = all(checks.values())
    failed = [k for k, v in checks.items() if not v]
    return result(ok, sum(checks.values()) / len(checks), f"Pullbacks {shape}, pivot {pivot:.2f}"
                  + ("" if ok else f" · missing: {', '.join(failed)}"), "bullish" if ok else None)


@block("ema_coil", "squeeze", "EMA coil", "Fast and slow EMAs squeezed together above the trend line: a coiled spring",
       [number("fast", "Fast EMA", 10, 3, 50, 1), number("slow", "Slow EMA", 21, 5, 100, 1),
        number("spread", "Spread at most", 1.5, 0.1, 10, 0.1, "%"), toggle("above50", "Both above the 50-day EMA", True)],
       styles=("squeeze", "trend"))
def ema_coil(ctx, p):
    f, s = ctx.ma("ema", p["fast"]).iloc[-1], ctx.ma("ema", p["slow"]).iloc[-1]
    e50 = ctx.ma("ema", 50).iloc[-1]
    if any(np.isnan(x) for x in (f, s, e50)):
        return result(False, 0, "not enough history")
    spread = abs(f / s - 1) * 100
    above = f > e50 and s > e50
    ok = spread <= p["spread"] and (above or not p["above50"])
    return result(ok, ramp(spread, p["spread"] * 3, p["spread"]) * (1 if above or not p["above50"] else 0.5),
                  f"EMA {p['fast']}/{p['slow']} {spread:.2f}% apart{', above the 50' if above else ''}", "bullish" if ok and f > s else None)


@block("clean_setup", "squeeze", "Pump-and-dump filter",
       "Passes only stocks without the classic red flags: OTC listing, no options, tiny size, sub-dollar price",
       [number("min_price", "Price at least", 1, 0, 50, 0.5, "$"), number("min_cap", "Market cap at least", 50, 0, 100000, 10, "$M"),
        number("min_dollar_vol", "Dollar volume at least", 2, 0, 1000, 0.5, "$M / day"),
        toggle("options", "Must have listed options", True), toggle("exchange", "Must trade on a national exchange (not OTC)", True)],
       styles=("filter", "squeeze"), needs=("short_interest", "options"))
def clean_setup(ctx, p):
    info, chain = ctx.external("short_interest") or {}, ctx.external("options")
    flags = []
    if ctx.close < p["min_price"]:
        flags.append(f"price {ctx.close:.2f}")
    cap = info.get("marketCap")
    if cap is not None and cap / 1e6 < p["min_cap"]:
        flags.append(f"market cap ${cap / 1e6:.0f}M")
    dv = float((ctx.c.iloc[-20:] * ctx.v.iloc[-20:]).mean()) / 1e6
    if dv < p["min_dollar_vol"]:
        flags.append(f"${dv:.1f}M a day")
    if p["options"] and chain is not None and not chain.get("has_options"):
        flags.append("no listed options")
    exch = (info.get("exchange") or "").upper()
    if p["exchange"] and exch in ("PNK", "OTC", "OQB", "OQX", "OEM", "PINK", "OTCM", "GREY"):
        flags.append(f"OTC ({exch})")
    unknown = not info and chain is None
    return result(not flags, 1 - min(1, len(flags) / 3), ("Red flags: " + ", ".join(flags)) if flags else
                  ("No red flags" + (" (exchange and options unknown)" if unknown else "")))
