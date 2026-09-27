"""Smoke test for the P0 bug-fix batch. Run with the venv python:
    .venv/Scripts/python test_p0_fixes.py

Covers:
  1. App boots WITHOUT OPENAI_API_KEY (was a hard crash)
  2. Confidence-scorer unit/vocabulary mismatch fixed in the scanner
  3. Journal endpoints persist rows with user_id (was: every save 500'd)
  4. Login open redirect closed
  5. /forecast creates real Stock rows (was: name='Unknown Company', price=0)
  6. reset_password.py works via CLI args (no hardcoded credentials)
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(BASE, "test_p0.db").replace("\\", "/")
os.environ["SESSION_SECRET"] = "test-secret"
os.environ.pop("OPENAI_API_KEY", None)  # boot must survive without it

sys.path.insert(0, BASE)

PASS = []
FAIL = []

def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name} {extra}")

# --- 1. boot without OPENAI_API_KEY ----------------------------------------
print("\n[1] Boot without OPENAI_API_KEY")
try:
    from app import app, db
    app.config['WTF_CSRF_ENABLED'] = False
    import routes
    check("app boots without OPENAI_API_KEY", True)
    check("personalizer is None (degraded, not crashed)", routes.personalizer is None)
except Exception as e:
    check("app boots without OPENAI_API_KEY", False, f"({type(e).__name__}: {e})")
    print("Cannot continue without app boot")
    sys.exit(1)

from models import User, Stock, TradeJournal
from stock_scanner import StockScanner
from confidence_scorer import ConfidenceScorer

# --- 2. scorer unit/vocabulary fix ------------------------------------------
print("\n[2] Confidence scorer input format")
check("map_pattern_for_scorer maps lowercase labels",
      StockScanner.map_pattern_for_scorer('uptrend') == 'Bullish Trend' and
      StockScanner.map_pattern_for_scorer('downtrend') == 'Bearish Trend' and
      StockScanner.map_pattern_for_scorer('sideways') == 'Consolidation' and
      StockScanner.map_pattern_for_scorer('mixed') == 'Neutral')

scorer = ConfidenceScorer()
same_stock_old_format = {'rsi': 55.0, 'volume_spike': 120.0, 'pattern_type': 'uptrend',
                         'fibonacci_position': 0.62, 'price': 25.0}
same_stock_new_format = {'rsi': 55.0, 'volume_spike': 120.0, 'pattern_type': 'Bullish Trend',
                         'fibonacci_position': 62.0, 'price': 25.0}
old_score = scorer.calculate_score(same_stock_old_format)
new_score = scorer.calculate_score(same_stock_new_format)
check("fixed format scores materially higher than broken format",
      new_score > old_score, f"(old={old_score}, new={new_score})")

try:
    scanner = StockScanner()
    analysis = scanner.analyze_stock('AAPL')
    check("analyze_stock returns a result for AAPL", analysis is not None)
    if analysis:
        check("fibonacci_position on 0-100 scale",
              0 <= analysis['fibonacci_position'] <= 100,
              f"(fib={analysis['fibonacci_position']})")
        check("confidence score is pattern-sensitive (not the old flat ~60)",
              analysis['confidence_score'] != 60.72,
              f"(score={analysis['confidence_score']})")
except Exception as e:
    check("live analyze_stock", False, f"({e})")

# --- DB seed -----------------------------------------------------------------
with app.app_context():
    db.create_all()
    TradeJournal.query.delete()
    Stock.query.delete()
    User.query.filter_by(email="p0test@example.com").delete()
    db.session.commit()
    user = User(email="p0test@example.com", first_name="P", last_name="Zero",
                is_verified=True, beta_user_number=1)
    user.set_password("TestPass123!")
    db.session.add(user)
    db.session.commit()
    uid = user.id

# --- 3. journal endpoints -----------------------------------------------------
print("\n[3] Journal endpoints persist with user_id")
client = app.test_client()
client.post('/login', data={'email': 'p0test@example.com', 'password': 'TestPass123!'})

resp = client.post('/journal/save', json={
    'symbol': 'AAPL', 'entry_price': 200, 'stop_loss': 190, 'take_profit': 220,
    'tradeHighlights': 'clean breakout', 'keyLearnings': 'wait for volume',
    'confidence': 75
})
check("POST /journal/save succeeds", resp.status_code == 200 and resp.get_json().get('success'),
      f"(status={resp.status_code})")

resp = client.post('/add_trade', json={
    'symbol': 'MSFT', 'entry_price': 400, 'stop_loss': 390, 'take_profit': 430,
    'reflection': 'test trade', 'confidence_at_entry': 70
})
check("POST /add_trade (trade format) succeeds",
      resp.status_code == 200 and resp.get_json().get('success'),
      f"(status={resp.status_code}, resp={resp.get_json()})")

resp = client.post('/add_trade', json={
    'mood': 'confident', 'behaviors': ['patient'], 'highlights': 'good day',
    'learnings': 'stick to plan', 'confidence': 80
})
check("POST /add_trade (mood format) succeeds",
      resp.status_code == 200 and resp.get_json().get('success'),
      f"(status={resp.status_code})")

with app.app_context():
    rows = TradeJournal.query.filter_by(user_id=uid).all()
    check("3 journal rows persisted with correct user_id", len(rows) == 3,
          f"(rows={len(rows)})")

anon = app.test_client()
resp = anon.post('/journal/save', json={'symbol': 'AAPL'}, follow_redirects=False)
check("anonymous journal save is rejected (302 to login)", resp.status_code in (302, 303),
      f"(status={resp.status_code})")

# --- 4. open redirect ----------------------------------------------------------
print("\n[4] Login redirect safety")
c2 = app.test_client()
resp = c2.post('/login?next=https://evil.com/phish',
               data={'email': 'p0test@example.com', 'password': 'TestPass123!'},
               follow_redirects=False)
loc = resp.headers.get('Location', '')
check("external ?next= is rejected", 'evil.com' not in loc, f"(Location={loc})")

c3 = app.test_client()
resp = c3.post('/login?next=/journal',
               data={'email': 'p0test@example.com', 'password': 'TestPass123!'},
               follow_redirects=False)
loc = resp.headers.get('Location', '')
check("internal ?next= still works", loc.endswith('/journal'), f"(Location={loc})")

# --- 5. forecast creates real stock rows ---------------------------------------
print("\n[5] /forecast creates real Stock rows")
try:
    resp = client.get('/forecast/NVDA')
    check("GET /forecast/NVDA returns 200", resp.status_code == 200,
          f"(status={resp.status_code})")
    with app.app_context():
        stock = Stock.query.filter_by(symbol='NVDA').first()
        check("Stock row has real price and name",
              stock is not None and stock.price and stock.price > 0 and stock.name != 'Unknown Company',
              f"(price={stock.price if stock else None}, name={stock.name if stock else None})")
        check("Stock row has 0-100 fibonacci",
              stock is not None and 0 <= (stock.fibonacci_position or -1) <= 100,
              f"(fib={stock.fibonacci_position if stock else None})")
except Exception as e:
    check("forecast route", False, f"({e})")

# --- 6. reset_password CLI ------------------------------------------------------
print("\n[6] reset_password utility")
from reset_password import reset_user_password
ok = reset_user_password('p0test@example.com', 'BrandNewPass456!')
check("reset_user_password works", ok is True)
with app.app_context():
    u = User.query.filter_by(email='p0test@example.com').first()
    check("new password is usable", u.check_password('BrandNewPass456!'))
import subprocess
r = subprocess.run([sys.executable, 'reset_password.py'], capture_output=True, text=True,
                   env={**os.environ})
check("CLI without args prints usage (no hardcoded email)", 'usage:' in r.stderr.lower(),
      f"(stderr={r.stderr.strip()[:60]})")

print(f"\n{'='*50}\nRESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("Failed:", FAIL)
    sys.exit(1)
print("ALL P0 TESTS PASSED")
