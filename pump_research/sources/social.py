"""Reddit posts and comments mentioning the ticker, via the Pullpush archive"""

import re

import requests
from datetime import datetime, time, timezone

from .base import DataSource, Partial, http_get_json

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
    max_pages = 30  # 100 items per page per endpoint; beyond this the result is marked partial

    def __init__(self, settings):
        super().__init__(settings)
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self.analyzer = SentimentIntensityAnalyzer()

    def _search(self, kind, query, after, before):
        """Returns (items, capped)"""
        items = []
        for _ in range(self.max_pages):
            data = http_get_json(f"{self.base_url}/{kind}/", params={
                "q": query, "after": after, "before": before, "size": 100, "sort": "desc",
            }, timeout=self.settings.request_timeout)
            batch = data.get("data", [])
            items.extend(batch)
            if len(batch) < 100:
                return items, False
            before = min(int(i["created_utc"]) for i in batch)
        return items, True

    def _fetch(self, ticker, start, end, **kwargs):
        pattern = mention_pattern(ticker)
        query = f"${ticker}" if ticker.upper() in AMBIGUOUS_TICKERS else ticker
        after, before = _epoch(start), _epoch(end, end_of_day=True)
        records, capped_kinds, failed = [], [], []
        for kind in ("submission", "comment"):
            try:
                items, capped = self._search(kind, query, after, before)
            except requests.HTTPError as e:
                # One endpoint failing (e.g. comment search) shouldn't discard the other's results
                failed.append(f"{kind} search failed ({str(e)[:80]})")
                continue
            if capped:
                capped_kinds.append(kind)
            for item in items:
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
        records.sort(key=lambda r: r["date"])
        if len(failed) == 2:
            raise requests.HTTPError("; ".join(failed))
        notes = failed + ([f"stopped after {self.max_pages * 100} {'/'.join(capped_kinds)}s"] if capped_kinds else [])
        if notes:
            return Partial(records, "; ".join(notes) + ": counts are lower bounds")
        return records


class ArcticShiftReddit(PullpushReddit):
    """
    Reddit posts and comments via the Arctic Shift archive. Its search needs a
    subreddit, so this queries the main trading subreddits one by one.
    """
    name = "reddit_arctic_shift"
    base_url = "https://arctic-shift.photon-reddit.com/api"
    subreddits = ("wallstreetbets", "pennystocks", "stocks", "Shortsqueeze", "smallstreetbets", "Superstonk",
                  "StockMarket", "investing", "Daytrading", "RobinHoodPennyStocks")
    max_pages = 5

    def _search(self, kind, query, after, before):
        endpoint = "posts" if kind == "submission" else "comments"
        text_param = "query" if kind == "submission" else "body"
        items, capped = [], False
        for sub in self.subreddits:
            cursor_before = before
            for page in range(self.max_pages):
                data = http_get_json(f"{self.base_url}/{endpoint}/search", params={
                    "subreddit": sub, text_param: query, "after": after, "before": cursor_before,
                    "limit": 100, "sort": "desc",
                }, timeout=self.settings.request_timeout)
                batch = data.get("data") or []
                items.extend(batch)
                if len(batch) < 100:
                    break
                cursor_before = min(int(i["created_utc"]) for i in batch)
                capped = capped or page == self.max_pages - 1
        return items, capped
