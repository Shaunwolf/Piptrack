"""Smoke test for the dead-endpoint cleanup + missing templates batch.
    .venv/Scripts/python test_cleanup_smoke.py

Covers:
  1. App boots with zero references to deleted modules
  2. The 4 previously-missing templates now render (200)
  3. Removed dead routes return 404
  4. Main pages still render (no url_for BuildError from removed endpoints)
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(BASE, "test_cleanup.db").replace("\\", "/")
os.environ["SESSION_SECRET"] = "test-secret"
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-boot-test")

sys.path.insert(0, BASE)

PASS = []
FAIL = []

def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name} {extra}")

from app import app, db
app.config['WTF_CSRF_ENABLED'] = False
import routes
from models import User, Stock

# --- 1. no dead imports remain ----------------------------------------------
print("\n[1] Dead module references")
with open(os.path.join(BASE, 'routes.py'), encoding='utf-8') as f:
    src = f.read()
dead_modules = ['enhanced_pump_detector', 'phase1_pump_detector', 'early_detection_watchlist',
                'historical_pump_backtest', 'enhanced_phase1_detector', 'biotech_catalyst_monitor',
                'simple_pump_analyzer', 'historical_comparison_engine', 'options_flow_monitor',
                'physics_engine']
remaining = [m for m in dead_modules if m in src]
check("no references to deleted modules in routes.py", remaining == [], f"(remaining={remaining})")

# --- seed user ----------------------------------------------------------------
with app.app_context():
    db.create_all()
    User.query.filter_by(email="cleanup@example.com").delete()
    Stock.query.delete()
    db.session.commit()
    user = User(email="cleanup@example.com", first_name="Clean", last_name="Up",
                is_verified=True, beta_user_number=7)
    user.set_password("TestPass123!")
    db.session.add(user)
    # Seed one high-confidence stock so /ai-picks has content
    db.session.add(Stock(symbol='TEST', name='Test Co', price=25.5, rsi=55.0,
                         volume_spike=120.0, pattern_type='uptrend',
                         fibonacci_position=62.0, confidence_score=82.0))
    db.session.commit()

client = app.test_client()
client.post('/login', data={'email': 'cleanup@example.com', 'password': 'TestPass123!'})

# --- 2. previously-missing templates render -----------------------------------
print("\n[2] Previously-missing templates now render")
for path, marker in [
    ('/account/preferences', 'Notification Preferences'),
    ('/subscription', 'Beta Founder'),
    ('/help', 'Frequently Asked Questions'),
    ('/ai-picks', 'AI Stock Picks'),
]:
    resp = client.get(path)
    body = resp.get_data(as_text=True)
    check(f"GET {path} -> 200 with content",
          resp.status_code == 200 and marker in body,
          f"(status={resp.status_code})")

# /ai-picks shows the seeded stock
resp = client.get('/ai-picks')
check("/ai-picks lists seeded high-confidence stock", 'TEST' in resp.get_data(as_text=True))

# --- 3. removed routes are gone -------------------------------------------------
print("\n[3] Removed dead routes return 404")
for path in ['/pump-analysis', '/backtest', '/early_detection', '/physics/AAPL',
             '/enhanced_detector', '/historical_backtest',
             '/api/physics/gravity/AAPL', '/api/physics/quantum/AAPL',
             '/api/run_pump_backtest', '/api/backtest_report',
             '/api/enhanced_pump_scan', '/api/pump_analysis/AAPL',
             '/api/phase1_market_scan', '/api/early_detection_scan',
             '/api/watchlist_summary', '/api/historical_backtest',
             '/api/biotech_catalysts', '/api/options_flow_scan',
             '/api/enhancement_summary', '/api/historical-comparison/AAPL']:
    resp = client.get(path)
    check(f"GET {path} -> 404", resp.status_code == 404, f"(status={resp.status_code})")

# --- 4. main pages still render (no url_for BuildError) -------------------------
print("\n[4] Main pages still render after nav cleanup")
for path in ['/', '/dashboard', '/profile', '/journal', '/scanner_dashboard']:
    resp = client.get(path)
    check(f"GET {path} -> 200", resp.status_code == 200, f"(status={resp.status_code})")

# --- 5. settings & profile pages (csrf_token / hasattr / delete_account bugs) ---
print("\n[5] Settings and profile pages")
resp = client.get('/settings')
check("GET /settings -> 200", resp.status_code == 200, f"(status={resp.status_code})")

resp = client.get('/profile/edit')
check("GET /profile/edit -> 200", resp.status_code == 200, f"(status={resp.status_code})")

# delete_account: anonymous rejected, logged-in works and removes data
anon = app.test_client()
resp = anon.post('/account/delete', follow_redirects=False)
check("anonymous account deletion rejected", resp.status_code in (302, 303),
      f"(status={resp.status_code})")

resp = client.post('/account/delete', follow_redirects=False)
check("POST /account/delete redirects after success", resp.status_code in (302, 303),
      f"(status={resp.status_code})")
with app.app_context():
    gone = User.query.filter_by(email="cleanup@example.com").first()
    check("user row actually deleted", gone is None)

print(f"\n{'='*50}\nRESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("Failed:", FAIL)
    sys.exit(1)
print("ALL CLEANUP TESTS PASSED")
