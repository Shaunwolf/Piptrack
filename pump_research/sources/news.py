"""News coverage during the window"""

from datetime import date, timedelta

from .base import DataSource, Partial, http_get_json
from ..models import SourceResult, NEEDS_KEY, SKIPPED


class PolygonNews(DataSource):
    """Polygon.io ticker news (multi-year history). Needs POLYGON_API_KEY."""
    name = "polygon_news"
    max_pages = 20  # 1,000 articles per page

    def _fetch(self, ticker, start, end, **kwargs):
        if not self.settings.polygon_api_key:
            return SourceResult(self.name, NEEDS_KEY, detail="Set POLYGON_API_KEY")
        key = self.settings.polygon_api_key
        url = "https://api.polygon.io/v2/reference/news"
        params = {"ticker": ticker, "published_utc.gte": start.isoformat(),
                  # Exclusive upper bound at the day after the window; records are re-checked below
                  "published_utc.lt": (end + timedelta(days=1)).isoformat(),
                  "order": "asc", "limit": 1000, "apiKey": key}
        articles, capped = [], False
        for page in range(self.max_pages):
            data = http_get_json(url, params=params, timeout=self.settings.request_timeout)
            articles.extend(data.get("results", []))
            next_url = data.get("next_url")
            if not next_url:
                break
            url, params = next_url, {"apiKey": key}
            capped = page == self.max_pages - 1
        records = [
            {"date": a["published_utc"][:10], "title": a.get("title", ""),
             "publisher": a.get("publisher", {}).get("name", ""), "url": a.get("article_url", ""),
             "description": a.get("description", ""), "tickers": a.get("tickers", [])}
            for a in articles if start.isoformat() <= a.get("published_utc", "")[:10] <= end.isoformat()
        ]
        return Partial(records, f"stopped after {self.max_pages} pages") if capped else records


class GdeltNews(DataSource):
    """GDELT DOC 2.0 article search. Free, but only covers roughly the last three months."""
    name = "gdelt_news"
    coverage_days = 90
    max_records = 250

    def _fetch(self, ticker, start, end, company_name=None, **kwargs):
        if (date.today() - end).days > self.coverage_days:
            return SourceResult(self.name, SKIPPED,
                                detail="Window is older than GDELT DOC's ~3 month search range")
        query = f'"{company_name}"' if company_name else f'"{ticker}" stock'
        data = http_get_json("https://api.gdeltproject.org/api/v2/doc/doc", params={
            "query": query, "mode": "ArtList", "format": "json", "maxrecords": self.max_records,
            "startdatetime": start.strftime("%Y%m%d000000"),
            "enddatetime": end.strftime("%Y%m%d235959"),
        }, timeout=self.settings.request_timeout)
        articles = data.get("articles", [])
        records = [
            {"date": f"{a['seendate'][:4]}-{a['seendate'][4:6]}-{a['seendate'][6:8]}",
             "title": a.get("title", ""), "publisher": a.get("domain", ""), "url": a.get("url", "")}
            for a in articles
        ]
        # GDELT returns at most maxrecords articles and has no pagination
        return Partial(records, f"GDELT cap of {self.max_records} articles reached") if len(articles) >= self.max_records else records
