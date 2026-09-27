"""Offline tests for pump_research using synthetic prices and fake context sources"""

import json
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from pump_research.analysis import analyze
from pump_research.collector import collect_all, load_dataset
from pump_research.config import Settings
from pump_research.detection import locate_pump, discover
from pump_research.features import price_features, context_features
from pump_research.models import Seed, SourceResult, BLOCKED
from pump_research.report import build_report
from pump_research.sources.base import DataSource


def make_prices(start, days, pump_at=None, pump_multiple=6.0, run=None, seed=0, base_price=2.0):
    """Random-walk prices; optionally a one-day pump at index pump_at or a multi-day run (start, days, total multiple)"""
    rng = np.random.default_rng(seed)
    dates = [d.date() for d in pd.bdate_range(start, periods=days)]
    closes = base_price * np.cumprod(1 + rng.normal(0, 0.02, days))
    volume = rng.integers(100_000, 200_000, days).astype(float)
    highs = closes * 1.02
    if pump_at is not None:
        # Rising volume into the pump, then the spike
        volume[pump_at - 5:pump_at] *= np.linspace(2, 6, 5)
        closes[pump_at:] *= pump_multiple
        highs[pump_at] = closes[pump_at] * 1.2
        volume[pump_at] *= 50
    if run is not None:
        s, n, total = run
        step = total ** (1 / n)
        for i in range(n):
            closes[s + i:] *= step
        highs[s:s + n] = closes[s:s + n] * 1.02
    opens = np.r_[closes[0], closes[:-1]]
    return pd.DataFrame({"open": opens, "high": np.maximum(highs, closes), "low": closes * 0.98,
                         "close": closes, "volume": volume}, index=dates)


class FakePrices(DataSource):
    name = "fake_prices"

    def __init__(self, settings, frames):
        super().__init__(settings)
        self.frames = frames

    def _fetch(self, ticker, start, end, **kwargs):
        df = self.frames.get(ticker)
        if df is None:
            return []
        df = df[(df.index >= start) & (df.index <= end)]
        return [{"date": d.isoformat(), **{k: float(v) for k, v in row.items()}} for d, row in df.iterrows()]


class FakeReddit(DataSource):
    name = "reddit"

    def _fetch(self, ticker, start, end, **kwargs):
        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        # Chatter that accelerates into the pump
        return [{"date": d.isoformat(), "kind": "submission", "subreddit": "pennystocks", "author": f"u{i}_{j}",
                 "score": j, "title": f"${ticker} to the moon", "text": f"${ticker}", "sentiment": 0.6, "url": ""}
                for i, d in enumerate(days) for j in range(i)]


class FakeFilings(DataSource):
    name = "sec_filings"

    def _fetch(self, ticker, start, end, **kwargs):
        return [{"date": start.isoformat(), "form": "424B4", "group": "offering", "description": "Prospectus", "url": ""}]


class BlockedNews(DataSource):
    name = "polygon_news"

    def _fetch(self, ticker, start, end, **kwargs):
        return SourceResult(self.name, BLOCKED, detail="blocked in test")


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=str(tmp_path / "data"))


def test_single_day_pump_is_located_and_meets_strict(settings):
    prices = make_prices("2021-01-01", 300, pump_at=250, pump_multiple=6.0)
    approx = prices.index[247]  # seed date a few days off
    ev = locate_pump(prices, approx, settings)
    assert ev.pump_date == prices.index[250]
    assert ev.event_type == "single_day"
    assert ev.meets_strict and ev.meets_broad
    assert ev.close_multiple == pytest.approx(6.0, rel=0.15)
    assert ev.window_end == prices.index[249]
    assert ev.window_start == prices.index[240]


def test_multi_day_run_uses_run_start_for_window(settings):
    prices = make_prices("2021-01-01", 300, run=(250, 3, 8.0))
    ev = locate_pump(prices, prices.index[251], settings)
    assert ev.event_type == "multi_day_run"
    assert ev.pump_date == prices.index[250]
    assert ev.meets_broad and not ev.meets_strict
    assert ev.run_multiple == pytest.approx(8.0, rel=0.15)


def test_famous_squeeze_below_threshold_is_kept_but_not_qualifying(settings):
    prices = make_prices("2021-01-01", 300, pump_at=250, pump_multiple=2.3)
    ev = locate_pump(prices, prices.index[250], settings)
    assert ev is not None
    assert not ev.meets_broad and not ev.meets_strict


def test_ipo_debut_uses_offering_price_and_has_no_window(settings):
    prices = make_prices("2022-08-05", 40, base_price=40.0)
    ev = locate_pump(prices, prices.index[0], settings, ipo_price=4.0)
    assert ev.event_type == "ipo_debut"
    assert ev.prev_close == 4.0
    assert ev.meets_broad
    assert ev.window_start is None


def test_no_data_near_seed_returns_none(settings):
    prices = make_prices("2019-01-01", 100)
    assert locate_pump(prices, date(2021, 1, 27), settings) is None


def test_discover_finds_pump_days(settings):
    prices = make_prices("2021-01-01", 300, pump_at=250)
    assert discover(prices, settings) == [prices.index[250]]


def test_price_features_detect_volume_build_up(settings):
    prices = make_prices("2021-01-01", 300, pump_at=250)
    feats = price_features(prices, 249, settings)
    assert feats["window_days"] == 10
    assert feats["max_volume_ratio"] > 4
    assert feats["volume_trend_slope"] > 0


def test_context_features_measure_acceleration():
    window = [date(2021, 1, 11) + timedelta(days=i) for i in range(10)]
    reddit = [{"date": d.isoformat(), "author": f"a{i}", "sentiment": 0.5, "subreddit": "wsb"}
              for i, d in enumerate(window) for _ in range(i)]
    feats = context_features({"reddit": reddit}, window)
    assert feats["reddit_mentions"] == 45
    assert feats["reddit_mention_acceleration"] > 2


def test_full_pipeline_writes_dataset_and_report(settings):
    frames = {"PUMP": make_prices("2020-01-01", 400, pump_at=350, seed=1),
              "SQZ": make_prices("2020-01-01", 400, pump_at=350, pump_multiple=2.0, seed=2),
              "RUN": make_prices("2020-01-01", 400, pump_at=340, pump_multiple=7.0, seed=4),
              "IPO": make_prices("2022-08-05", 30, base_price=40.0, seed=3)}
    seeds = [Seed("PUMP", frames["PUMP"].index[352], "extreme"),
             Seed("RUN", frames["RUN"].index[340], "extreme"),
             Seed("SQZ", frames["SQZ"].index[350], "famous_squeeze"),
             Seed("IPO", frames["IPO"].index[0], "extreme", ipo_price=4.0),
             Seed("GONE", date(2018, 1, 5), "extreme")]
    records = collect_all(seeds, settings, [FakePrices(settings, frames)],
                          [FakeFilings(settings), BlockedNews(settings), FakeReddit(settings)])

    by_id = {r["id"].split("_")[0]: r for r in records}
    assert by_id["PUMP"]["qualifies"] and not by_id["SQZ"]["qualifies"]
    assert by_id["PUMP"]["sources"]["polygon_news"]["status"] == BLOCKED
    assert by_id["PUMP"]["context_features"]["filings_offering"] == 1
    # A blocked source means unknown, not zero
    assert by_id["PUMP"]["context_features"]["news_articles"] is None
    assert len(by_id["PUMP"]["controls"]) == settings.control_windows_per_event
    assert by_id["IPO"]["sources"]["reddit"]["status"] == "skipped"
    assert by_id["GONE"]["detection"] == "no price data around the seed date"

    # Files on disk round-trip
    assert os.path.exists(os.path.join(settings.data_dir, "pump_summary.csv"))
    assert len(os.listdir(os.path.join(settings.data_dir, "events"))) == 5
    reloaded = load_dataset(settings)
    assert [r["id"] for r in reloaded] == [r["id"] for r in records]

    result = analyze(reloaded)
    assert result["n_qualifying"] == 3  # PUMP, RUN and the IPO debut
    feats = {r["feature"]: r for r in result["feature_comparison"]}
    assert feats["max_volume_ratio"]["prob_event_higher"] > 0.8
    assert result["countdown"][0]["offset"] == -10
    json.dumps(result, default=str)

    report = build_report(reloaded, result, settings)
    assert "## Event dossiers" in report and "PUMP" in report and "BLOCKED" in report


def test_model_trains_and_scores_pre_pump_windows_higher(settings):
    from pump_research.model import train, score_features, analyze_prices, load_model
    frames = {f"P{i}": make_prices("2020-01-01", 400, pump_at=350, seed=10 + i) for i in range(10)}
    seeds = [Seed(t, df.index[350], "extreme") for t, df in frames.items()]
    records = collect_all(seeds, settings, [FakePrices(settings, frames)], [])
    model = train(records, settings)
    assert model["logistic"] is not None and model["logistic"]["cv_auc"] > 0.7
    assert load_model(settings)["n_events"] == 10

    pre = score_features(records[0]["price_features"], model)["score"]
    ordinary = score_features(records[0]["controls"][0], model)["score"]
    assert pre > ordinary

    res = analyze_prices("P0", frames["P0"].iloc[:350], settings, model)
    assert res["score"]["score"] is not None
    assert "volume_spike_5x_day" in res["signals"]
    assert res["technicals"]["fibonacci"]
