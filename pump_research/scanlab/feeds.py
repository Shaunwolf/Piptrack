"""
Live data feeds for Scan Lab blocks that need more than prices. The runner asks for the feeds a scan
uses, fetches them once per batch (in parallel, cached on disk) and hands each ticker its slice.

    short_interest  Yahoo: short % of float, days to cover, float, exchange, market cap
    options         Yahoo option chains → gamma exposure, gamma flip, call wall, call activity
    squeeze         FINRA daily short-volume ratio and Reg SHO threshold-list streak (10-day window)
    social          ApeWisdom mention counts now vs 24 hours ago
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Callable, Dict, Iterable, List, Optional

from ..squeeze import options as opt
from ..squeeze import sources
from ..squeeze.features import SqueezeData, _bdays_before, squeeze_features

WORKERS = 8


def _parallel(fn: Callable, tickers: List[str]) -> Dict[str, Optional[Dict]]:
    def safe(t):
        try:
            return t, fn(t)
        except Exception as e:
            logging.info("feed failed for %s: %s", t, e)
            return t, None
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return dict(pool.map(safe, tickers))


def feed_short_interest(tickers, asof):
    return _parallel(sources.float_and_short, tickers)


def feed_options(tickers, asof):
    return _parallel(opt.options_snapshot, tickers)


def feed_squeeze(tickers, asof):
    window = _bdays_before(asof, 9) + [asof]
    data = SqueezeData()
    sources.short_volume_ratios(tickers, _bdays_before(window[0], 10) + window)   # warm the day files once for all tickers
    return {t: squeeze_features(t, window, data) for t in tickers}


def feed_social(tickers, asof):
    trending = sources.mention_velocity(pages=5)
    return {t: trending.get(t, {"mentions": 0.0, "mentions_24h_ago": 0.0, "rank": None, "rank_24h_ago": None}) for t in tickers}


FEEDS: Dict[str, Callable] = {"short_interest": feed_short_interest, "options": feed_options, "squeeze": feed_squeeze,
                              "social": feed_social}


def fetch_feeds(needs: Iterable[str], tickers: List[str], asof: date) -> Dict[str, Dict[str, Optional[Dict]]]:
    """{ticker: {feed: data}} for every needed feed (a feed that fails leaves None for its tickers)"""
    per_ticker: Dict[str, Dict] = {t: {} for t in tickers}
    for name in needs:
        fn = FEEDS.get(name)
        if not fn:
            continue
        try:
            got = fn(tickers, asof) or {}
        except Exception as e:
            logging.warning("feed %s unavailable: %s", name, e)
            got = {}
        for t in tickers:
            per_ticker[t][name] = got.get(t)
    return per_ticker


def trending_tickers(limit: int = 60) -> List[str]:
    """Most-mentioned tickers on Reddit/StockTwits right now, fastest-rising first"""
    data = sources.mention_velocity(pages=3)
    rows = sorted(data.items(), key=lambda kv: -((kv[1]["mentions"] or 0) / max(kv[1]["mentions_24h_ago"] or 0, 3)))
    return [t for t, _ in rows[:limit]]


def threshold_tickers(asof: Optional[date] = None) -> List[str]:
    """Today's (or the latest published) Reg SHO threshold list"""
    d = asof or date.today()
    for back in range(0, 7):
        cur = date.fromordinal(d.toordinal() - back)
        if cur.weekday() < 5:
            lst = sources.threshold_list(cur)
            if lst:
                return sorted(lst)
    return []
