"""
Technical analysis engine used by pump research and the web app.

All functions take a daily OHLCV DataFrame with lowercase columns
(open, high, low, close, volume) and never look past the bar they analyze.
"""

from .snapshot import technical_snapshot

__all__ = ["technical_snapshot"]
