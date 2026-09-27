"""Regression tests for issues raised in code review of the pump research toolkit"""

import csv
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_pump_research import make_prices, FakePrices  # noqa: E402

from pump_research.collector import collect_all
from pump_research.config import Settings
from pump_research.detection import locate_pump
from pump_research.features import context_features
from pump_research.models import Seed, PARTIAL, SKIPPED, OK
from pump_research.sources import filings as filings_mod, news as news_mod, social as social_mod


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=str(tmp_path / "data"), polygon_api_key="test")


def test_control_windows_use_full_baseline(settings):
    frames = {"P": make_prices("2020-01-01", 400, pump_at=350)}
    rec = collect_all([Seed("P", frames["P"].index[350], "extreme")], settings, [FakePrices(settings, frames)], [])[0]
    assert rec["controls"]
    assert all(c["baseline_days"] == settings.baseline_days for c in rec["controls"])
    assert rec["price_features"]["baseline_days"] == settings.baseline_days


def test_multi_day_run_fields_describe_one_day(settings):
    prices = make_prices("2021-01-01", 300, run=(250, 3, 8.0))
    ev = locate_pump(prices, prices.index[251], settings)
    assert ev.event_type == "multi_day_run" and ev.pump_date == prices.index[250]
    spike = prices.loc[ev.spike_date]
    prev = prices["close"].shift(1).loc[ev.spike_date]
    assert ev.prev_close == pytest.approx(prev)
    assert ev.day_high == pytest.approx(spike["high"])
    assert ev.high_multiple == pytest.approx(spike["high"] / prev, abs=1e-3)


def test_polygon_news_stays_in_window_and_paginates(settings, monkeypatch):
    pages = [
        {"results": [{"published_utc": "2021-01-11T10:00:00Z", "title": "in"}], "next_url": "https://api.polygon.io/next"},
        {"results": [{"published_utc": "2021-01-22T23:00:00Z", "title": "last day"},
                     {"published_utc": "2021-01-23T01:00:00Z", "title": "after window"}]},
    ]
    calls = []
    monkeypatch.setattr(news_mod, "http_get_json", lambda url, params=None, **kw: calls.append(url) or pages[len(calls) - 1])
    res = news_mod.PolygonNews(settings).fetch("GME", date(2021, 1, 11), date(2021, 1, 22))
    assert res.status == OK and [r["title"] for r in res.records] == ["in", "last day"]
    assert calls[1] == "https://api.polygon.io/next"


def test_capped_sources_are_marked_partial(settings, monkeypatch):
    full_page = {"data": [{"created_utc": 1610400000 - i, "title": "$GME moon", "subreddit": "wsb", "author": f"a{i}",
                           "permalink": f"/r/wsb/{i}"} for i in range(100)]}
    monkeypatch.setattr(social_mod, "http_get_json", lambda *a, **k: full_page)
    reddit = social_mod.PullpushReddit(settings)
    reddit.max_pages = 2
    res = reddit.fetch("GME", date(2021, 1, 11), date(2021, 1, 22))
    assert res.status == PARTIAL and "lower bounds" in res.detail

    gdelt = news_mod.GdeltNews(settings)
    gdelt.coverage_days = 10 ** 6
    arts = {"articles": [{"seendate": "20210111T000000Z", "title": "x", "domain": "d", "url": "u"}] * gdelt.max_records}
    monkeypatch.setattr(news_mod, "http_get_json", lambda *a, **k: arts)
    assert gdelt.fetch("GME", date(2021, 1, 11), date(2021, 1, 22)).status == PARTIAL

    feats = context_features({"reddit": res.records}, [date(2021, 1, 11)], answered=["reddit"], partial=["reddit"])
    assert feats["reddit_partial"] and feats["reddit_mentions"] == len(res.records)


def test_sec_unknown_ticker_is_skipped_not_empty(settings, monkeypatch):
    filings_mod.SecEdgarFilings._ticker_map = None
    monkeypatch.setattr(filings_mod, "http_get_json", lambda *a, **k: {"0": {"ticker": "AAPL", "cik_str": 320193}})
    res = filings_mod.SecEdgarFilings(settings).fetch("LFIN", date(2017, 12, 1), date(2017, 12, 15))
    assert res.status == SKIPPED and "CIK" in res.detail
    filings_mod.SecEdgarFilings._ticker_map = None


def test_sec_follows_older_filing_pages(settings, monkeypatch):
    def fake(url, **kw):
        if url.endswith("CIK0000000042.json"):
            return {"filings": {"recent": {"form": ["10-K"], "filingDate": ["2024-03-01"], "accessionNumber": ["1-1"],
                                           "primaryDocument": ["a.htm"], "primaryDocDescription": [""]},
                                "files": [{"name": "CIK0000000042-submissions-001.json", "filingFrom": "2016-01-01", "filingTo": "2019-12-31"},
                                          {"name": "CIK0000000042-submissions-000.json", "filingFrom": "2005-01-01", "filingTo": "2015-12-31"}]}}
        if url.endswith("-001.json"):
            return {"form": ["424B4", "8-K"], "filingDate": ["2017-12-05", "2018-02-01"], "accessionNumber": ["2-2", "3-3"],
                    "primaryDocument": ["b.htm", "c.htm"], "primaryDocDescription": ["Prospectus", ""]}
        raise AssertionError(f"unexpected fetch {url}")
    monkeypatch.setattr(filings_mod, "http_get_json", fake)
    res = filings_mod.SecEdgarFilings(settings).fetch("LFIN", date(2017, 12, 1), date(2017, 12, 15), cik=42)
    assert [r["form"] for r in res.records] == ["424B4"]


def test_discover_respects_start_date(tmp_path, monkeypatch):
    from pump_research import cli
    prices = make_prices("2021-01-01", 60, pump_at=5)  # pump on 2021-01-08
    monkeypatch.setattr(cli, "default_price_sources", lambda s: [FakePrices(s, {"X": prices})])
    tickers = tmp_path / "t.txt"
    tickers.write_text("X\n")
    out = tmp_path / "found.csv"
    start_after_pump = prices.index[6].isoformat()
    cli.main(["discover", "--tickers-file", str(tickers), "--start", start_after_pump, "--out", str(out)])
    assert list(csv.DictReader(open(out))) == []
    cli.main(["discover", "--tickers-file", str(tickers), "--start", "2021-01-01", "--out", str(out)])
    assert [r["approx_date"] for r in csv.DictReader(open(out))] == [prices.index[5].isoformat()]
