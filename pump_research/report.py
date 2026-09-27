"""Write a readable Markdown report from the dataset and analysis"""

import os
from typing import Dict, List

STATUS_MARK = {"ok": "ok", "no_data": "none found", "blocked": "BLOCKED", "needs_key": "needs key",
               "error": "error", "skipped": "n/a"}


def _pct(v):
    return "–" if v is None else f"{v * 100:+.0f}%"


def _num(v, fmt="{:.2f}"):
    return "–" if v is None else fmt.format(v)


def _mult(v):
    return "–" if v is None else f"{v:.1f}x"


def _known(v):
    """'?' marks a value that is unknown because its source didn't answer"""
    return "?" if v is None else v


def _table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def technical_summary(ta: Dict, pf: Dict, ev: Dict) -> str:
    """Moving averages, oscillators, Fibonacci, structure and patterns at the end of the pre-pump window"""
    lines = ["**Technical picture at the end of the window**"]
    mas = ta.get("moving_averages", {})
    stack = "bullish" if pf.get("ta_ema_bull_stack") else "bearish" if pf.get("ta_ema_bear_stack") else "mixed"
    lines.append(f"- Moving averages: EMA 8/21/50 stack {stack}; close vs EMA21 {_pct(pf.get('ta_close_vs_ema21'))}, "
                 f"vs WMA20 {_pct(pf.get('ta_close_vs_wma20'))}, vs HMA20 {_pct(pf.get('ta_close_vs_hma20'))}, "
                 f"vs VWMA20 {_pct(pf.get('ta_close_vs_vwma20'))}, vs SMA200 {_pct(pf.get('ta_close_vs_sma200'))}"
                 + (" (EMA200 unavailable: short history)" if mas.get("ema200") is None else ""))
    lines.append(f"- Momentum: RSI {_num(pf.get('ta_rsi14'), '{:.0f}')}, stochastic %K {_num(pf.get('ta_stoch_k'), '{:.0f}')}, "
                 f"MACD cross in window: {'yes' if pf.get('ta_macd_bull_cross_in_window') else 'no'}, "
                 f"ADX {_num(pf.get('ta_adx'), '{:.0f}')}, RSI bullish divergence: {'yes' if pf.get('ta_rsi_bullish_divergence') else 'no'}")
    lines.append(f"- Volatility & flow: Bollinger %B {_num(pf.get('ta_bb_pct_b'))}, squeeze: {'yes' if pf.get('ta_bb_squeeze') else 'no'}, "
                 f"ATR {_pct(pf.get('ta_atr_pct')).lstrip('+')} of price, CMF {_num(pf.get('ta_cmf20'))}, MFI {_num(pf.get('ta_mfi14'), '{:.0f}')}, "
                 f"OBV accumulation divergence: {'yes' if pf.get('ta_obv_bullish_divergence') else 'no'}")
    fib = ta.get("fibonacci") or {}
    if fib:
        lines.append(f"- Fibonacci: {fib['direction']}swing ${fib['swing_low']:.2f} → ${fib['swing_high']:.2f}; "
                     f"close at {fib['retracement']:.3f} {'retracement' if fib['direction'] == 'up' else 'bounce'} "
                     f"(nearest {fib['nearest_level']:g}){', in golden pocket' if fib['in_golden_pocket'] else ''}"
                     + (f"; pump peaked at the {ev['peak_fib_extension']:.2f} extension" if ev.get("peak_fib_extension") else ""))
    st = ta.get("structure") or {}
    lv = ta.get("levels") or {}
    lines.append(f"- Structure: {st.get('structure', '–')} ({st.get('higher_highs', 0)} higher highs, {st.get('higher_lows', 0)} higher lows); "
                 f"support {('$%.2f' % lv['support']['price']) if lv.get('support') else '–'}, "
                 f"resistance {('$%.2f' % lv['resistance']['price']) if lv.get('resistance') else '–'}")
    groups = {"harmonic": [], "chart": [], "candle": []}
    for p in ta.get("patterns", []):
        date_ = p.get("completed_date") or p.get("date")
        label = f"{p['name'].replace('_', ' ')} ({p['direction']}, {date_}" + (f", score {p['score']}" if "score" in p else "") + ")"
        groups[p["type"]].append(label)
    for kind, title in (("harmonic", "Harmonic patterns"), ("chart", "Chart patterns"), ("candle", "Candlesticks")):
        lines.append(f"- {title}: {', '.join(groups[kind]) or 'none'}")
    return "\n".join(lines)


def event_dossier(rec: Dict) -> str:
    seed, ev = rec["seed"], rec.get("event")
    out = [f"### {seed['ticker']} — {ev['pump_date'] if ev else seed['approx_date'] + ' (approx.)'}"]
    out.append(f"*Reported:* {seed['reported_move'] or '–'}" + (f" ([source]({seed['source_url']}))" if seed['source_url'] else ""))
    if seed.get("notes"):
        out.append(f"*Notes:* {seed['notes']}")
    if ev:
        out.append(f"*Measured:* {ev['event_type'].replace('_', ' ')}; close {_mult(ev['close_multiple'])}, "
                   f"intraday high {_mult(ev['high_multiple'])}, best {ev['run_days']}-day run {_mult(ev['run_multiple'])} "
                   f"from ${_num(ev['prev_close'])}. Qualifies: **{'yes' if rec['qualifies'] else 'no'}**")
    else:
        out.append(f"*Measured:* {rec['detection']}")

    pf = rec.get("price_features")
    if pf:
        out.append(f"*Pre-pump window ({pf['window_days']} days):* return {_pct(pf['window_return'])}, "
                   f"avg volume {_mult(pf['avg_volume_ratio'])} baseline (max day {_mult(pf['max_volume_ratio'])}), "
                   f"volatility {_mult(pf['volatility_ratio'])} baseline, RSI {_num(pf['rsi_14'], '{:.0f}')}, "
                   f"last close ${_num(pf['last_close'])}")
    if rec.get("daily_profile"):
        out.append("\n" + _table(["Day", "Date", "Close", "Return", "Volume vs baseline"], [
            [p["offset"], p["date"], _num(p["close"]), _pct(p["return"]), _mult(p["volume_ratio"])]
            for p in rec["daily_profile"]]))

    ta = rec.get("technicals")
    if ta:
        out.append("\n" + technical_summary(ta, pf or {}, ev or {}))

    ctx = rec.get("context", {})
    filings = ctx.get("sec_filings", [])
    if filings:
        out.append("\n**SEC filings in window**")
        out += [f"- {f['date']} {f['form']} ({f['group']}) — [{f['description'] or 'filing'}]({f['url']})" for f in filings[:15]]
    news = ctx.get("polygon_news", []) + ctx.get("gdelt_news", [])
    if news:
        out.append("\n**News in window**")
        out += [f"- {n['date']} {n['publisher']}: [{n['title']}]({n['url']})" for n in news[:15]]
    reddit = sorted(ctx.get("reddit", []), key=lambda r: -(r.get("score") or 0))
    if reddit:
        cf = rec.get("context_features") or {}
        out.append(f"\n**Reddit** — {cf.get('reddit_mentions')} mentions by {cf.get('reddit_unique_authors')} authors, "
                   f"avg sentiment {_num(cf.get('reddit_avg_sentiment'))}, mentions per day {cf.get('reddit_mentions_per_day')}")
        for r in reddit[:8]:
            label = r["title"] or r["text"][:120]
            out.append(f"- {r['date']} r/{r['subreddit']} (score {r['score']}): [{label}]({r['url']})")

    missing = [f"{k}: {STATUS_MARK.get(v['status'], v['status'])}" for k, v in rec["sources"].items() if v["status"] != "ok"]
    if missing:
        out.append("\n*Gaps:* " + ", ".join(missing))
    return "\n".join(out)


def build_report(records: List[Dict], result: Dict, settings) -> str:
    rule = (f"close ≥ {settings.min_multiple:g}x the previous close on the same day" if settings.criterion == "strict"
            else f"intraday high ≥ {settings.min_multiple:g}x the previous close, or a run of up to "
                 f"{settings.max_run_days} days reaching {settings.min_multiple:g}x")
    out = [
        "# Pump Research Report",
        f"Criterion: **{settings.criterion}** ({rule}). Pre-pump window: {settings.pre_window_days} trading days; "
        f"baseline: the {settings.baseline_days} trading days before that.",
        "",
        f"- Candidates researched: **{result['n_records']}**",
        f"- Pump located in price data: **{result['n_located']}**",
        f"- Clear the criterion: **{result['n_qualifying']}**",
        f"- Events with a usable pre-pump window: **{result['n_with_window']}**, compared with **{result['n_controls']}** "
        "ordinary windows from the same stocks",
    ]

    out += ["", "## Data coverage", _table(["Source"] + sorted({s for v in result["coverage"].values() for s in v}),
            [[src] + [counts.get(s, 0) for s in sorted({s for v in result["coverage"].values() for s in v})]
             for src, counts in sorted(result["coverage"].items())])]

    rows = []
    for rec in records:
        ev, pf, cf = rec.get("event") or {}, rec.get("price_features") or {}, rec.get("context_features") or {}
        rows.append([rec["seed"]["ticker"], ev.get("pump_date", rec["seed"]["approx_date"] + "?"), rec["seed"]["category"],
                     ev.get("event_type", "–"), _mult(ev.get("close_multiple")), _mult(ev.get("high_multiple")),
                     _mult(ev.get("run_multiple")), "yes" if rec["qualifies"] else "no",
                     _pct(pf.get("window_return")), _mult(pf.get("avg_volume_ratio")),
                     _known(cf.get("filings_total")), _known(cf.get("reddit_mentions"))])
    out += ["", "## Events", _table(["Ticker", "Pump date", "Category", "Type", "Close", "High", "Run", "Qualifies",
                                     "Window return", "Volume vs base", "Filings", "Reddit"], rows)]

    if result["feature_comparison"]:
        out += ["", "## What separates pre-pump windows from ordinary ones",
                "`P(event higher)` is the chance a random pre-pump window scores higher than a random ordinary window "
                "for the same stocks: 0.5 means no difference, near 1 or 0 means a strong tell. Small samples: treat "
                "p-values as rough.", "",
                _table(["Feature", "Pre-pump median", "Ordinary median", "P(event higher)", "p-value", "n (events/ordinary)"], [
                    [r["feature"], _num(r["event_median"], "{:.3g}"), _num(r["control_median"], "{:.3g}"),
                     _num(r["prob_event_higher"]), _num(r["p_value"], "{:.3f}"), f"{r['events_n']}/{r['controls_n']}"]
                    for r in result["feature_comparison"]])]

    if result.get("boolean_comparison"):
        out += ["", "## Yes/no technical signals: before pumps vs ordinary windows",
                _table(["Signal", "Before pumps", "Ordinary", "Lift", "p-value"], [
                    [r["feature"], _pct(r["event_rate"]).lstrip("+"), _pct(r["control_rate"]).lstrip("+"),
                     _mult(r["lift"]), _num(r["p_value"], "{:.3f}")] for r in result["boolean_comparison"][:25]])]

    if result["signal_rates"]:
        out += ["", "## Warning signs present before the pump",
                _table(["Signal", "Share of events", "Events with data"], [
                    [r["signal"], _pct(r["share_true"]).lstrip("+") if r["share_true"] is not None else "–", r["events_with_data"]]
                    for r in result["signal_rates"]])]

    if result["countdown"]:
        out += ["", "## Countdown: median day-by-day behavior before the pump",
                _table(["Day", "Events", "Median return", "Median volume vs baseline"], [
                    [c["offset"], c["events"], _pct(c["median_return"]), _mult(c["median_volume_ratio"])]
                    for c in result["countdown"]])]

    out += ["", "## Event dossiers", ""]
    out += [event_dossier(rec) + "\n" for rec in records]
    return "\n".join(out)


def write_report(records, result, settings) -> str:
    path = os.path.join(settings.data_dir, "pump_report.md")
    with open(path, "w") as f:
        f.write(build_report(records, result, settings))
    return path
