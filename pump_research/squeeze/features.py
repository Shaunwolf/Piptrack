"""
Squeeze features for one window, "as of" its last day, from historical data only (no look-ahead):
FINRA daily short-volume ratio, Reg SHO threshold-list streaks and FINRA short interest.
The same function serves the backtest (historical windows) and live scans (today's window).
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np

from . import sources


class SqueezeData:
    """Where the numbers come from; tests substitute a fake with the same three methods"""

    def short_volume_ratios(self, tickers, days):
        return sources.short_volume_ratios(tickers, days)

    def threshold_list(self, d):
        return sources.threshold_list(d)

    def short_interest_history(self, ticker):
        return sources.short_interest_history(ticker)


def _mean(values):
    vals = [v for v in values if v is not None]
    return float(np.mean(vals)) if vals else None


def _bdays_before(d: date, n: int) -> List[date]:
    out, cur = [], d
    while len(out) < n:
        cur -= timedelta(days=1)
        if cur.weekday() < 5:
            out.append(cur)
    return out[::-1]


def threshold_streak(data: SqueezeData, asof: date, ticker: str, lookback: int = 25) -> Optional[int]:
    """Consecutive published days on the threshold list ending at asof (None if no lists were available)"""
    n, seen_any, cur, checked = 0, False, asof, 0
    while checked < lookback * 2 and n < lookback:
        if cur.weekday() < 5:
            lst = data.threshold_list(cur)
            if lst is not None:
                seen_any = True
                if ticker.upper() in lst:
                    n += 1
                else:
                    break
        cur -= timedelta(days=1)
        checked += 1
    return n if seen_any else None


def squeeze_features(ticker: str, window_dates: List[date], data: Optional[SqueezeData] = None,
                     baseline_days: int = 10) -> Dict:
    """sq_* features for the window ending at window_dates[-1]"""
    data = data or SqueezeData()
    window_dates = [d if isinstance(d, date) else date.fromisoformat(str(d)[:10]) for d in window_dates]
    asof = window_dates[-1]
    t = ticker.upper()
    out: Dict = {}
    try:
        base = _bdays_before(window_dates[0], baseline_days)
        ratios = data.short_volume_ratios([t], base + window_dates)[t]
        base_r, win_r = ratios[:len(base)], ratios[len(base):]
        out["sq_short_vol_ratio"] = _mean(win_r)
        out["sq_short_vol_ratio_last3"] = _mean(win_r[-3:])
        b = _mean(base_r)
        out["sq_short_vol_ratio_change"] = out["sq_short_vol_ratio"] - b if out["sq_short_vol_ratio"] is not None and b is not None else None
    except Exception as e:
        logging.info("short volume unavailable for %s: %s", t, e)
    try:
        streak = threshold_streak(data, asof, t)
        if streak is not None:
            out["sq_threshold_streak"] = streak
            out["sq_on_threshold_list"] = streak > 0
            out["sq_threshold_day8_plus"] = streak >= 8
    except Exception as e:
        logging.info("threshold list unavailable for %s: %s", t, e)
    try:
        hist = data.short_interest_history(t)
        si = sources.short_interest_asof(hist, asof)
        if si:
            out["sq_days_to_cover"] = si["days_to_cover"]
            out["sq_short_interest_change_pct"] = si["change_pct"]
            out["sq_short_vs_avg_volume"] = si["short"] / si["avg_volume"] if si["avg_volume"] else None
            out["sq_days_to_cover_3plus"] = si["days_to_cover"] >= 3
    except Exception as e:
        logging.info("short interest unavailable for %s: %s", t, e)
    return {k: v for k, v in out.items() if v is not None}
