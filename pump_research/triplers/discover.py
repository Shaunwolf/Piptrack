"""
Find triplers: a close that at least triples within `horizon` trading days (three weeks = 15).

The launch point is the lowest qualifying close of the episode, so the pre-launch window ends on the
last quiet close before the move. Ordinary (control) windows are drawn from the same price bands, so
"cheap stocks move more" doesn't pass for a signal.
"""

import logging
import random
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

MULTIPLE = 3.0
HORIZON = 15            # trading days: three weeks
PRE_WINDOW = 10         # trading days in the pre-launch window
MIN_HISTORY = 60        # bars needed before the launch (indicator warm-up)
MIN_PRICE = 0.10
MIN_DOLLAR_VOLUME = 50_000
MAX_DAY_JUMP = 50.0     # a single-day ×50 is almost always a data error (unadjusted split)
PRICE_BANDS = [0, 1, 3, 10, float("inf")]


def _date(d):
    return d.isoformat()[:10] if hasattr(d, "isoformat") else str(d)[:10]


def price_band(price: float) -> int:
    for i in range(len(PRICE_BANDS) - 1):
        if PRICE_BANDS[i] <= price < PRICE_BANDS[i + 1]:
            return i
    return len(PRICE_BANDS) - 2


def forward_max(closes: np.ndarray, horizon: int) -> np.ndarray:
    """Highest close in the next `horizon` bars (NaN where there aren't any)"""
    n = len(closes)
    out = np.full(n, np.nan)
    s = pd.Series(closes[::-1]).rolling(horizon, min_periods=1).max().to_numpy()[::-1]
    out[:-1] = s[1:]
    return out


def find_triples(df: pd.DataFrame, ticker: str = "", multiple: float = MULTIPLE, horizon: int = HORIZON,
                 pre_window: int = PRE_WINDOW, min_price: float = MIN_PRICE,
                 min_dollar_volume: float = MIN_DOLLAR_VOLUME, min_history: int = MIN_HISTORY) -> List[Dict]:
    if df is None or len(df) < min_history + 2:
        return []
    c = df["close"].to_numpy(float)
    h = df["high"].to_numpy(float)
    v = df["volume"].to_numpy(float)
    n = len(c)
    with np.errstate(divide="ignore", invalid="ignore"):
        jumps = c[1:] / c[:-1]
    fmax = forward_max(c, horizon)
    qualifies = fmax >= multiple * c
    events, i = [], min_history
    while i < n - 1:
        if not qualifies[i]:
            i += 1
            continue
        cand = [t for t in range(i, min(n - 1, i + horizon)) if qualifies[t]]
        launch = min(cand, key=lambda t: (c[t], t))
        stop = min(n, launch + horizon + 1)
        after = c[launch + 1:stop]
        triple = launch + 1 + int(np.argmax(after >= multiple * c[launch]))
        peak = launch + 1 + int(np.argmax(after))
        nxt = peak + horizon
        dollar_vol = float(np.nanmean(c[launch - pre_window + 1:launch + 1] * v[launch - pre_window + 1:launch + 1]))
        bad = (np.nanmax(jumps[max(0, launch - pre_window):stop - 1]) > MAX_DAY_JUMP) or v[triple] <= 0
        if c[launch] >= min_price and dollar_vol >= min_dollar_volume and not bad:
            dates = df.index
            events.append({
                "id": f"{ticker}_{_date(dates[launch])}", "ticker": ticker,
                "launch_date": _date(dates[launch]), "launch_idx": launch, "base_close": round(float(c[launch]), 4),
                "triple_date": _date(dates[triple]), "days_to_triple": triple - launch,
                "peak_date": _date(dates[peak]), "peak_close": round(float(c[peak]), 4),
                "peak_multiple": round(float(c[peak] / c[launch]), 2),
                "peak_high_multiple": round(float(np.nanmax(h[launch + 1:stop]) / c[launch]), 2),
                "window_dollar_volume": round(dollar_vol), "price_band": price_band(float(c[launch])),
                "window_dates": [_date(d) for d in dates[launch - pre_window + 1:launch + 1]],
            })
        i = max(nxt, i + 1)
    return events


def control_windows(prices: Dict[str, pd.DataFrame], events: List[Dict], per_event: int = 3, seed: int = 7,
                    horizon: int = HORIZON, pre_window: int = PRE_WINDOW, min_history: int = MIN_HISTORY,
                    multiple: float = MULTIPLE, max_tries: int = 200) -> List[Dict]:
    """Ordinary windows from the same price bands that did NOT triple within the horizon, away from any event"""
    rng = random.Random(seed)
    blocked = {}
    for e in events:
        blocked.setdefault(e["ticker"], []).append(e["launch_idx"])
    tickers = [t for t, df in prices.items() if df is not None and len(df) > min_history + horizon + 2]
    by_band: Dict[int, List] = {b: [] for b in range(len(PRICE_BANDS) - 1)}
    out = []
    want = {b: 0 for b in by_band}
    for e in events:
        want[e["price_band"]] += per_event
    for band, need in want.items():
        tries = 0
        while need > 0 and tries < need * max_tries and tickers:
            tries += 1
            t = rng.choice(tickers)
            df = prices[t]
            idx = rng.randrange(min_history, len(df) - horizon - 1)
            c = df["close"].to_numpy(float)
            if price_band(c[idx]) != band or any(abs(idx - b) < 2 * horizon for b in blocked.get(t, [])):
                continue
            w = slice(idx - pre_window + 1, idx + 1)
            dollar_vol = float(np.nanmean(c[w] * df["volume"].to_numpy(float)[w]))
            fwd = float(np.nanmax(c[idx + 1:idx + horizon + 1]) / c[idx])
            if c[idx] < MIN_PRICE or dollar_vol < MIN_DOLLAR_VOLUME or fwd >= multiple:
                continue
            out.append({"id": f"{t}_{_date(df.index[idx])}_ctl", "ticker": t, "launch_date": _date(df.index[idx]),
                        "launch_idx": idx, "base_close": round(float(c[idx]), 4), "price_band": band,
                        "forward_multiple": round(fwd, 3), "window_dollar_volume": round(dollar_vol),
                        "window_dates": [_date(d) for d in df.index[w]], "control": True})
            blocked.setdefault(t, []).append(idx)
            need -= 1
    return out


def discover(tickers: List[str], loader: Optional[Callable] = None, multiple: float = MULTIPLE,
             horizon: int = HORIZON) -> Dict:
    """Daily prices (two years, the reach of Yahoo's hourly history) for every ticker, and every tripler in them"""
    if loader is None:
        from ..scanlab.runner import load_prices as loader
    prices = loader(list(tickers), "1d")
    events = []
    for t in tickers:
        try:
            events.extend(find_triples(prices.get(t), t, multiple, horizon))
        except Exception as e:
            logging.warning("tripler search failed for %s: %s", t, e)
    events.sort(key=lambda e: e["launch_date"])
    return {"events": events, "prices": prices, "scanned": len(prices), "requested": len(tickers)}
