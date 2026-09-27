"""
#10 Sentdex/wsb_reddit_v001 and #11 kowalsky/reddit_about_money — offline Reddit text.

Neither dataset has timestamps (inspected: WSB is comment/reply text in
[INST]...[/INST] pairs from ~2017-18; reddit_about_money is title/score/URL/comments
CSVs), so they can't be tied to a pre-pump window. They answer "how much was this
ticker talked about in the corpus, and what was said".
"""

import csv
import io
import json
from typing import Dict, List

from ..sources.social import mention_pattern
from .base import Integration, hf_download

WSB_REPO, MONEY_REPO = "Sentdex/wsb_reddit_v001", "kowalsky/reddit_about_money"
MONEY_FILES = ("reddit_stocks.csv", "reddit_WallStreet.csv", "reddit_daytrading.csv", "reddit_posts_trading.csv",
               "reddit_HedgeFund.csv", "reddit_posts.csv")
_CACHE: Dict[str, List] = {}


def _wsb_samples() -> List[str]:
    if "wsb" not in _CACHE:
        with open(hf_download(WSB_REPO, "wsb-v001.json", repo_type="dataset"), encoding="utf-8") as f:
            raw = f.read()
        try:
            data = json.loads(raw)
            items = data if isinstance(data, list) else data.get("data") or data.get("train") or list(data.values())
        except json.JSONDecodeError:
            items = [json.loads(line) for line in raw.splitlines() if line.strip()]
        _CACHE["wsb"] = [i.get("sample", "") if isinstance(i, dict) else str(i) for i in items]
    return _CACHE["wsb"]


def wsb_corpus_mentions(ticker: str, examples: int = 5) -> Dict:
    pattern = mention_pattern(ticker.upper())
    hits = [s for s in _wsb_samples() if pattern.search(s)]
    clean = [h.replace("[INST]", "").replace("[/INST]", " → ").strip()[:280] for h in hits[:examples]]
    return {"dataset": WSB_REPO, "period": "~2017-2018 (undated)", "corpus_size": len(_wsb_samples()),
            "mentions": len(hits), "examples": clean}


def _money_rows() -> List[Dict]:
    if "money" not in _CACHE:
        rows = []
        for name in MONEY_FILES:
            try:
                path = hf_download(MONEY_REPO, name, repo_type="dataset")
            except Exception:
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                for row in csv.DictReader(io.StringIO(f.read())):
                    rows.append({"source": name.removesuffix(".csv"), "title": row.get("Title") or "",
                                 "score": row.get("Score"), "url": row.get("URL") or "", "comments": row.get("Comments") or ""})
        _CACHE["money"] = rows
    return _CACHE["money"]


def reddit_money_mentions(ticker: str, examples: int = 8) -> Dict:
    pattern = mention_pattern(ticker.upper())
    rows = _money_rows()
    hits = [r for r in rows if pattern.search(r["title"]) or pattern.search(r["comments"])]

    def score(r):
        try:
            return int(r["score"])
        except (TypeError, ValueError):
            return 0
    hits.sort(key=score, reverse=True)
    return {"dataset": MONEY_REPO, "period": "undated", "posts_scanned": len(rows), "mentions": len(hits),
            "examples": [{"subreddit_file": h["source"], "title": h["title"][:200], "score": h["score"],
                          "url": h["url"] if h["url"].startswith("https://www.reddit.com/") else ""} for h in hits[:examples]]}


WSB_INTEGRATION = Integration(
    key="wsb_corpus", title="WallStreetBets 2017–18 corpus (Sentdex)", hf_id=WSB_REPO, hf_kind="dataset",
    category="social_source", description="Counts and quotes r/wallstreetbets comments mentioning the ticker (~2017–18, undated).",
    requires=["huggingface_hub"], pip=["huggingface_hub"])
WSB_INTEGRATION.run = lambda prices=None, ticker="", **kw: wsb_corpus_mentions(ticker)

MONEY_INTEGRATION = Integration(
    key="reddit_money_corpus", title="Reddit finance posts (kowalsky)", hf_id=MONEY_REPO, hf_kind="dataset",
    category="social_source", description="Finds Reddit finance/trading posts mentioning the ticker (undated, unfiltered scrape).",
    requires=["huggingface_hub"], pip=["huggingface_hub"])
MONEY_INTEGRATION.run = lambda prices=None, ticker="", **kw: reddit_money_mentions(ticker)
