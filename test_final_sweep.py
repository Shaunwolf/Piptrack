"""Smoke test for the final-sweep batch.
    .venv/Scripts/python test_final_sweep.py

Covers:
  1. Ghost-field migration: a pre-existing DB lacking the two new
     pattern_evolution columns gets them via the idempotent ALTERs in app.py
  2. Scanner / Patterns nav links are visible again
  3. Newly protected endpoints redirect anonymous users to login (302)
  4. /track_stock is POST-only and works for a logged-in user
  5. /pattern_dashboard renders with a seeded PatternEvolution row that
     uses timing_confidence (the former ghost field)
  6. Scan universes contain no confirmed-dead tickers and use the
     corrected symbols (BRK-B, XYZ, ZM)
"""
import ast
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "test_sweep.db")
os.environ["DATABASE_URL"] = "sqlite:///" + DB_PATH.replace("\\", "/")
os.environ["SESSION_SECRET"] = "test-secret"
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-boot-test")

sys.path.insert(0, BASE)

PASS = []
FAIL = []

def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name} {extra}")

# --- 1. pre-existing DB without the new columns gets migrated -----------------
print("\n[1] Ghost-field migration on pre-existing DB")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
# Simulate an old deployment: pattern_evolution exists but lacks the two columns
conn = sqlite3.connect(DB_PATH)
conn.execute("""CREATE TABLE pattern_evolution (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    pattern_type VARCHAR(50),
    confidence_score FLOAT,
    stage VARCHAR(30),
    completion_percentage FLOAT,
    time_in_pattern INTEGER,
    volatility_trend FLOAT,
    volume_trend FLOAT,
    momentum_change FLOAT,
    estimated_days_to_breakout INTEGER,
    breakout_probability_5_days FLOAT,
    breakout_probability_10_days FLOAT,
    direction_bias FLOAT,
    resistance_level FLOAT,
    support_level FLOAT,
    breakout_confirmation_level FLOAT,
    pattern_data JSON,
    created_at DATETIME,
    updated_at DATETIME)""")
conn.commit()
conn.close()

from app import app, db  # boot runs create_all + idempotent ALTERs
app.config['WTF_CSRF_ENABLED'] = False
import routes
from models import User, Stock, PatternEvolution

conn = sqlite3.connect(DB_PATH)
cols = {row[1] for row in conn.execute("PRAGMA table_info(pattern_evolution)")}
conn.close()
check("support_resistance_strength column added", "support_resistance_strength" in cols)
check("timing_confidence column added", "timing_confidence" in cols)

# --- seed user + data -----------------------------------------------------------
with app.app_context():
    User.query.filter_by(email="sweep@example.com").delete()
    Stock.query.delete()
    PatternEvolution.query.delete()
    db.session.commit()
    user = User(email="sweep@example.com", first_name="Final", last_name="Sweep",
                is_verified=True, beta_user_number=11)
    user.set_password("TestPass123!")
    db.session.add(user)
    db.session.add(Stock(symbol='TEST', name='Test Co', price=25.5, rsi=55.0,
                         volume_spike=120.0, pattern_type='uptrend',
                         fibonacci_position=62.0, confidence_score=82.0))
    db.session.add(PatternEvolution(
        symbol='TEST', pattern_type='ascending_triangle', stage='forming',
        confidence_score=0.72, completion_percentage=45.0,
        breakout_probability_5_days=0.6, estimated_days_to_breakout=5,
        volume_trend=0.4, volatility_trend=-0.1,
        momentum_change=0.12, support_resistance_strength=0.65,
        direction_bias=0.7, timing_confidence=0.78))
    db.session.commit()

# --- 2. nav links visible -------------------------------------------------------
print("\n[2] Navigation links re-enabled")
client = app.test_client()
client.post('/login', data={'email': 'sweep@example.com', 'password': 'TestPass123!'})
resp = client.get('/')
body = resp.get_data(as_text=True)
check("dashboard renders", resp.status_code == 200, f"(status={resp.status_code})")
check("Scanner nav link present", 'href="/scanner"' in body)
check("Patterns nav link present", 'href="/pattern_dashboard"' in body)

# --- 3. anonymous users are redirected -------------------------------------------
print("\n[3] Auth hardening on previously open endpoints")
anon = app.test_client()
protected = [
    ('GET', '/pattern_dashboard'), ('GET', '/widgets'), ('GET', '/forecast/AAPL'),
    ('GET', '/forecast_enhanced/AAPL'), ('GET', '/api/market/movers'),
    ('GET', '/api/market/quick-scan'), ('GET', '/api/background-scan/status'),
    ('GET', '/api/market/cache/stats'), ('GET', '/api/leaderboard'),
    ('GET', '/api/widget/AAPL'), ('GET', '/api/sparkline/AAPL'),
    ('GET', '/api/trading_journey'), ('GET', '/export_weekly_report'),
    ('GET', '/ai_review/AAPL'), ('GET', '/pattern_evolution/all'),
    ('POST', '/track_stock/TEST'), ('POST', '/generate_forecast'),
    ('POST', '/api/award_xp'), ('POST', '/update_confidence_scores'),
    ('POST', '/update_pattern_evolutions'),
]
for method, path in protected:
    resp = anon.open(path, method=method)
    check(f"anon {method} {path} -> 302", resp.status_code == 302,
          f"(status={resp.status_code})")

# --- 4. track_stock is POST-only and works ---------------------------------------
print("\n[4] /track_stock hardening")
resp = client.get('/track_stock/TEST')
check("GET /track_stock -> 405", resp.status_code == 405, f"(status={resp.status_code})")
resp = client.post('/track_stock/TEST')
check("POST /track_stock works", resp.status_code == 200 and resp.get_json().get('success'),
      f"(status={resp.status_code})")
with app.app_context():
    check("stock flagged tracked in DB",
          Stock.query.filter_by(symbol='TEST').first().is_tracked is True)

# --- 5. pattern dashboard renders with former ghost field ------------------------
print("\n[5] Pattern dashboard with timing_confidence")
resp = client.get('/pattern_dashboard')
body = resp.get_data(as_text=True)
check("GET /pattern_dashboard -> 200", resp.status_code == 200, f"(status={resp.status_code})")
check("seeded pattern appears", 'TEST' in body)

# --- 6. universe ticker hygiene ----------------------------------------------------
print("\n[6] Scan universe ticker hygiene")
METHODS = {
    "stock_scanner.py": ["top_gappers", "get_sp500_universe", "get_nasdaq_universe",
        "get_nyse_universe", "get_small_cap_universe", "get_biotech_universe",
        "get_crypto_stocks", "get_trending_stocks", "get_penny_stocks",
        "get_international_adrs", "get_sector_stocks"],
    "market_data_engine.py": ["_get_sp500_symbols", "_get_nasdaq100_symbols",
        "_get_russell2000_symbols", "_get_popular_etfs", "_get_high_volume_stocks",
        "_get_biotech_symbols", "_get_crypto_symbols"],
}
tickers = set()
for fname, methods in METHODS.items():
    tree = ast.parse(open(os.path.join(BASE, fname), encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in methods:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Attribute) and sub.attr in methods:
                    pass
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    s = sub.value.strip()
                    if s.isupper() and 1 <= len(s) <= 6 and s.replace('.', '').replace('-', '').isalpha():
                        tickers.add(s)

DEAD = ['TWTR', 'ATVI', 'BRK.B', 'CELG', 'KSU', 'ZOOM', 'SQ', 'WORK', 'DIDI',
        'NAKD', 'CRTX', 'CTIC', 'RIDE', 'HZNP', 'BLUE', 'SAGE', 'GNUS', 'XSPA',
        'TSNP', 'HMBL', 'EQOS', 'SKLZ', 'NKLA', 'MULN', 'WISH']
still_dead = [t for t in DEAD if t in tickers]
check("no confirmed-dead tickers remain", still_dead == [], f"(remaining={still_dead})")
for good in ['BRK-B', 'XYZ', 'ZM']:
    check(f"corrected symbol {good} present", good in tickers)

# --- summary ------------------------------------------------------------------------
print(f"\n{'=' * 50}\nRESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILURES:", *FAIL, sep="\n  - ")
    sys.exit(1)
print("ALL CHECKS PASSED")
