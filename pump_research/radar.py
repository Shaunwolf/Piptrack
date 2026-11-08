"""
Daily radar: run a few Scan Lab scans after each close, keep every pick, and grade old picks by what
happened next. Over time this measures which scans, and which individual blocks, actually precede big
moves, compared with everything else scanned the same day (the base rate).

    python -m pump_research radar run   --dir radar     # today's picks → radar/picks/YYYY-MM-DD.json
    python -m pump_research radar grade --dir radar     # forward returns of past picks → radar/report.md

A pick is graded once 10 trading days have passed: its largest gain from that day's close to any later
high within 5 and 10 days, and its 10-day close-to-close return.
"""

import json
import os
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional

import numpy as np

from .scanlab import expand_universe, preset, run_scan
from .scanlab.runner import load_prices

RADAR_SCANS = ["squeeze_setup", "pump_dna", "momentum_breakout"]
THRESHOLDS = (0.2, 0.5, 1.0)       # +20%, +50%, +100% within 10 trading days
HORIZON = 10


def run_radar(out_dir: str, scans: List[str] = RADAR_SCANS, extra_universe: Optional[Dict] = None,
              loader: Callable = load_prices, model=None, settings=None, today: Optional[date] = None, **run_kwargs) -> Dict:
    """Run each scan over its universe; store matches plus everything scanned (the comparison group)"""
    today = today or datetime.now(timezone.utc).date()
    snapshot = {"date": today.isoformat(), "scans": {}}
    for key in scans:
        p = preset(key)
        universe = p["universe"]
        if extra_universe:
            universe = {k: list(universe.get(k, [])) + list(extra_universe.get(k, [])) for k in ("sectors", "lists", "tickers")}
        u = expand_universe(universe)
        out = run_scan(p["spec"], u["tickers"], u["sector_of"], loader=loader, model=model, settings=settings, **run_kwargs)
        snapshot["scans"][key] = {
            "title": p["title"], "scanned": [r["ticker"] for r in out["results"]],
            "closes": {r["ticker"]: r["price"] for r in out["results"]},
            "as_of": max((r["as_of"] for r in out["results"]), default=None),
            "picks": [{"ticker": r["ticker"], "score": r["score"], "price": r["price"], "sector": r["sector"], "fired": r["fired"]}
                      for r in out["results"] if r["matched"]],
        }
    os.makedirs(os.path.join(out_dir, "picks"), exist_ok=True)
    with open(os.path.join(out_dir, "picks", f"{today.isoformat()}.json"), "w") as f:
        json.dump(snapshot, f, indent=1)
    with open(os.path.join(out_dir, "latest.json"), "w") as f:
        json.dump(snapshot, f, indent=1)
    return snapshot


def forward_stats(prices, asof: str, close: float, horizon: int = HORIZON) -> Optional[Dict]:
    """Max gain to a later high within 5 and 10 bars after `asof`, and the close-to-close return over 10"""
    after = prices[[str(d)[:10] > asof for d in prices.index]]
    if len(after) < horizon or not close:
        return None
    hi5, hi10 = float(after["high"].iloc[:5].max()), float(after["high"].iloc[:horizon].max())
    return {"max_gain_5": hi5 / close - 1, "max_gain_10": hi10 / close - 1, "return_10": float(after["close"].iloc[horizon - 1]) / close - 1}


def _rates(gains: List[float]) -> Dict:
    if not gains:
        return {"n": 0}
    g = np.array(gains)
    return {"n": len(g), "median_max_gain_10": float(np.median(g)),
            **{f"hit_{int(t * 100)}": float((g >= t).mean()) for t in THRESHOLDS}}


def grade(out_dir: str, loader: Callable = load_prices) -> Dict:
    """Grade every stored day that is at least 10 trading days old; returns and writes the learned summary"""
    pick_dir = os.path.join(out_dir, "picks")
    days = sorted(f[:-5] for f in os.listdir(pick_dir) if f.endswith(".json")) if os.path.isdir(pick_dir) else []
    picks_by_scan, base_by_scan = defaultdict(list), defaultdict(list)
    per_block = defaultdict(list)
    graded_days = []
    for day in days:
        with open(os.path.join(pick_dir, f"{day}.json")) as f:
            snap = json.load(f)
        tickers = sorted({t for s in snap["scans"].values() for t in s["scanned"]})
        if not tickers:
            continue
        prices = loader(tickers, "1d")
        complete = False
        for key, s in snap["scans"].items():
            asof = s.get("as_of") or day
            for t in s["scanned"]:
                df = prices.get(t)
                stats = forward_stats(df, asof, s["closes"].get(t)) if df is not None else None
                if stats is None:
                    continue
                complete = True
                base_by_scan[key].append(stats["max_gain_10"])
            for p in s["picks"]:
                df = prices.get(p["ticker"])
                stats = forward_stats(df, asof, p["price"]) if df is not None else None
                if stats is None:
                    continue
                picks_by_scan[key].append(stats["max_gain_10"])
                for title in p["fired"]:
                    per_block[title].append(stats["max_gain_10"])
        if complete:
            graded_days.append(day)
    summary = {"graded_days": graded_days, "pending_days": [d for d in days if d not in graded_days], "scans": {}, "blocks": {}}
    for key in set(picks_by_scan) | set(base_by_scan):
        pk, bs = _rates(picks_by_scan[key]), _rates(base_by_scan[key])
        lift = (pk.get("hit_20", 0) / bs["hit_20"]) if bs.get("hit_20") else None
        summary["scans"][key] = {"picks": pk, "base_rate": bs, "lift_at_20pct": lift}
    for title, gains in per_block.items():
        summary["blocks"][title] = _rates(gains)
    with open(os.path.join(out_dir, "grades.json"), "w") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict) -> str:
    lines = ["# Squeeze radar: how the picks did", "",
             f"Graded days: {len(summary['graded_days'])} · waiting for 10 trading days to pass: {len(summary['pending_days'])}", "",
             "A pick's outcome is its largest gain to any high within the next 10 trading days. "
             "The base rate is the same measure for every stock the scan looked at that day.", "",
             "| Scan | Picks | Hit +20% | Hit +50% | Hit +100% | Base rate +20% | Lift | Median max gain |",
             "|---|---|---|---|---|---|---|---|"]
    for key, s in sorted(summary["scans"].items()):
        p, b = s["picks"], s["base_rate"]
        if not p.get("n"):
            lines.append(f"| {key} | 0 | – | – | – | {b.get('hit_20', 0):.0%} | – | – |")
            continue
        lift = f"{s['lift_at_20pct']:.1f}×" if s["lift_at_20pct"] else "–"
        lines.append(f"| {key} | {p['n']} | {p['hit_20']:.0%} | {p['hit_50']:.0%} | {p['hit_100']:.0%} | "
                     f"{b.get('hit_20', 0):.0%} | {lift} | {p['median_max_gain_10']:+.0%} |")
    lines += ["", "## Which blocks fired on the picks that ran", "", "| Block | Picks it fired on | Hit +20% | Hit +50% |", "|---|---|---|---|"]
    for title, r in sorted(summary["blocks"].items(), key=lambda kv: -kv[1].get("hit_20", 0)):
        if r.get("n"):
            lines.append(f"| {title} | {r['n']} | {r['hit_20']:.0%} | {r['hit_50']:.0%} |")
    return "\n".join(lines) + "\n"
