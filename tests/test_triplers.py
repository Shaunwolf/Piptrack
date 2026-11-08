import json
import os

import numpy as np
import pandas as pd
import pytest

from pump_research.models import SourceResult
from pump_research.triplers import find_triples
from pump_research.triplers.collect import collect, end_position, to_4h
from pump_research.triplers.discover import control_windows, forward_max
from pump_research.triplers.universe import parse_directory


def daily(n=400, seed=0, triple_at=None, start=5.0):
    rng = np.random.default_rng(seed)
    c = start * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    if triple_at is not None:
        ramp = np.linspace(1, 3.6, 8)
        c[triple_at + 1:triple_at + 9] = c[triple_at] * ramp
        c[triple_at + 9:] = c[triple_at] * 3.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n - triple_at - 9)))
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    return pd.DataFrame({"open": c * 0.99, "high": c * 1.02, "low": c * 0.98, "close": c,
                         "volume": rng.integers(200_000, 900_000, n).astype(float)}, index=idx)


def hourly_from(d):
    rows = []
    for day, r in d.iterrows():
        for k, hh in enumerate([(9, 30), (10, 30), (11, 30), (12, 30), (13, 30), (14, 30), (15, 30)]):
            ts = day + pd.Timedelta(hours=hh[0], minutes=hh[1])
            p = r["open"] + (r["close"] - r["open"]) * (k + 1) / 7
            rows.append((ts, p, p * 1.005, p * 0.995, p, r["volume"] / 7))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index("ts")


def test_find_triples_locates_launch_and_peak():
    d = daily(triple_at=300)
    ev = find_triples(d, "ABC")
    assert len(ev) == 1
    e = ev[0]
    assert 290 <= e["launch_idx"] <= 300 and e["days_to_triple"] <= 15 and e["peak_multiple"] >= 3
    assert len(e["window_dates"]) == 10 and e["window_dates"][-1] == e["launch_date"]
    assert find_triples(daily(seed=3), "XYZ") == []


def test_find_triples_rejects_illiquid_and_bad_data():
    d = daily(triple_at=300)
    d["volume"] = 10.0
    assert find_triples(d, "ABC") == []
    d = daily(triple_at=300)
    d.iloc[305, d.columns.get_loc("close")] *= 200          # an unadjusted split-sized glitch
    assert find_triples(d, "ABC") == []


def test_forward_max_and_controls_match_bands_and_exclude_triplers():
    assert list(forward_max(np.array([1., 3., 2., 5.]), 2)[:3]) == [3., 5., 5.]
    prices = {f"T{i}": daily(seed=i) for i in range(6)}
    prices["ABC"] = daily(triple_at=300)
    events = find_triples(prices["ABC"], "ABC")
    ctl = control_windows(prices, events, per_event=4)
    assert len(ctl) == 4
    assert all(c["price_band"] == events[0]["price_band"] and c["forward_multiple"] < 3 for c in ctl)
    assert all(not (c["ticker"] == "ABC" and abs(c["launch_idx"] - 300) < 30) for c in ctl)


def test_four_hour_bars_split_the_session():
    d = daily(n=5)
    h4 = to_4h(hourly_from(d))
    assert len(h4) == 10
    first = h4.iloc[0]
    assert first.name.hour == 9 and h4.iloc[1].name.hour == 13
    assert first["volume"] == pytest.approx(d["volume"].iloc[0] * 4 / 7)
    day = d.index[2].isoformat()[:10]
    assert h4.index[end_position(h4, day, True)].hour == 13
    assert end_position(h4, "1990-01-01", True) is None


def test_parse_directory_keeps_common_stock_only():
    text = ("Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
            "AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N\nQQQ|Invesco QQQ|G|N|N|100|Y|N\n"
            "ABCDW|Abc Corp - Warrants|S|N|N|100|N|N\nZTEST|Test|Q|Y|N|100|N|N\nXYZW|Xyz Inc - Warrant|S|N|N|100|N|N\n"
            "File Creation Time: 1108202600:00|||||||\n")
    assert parse_directory(text, "Symbol") == ["AAPL"]


class FakeNews:
    name = "google_news"

    def fetch(self, ticker, start, end, **kw):
        recs = [{"date": end.isoformat(), "title": f"{ticker} announces deal", "publisher": "Wire", "url": "u"}] if ticker == "ABC" else []
        return SourceResult(self.name, "ok" if recs else "no_data", records=recs)


def test_collect_end_to_end_and_analyze(tmp_path):
    prices = {f"T{i}": daily(seed=i) for i in range(10)}
    for k in range(12):
        prices[f"P{k}"] = daily(seed=100 + k, triple_at=250 + k * 8)
    loader = lambda tickers, tf: {t: prices[t] for t in tickers if t in prices}
    hourly = lambda tickers: {t: hourly_from(prices[t].iloc[-120:]) for t in tickers}
    meta = collect(list(prices), str(tmp_path), daily_loader=loader, hourly_loader=hourly, sources=[FakeNews()],
                   controls_per_event=2)
    assert meta["triplers"] == 12 and meta["controls"] == 24
    data = json.load(open(tmp_path / "dataset.json"))
    rec = next(r for r in data["records"] if not r.get("control"))
    assert "1d" in rec["timeframes"] and rec["paths"]["1d"]["close"][rec["paths"]["1d"]["offset"].index(0)] == 1.0
    ev_file = json.load(open(tmp_path / "events" / f"{rec['id']}.json"))
    assert ev_file["rows_1d"] and ev_file["readings"]["1d"]["blocks"]
    assert any("1h" in r["timeframes"] and "4h" in r["timeframes"] for r in data["records"])
    table = pd.read_csv(tmp_path / "readings.csv.gz")
    assert {"1d"} <= set(table["timeframe"]) and "blk_rsi" in table.columns

    from pump_research.triplers.analyze import analyze, bh
    assert bh([0.01, 0.04, 0.5]) == pytest.approx([0.03, 0.06, 0.5])
    res = analyze(str(tmp_path))
    assert res["comparison"] and os.path.exists(tmp_path / "report.md")
    assert set(res["learned"]) == {"1d", "4h", "1h"}


def test_overlay_analogs_and_pages(tmp_path, monkeypatch):
    prices = {f"T{i}": daily(seed=i) for i in range(8)}
    for k in range(10):
        prices[f"P{k}"] = daily(seed=300 + k, triple_at=240 + k * 9)
    loader = lambda tickers, tf: {t: prices[t] for t in tickers if t in prices}
    hourly = lambda tickers: {t: hourly_from(prices[t].iloc[-120:]) for t in tickers}
    collect(list(prices), str(tmp_path), daily_loader=loader, hourly_loader=hourly, sources=[FakeNews()], controls_per_event=2)
    from pump_research.triplers import overlay
    from pump_research.triplers.analyze import analyze
    analyze(str(tmp_path))
    data = overlay.load(str(tmp_path))
    ov = overlay.overlay_data(data, "1d")
    assert ov["triplers"] and ov["bands"]["triplers"]["median"][ov["bands"]["triplers"]["offset"].index(0)] == 1.0
    trip = ov["triplers"][0]
    z = trip["offset"].index(0)
    res = overlay.analogs(data, [c * 7 for c in trip["close"][:z + 1]], "1d")
    assert res["matches"][0]["id"] == trip["id"] and res["matches"][0]["distance"] == 0
    rec = overlay.load_event(str(tmp_path), trip["id"])
    chart = overlay.event_chart(rec, "1d", ["spiral", "gann_fan"])
    groups = {t.get("legendgroup"): t.get("visible") for t in chart["figure"]["data"] if t.get("legendgroup")}
    assert groups.get("Gann fan") is True
    assert overlay.load_event(str(tmp_path), "../etc") is None

    monkeypatch.setenv("TRIPLER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DISABLE_BACKGROUND_SCANNER", "1")
    from main import app
    import tripler_routes
    monkeypatch.setattr(tripler_routes.overlay, "live_closes", lambda t, tf: prices["P1"])
    app.config.update(TESTING=True, LOGIN_DISABLED=True, WTF_CSRF_ENABLED=False)
    c = app.test_client()
    assert c.get("/pump-research/triplers").status_code == 200
    assert c.get("/api/pump-research/triplers/overlay?tf=4h").status_code == 200
    m = c.get("/api/pump-research/triplers/match/ZZZ?tf=1d").get_json()
    assert "tripler_share" in m and m["live"]["close"][-1] == 1.0
    assert c.get(f"/pump-research/triplers/event/{trip['id']}?tf=1h&tool=spiral").status_code == 200
    assert c.get("/pump-research/triplers/event/NOPE_1").status_code == 404
