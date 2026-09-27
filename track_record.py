"""
Track Record Engine
-------------------
Logs every signal PipSqueak generates (scanner hits, AI picks) and prices
them 5 / 10 / 20 days later, so the app can answer one honest question:
"when we flag a stock, does it actually go up?"

Public API:
    log_signals_from_scan(results, source)  -> int   (new signals logged)
    update_outcomes(batch_limit)            -> dict  (pricing run summary)
    get_track_record_stats()                -> dict  (everything the page needs)
"""

import logging
from datetime import datetime, timedelta

import yfinance as yf

from app import db
from models import Signal

DEDUPE_WINDOW_HOURS = 20   # don't re-log the same symbol within this window
HORIZONS = (5, 10, 20)     # outcome horizons in calendar days
DEFAULT_BATCH_LIMIT = 25   # max symbols priced per update run
STALE_DAYS = 45            # give up pricing signals older than this


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_signal(result, source='scanner'):
    """Log one signal dict (shape returned by StockScanner.analyze_stock).
    Returns True if a new row was created, False otherwise."""
    try:
        symbol = (result.get('symbol') or '').upper().strip()
        price = result.get('price')
        if not symbol or not price:
            return False

        cutoff = datetime.utcnow() - timedelta(hours=DEDUPE_WINDOW_HOURS)
        duplicate = Signal.query.filter(
            Signal.symbol == symbol,
            Signal.created_at >= cutoff
        ).first()
        if duplicate:
            return False

        db.session.add(Signal(
            symbol=symbol,
            source=source,
            entry_price=float(price),
            confidence_score=_safe_float(result.get('confidence_score')),
            rsi=_safe_float(result.get('rsi')),
            volume_spike=_safe_float(result.get('volume_spike')),
            pattern_type=result.get('pattern_type'),
        ))
        return True
    except Exception as e:
        logging.error(f"Track record: failed to log signal {result.get('symbol')}: {e}")
        return False


def log_signals_from_scan(results, source='scanner'):
    """Log a list of scan results. Never raises — logging must not break scans."""
    created = 0
    try:
        for result in results or []:
            if log_signal(result, source):
                created += 1
        if created:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Track record: bulk log failed: {e}")
        return 0
    if created:
        logging.info(f"Track record: logged {created} new signals (source={source})")
    return created


# ---------------------------------------------------------------------------
# Outcome pricing
# ---------------------------------------------------------------------------

def update_outcomes(batch_limit=DEFAULT_BATCH_LIMIT):
    """Price due signals against market data. Bounded work per run.

    A signal is 'due' for horizon H when it is at least H days old and
    has no recorded return for H yet.
    """
    now = datetime.utcnow()
    summary = {'symbols_priced': 0, 'signals_updated': 0, 'marked_unpriceable': 0}

    try:
        due = Signal.query.filter(
            Signal.unpriceable.is_(False),
            db.or_(
                Signal.return_20d.is_(None),
                db.and_(Signal.return_10d.is_(None),
                        Signal.created_at <= now - timedelta(days=10)),
                db.and_(Signal.return_5d.is_(None),
                        Signal.created_at <= now - timedelta(days=5)),
            )
        ).order_by(Signal.created_at.asc()).all()

        if not due:
            return summary

        # Group by symbol so each ticker is fetched once; cap the work.
        by_symbol = {}
        for signal in due:
            by_symbol.setdefault(signal.symbol, []).append(signal)
        symbols = list(by_symbol)[:batch_limit]

        for symbol in symbols:
            signals = by_symbol[symbol]
            start = min(s.created_at for s in signals) - timedelta(days=2)
            try:
                hist = yf.Ticker(symbol).history(start=start)
            except Exception as e:
                logging.warning(f"Track record: price fetch failed for {symbol}: {e}")
                continue

            if hist is None or hist.empty:
                # Delisted or no data — stop trying after STALE_DAYS
                for s in signals:
                    if (now - s.created_at).days > STALE_DAYS:
                        s.unpriceable = True
                        summary['marked_unpriceable'] += 1
                continue

            closes = hist['Close'].copy()
            closes.index = closes.index.tz_localize(None)  # naive for comparison
            summary['symbols_priced'] += 1

            for s in signals:
                updated = False
                for horizon in HORIZONS:
                    if getattr(s, f'return_{horizon}d') is not None:
                        continue
                    target = s.created_at + timedelta(days=horizon)
                    if target > now:
                        continue  # not due yet
                    price = _price_on_or_after(closes, target)
                    if price is None:
                        continue
                    setattr(s, f'price_{horizon}d', round(float(price), 2))
                    setattr(s, f'return_{horizon}d',
                            round((float(price) - s.entry_price) / s.entry_price * 100, 2))
                    updated = True
                if updated:
                    s.priced_at = now
                    summary['signals_updated'] += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Track record: outcome update failed: {e}")

    logging.info(f"Track record pricing run: {summary}")
    return summary


def _price_on_or_after(closes, target):
    """First closing price on or after the target date.

    Daily bars are indexed at midnight, so the target is floored to its
    date — otherwise a signal logged at 14:55 would miss that day's close.
    """
    try:
        target_day = target.replace(hour=0, minute=0, second=0, microsecond=0)
        future = closes[closes.index >= target_day]
        if len(future) > 0:
            return future.iloc[0]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

CALIBRATION_BUCKETS = [(0, 40), (40, 60), (60, 75), (75, 90), (90, 101)]


def get_track_record_stats():
    """Everything the Track Record page needs, in one dict."""
    signals = Signal.query.order_by(Signal.created_at.desc()).all()

    stats = {
        'total_signals': len(signals),
        'priced_signals': 0,
        'pending_signals': 0,
        'horizons': {},
        'calibration': [],
        'by_source': {},
        'recent_signals': signals[:25],
        'best_calls': [],
        'worst_calls': [],
    }

    priced = [s for s in signals if not s.unpriceable and
              (s.return_5d is not None or s.return_10d is not None or s.return_20d is not None)]
    stats['priced_signals'] = len(priced)
    stats['pending_signals'] = len(signals) - len(priced) - len([s for s in signals if s.unpriceable])

    # Per-horizon performance
    for horizon in HORIZONS:
        returns = [getattr(s, f'return_{horizon}d') for s in priced]
        returns = [r for r in returns if r is not None]
        stats['horizons'][horizon] = _summarize_returns(returns)

    # Calibration: does a higher confidence score actually mean a better outcome?
    # Uses the 10-day return where available, else 5-day.
    for low, high in CALIBRATION_BUCKETS:
        bucket = [s for s in priced
                  if s.confidence_score is not None and low <= s.confidence_score < high]
        returns = [_primary_return(s) for s in bucket]
        returns = [r for r in returns if r is not None]
        label = f"{low}+" if high > 100 else f"{low}-{high}"
        entry = _summarize_returns(returns)
        entry['label'] = label
        stats['calibration'].append(entry)

    # Performance by signal source
    for s in priced:
        r = _primary_return(s)
        if r is None:
            continue
        src = stats['by_source'].setdefault(s.source, [])
        src.append(r)
    stats['by_source'] = {k: _summarize_returns(v) for k, v in stats['by_source'].items()}

    # Hall of fame / shame (10-day return preferred)
    ranked = [(s, _primary_return(s)) for s in priced]
    ranked = [(s, r) for s, r in ranked if r is not None]
    ranked.sort(key=lambda t: t[1], reverse=True)
    stats['best_calls'] = ranked[:5]
    stats['worst_calls'] = ranked[-5:][::-1] if len(ranked) >= 5 else []

    return stats


def _primary_return(signal):
    """The return we judge a signal by: 10d if priced, else 5d, else 20d."""
    for attr in ('return_10d', 'return_5d', 'return_20d'):
        value = getattr(signal, attr)
        if value is not None:
            return value
    return None


def _summarize_returns(returns):
    count = len(returns)
    if count == 0:
        return {'count': 0, 'hit_rate': None, 'avg_return': None, 'best': None, 'worst': None}
    wins = [r for r in returns if r > 0]
    return {
        'count': count,
        'hit_rate': round(len(wins) / count * 100, 1),
        'avg_return': round(sum(returns) / count, 2),
        'best': round(max(returns), 2),
        'worst': round(min(returns), 2),
    }


def _safe_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
