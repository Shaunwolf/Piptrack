"""Scan Lab: block library, spec logic, block behaviour on built price paths, universe, runner, API and alerts"""

import functools
import os
import re
import sys
import zlib

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_pump_research import make_prices  # noqa: E402
from test_technicals import bars  # noqa: E402

from pump_research.scanlab import (BLOCKS, FAMILIES, PRESETS, ScanContext, catalog, evaluate, expand_universe,  # noqa: E402
                                   normalize_spec, run_scan)
from pump_research.scanlab.universe import LISTS, SECTORS  # noqa: E402
from pump_research.technicals.harmonics import projected_harmonics  # noqa: E402
from pump_research.technicals.pivots import Pivot  # noqa: E402


def one(type_, logic="all", **params):
    return {"groups": [{"name": "G", "logic": logic, "blocks": [{"type": type_, "params": params}]}]}


def run_block(df, type_, **params):
    ev = evaluate(one(type_, **params), ScanContext(df))
    return ev["groups"][0]["blocks"][0]


def path(closes, vol=1e6, wick=0.01):
    """OHLCV bars following a list of closes"""
    c = np.asarray(closes, float)
    o = np.r_[c[0], c[:-1]]
    rows = [[oo, max(oo, cc) * (1 + wick), min(oo, cc) * (1 - wick), cc, vol] for oo, cc in zip(o, c)]
    return bars(rows)


# --- Library -----------------------------------------------------------------------------------------

def test_catalog_covers_every_family_with_valid_params():
    cat = catalog()
    fams = [f["id"] for f in cat["families"]]
    assert fams[:5] == ["squeeze", "candles", "harmonics", "chart", "fibgann"] and len(cat["blocks"]) >= 54
    for b in cat["blocks"]:
        assert b["family"] in FAMILIES and b["title"] and b["summary"]
        for p in b["params"]:
            if p["kind"] in ("select", "multi"):
                values = [str(o[0]) for o in p["options"]]
                defaults = p["default"] if p["kind"] == "multi" else [p["default"]]
                assert all(str(d) in values for d in defaults), (b["id"], p["key"])
            if p["kind"] == "number":
                assert p["min"] <= p["default"] <= p["max"], (b["id"], p["key"])


def test_every_block_runs_on_ordinary_prices():
    ctx = ScanContext(make_prices("2022-01-01", 400, seed=3), benchmark=make_prices("2022-01-01", 400, seed=4))
    rows = []
    names = list(BLOCKS)
    for chunk in (names[:30], names[30:]):              # a spec holds at most 40 blocks
        ev = evaluate({"groups": [{"name": "G", "logic": "any", "blocks": [{"type": k} for k in chunk]}]}, ctx)
        rows += [b for g in ev["groups"] for b in g["blocks"]]
    assert len(rows) == len(BLOCKS)
    assert not [b["type"] for b in rows if b["detail"].startswith("could not evaluate")]
    assert all(0 <= b["strength"] <= 1 for b in rows)


def test_presets_are_valid_and_selective():
    for key, p in PRESETS.items():
        if key != "blank":
            assert normalize_spec(p["spec"])["groups"]
    matched = sum(evaluate(PRESETS["fib_gann"]["spec"], ScanContext(make_prices("2022-01-01", 400, seed=s)))["matched"]
                  for s in range(200, 220))
    assert matched <= 4


# --- Spec handling ----------------------------------------------------------------------------------------

def test_spec_validation_coerces_and_rejects():
    with pytest.raises(ValueError):
        normalize_spec({"groups": []})
    with pytest.raises(ValueError):
        normalize_spec({"groups": [{"blocks": [{"type": "no_such_block"}]}]})
    spec = normalize_spec({"groups": [{"logic": "weird", "blocks": [
        {"type": "rsi", "params": {"length": 9999, "condition": "bogus", "level": "abc"}, "weight": 99}]}]})
    p = spec["groups"][0]["blocks"][0]
    assert spec["groups"][0]["logic"] == "all" and p["weight"] == 10
    assert p["params"]["length"] == 50 and p["params"]["condition"] == "cross_up" and p["params"]["level"] == 30
    multi = normalize_spec(one("candle_pattern", patterns=["hammer", "<script>"]))["groups"][0]["blocks"][0]["params"]
    assert multi["patterns"] == ["hammer"]


def test_group_logic_negation_and_modes(monkeypatch):
    from pump_research.scanlab import engine
    monkeypatch.setitem(BLOCKS, "always", engine.Block("always", "filters", "Always", "", [], lambda c, p: engine.result(True, 1)))
    monkeypatch.setitem(BLOCKS, "never", engine.Block("never", "filters", "Never", "", [], lambda c, p: engine.result(False, 0.4)))
    ctx = ScanContext(make_prices("2022-01-01", 120, seed=1))

    def spec(logic, types, match="all", **extra):
        return {"match": match, "groups": [{"name": "G", "logic": logic, "min": 2, "blocks": [{"type": t} for t in types]}], **extra}
    assert not evaluate(spec("all", ["always", "never"]), ctx)["matched"]
    assert evaluate(spec("any", ["always", "never"]), ctx)["matched"]
    assert not evaluate(spec("atleast", ["always", "never"]), ctx)["matched"]
    assert evaluate(spec("atleast", ["always", "always", "never"]), ctx)["matched"]
    neg = {"groups": [{"name": "G", "logic": "all", "blocks": [{"type": "never", "negate": True}]}]}
    out = evaluate(neg, ctx)
    assert out["matched"] and out["score"] == 60.0
    ranked = spec("all", ["always", "never"], mode="ranked", min_score=60)
    assert evaluate(ranked, ctx)["matched"] and evaluate({**ranked, "min_score": 80}, ctx)["score"] == 70.0
    assert not evaluate({**ranked, "min_score": 80}, ctx)["matched"]


# --- Block behaviour on built price paths -----------------------------------------------------------------

def test_rsi_cross_up_from_oversold():
    closes = list(np.linspace(100, 60, 40)) + [61, 63, 66]
    hit = run_block(path(closes), "rsi", length=14, condition="cross_up", level=30, within=3)
    assert hit["hit"] and hit["direction"] == "bullish"
    assert not run_block(path(list(np.linspace(60, 100, 43))), "rsi", length=14, condition="cross_up", level=30, within=3)["hit"]


def test_breakout_needs_volume():
    closes = [50 + np.sin(i / 3) for i in range(60)] + [55]
    quiet = path(closes)
    assert not run_block(quiet, "breakout", side="up", lookback="50", volume=1.5, within=1)["hit"]
    loud = quiet.copy()
    loud.iloc[-1, loud.columns.get_loc("volume")] = 4e6
    r = run_block(loud, "breakout", side="up", lookback="50", volume=1.5, within=1)
    assert r["hit"] and "4.0×" in r["detail"]


def test_golden_cross_and_ribbon():
    closes = list(np.linspace(100, 70, 120)) + list(np.linspace(70, 115, 50))
    df = path(closes)
    assert run_block(df, "ma_cross", fast_kind="sma", fast=20, slow_kind="sma", slow=50, condition="golden", within=60)["hit"]
    assert run_block(df, "ma_ribbon", kind="ema", lengths="8,21,50", order="bullish", expanding=False)["hit"]
    assert not run_block(df, "ma_ribbon", kind="ema", lengths="8,21,50", order="bearish", expanding=False)["hit"]


def test_volume_spike_gap_and_streak():
    closes = [20.0] * 40 + [20.5, 21, 21.6, 22.4]
    df = path(closes, vol=1e5)
    df.iloc[-1, df.columns.get_loc("volume")] = 6e5
    assert run_block(df, "volume_spike", mult=3, avg=20, direction="up", within=1)["hit"]
    assert run_block(df, "candle_streak", color="green", count=4, progressive=True)["hit"]
    gapped = df.copy()
    gapped.iloc[-1] = [26, 27, 25.8, 26.5, 6e5]
    g = run_block(gapped, "gap", side="up", size=10, within=1, fill="open")
    assert g["hit"] and "open" in g["detail"]


def test_bollinger_squeeze_and_reentry():
    rng = np.random.default_rng(0)
    noisy = list(100 + np.cumsum(rng.normal(0, 2, 150)))
    calm = [noisy[-1] + 0.05 * np.sin(i) for i in range(30)]
    assert run_block(path(noisy + calm, wick=0.002), "bollinger", length=20, std=2, condition="squeeze", lookback=120, within=3)["hit"]
    dip = [100.0] * 40 + [100.5, 99.5] * 5 + [90, 99.8]
    assert run_block(path(dip, wick=0.002), "bollinger", length=20, std=2, condition="reentry_up", within=2)["hit"]


def test_fib_retracement_golden_pocket():
    up = list(np.linspace(50, 100, 40))
    pull = list(np.linspace(100, 69, 15))            # 62% back toward 50
    r = run_block(path(up + pull + [68.7], wick=0.002), "fib_retracement", levels=["golden"], anchor="last",
                  context="pullback", tolerance=2, min_swing=5, swing="8")
    assert r["hit"] and "Golden pocket" in r["detail"]


def test_projected_harmonic_prz_for_a_forming_bat():
    # Bullish Bat legs: XA up 100→200, B retraces 0.45 (155), C retraces 0.6 of AB (182)
    piv = [Pivot(0, 100.0, "low", True), Pivot(10, 200.0, "high", True), Pivot(20, 155.0, "low", True), Pivot(30, 182.0, "high", True)]
    found = {p["name"]: p for p in projected_harmonics(piv, close=125.0)}
    bat = found["bat"]
    assert bat["direction"] == "bullish" and bat["zones_overlap"]
    assert bat["prz_low"] <= 111.4 <= bat["prz_high"] + 1                 # D at the 0.886 retracement of XA
    assert bat["status"] == "approaching" and 0 < bat["distance"] < 0.2
    inside = {p["name"]: p for p in projected_harmonics(piv, close=112.0)}["bat"]
    assert inside["status"] == "in_zone"


def test_candle_pattern_hammer_at_support_after_decline():
    rows = [[30 - i * 0.5, 30.2 - i * 0.5, 29.6 - i * 0.5, 29.7 - i * 0.5, 1e5] for i in range(30)]
    last = rows[-1][3]
    rows.append([last - 0.1, last, last - 1.6, last - 0.05, 3e5])   # hammer: long lower wick, tiny body near the high
    r = run_block(bars(rows), "candle_pattern", patterns=["hammer"], within=1, trend="decline", level="any", volume=2)
    assert r["hit"] and r["direction"] == "bullish" and "Hammer" in r["detail"]


# --- Universe and runner -----------------------------------------------------------------------------------------

def test_universe_expands_sectors_lists_and_custom_tickers():
    u = expand_universe({"sectors": ["Energy"], "lists": ["meme"], "tickers": ["aapl", "$tsla", "bad ticker!!", "XOM"]})
    assert len(SECTORS["Energy"]) >= 15 and u["tickers"][:len(SECTORS["Energy"])] == SECTORS["Energy"]
    assert u["sector_of"]["GME"] == LISTS["meme"]["theme"] and u["sector_of"]["AAPL"] == "Information Technology"
    assert "TSLA" in u["tickers"] and u["tickers"].count("XOM") == 1 and not any(" " in t for t in u["tickers"])
    assert expand_universe({"sectors": list(SECTORS)}, limit=50)["truncated"]


def fake_loader(tickers, timeframe="1d"):
    return {t: make_prices("2023-06-01", 300, seed=zlib.crc32(t.encode()) % 1000) for t in tickers if t != "GONE"}


def test_run_scan_ranks_and_reports_missing():
    spec = {"mode": "ranked", "groups": [{"name": "G", "logic": "any", "blocks": [{"type": "rsi", "params": {"condition": "above", "level": 50}},
                                                                                 {"type": "relative_strength"}]}]}
    out = run_scan(spec, ["AAA", "BBB", "CCC", "GONE"], {"AAA": "Energy"}, loader=fake_loader)
    assert out["missing"] == ["GONE"] and out["scanned"] == 3
    scores = [r["score"] for r in out["results"]]
    assert scores == sorted(scores, reverse=True) and out["results"][0]["spark"]
    rs = [b for r in out["results"] for g in r["groups"] for b in g["blocks"] if b["type"] == "relative_strength"]
    assert rs and "unavailable" not in rs[0]["detail"]            # SPY came through the same loader


# --- Web API, saved scans and alerts ---------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    if "app" not in sys.modules:
        tmp = tmp_path_factory.mktemp("lab")
        os.environ.setdefault("DATABASE_URL", f"sqlite:///{tmp / 'app.db'}")
    os.environ["DISABLE_BACKGROUND_SCANNER"] = "1"
    import main  # noqa: F401
    import scanlab_routes
    from app import app, db
    from models import User
    app.config.update(TESTING=True)
    scanlab_routes.run_scan = functools.partial(run_scan, loader=fake_loader)
    with app.app_context():
        if not User.query.filter_by(email="lab@example.com").first():
            u = User(email="lab@example.com", first_name="Lab", last_name="Test")
            u.set_password("secret123")
            db.session.add(u)
            db.session.commit()
    c = app.test_client()
    login_html = c.get("/login").get_data(as_text=True)
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', login_html) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', login_html)
    c.post("/login", data={"email": "lab@example.com", "password": "secret123", "csrf_token": token.group(1) if token else ""})
    page = c.get("/scan-lab")
    assert page.status_code == 200, "login failed"
    c.csrf = re.search(r'name="csrf-token" content="([^"]+)"', page.get_data(as_text=True)).group(1)
    return c


def post(c, url, body, method="post"):
    return getattr(c, method)(url, json=body, headers={"X-CSRFToken": c.csrf})


def test_page_and_catalog(lab):
    html = lab.get("/scan-lab").get_data(as_text=True)
    assert "Scan Lab" in html and 'id="palette"' in html
    cat = lab.get("/api/scan-lab/catalog").get_json()
    assert len(cat["blocks"]) == len(BLOCKS) and {p["key"] for p in cat["presets"]} >= set(PRESETS)
    assert any(s["name"] == "Information Technology" for s in cat["universe"]["sectors"])


def test_run_api_batches_and_checks_csrf(lab):
    spec = PRESETS["momentum_breakout"]["spec"]
    assert lab.post("/api/scan-lab/run", json={"spec": spec, "tickers": ["AAA"]}).status_code == 400   # no CSRF token
    u = post(lab, "/api/scan-lab/universe", {"universe": {"sectors": ["Utilities"]}}).get_json()
    assert len(u["tickers"]) == len(SECTORS["Utilities"])
    out = post(lab, "/api/scan-lab/run", {"spec": spec, "tickers": u["tickers"][:10], "sector_of": u["sector_of"]}).get_json()
    assert out["scanned"] == 10 and all(r["sector"] == "Utilities" for r in out["results"])
    assert post(lab, "/api/scan-lab/run", {"spec": {"groups": []}, "tickers": ["AAA"]}).status_code == 400


def test_saved_scan_alerts_new_matches_once(lab):
    spec = {"mode": "ranked", "groups": [{"name": "G", "logic": "all", "blocks": [{"type": "price_range", "params": {"min": 0, "max": 100000}}]}]}
    bad = post(lab, "/api/scan-lab/scans", {"name": "x", "spec": spec, "universe": {"tickers": ["AAA"]}, "alert_webhook": "https://evil.example/hook"})
    assert bad.status_code == 400
    r = post(lab, "/api/scan-lab/scans", {"name": "Everything", "spec": spec, "universe": {"tickers": ["AAA", "BBB"]},
                                          "alert_enabled": True, "alert_new_only": True})
    assert r.status_code == 201
    scan_id = r.get_json()["id"]
    first = post(lab, f"/api/scan-lab/scans/{scan_id}/check", {}).get_json()
    assert {a["ticker"] for a in first["new_alerts"]} == {"AAA", "BBB"}
    again = post(lab, f"/api/scan-lab/scans/{scan_id}/check", {}).get_json()
    assert again["new_alerts"] == []                               # same matches: nothing new
    inbox = lab.get("/api/scan-lab/alerts").get_json()
    assert inbox["unseen"] == 2
    post(lab, "/api/scan-lab/alerts/seen", {})
    assert lab.get("/api/scan-lab/alerts").get_json()["unseen"] == 0
    assert post(lab, f"/api/scan-lab/scans/{scan_id}", {"name": "Renamed"}, method="put").get_json()["name"] == "Renamed"
    assert post(lab, f"/api/scan-lab/scans/{scan_id}", {}, method="delete").status_code == 200
    assert post(lab, f"/api/scan-lab/scans/{scan_id}", {}, method="delete").status_code == 404


def test_cron_endpoint_requires_secret(lab, monkeypatch):
    monkeypatch.delenv("CRON_SECRET", raising=False)
    assert lab.get("/api/scan-lab/alerts/run-all").status_code == 403
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    assert lab.get("/api/scan-lab/alerts/run-all", headers={"Authorization": "Bearer nope"}).status_code == 403
    r = lab.get("/api/scan-lab/alerts/run-all", headers={"Authorization": "Bearer s3cret"})
    assert r.status_code == 200 and "ran" in r.get_json()
