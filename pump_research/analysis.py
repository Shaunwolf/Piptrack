"""
Cross-event analysis: what do pre-pump windows have in common, and how do they
differ from ordinary windows for the same stocks?
"""

from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, fisher_exact

# Price features compared between pre-pump and control windows
COMPARED_FEATURES = [
    "window_return", "window_volatility", "volatility_ratio", "avg_volume_ratio", "max_volume_ratio",
    "last3_volume_ratio", "volume_trend_slope", "up_days_share", "avg_range_pct", "gap_ups_5pct",
    "rsi_14", "close_vs_period_low", "last_close", "avg_dollar_volume",
]

# Simple yes/no warning signs checked for every event window: name -> (columns needed, test)
SIGNALS = {
    "volume_2x_baseline": (["avg_volume_ratio"], lambda r: r["avg_volume_ratio"] >= 2),
    "volume_spike_5x_day": (["max_volume_ratio"], lambda r: r["max_volume_ratio"] >= 5),
    "volume_rising": (["volume_trend_slope"], lambda r: r["volume_trend_slope"] > 0.05),
    "volatility_1_5x_baseline": (["volatility_ratio"], lambda r: r["volatility_ratio"] >= 1.5),
    "sub_5_dollar_price": (["last_close"], lambda r: r["last_close"] < 5),
    "sub_1_dollar_price": (["last_close"], lambda r: r["last_close"] < 1),
    "oversold_rsi_below_35": (["rsi_14"], lambda r: r["rsi_14"] < 35),
    "already_up_20pct": (["window_return"], lambda r: r["window_return"] >= 0.20),
    "reddit_chatter_accelerating": (["reddit_mention_acceleration"], lambda r: r["reddit_mention_acceleration"] >= 2),
    "offering_filing_in_window": (["filings_offering"], lambda r: r["filings_offering"] >= 1),
    "any_news_in_window": (["news_articles"], lambda r: r["news_articles"] >= 1),
    # Technical analysis
    "ema_bull_stack": (["ta_ema_bull_stack"], lambda r: r["ta_ema_bull_stack"]),
    "wma_bull_stack": (["ta_wma_bull_stack"], lambda r: r["ta_wma_bull_stack"]),
    "bollinger_squeeze": (["ta_bb_squeeze"], lambda r: r["ta_bb_squeeze"]),
    "macd_bull_cross": (["ta_macd_bull_cross_in_window"], lambda r: r["ta_macd_bull_cross_in_window"]),
    "rsi_bullish_divergence": (["ta_rsi_bullish_divergence"], lambda r: r["ta_rsi_bullish_divergence"]),
    "obv_accumulation_divergence": (["ta_obv_bullish_divergence"], lambda r: r["ta_obv_bullish_divergence"]),
    "money_flow_positive": (["ta_cmf20"], lambda r: r["ta_cmf20"] > 0.05),
    "fib_golden_pocket": (["ta_fib_golden_pocket"], lambda r: r["ta_fib_golden_pocket"]),
    "bullish_harmonic_completed": (["ta_harmonic_bullish_in_window"], lambda r: r["ta_harmonic_bullish_in_window"] >= 1),
    "bullish_chart_pattern": (["ta_chart_bullish_in_window"], lambda r: r["ta_chart_bullish_in_window"] >= 1),
    "bullish_candles_outnumber_bearish": (["ta_candles_bullish", "ta_candles_bearish"],
                                          lambda r: r["ta_candles_bullish"] > r["ta_candles_bearish"]),
    "break_of_structure": (["ta_break_of_structure"], lambda r: r["ta_break_of_structure"]),
    "trend_strong_adx_25": (["ta_adx"], lambda r: r["ta_adx"] >= 25),
    # Fibonacci & Gann suite (4+ tools agreeing happens on ~8% of random-walk bars)
    "fib_confluence_4plus": (["ta_fib_confluence"], lambda r: r["ta_fib_confluence"] >= 4),
    "fib_time_line_today": (["ta_fib_time_confluence"], lambda r: r["ta_fib_time_confluence"] >= 1),
    "near_trend_fib_extension": (["ta_fib_ext_near"], lambda r: r["ta_fib_ext_near"]),
    "above_gann_1x1": (["ta_gann_above_1x1"], lambda r: r["ta_gann_above_1x1"]),
    "above_pitchfan_median": (["ta_pitchfan_above_median"], lambda r: r["ta_pitchfan_above_median"]),
    # Kalman, support/resistance signals, fear & greed
    "kalman_uptrend": (["ta_kalman_uptrend"], lambda r: r["ta_kalman_uptrend"]),
    "kalman_turned_up": (["ta_kalman_turned_up_in_window"], lambda r: r["ta_kalman_turned_up_in_window"]),
    "sr_buy_signal": (["ta_sr_buy_signals"], lambda r: r["ta_sr_buy_signals"] >= 1),
    "sr_sell_signal": (["ta_sr_sell_signals"], lambda r: r["ta_sr_sell_signals"] >= 1),
    "extreme_fear": (["ta_fear_greed"], lambda r: r["ta_fear_greed"] < 25),
    "extreme_greed": (["ta_fear_greed"], lambda r: r["ta_fear_greed"] > 75),
    "near_all_time_low": (["ta_alltime_fib_position"], lambda r: r["ta_alltime_fib_position"] < 0.1),
}


def _missing(v):
    return v is None or (not isinstance(v, (bool, np.bool_)) and pd.isna(v))


def event_frame(records: List[Dict], qualifying_only=False) -> pd.DataFrame:
    rows = []
    for rec in records:
        known_context = any(v is not None for k, v in (rec.get("context_features") or {}).items()
                            if not k.endswith("_partial"))
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


def _is_bool_column(series: pd.Series) -> bool:
    values = series.dropna()
    return len(values) > 0 and all(isinstance(v, (bool, np.bool_)) for v in values)


def numeric_features(events: pd.DataFrame, controls: pd.DataFrame) -> List[str]:
    """Core price features plus every numeric technical (ta_*) feature present in both groups"""
    ta = sorted(c for c in events.columns if c.startswith("ta_") and c in controls
                and not _is_bool_column(events[c]) and not _is_bool_column(controls[c]))
    return [f for f in COMPARED_FEATURES if f in events and f in controls] + ta


def compare_boolean_features(events: pd.DataFrame, controls: pd.DataFrame) -> List[Dict]:
    """How often each yes/no technical signal fired before pumps vs in ordinary windows (Fisher exact test)"""
    out = []
    for col in sorted(c for c in events.columns if c in controls and _is_bool_column(events[c])):
        e, c = events[col].dropna().astype(bool), controls[col].dropna().astype(bool)
        if len(e) < 3 or len(c) < 3:
            continue
        table = [[int(e.sum()), int((~e).sum())], [int(c.sum()), int((~c).sum())]]
        _, p = fisher_exact(table)
        out.append({"feature": col, "event_rate": float(e.mean()), "control_rate": float(c.mean()),
                    "lift": float(e.mean() / c.mean()) if c.mean() > 0 else None,
                    "p_value": float(p), "events_n": len(e), "controls_n": len(c)})
    return sorted(out, key=lambda r: abs(r["event_rate"] - r["control_rate"]), reverse=True)


def compare_features(events: pd.DataFrame, controls: pd.DataFrame) -> List[Dict]:
    """Median pre-pump vs control value per feature, with a Mann-Whitney test, ranked by separation"""
    out = []
    for feat in numeric_features(events, controls):
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
    rows = {}
    for _, row in events.iterrows():
        rows[row["id"]] = {
            name: None if any(c not in row or _missing(row[c]) for c in cols) else bool(test(row))
            for name, (cols, test) in SIGNALS.items()
        }
    return pd.DataFrame.from_dict(rows, orient="index", columns=list(SIGNALS))


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
        "boolean_comparison": compare_boolean_features(events, controls) if not events.empty and not controls.empty else [],
        "signal_rates": signal_rates(signals) if not signals.empty else [],
        "signals_by_event": signals.replace({np.nan: None}).to_dict(orient="index") if not signals.empty else {},
        "countdown": countdown_profile(records),
    }
