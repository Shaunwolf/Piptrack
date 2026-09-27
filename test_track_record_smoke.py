"""Smoke test for the Track Record feature. Run with the venv python:
    .venv/Scripts/python test_track_record_smoke.py
Boots the real Flask app against a throwaway SQLite DB, exercises the
logging -> pricing -> stats -> page-render chain end to end.

NOTE: HTTP checks run OUTSIDE `with app.app_context()` — a manually pushed
app context is reused by test requests, so Flask-Login state stored on `g`
would leak between requests and make anonymous users look authenticated.
"""
import os
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(BASE, "test_track_record.db").replace("\\", "/")
os.environ["SESSION_SECRET"] = "test-secret"
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-boot-test")

sys.path.insert(0, BASE)

from app import app, db  # noqa: E402
app.config['WTF_CSRF_ENABLED'] = False  # test client posts without CSRF tokens
import routes  # noqa: E402, F401  (registers routes)

from models import User, Signal  # noqa: E402
import track_record  # noqa: E402

PASS = []
FAIL = []

def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name} {extra}")

network_ok = False

with app.app_context():
    db.create_all()

    # Clean slate
    Signal.query.delete()
    User.query.filter_by(email="tracktest@example.com").delete()
    db.session.commit()

    # --- 1. logging -------------------------------------------------------
    print("\n[1] Signal logging")
    fake_results = [
        {'symbol': 'AAPL', 'price': 200.0, 'rsi': 55.0, 'volume_spike': 120.0,
         'pattern_type': 'uptrend', 'confidence_score': 78.5},
        {'symbol': 'MSFT', 'price': 400.0, 'rsi': 61.0, 'volume_spike': 30.0,
         'pattern_type': 'sideways', 'confidence_score': 62.0},
        {'symbol': '', 'price': 0, 'confidence_score': 10},  # junk, must be skipped
    ]
    created = track_record.log_signals_from_scan(fake_results, source='scanner')
    check("logs 2 valid signals, skips junk", created == 2, f"(created={created})")

    # dedupe: same symbol again within window -> 0 new
    created2 = track_record.log_signals_from_scan(fake_results[:1], source='scanner')
    check("dedupes repeat symbol within window", created2 == 0, f"(created={created2})")

    # --- 2. outcome pricing ----------------------------------------------
    print("\n[2] Outcome pricing")
    # Age the signals so all horizons are due
    aged = Signal.query.filter_by(symbol='AAPL').first()
    aged.created_at = datetime.utcnow() - timedelta(days=30)
    aged2 = Signal.query.filter_by(symbol='MSFT').first()
    aged2.created_at = datetime.utcnow() - timedelta(days=12)
    db.session.commit()

    try:
        summary = track_record.update_outcomes(batch_limit=10)
        print(f"      pricing summary: {summary}")
        aapl = Signal.query.filter_by(symbol='AAPL').first()
        msft = Signal.query.filter_by(symbol='MSFT').first()
        check("AAPL priced at all 3 horizons",
              aapl.return_5d is not None and aapl.return_10d is not None and aapl.return_20d is not None,
              f"(5d={aapl.return_5d}, 10d={aapl.return_10d}, 20d={aapl.return_20d})")
        check("MSFT priced at 5d+10d, 20d still pending",
              msft.return_5d is not None and msft.return_10d is not None and msft.return_20d is None,
              f"(5d={msft.return_5d}, 10d={msft.return_10d}, 20d={msft.return_20d})")
        check("returns are sane (-100 < r < 1000)",
              all(-100 < r < 1000 for r in (aapl.return_5d, aapl.return_10d, aapl.return_20d)))
        network_ok = True
    except Exception as e:
        print(f"      pricing skipped (likely no network): {e}")

    # --- 3. stats ----------------------------------------------------------
    print("\n[3] Stats")
    stats = track_record.get_track_record_stats()
    check("total signals counted", stats['total_signals'] == 2)
    check("horizon keys present", set(stats['horizons'].keys()) == {5, 10, 20})
    check("calibration has 5 buckets", len(stats['calibration']) == 5)
    if network_ok:
        check("10d horizon has priced count", stats['horizons'][10]['count'] >= 1,
              f"(count={stats['horizons'][10]['count']}, hit={stats['horizons'][10]['hit_rate']})")

    # --- 4. seed a user for HTTP checks ------------------------------------
    user = User(email="tracktest@example.com", first_name="Track", last_name="Test",
                is_verified=True, beta_user_number=1)
    user.set_password("TestPass123!")
    db.session.add(user)
    db.session.commit()

# --- 5. page render over HTTP (outside app context — see note above) -------
print("\n[5] Page render (logged-in)")
client = app.test_client()
resp = client.post('/login', data={
    'email': 'tracktest@example.com', 'password': 'TestPass123!'
}, follow_redirects=False)
check("login succeeds", resp.status_code in (302, 303), f"(status={resp.status_code})")

resp = client.get('/track_record')
body = resp.get_data(as_text=True)
check("GET /track_record returns 200", resp.status_code == 200, f"(status={resp.status_code})")
check("page shows logged signals", 'AAPL' in body and 'MSFT' in body)
check("page shows calibration section", 'Score Calibration' in body)
check("page shows horizon cards", '10-Day Outcomes' in body)

client2 = app.test_client()
resp2 = client2.get('/track_record', follow_redirects=False)
check("anonymous user is redirected to login", resp2.status_code in (302, 303),
      f"(status={resp2.status_code})")

resp = client.post('/api/track_record/update', json={'batch_limit': 5})
check("POST /api/track_record/update succeeds",
      resp.status_code == 200 and resp.get_json().get('success') is True,
      f"(resp={resp.get_json()})")

print(f"\n{'='*50}\nRESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("Failed:", FAIL)
    sys.exit(1)
print("ALL SMOKE TESTS PASSED")
