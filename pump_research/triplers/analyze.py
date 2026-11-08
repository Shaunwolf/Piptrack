"""
Which readings come before triplers more often than before ordinary windows, on each timeframe.

Every block hit and every 0/1 snapshot flag is a 2×2 test (Fisher exact); numeric readings compare
distributions (Mann-Whitney). p-values are corrected for the number of tests (Benjamini-Hochberg),
because with hundreds of readings some will look good by luck.

The Tripler DNA scan is learned on the earlier 70% of launches and scored on the later 30%, so the
lift it reports is out of sample.
"""

import json
import math
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

from ..scanlab.engine import BLOCKS

MIN_EVENTS = 8
TRAIN_SHARE = 0.7


def bh(pvals: List[float]) -> List[float]:
    n = len(pvals)
    if not n:
        return []
    order = np.argsort(pvals)
    q = np.empty(n)
    prev = 1.0
    for rank, i in reversed(list(enumerate(order, start=1))):
        prev = min(prev, pvals[i] * n / rank)
        q[i] = prev
    return [float(x) for x in q]


def _binary(col: pd.Series) -> bool:
    vals = set(col.dropna().unique())
    return bool(vals) and vals <= {0, 1}


def label(col: str) -> str:
    if col.startswith(("blk_", "str_")):
        blk = BLOCKS.get(col[4:])
        return blk.title if blk else col[4:]
    try:
        from ..labels import feature_label
        return feature_label(col[4:] if col.startswith("ctx_") else col)
    except Exception:
        return col


def compare(df: pd.DataFrame) -> List[Dict]:
    """Every reading on every timeframe: rate (or median) before triplers vs ordinary windows"""
    out = []
    skip = {"id", "ticker", "launch_date", "timeframe", "tripler", "price_band"}
    for tf, part in df.groupby("timeframe"):
        ev, ct = part[part["tripler"]], part[~part["tripler"]]
        if len(ev) < MIN_EVENTS or len(ct) < MIN_EVENTS:
            continue
        for col in part.columns:
            if col in skip or col.startswith("str_"):
                continue
            a, b = ev[col].dropna(), ct[col].dropna()
            if len(a) < MIN_EVENTS or len(b) < MIN_EVENTS:
                continue
            row = {"timeframe": tf, "reading": col, "label": label(col), "n_triplers": int(len(a)), "n_ordinary": int(len(b))}
            if _binary(part[col]):
                ha, hb = int(a.sum()), int(b.sum())
                if ha + hb == 0:
                    continue
                pa, pb = ha / len(a), hb / len(b)
                _, p = fisher_exact([[ha, len(a) - ha], [hb, len(b) - hb]])
                row.update(kind="flag", tripler_rate=round(pa, 4), ordinary_rate=round(pb, 4),
                           lift=round((pa + 1e-9) / (pb + 1e-9), 2) if pb else (None if not pa else 99.0), p=float(p))
            else:
                if a.nunique() < 2 and b.nunique() < 2:
                    continue
                try:
                    _, p = mannwhitneyu(a, b, alternative="two-sided")
                except ValueError:
                    continue
                row.update(kind="number", tripler_median=round(float(a.median()), 5), ordinary_median=round(float(b.median()), 5),
                           tripler_q1=round(float(a.quantile(0.25)), 5), tripler_q3=round(float(a.quantile(0.75)), 5),
                           p=float(p))
            out.append(row)
    for row, q in zip(out, bh([r["p"] for r in out])):
        row["q"] = round(q, 5)
        row["p"] = round(row["p"], 6)
    out.sort(key=lambda r: (r["q"], -(r.get("lift") or 0)))
    return out


def _hits(part: pd.DataFrame, pick: Dict) -> pd.Series:
    """Strength of one pick on each window: the block's recorded strength, or a learned threshold on a reading"""
    if pick.get("feature"):
        col = part[pick["feature"]]
        hit = col <= pick["value"] if pick["condition"] == "below" else col >= pick["value"]
        return hit.fillna(False).astype(float)
    return part[f"str_{pick['block']}"].fillna(0)


def best_threshold(ev: pd.Series, ct: pd.Series, direction: str) -> Optional[Dict]:
    """The level that best separates triplers from ordinary windows (largest hit-rate gap)"""
    vals = np.unique(np.quantile(pd.concat([ev, ct]).to_numpy(float), np.linspace(0.05, 0.95, 37)))
    best = None
    for t in vals:
        a = (ev <= t).mean() if direction == "below" else (ev >= t).mean()
        b = (ct <= t).mean() if direction == "below" else (ct >= t).mean()
        if best is None or a - b > best["gap"]:
            best = {"value": float(t), "gap": float(a - b), "rate": float(a), "ordinary_rate": float(b)}
    return best


def _nice(v: float) -> float:
    if v == 0 or not math.isfinite(v):
        return 0.0
    digits = 2 - int(math.floor(math.log10(abs(v))))
    return round(v, max(0, digits))


def _score(part: pd.DataFrame, picks: List[Dict]) -> pd.Series:
    wsum = sum(p["weight"] for p in picks)
    s = sum(p["weight"] * _hits(part, p) for p in picks)
    return 100 * s / wsum if wsum else pd.Series(0, index=part.index)


def learn_scan(df: pd.DataFrame, timeframe: str = "1d", max_blocks: int = 8, min_lift: float = 1.5,
               min_rate: float = 0.15, max_q: float = 0.25) -> Optional[Dict]:
    """Pick the blocks that best separate triplers (earlier launches), then test the blended score on later ones"""
    part = df[df["timeframe"] == timeframe].sort_values("launch_date")
    ev_dates = part.loc[part["tripler"], "launch_date"].sort_values()
    if len(ev_dates) < 2 * MIN_EVENTS:
        return None
    cut = ev_dates.iloc[int(len(ev_dates) * TRAIN_SHARE)]
    train, test = part[part["launch_date"] < cut], part[part["launch_date"] >= cut]
    from ..scanlab.blocks_indicators import reading_options
    readable = {k for k, _ in reading_options()}
    candidates = []
    for r in compare(train):
        if r["q"] > max_q:
            continue
        if r["reading"].startswith("blk_") and r.get("kind") == "flag":
            if r.get("lift") and r["lift"] >= min_lift and r["tripler_rate"] >= min_rate:
                candidates.append({"block": r["reading"][4:], "title": r["label"], "lift": r["lift"], "rate": r["tripler_rate"]})
        elif r.get("kind") == "number" and r["reading"] in readable:
            ev, ct = train.loc[train["tripler"], r["reading"]].dropna(), train.loc[~train["tripler"], r["reading"]].dropna()
            direction = "below" if r["tripler_median"] < r["ordinary_median"] else "above"
            t = best_threshold(ev, ct, direction)
            if t and t["ordinary_rate"] < 1 and t["rate"] >= min_rate:
                lift = t["rate"] / max(t["ordinary_rate"], 1e-3)
                if lift >= min_lift:
                    value = _nice(t["value"])
                    candidates.append({"block": "chart_reading", "feature": r["reading"], "condition": direction, "value": value,
                                       "title": f"{r['label']} {'≤' if direction == 'below' else '≥'} {value:g}",
                                       "lift": round(lift, 2), "rate": round(t["rate"], 3)})
    candidates.sort(key=lambda c: -c["lift"] * c["rate"])
    picks, kept_hits = [], []
    for c in candidates:
        h = _hits(train, c)
        # Skip near-duplicates (the many "price vs moving average" readings say much the same thing)
        if any(abs(np.corrcoef(h, k)[0, 1]) > 0.5 for k in kept_hits if h.std() > 0 and k.std() > 0):
            continue
        c["weight"] = round(min(3.0, max(0.5, math.log2(max(c["lift"], 1.01)))), 2)
        picks.append(c)
        kept_hits.append(h)
        if len(picks) >= max_blocks:
            break
    if not picks:
        return {"timeframe": timeframe, "picks": [], "cut": cut, "note": "no block cleared the bar on the training launches"}

    def evaluate(frame, threshold):
        s = _score(frame, picks)
        sel = s >= threshold
        ev = frame["tripler"]
        base = ev.mean()
        prec = ev[sel].mean() if sel.any() else 0.0
        return {"windows": int(len(frame)), "flagged": int(sel.sum()), "recall": round(float(ev[sel].sum() / max(1, ev.sum())), 3),
                "tripler_share_flagged": round(float(prec), 4), "tripler_share_all": round(float(base), 4),
                "lift": round(float(prec / base), 2) if base and sel.any() else None}

    best = None
    for th in range(5, 100, 5):
        m = evaluate(train, th)
        if m["recall"] >= 0.25 and m["lift"] and (best is None or m["lift"] > best[1]["lift"]):
            best = (th, m)
    threshold = best[0] if best else 50
    return {"timeframe": timeframe, "cut": cut, "picks": picks, "min_score": threshold,
            "train": evaluate(train, threshold), "test": evaluate(test, threshold)}


def to_preset(learned: Dict) -> Optional[Dict]:
    if not learned or not learned.get("picks"):
        return None
    test = learned.get("test") or {}
    tf = learned["timeframe"]
    return {
        "title": f"Tripler DNA ({ {'1d': 'daily', '1h': 'hourly', '4h': '4-hour'}.get(tf, tf) })", "style": "tripler",
        "tagline": (f"Learned from stocks that tripled within 3 weeks: on later launches, flagged windows were "
                    f"{test.get('lift')}× as likely to be triplers as an average window.") if test.get("lift") else
                   "Learned from stocks that tripled within 3 weeks.",
        "universe": {"lists": ["trending", "reg_sho", "pump_history", "meme"]},
        "timeframe": tf,
        "spec": {"match": "all", "mode": "ranked", "min_score": learned["min_score"], "groups": [
            {"name": "Tripler build-up", "logic": "atleast", "min": 1, "weight": 1,
             "blocks": [{"type": p["block"], "weight": p["weight"], "negate": False,
                         "params": {"reading": p["feature"], "condition": p["condition"], "value": p["value"]} if p.get("feature") else {}}
                        for p in learned["picks"]]}]},
        "learned": {k: learned[k] for k in ("cut", "train", "test", "min_score")},
    }


def multi_timeframe(df: pd.DataFrame) -> List[Dict]:
    """Blocks firing on 2+ timeframes at once before a launch vs ordinary windows (confluence across charts)"""
    blocks = sorted({c[4:] for c in df.columns if c.startswith("blk_")})
    wide = df.pivot_table(index=["id", "tripler"], columns="timeframe", values=[f"blk_{b}" for b in blocks], aggfunc="first")
    out = []
    for b in blocks:
        try:
            sub = wide[f"blk_{b}"]
        except KeyError:
            continue
        if sub.shape[1] < 2:
            continue
        both = (sub.fillna(0).sum(axis=1) >= 2).astype(int)
        has = sub.notna().sum(axis=1) >= 2
        both = both[has]
        trip = both.index.get_level_values("tripler")
        a, b_ = both[trip], both[~trip]
        if len(a) < MIN_EVENTS or len(b_) < MIN_EVENTS or a.sum() + b_.sum() == 0:
            continue
        _, p = fisher_exact([[int(a.sum()), int(len(a) - a.sum())], [int(b_.sum()), int(len(b_) - b_.sum())]])
        pa, pb = a.mean(), b_.mean()
        out.append({"block": b, "label": label(f"blk_{b}"), "tripler_rate": round(float(pa), 4), "ordinary_rate": round(float(pb), 4),
                    "lift": round(float(pa / pb), 2) if pb else None, "p": float(p)})
    for row, q in zip(out, bh([r["p"] for r in out])):
        row["q"] = round(q, 5)
    out.sort(key=lambda r: r["q"])
    return out


def analyze(out_dir: str) -> Dict:
    df = pd.read_csv(os.path.join(out_dir, "readings.csv.gz"))
    df["tripler"] = df["tripler"].astype(str).str.lower().isin(("true", "1"))
    with open(os.path.join(out_dir, "dataset.json")) as f:
        data = json.load(f)
    comparison = compare(df)
    learned = {tf: learn_scan(df, tf) for tf in ("1d", "4h", "1h")}
    result = {"meta": data.get("meta", {}), "comparison": comparison, "multi_timeframe": multi_timeframe(df),
              "learned": learned, "presets": {tf: to_preset(v) for tf, v in learned.items() if to_preset(v)}}
    with open(os.path.join(out_dir, "analysis.json"), "w") as f:
        json.dump(result, f, indent=1, default=str)
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write(render_report(result))
    return result


def render_report(res: Dict) -> str:
    m = res.get("meta", {})
    lines = [f"# Triplers: what came before stocks that tripled within 3 weeks", "",
             f"{m.get('triplers', 0)} triplers and {m.get('controls', 0)} ordinary windows (same price bands) in "
             f"{m.get('stocks_with_prices', 0)} listed stocks, collected {m.get('collected_at', '')}. Hourly and 4-hour "
             f"readings exist for launches after {m.get('hourly_reach_from', '')}.", "",
             "## Strongest differences (q ≤ 0.10)", "", "| Chart | Reading | Before triplers | Ordinary | Lift | q |", "|---|---|---|---|---|---|"]
    for r in [r for r in res["comparison"] if r["q"] <= 0.10][:40]:
        if r["kind"] == "flag":
            lines.append(f"| {r['timeframe']} | {r['label']} | {r['tripler_rate']:.0%} | {r['ordinary_rate']:.0%} | {r['lift']}× | {r['q']:.3f} |")
        else:
            lines.append(f"| {r['timeframe']} | {r['label']} | median {r['tripler_median']:g} | {r['ordinary_median']:g} | | {r['q']:.3f} |")
    lines += ["", "## Learned scans (out-of-sample check on the latest 30% of launches)", ""]
    for tf, l in res["learned"].items():
        if not l or not l.get("picks"):
            lines.append(f"- **{tf}**: {(l or {}).get('note', 'not enough triplers')}")
            continue
        t = l["test"]
        lines.append(f"- **{tf}**: {', '.join(p['title'] for p in l['picks'])}; min score {l['min_score']}. Later launches: "
                     f"{t['flagged']} of {t['windows']} windows flagged, {t['recall']:.0%} of triplers caught, lift {t['lift']}×.")
    lines += ["", "Not investment advice. Survivorship bias: stocks delisted since are missing, so failed pumps are under-counted."]
    return "\n".join(lines) + "\n"
