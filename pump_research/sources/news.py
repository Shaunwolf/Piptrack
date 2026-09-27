"""News coverage during the window"""

from datetime import date, timedelta

from .base import DataSource, http_get_json
from ..models import SourceResult, NEEDS_KEY, SKIPPED


class PolygonNews(DataSource):
    """Polygon.io ticker news (multi-year history). Needs POLYGON_API_KEY."""
    name = "polygon_news"

    def _fetch(self, ticker, start, end, **kwargs):
        if not self.settings.polygon_api_key:
            return SourceResult(self.name, NEEDS_KEY, detail="Set POLYGON_API_KEY")
        data = http_get_json("https://api.polygon.io/v2/reference/news", params={
            "ticker": ticker, "published_utc.gte": start.isoformat(),
            "published_utc.lte": (end + timedelta(days=1)).isoformat(),
            "order": "asc", "limit": 1000, "apiKey": self.settings.polygon_api_key,
        }, timeout=self.settings.request_timeout)
        return [
            {"date": a["published_utc"][:10], "title": a.get("title", ""),
             "publisher": a.get("publisher", {}).get("name", ""), "url": a.get("article_url", ""),
             "description": a.get("description", ""), "tickers": a.get("tickers", [])}
            for a in data.get("results", [])
        ]


class GdeltNews(DataSource):
    """GDELT DOC 2.0 article search. Free, but only covers roughly the last three months."""
    name = "gdelt_news"
    coverage_days = 90

    def _fetch(self, ticker, start, end, company_name=None, **kwargs):
        if (date.today() - end).days > self.coverage_days:
            return SourceResult(self.name, SKIPPED,
                                detail="Window is older than GDELT DOC's ~3 month search range")
        query = f'"{company_name}"' if company_name else f'"{ticker}" stock'
        data = http_get_json("https://api.gdeltproject.org/api/v2/doc/doc", params={
            "query": query, "mode": "ArtList", "format": "json", "maxrecords": 250,
            "startdatetime": start.strftime("%Y%m%d000000"),
            "enddatetime": end.strftime("%Y%m%d235959"),
        }, timeout=self.settings.request_timeout)
        return [
            {"date": f"{a['seendate'][:4]}-{a['seendate'][4:6]}-{a['seendate'][6:8]}",
             "title": a.get("title", ""), "publisher": a.get("domain", ""), "url": a.get("url", "")}
            for a in data.get("articles", [])
        ]
