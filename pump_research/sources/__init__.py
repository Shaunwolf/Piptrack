"""Pluggable data sources. Each returns a SourceResult with an explicit status."""

from .prices import YahooPrices, PolygonPrices
from .filings import SecEdgarFilings
from .news import PolygonNews, GdeltNews
from .social import PullpushReddit, ArcticShiftReddit


def default_price_sources(settings):
    """Polygon first when a key is set (it keeps delisted tickers), Yahoo as fallback"""
    sources = []
    if settings.polygon_api_key:
        sources.append(PolygonPrices(settings))
    sources.append(YahooPrices(settings))
    # Hugging Face minute-bar history as a fallback (e.g. delisted tickers), when switched on
    from ..integrations import is_enabled, HfMinutePrices
    if is_enabled("ohlcv_1m_prices"):
        sources.append(HfMinutePrices(settings))
    return sources


def default_context_sources(settings):
    """Sources describing what happened around the stock in the pre-pump window"""
    return [
        SecEdgarFilings(settings),
        PolygonNews(settings),
        GdeltNews(settings),
        PullpushReddit(settings),
        ArcticShiftReddit(settings),
    ]
