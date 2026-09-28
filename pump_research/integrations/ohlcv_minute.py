"""
#1 mito0o852/OHLCV-1m — offline price history from 1-minute bars.

The dataset stores one Parquet file per month (data/ohlcv_YYYY-MM.parquet, ~30 MB)
holding every ticker's 1-minute bars with a ticker column. We download only the
months covering the request (cached), keep the ticker's regular-session bars
(09:30–16:00 New York) and aggregate them into daily OHLCV. When switched on it
acts as a fallback price source for tickers Yahoo no longer serves.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..sources.base import DataSource
from ..models import OK, SKIPPED, SourceResult
from .base import Integration, IntegrationUnavailable, hf_download

REPO = "mito0o852/OHLCV-1m"


def months_between(start: date, end: date) -> List[str]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def minute_to_daily(minutes: pd.DataFrame) -> pd.DataFrame:
    """Regular-session 1-minute bars → daily OHLCV indexed by date"""
    if minutes.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    ts = pd.to_datetime(minutes["timestamp"], utc=True).dt.tz_convert("America/New_York")
    m = minutes.assign(ts=ts).set_index("ts").sort_index()
    m = m.between_time("09:30", "15:59")
    daily = m.groupby(m.index.date).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                        close=("close", "last"), volume=("volume", "sum"))
    return daily.dropna()


def _month_minutes(ticker: str, month: str) -> pd.DataFrame:
    import pyarrow.parquet as pq
    path = hf_download(REPO, f"data/ohlcv_{month}.parquet", repo_type="dataset")
    table = pq.read_table(path, columns=["timestamp", "open", "high", "low", "close", "volume", "ticker"],
                          filters=[("ticker", "=", ticker.upper())])
    return table.to_pandas()


def daily_prices(ticker: str, start: date, end: date, probe: Optional[date] = None) -> pd.DataFrame:
    """Daily bars for ticker between start and end. With `probe`, the month holding that date is read
    first and an empty result stops early, so a ticker the dataset lacks costs one download, not one per month."""
    try:
        import pyarrow.parquet  # noqa: F401
    except ImportError:
        raise IntegrationUnavailable("needs pyarrow (pip install pyarrow)")
    months = months_between(start, end)
    frames = {}
    if probe is not None:
        first = f"{probe.year:04d}-{probe.month:02d}"
        if first in months:
            frames[first] = _month_minutes(ticker, first)
            if frames[first].empty:
                return minute_to_daily(pd.DataFrame())
    for month in months:
        if month not in frames:
            frames[month] = _month_minutes(ticker, month)
    parts = [f for f in frames.values() if not f.empty]
    daily = minute_to_daily(pd.concat(parts, ignore_index=True) if parts else pd.DataFrame())
    return daily[(daily.index >= start) & (daily.index <= end)]


SPLIT_FACTORS = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 50, 60, 75, 80, 100, 150, 200, 250)
SPLIT_TOLERANCE = 0.04


def adjust_splits(daily: pd.DataFrame, protect_from: Optional[date] = None) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    The minute bars are not split-adjusted. An overnight gap whose ratio sits within 4% of a common split
    factor (and whose close holds that level) is treated as a split, and earlier bars are rescaled to the
    new share basis: prices by the factor, volume by its inverse. Days from `protect_from` on (the pump and
    its lead-in) are never read as splits, so a genuine 10x gap there is left alone.
    """
    df = daily.copy()
    if len(df) < 2:
        return df, []
    adjustments = []
    for t in range(len(df) - 1, 0, -1):
        day = df.index[t]
        if protect_from is not None and day >= protect_from:
            continue
        prev_close, opened, closed = df["close"].iloc[t - 1], df["open"].iloc[t], df["close"].iloc[t]
        if prev_close <= 0 or opened <= 0:
            continue
        ratio = opened / prev_close
        for k in SPLIT_FACTORS:
            for factor, kind in ((k, "reverse"), (1 / k, "forward")):
                if abs(ratio / factor - 1) <= SPLIT_TOLERANCE and 0.65 <= closed / (prev_close * factor) <= 1.35:
                    before = df.index[:t]
                    df.loc[before, ["open", "high", "low", "close"]] *= factor
                    df.loc[before, "volume"] /= factor
                    adjustments.append({"date": day.isoformat() if hasattr(day, "isoformat") else str(day),
                                        "kind": kind, "ratio": f"1:{k}" if kind == "reverse" else f"{k}:1"})
                    break
            else:
                continue
            break
    return df, adjustments[::-1]


class HfMinutePrices(DataSource):
    """Price source backed by the OHLCV-1m dataset"""
    name = "hf_ohlcv_1m"

    def _fetch(self, ticker, start, end, **kwargs):
        try:
            # The collector asks for ~400 days before the pump and 30 after: probe the month before the end
            lead_in = max(start, end - timedelta(days=45))
            df = daily_prices(ticker, start, end, probe=lead_in)
        except IntegrationUnavailable as e:
            return SourceResult(self.name, SKIPPED, detail=str(e))
        df, splits = adjust_splits(df, protect_from=lead_in)
        records = [{"date": d.isoformat(), **{k: float(v) for k, v in row.items()}} for d, row in df.iterrows()]
        if not records:
            return records
        detail = "split-adjusted: " + ", ".join(f"{a['date']} {a['ratio']} {a['kind']}" for a in splits) if splits else ""
        return SourceResult(self.name, OK, records=records, detail=detail)


INTEGRATION = Integration(
    key="ohlcv_1m_prices", title="OHLCV-1m minute history (mito0o852)", hf_id=REPO, hf_kind="dataset",
    category="price_source",
    description="Fallback price source: monthly Parquet files of 1-minute bars (1992–2026) aggregated to daily bars.",
    requires=["huggingface_hub", "pyarrow"], pip=["huggingface_hub", "pyarrow"])
INTEGRATION.run = lambda prices=None, ticker="", start=None, end=None, **kw: {
    "rows": len(daily_prices(ticker, start, end))} if ticker and start and end else {"error": "needs ticker, start and end"}
