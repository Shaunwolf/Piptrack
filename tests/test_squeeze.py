"""Squeeze mechanics: gamma maths, feature windows, collector wiring and Scan Lab blocks (fakes; no network)"""

import os
import sys
from datetime import date

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_pump_research import make_prices  # noqa: E402

from pump_research.scanlab import PRESETS, ScanContext, evaluate, normalize_spec, run_scan  # noqa: E402
from pump_research.scanlab.engine import needed_feeds  # noqa: E402
from pump_research.squeeze import gamma_profile, squeeze_features  # noqa: E402
from pump_research.squeeze.options import bs_gamma, net_gex  # noqa: E402
from pump_research.squeeze.sources import _parse_pipe, short_interest_asof  # noqa: E402


# --- File formats (samples copied from the real FINRA / Nasdaq files) ---------------------------------------------

def test_parsers_read_real_file_layouts():
    finra = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n20251031|A|242448|10|345552|B,Q,N\n11061\n"
    df = _parse_pipe(finra)
    assert list(df["Symbol"]) == ["A"] and df["ShortVolume"].iloc[0] == "242448"
    nasdaq = ("Symbol|Security Name|Market Category|Reg SHO Threshold Flag|Rule 3210|Filler\n"
              "ACCL|ACCO GROUP HLDGS LTD ORD SHS N|S|Y|N|\n20251031230019\n")
    assert list(_parse_pipe(nasdaq)["Symbol"]) == ["ACCL"]


# --- Gamma exposure ------------------------------------------------------------------------------------------------------

def test_gamma_peaks_at_the_money_and_flip_is_found():
    assert bs_gamma(100, 100, 0.05, 0.6) > bs_gamma(100, 130, 0.05, 0.6) > 0
    calls = [{"kind": "call", "strike": 120.0, "years": 14 / 365, "iv": 0.8, "oi": 5000, "volume": 9000}]
    puts = [{"kind": "put", "strike": 90.0, "years": 14 / 365, "iv": 0.8, "oi": 8000, "volume": 100}]
    profile = gamma_profile(calls + puts, spot=95.0)
    assert profile["net_gex"] < 0 and profile["regime"] == "negative"           # near the big put strike: dealers short gamma
    assert 95 < profile["gamma_flip"] < 120                                      # rising into the call strike flips it positive
    assert net_gex(calls + puts, profile["gamma_flip"] + 3) > 0
    assert profile["call_wall"] == 120.0 and profile["short_dated_call_vol_oi"] is None   # 120 is >25% above spot
    assert gamma_profile([], 10) == {}


# --- Squeeze features over a window --------------------------------------------------------------------------------------

class FakeData:
    def __init__(self, ratios, lists, si):
        self.ratios, self.lists, self.si = ratios, lists, si

    def short_volume_ratios(self, tickers, days):
        return {t: [self.ratios.get(d) for d in days] for t in tickers}

    def threshold_list(self, d):
        return self.lists.get(d)

    def short_interest_history(self, ticker):
        return self.si


def bdays(end, n):
    import pandas as pd
    return [d.date() for d in pd.bdate_range(end=end, periods=n)]


def test_squeeze_features_use_only_data_up_to_the_window_end():
    window = bdays("2021-01-22", 10)
    base = bdays("2021-01-08", 10)
    ratios = {d: 0.40 for d in base} | {d: 0.60 for d in window}
    lists = {d: {"GME"} for d in bdays("2021-01-22", 9)} | {d: set() for d in bdays("2021-01-08", 5)}
    si = [{"date": "2020-12-31", "short": 70e6, "days_to_cover": 5.2, "avg_volume": 13.4e6, "change_pct": 4.0},
          {"date": "2021-01-15", "short": 61e6, "days_to_cover": 2.1, "avg_volume": 29e6, "change_pct": -12.0}]
    f = squeeze_features("GME", window, FakeData(ratios, lists, si))
    assert f["sq_short_vol_ratio"] == pytest.approx(0.60) and f["sq_short_vol_ratio_change"] == pytest.approx(0.20)
    assert f["sq_threshold_streak"] == 9 and f["sq_threshold_day8_plus"] and f["sq_on_threshold_list"]
    # The Jan 15 report isn't public until ~9 days later, so the Dec 31 report is the one known on Jan 22
    assert f["sq_days_to_cover"] == 5.2 and f["sq_days_to_cover_3plus"]
    assert short_interest_asof(si, date(2021, 1, 25))["date"] == "2021-01-15"
    # Lists published but the ticker isn't on them: a real zero. No lists at all: unknown, so no feature
    assert squeeze_features("XYZ", window, FakeData({}, lists, [])) == {"sq_threshold_streak": 0, "sq_on_threshold_list": False,
                                                                        "sq_threshold_day8_plus": False}
    assert squeeze_features("XYZ", window, FakeData({}, {}, [])) == {}


def test_collector_adds_squeeze_features_to_event_and_controls(monkeypatch):
    from pump_research import collector
    record = {"price_features": {"window_return": 0.1}, "controls": [{"window_end": "2020-06-01"}, {"window_end": "2020-07-01"}],
              "sources": {}}
    calls = []

    def fake(ticker, window, data=None):
        calls.append(window[-1])
        return {"sq_threshold_streak": len(calls)}
    monkeypatch.setattr("pump_research.squeeze.squeeze_features", fake)
    collector.add_squeeze_features(record, "KOSS", [date(2021, 1, 22)], [[date(2020, 6, 1)], [date(2020, 7, 1)]])
    assert record["price_features"]["sq_threshold_streak"] == 1
    assert [c["sq_threshold_streak"] for c in record["controls"]] == [2, 3]
    assert record["sources"]["squeeze"]["status"] == "ok"


# --- Scan Lab blocks with injected feeds -----------------------------------------------------------------------------------

def ctx_with(feeds, df=None):
    return ScanContext(df if df is not None else make_prices("2022-01-01", 300, seed=5), ticker="T", meta={"feeds": feeds})


def run(block_type, feeds, df=None, **params):
    spec = {"groups": [{"name": "G", "logic": "all", "blocks": [{"type": block_type, "params": params}]}]}
    return evaluate(spec, ctx_with(feeds, df))["groups"][0]["blocks"][0]


def test_squeeze_blocks_read_their_feeds():
    assert run("reg_sho", {"squeeze": {"sq_threshold_streak": 9}}, mode="closeout")["hit"]
    assert not run("reg_sho", {"squeeze": {"sq_threshold_streak": 2}}, mode="streak", days=5)["hit"]
    assert "unavailable" in run("reg_sho", {}, mode="streak")["detail"]
    si = {"shortPercentOfFloat": 0.31, "shortRatio": 4.2, "sharesShort": 9e6, "sharesShortPriorMonth": 7e6}
    assert run("short_interest", {"short_interest": si}, pct_float=20, days_to_cover=3, rising=True)["hit"]
    assert not run("short_interest", {"short_interest": {**si, "shortPercentOfFloat": 0.05}}, pct_float=20)["hit"]
    assert run("short_volume", {"squeeze": {"sq_short_vol_ratio": 0.62, "sq_short_vol_ratio_change": 0.08}}, ratio=0.55)["hit"]
    gex = {"has_options": True, "net_gex": -2.5e6, "gamma_flip": 10.0, "call_wall": 12.0, "short_dated_call_vol_oi": 2.3}
    assert run("gamma", {"options": gex}, condition="negative")["hit"]
    assert run("gamma", {"options": gex}, condition="hot_calls", vol_oi=1)["hit"]
    assert not run("gamma", {"options": {"has_options": False}}, condition="negative")["hit"]
    assert run("mention_velocity", {"social": {"mentions": 300, "mentions_24h_ago": 40, "rank": 3}}, mentions=20, growth=2)["hit"]
    assert not run("mention_velocity", {"social": {"mentions": 30, "mentions_24h_ago": 25}}, mentions=20, growth=2)["hit"]


def test_pump_and_dump_filter_flags_red_flags():
    df = make_prices("2022-01-01", 300, seed=5)
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]] * 0 + 0.4
    r = run("clean_setup", {"short_interest": {"exchange": "PNK", "marketCap": 8e6}, "options": {"has_options": False}}, df)
    assert not r["hit"] and "OTC" in r["detail"] and "no listed options" in r["detail"] and "price" in r["detail"]
    good = make_prices("2022-01-01", 300, seed=5)
    good["volume"] = 5e6
    ok = run("clean_setup", {"short_interest": {"exchange": "NMS", "marketCap": 9e8}, "options": {"has_options": True}}, good)
    assert ok["hit"], ok["detail"]
    etf = run("clean_setup", {"short_interest": {"exchange": "PCX", "marketCap": 9e8, "quoteType": "ETF"}, "options": {"has_options": True}}, good)
    assert not etf["hit"] and "ETF" in etf["detail"]


def test_vcp_and_ema_coil_on_a_built_base():
    # Uptrend, then a base with pullbacks of ~20%, ~11%, ~5% on shrinking volume, closing just under the pivot
    up = list(np.linspace(20, 50, 220))
    legs = [(50, 40), (48, 42.7), (47.5, 45.1)]
    closes, vols = up[:], [2e6] * len(up)
    for hi, lo in legs:
        closes += list(np.linspace(closes[-1], hi, 8)) + list(np.linspace(hi, lo, 8))
        vols += [1.8e6] * 8 + [1.2e6 if lo == 45.1 else 1.6e6] * 8
    closes += list(np.linspace(45.1, 46.6, 5))
    vols += [0.9e6] * 5
    import pandas as pd
    idx = pd.bdate_range("2021-01-04", periods=len(closes)).date
    c = np.array(closes)
    df = pd.DataFrame({"open": c, "high": c * 1.004, "low": c * 0.996, "close": c, "volume": vols}, index=idx)
    r = run("vcp", {}, df, contractions=3, last_max=8, first_max=35, lookback=80, status="setting_up", near=5, stage2=True, dry=False)
    assert r["hit"], r["detail"]
    assert "→" in r["detail"]


def test_runner_prefetches_only_needed_feeds():
    seen = {}

    def feeds(needs, tickers, asof):
        seen["needs"], seen["tickers"], seen["asof"] = list(needs), list(tickers), asof
        return {t: {"squeeze": {"sq_threshold_streak": 10}} for t in tickers}

    def loader(tickers, timeframe="1d"):
        return {t: make_prices("2023-01-02", 200, seed=1) for t in tickers}
    spec = {"groups": [{"name": "G", "logic": "all", "blocks": [{"type": "reg_sho", "params": {"mode": "closeout"}}]}]}
    out = run_scan(spec, ["AAA", "BBB"], loader=loader, feeds=feeds)
    assert seen["needs"] == ["squeeze"] and seen["tickers"] == ["AAA", "BBB"] and out["matched"] == 2
    plain = {"groups": [{"name": "G", "logic": "all", "blocks": [{"type": "rsi"}]}]}
    seen.clear()
    run_scan(plain, ["AAA"], loader=loader, feeds=feeds)
    assert not seen                                                          # price-only scans fetch nothing extra


def test_squeeze_preset_uses_all_four_feeds():
    assert needed_feeds(normalize_spec(PRESETS["squeeze_setup"]["spec"])) == ["options", "short_interest", "social", "squeeze"]


# --- Radar: stores picks, grades them later against the day's base rate ---------------------------------------------------

def test_radar_stores_picks_and_grades_them(tmp_path, monkeypatch):
    import pandas as pd
    from pump_research import radar

    days = pd.bdate_range("2024-01-02", periods=80)
    flat = pd.DataFrame({"open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1e6}, index=days.date)
    jumper = flat.copy()
    jumper.iloc[62:, jumper.columns.get_loc("high")] = 16.0                 # +60% high soon after the radar day
    frames = {"JUMP": jumper, "FLAT": flat, "SPY": flat}

    def loader_until(n):
        return lambda tickers, timeframe="1d": {t: frames[t].iloc[:n] for t in tickers if t in frames}

    def fake_preset(key):
        return {"title": key, "universe": {"tickers": ["JUMP", "FLAT"]},
                "spec": {"mode": "ranked", "groups": [{"name": "G", "logic": "all", "blocks": [{"type": "price_range"}]}]}}
    monkeypatch.setattr(radar, "preset", fake_preset)
    snap = radar.run_radar(str(tmp_path), scans=["demo"], loader=loader_until(60), today=date(2024, 3, 25))
    assert {p["ticker"] for p in snap["scans"]["demo"]["picks"]} == {"JUMP", "FLAT"}
    assert (tmp_path / "picks" / "2024-03-25.json").exists() and (tmp_path / "latest.json").exists()

    pending = radar.grade(str(tmp_path), loader=loader_until(65))            # only 5 bars later: not gradable yet
    assert pending["pending_days"] == ["2024-03-25"]
    done = radar.grade(str(tmp_path), loader=loader_until(80))
    s = done["scans"]["demo"]
    assert s["picks"]["n"] == 2 and s["picks"]["hit_50"] == 0.5 and s["base_rate"]["hit_50"] == 0.5
    assert "Squeeze radar" in (tmp_path / "report.md").read_text()
