"""
Cross-event analysis: what do pre-pump windows have in common, and how do they
differ from ordinary windows for the same stocks?
"""

from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

# Price features compared between pre-pump and control windows
COMPARED_FEATURES = [
    "window_return", "window_volatility", "volatility_ratio", "avg_volume_ratio", "max_volume_ratio",
    "last3_volume_ratio", "volume_trend_slope", "up_days_share", "avg_range_pct", "gap_ups_5pct",
    "rsi_14", "close_vs_period_low", "last_close", "avg_dollar_volume",
]

# Simple yes/no warning signs checked for every event window
SIGNALS = {
    "volume_2x_baseline": ("avg_volume_ratio", lambda v: v >= 2),
    "volume_spike_5x_day": ("max_volume_ratio", lambda v: v >= 5),
    "volume_rising": ("volume_trend_slope", lambda v: v > 0.05),
    "volatility_1_5x_baseline": ("volatility_ratio", lambda v: v >= 1.5),
    "sub_5_dollar_price": ("last_close", lambda v: v < 5),
    "sub_1_dollar_price": ("last_close", lambda v: v < 1),
    "oversold_rsi_below_35": ("rsi_14", lambda v: v < 35),
    "already_up_20pct": ("window_return", lambda v: v >= 0.20),
    "reddit_chatter_accelerating": ("reddit_mention_acceleration", lambda v: v >= 2),
    "offering_filing_in_window": ("filings_offering", lambda v: v >= 1),
    "any_news_in_window": ("news_articles", lambda v: v >= 1),
}


def event_frame(records: List[Dict], qualifying_only=False) -> pd.DataFrame:
    rows = []
    for rec in records:
        known_context = any(v is not None for v in (rec.get("context_features") or {}).values())
        if not rec.get("price_features") and not known_context:
            continue
        if qualifying_only and not rec.get("qualifies"):
            continue
        ctx = {k: v for k, v in (rec.get("context_features") or {}).items() if not isinstance(v, list)}
        rows.append({"id": rec["id"], "category": rec["seed"]["category"],
                     "qualifies": rec.get("qualifies"), **(rec.get("price_features") or {}), **ctx})
    return pd.DataFrame(rows)


def control_frame(records: List[Dict]) -> pd.DataFrame:
    rows = [{"id": rec["id"], **c} for rec in records for c in rec.get("controls", [])]
    return pd.DataFrame(rows)


def compare_features(events: pd.DataFrame, controls: pd.DataFrame) -> List[Dict]:
    """Median pre-pump vs control value per feature, with a Mann-Whitney test, ranked by separation"""
    out = []
    for feat in COMPARED_FEATURES:
        if feat not in events or feat not in controls:
            continue
        e = pd.to_numeric(events[feat], errors="coerce").dropna()
        c = pd.to_numeric(controls[feat], errors="coerce").dropna()
        if len(e) < 3 or len(c) < 3:
            continue
        stat, p = mannwhitneyu(e, c, alternative="two-sided")
        # Probability a random pre-pump window scores higher than a random control window
        auc = stat / (len(e) * len(c))
        out.append({
            "feature": feat, "events_n": len(e), "controls_n": len(c),
            "event_median": float(e.median()), "control_median": float(c.median()),
            "prob_event_higher": float(auc), "p_value": float(p),
        })
    return sorted(out, key=lambda r: abs(r["prob_event_higher"] - 0.5), reverse=True)


def signal_table(events: pd.DataFrame) -> pd.DataFrame:
    """Per-event True/False/None for each warning sign (None = data unavailable)"""
    table = pd.DataFrame(index=events["id"] if "id" in events else [])
    for name, (feat, test) in SIGNALS.items():
        if feat not in events:
            table[name] = None
            continue
        table[name] = [None if pd.isna(v) else bool(test(v)) for v in events[feat]]
    return table


def signal_rates(table: pd.DataFrame) -> List[Dict]:
    rates = []
    for col in table.columns:
        known = table[col].dropna()
        rates.append({"signal": col, "events_with_data": int(len(known)),
                      "share_true": float(known.mean()) if len(known) else None})
    return sorted(rates, key=lambda r: -(r["share_true"] or 0))


def countdown_profile(records: List[Dict]) -> List[Dict]:
    """Median daily return and volume ratio by trading day before the pump, across events"""
    rows = [p for rec in records for p in rec.get("daily_profile", [])]
    if not rows:
        return []
    df = pd.DataFrame(rows)
    grouped = df.groupby("offset")
    return [
        {"offset": int(off), "events": int(len(g)),
         "median_return": float(g["return"].median()),
         "median_volume_ratio": float(pd.to_numeric(g["volume_ratio"], errors="coerce").median())}
        for off, g in grouped
    ]


def coverage(records: List[Dict]) -> Dict[str, Dict[str, int]]:
    """How many events each source succeeded / failed on"""
    cov: Dict[str, Dict[str, int]] = {}
    for rec in records:
        for source, info in rec["sources"].items():
            cov.setdefault(source, {})
            cov[source][info["status"]] = cov[source].get(info["status"], 0) + 1
    return cov


def analyze(records: List[Dict], qualifying_only=False) -> Dict:
    events = event_frame(records, qualifying_only)
    controls = control_frame([r for r in records if not qualifying_only or r.get("qualifies")])
    signals = signal_table(events) if not events.empty else pd.DataFrame()
    return {
        "n_records": len(records),
        "n_located": sum(1 for r in records if r.get("event")),
        "n_qualifying": sum(1 for r in records if r.get("qualifies")),
        "n_with_window": len(events),
        "n_controls": len(controls),
        "coverage": coverage(records),
        "feature_comparison": compare_features(events, controls) if not events.empty and not controls.empty else [],
        "signal_rates": signal_rates(signals) if not signals.empty else [],
        "signals_by_event": signals.replace({np.nan: None}).to_dict(orient="index") if not signals.empty else {},
        "countdown": countdown_profile(records),
    }
