"""Reddit posts and comments mentioning the ticker, via the Pullpush archive"""

import re
from datetime import datetime, time, timezone

from .base import DataSource, http_get_json

# Tickers that are also common words/abbreviations: only count "$TICKER" mentions
AMBIGUOUS_TICKERS = {
    "TOP", "BB", "AMC", "NOK", "GME", "EXPR", "IT", "ALL", "ARE", "CAN", "FOR", "ONE", "NOW",
    "SO", "ON", "GO", "BE", "OR", "AI", "DD", "HOLO", "KOSS", "CLOV", "WISH", "FUN", "LOVE",
}


def _epoch(d, end_of_day=False):
    return int(datetime.combine(d, time.max if end_of_day else time.min, tzinfo=timezone.utc).timestamp())


def mention_pattern(ticker):
    if ticker.upper() in AMBIGUOUS_TICKERS:
        return re.compile(rf"\${re.escape(ticker)}\b", re.IGNORECASE)
    return re.compile(rf"(\${re.escape(ticker)}\b|\b{re.escape(ticker.upper())}\b)")


class PullpushReddit(DataSource):
    name = "reddit"
    base_url = "https://api.pullpush.io/reddit/search"
    max_pages = 10  # 100 items per page per endpoint

    def __init__(self, settings):
        super().__init__(settings)
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self.analyzer = SentimentIntensityAnalyzer()

    def _search(self, kind, query, after, before):
        items = []
        for _ in range(self.max_pages):
            data = http_get_json(f"{self.base_url}/{kind}/", params={
                "q": query, "after": after, "before": before, "size": 100, "sort": "desc",
            }, timeout=self.settings.request_timeout)
            batch = data.get("data", [])
            items.extend(batch)
            if len(batch) < 100:
                break
            before = min(int(i["created_utc"]) for i in batch)
        return items

    def _fetch(self, ticker, start, end, **kwargs):
        pattern = mention_pattern(ticker)
        query = f"${ticker}" if ticker.upper() in AMBIGUOUS_TICKERS else ticker
        after, before = _epoch(start), _epoch(end, end_of_day=True)
        records = []
        for kind in ("submission", "comment"):
            for item in self._search(kind, query, after, before):
                text = " ".join(filter(None, [item.get("title"), item.get("selftext"), item.get("body")]))
                if not pattern.search(text):
                    continue
                created = datetime.fromtimestamp(int(item["created_utc"]), tz=timezone.utc)
                records.append({
                    "date": created.date().isoformat(), "kind": kind,
                    "subreddit": item.get("subreddit", ""), "author": item.get("author", ""),
                    "score": item.get("score", 0), "num_comments": item.get("num_comments"),
                    "title": item.get("title", ""), "text": text[:1000],
                    "sentiment": self.analyzer.polarity_scores(text)["compound"],
                    "url": f"https://www.reddit.com{item['permalink']}" if item.get("permalink") else "",
                })
        return sorted(records, key=lambda r: r["date"])
