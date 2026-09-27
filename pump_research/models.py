"""Data structures shared across the toolkit"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional

# Source result statuses
OK = "ok"
NO_DATA = "no_data"
BLOCKED = "blocked"        # network policy / host unreachable
NEEDS_KEY = "needs_key"    # source requires an API key that isn't configured
ERROR = "error"
SKIPPED = "skipped"


@dataclass
class Seed:
    """A candidate event to research. Dates are approximate until price data confirms them."""
    ticker: str
    approx_date: date
    category: str                  # 'extreme' (reported >=5x) or 'famous_squeeze'
    reported_move: str = ""
    source_url: str = ""
    notes: str = ""
    ipo_price: Optional[float] = None


@dataclass
class SourceResult:
    source: str
    status: str
    records: List[Dict[str, Any]] = field(default_factory=list)
    detail: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def to_dict(self):
        return asdict(self)


@dataclass
class PumpEvent:
    ticker: str
    pump_date: date
    event_type: str                # 'single_day', 'multi_day_run', 'ipo_debut'
    prev_close: Optional[float]
    day_open: float
    day_high: float
    day_close: float
    day_volume: float
    close_multiple: Optional[float]    # day close / prev close
    high_multiple: Optional[float]     # day high / prev close
    run_multiple: Optional[float]      # best close within max_run_days / close before the run
    run_days: int
    meets_strict: bool
    meets_broad: bool
    window_start: Optional[date] = None
    window_end: Optional[date] = None

    def to_dict(self):
        d = asdict(self)
        for k in ("pump_date", "window_start", "window_end"):
            d[k] = d[k].isoformat() if d[k] else None
        return d
