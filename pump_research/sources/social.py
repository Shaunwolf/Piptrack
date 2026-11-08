"""Reddit posts and comments mentioning the ticker, via the Pullpush archive"""

import re
import time as clock  # `time` is taken by datetime.time below

import requests
from datetime import datetime, time, timezone

from .base import DataSource, Partial, http_get_json

# Tickers that are also common words/abbreviations: only count "$TICKER" mentions
AMBIGUOUS_TICKERS = {
    "TOP", "BB", "IT", "ALL", "ARE", "CAN", "FOR", "ONE", "NOW", "SO", "ON", "GO", "BE", "OR", "AI", "DD",
    "WISH", "FUN", "LOVE", "REAL", "BIG", "RUN", "TRUE", "OPEN", "LIFE", "PLAY", "WELL", "CASH", "HAS", "SEE", "NEW",
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

    search_kinds = ("submission", "comment")

    def _fetch(self, ticker, start, end, **kwargs):
        pattern = mention_pattern(ticker)
        query = f"${ticker}" if ticker.upper() in AMBIGUOUS_TICKERS else ticker
        after, before = _epoch(start), _epoch(end, end_of_day=True)
        records, capped_kinds, failed = [], [], []
        self._notes = []
        for kind in self.search_kinds:
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
        if len(failed) == len(self.search_kinds):
            # Nothing answered: that's unknown, never "zero mentions"
            raise requests.HTTPError("; ".join(failed))
        notes = failed + self._notes + ([f"stopped after {self.max_pages * 100} {'/'.join(capped_kinds)}s"] if capped_kinds else [])
        if notes:
            return Partial(records, "; ".join(notes) + ": counts are lower bounds")
        return records


class ArcticShiftReddit(PullpushReddit):
    """
    Reddit posts via the Arctic Shift archive. Its search needs a subreddit, so this
    queries the main trading subreddits one by one, at most one request per second.
    Comment search is skipped (the archive errors on it), so results are marked partial.
    """
    name = "reddit_arctic_shift"
    base_url = "https://arctic-shift.photon-reddit.com/api"
    subreddits = ("wallstreetbets", "pennystocks", "stocks", "Shortsqueeze", "smallstreetbets", "Superstonk",
                  "StockMarket", "investing", "Daytrading", "RobinHoodPennyStocks")
    max_pages = 5
    request_interval = 1.0
    search_kinds = ("submission",)
    _last_request = 0.0

    def _throttle(self):
        wait = self.request_interval - (clock.monotonic() - ArcticShiftReddit._last_request)
        if wait > 0:
            clock.sleep(wait)
        ArcticShiftReddit._last_request = clock.monotonic()

    def _fetch(self, ticker, start, end, **kwargs):
        result = super()._fetch(ticker, start, end, **kwargs)
        if isinstance(result, Partial):
            return result
        return Partial(result, "post titles only (comments and full text aren't searchable here): counts are lower bounds")

    def _search(self, kind, query, after, before):
        items, capped, failed_subs = [], False, []
        for sub in self.subreddits:
            cursor_before = before
            try:
                for page in range(self.max_pages):
                    self._throttle()
                    # Title search: full-text search over big subreddits times out on the archive's side
                    data = http_get_json(f"{self.base_url}/posts/search", params={
                        "subreddit": sub, "title": query, "after": after, "before": cursor_before,
                        "limit": 100, "sort": "desc",
                    }, timeout=self.settings.request_timeout)
                    batch = data.get("data") or []
                    items.extend(batch)
                    if len(batch) < 100:
                        break
                    cursor_before = min(int(i["created_utc"]) for i in batch)
                    capped = capped or page == self.max_pages - 1
            except requests.HTTPError as e:
                failed_subs.append(f"r/{sub} ({str(e)[:40]})")
        if failed_subs and len(failed_subs) == len(self.subreddits):
            raise requests.HTTPError("every subreddit search failed: " + "; ".join(failed_subs[:3]))
        if failed_subs:
            self._notes.append(f"{len(failed_subs)} of {len(self.subreddits)} subreddits failed")
        return items, capped
