"""The one-call toolkit: every tool runs, results are JSON-ready, names and aliases resolve"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_pump_research import make_prices  # noqa: E402

from pump_research import run_all_tools, run_tool, list_tools
from pump_research.toolkit import TOOLS

SCREENSHOT_TOOLS = [
    "fib_retracement", "trend_based_fib_extension", "fib_channel", "fib_time_zone", "fib_speed_resistance_fan",
    "trend_based_fib_time", "fib_circles", "fib_spiral", "fib_speed_resistance_arcs", "fib_wedge", "pitchfan",
    "gann_box", "gann_square_fixed", "gann_square", "gann_fan",
    "adaptive_kalman_trend_filter", "all_candlestick_patterns", "all_time_fibonacci_retracement", "auto_fib_retracement",
    "fib_gann_confluence", "auto_harmonic_patterns", "bollinger_bands", "support_resistance_signals", "fear_greed_index",
    "fibonacci_levels",
]


def test_every_screenshot_tool_is_registered():
    assert set(SCREENSHOT_TOOLS) <= set(TOOLS)
    assert len(list_tools()) == len(TOOLS)


def test_run_all_tools_returns_json_ready_results_without_errors():
    prices = make_prices("2020-01-01", 300, pump_at=250, seed=5)
    out = run_all_tools(prices)
    json.dumps(out)  # must be JSON-serializable
    errors = {k: v for k, v in out.items() if isinstance(v, dict) and "error" in v}
    assert not errors, errors
    assert set(TOOLS) <= set(out)
    assert out["gann_fan"]["values_now"]["1x1"] is not None
    assert 0 <= out["fear_greed_index"]["score"] <= 100


def test_single_tool_aliases_and_yfinance_columns():
    prices = make_prices("2020-01-01", 200, seed=6)
    yf_style = prices.rename(columns=str.capitalize)
    assert run_tool("kalman", yf_style)["trend"] in ("up", "down")
    assert "patterns" in run_tool("harmonic_patterns", prices)
    subset = run_all_tools(prices, ["gann_box", "bollinger_bands"])
    assert set(subset) == {"as_of", "close", "gann_box", "bollinger_bands"}
    with pytest.raises(KeyError):
        run_tool("not_a_tool", prices)
