"""
Triplers: every listed US stock that tripled within three weeks, and everything that was true
in the window before it launched (1-hour, 4-hour and daily readings, news, filings, social).
The collected windows train the scanner: blocks that fire far more often before triplers than in
ordinary windows become the Tripler DNA scan.
"""

from .discover import find_triples, discover
from .universe import listed_tickers

__all__ = ["find_triples", "discover", "listed_tickers"]
