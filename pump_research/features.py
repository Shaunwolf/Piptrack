"""Turn a pre-pump window of raw data into comparable numbers"""

from collections import Counter
from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .technicals import technical_snapshot


def rsi(closes: pd.Series, period: int = 14) -> Optional[float]:
    if len(closes) <= period:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if loss == 0:
        return 100.0
    return float(100 - 100 / (1 + gain / loss))


def _ratio(a, b):
    return float(a / b) if b and not pd.isna(b) and b != 0 else None


def price_features(prices: pd.DataFrame, window_end_idx: int, settings, technicals: Optional[Dict] = None) -> Optional[Dict]:
    """
    Features for the pre_window_days rows ending at window_end_idx (inclusive),
    compared with the baseline_days rows before them, plus every `ta_*` technical
    feature. Pass a precomputed technical_snapshot to avoid recomputing it.
    """
    n = settings.pre_window_days
    w_start = window_end_idx - n + 1
    if w_start < 1:
        return None
    window = prices.iloc[w_start:window_end_idx + 1]
    baseline = prices.iloc[max(0, w_start - settings.baseline_days):w_start]
    base_close = prices["close"].iloc[w_start - 1]
    returns = window["close"].pct_change().dropna()
    base_returns = baseline["close"].pct_change().dropna()
    base_vol_mean = baseline["volume"].mean() if len(baseline) else None
    log_vol = np.log1p(window["volume"].to_numpy(dtype=float))
    history = prices["close"].iloc[:window_end_idx + 1]
    prev_closes = prices["close"].shift(1).iloc[w_start:window_end_idx + 1]

    if technicals is None:
        technicals = technical_snapshot(prices, window_end_idx, n)
    return {
        **technicals["features"],
        "window_days": len(window),
        "baseline_days": len(baseline),
        "last_close": float(window["close"].iloc[-1]),
        "window_return": _ratio(window["close"].iloc[-1], base_close) - 1 if base_close else None,
        "window_max_drawdown": float((window["close"] / window["close"].cummax() - 1).min()),
        "window_volatility": float(returns.std()) if len(returns) > 1 else None,
        "volatility_ratio": _ratio(returns.std(), base_returns.std()) if len(base_returns) > 1 else None,
        "avg_volume_ratio": _ratio(window["volume"].mean(), base_vol_mean),
        "max_volume_ratio": _ratio(window["volume"].max(), base_vol_mean),
        "last3_volume_ratio": _ratio(window["volume"].tail(3).mean(), base_vol_mean),
        "volume_trend_slope": float(np.polyfit(np.arange(len(log_vol)), log_vol, 1)[0]) if len(log_vol) > 1 else None,
        "up_days_share": float((returns > 0).mean()) if len(returns) else None,
        "avg_range_pct": float(((window["high"] - window["low"]) / window["close"]).mean()),
        "gap_ups_5pct": int((window["open"] > prev_closes * 1.05).sum()),
        "rsi_14": rsi(history),
        "close_vs_period_low": _ratio(window["close"].iloc[-1], prices["close"].iloc[max(0, w_start - settings.baseline_days):window_end_idx + 1].min()),
        "avg_dollar_volume": float((window["close"] * window["volume"]).mean()),
    }


def daily_profile(prices: pd.DataFrame, pump_idx: int, settings) -> List[Dict]:
    """Day-by-day countdown to the pump: return and volume vs baseline for day -N..-1"""
    n = settings.pre_window_days
    w_start = max(1, pump_idx - n)
    baseline = prices.iloc[max(0, w_start - settings.baseline_days):w_start]
    base_vol = baseline["volume"].mean() if len(baseline) else None
    rows = []
    for i in range(w_start, pump_idx):
        rows.append({
            "offset": i - pump_idx,
            "date": prices.index[i].isoformat(),
            "close": float(prices["close"].iloc[i]),
            "return": float(prices["close"].iloc[i] / prices["close"].iloc[i - 1] - 1),
            "volume": float(prices["volume"].iloc[i]),
            "volume_ratio": _ratio(prices["volume"].iloc[i], base_vol),
        })
    return rows


def control_window_ends(prices: pd.DataFrame, pump_idx: int, settings) -> List[int]:
    """Evenly spaced end positions for ordinary windows well before the pump"""
    # A full baseline before the window, so ratios are measured the same way as for pump windows
    first = settings.baseline_days + settings.pre_window_days
    last = pump_idx - settings.control_gap_days
    if last <= first:
        return []
    k = settings.control_windows_per_event
    return sorted({int(x) for x in np.linspace(first, last, k)})


def context_features(context: Dict[str, List[Dict]], window_dates: List[date], answered=None, partial=()) -> Dict:
    """
    Summaries of filings, news and Reddit activity inside the window.
    `answered` is the set of sources that actually responded; features from the others are None
    (unknown) rather than zero. Defaults to every source present in `context`.
    `partial` lists sources that hit a result cap; their counts are lower bounds (flagged *_partial).
    """
    answered = set(context) if answered is None else set(answered)
    has_filings = "sec_filings" in answered
    has_news = bool({"polygon_news", "gdelt_news"} & answered)
    has_reddit = "reddit" in answered
    filings = context.get("sec_filings", [])
    news = context.get("polygon_news", []) + context.get("gdelt_news", [])
    reddit = context.get("reddit", [])
    groups = Counter(f["group"] for f in filings)

    per_day = Counter(r["date"] for r in reddit)
    days = [d.isoformat() for d in window_dates]
    counts = [per_day.get(d, 0) for d in days]
    late, early = counts[-3:], counts[:-3]
    early_rate = (sum(early) / len(early)) if early else 0
    late_rate = (sum(late) / len(late)) if late else 0

    sentiments = [r["sentiment"] for r in reddit if r.get("sentiment") is not None]
    feats = {
        "filings_total": len(filings),
        "filings_offering": groups.get("offering", 0),
        "filings_material_event": groups.get("material_event", 0),
        "filings_insider": groups.get("insider", 0),
        "filings_ownership": groups.get("ownership", 0),
        "news_articles": len(news),
        "reddit_mentions": len(reddit),
        "reddit_unique_authors": len({r["author"] for r in reddit if r.get("author")}),
        "reddit_mentions_per_day": counts,
        # Last 3 days' mention rate vs the earlier days, smoothed so zero-mention starts stay finite
        "reddit_mention_acceleration": (late_rate + 0.5) / (early_rate + 0.5) if reddit else None,
        "reddit_avg_sentiment": float(np.mean(sentiments)) if sentiments else None,
        "reddit_top_subreddits": Counter(r["subreddit"] for r in reddit).most_common(5),
    }
    feats["news_partial"] = bool({"polygon_news", "gdelt_news"} & set(partial))
    feats["reddit_partial"] = "reddit" in set(partial)
    for key in feats:
        if key.endswith("_partial"):
            continue
        if (key.startswith("filings_") and not has_filings) or (key.startswith("news_") and not has_news) \
                or (key.startswith("reddit_") and not has_reddit):
            feats[key] = None
    return feats
