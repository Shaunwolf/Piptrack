"""Daily OHLCV price history"""

from datetime import timedelta

import pandas as pd

from .base import DataSource, SourceBlocked, http_get_json
from ..models import SourceResult, NEEDS_KEY


def records_to_frame(records):
    """Price records -> DataFrame indexed by date with open/high/low/close/volume"""
    if not records:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.set_index("date").sort_index()[["open", "high", "low", "close", "volume"]]


class YahooPrices(DataSource):
    """Yahoo Finance via yfinance. Free, split-adjusted, but drops most delisted tickers."""
    name = "yahoo_prices"
    _reachable = None

    def _check_reachable(self):
        # yfinance reports "possibly delisted" when the connection itself was refused
        if YahooPrices._reachable is None:
            try:
                http_get_json("https://query1.finance.yahoo.com/v8/finance/chart/SPY",
                              headers={"User-Agent": "Mozilla/5.0"}, timeout=self.settings.request_timeout)
                YahooPrices._reachable = True
            except SourceBlocked:
                YahooPrices._reachable = False
            except Exception:
                YahooPrices._reachable = True  # host answered (e.g. rate limit), so it isn't blocked
        if not YahooPrices._reachable:
            raise SourceBlocked("Yahoo Finance unreachable (query1.finance.yahoo.com)")

    def _fetch(self, ticker, start, end, **kwargs):
        import yfinance as yf
        self._check_reachable()
        try:
            df = yf.Ticker(ticker).history(start=start, end=end + timedelta(days=1),
                                           interval="1d", auto_adjust=True, raise_errors=True)
        except Exception as e:
            text = str(e)
            if "403" in text or "CONNECT" in text or "Failed to perform" in text:
                raise SourceBlocked(f"Yahoo Finance unreachable: {text[:120]}")
            if "delisted" in text or "No data" in text or "no price data" in text.lower():
                return []
            raise
        return [
            {"date": idx.date().isoformat(), "open": float(r.Open), "high": float(r.High),
             "low": float(r.Low), "close": float(r.Close), "volume": float(r.Volume)}
            for idx, r in df.iterrows()
        ]


class PolygonPrices(DataSource):
    """Polygon.io aggregates. Needs POLYGON_API_KEY; includes delisted tickers."""
    name = "polygon_prices"

    def _fetch(self, ticker, start, end, **kwargs):
        if not self.settings.polygon_api_key:
            return SourceResult(self.name, NEEDS_KEY, detail="Set POLYGON_API_KEY")
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        data = http_get_json(url, params={"adjusted": "true", "sort": "asc", "limit": 50000,
                                          "apiKey": self.settings.polygon_api_key},
                             timeout=self.settings.request_timeout)
        return [
            {"date": pd.Timestamp(bar["t"], unit="ms").date().isoformat(), "open": bar["o"],
             "high": bar["h"], "low": bar["l"], "close": bar["c"], "volume": bar.get("v", 0)}
            for bar in data.get("results", [])
        ]
