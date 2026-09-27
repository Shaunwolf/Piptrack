"""
Locate the actual pump in a price history and classify it.

Seed dates are approximate, so we search a few trading days either side for the
biggest spike, then decide whether it was a single-day pump, a multi-day run,
or an IPO debut, and whether it clears the configured multiple.
"""

from datetime import date
from typing import List, Optional

import pandas as pd

from .models import PumpEvent


def _nearest_index(dates, target):
    """Position of the first trading day on or after target (or the last day)"""
    for i, d in enumerate(dates):
        if d >= target:
            return i
    return len(dates) - 1


def _best_run(closes, prev_closes, lo, hi, max_run_days):
    """Best (start, days, multiple) for runs starting in [lo, hi]: max close within the run / close before it"""
    best = (None, 0, 0.0)
    for s in range(lo, hi + 1):
        base = prev_closes[s]
        if not base or pd.isna(base):
            continue
        end = min(s + max_run_days, len(closes))
        window = closes[s:end]
        peak = max(window)
        mult = peak / base
        if mult > best[2]:
            best = (s, window.index(peak) + 1, mult)
    return best


def locate_pump(prices: pd.DataFrame, approx_date: date, settings, ipo_price: Optional[float] = None) -> Optional[PumpEvent]:
    """Find the pump nearest approx_date. Returns None when there is no price data near that date."""
    if prices.empty:
        return None
    dates = list(prices.index)
    center = _nearest_index(dates, approx_date)
    if abs((dates[center] - approx_date).days) > settings.search_radius_days * 2:
        return None  # data doesn't cover the seed date
    lo = max(0, center - settings.search_radius_days)
    hi = min(len(dates) - 1, center + settings.search_radius_days)

    closes = prices["close"].tolist()
    prev_closes = [None] + closes[:-1]
    # An IPO debut's reference price is the offering price
    is_ipo = lo == 0 and ipo_price is not None
    if is_ipo:
        prev_closes[0] = ipo_price

    # Biggest single-day spike (prev close -> intraday high)
    spike, spike_mult = None, 0.0
    for i in range(lo, hi + 1):
        base = prev_closes[i]
        if base:
            mult = prices["high"].iloc[i] / base
            if mult > spike_mult:
                spike, spike_mult = i, mult
    if spike is None:
        return None

    run_start, run_days, run_mult = _best_run(closes, prev_closes, lo, hi, settings.max_run_days)
    row = prices.iloc[spike]
    base = prev_closes[spike]
    close_mult = row["close"] / base

    meets_strict = close_mult >= settings.min_multiple
    meets_broad = spike_mult >= settings.min_multiple or run_mult >= settings.min_multiple

    if is_ipo and spike == 0:
        event_type, pump_idx = "ipo_debut", 0
    elif spike_mult >= settings.min_multiple or run_days <= 1 or run_mult <= close_mult:
        event_type, pump_idx = "single_day", spike
    else:
        # The window of interest is before the run began, not before its biggest day
        event_type, pump_idx = "multi_day_run", min(run_start, spike)

    window = pre_window_dates(dates, pump_idx, settings.pre_window_days)
    pump_row = prices.iloc[pump_idx]
    return PumpEvent(
        ticker="", pump_date=dates[pump_idx], event_type=event_type,
        prev_close=prev_closes[pump_idx], day_open=float(pump_row["open"]),
        day_high=float(pump_row["high"]), day_close=float(pump_row["close"]),
        day_volume=float(pump_row["volume"]),
        close_multiple=round(close_mult, 3), high_multiple=round(spike_mult, 3),
        run_multiple=round(run_mult, 3), run_days=run_days,
        meets_strict=bool(meets_strict), meets_broad=bool(meets_broad),
        window_start=window[0] if window else None, window_end=window[-1] if window else None,
    )


def pre_window_dates(dates, pump_idx, n_days):
    """Trading dates of the n days immediately before the pump (may be shorter near the start of data)"""
    return list(dates[max(0, pump_idx - n_days):pump_idx])


def qualifies(event: PumpEvent, settings) -> bool:
    return event.meets_strict if settings.criterion == "strict" else event.meets_broad


def discover(prices: pd.DataFrame, settings) -> List[date]:
    """Every date in a price history that clears the threshold (for scanning a ticker universe)"""
    hits = []
    closes = prices["close"].tolist()
    for i in range(1, len(prices)):
        base = closes[i - 1]
        if not base:
            continue
        if settings.criterion == "strict":
            mult = closes[i] / base
        else:
            # Flag the day the threshold is reached: vs yesterday's close, or vs the lowest close of the run
            run_base = min(c for c in closes[max(0, i - settings.max_run_days):i] if c)
            mult = max(prices["high"].iloc[i] / base, closes[i] / run_base)
        if mult >= settings.min_multiple and (not hits or (prices.index[i] - hits[-1]).days > 14):
            hits.append(prices.index[i])
    return hits
