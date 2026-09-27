"""Settings for pump detection and data collection"""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # A pump is a move of at least this multiple (5.0 = +400%)
    min_multiple: float = 5.0
    # 'strict': prev close -> same-day close must reach min_multiple
    # 'broad':  prev close -> same-day high, or a run of up to max_run_days, may reach it
    criterion: str = "broad"
    max_run_days: int = 5

    # Pre-pump window: trading days immediately before the pump day
    pre_window_days: int = 10
    # Baseline used to judge "unusual" volume/volatility inside the window
    baseline_days: int = 60
    # Seed dates are approximate; search this many trading days either side for the real spike
    search_radius_days: int = 10
    # Ordinary windows per event used as a comparison group
    control_windows_per_event: int = 4
    # Control windows must end at least this many trading days before the pump
    control_gap_days: int = 30

    data_dir: str = "pump_data"
    seeds_file: str = field(default_factory=lambda: os.path.join(os.path.dirname(__file__), "seeds.csv"))

    # Contact string required by SEC EDGAR's fair-access policy
    sec_user_agent: str = field(default_factory=lambda: os.environ.get(
        "SEC_USER_AGENT", "PipSqueak pump research (set SEC_USER_AGENT to 'Name email')"))
    polygon_api_key: str = field(default_factory=lambda: os.environ.get("POLYGON_API_KEY", ""))
    request_timeout: int = 20
