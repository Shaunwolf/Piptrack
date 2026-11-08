"""Load prices for a universe (batched, cached for the day) and run a scan spec over it"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import pandas as pd

from .engine import ScanContext, evaluate, needed_feeds, normalize_spec
from .universe import NAMES

TIMEFRAMES = {"1d": ("1d", "2y"), "1wk": ("1wk", "10y"), "4h": ("60m", "360d"), "1h": ("60m", "180d")}
BENCHMARK = "SPY"
MIN_BARS = 30


def cache_dir() -> str:
    base = os.environ.get("APP_WRITABLE_DIR") or ("/tmp" if os.environ.get("VERCEL") else ".cache")
    path = os.path.join(base, "scanlab_prices")
    os.makedirs(path, exist_ok=True)
    return path


def _stamp(timeframe):
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H") if timeframe in ("1h", "4h") else now.strftime("%Y-%m-%d")


def _frame(raw: pd.DataFrame) -> Optional[pd.DataFrame]:
    if raw is None or raw.empty:
        return None
    df = raw.rename(columns=lambda c: str(c).lower())
    need = ["open", "high", "low", "close", "volume"]
    if any(c not in df.columns for c in need):
        return None
    df = df[need].astype(float).dropna(subset=["close"])
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    return df if len(df) else None


def load_prices(tickers: List[str], timeframe: str = "1d", batch: int = 60) -> Dict[str, pd.DataFrame]:
    """Daily (or weekly/hourly) OHLCV from Yahoo Finance in batches, cached on disk until the next day (hour)"""
    interval, period = TIMEFRAMES.get(timeframe, TIMEFRAMES["1d"])
    stamp, folder, out, missing = _stamp(timeframe), cache_dir(), {}, []
    for t in tickers:
        path = os.path.join(folder, f"{timeframe}_{stamp}_{t}.pkl")
        if os.path.exists(path):
            try:
                out[t] = pd.read_pickle(path)
                continue
            except Exception:
                pass
        missing.append(t)
    if not missing:
        return out
    import yfinance as yf
    for i in range(0, len(missing), batch):
        chunk = missing[i:i + batch]
        try:
            raw = yf.download(chunk, period=period, interval=interval, group_by="ticker", auto_adjust=True,
                              threads=True, progress=False)
        except Exception as e:  # network or Yahoo errors: the tickers are reported as missing
            logging.warning("price download failed for %d tickers: %s", len(chunk), e)
            continue
        for t in chunk:
            try:
                part = raw[t] if isinstance(raw.columns, pd.MultiIndex) and t in raw.columns.get_level_values(0) else (
                    raw if len(chunk) == 1 else None)
            except KeyError:
                part = None
            df = _frame(part)
            if df is not None and timeframe == "4h":
                from ..triplers.collect import to_4h
                df = to_4h(df)
            if df is None:
                continue
            out[t] = df
            try:
                df.to_pickle(os.path.join(folder, f"{timeframe}_{stamp}_{t}.pkl"))
            except OSError:
                pass
    return out


def run_scan(spec: Dict, tickers: List[str], sector_of: Optional[Dict[str, str]] = None, timeframe: str = "1d",
             loader: Callable = load_prices, model: Optional[Dict] = None, settings=None, include_misses: bool = True,
             feeds: Optional[Callable] = None) -> Dict:
    """Evaluate the spec on every ticker; matches first, then the best near misses, by blend score"""
    spec = normalize_spec(spec)
    started = time.time()
    prices = loader(list(tickers) + [BENCHMARK], timeframe)
    bench = prices.get(BENCHMARK)
    needs = needed_feeds(spec)
    fed: Dict[str, Dict] = {}
    if needs:
        from .feeds import fetch_feeds
        have = [t for t in tickers if prices.get(t) is not None and len(prices[t]) >= MIN_BARS]
        last_days = [prices[t].index[-1] for t in have]
        asof = max(last_days) if last_days else datetime.now(timezone.utc).date()
        asof = asof.date() if hasattr(asof, "date") and callable(asof.date) else asof
        fed = (feeds or fetch_feeds)(needs, have, asof)
    rows, missing = [], []
    for t in tickers:
        df = prices.get(t)
        if df is None or len(df) < MIN_BARS:
            missing.append(t)
            continue
        try:
            ctx = ScanContext(df, ticker=t, benchmark=bench, model=model, settings=settings, meta={"feeds": fed.get(t, {})})
            ev = evaluate(spec, ctx, normalized=True)
        except Exception as e:
            logging.warning("scan failed for %s: %s", t, e)
            missing.append(t)
            continue
        closes = ctx.c.iloc[-60:]
        rows.append({"ticker": t, "name": NAMES.get(t, ""), "sector": (sector_of or {}).get(t, ""),
                     "price": round(ctx.close, 4), "change": round((ctx.close / float(ctx.c.iloc[-2]) - 1) * 100, 2) if len(ctx.c) > 1 else None,
                     "as_of": ctx.date(ctx.end), "spark": [round(float(x), 4) for x in closes], **ev})
    rows.sort(key=lambda r: (not r["matched"], -r["score"]))
    if not include_misses:
        rows = [r for r in rows if r["matched"]]
    return {"results": rows, "missing": missing, "scanned": len(tickers) - len(missing),
            "matched": sum(r["matched"] for r in rows), "timeframe": timeframe, "seconds": round(time.time() - started, 2)}
