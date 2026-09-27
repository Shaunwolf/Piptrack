"""
#1 mito0o852/OHLCV-1m — offline price history from 1-minute bars.

The dataset stores one Parquet file per month (data/ohlcv_YYYY-MM.parquet, ~30 MB)
holding every ticker's 1-minute bars with a ticker column. We download only the
months covering the request (cached), keep the ticker's regular-session bars
(09:30–16:00 New York) and aggregate them into daily OHLCV. When switched on it
acts as a fallback price source for tickers Yahoo no longer serves.
"""

from datetime import date
from typing import List

import pandas as pd

from ..sources.base import DataSource
from ..models import SourceResult, SKIPPED
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


def daily_prices(ticker: str, start: date, end: date) -> pd.DataFrame:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise IntegrationUnavailable("needs pyarrow (pip install pyarrow)")
    frames = []
    for month in months_between(start, end):
        path = hf_download(REPO, f"data/ohlcv_{month}.parquet", repo_type="dataset")
        table = pq.read_table(path, columns=["timestamp", "open", "high", "low", "close", "volume", "ticker"],
                              filters=[("ticker", "=", ticker.upper())])
        frames.append(table.to_pandas())
    daily = minute_to_daily(pd.concat(frames, ignore_index=True) if frames else pd.DataFrame())
    return daily[(daily.index >= start) & (daily.index <= end)]


class HfMinutePrices(DataSource):
    """Price source backed by the OHLCV-1m dataset"""
    name = "hf_ohlcv_1m"

    def _fetch(self, ticker, start, end, **kwargs):
        try:
            df = daily_prices(ticker, start, end)
        except IntegrationUnavailable as e:
            return SourceResult(self.name, SKIPPED, detail=str(e))
        return [{"date": d.isoformat(), **{k: float(v) for k, v in row.items()}} for d, row in df.iterrows()]


INTEGRATION = Integration(
    key="ohlcv_1m_prices", title="OHLCV-1m minute history (mito0o852)", hf_id=REPO, hf_kind="dataset",
    category="price_source",
    description="Fallback price source: monthly Parquet files of 1-minute bars (1992–2026) aggregated to daily bars.",
    requires=["huggingface_hub", "pyarrow"], pip=["huggingface_hub", "pyarrow"])
INTEGRATION.run = lambda prices=None, ticker="", start=None, end=None, **kw: {
    "rows": len(daily_prices(ticker, start, end))} if ticker and start and end else {"error": "needs ticker, start and end"}
