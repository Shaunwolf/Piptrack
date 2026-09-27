"""
Pump research toolkit.

Collects everything that was happening to a stock in the one to two weeks before
an extreme price spike (price/volume, SEC filings, news, Reddit chatter), stores
it per event, and analyzes what the pre-pump windows have in common compared to
ordinary periods for the same stocks.

Run `python -m pump_research --help` for the command line interface.
"""

from .toolkit import run_all_tools, run_tool, list_tools  # noqa: E402,F401  one-call access to every tool
