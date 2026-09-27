"""Web pages for pump research, rendered through Flask's test client on synthetic data"""

import os
import sys
from datetime import date

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_pump_research import make_prices, FakePrices, FakeReddit, FakeFilings  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("web")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp / 'app.db'}"
    os.environ["DISABLE_BACKGROUND_SCANNER"] = "1"
    os.environ["PUMP_DATA_DIR"] = str(tmp / "pump_data")

    from pump_research.collector import collect_all
    from pump_research.config import Settings
    from pump_research.model import train
    from pump_research.models import Seed

    settings = Settings(data_dir=os.environ["PUMP_DATA_DIR"])
    frames = {f"P{i}": make_prices("2020-01-01", 400, pump_at=350, seed=20 + i) for i in range(9)}
    seeds = [Seed(t, df.index[350], "extreme", reported_move="+500%", source_url="https://example.com") for t, df in frames.items()]
    records = collect_all(seeds, settings, [FakePrices(settings, frames)], [FakeFilings(settings), FakeReddit(settings)])
    train(records, settings)

    import main  # noqa: F401  registers routes and the blueprint
    import pump_routes
    from app import app, db
    from models import User

    # Live scans read synthetic prices re-dated to end today (scans look at the last ~500 days)
    live = frames["P0"].iloc[:350].copy()
    live.index = [d.date() for d in pd.bdate_range(end=date.today(), periods=len(live))]
    pump_routes.default_price_sources = lambda s: [FakePrices(s, {"LIVE": live})]
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        u = User(email="web@example.com", first_name="Web", last_name="Test")
        u.set_password("secret123")
        db.session.add(u)
        db.session.commit()
    c = app.test_client()
    c.post("/login", data={"email": "web@example.com", "password": "secret123"})
    c.records = records
    return c


def test_dashboard_lists_events_and_analysis(client):
    r = client.get("/pump-research")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "P0" in html and "What separates pre-pump windows" in html and "Cross-validated AUC" in html
    assert "Pump Research" in html  # nav link


def test_event_dossier_renders_chart_and_technicals(client):
    rid = client.records[0]["id"]
    html = client.get(f"/pump-research/event/{rid}").get_data(as_text=True)
    assert "Plotly.newPlot" in html and "Technical picture" in html and "Fibonacci" in html
    assert "424B4" in html  # filing from the fake source
    assert client.get("/pump-research/event/NOPE").status_code == 404


def test_untrusted_links_are_not_rendered_as_javascript(client):
    from flask import render_template
    from app import app
    rec = dict(client.records[0])
    rec["context"] = {**rec["context"], "polygon_news": [{"date": "2021-01-01", "publisher": "x", "title": "bad", "url": "javascript:alert(1)"}]}
    with app.test_request_context():
        html = render_template("pump_research/event.html", rec=rec, ev=rec["event"], fig={"data": [], "layout": {}})
    assert "javascript:alert" not in html and "bad" in html


def test_live_scan_page_and_api(client):
    html = client.get("/pump-research/scan?ticker=live").get_data(as_text=True)
    assert "Technical Scan: LIVE" in html and "/100" in html and "Warning signs" in html
    r = client.get("/api/pump-research/scan/LIVE")
    assert r.status_code == 200 and r.get_json()["score"]["score"] is not None
    assert client.get("/api/pump-research/scan/UNKNOWN").status_code == 502
    assert client.get("/api/pump-research/scan/bad!ticker").status_code == 400


def test_legacy_pump_urls_redirect(client):
    for url in ("/backtest", "/pump-analysis", "/early_detection"):
        r = client.get(url)
        assert r.status_code == 302 and r.headers["Location"].endswith("/pump-research")


def test_pages_require_login():
    from app import app
    anon = app.test_client()
    assert anon.get("/pump-research").status_code == 302
