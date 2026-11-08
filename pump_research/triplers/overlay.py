"""
Historical overlays for the Tripler Lab: every tripler's price path lined up on its launch bar, the
ordinary-window band for comparison, the nearest historical analogs of a live chart, and event charts
with the Fibonacci and Gann drawing tools.
"""

import json
import math
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

SHAPE_BARS = {"1d": 20, "4h": 20, "1h": 35}     # bars before launch compared when matching a live chart
MAX_LINES = 160


def load(data_dir: str) -> Optional[Dict]:
    path = os.path.join(data_dir, "dataset.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    try:
        with open(os.path.join(data_dir, "analysis.json")) as f:
            data["analysis"] = json.load(f)
    except (OSError, ValueError):
        data["analysis"] = None
    return data


def load_event(data_dir: str, event_id: str) -> Optional[Dict]:
    if not all(c.isalnum() or c in "_-" for c in event_id):
        return None
    path = os.path.join(data_dir, "events", f"{event_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _q(vals, q):
    vals = [v for v in vals if v is not None and v > 0]
    return round(float(np.quantile(vals, q)), 4) if len(vals) >= 3 else None


def bands(records: List[Dict], tf: str) -> Dict:
    """Median and middle-half band of the relative close at every bar offset, triplers vs ordinary windows"""
    out = {}
    for group, pick in (("triplers", lambda r: not r.get("control")), ("ordinary", lambda r: r.get("control"))):
        by_off: Dict[int, List[float]] = {}
        for r in records:
            p = (r.get("paths") or {}).get(tf)
            if not p or not pick(r):
                continue
            for o, c in zip(p["offset"], p["close"]):
                by_off.setdefault(o, []).append(c)
        offs = sorted(by_off)
        out[group] = {"offset": offs, "median": [_q(by_off[o], 0.5) for o in offs], "q1": [_q(by_off[o], 0.25) for o in offs],
                      "q3": [_q(by_off[o], 0.75) for o in offs], "n": max((len(v) for v in by_off.values()), default=0)}
    return out


def overlay_data(data: Dict, tf: str = "1d", max_ordinary: int = 400) -> Dict:
    """Everything the overlay and 3D views draw for one timeframe"""
    recs = data["records"]
    trip = [r for r in recs if not r.get("control") and tf in (r.get("paths") or {})]
    ctl = [r for r in recs if r.get("control") and tf in (r.get("paths") or {})]
    step = max(1, len(ctl) // max_ordinary)

    def pack(r):
        p = r["paths"][tf]
        return {"id": r["id"], "ticker": r["ticker"], "date": r["launch_date"], "peak": r.get("peak_multiple"),
                "days": r.get("days_to_triple"), "offset": p["offset"], "close": p["close"], "volume": p["volume"],
                "fired": (r.get("fired") or {}).get(tf, [])}
    trip.sort(key=lambda r: -(r.get("peak_multiple") or 0))
    return {"timeframe": tf, "bands": bands(recs, tf), "triplers": [pack(r) for r in trip],
            "ordinary": [pack(r) for r in ctl[::step]], "meta": data.get("meta", {})}


def shape(closes: List[float], bars: int) -> Optional[np.ndarray]:
    """Log price path over the last `bars` bars, ending at 0 (the launch close or today's close)"""
    c = np.array([x for x in closes if x], float)
    if len(c) < bars + 1:
        return None
    seg = np.log(c[-bars - 1:])
    return seg - seg[-1]


def analogs(data: Dict, live_closes: List[float], tf: str = "1d", k: int = 30) -> Dict:
    """The k historical windows whose run-up looks most like the live chart, and how many of them tripled"""
    bars = SHAPE_BARS.get(tf, 20)
    target = shape(live_closes, bars)
    if target is None:
        return {"error": f"need at least {bars + 1} bars"}
    scored = []
    for r in data["records"]:
        p = (r.get("paths") or {}).get(tf)
        if not p or 0 not in p["offset"]:
            continue
        z = p["offset"].index(0)
        s = shape(p["close"][:z + 1], bars)
        if s is None:
            continue
        scored.append((float(np.sqrt(np.mean((s - target) ** 2))), r, z))
    if not scored:
        return {"error": "no historical windows on this timeframe yet"}
    scored.sort(key=lambda x: x[0])
    near = scored[:k]
    base = sum(not r.get("control") for _, r, _ in scored) / len(scored)
    share = sum(not r.get("control") for _, r, _ in near) / len(near)
    return {"timeframe": tf, "bars_compared": bars, "k": len(near), "tripler_share": round(share, 3),
            "base_share": round(base, 3), "lift": round(share / base, 2) if base else None,
            "matches": [{"id": r["id"], "ticker": r["ticker"], "date": r["launch_date"], "tripler": not r.get("control"),
                         "distance": round(d, 4), "peak": r.get("peak_multiple") or r.get("forward_multiple"),
                         "offset": r["paths"][tf]["offset"], "close": r["paths"][tf]["close"]} for d, r, z in near[:12]]}


def live_closes(ticker: str, tf: str, loader=None) -> Optional[pd.DataFrame]:
    if loader is None:
        from ..scanlab.runner import load_prices as loader
    return loader([ticker], tf).get(ticker)


# --- Event charts ---------------------------------------------------------------------------------------

TOOL_GROUPS = {"spiral": ["Fib spiral"], "gann_fan": ["Gann fan"], "speed_fan": ["Fib speed fan"], "circles": ["Fib circles"],
               "arcs": ["Fib speed arcs"], "pitchfan": ["Pitchfan"], "channel": ["Fib channel"], "gann_box": ["Gann box"],
               "extension": ["Trend fib extension"], "time": ["Fib time zones", "Trend fib time"]}


def frame(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("date"))
    if all(t.hour == 0 and t.minute == 0 for t in df.index):
        df.index = df.index.date
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def event_chart(rec: Dict, tf: str = "1d", tools=("spiral", "gann_fan")) -> Optional[Dict]:
    """The event's chart up to a few weeks after launch, with drawings anchored on the swings before launch"""
    from ..charts import price_chart
    from ..technicals import technical_snapshot
    from .collect import end_position, to_4h
    if tf == "1d":
        rows = rec.get("rows_1d")
    else:
        rows = rec.get("rows_1h")
    if not rows:
        return None
    df = frame(rows)
    if tf == "4h":
        df = to_4h(df.set_axis(pd.to_datetime(df.index)))
    pos = end_position(df if tf != "1d" else df.set_axis(pd.to_datetime(df.index)), rec["launch_date"], tf != "1d")
    if pos is None or pos < 20:
        return None
    per = {"1d": 1, "4h": 2, "1h": 7}[tf]
    snap = technical_snapshot(df, pos, 10 * per)
    lo = max(0, pos - (120 if tf == "1d" else 40 * per))
    view = df.iloc[lo:]
    fmt = (lambda d: d.isoformat()[:10]) if tf == "1d" else (lambda d: d.isoformat()[:16])
    rows_out = [{"date": fmt(d), **r} for d, r in zip(view.index, view.to_dict("records"))]
    dates = [r["date"] for r in rows_out]
    window = [d for d in dates if d[:10] in set(rec["window_dates"])]
    if tf != "1d":
        # drawings come back with full ISO timestamps; match the chart's minute precision
        for ov in (snap.get("fib_gann") or {}).get("overlays", []):
            ov["points"] = [(p[0][:16], p[1]) for p in ov["points"]]
        for g, ds in ((snap.get("fib_gann") or {}).get("time_lines") or {}).items():
            snap["fib_gann"]["time_lines"][g] = [d[:16] for d in ds]
        for p in snap.get("patterns", []):
            for key in ("date", "completed_date", "start_date"):
                if p.get(key):
                    p[key] = p[key][:16]
            for pt in p.get("points", []):
                pt["date"] = pt["date"][:16]
    snap["patterns"] = [p for p in snap.get("patterns", []) if (p.get("completed_date") or p.get("date") or "") in dates
                        or p.get("type") == "harmonic"]
    launch = next((d for d in reversed(dates) if d[:10] == rec["launch_date"]), None)
    fig = price_chart(rows_out, snap, window, launch, f"{rec['ticker']} · launch {rec['launch_date']}")
    show = {g for t in tools for g in TOOL_GROUPS.get(t, [])}
    for tr in fig["data"]:
        if tr.get("legendgroup") in TOOL_GROUPS_ALL:
            tr["visible"] = True if tr["legendgroup"] in show else "legendonly"
    for a in fig["layout"].get("annotations", []):
        if a.get("text") == "PUMP":
            a["text"] = "LAUNCH"
        if a.get("text") == "PRE-PUMP WINDOW":
            a["text"] = "PRE-LAUNCH WINDOW"
    fig["layout"]["height"] = 520
    if tf != "1d":
        fig["layout"]["xaxis"].update(tickangle=0, nticks=7)
    return {"figure": fig, "fib_gann": {k: (snap.get("fib_gann") or {}).get(k) for k in ("price_confluence", "time_confluence", "anchors")},
            "fibonacci": snap.get("fibonacci")}


TOOL_GROUPS_ALL = {g for gs in TOOL_GROUPS.values() for g in gs}


def lift_matrix(analysis: Optional[Dict], max_rows: int = 40) -> Dict:
    """Block × timeframe lift grid for the readings heatmap"""
    if not analysis:
        return {"rows": [], "cols": [], "lift": [], "rate": []}
    rows = [r for r in analysis.get("comparison", []) if r["reading"].startswith("blk_") and r.get("kind") == "flag"]
    best: Dict[str, float] = {}
    for r in rows:
        best[r["label"]] = min(best.get(r["label"], 1.0), r["q"])
    labels = sorted(best, key=best.get)[:max_rows]
    cols = ["1h", "4h", "1d"]
    grid = {(r["label"], r["timeframe"]): r for r in rows}
    lift = [[(grid.get((lb, c)) or {}).get("lift") for c in cols] for lb in labels]
    rate = [[(grid.get((lb, c)) or {}).get("tripler_rate") for c in cols] for lb in labels]
    q = [[(grid.get((lb, c)) or {}).get("q") for c in cols] for lb in labels]
    return {"rows": labels, "cols": cols, "lift": [[None if v is None or not math.isfinite(v) else round(math.log2(max(v, 1e-3)), 3)
                                                    for v in row] for row in lift], "lift_raw": lift, "rate": rate, "q": q}
